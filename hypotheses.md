# Fraud Detection: EDA Hypotheses

Guesses about what fraud might look like. Each one is checked in EDA (fraud vs non-fraud), and the ones that hold up become features. The tests are in [03_eda-analysis.ipynb](03_eda-analysis.ipynb), in the same order and with the same numbers. Overall fraud rate in train: **5.6%**.

**Gas vs electricity:** [04_hypotheses-gas-vs-elec.ipynb](04_hypotheses-gas-vs-elec.ipynb) repeats every test separately for ELEC and GAZ (features calculated only from the bills of one meter). The label belongs to the client, so we cannot say which meter was manipulated. Gas rates in 07 rest on smaller groups. Results from 07 are marked "(07)" below. The team decided to keep 06 as the main analysis and build per-meter features only if they improve the validation score (see [protocol.md](protocol.md)).

**Review by our data analyst agent:** the agent found that the **number of bills** per client is linked to fraud (1.3% for 1 to 10 bills, 9.0% for 51 or more) and explains part of some effects. Changes made because of its suggestions are marked "(agent)".

| # | Hypothesis | Columns | Result | Possible feature |
|---|-----------|---------|--------|------------------|
| 1 | Fraud rate differs by **region** | `region` | **Supported.** Region 103 (8,964 clients) 10.3% and 311 (12,406) 8.0% are high. Region 101 (33,770) 3.6% and 301 (9,544) 3.3% are low. | `region` as category |
| 2 | A **sudden, drastic change in consumption** indicates fraud | `consommation_level_1-4`, `invoice_date`, `counter_type`, `counter_number` | **Supported, also with a similar number of bills.** (agent: jumps now calculated within each meter.) Median biggest jump: 1,530 (fraud) vs 930 (no fraud). Median std: 453 vs 320. In every bill group fraud is higher. **(07) Mostly an electricity signal:** 1,492 vs 910 on ELEC (about 64% higher) but only 279 vs 217 on GAZ (about 29%), and on GAZ it is gone for 31 or more bills. | `max_change`, `std_cons` per client, also per meter (`_elec`, `_gaz`) |
| 3 | **Index mismatch**: `new_index − old_index` differs from the sum of consumption levels | `old_index`, `new_index`, `consommation_level_1-4` | **Weak.** (agent) Overall 8.5% vs 5.4%, but inside each bill group the gap is small (for example 8.9% vs 9.6% for 51+ bills). Overlaps with 6, every backward bill is also a mismatch. **(07) Electricity only:** 9.2% vs 5.5% on ELEC (small, mostly for up to 30 bills), 7.9% vs 7.1% on GAZ (no pattern). | `has_mismatch`, `mismatch_count` (ELEC bills first). No `mismatch_share` (team decision) |
| 4 | Fraud rate differs by **tariff type** | `tarif_type` | **Supported for large tariffs.** Tariff 40 7.7% and 10 6.8% are above, 11 (84% of clients) 5.2% is below. Small tariffs are too few to trust. (agent: tariff 40 only appears on gas bills, so this may partly be a meter effect. **(07) Confirmed:** tariff 40 has 7.1%, the same as all gas clients (7.2%), so its high rate in 06 was a gas-meter effect, not a tariff effect. On ELEC tariff 10 (7.3%) is above tariff 11 (5.4%). Gas tariff 45 has 16.2%, but only 388 clients.) | `tarif_type` as category, group rare ones |
| 5 | **`reading_remarque`** has an impact on fraud | `reading_remarque` | **Partly supported.** Codes 6, 8, 9 are 6.0%, 7.2%, 6.4%. Code 7 is almost never fraud (0.2%, 478 clients). (agent: those clients have few and old bills, so remark 7 may only mean short history. **(07)** It is almost only an ELEC remark (0 of 472 clients are fraud, median 3 bills). About 4 fraud clients would be expected at that history length, so short history explains most of it, not all.) | none, not used as a feature (team decision) |
| 6 | A **negative index difference** (`new_index < old_index`) indicates fraud | `old_index`, `new_index` | **Supported.** Clients with a backward bill: 11.3% fraud vs 5.5% without (about 2x). Only 1,816 clients have one. (agent: the effect also holds inside each bill group; **(07)** 85% of the electricity and 79% of the gas backward bills are normal rollovers, and clients with only rollovers have the high rate (11.5% ELEC, 14.5% GAZ). Gas has only 146 backward clients.) | `has_backward`, `backward_count` |
| 7 | **Outliers** (very high consumption) show fraud | `consommation_level_1-4` | **Supported, with a catch.** Fraud rate rises with the client's biggest bill: 2.6%, 6.7%, 11.4%, 13.2% (10,000 to 50,000). Above 50,000 it drops to 3.8% (probably errors, a guess). (agent: the effect also holds inside each bill group.) | `max_consumption`, median per client, no capping |
| 8 | Fraud rate differs by **client category** (agent: new) | `client_catg` | **Supported, strong.** Category 51 (1,678 clients) 16.9% vs 5.5% for category 11. It is the highest in every bill group. | `client_catg` as category |
| 9 | The **meter setup** (ELEC, GAZ or both) has an impact on fraud | `counter_type` | **Not supported.** (agent suggested testing the meter type.) "Both meters" looks risky (7.2% vs 4.2% for ELEC only), but with a similar number of bills both are almost the same. | none |
| - | The **number of bills** per client is linked to fraud (agent: new) | all invoice rows | **Strong.** 1.3%, 4.8%, 7.5%, 9.0% for 1 to 10, 11 to 30, 31 to 50, 51+ bills. Median bills: 41 (fraud) vs 29. | `n_bills` |

## Dropped
- "Zero or very low consumption" indicates fraud: not supported. Fraud clients had a slightly lower zero ratio (0.107 vs 0.128) and slightly higher median consumption (528 vs 506).


## Column check (not a hypothesis)
- **Keep or delete the `consommation_level` columns?** Keep. We keep the four original columns and create no new level features (team decision). Clients whose bills are all level 1 are fraud only 1.7% (27,844 clients) vs 6.9% for clients using higher levels, also inside each consumption group. Details in the "Column check" section of the notebook.

## Still to test (agent suggestions)
- Why rollover clients have more fraud (heavy use?): compare rollover and non-rollover clients with similar consumption and bill count
- Client category 51 against consumption level (category 51 bills are about 5 times bigger)
- "Biggest drop" in consumption (the most negative change within one meter)
- `months_number`, gaps between bills, and history length (first bill date, client age from `creation_date`)
- A simple chi-square test for the moderate differences

## Notes
- Invoices are many rows per client, so aggregate to one row per client (mean, median, max, min, std, counts).
- Don't remove outliers: they may be the fraud (team decision, see [protocol.md](protocol.md)).
- Keep a validation split from the train set (test has no labels). Anything learned from the target (such as grouping regions by fraud rate) must be learned on the training split only.
