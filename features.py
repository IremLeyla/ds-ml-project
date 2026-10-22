"""Feature engineering for the fraud detection data (task #11).

build_features() only uses fixed rules: each client's features come from that
client's own bills, so nothing is learned from other clients or from the target.
The same function is applied to train, validation and test, so the columns match.

Input: the cleaned tables from cleaning.py (data/clean/).
Output: one row per client, indexed by client_id, without target.
"""

import pandas as pd

LEVEL_COLUMNS = [f"consommation_level_{i}" for i in range(1, 5)]
METERS = {"ELEC": "elec", "GAZ": "gaz"}
OTHER_CATEGORY = -1
# fixed reference date for client age (the data ends in 2019), the same for train and test
REFERENCE_DATE = pd.Timestamp("2020-01-01")
# "recent" bills: the last two years of a client's history
RECENT_DAYS = 730


def _add_bill_columns(invoices):
    """Add total consumption and the backward-index flag per bill."""
    invoices = invoices.copy()
    invoices["consumption"] = invoices[LEVEL_COLUMNS].sum(axis=1)
    invoices["backward"] = (invoices["new_index"] < invoices["old_index"]).astype(int)
    return invoices


def _consumption_changes(invoices):
    """Absolute change in consumption between consecutive bills of one meter type."""
    ordered = invoices.sort_values(["client_id", "counter_type", "invoice_date"])
    changes = ordered.groupby(["client_id", "counter_type"])["consumption"].diff().abs()
    return ordered.assign(change=changes)


def build_features(clients, invoices):
    """Build the model table with one row per client.

    clients: cleaned client table (clean_clients), invoices: cleaned invoice table.
    """
    bills = _consumption_changes(_add_bill_columns(invoices))
    by_client = bills.groupby("client_id")

    features = pd.DataFrame(index=pd.Index(sorted(clients["client_id"]), name="client_id"))

    # Number of bills and total consumption per bill (mean, median and max as agreed)
    features["n_bills"] = by_client.size()
    cons = by_client["consumption"]
    features["cons_mean"] = cons.mean()
    features["cons_median"] = cons.median()
    features["cons_std"] = cons.std()
    features["cons_min"] = cons.min()
    features["cons_max"] = cons.max()

    # The four original consumption levels: sum and biggest single bill per level
    for level in LEVEL_COLUMNS:
        features[f"{level}_sum"] = by_client[level].sum()
        features[f"{level}_max"] = by_client[level].max()

    # Meter index going backward (new_index < old_index)
    features["backward_count"] = by_client["backward"].sum()
    features["has_backward"] = (features["backward_count"] > 0).astype(int)

    # Biggest jump between bills, within one meter type
    features["max_change"] = by_client["change"].max()

    # Per meter: only std and biggest jump (the electricity signal, see protocol.md).
    # The groups only exist for clients with a bill on that meter, so NaN stays
    # "no bill on this meter" after the join. One bill on a meter gives 0, not NaN.
    for meter, suffix in METERS.items():
        on_meter = bills[bills["counter_type"] == meter].groupby("client_id")
        features[f"cons_std_{suffix}"] = on_meter["consumption"].std().fillna(0)
        features[f"max_change_{suffix}"] = on_meter["change"].max().fillna(0)

    # std and biggest jump of a single bill are not defined: set to 0 (team decision)
    features["cons_std"] = features["cons_std"].fillna(0)
    features["max_change"] = features["max_change"].fillna(0)

    # Most common tariff plan per client (rare plans are grouped later, on train only)
    # (ties go to the smaller plan number, so the result is the same on every run)
    plan_counts = bills.groupby(["client_id", "tarif_type"]).size().rename("n").reset_index()
    plan_counts = plan_counts.sort_values(["client_id", "n", "tarif_type"], ascending=[True, False, True])
    features["tarif_type"] = plan_counts.drop_duplicates("client_id").set_index("client_id")["tarif_type"]

    # Client table: categories as integers
    client_part = clients.set_index("client_id")[["client_catg", "region"]]
    features = features.join(client_part)

    return features


