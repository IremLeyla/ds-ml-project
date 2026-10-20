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


def group_rare(values, keep, other=OTHER_CATEGORY):
    """Replace every category that is not in `keep` by `other`.

    `keep` is learned on the training split only, then reused on validation and test.
    """
    return values.where(values.isin(keep), other)


def categories_to_keep(values, min_share=0.01):
    """Categories that cover at least min_share of the (training) clients."""
    shares = values.value_counts(normalize=True)
    return shares[shares >= min_share].index.tolist()
