"""Checks combine.py against the mess planted by make_sample_data.py. Run: python test_combine.py"""
import tempfile
from pathlib import Path

import make_sample_data as m
import combine as c


def main():
    tmp = Path(tempfile.mkdtemp())
    m.OUT = tmp
    m.main()
    data, log = c.combine(tmp)
    st = dict(zip(log["file"], log["status"]))
    assert len(log) == 50, len(log)
    assert (log["status"] == "OK").sum() == 47
    assert "duplicate" in st["North_2026-03.xlsx"] or "duplicate" in st["North_2026-03 (1).xlsx"]
    assert st["East_2026-07.xlsx"] == "Skipped: Empty file"
    assert "Not sales data" in st["contacts_old.xlsx"]
    assert data["branch"].nunique() == 4 and data["month"].nunique() == 12
    assert data[["date", "product", "qty", "amount"]].notna().all().all()
    assert (data[data["branch"] == "South"]["amount"] > 0).all()  # title rows were skipped correctly
    c.write(data, log, tmp / "out.xlsx")
    print("All combine tests passed.")


main()
