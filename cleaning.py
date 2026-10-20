"""Cleaning rules for the fraud detection data.

Every rule is fixed (it learns nothing from the data), so the same functions
are applied to train and test. Test rows are never dropped.
"""

import pandas as pd

VALID_COUNTER_STATUS = range(6)
KEPT_REMARKS = [6, 7, 8, 9]
OTHER_REMARK = 0


def clean_clients(clients):
    """Fix the misspelled column name and convert the creation date."""
    clients = clients.copy()
    clients = clients.rename(columns={"disrict": "district"})
    clients["creation_date"] = pd.to_datetime(
        clients["creation_date"], format="%d/%m/%Y"
    )
    return clients


def clean_invoices(invoices, drop_duplicates=False):
    """Clean the invoice table.

    drop_duplicates: drop exact duplicate rows. Off for now, the team
    still has to decide (see protocol.md).
    """
    invoices = invoices.copy()
    if drop_duplicates:
        invoices = invoices.drop_duplicates().reset_index(drop=True)

    invoices["invoice_date"] = pd.to_datetime(
        invoices["invoice_date"], format="%Y-%m-%d"
    )

    # Odd values like "A" or 618 become NaN, valid status is 0 to 5
    status = pd.to_numeric(invoices["counter_statue"], errors="coerce")
    # float in train and test, so both tables get the same dtype
    invoices["counter_statue"] = status.where(
        status.isin(VALID_COUNTER_STATUS)
    ).astype("float64")

    # Rare remark codes (5, 203, 207, 413) are grouped into 0 = "other"
    remark = invoices["reading_remarque"]
    invoices["reading_remarque"] = remark.where(remark.isin(KEPT_REMARKS), OTHER_REMARK)

    # months_number is kept as it is (team decision, revisit in feature engineering)
    return invoices
