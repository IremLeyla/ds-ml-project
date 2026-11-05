# Model Comparison Report

LightGBM (historical baseline) vs. a Keras feed-forward neural network on the STEG fraud data. Draft by Dhanya's Claude session on 2026-11-05, to be reviewed by Tim. Decision: [decision-memo.md](decision-memo.md).

**Short answer:** the neural network is good but does not beat LightGBM. Its mean test ROC-AUC is **0.8736106260** against LightGBM's documented **0.881**: 0.0074 lower, which is more than the practical difference of 0.005 and six times the NN's seed spread. It is also lower on PR-AUC and catches 9.7 fewer fraud cases in the top-10% inspection list. Under the frozen decision rule the result favours keeping LightGBM.

## Scope and Protocol

The rules were frozen in [model-comparison-plan.md](model-comparison-plan.md) on 2026-11-05, before any NN result existed. The final NN configuration was committed (`7d84039`) before the test set was scored, and the test set was scored once. All team decisions are in [protocol.md](protocol.md).

**Deviations from the frozen plan** (all logged in `protocol.md`, 2026-11-05):

| Deviation | Why | Does it weaken the evidence? |
|---|---|---|
| **Feature tables.** The NN uses the v3 tables rebuilt on Dhanya's Apple M2. Their SHA-256 values differ from the plan (`X_train_v3` 1cf6b683d2da1516 vs. 90e52789a4c4698a, `X_valid_v3` 5f880604ffea81e0 vs. 1a5ebdca6d5f2c2f). The labels match (`y_train` 5174ffcfe33498d9, `y_valid` 1d12f28fd072ac98), so clients, split and target are the same. | Rebuilt twice from today's code with identical results; probably floating-point differences between Intel and Apple-silicon CPUs. Agreed with Tim. | No, as far as we can check: LightGBM re-scored post-hoc on the rebuilt tables gives the documented numbers (0.8805287085 ROC-AUC, 864 caught for seed 42). The tables were not compared value by value. |
| **Hardware.** NN training and both timings run on an Apple M2 (8 cores, 8 GB RAM, macOS 26.2), not on the Intel i7 (32 GB) named in the plan. | The planned machine was not available. | No for the scores. Timings are not comparable with any number measured on the Intel machine; both models were timed on the M2. |
| **Parallel search.** The 30 trials ran in 4 processes × 2 threads at a time. | Cut the search from about 26 min to 7.3 min. | No. Same 30 settings, seed and split. A trial can differ from a single-process run in the last decimals. |
| **Authorship.** Notebook sections 1–9 and this report were written by Dhanya's Claude session (Tim's draft of sections 1–4 was never pushed). | Workflow. | No, but Tim's planned preprocessing was not available; the preprocessing follows the plan's description. |

## Reproducibility Record

| Item | Historical ML (LightGBM) | Optional ML challenger | Neural network (MLP) |
|---|---|---|---|
| Code location | Notebooks [13](13_diversity-features.ipynb) (scores) and [14](14_final-model-submission.ipynb); timing: [lightgbm_timing.py](lightgbm_timing.py) | Not applicable: no extra tree challenger (team decision 2026-11-05) | [16_neural-network.ipynb](16_neural-network.ipynb), [nn_pipeline.py](nn_pipeline.py) |
| Data and split | Feature set v3 (39 features, `models/selected_features_v3.json`); train 108,394 clients, test 27,099 (20% stratified split of notebook 06, `random_state=42`) | – | Same 39 features, same clients (test ids asserted equal to `y_valid.csv`); tables rebuilt on the M2 (see deviations) |
| Preprocessing | None (trees use raw values and handle missing values) | – | Fitted on training clients only: median imputation → `log1p` on 30 skewed non-negative columns → standardisation; one-hot for `tarif_type`, `client_catg`, `region` (levels < 1% grouped). 62 input columns |
| Main hyperparameters | `models/lightgbm_final_params.json`: 289 trees, learning rate 0.0271, 111 leaves, min_child_samples 250, subsample 0.859, colsample 0.662, reg_lambda 0.0123, class weight balanced | – | `results/nn_final_config.json`: 2 hidden layers × 156 units, ReLU, dropout 0.3930321526384769, L2 2.4229301715750363e-06, Adam lr 0.0007957412573105, batch 1024, 32 epochs, class weight balanced, sigmoid output |
| Seeds | 42, 1, 2 | – | Search 42; final 42, 1, 2; TensorFlow op determinism on |
| Software and hardware | Python 3.13.18, LightGBM 4.7.0; scores from the team's earlier runs, timing on the M2 | – | Python 3.12.14, TensorFlow 2.16.2, Keras 3.15.1, scikit-learn 1.9.1, pandas 3.0.6, numpy 1.26.4; Apple M2, CPU only (`results/nn_environment.json`) |
| Tuning budget | 30 random-search combinations (notebook 09) plus a second search on the 39 features (notebook 13); **tuned and selected while looking at this test split** | – | 30 random-search trials, inner stratified 80/20 split of the training clients, ≤ 100 epochs, early stopping patience 10 (`results/nn_search_trials.csv`). **Test split never used before the final scoring** |

