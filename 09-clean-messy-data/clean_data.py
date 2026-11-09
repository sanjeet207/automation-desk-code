"""Clean a messy Excel export in one run, and log every change.
Run: python clean_data.py                         (uses messy_customers.xlsx)
     python clean_data.py --excel my_export.xlsx --out clean.xlsx
Writes three sheets: Clean data, What changed, Needs a human.
"""
import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$")


def clean(df):
    log, human = Counter(), []
    n0 = len(df)
    # 1. drop empty rows and the "TOTAL" line people add at the bottom
    df = df.dropna(how="all")
    log["Empty rows removed"] = n0 - len(df)
    is_total = df["Order ID"].astype(str).str.strip().str.upper().isin(["TOTAL", "GRAND TOTAL"])
    log["Total rows removed"] = int(is_total.sum()); df = df[~is_total].copy()
    # 2. text: trim spaces, one space between words, proper case for names and cities
    for col in ["Customer Name", "City"]:
        before = df[col].copy()
        df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        log[f"{col}: spaces or capitals fixed"] = int((before != df[col]).sum())
    # 3. phones: digits only, last 10 digits
    before = df["Phone"].astype(str)
    digits = before.str.replace(r"\D", "", regex=True).str[-10:]
    df["Phone"] = digits
    log["Phone: formatted to 10 digits"] = int((before != digits).sum())
    # 4. emails: lowercase, then check the shape
    before = df["Email"].astype(str)
    df["Email"] = before.str.strip().str.lower()
    log["Email: made lowercase"] = int((before != df["Email"]).sum())
    # 5. dates: three formats in one column -> real dates
    raw = df["Order Date"].astype(str).str.strip()
    parsed = pd.to_datetime(raw, format="%Y-%m-%d", errors="coerce")
    for fmt in ("%d/%m/%Y", "%d %b %Y"):
        parsed = parsed.fillna(pd.to_datetime(raw, format=fmt, errors="coerce"))
    log["Order Date: text turned into real dates"] = int(parsed.notna().sum())
    df["Date text"] = raw  # kept until the end, to show what could not be read
    df["Order Date"] = parsed.dt.date
    # 6. amounts: remove currency signs and commas, make them numbers
    raw = df["Amount"].astype(str)
    num = pd.to_numeric(raw.str.replace(r"[^\d.]", "", regex=True).str.lstrip("."), errors="coerce")
    log["Amount: text or symbols turned into numbers"] = int((~raw.str.fullmatch(r"\d+(\.\d+)?")).sum())
    df["Amount"] = num.round(2)
    # 7. duplicates: same order ID after cleaning = the same order typed twice
    dup = df.duplicated(subset=["Order ID", "Customer Name", "Amount"], keep="first")
    log["Duplicate orders removed"] = int(dup.sum()); df = df[~dup]
    # 8. what code should not guess: list it for a person to fix at the source
    checks = [("Phone", df["Phone"].str.len() != 10, "Phone", "Not 10 digits"),
              ("Email", ~df["Email"].str.match(EMAIL), "Email", "Not a valid email"),
              ("Order Date", df["Order Date"].isna(), "Date text", "Not a date"),
              ("Amount", df["Amount"].isna(), "Amount", "Not a number")]
    for col, mask, shown, problem in checks:
        for _, r in df[mask].iterrows():
            human.append({"Order ID": r["Order ID"], "column": col, "value": r[shown], "problem": problem})
    df = df.drop(columns="Date text")
    return df.sort_values("Order ID").reset_index(drop=True), log, pd.DataFrame(human)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", default=str(Path(__file__).parent / "messy_customers.xlsx"))
    ap.add_argument("--out", default="clean_customers.xlsx")
    a = ap.parse_args()
    raw = pd.read_excel(a.excel, dtype=str)
    df, log, human = clean(raw)
    with pd.ExcelWriter(a.out, engine="xlsxwriter") as xw:
        df.to_excel(xw, sheet_name="Clean data", index=False)
        pd.DataFrame(log.items(), columns=["fix", "rows"]).to_excel(xw, sheet_name="What changed", index=False)
        human.to_excel(xw, sheet_name="Needs a human", index=False)
        for ws in xw.sheets.values():
            ws.set_column("A:G", 20); ws.freeze_panes(1, 0)
        xw.sheets["Clean data"].set_column("G:G", 12, xw.book.add_format({"num_format": "#,##0.00"}))
    print(f"Rows in: {len(raw)}  |  clean rows out: {len(df)}  |  need a human: {len(human)}")
    for fix, n in log.items():
        print(f"  {fix}: {n}")
    print(f"Saved: {a.out}  (Clean data, What changed, Needs a human)")


if __name__ == "__main__":
    main()
