"""Shared code of the neural-network challenger (16_neural-network.ipynb).

Why this file exists: the random search (section 5) runs 4 trials at the same time in separate
processes. On macOS, worker processes can only use functions that live in an importable module, not
functions defined inside a notebook. The notebook imports everything from here and prints the most
important functions, so it still documents the full method.

Run with the NN environment (.venv-nn, Python 3.12, TensorFlow 2.16.2) from the repository root.
"""
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight

FEATURE_DIR = Path("data/features")
MODEL_DIR = Path("models")
CAT_FEATURES = ["tarif_type", "client_catg", "region"]  # integer codes of categories, one-hot encoded


# ---------------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------------
def load_features():
    # The 39 features of the final LightGBM, in the saved order
    return json.loads((MODEL_DIR / "selected_features_v3.json").read_text())["features"]


def load_training_clients():
    # The 108,394 training clients: X (39 columns, saved order) and y (0/1). Never the test clients.
    features = load_features()
    X = pd.read_csv(FEATURE_DIR / "X_train_v3.csv", index_col="client_id")[features]
    y = pd.read_csv(FEATURE_DIR / "y_train.csv", index_col="client_id")["target"].astype(int)
    assert X.index.equals(y.index), "X_train and y_train rows are not aligned"
    return X, y


def inner_split(X, y, seed=42):
    # Stratified 80/20 split of the TRAINING clients, used for tuning and early stopping
    fit_idx, ival_idx = train_test_split(X.index, test_size=0.2, stratify=y, random_state=seed)
    return X.loc[fit_idx], y.loc[fit_idx], X.loc[ival_idx], y.loc[ival_idx]


# ---------------------------------------------------------------------------------------------
# Preprocessing (always fitted on the clients the network is trained on, never on test clients)
# ---------------------------------------------------------------------------------------------
class SkewedLog1p(BaseEstimator, TransformerMixin):
    # Apply log1p to the columns that are non-negative and strongly right-skewed.
    # Which columns are transformed is decided in fit(), i.e. on the training clients only.
    def __init__(self, skew_threshold=1.0):
        self.skew_threshold = skew_threshold

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        skew = pd.DataFrame(X).skew().to_numpy()
        self.log_mask_ = (X.min(axis=0) >= 0) & (skew > self.skew_threshold)
        self.n_fit_rows_ = X.shape[0]  # kept to check on how many clients it was fitted
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float).copy()
        # clip at 0 so a (rare) negative value in new data cannot produce NaN
        X[:, self.log_mask_] = np.log1p(np.clip(X[:, self.log_mask_], 0, None))
        return X

    def get_feature_names_out(self, input_features=None):
        # one output column per input column, same names
        return np.asarray(input_features, dtype=object)


def make_preprocessor(features):
    # Return a NEW, unfitted pipeline:
    #   numeric:     median imputation -> log1p for skewed non-negative columns -> standardisation
    #   categorical: one-hot encoding, levels with < 1% of the clients grouped as "infrequent",
    #                unseen levels -> all zeros
    num_features = [f for f in features if f not in CAT_FEATURES]
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("log", SkewedLog1p(skew_threshold=1.0)),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),  # no missing codes today, kept for safety
        ("onehot", OneHotEncoder(min_frequency=0.01, handle_unknown="infrequent_if_exist",
                                 sparse_output=False, dtype=np.float32)),
    ])
    return ColumnTransformer(
        [("num", numeric, num_features), ("cat", categorical, CAT_FEATURES)],
        verbose_feature_names_out=False,
    )


# ---------------------------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------------------------
def build_mlp(n_inputs, n_layers, units, dropout, l2, learning_rate):
    # Feed-forward MLP: n_layers x [Dense(units, ReLU, L2) -> Dropout], sigmoid output
    import keras
    model = keras.Sequential(name="fraud_mlp")
    model.add(keras.Input(shape=(n_inputs,)))
    for _ in range(n_layers):
        model.add(keras.layers.Dense(units, activation="relu",
                                     kernel_regularizer=keras.regularizers.L2(l2)))
        if dropout > 0:
            model.add(keras.layers.Dropout(dropout))
    model.add(keras.layers.Dense(1, activation="sigmoid"))
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[keras.metrics.AUC(name="auc")],  # Keras' approximate ROC-AUC, steers early stopping
    )
    return model


def balanced_class_weight(y):
    # Same formula as class_weight="balanced" in scikit-learn / LightGBM: n / (2 * n_class)
    w = compute_class_weight("balanced", classes=np.array([0, 1]), y=np.asarray(y))
    return {0: float(w[0]), 1: float(w[1])}