## Predictive Results

Test set: 27,099 clients, 1,513 fraud. NN numbers are unrounded (`results/nn_final_runs.csv`). LightGBM numbers are the documented ones (`model_results.md`, notebook 13), rounded to 3 decimals there and **not re-scored** (team decision).

| Evidence | Historical ML (LightGBM) | Optional ML challenger | Neural network (MLP) |
|---|---|---|---|
| Primary metric: ROC-AUC | **0.881** (mean of 3 seeds; seeds range 0.880–0.881) | Not applicable | **0.8736106260** (mean); seeds 0.8735311838 / 0.8730556289 / 0.8742450651 |
| Secondary: PR-AUC | 0.371 | Not applicable | 0.3502542958 (mean); 0.3493123661 / 0.3505757862 / 0.3508747351 |
| Secondary: top-10% list (2,710 visits) | 864 of 1,513 caught (57.1%, seed 42), hit rate 0.3188, 1,846 false alarms, 649 missed | Not applicable | 854.33 caught on average (852 / 851 / 860, 56.5%), hit rate 0.3152521525, 1,855.67 false alarms, 658.67 missed |
| For reference only: F1-best threshold | precision 0.367, recall 0.504, F1 0.424 | Not applicable | precision 0.3611531782, recall 0.4877726371, F1 0.4147484857 (means) |
| Variability | Seeds 0.880–0.881; 5-fold CV std ≈ 0.003 | Not applicable | ROC-AUC std 0.0005986843, spread (max − min) 0.0011894362; top-10% catch std 4.93 |
| Practical difference | Reference | Not applicable | NN − LightGBM: ROC-AUC **−0.0073893740** (−0.84%), PR-AUC −0.0207457042 (−5.6%), top-10% −9.67 cases (−1.1%). The gap exceeds 0.005 and the seed spread, **in LightGBM's favour** |
| Calibration (post-hoc, see below) | Raw: Brier 0.107055, ECE 0.184894 (over-confident). After isotonic calibration: Brier 0.042301, log loss 0.153947, ECE 0.005425 | Not applicable | Raw: Brier 0.145753, ECE 0.252584 (more over-confident). After isotonic calibration: Brier 0.042909, log loss 0.156741, ECE 0.005199 |
| Costly errors | Top-10%: 649 missed fraud, 1,846 wasted visits (seed 42) | Not applicable | Top-10%: 661 missed, 1,858 wasted visits (seed 42); see Error Analysis |
| Subgroups / conditions (post-hoc, see below) | Weakest: clients inactive 1–5 years (ROC-AUC 0.815695), history Q3 (0.838703), category 51 (0.848018) | Not applicable | Below LightGBM in 19 of 20 groups with ≥ 50 fraud cases; largest gaps for short histories (−0.020716) and young clients (−0.012437); ahead only in category 51 (+0.012307) |

