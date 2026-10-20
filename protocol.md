# Protocol: Team Decisions

All decisions of the team, newest at the bottom. Details and numbers are in the notebooks (data cleaning: [05_eda.ipynb](05_eda.ipynb), rules in [cleaning.py](cleaning.py)).

**Status:** Decided = agreed by the team, Open = still to be discussed, To confirm = proposed, not yet confirmed by the whole team, Noted = reminder, no action needed now.

| Date | Topic | Decision | Reason | Status |
| --- | --- | --- | --- | --- |
| 2026-10-19 | Project | We work on the Zindi challenge "Fraud Detection in Electricity and Gas Consumption" | Medium difficulty, real stakeholder (STEG), starter notebook available | Decided |
| 2026-10-19 | Raw data in git | Competition data stays in `data/` and is ignored by git. Every teammate downloads it from Zindi | Competition rules, public repo, files are large | Decided |
| 2026-10-20 | Odd `counter_statue` values (`A`, `46`, `618`, ...) | Keep the rows and set the value to NaN | Only 47 of 4.5 million rows (6 clients, none fraudulent), no information lost, same rule for train and test, LightGBM and XGBoost handle NaN | Decided |
| 2026-10-20 | `months_number` | Keep all values, no maximum. Decide how to use the column in feature engineering | We do not want to lose information that may help us find the most fraudulent clients | Decided |
| 2026-10-20 | Duplicate invoices | Take a closer look at them again. Nothing is dropped until then | 11 duplicate rows in train and 8 in test, effect is tiny, no agreement yet | Open |
| 2026-10-20 | Meter index going backward (`new_index` < `old_index`) | Keep the rows. Look closer in feature engineering. Add to our hypotheses that this could indicate fraud. Indicator: number of backward steps per client | Some are normal rollovers after 99,999, others may be manipulation | Decided |
| 2026-10-20 | Outliers (for example `consommation_level_1` up to 999,910) | Follow the recommendation: keep all rows, no capping for now. Use median and max besides the mean when aggregating per client. Use a log transform for the logistic regression baseline. Look at the distributions first, cap on train only if a few values are obvious typing errors | Tree models handle outliers well. Clients with a consumption value above 10,000 are fraudulent in 11.8% of cases vs. 5.6% overall, so capping could hide the fraud signal | Decided |
| 2026-10-20 | Presentation | Say in the presentation that we kept the outliers on purpose, because extreme values are what we are looking for | The outliers carry the fraud signal | Noted |
| 2026-10-20 | `reading_remarque` | Keep codes 6, 7, 8, 9 and group the rare codes 5, 203, 207, 413 into 0 ("other"). Treat the column as a category | The rare codes cover 5 clients and never appear in test. Zindi does not explain the code meanings | To confirm |
| 2026-10-20 | Column name `disrict` | Rename to `district` in the cleaning. Cleaned data is saved as CSV files in `data/clean/` (not committed) | Typo in the Zindi file. Everyone can load the cleaned tables directly | Decided |
