# Model Comparison Plan

**Status: FROZEN on 2026-11-05**, before any neural-network result on the test set exists. Changes after this date need a logged decision in [protocol.md](protocol.md) with a reason, and must be listed in the report. Decisions are logged in [protocol.md](protocol.md).

## Product Decision

- **Decision supported by the model:** which clients STEG inspects first. The model gives every client a fraud probability and STEG visits the highest-ranked clients (see [problem_framing.md](problem_framing.md)).
- **People or process affected:** STEG inspection teams (limited on-site visits) and the clients who are visited.
- **Cost of important errors:** a false alarm costs one wasted inspection visit; a missed fraud case is lost revenue. STEG has not given us money values for either, so we do not compute a cost. We use the top-10% inspection scenario (2,710 visits on the 27,099 test clients) as a business view. The 10% is our assumption for STEG's capacity, confirmed by the team because it matches the earlier notebooks.
- **Hard constraints:** none stated by STEG. We assume the scores are computed in batch (one priority list per inspection round), not in real time, confirmed by the team. The official Zindi metric is ROC-AUC.

## Candidate Systems

| Candidate | Role | Current evidence |
|---|---|---|
| No ML / rule | Not evaluated | Team decision 2026-11-05: no rule is built and no metric is computed. The decision memo discusses "no ML" in words only. |
| Historical traditional ML | Existing baseline | LightGBM, feature set v3 (39 features), final settings in `models/lightgbm_final_params.json`. Test-set scores (mean of seeds 42, 1, 2) taken from [model_results.md](model_results.md) and notebook 13: ROC-AUC 0.881, PR-AUC 0.371, top-10% inspection 864 of 1,513 fraud cases caught (seed 42). **Not re-scored** (team decision 2026-11-05). |
| Optional traditional ML | Not used | Team decision 2026-11-05: no extra tree challenger. |
| Neural network | New challenger | Keras/TensorFlow feed-forward MLP on the same 39 features. No results yet. |

## Frozen Data Protocol

- **Dataset version or hash:** Zindi STEG data, cleaned with [cleaning.py](cleaning.py) into `data/clean/`, features built with [features.py](features.py) (feature set v3, list in `models/selected_features_v3.json`). The raw data and the feature tables are not in git. SHA-256 (first 16 characters) of the feature tables as rebuilt on 2026-11-05 from the repo at commit `8423c50`: `X_train_v3.csv` 90e52789a4c4698a, `X_valid_v3.csv` 1a5ebdca6d5f2c2f, `y_train.csv` 5174ffcfe33498d9, `y_valid.csv` 1d12f28fd072ac98.
- **Target:** `target` (1 = fraud, 0 = not fraud), one row per client.
- **Training observations:** 108,394 clients, 6,053 fraud (5.584%). This is the 80% training split of notebook 06 (`train_test_split`, stratified on the target, `random_state=42`).
- **Validation or cross-validation strategy:** the neural network is tuned and stopped early only inside the 108,394 training clients, with one stratified 80/20 inner split (about 86,715 fit / 21,679 validation clients, seed 42), confirmed by the team instead of 5-fold CV, to keep the search affordable on a CPU. The final configuration is refit on all 108,394 training clients, with the number of epochs fixed from the inner validation.
- **Untouched test observations:** the 27,099 clients, 1,513 fraud (5.583%), of the 20% validation split of notebook 06, the same ones LightGBM was scored on. Zindi's own test set has no labels and is not used. The NN never sees them before the final evaluation.
- **Group or time constraints:** each client is one row, so the split is by client and all bills of a client are in the same part. The features aggregate the whole bill history of a client, up to 2019. We do not use a time-ordered split, because the Zindi train and test sets come from the same period.
- **Leakage checks:** (1) every learned preprocessing step (median imputation, scaling, rare-category grouping) is fitted on the training clients only; (2) no test client is used for early stopping, tuning or threshold choice; (3) the test row ids of the NN are checked to be identical to the LightGBM test ids (`y_valid.csv`); (4) `client_id` and `target` are not features. Known risk we cannot remove: `n_counters` and `days_since_last_bill` may partly reflect what STEG did after finding fraud (see [model_results.md](model_results.md)). Both models use them.

## Evaluation Protocol

