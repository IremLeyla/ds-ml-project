# Fraud Detection: EDA Hypotheses

Guesses about what fraud might look like. Each one is checked in EDA (fraud vs non-fraud), and the ones that hold up become features.

| # | Hypothesis | Columns | How to check | Possible feature |
|---|-----------|---------|--------------|------------------|
| 1 | Fraud rate differs by **region** | `region`, `disrict` (client file, spelled this way in the data) | Fraud rate per region | Region as categorical |
| 2 | A **sudden, drastic change in consumption** indicates fraud | `consommation_level_1-4`, `invoice_date` | Compare consumption over time for fraud vs non-fraud clients | Per-client max drop, std, trend |
| 3 | Consumption **only in consommation level 1** indicates fraud | `consommation_level_1-4` | Share of level 1 in total consumption per client | Level-1 share, count of level-1-only invoices |
| 4 | **Zero or very low consumption** over many invoices indicates fraud | `consommation_level_1-4` | Count of zero-consumption invoices per client | Zero-consumption count and ratio |
| 5 | **Index mismatch**: `new_index − old_index` differs from the sum of consumption levels | `old_index`, `new_index`, `consommation_level_1-4` | Share of mismatching invoices per client (about 0.4% of rows overall) | Mismatch count and ratio |

## Other ideas to test later
- Tariff type (`tarif_type`) and fraud rate
- Meter type (ELEC vs GAZ) and number of meters per client
- Meter status/code and reading remarks
- Unusual `months_number` or billing gaps

## Notes
- Invoices are many rows per client, so aggregate to one row per client (mean, median, max, min, std, counts).
- Don't remove outliers: they may be the fraud.
- Keep a validation split from the train set (test has no labels).