**Fairness of the comparison.** LightGBM's 0.881 is slightly optimistic, because its features and settings were chosen while looking at this split; the NN never saw it. A view on unseen-during-tuning data for both: LightGBM's 5-fold CV on the training clients was 0.872, the NN's best inner-validation ROC-AUC was 0.8701646945. These are different splits, so this is only an indication, but it also does not show the NN ahead.

## System Results

Same machine for both (Apple M2, 8 threads, CPU only), two Python environments, one batch of 27,099 clients, 1 warm-up + 10 repetitions (`results/nn_timing.csv`).

| Evidence | Historical ML (LightGBM) | Optional ML challenger | Neural network (MLP) |
|---|---|---|---|
| Final training time (one fit, 108,394 clients) | 7.173105791 s | Not applicable | 11.277063417 s (seed 42); 15.43 s and 15.66 s for seeds 1 and 2 |
| Total tuning effort | Not recorded in the earlier notebooks (30 + 1 searches with 5-fold CV) | Not applicable | 30 trials: 440.89 s wall time with 4 workers; 1,582.82 s summed over trials |
| Median / tail inference latency, per 1,000 clients | 10.6698 ms median (min 9.6059, max 11.2487); 0.289 s per batch | Not applicable | Model only: 2.0443 ms median (min 1.8914, max 3.2906). With preprocessing: 2.9834 ms (min 2.9140, max 3.4562); 0.055 s per batch (model only) |
| Throughput | 93,723 clients/s | Not applicable | 335,190 clients/s (incl. preprocessing) |
| Artifact size | 3,523,429 bytes (`lightgbm_final.txt`) | Not applicable | 444,218 bytes (`nn_seed42.keras`) + 5,865 bytes fitted preprocessing |
| Hardware / memory | CPU; peak RSS 313 MB for fit + inference script; main project environment | Not applicable | CPU; peak RSS ≤ 872 MB (whole notebook process, upper bound); needs TensorFlow in a separate Python 3.12 environment |

Both models score the whole test set in well under a second, so for a batch inspection list neither latency matters. The NN is faster at inference and its file is smaller; LightGBM trains faster and needs far less tuning.

## Required Comparison Table

The summary table of course handout 05. The no-ML option is compared in words only (team decision 2026-11-05: no rule is built and no metric is computed for it).

| Dimension | Historical ML (LightGBM) | Optional ML challenger | Neural network (MLP) | No ML / rule |
|---|---|---|---|---|
| Primary metric (test ROC-AUC) | 0.881 (documented) | Not applicable: none built (team decision) | 0.8736106260 (mean of 3 seeds) | Not measured. A random inspection list has ROC-AUC 0.5 by definition |
| Practical difference reached? | Reference | – | Yes, but **against** the NN: −0.0074 (threshold 0.005, seed spread 0.0012) | – |
| Costly error profile | Top-10%: 649 missed, 1,846 false alarms (seed 42) | – | 658.67 missed, 1,855.67 false alarms (mean); misses young clients with short histories, like LightGBM | Random 10% list would catch about 151 of 1,513 fraud cases (5.6% hit rate) |
| Calibration / probability quality | Raw scores over-confident (Brier 0.107); well calibrated after isotonic calibration (Brier 0.0423, ECE 0.0054) | – | Raw scores more over-confident (Brier 0.146); after isotonic calibration on par (Brier 0.0429, ECE 0.0052) | Not applicable |
| Stability across runs | Seeds 0.880–0.881; CV std ≈ 0.003 | – | ROC-AUC std 0.0005986843 | Not applicable |
| Training and tuning effort | 7.17 s per fit; 30-combination search + re-search (time not recorded) | – | 11.28 s per fit; 30-trial search 440.9 s wall (1,582.8 s summed) | None, but rules need expert time to define |
| Inference latency and throughput | 10.67 ms per 1,000 clients; 93,723 clients/s | – | 2.98 ms per 1,000 incl. preprocessing; 335,190 clients/s | Instant |
| Model size and hardware | 3.5 MB; CPU; main environment | – | 0.44 MB + preprocessing; CPU; separate TensorFlow environment | None |
| Interpretability and auditability | Good (importances, SHAP available, readable settings) | – | Weaker (black box, needs extra tooling) | Best: a rule can be read by anyone |
| Maintenance and monitoring | Low: one file, one environment, fixed settings | – | Higher: preprocessing + model + TensorFlow version, input drift on scaled features | Low, but rules go stale as fraud patterns change |
| Product value and risk | Best ranking found; the known leakage risk of two features applies | – | Slightly fewer fraud cases found per visit; same leakage risk | Much lower hit rate than either model, likely more wasted visits |
| Evidence confidence | Medium-high (documented, slightly optimistic) | – | Medium-high (frozen protocol, 3 seeds, one search) | Low (not measured) |

