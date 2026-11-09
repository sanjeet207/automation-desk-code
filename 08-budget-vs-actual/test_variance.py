"""Checks variance.py on the planted story in make_sample_data.py. Run: python test_variance.py"""
import tempfile
from pathlib import Path

import pandas as pd

import make_sample_data as m
import variance as v


def main():
    tmp = Path(tempfile.mkdtemp()); m.OUT = tmp / "b.xlsx"; m.main()
    b, a = pd.read_excel(m.OUT, sheet_name="Budget"), pd.read_excel(m.OUT, sheet_name="Actual")
    full = v.compare(b, a, 10, 5000)
    oct_ = full[full["month"] == "2026-10"].set_index("line")
    assert set(oct_[oct_["material"]].index) == {"Product sales", "Marketing", "Subscriptions", "Software"}
    assert oct_.loc["Marketing", "result"] == "Unfavourable" and oct_.loc["Subscriptions", "result"] == "Favourable"
    assert not oct_.loc["Travel", "material"]  # 44% under, but under 5,000: not worth a comment
    assert v.streaks(full, "2026-10")["Marketing"] == 3
    assert (full["variance"] - (full["actual"] - full["budget"])).abs().max() < 0.01
    print("All variance tests passed.")


main()
