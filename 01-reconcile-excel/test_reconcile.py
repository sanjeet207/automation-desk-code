"""Run with:  python test_reconcile.py   (no pytest needed)

Checks the reconciliation against the known problems planted in make_sample_data.py.
"""
from make_sample_data import build
from reconcile import (
    AMOUNT_DIFF,
    BOOKS_ONLY,
    DUPLICATE,
    MATCHED,
    PORTAL_ONLY,
    POSSIBLE,
    normalize_invoice,
    reconcile,
    summarize,
)
import pandas as pd


def prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["invoice_key"] = df["invoice_no"].map(normalize_invoice)
    return df


def test_normalize() -> None:
    assert normalize_invoice("INV/0012") == normalize_invoice("inv-12") == "INV12"
    assert normalize_invoice("Inv 0014") == "INV14"
    assert normalize_invoice("A-007/B-01") == "A7B1"


def test_planted_problems_are_found() -> None:
    books, portal = build()
    report = reconcile(prep(books), prep(portal))
    counts = report["status"].value_counts().to_dict()

    assert counts[AMOUNT_DIFF] == 5, counts
    assert counts[POSSIBLE] == 2, counts
    assert counts[BOOKS_ONLY] == 4, counts
    assert counts[PORTAL_ONLY] == 4, counts
    assert counts[DUPLICATE] == 2, counts
    # 60 base invoices - 5 amount mismatches - 2 typos - 4 missing from portal = 49 clean.
    # (The 4 formatting-only cases still match because the cleaner fixes them.)
    assert counts[MATCHED] == 49, counts


def test_no_invoice_is_lost() -> None:
    """Every row from both files must appear in the report exactly once."""
    books, portal = build()
    report = reconcile(prep(books), prep(portal))
    from_books = report["invoice_no_books"].notna().sum()
    from_portal = report["invoice_no_portal"].notna().sum()
    assert from_books == len(books), (from_books, len(books))
    assert from_portal == len(portal), (from_portal, len(portal))


def test_summary_money_adds_up() -> None:
    books, portal = build()
    report = reconcile(prep(books), prep(portal))
    summary = summarize(report)
    # GST in books, across all statuses, equals the books total (duplicates included).
    assert round(summary["gst_in_books"].sum(), 2) == round(books["gst_amount"].sum(), 2)
    assert round(summary["gst_in_portal"].sum(), 2) == round(portal["gst_amount"].sum(), 2)


if __name__ == "__main__":
    test_normalize()
    test_planted_problems_are_found()
    test_no_invoice_is_lost()
    test_summary_money_adds_up()
    print("All reconciliation tests passed.")
