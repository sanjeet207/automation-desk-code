"""Checks make_statements.py against the problems planted in make_sample_data.py. Run: python test_statements.py"""
import tempfile
from pathlib import Path

import pandas as pd
import pdfplumber

import make_sample_data as m
import make_statements as s


def main():
    tmp = Path(tempfile.mkdtemp())
    m.OUT = tmp / "customers.xlsx"
    m.main()
    log = s.make_all(m.OUT, tmp / "out")
    st = dict(zip(log["customer_id"] + " " + log["name"], log["status"]))
    assert log["file"].astype(bool).sum() == 23
    assert st["C-019 Saffron Kitchen"] == "Skipped: no transactions"
    assert st["C-007 Granite Builders"] == "Created, but no email address"
    assert (log["status"].str.startswith("Unknown customer")).sum() == 2
    # the closing balance on the PDF must equal opening + debits - credits
    tx = pd.read_excel(m.OUT, sheet_name="Transactions")
    cus = pd.read_excel(m.OUT, sheet_name="Customers").set_index("customer_id")
    for cid in ("C-001", "C-012"):
        t = tx[tx["customer_id"] == cid]
        expected = round(cus.loc[cid, "opening_balance"] + t["debit"].sum() - t["credit"].sum(), 2)
        pdf = next((tmp / "out").glob(f"{cid}_*.pdf"))
        text = pdfplumber.open(pdf).pages[0].extract_text()
        assert f"{abs(expected):,.2f}" in text.splitlines()[-3] or f"{abs(expected):,.2f}" in text, (cid, expected)
    print("All statement tests passed.")


main()
