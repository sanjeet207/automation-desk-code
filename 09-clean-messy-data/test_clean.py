"""Checks clean_data.py on the mess planted by make_messy_data.py. Run: python test_clean.py"""
import tempfile
from pathlib import Path

import pandas as pd

import make_messy_data as m
import clean_data as c


def main():
    tmp = Path(tempfile.mkdtemp()); m.OUT = tmp / "m.xlsx"; m.main()
    raw = pd.read_excel(m.OUT, dtype=str)
    df, log, human = c.clean(raw)
    assert len(df) == 485 and df["Order ID"].is_unique
    assert log["Duplicate orders removed"] == 12 and log["Empty rows removed"] == 3 and log["Total rows removed"] == 1
    assert (df["Customer Name"] == df["Customer Name"].str.strip().str.title()).all()
    assert df["Phone"].str.fullmatch(r"\d{10}").all()
    assert df["Amount"].notna().all() and (df["Amount"] > 0).all()
    assert set(human["problem"]) == {"Not a date", "Not a valid email"}
    assert (human["problem"] == "Not a date").sum() == df["Order Date"].isna().sum()
    print("All cleaning tests passed.")


main()
