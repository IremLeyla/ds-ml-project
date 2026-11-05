"""Time the final LightGBM (one fit + inference). TIMING ONLY: no metric is computed.

Why this file exists: the frozen comparison plan (model-comparison-plan.md, Resource Protocol) asks for
LightGBM's training time and inference latency on the same machine as the neural network. LightGBM was
never timed in the earlier notebooks, and the team decided not to re-score it (protocol.md, 2026-11-05).
So this script fits and predicts, but never reads the test labels and never computes a score.

Run with the MAIN project environment (LightGBM lives there, not in .venv-nn), from the repository root:
    .venv/bin/python lightgbm_timing.py
It is called from section 8 of 16_neural-network.ipynb and prints one JSON object.
"""
import json
import platform
import resource
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

FEATURE_DIR, MODEL_DIR = Path("data/features"), Path("models")
N_THREADS = 8      # all cores of the M2, same as the NN timing
N_REPEATS = 10     # inference: 1 warm-up + 10 timed repetitions (plan)

features = json.loads((MODEL_DIR / "selected_features_v3.json").read_text())["features"]
settings = json.loads((MODEL_DIR / "lightgbm_final_params.json").read_text())["settings"]

# ---- one training fit with the saved final settings on the 108,394 training clients ----
X_train = pd.read_csv(FEATURE_DIR / "X_train_v3.csv", index_col="client_id")[features]
y_train = pd.read_csv(FEATURE_DIR / "y_train.csv", index_col="client_id")["target"].astype(int)
model = lgb.LGBMClassifier(**settings, n_jobs=N_THREADS, verbose=-1)
t0 = time.perf_counter()
model.fit(X_train, y_train)
fit_seconds = time.perf_counter() - t0

# ---- inference with the saved final model on the 27,099 test clients (features only, no labels) ----
X_test = pd.read_csv(FEATURE_DIR / "X_valid_v3.csv", index_col="client_id")[features]
booster = lgb.Booster(model_file=str(MODEL_DIR / "lightgbm_final.txt"))
booster.predict(X_test, num_threads=N_THREADS)          # warm-up, not timed
times = []
for _ in range(N_REPEATS):
    t0 = time.perf_counter()
    booster.predict(X_test, num_threads=N_THREADS)       # scores are thrown away on purpose
    times.append(time.perf_counter() - t0)
times = np.array(times)
n = len(X_test)

print(json.dumps({
    "model": "LightGBM (final, feature set v3)",
    "lightgbm_version": lgb.__version__,
    "python": platform.python_version(),
    "threads": N_THREADS,
    "final_fit_seconds": fit_seconds,
    "n_train": int(len(X_train)),
    "n_test": int(n),
    "inference_repeats": N_REPEATS,
    "inference_batch_seconds_median": float(np.median(times)),
    "inference_batch_seconds_min": float(times.min()),
    "inference_batch_seconds_max": float(times.max()),
    "inference_ms_per_1000_median": float(np.median(times) / n * 1000 * 1000),
    "inference_ms_per_1000_min": float(times.min() / n * 1000 * 1000),
    "inference_ms_per_1000_max": float(times.max() / n * 1000 * 1000),
    "throughput_clients_per_second": float(n / np.median(times)),
    "model_file": "models/lightgbm_final.txt",
    "model_file_bytes": (MODEL_DIR / "lightgbm_final.txt").stat().st_size,
    "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024,  # macOS: bytes
    "note": "timing only; no metric computed, test labels not read",
}))
