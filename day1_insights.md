# Day 1: First Insights and Challenges

## First insights

- **Size:** Train has 135,493 clients and 4.48M invoices. Test has 58,069 clients and 1.94M invoices. Each client appears once in the client file and many times in the invoice file (median 30 invoices, max 439).
- **Class imbalance:** Only 5.6% of clients are fraudulent (7,566 vs 127,927). Plain accuracy is useless here, which supports using AUC plus precision, recall and F1.
- **Clean on the surface:** No missing values and no duplicate client IDs. There are 11 fully duplicated invoice rows.
- **Two services:** Invoices are 69% electricity and 31% gas. Fraud rate is similar for both, at about 7.7% and 8.4% of invoice rows. Invoice-level rates are weighted towards clients with many invoices, so they are not client-level rates.
- **Client category looks predictive:** Category 51 has a 16.9% fraud rate, against 5.5% for category 11 and 4.0% for category 12. Category 51 is small, with 1,678 clients.
- **Region matters:** Fraud rate varies by region, for example 3.3% in region 301 and 10.3% in region 103.
- **Invoice dates:** They run from 1977 to 2019. The Zindi page says 2005 to 2019, so some history is older than described.

## Challenges

- **Aggregation:** Invoices have to be aggregated to one row per client. We need to decide which features to build, for example consumption stats, invoice counts, counter changes and the `reading_remarque` mix.
- **Data quality in invoices:**
  - `months_number` has an extreme outlier (max 636,624) and values of 0, while the typical value is 4.
  - 2,264 invoices have `new_index` lower than `old_index`.
  - `counter_statue` is mixed-type, with codes like `A`, `46` and `618` beside `0` to `5`.
  - `reading_remarque` has rare codes such as 203 and 413.
- **Unclear columns:** `counter_number` and `counter_code` have no description from Zindi.
- **Naming:** The district column is spelled `disrict` in the client file and `District` on Zindi.
- **Test set:** We should check that test clients come from the same distribution as train, for example regions and creation dates.

## Proposed rough plan

1. Clean the invoices and fix types.
2. Build per-client aggregate features.
3. Run a baseline, for example logistic regression and gradient boosting, with stratified cross-validation on AUC.
4. Iterate on features and tune.
5. Check precision, recall and F1 at sensible thresholds.
