# Model Results: Fraud Detection in Electricity and Gas Consumption

All models of the project, scored **the same way** on the **validation split** (27,099 clients, 1,513 of them fraud). Every model is trained on the training split (108,394 clients) and scored as the **mean of 3 seeds** (42, 1, 2). Precision, recall, F1 and the counts use the **F1-best threshold** of each model. Main metric: **ROC-AUC** (see [protocol.md](protocol.md)).

| Validation, mean of 3 seeds | ROC-AUC | PR-AUC | Precision | Recall | F1 | Caught | Missed | False alarms |
|---|---|---|---|---|---|---|---|---|
| Logistic regression baseline (nb 07), 57 cols | 0.757 | 0.156 | 0.154 | 0.433 | 0.227 | 655 | 858 | 3,593 |
| Random Forest, default, weighted (nb 08), 24 features | 0.743 | 0.143 | 0.155 | 0.391 | 0.221 | 592 | 921 | 3,255 |
| XGBoost, default, weighted (nb 08), 24 features | 0.743 | 0.157 | 0.165 | 0.356 | 0.226 | 539 | 974 | 2,725 |
| LightGBM, default, weighted (nb 08), 24 features | 0.767 | 0.178 | 0.164 | 0.445 | 0.240 | 673 | 840 | 3,429 |
| LightGBM, tuned (nb 09 settings), 24 features | 0.774 | 0.184 | 0.201 | 0.344 | 0.252 | 521 | 992 | 2,109 |
| LightGBM, nb 09 settings, 30 features (feature set v2, nb 11) | 0.858 | 0.317 | 0.330 | 0.446 | 0.378 | 674 | 839 | 1,383 |
| LightGBM, v2 settings, 30 features (nb 12) | 0.859 | 0.324 | 0.325 | 0.467 | 0.383 | 706 | 807 | 1,470 |
| LightGBM, v2 settings, 27 base (nb 13) | 0.859 | 0.326 | 0.324 | 0.454 | 0.378 | 687 | 826 | 1,432 |
| **Final: LightGBM, v2 settings, 39 features (feature set v3, nb 13)** | **0.881** | **0.371** | **0.367** | **0.504** | **0.424** | **763** | **750** | **1,325** |

## What changed at each step

| Step | Change | ROC-AUC |
|---|---|---|
| Baseline | logistic regression, class weights, 57 scaled and one-hot columns | 0.757 |
| Model choice | four default models compared with 5-fold CV; LightGBM wins | 0.767 |
| Tuning | random search for LightGBM (30 combinations, 5-fold CV) | 0.774 |
| Feature set v2 | + time features (client age, history, gaps between bills) and meter features (`n_counters`), − level max columns | **0.858** |
| Re-tuning | new random search on the 30 features (v2 settings) | 0.859 |
| Feature set v3 | − 3 unused columns, + 12 features: meter-setup diversity (`n_codes`, `n_remarque`, `n_tarif`, `remarque_8_share`), consumption shape, time activity | **0.881** |
| Tuning on 39 features | new random search found no better settings, so the v2 settings stay | 0.881 |

The big steps came from the **features** (+0.084 and +0.022), not from the model settings (+0.007 and +0.001).

## Other views on the final model

| Check | Result |
|---|---|
| 5-fold CV on the training split | ROC-AUC 0.848 → **0.872** (27 base → 39 features), better in 5 of 5 folds |
| CV on all 135,493 labelled clients (nb 14) | ROC-AUC **0.876** (± 0.003), PR-AUC 0.355 |
| Inspection scenario: top 10% flagged (2,710 visits, seed 42) | **864 of 1,513 fraud cases caught (57%)**, hit rate 32% (first model, nb 10: 517 caught, 34%) |
| **Zindi public score** (test set, 2026-10-22) | **ROC-AUC 0.8738**, within 0.003 of the CV estimate (0.876) |

## Compared with published solutions (same STEG data)

| Solution | ROC-AUC |
|---|---|
| 4th place, original challenge (AI Hack Tunisia 2019, team GORNYAKI, LightGBM) | 0.883 (public leaderboard) |
| **Our final model** | **0.874 (public leaderboard)** |
| Top 25% (AmirFARES, XGBoost) | 0.864 (self-reported) |
| Our first tuned model (24 features) | 0.774 (validation) |
| Zindi benchmark | 0.500 |

Sources: [imgremlin/Fraud-Detection-by-Zindi](https://github.com/imgremlin/Fraud-Detection-by-Zindi), [AmirFARES/Tunisia_Energy_Fraud_Detection_STEG](https://github.com/AmirFARES/Tunisia_Energy_Fraud_Detection_STEG). The first-place score was not published. Leaderboards of different competition rounds use different parts of the test set, so the comparison is approximate.

## Keep in mind

- **The threshold is chosen on validation.** Precision, recall, F1 and the counts use the F1-best threshold of each model on the validation split, so they are slightly optimistic. ROC-AUC and PR-AUC do not depend on a threshold.
- **The counts depend on the threshold.** Each model has its own F1-best threshold, so "caught" and "false alarms" move together. Compare models by ROC-AUC and PR-AUC first.
- **Possible leakage in two strong features.** `n_counters` (meter replacements) and `days_since_last_bill` (inactive accounts) may partly reflect what STEG did *after* finding fraud, or which accounts it inspects. Both help the Zindi score (the test set has the same pattern), but they are a question for STEG.
- **Numbers can differ slightly from the notebooks.** Some notebooks report one seed or a different column order; this table refits every model the same way.
