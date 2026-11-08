"""Reconcile a purchase register (your books) against supplier-reported data.

This is a PROCESS-AUTOMATION demo on sample data. It is not tax advice.

Usage:
    python make_sample_data.py
    python reconcile.py                       # uses the sample files in ./data
    python reconcile.py --books A.xlsx --portal B.xlsx --out report.xlsx

How it works (the story to tell on camera):
  1. Load both files and clean the invoice numbers so "INV/0012" == "inv-12".
  2. Flag duplicates in the books.
  3. Match on (supplier GSTIN, cleaned invoice number).
  4. Compare amounts within a small tolerance.
  5. Try to pair leftovers by supplier + amount (probable typos in invoice numbers).
  6. Write a formatted Excel report with a summary sheet.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

TOLERANCE = 1.00  # rupees; differences up to this are treated as rounding

# Status labels (kept as constants so the summary and the filters never drift apart)
MATCHED = "Matched"
AMOUNT_DIFF = "Amount mismatch"
POSSIBLE = "Possible match (invoice no. differs)"
BOOKS_ONLY = "In books, not in portal data"
PORTAL_ONLY = "In portal data, not in books"
DUPLICATE = "Duplicate in books"

STATUS_COLORS = {
    MATCHED: "E2F0D9",
    AMOUNT_DIFF: "FFF2CC",
    POSSIBLE: "DDEBF7",
    BOOKS_ONLY: "F8CBAD",
    PORTAL_ONLY: "E4DFEC",
    DUPLICATE: "D9D9D9",
}

REQUIRED = ["invoice_no", "invoice_date", "supplier_gstin", "taxable_value", "gst_amount"]


# ---------------------------------------------------------------- cleaning
def normalize_invoice(value: object) -> str:
    """'INV/0012', 'inv-12' and 'Inv 12' all become 'INV12'.

    Upper-case, drop punctuation/spaces, and strip leading zeros from number groups.
    """
    text = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    parts = re.findall(r"[A-Z]+|\d+", text)
    return "".join(p.lstrip("0") or "0" if p.isdigit() else p for p in parts)


def load(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path) if path.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(f"{path.name} is missing columns: {', '.join(missing)}")
    df["supplier_gstin"] = df["supplier_gstin"].astype(str).str.strip().str.upper()
    df["invoice_key"] = df["invoice_no"].map(normalize_invoice)
    df["taxable_value"] = pd.to_numeric(df["taxable_value"], errors="coerce").fillna(0.0)
    df["gst_amount"] = pd.to_numeric(df["gst_amount"], errors="coerce").fillna(0.0)
    return df


# ---------------------------------------------------------------- matching
def reconcile(books: pd.DataFrame, portal: pd.DataFrame) -> pd.DataFrame:
    keys = ["supplier_gstin", "invoice_key"]

    # 1) Duplicates in books: keep the first, report the rest.
    is_dup = books.duplicated(subset=keys, keep="first")
    duplicates = books[is_dup].copy()
    duplicates["status"] = DUPLICATE
    duplicates["gst_difference"] = 0.0
    books = books[~is_dup]
    portal = portal.drop_duplicates(subset=keys, keep="first")

    # 2) Outer merge on supplier + cleaned invoice number.
    merged = books.merge(portal, on=keys, how="outer", suffixes=("_books", "_portal"), indicator=True)

    both = merged[merged["_merge"] == "both"].copy()
    diff = (both["taxable_value_books"] - both["taxable_value_portal"]).abs()
    both["status"] = (diff <= TOLERANCE).map({True: MATCHED, False: AMOUNT_DIFF})
    both["gst_difference"] = both["gst_amount_books"] - both["gst_amount_portal"]

    left = merged[merged["_merge"] == "left_only"].copy()
    right = merged[merged["_merge"] == "right_only"].copy()

    # 3) Pair leftovers by supplier + amount: probably the same invoice typed differently.
    paired_rows = []
    used_right: set[int] = set()
    for li, lrow in left.iterrows():
        candidates = right[
            (right["supplier_gstin"] == lrow["supplier_gstin"])
            & ((right["taxable_value_portal"] - lrow["taxable_value_books"]).abs() <= TOLERANCE)
            & (~right.index.isin(used_right))
        ]
        if not candidates.empty:
            ri = candidates.index[0]
            used_right.add(ri)
            row = lrow.copy()
            for col in right.columns:
                if col.endswith("_portal"):
                    row[col] = right.loc[ri, col]
            row["status"] = POSSIBLE
            row["gst_difference"] = row["gst_amount_books"] - row["gst_amount_portal"]
            paired_rows.append((li, row))

    paired_left = {li for li, _ in paired_rows}
    possible = pd.DataFrame([r for _, r in paired_rows])

    books_only = left[~left.index.isin(paired_left)].copy()
    books_only["status"] = BOOKS_ONLY
    books_only["gst_difference"] = books_only["gst_amount_books"]

    portal_only = right[~right.index.isin(used_right)].copy()
    portal_only["status"] = PORTAL_ONLY
    portal_only["gst_difference"] = -portal_only["gst_amount_portal"]

    # 4) Tidy into one table.
    dup_tidy = duplicates.rename(
        columns={c: f"{c}_books" for c in ["invoice_no", "invoice_date", "supplier_name", "taxable_value", "gst_amount"]}
    )
    result = pd.concat([both, possible, books_only, portal_only, dup_tidy], ignore_index=True)

    def pick(a: str, b: str) -> pd.Series:
        return result[a].where(result[a].notna(), result[b])

    out = pd.DataFrame(
        {
            "status": result["status"],
            "supplier_gstin": result["supplier_gstin"],
            "supplier_name": pick("supplier_name_books", "supplier_name_portal"),
            "invoice_no_books": result["invoice_no_books"],
            "invoice_no_portal": result["invoice_no_portal"],
            "taxable_books": result["taxable_value_books"],
            "taxable_portal": result["taxable_value_portal"],
            "gst_books": result["gst_amount_books"],
            "gst_portal": result["gst_amount_portal"],
            "gst_difference": result["gst_difference"],
        }
    )
    order = [MATCHED, AMOUNT_DIFF, POSSIBLE, BOOKS_ONLY, PORTAL_ONLY, DUPLICATE]
    out["status"] = pd.Categorical(out["status"], categories=order, ordered=True)
    return out.sort_values(["status", "supplier_gstin", "invoice_no_books"]).reset_index(drop=True)


def summarize(report: pd.DataFrame) -> pd.DataFrame:
    grouped = report.groupby("status", observed=False)
    summary = grouped.agg(
        invoices=("status", "size"),
        gst_in_books=("gst_books", "sum"),
        gst_in_portal=("gst_portal", "sum"),
        gst_difference=("gst_difference", "sum"),
    ).reset_index()
    return summary


# ---------------------------------------------------------------- output
def write_report(report: pd.DataFrame, summary: pd.DataFrame, out: Path) -> None:
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        report.to_excel(xl, sheet_name="All invoices", index=False)
        needs_action = report[report["status"] != MATCHED]
        needs_action.to_excel(xl, sheet_name="Needs action", index=False)

    wb = load_workbook(out)
    header_fill = PatternFill("solid", fgColor="1F3864")
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for idx, col in enumerate(ws.columns, start=1):
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[get_column_letter(idx)].width = min(max(width + 2, 12), 38)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, float):
                    cell.number_format = "#,##0.00"
            status = row[0].value
            if status in STATUS_COLORS:
                fill = PatternFill("solid", fgColor=STATUS_COLORS[status])
                for cell in row:
                    cell.fill = fill
    wb.save(out)


def main() -> None:
    here = Path(__file__).parent
    ap = argparse.ArgumentParser(description="Reconcile books vs supplier-reported data")
    ap.add_argument("--books", type=Path, default=here / "data" / "purchase_register.xlsx")
    ap.add_argument("--portal", type=Path, default=here / "data" / "portal_data.xlsx")
    ap.add_argument("--out", type=Path, default=here / "reconciliation_report.xlsx")
    args = ap.parse_args()

    report = reconcile(load(args.books), load(args.portal))
    summary = summarize(report)
    write_report(report, summary, args.out)

    print(summary.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"\nReport written to {args.out}")


if __name__ == "__main__":
    main()
