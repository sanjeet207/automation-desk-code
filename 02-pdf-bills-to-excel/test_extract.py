"""Checks the extractor against the problems planted in make_sample_bills.py. Run: python test_extract.py"""
import tempfile
from pathlib import Path

import make_sample_bills as m
import extract_bills as e


def main():
    tmp = Path(tempfile.mkdtemp())
    m.OUT = tmp
    m.main()
    df = e.check(__import__("pandas").DataFrame([e.read_bill(f) for f in sorted(tmp.glob("*.pdf"))]))
    bad = dict(zip(df["file"], df["problem"]))
    assert len(df) == 41
    assert (df["status"] == "OK").sum() == 37, (df["status"] == "OK").sum()
    assert "off by 500.00" in bad["bill_012.pdf"]
    assert "off by -90.50" in bad["bill_028.pdf"]
    assert "No invoice number" in bad["bill_020.pdf"]
    assert "Duplicate" in bad["bill_006_copy.pdf"]
    assert df["total"].notna().all() and df["supplier"].str.len().gt(0).all()
    print("All PDF bill tests passed.")


main()