def build_extra_features(clients, invoices):
    """Extra features per client for the feature selection test (notebook 13).

    Like build_features(), every value comes from the client's own bills and
    client row, so nothing is learned from other clients and the same function
    is used for train, validation and test.
    """
    bills = _add_bill_columns(invoices)
    by_client = bills.groupby("client_id")
    n_bills = by_client.size()

    extra = pd.DataFrame(index=pd.Index(sorted(clients["client_id"]), name="client_id"))

    # A. Per-bill levels: the level sums divided by the number of bills
    for level in LEVEL_COLUMNS:
        extra[f"{level}_per_bill"] = by_client[level].sum() / n_bills

    # B. Time: client age, length of the bill history and gaps between bills
    created = clients.set_index("client_id")["creation_date"]
    extra["client_age_years"] = (REFERENCE_DATE - created).dt.days / 365.25
    first_bill, last_bill = by_client["invoice_date"].min(), by_client["invoice_date"].max()
    extra["history_years"] = (last_bill - first_bill).dt.days / 365.25
    # a history shorter than one month counts as one month, so one bill does not divide by zero
    extra["bills_per_year"] = n_bills / extra["history_years"].clip(lower=1 / 12)
    # gaps between distinct bill dates (electricity and gas are often billed on the same day)
    dates = bills[["client_id", "invoice_date"]].drop_duplicates().sort_values(["client_id", "invoice_date"])
    gaps = dates.groupby("client_id")["invoice_date"].diff().dt.days
    extra["gap_mean_days"] = gaps.groupby(dates["client_id"]).mean()
    extra["gap_max_days"] = gaps.groupby(dates["client_id"]).max()
    extra["months_number_mean"] = by_client["months_number"].mean()
    extra["months_number_max"] = by_client["months_number"].max()

    # C. Change over time: recent vs. early consumption, biggest drop, bills with no consumption
    recent = bills["invoice_date"] > bills["client_id"].map(last_bill) - pd.Timedelta(days=RECENT_DAYS)
    recent_mean = bills[recent].groupby("client_id")["consumption"].mean()
    early_mean = bills[~recent].groupby("client_id")["consumption"].mean()
    # +1 avoids dividing by zero; NaN = no bill before the last two years
    extra["recent_vs_early"] = (recent_mean + 1) / (early_mean + 1)
    ordered = bills.sort_values(["client_id", "counter_type", "invoice_date"])
    change = ordered.groupby(["client_id", "counter_type"])["consumption"].diff()
    # biggest decrease between consecutive bills of one meter; 0 if there is none (like max_change)
    extra["max_drop"] = (-change).clip(lower=0).groupby(ordered["client_id"]).max().fillna(0)
    extra["zero_share"] = (bills["consumption"] == 0).groupby(bills["client_id"]).mean()

    # D. Meter: meter changes and unusual meter readings
    extra["n_counters"] = by_client["counter_number"].nunique()
    # status 0 is the normal case; odd values were set to NaN in cleaning and count as unusual
    extra["statue_unusual_share"] = (bills["counter_statue"] != 0).groupby(bills["client_id"]).mean()
    extra["coef_not1_share"] = (bills["counter_coefficient"] != 1).groupby(bills["client_id"]).mean()

    return extra


def build_diversity_features(clients, invoices):
    """Diversity, consumption-shape and time-activity features per client (notebook 16).

    Like build_features(), every value comes from the client's own bills, so
    nothing is learned from other clients and the same function is used for
    train, validation and test.
    """
    bills = _add_bill_columns(invoices)
    by_client = bills.groupby("client_id")

    extra = pd.DataFrame(index=pd.Index(sorted(clients["client_id"]), name="client_id"))

    # Diversity of the meter setup: how many different codes, remarks and tariffs a client has
    extra["n_codes"] = by_client["counter_code"].nunique()
    extra["n_remarque"] = by_client["reading_remarque"].nunique()
    extra["n_tarif"] = by_client["tarif_type"].nunique()
    extra["remarque_8_share"] = (bills["reading_remarque"] == 8).groupby(bills["client_id"]).mean()

    # Consumption shape; +1 avoids dividing by zero for clients without consumption
    cons = by_client["consumption"]
    # std of a single bill is not defined: set to 0 (team rule, as for cons_std)
    extra["cons_cv"] = (cons.std() / (cons.mean() + 1)).fillna(0)
    total = cons.sum() + 1
    extra["level2_3_share"] = (by_client["consommation_level_2"].sum() + by_client["consommation_level_3"].sum()) / total
    extra["level4_share"] = by_client["consommation_level_4"].sum() / total
    extra["cons_p90_over_median"] = (cons.quantile(0.9) + 1) / (cons.median() + 1)

    # Time activity: how recent and how dense the bills are
    last_bill = by_client["invoice_date"].max()
    recent = bills["invoice_date"] > bills["client_id"].map(last_bill) - pd.Timedelta(days=RECENT_DAYS)
    extra["share_last_2y"] = recent.groupby(bills["client_id"]).mean()
    in_2016_17 = bills["invoice_date"].dt.year.isin([2016, 2017])
    extra["bills_in_2016_17"] = in_2016_17.groupby(bills["client_id"]).sum()
    extra["days_since_last_bill"] = (REFERENCE_DATE - last_bill).dt.days
    # bills per billing date, counting each (date, meter type) once
    pairs = bills[["client_id", "invoice_date", "counter_type"]].drop_duplicates().groupby("client_id").size()
    extra["inv_per_date"] = pairs / by_client["invoice_date"].nunique()

    return extra


def group_rare(values, keep, other=OTHER_CATEGORY):
    """Replace every category that is not in `keep` by `other`.

    `keep` is learned on the training split only, then reused on validation and test.
    """
    return values.where(values.isin(keep), other)


def categories_to_keep(values, min_share=0.01):
    """Categories that cover at least min_share of the (training) clients."""
    shares = values.value_counts(normalize=True)
    return shares[shares >= min_share].index.tolist()
