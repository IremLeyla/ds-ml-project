"""Rebuild the feature tables v2 and v3 (the 39 features of the final LightGBM).

Why this file exists: data/ is not in git (competition rules), and the v2/v3 tables are written by
notebooks 11 and 13. This script repeats exactly those steps without any model, so a teammate can
rebuild the tables from the cleaned data and the v1 tables (notebooks 02 and 06) in one go.

Run from the repository root with the main project environment:
    .venv/bin/python build_feature_tables.py

Needs:   data/clean/*.csv (notebook 02) and data/features/X_{train,valid,test}.csv, y_{train,valid}.csv (notebook 06)
Writes:  data/features/X_{train,valid,test}_v2.csv and X_{train,valid,test}_v3.csv
Prints:  the shape and a SHA-256 of every v3 table, to compare with model-comparison-plan.md
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

from features import build_diversity_features, build_extra_features

FEATURE_DIR, CLEAN_DIR, MODEL_DIR = Path("data/features"), Path("data/clean"), Path("models")


def load(name):
    # one feature table with client_id as the index
    return pd.read_csv(FEATURE_DIR / f"{name}.csv", index_col="client_id")


# v1 tables from notebook 06 (the 80/20 split, stratified, random_state=42, is already inside them)
X_train, X_valid, X_test = load("X_train"), load("X_valid"), load("X_test")

# cleaned tables from notebook 02, read as in notebook 11 (v2 features)
client_train = pd.read_csv(CLEAN_DIR / "client_train_clean.csv", parse_dates=["creation_date"])
invoice_train = pd.read_csv(CLEAN_DIR / "invoice_train_clean.csv", parse_dates=["invoice_date"], low_memory=False)
client_test = pd.read_csv(CLEAN_DIR / "client_test_clean.csv", parse_dates=["creation_date"])
invoice_test = pd.read_csv(CLEAN_DIR / "invoice_test_clean.csv", parse_dates=["invoice_date"], low_memory=False)

# v2: time and meter features, joined client by client (train and valid clients both come from the Zindi train set)
extra_train = build_extra_features(client_train, invoice_train)
extra_test = build_extra_features(client_test, invoice_test)
v2 = {"train": X_train.join(extra_train), "valid": X_valid.join(extra_train), "test": X_test.join(extra_test)}

# v3: diversity features (notebook 13 reads the clean client tables without parse_dates)
new_train = build_diversity_features(pd.read_csv(CLEAN_DIR / "client_train_clean.csv"), invoice_train)
new_test = build_diversity_features(pd.read_csv(CLEAN_DIR / "client_test_clean.csv"), invoice_test)
v3 = {"train": v2["train"].join(new_train), "valid": v2["valid"].join(new_train), "test": v2["test"].join(new_test)}

# the 39 final columns must be the saved list, in the saved order
v2_columns = json.loads((MODEL_DIR / "selected_features.json").read_text())["features"]
dropped = ["coef_not1_share", "has_backward", "backward_count"]
all_39 = json.loads((MODEL_DIR / "selected_features_v3.json").read_text())["features"]
assert all_39 == [c for c in v2_columns if c not in dropped] + list(new_train.columns), "feature list differs"
assert len(v3["train"]) == 108394 and len(v3["valid"]) == 27099 and len(v3["test"]) == 58069, "unexpected row counts"

for part in v2:
    v2[part].to_csv(FEATURE_DIR / f"X_{part}_v2.csv")
    v3[part].to_csv(FEATURE_DIR / f"X_{part}_v3.csv")

for part in v3:
    path = FEATURE_DIR / f"X_{part}_v3.csv"
    print(f"{path.name}: {v3[part].shape}, sha256 {hashlib.sha256(path.read_bytes()).hexdigest()[:16]}")
