# Model Decision Memo

Draft by Dhanya's Claude session on 2026-11-05, to be reviewed by Tim. Evidence: [model-comparison-report.md](model-comparison-report.md). Rules: [model-comparison-plan.md](model-comparison-plan.md) (frozen 2026-11-05).

## Recommendation

**Keep traditional ML: the existing LightGBM (feature set v3, 39 features).** The neural network is not adopted.

## Decision Context

STEG has a limited number of on-site inspections. The model ranks all clients by fraud risk and STEG visits the highest-ranked clients first, in batch (one list per inspection round). People affected: STEG's inspection teams and the clients who are visited. No money values for errors and no hard latency or hardware constraints were given; we use the top 10% of clients (2,710 of 27,099 test clients) as the assumed inspection capacity.

## Strongest Evidence

- **Ranking quality:** the NN's mean test ROC-AUC is 0.8736106260 against LightGBM's 0.881. The gap of −0.0074 is larger than the agreed practical difference (0.005) and about six times the NN's seed spread (0.0012), so it is not noise ([Predictive Results](model-comparison-report.md#predictive-results)).
- **No metric favours the NN:** PR-AUC 0.3503 vs. 0.371, and in the top-10% list it catches 854.33 fraud cases on average vs. 864. Under the frozen decision rule this is the "keep LightGBM" case, not a "further experiment" case.
- **No client group favours the NN:** a post-hoc check of 20 client groups shows the NN behind LightGBM in 19; after calibration both give equally reliable probabilities ([Post-hoc Analysis](model-comparison-report.md#post-hoc-analysis-calibration-and-subgroups)).
- **The comparison is fair to the NN:** same clients, same 39 features, same metric. The NN was tuned without seeing the test set. LightGBM's score is slightly optimistic, but the gap is larger than that bias is likely to be.

## Most Important Trade-Off

Keeping LightGBM gives the better ranking (about 10 more fraud cases found per 2,710 visits on this test set), a single model file, one Python environment, a 7-second retrain without a search, and established ways to explain scores to STEG. We give up the NN's advantages: about 3.6× faster inference including preprocessing (2.98 vs. 10.67 ms per 1,000 clients) and an 8× smaller model file. Both are irrelevant for a batch list that both models compute in under a second.

## Contradicting Evidence and Uncertainty

- The decision rule uses LightGBM's documented, rounded numbers. A post-hoc re-scoring on our rebuilt feature tables reproduced them (0.8805287085, 864 caught for seed 42).
- Calibration and subgroups were checked only after the test results were known (post-hoc), so they support but do not decide the recommendation.
- LightGBM was tuned on the test split, so its 0.881 is optimistic. On data unseen during tuning, the two are closer (LightGBM 5-fold CV 0.872 vs. NN inner validation 0.870, different splits).
- The NN search was bounded (30 trials, one inner split). 8 trials with low learning rates hit the 100-epoch limit. Other NN types for tabular data were not tried.
- Only 3 seeds; no error costs from STEG.

## Operating Conditions

- **Threshold:** no probability threshold. STEG inspects the top-ranked clients up to its capacity (assumed 10%); the cut-off follows from the capacity, not from a tuned score.
- **Scores as probabilities:** raw scores are strongly over-confident (balanced class weights). If STEG is shown a "fraud risk in %", use isotonic-calibrated scores (fitted on training-side data, as in notebook 17).
- **Infrastructure:** the existing Python 3.13 environment and `models/lightgbm_final.txt`; batch scoring per inspection round.
- **Human oversight:** inspectors decide on site. `n_counters` and `days_since_last_bill` may partly reflect STEG's own actions after a fraud was found, which should be checked with STEG before real use.
- **Monitoring:** hit rate of the top-ranked list per inspection round, score distribution and feature drift; known weak groups (young clients, short histories, low consumption) should be watched.
- **Retraining:** refit with the saved settings when new labelled inspections are available; re-tune only if the hit rate drops.

## Flip Conditions

- A re-scored or newly built NN reaches a mean ROC-AUC at least 0.005 above LightGBM's on the same frozen test set, beyond its seed spread, without losing PR-AUC or top-10% catch.
- STEG needs real-time scoring of very large volumes on limited hardware where the NN's faster inference and smaller file matter (not the case for batch lists).
- Much more or different data becomes available (for example raw bill sequences instead of aggregates), where sequence models could learn patterns the 39 features miss.
- STEG decides it cannot use any model it cannot fully audit. Then "no ML" or a simple rule would have to be evaluated with a metric, which was not done here.

## Next Decision Point

Tim reviews this draft and the report with the team. The next review is after the first inspection round with STEG feedback (real hit rates and capacity), or when the flip conditions above occur. The NN result is recorded in `results/` and notebook 16, so it can be reproduced then.
