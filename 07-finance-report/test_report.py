"""Checks finance_report.py against the problems planted in make_sample_data.py. Run: python test_report.py"""
import tempfile
from pathlib import Path

import pandas as pd

import make_sample_data as m
import finance_report as f


def main():
    tmp = Path(tempfile.mkdtemp())
    m.OUT = tmp / "t.xlsx"
    m.main()
    df, issues = f.load_and_check(m.OUT, pd.Timestamp("2026-10-31"))
    counts = issues["problem"].value_counts()
    assert counts["Duplicate row, left out"] == 3
    assert counts["Dated in the future, left out"] == 2
    assert counts["No category, counted as Uncategorised"] == 6
    pnl, by_cat = f.summarise(df)
    assert len(pnl) == 10 and ((pnl["Profit"] - (pnl["Revenue"] - pnl["Expenses"])).abs() < 0.02).all()
    raw = pd.read_excel(m.OUT).drop_duplicates()
    raw = raw[pd.to_datetime(raw["date"]) <= "2026-10-31"]
    assert abs(pnl["Revenue"].sum() - raw[raw["amount"] > 0]["amount"].sum()) < 0.01  # nothing lost or doubled
    f.write(pnl, by_cat, issues, tmp / "r.xlsx")
    assert set(pd.read_excel(tmp / "r.xlsx", sheet_name=None)) == {"Summary", "Monthly P&L", "Expenses by category", "Data issues"}
    print("All finance report tests passed.")


main()
