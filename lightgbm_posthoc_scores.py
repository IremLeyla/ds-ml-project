"""LightGBM scores for the post-hoc calibration and subgroup analysis (17_calibration-subgroups.ipynb).

Why this file exists: LightGBM lives in the main environment (.venv, Python 3.13), the neural network in
.venv-nn. Notebook 17 needs LightGBM scores next to the NN scores. Team decision 2026-11-05 (protocol.md):
LightGBM is scored for this post-hoc analysis only; the main comparison keeps the documented scores.

IMPORTANT: models/lightgbm_final.txt is NOT used. Notebook 14 trained it on all 135,493 labelled clients,
including the 27,099 test clients, so its test scores would leak. Instead, LightGBM is refitted with the
saved final settings (models/lightgbm_final_params.json) exactly as in notebook 13:

  * test scores:        fit on the 108,394 training clients, predict the 27,099 test clients
  * calibration scores: fit on the inner FIT clients (80%), predict the inner VALIDATION clients (20%);
                        the inner split is read from the ids file written by notebook 17 (same split as the NN)

for seeds 42, 1 and 2. Run from the repository root with the main environment:
    .venv/bin/python lightgbm_posthoc_scores.py <inner_val_ids.csv> <output.csv>
The output (scores of test clients) goes to data/output/, which is not in git.
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import pandas as pd

FEATURE_DIR, MODEL_DIR = Path("data/features"), Path("models")
SEEDS = [42, 1, 2]
ids_file, out_file = Path(sys.argv[1]), Path(sys.argv[2])

features = json.loads((MODEL_DIR / "selected_features_v3.json").read_text())["features"]
settings = json.loads((MODEL_DIR / "lightgbm_final_params.json").read_text())["settings"]

X_train = pd.read_csv(FEATURE_DIR / "X_train_v3.csv", index_col="client_id")[features]
y_train = pd.read_csv(FEATURE_DIR / "y_train.csv", index_col="client_id")["target"].astype(int)
X_test = pd.read_csv(FEATURE_DIR / "X_valid_v3.csv", index_col="client_id")[features]

# the NN's inner split: validation ids from notebook 17, fit ids = the rest of the training clients
ival_ids = pd.read_csv(ids_file)["client_id"]
assert set(ival_ids) <= set(X_train.index) and len(ival_ids) == 21679
fit_mask = ~X_train.index.isin(ival_ids)

rows = []
for seed in SEEDS:
    params = {**settings, "random_state": seed}
    # 1) calibration scores: trained on the inner fit clients only
    m_inner = lgb.LGBMClassifier(**params, n_jobs=-1, verbose=-1).fit(X_train[fit_mask], y_train[fit_mask])
    rows.append(pd.DataFrame({"client_id": ival_ids, "part": "inner_val", "seed": seed,
                              "score": m_inner.predict_proba(X_train.loc[ival_ids])[:, 1]}))
    # 2) test scores: trained on all training clients (as in notebook 13)
    m_full = lgb.LGBMClassifier(**params, n_jobs=-1, verbose=-1).fit(X_train, y_train)
    rows.append(pd.DataFrame({"client_id": X_test.index, "part": "test", "seed": seed,
                              "score": m_full.predict_proba(X_test)[:, 1]}))
    print(f"seed {seed} done", flush=True)

out_file.parent.mkdir(parents=True, exist_ok=True)
pd.concat(rows, ignore_index=True).to_csv(out_file, index=False)
print(json.dumps({"lightgbm_version": lgb.__version__, "rows": int(sum(len(r) for r in rows)), "file": str(out_file)}))