## Post-hoc Analysis: Calibration and Subgroups

Added on 2026-11-05 **after** the NN test results were known (team decision, logged in `protocol.md`; it changes the plan's "no calibration, no subgroups, no re-scoring" rows for this analysis only). Code: [17_calibration-subgroups.ipynb](17_calibration-subgroups.ipynb), [lightgbm_posthoc_scores.py](lightgbm_posthoc_scores.py). Results: `results/posthoc_calibration.csv`, `results/posthoc_subgroups.csv`. **This evidence describes the models; it does not change the decision rule**, which stays on the documented LightGBM scores.

**LightGBM scores for this analysis.** `models/lightgbm_final.txt` cannot be used for test scores: notebook 14 trained it on all 135,493 labelled clients, **including the 27,099 test clients**. LightGBM was therefore refitted with the saved final settings on the 108,394 training clients (seeds 42, 1, 2), as in notebook 13. This re-run on the M2 feature tables gives ROC-AUC **0.8805287085**, PR-AUC **0.3706576555** (means) and **864** caught in the top 10% for seed 42 (859 and 875 for seeds 1 and 2), the same as the documented numbers. So the different feature-table hashes (deviation 1) do not affect LightGBM's score.

### Calibration

Both models use balanced class weights, which help ranking but push every score up. Means over 3 seeds on the test clients (observed fraud rate 0.0558; always predicting it gives Brier 0.0527):

| | Brier | Log loss | ECE (10 bins) | Mean score | ROC-AUC |
|---|---|---|---|---|---|
| LightGBM, raw | 0.107055 | 0.334536 | 0.184894 | 0.240727 | 0.880529 |
| LightGBM, isotonic | **0.042301** | **0.153947** | 0.005425 | 0.058394 | 0.879849 |
| NN, raw | 0.145753 | 0.444114 | 0.252584 | 0.308417 | 0.873611 |
| NN, isotonic | 0.042909 | 0.156741 | **0.005199** | 0.059080 | 0.872711 |

- **Raw scores are not probabilities.** Both models are strongly over-confident: their raw Brier scores are worse than always predicting the base rate, and a client with a raw score of 0.8 is fraud only about 30% of the time (reliability curve in notebook 17). The NN is more over-confident than LightGBM.
- **Isotonic calibration fixes it for both.** It was fitted on the inner validation clients (training side only) and applied once to the test clients. Afterwards both are well calibrated (ECE about 0.005) and nearly equal; LightGBM is slightly better on Brier and log loss. Calibration costs a little ROC-AUC (−0.0007 for LightGBM, −0.0009 for the NN) because the step function creates ties.
- For STEG's top-10% list calibration does not matter (only the order counts). It matters if scores are shown as "fraud risk in %" or used to plan expected recoveries: then a calibrated score must be used.

### Subgroups

Groups and bins were defined before any subgroup score was computed (client category, region group, gas bills, quartiles of client age, history length and consumption from the training clients, inactivity). Means over 3 seeds; `catch` = share of the group's fraud that is in the overall top-10% list. Groups with fewer than 50 fraud cases (category 12, region 2xx, inactive > 5 years) are noisy and left out of the statements below.

| Group | Fraud cases | LightGBM ROC-AUC | NN ROC-AUC | NN − LightGBM (seed std) | LightGBM catch | NN catch |
|---|---|---|---|---|---|---|
| All test clients | 1,513 | 0.880529 | 0.873611 | −0.006918 | 0.572 | 0.565 |
| Client category 51 | 63 | 0.848018 | 0.860324 | **+0.012307** (0.0028) | 0.841 | 0.794 |
| Electricity only | 601 | 0.888250 | 0.883310 | −0.004940 (0.0018) | 0.537 | 0.543 |
| Has gas bills | 912 | 0.863282 | 0.851836 | −0.011446 (0.0009) | 0.596 | 0.579 |
| Client age Q1 (< 7.8 years) | 227 | 0.860952 | 0.848514 | −0.012437 (0.0042) | 0.382 | 0.360 |
| History length Q1 (< 3.3 years) | 89 | 0.911382 | 0.890666 | **−0.020716** (0.0061) | 0.236 | 0.176 |
| History length Q3 (9.3–13.3 years) | 577 | 0.838703 | 0.838318 | −0.000385 (0.0015) | 0.571 | 0.593 |
| History length Q4 (> 13.3 years) | 524 | 0.875871 | 0.863928 | −0.011943 (0.0010) | 0.707 | 0.684 |
| Consumption Q1 (mean < 235) | 244 | 0.902097 | 0.894981 | −0.007116 (0.0019) | 0.522 | 0.506 |
| Inactive 1–5 years | 264 | 0.815695 | 0.809233 | −0.006462 (0.0029) | 0.487 | 0.437 |

All 23 groups are in `results/posthoc_subgroups.csv`.

- **The NN is behind LightGBM in 19 of the 20 groups** with at least 50 fraud cases. The only group where it ranks better is client category 51 (+0.0123 ROC-AUC), but even there its top-10% list catches fewer cases (79.4% vs. 84.1%). There is no client group where switching to the NN would clearly help.
- **The NN loses most where data per client is thin:** short histories (−0.0207) and young clients (−0.0124), plus clients with gas bills and long histories (about −0.011 each).
- **Weak groups for both models** (where STEG's list is least useful): clients inactive for 1–5 years (ROC-AUC about 0.81), mid-length histories, and young clients and short histories in the top-10% list: only 18–38% of their fraud is caught, against 57% overall. This confirms the weak groups of [notebook 10](10_error-analysis.ipynb).
- Within-group ROC-AUC can be higher than overall (for example short histories, 0.91) while the catch rate is very low: the model ranks these clients well among themselves, but their scores are lower than those of other groups, so few make the overall top-10% list.

## Error Analysis

From [notebook 16, section 7](16_neural-network.ipynb), seed 42, top-10% list (descriptive only, nothing was tuned on it):

- **Missed fraud** (661 cases) looks **younger and shorter-lived** than caught fraud: median client age 13.2 vs. 20.2 years, history 11.0 vs. 13.2 years, 38 vs. 49 bills, and fewer counters (2 vs. 2.5). These are the same weak groups found for LightGBM in [notebook 10](10_error-analysis.ipynb) (young clients, little bill history). The NN does not fix them.
- **False alarms** (1,858) look like caught fraud on almost every feature in the table (long histories, about 2 counters, similar consumption), so the model cannot separate them with these features. Some may be undetected fraud (labels only show detected fraud).
- Most missed fraud is **not just below the cut-off**: the median score of missed fraud is 0.547 against a cut-off of 0.758; only the top 10% of missed cases score above 0.73.
- **Evidence against LightGBM:** the NN is faster at inference and 8× smaller on disk, and its seeds vary very little (ROC-AUC std 0.0006). None of these matter much for a batch list.

## Operating and Governance Assessment

| Aspect | LightGBM | Neural network |
|---|---|---|
| Interpretability | Feature importance and per-client explanations (SHAP) are standard; the team already used importances to discuss `n_counters` and `days_since_last_bill` | Harder to explain to STEG; would need SHAP/permutation methods that were not built |
| Auditability | One model file with readable trees and saved settings | Model file + fitted preprocessing + TensorFlow version must be kept together |
| Retraining | One fit (7 s); settings fixed | Preprocessing refit + fixed-epoch training (11–16 s); epochs are tied to the current data size, a re-search may be needed if data changes |
| Monitoring | Score distribution and top-10% hit rate per inspection round | The same, plus input-scale drift (standardisation and log transforms assume the training ranges) |
| Skills and dependencies | Main project environment (Python 3.13) | Second environment (Python 3.12, TensorFlow 2.16.2) because of TensorFlow's platform support |
| Affected groups and oversight | Both rank clients for inspection; inspectors decide on site. Both rely on `n_counters` and `days_since_last_bill`, which may partly reflect STEG's own actions after a fraud was found. Post-hoc subgroup check: both are weakest for young clients, short histories and clients inactive 1–5 years, so these clients are under-represented in the inspection list | Same weak groups, and slightly weaker than LightGBM in 19 of 20 groups |

## Limitations and Missing Evidence

- The decision rule uses LightGBM's rounded documented numbers (±0.0005). The post-hoc re-scoring on the M2 tables (0.8805287085 / 0.3706576555 / 864) matches them, so this does not change the conclusion.
- Calibration and subgroups were added **after** the test results were known (post-hoc). The subgroups were defined before computing their scores, but the decision to look at them was not pre-registered. Several groups have few fraud cases; 3 groups with fewer than 50 are not interpreted.
- The isotonic calibration was fitted on models trained on 80% of the training clients and applied to models trained on 100%; this small mismatch is common practice but not tested.
- LightGBM's 0.881 is optimistic (tuned on this split); the comparison favours LightGBM. The gap (0.0074) is larger than this bias is likely to be, but the bias was not measured.
- Feature tables rebuilt on another CPU type; not compared value by value with the tables behind LightGBM's scores.
- Bounded NN search (30 trials, one inner split); 8 of 30 trials, all with low learning rates, reached the 100-epoch limit without stopping, so slow-learning settings may be under-explored. The top 5 trials lie within 0.0006 inner ROC-AUC, so the search had reached a plateau for the faster settings.
- Only 3 seeds; the seed spread is a rough estimate.
- No extra tree challenger and no metric for a no-ML rule (team decisions 2026-11-05).
- Timings are indicative only: one machine, two Python environments, single runs of each fit. LightGBM's tuning time was never recorded.
- STEG gave no error costs or inspection capacity; the top-10% scenario is our assumption.

## Traceable Findings

| Finding | Evidence | Interpretation | Confidence | Open question |
|---|---|---|---|---|
| NN ROC-AUC is 0.0074 below LightGBM | `results/nn_final_runs.csv`; `model_results.md` | Exceeds the 0.005 practical difference and the NN seed spread (0.0012) → favours LightGBM | High (re-scored LightGBM on the M2 tables matches the documented score; remaining doubt: LightGBM's tuning bias) | – |
| Raw scores of both models are over-confident; isotonic calibration fixes both | `results/posthoc_calibration.csv`, notebook 17 | Use calibrated scores whenever a score is read as a probability | Medium (post-hoc, one calibration method) | – |
| NN is not better in any client group except category 51 (63 fraud cases) | `results/posthoc_subgroups.csv` | No group-specific reason to deploy the NN | Medium (post-hoc, groups of different size) | – |
| Both models are weak for young clients, short histories, clients inactive 1–5 years | same | A limit of the bill-based features, not of the model family | Medium | Can STEG add other signals (inspection history, meter type) for these clients? |
| NN is also worse on PR-AUC (−0.0207) and top-10% catch (−9.67) | same | No metric where the NN is better → no "further experiment" case under the plan | High | – |
| NN results are stable across seeds | std 0.0006 ROC-AUC | The gap is not a seed effect | Medium (3 seeds) | – |
| Search reached a plateau | `results/nn_search_trials.csv` (top 5 within 0.0006) | A bigger search of the same space is unlikely to close a 0.0074 gap | Medium | Would other architectures (embeddings, tabular-specific NNs) help? Out of scope |
| NN misses the same groups as LightGBM | notebook 16 §7, notebook 10 | The missing signal is in the data, not in the model family | Medium (descriptive, one seed) | – |
| NN is faster and smaller at inference, slower to tune | `results/nn_timing.csv` | Irrelevant for a batch list; tuning effort and second environment count against the NN | Medium (single machine) | – |
