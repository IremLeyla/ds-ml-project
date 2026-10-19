Why

# Problem Framing: Fraud Detection in Gas and Electricity

## Stakeholder

STEG (Société Tunisienne de l'Electricité et du Gaz), Tunisia's state electricity and gas utility. Its inspection teams are the practical users of the model.

## Value

- Find fraudulent consumers, for example tampered counters and misreported consumption.
- Reduce revenue loss caused by fraud.
- Target inspections: rank clients by fraud risk so that limited on-site visits go where fraud is most likely.

## Data

STEG's client and invoice history from 2005 to 2019.

- Client file: `Client_id`, `District`, `Client_catg`, `Region`, `Creation_date`, `Target`.
- Invoice file: one row per invoice, with tariff type, counter details, consumption levels 1 to 4, old and new index, and months billed.
- Invoices must be aggregated per client before modelling.

## Prediction task

Binary classification at client level.

- Target: `1` = fraud, `0` = not fraud.
- Output: a fraud probability per client, which also serves as an inspection priority score.

## Metrics

| Metric | Role | Why |
| --- | --- | --- |
| **AUC** (primary) | Official Zindi metric | Used by the Zindi leaderboard. Measures how well the model ranks fraudulent clients above honest ones, independent of a threshold. This matches the inspection-prioritisation use. |
| **PR-AUC** (average precision) | Our addition (imbalance check) | Area under the precision-recall curve. Like AUC it is threshold-independent, but it ignores true negatives and focuses on how well the rare fraud class is found. With only about 5.6% fraud, ROC-AUC can look good even when many flagged clients are honest, while PR-AUC drops. It shows whether the top of the ranking is really precise, which is what matters when inspections are limited. |
| **Precision** | Our addition (business view) | Of the clients flagged, how many are actually fraudulent. Each false positive costs an inspection visit. |
| **Recall** | Our addition (business view) | Of all fraudulent clients, how many are caught. Each miss is lost revenue. |
| **F1** | Our addition (business view) | Balances precision and recall at a chosen threshold. Fraud is likely rare, so accuracy would be misleading. |

Zindi scores only AUC. PR-AUC, precision, recall and F1 are not part of the competition. We add them to judge the model from STEG's side. The decision threshold for them depends on STEG's inspection capacity.

## Sources

- [Zindi data page](https://zindi.world/competitions/fraud-detection-in-electricity-and-gas-consumption-challenge/data)
- [Zindi competition page](https://zindi.world/competitions/fraud-detection-in-electricity-and-gas-consumption-challenge) (states AUC as the metric)