- **Primary metric:** ROC-AUC (as in [protocol.md](protocol.md), 2026-10-21).
- **Secondary metrics:** PR-AUC, and the top-10% inspection scenario (clients with the 10% highest scores are flagged: fraud caught, hit rate, false alarms). F1, precision and recall at the F1-best threshold are shown only for comparison with `model_results.md`, never to choose between models. All values are reported unrounded in the report.
- **Practical difference required:** 0.005 ROC-AUC, and the difference must also be larger than the seed-to-seed spread of the neural network. LightGBM's three documented seeds range from 0.880 to 0.881, and its 5-fold CV standard deviation is about 0.003.
- **Subgroups or conditions:** none. Team decision 2026-11-05: only overall scores are compared. LightGBM's per-subgroup scores are not documented and we do not re-score it. The weak groups from the error analysis ([10_error-analysis.ipynb](10_error-analysis.ipynb)) are not checked for the NN.
- **Calibration or threshold plan:** the decision is a ranking, so calibration is not part of the core evaluation (team decision 2026-11-05). The operating point is the top-10% cut-off; we do not tune a probability threshold on the test set.
- **Repeated-run policy and seeds:** the final NN configuration is trained with 3 seeds (42, 1, 2, the same seeds as LightGBM). We report the mean, the minimum and maximum, and the standard deviation. The NN search uses seed 42 only.

## Resource Protocol

- **Hardware:** Mac with an Intel Core i7-9750H (6 cores), 32 GB RAM, CPU only, macOS (Darwin 24.6). The NN runs in a separate Python 3.12 environment with TensorFlow 2.16.2 and Keras 3.15 (`requirements-nn.txt`), because TensorFlow has no Intel-Mac wheels for the project's Python 3.13.
- **Tuning budget per challenger:** neural network: 30 random-search trials on the inner split, maximum 100 epochs each with early stopping (patience 10). This matches the 30 combinations of the LightGBM search (notebook 09). Search space (confirmed by the team): 1 to 3 hidden layers, 32 to 256 units, dropout 0 to 0.5, L2 1e-6 to 1e-3, learning rate 1e-4 to 1e-2 (log scale), batch size 256, 512 or 1024. Class weights "balanced", as for LightGBM (protocol 2026-10-21).
- **Training-time method:** wall-clock time of one final fit on the 108,394 training clients, and the total time of the search. LightGBM's training time was not recorded in the earlier notebooks, so we time one LightGBM fit with the saved final settings on the same machine (team decision 2026-11-05). This is a timing only, no metric is re-scored.
- **Inference workload, warm-up, and repetitions:** score the 27,099 test clients in one batch; one warm-up call, then 10 repetitions, report the median and the range, per 1,000 clients. The same method for LightGBM, using the saved `models/lightgbm_final.txt`; only the time is recorded, its scores are not recomputed.
- **Artifact-size or memory method:** size of the saved model file on disk (`models/lightgbm_final.txt` is 3.5 MB for LightGBM). Model files stay out of git.

## Expected Decision Rule

- **Favours the neural network:** its mean test ROC-AUC is at least 0.005 above LightGBM's 0.881, the gap is larger than its seed spread, and PR-AUC and the top-10% catch are not worse. We would also weigh the extra effort (second environment, longer training, harder to interpret).
- **Favours traditional ML (keep LightGBM):** the NN is below 0.886, or within the seed spread, or better on ROC-AUC but worse on PR-AUC or the top-10% catch. LightGBM is also simpler to run and easier to explain to STEG.
- **Favours no ML:** not tested with a metric. We would only consider it if neither model clearly helps STEG's inspections, which the existing results (ROC-AUC 0.88 versus 0.5 for a random list) do not suggest.
- **Further experiment:** the NN is clearly worse than the practical difference on one metric but better on another, or the gap is between 0 and 0.005 with a seed spread that overlaps. Then we name one experiment, for example a bigger search budget or learning curves.

## Known Limitations Before Training

- The test set is the 20% validation split. LightGBM's tuning and feature choices were made while looking at it, so its 0.881 is slightly optimistic. The NN is tuned without it, so the comparison tends to favour LightGBM.
- LightGBM is not re-scored. We rely on the documented scores. The documented per-seed numbers vary a little between notebooks (for example, caught fraud for seed 42 is 822 at the F1-best threshold in notebook 13 and 864 in the top-10% view).
- `n_counters` and `days_since_last_bill` may partly leak information that STEG only has after finding fraud. Both models use them.
- The NN search is bounded (30 trials, one inner split), so a better network may exist.
- Only 3 seeds, so the seed spread is rough.
- No subgroup analysis, so we cannot say whether the NN handles the weak groups of LightGBM (low consumption, long histories, young clients) better or worse.
- One machine, CPU only, and two different Python environments for the two models, so timings are indicative only.
- STEG did not give error costs or capacity numbers; the top-10% scenario is our assumption.
