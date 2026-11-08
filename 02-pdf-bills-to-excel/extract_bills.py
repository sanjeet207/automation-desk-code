"""Reads every PDF bill in a folder and builds one Excel file, flagging what needs a human.

  python extract_bills.py                 # uses ./bills
  python extract_bills.py --folder my_bills --out my_bills.xlsx
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

NUM = r"([\d,]+\.\d{2})"
PATTERNS = {  # each field: the different ways suppliers write it
    "invoice_no": [r"Invoice No:\s*(\S+)", r"Bill #\s*(\S+)"],
    "date": [r"Date:\s*(\d{2}-\d{2}-\d{4})", r"Bill date\s*(\d{1,2} \w{3} \d{4})"],
    "subtotal": [rf"Subtotal:\s*{NUM}", rf"Sub total\s*{NUM}"],
    "tax": [rf"Tax \(18%\):\s*{NUM}", rf"Tax\s*{NUM}"],
    "total": [rf"Total:\s*{NUM}", rf"Amount due\s*{NUM}"],
}
TOLERANCE = 0.05


def first_match(patterns: list[str], text: str) -> str | None:
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def to_number(s: str | None) -> float | None:
    return float(s.replace(",", "")) if s else None


def read_bill(path: Path) -> dict:
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    supplier = lines[1].title() if lines and lines[0] == "BILL" else (lines[0] if lines else "")
    row = {"file": path.name, "supplier": supplier}
    for field, pats in PATTERNS.items():
        row[field] = first_match(pats, text)
    for f in ("subtotal", "tax", "total"):
        row[f] = to_number(row[f])
    row["date"] = pd.to_datetime(row["date"], dayfirst=True, errors="coerce")
    return row


def check(df: pd.DataFrame) -> pd.DataFrame:
    problems = []
    dup = df.duplicated(subset=["supplier", "invoice_no", "total"], keep="first") & df["invoice_no"].notna()
    for i, r in df.iterrows():
        p = []
        if pd.isna(r["invoice_no"]) or not str(r["invoice_no"]).strip():
            p.append("No invoice number")
        if pd.isna(r["total"]) or pd.isna(r["subtotal"]):
            p.append("Could not read amounts")
        elif abs(r["subtotal"] + (r["tax"] or 0) - r["total"]) > TOLERANCE:
            p.append(f"Total does not add up (off by {r['total'] - r['subtotal'] - r['tax']:,.2f})")
        if dup[i]:
            p.append("Duplicate of another bill")
        problems.append("; ".join(p))
    df["problem"] = problems
    df["status"] = ["Needs review" if p else "OK" for p in problems]
    return df


def write_excel(df: pd.DataFrame, out: Path) -> None:
    cols = ["status", "problem", "file", "supplier", "invoice_no", "date", "subtotal", "tax", "total"]
    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        df[cols].to_excel(xl, sheet_name="All bills", index=False)
        df[df["status"] != "OK"][cols].to_excel(xl, sheet_name="Needs review", index=False)
        df[df["status"] == "OK"].groupby("supplier")[["subtotal", "tax", "total"]].sum().round(2).to_excel(xl, sheet_name="By supplier")
    wb = load_workbook(out)
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1F3864")
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(max(len(str(c.value or "")) for c in col) + 2, 45)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                if isinstance(c.value, float):
                    c.number_format = "#,##0.00"
                if c.number_format and hasattr(c.value, "year"):
                    c.number_format = "dd-mmm-yyyy"
            if ws.title != "By supplier" and row[0].value == "Needs review":
                for c in row:
                    c.fill = PatternFill("solid", fgColor="FFF2CC")
    wb.save(out)


def main() -> None:
    here = Path(__file__).parent
    ap = argparse.ArgumentParser(description="PDF bills -> one Excel file")
    ap.add_argument("--folder", type=Path, default=here / "bills")
    ap.add_argument("--out", type=Path, default=here / "bills_summary.xlsx")
    a = ap.parse_args()
    files = sorted(a.folder.glob("*.pdf"))
    if not files:
        raise SystemExit(f"No PDF files in {a.folder}")
    df = check(pd.DataFrame([read_bill(f) for f in files]))
    write_excel(df, a.out)
    ok = df[df["status"] == "OK"]
    print(f"Read {len(df)} PDF bills from {a.folder.name}/")
    print(f"OK:            {len(ok)}")
    print(f"Needs review:  {len(df) - len(ok)}")
    for _, r in df[df["status"] != "OK"].iterrows():
        print(f"  - {r['file']}: {r['problem']}")
    print(f"Total of OK bills: {ok['total'].sum():,.2f}")
    print(f"Excel written: {a.out.name}")


if __name__ == "__main__":
    main()