def fit_with_early_stopping(config, Z_tr, y_tr, Z_va, y_va, seed, max_epochs=100, patience=10, verbose=0):
    # Train one network with early stopping on the validation AUC (patience 10, best weights restored).
    # Returns the model, the best epoch (1-based), the number of epochs run and the Keras history.
    import keras
    keras.utils.set_random_seed(seed)
    model = build_mlp(Z_tr.shape[1], config["n_layers"], config["units"], config["dropout"],
                      config["l2"], config["learning_rate"])
    stopper = keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=patience,
                                            restore_best_weights=True)
    history = model.fit(
        Z_tr, np.asarray(y_tr, dtype=np.float32),
        validation_data=(Z_va, np.asarray(y_va, dtype=np.float32)),
        epochs=max_epochs, batch_size=config["batch_size"],
        class_weight=balanced_class_weight(y_tr),
        callbacks=[stopper], verbose=verbose, shuffle=True,
    )
    best_epoch = int(np.argmax(history.history["val_auc"])) + 1
    return model, best_epoch, len(history.history["val_auc"]), history


def fit_fixed_epochs(config, Z_tr, y_tr, seed, epochs, verbose=0):
    # Train one network for a FIXED number of epochs, without any validation data (final refit, section 7)
    import keras
    keras.utils.set_random_seed(seed)
    model = build_mlp(Z_tr.shape[1], config["n_layers"], config["units"], config["dropout"],
                      config["l2"], config["learning_rate"])
    model.fit(Z_tr, np.asarray(y_tr, dtype=np.float32), epochs=epochs, batch_size=config["batch_size"],
              class_weight=balanced_class_weight(y_tr), verbose=verbose, shuffle=True)
    return model


def predict_proba(model, Z):
    # Fraud probabilities as a 1-D numpy array
    return model.predict(Z, batch_size=8192, verbose=0).ravel()


# ---------------------------------------------------------------------------------------------
# Random search
# ---------------------------------------------------------------------------------------------
def sample_configs(n_trials=30, seed=42):
    # Draw the trial settings from the frozen search space (model-comparison-plan.md)
    rng = np.random.default_rng(seed)
    rows = []
    for trial in range(n_trials):
        rows.append({
            "trial": trial,
            "n_layers": int(rng.integers(1, 4)),                                  # 1, 2 or 3
            "units": int(round(np.exp(rng.uniform(np.log(32), np.log(256))))),    # 32-256, log scale
            "dropout": float(rng.uniform(0.0, 0.5)),                              # 0-0.5
            "l2": float(10 ** rng.uniform(-6, -3)),                               # 1e-6 - 1e-3, log scale
            "learning_rate": float(10 ** rng.uniform(-4, -2)),                    # 1e-4 - 1e-2, log scale
            "batch_size": int(rng.choice([256, 512, 1024])),
        })
    return rows


# State of one worker process: the preprocessed inner split, built once per process
_WORKER = {}


def init_search_worker(threads_per_worker=2, seed=42):
    # Runs once in each worker process: limit CPU threads, then build the inner split and
    # fit the preprocessing on the inner FIT clients (identical in every worker: same seed, same data).
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    import tensorflow as tf
    tf.config.threading.set_intra_op_parallelism_threads(threads_per_worker)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()

    X, y = load_training_clients()
    X_fit, y_fit, X_ival, y_ival = inner_split(X, y, seed=seed)
    prep = make_preprocessor(list(X.columns)).fit(X_fit)
    _WORKER.update(
        Z_fit=prep.transform(X_fit).astype(np.float32), y_fit=y_fit.to_numpy(),
        Z_ival=prep.transform(X_ival).astype(np.float32), y_ival=y_ival.to_numpy(),
        seed=seed, threads=threads_per_worker,
    )


def run_trial(config):
    # One search trial: train with early stopping on the inner split, score the inner validation
    # clients with the EXACT ROC-AUC and PR-AUC (scikit-learn). Returns one result row.
    w = _WORKER
    t0 = time.perf_counter()
    model, best_epoch, epochs_run, history = fit_with_early_stopping(
        config, w["Z_fit"], w["y_fit"], w["Z_ival"], w["y_ival"], seed=w["seed"])
    fit_seconds = time.perf_counter() - t0
    p = predict_proba(model, w["Z_ival"])
    return {
        **config,
        "best_epoch": best_epoch,
        "epochs_run": epochs_run,
        "stopped_early": epochs_run < 100,
        "inner_val_roc_auc": float(roc_auc_score(w["y_ival"], p)),
        "inner_val_pr_auc": float(average_precision_score(w["y_ival"], p)),
        "inner_val_keras_auc_best": float(max(history.history["val_auc"])),
        "n_params": int(model.count_params()),
        "fit_seconds": fit_seconds,
        "threads": w["threads"],
        "seed": w["seed"],
    }
