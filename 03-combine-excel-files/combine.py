"""Combine a folder of Excel files into one clean master file.
Run: python combine.py                      (uses monthly_files/)
     python combine.py --folder my_files --out master.xlsx
"""
import argparse
import hashlib
from pathlib import Path

import pandas as pd

# every way people write the same column -> one standard name
COLUMN_NAMES = {
    "date": "date", "order date": "date",
    "product": "product", "item": "product", "product name": "product",
    "qty": "qty", "quantity": "qty", "units": "qty",
    "amount": "amount", "sales amount": "amount", "total": "amount", "net amount": "amount",
}
NEEDED = ["date", "product", "qty", "amount"]


def find_header(path):
    """Some files have a title above the table. Find the row that holds the real headers."""
    peek = pd.read_excel(path, header=None, nrows=10)
    for i, row in peek.iterrows():
        names = {str(v).strip().lower() for v in row if pd.notna(v)}
        matches = sum(COLUMN_NAMES.get(n) in NEEDED for n in names)
        if matches >= 3:
            return i  # this row holds the headers
    return None


def read_one(path):
    header = find_header(path)
    if header is None:
        return None, "Not sales data (no matching columns)"
    df = pd.read_excel(path, header=header)
    df.columns = [COLUMN_NAMES.get(str(c).strip().lower(), str(c)) for c in df.columns]
    missing = [c for c in NEEDED if c not in df.columns]
    if missing:
        return None, f"Missing columns: {', '.join(missing)}"
    df = df[NEEDED].dropna(how="all")
    if df.empty:
        return None, "Empty file"
    df["branch"] = path.stem.split("_")[0]
    df["source_file"] = path.name
    return df, "OK"


def combine(folder):
    frames, log, seen = [], [], {}
    # originals first, so "file (1).xlsx" is the one marked as the copy
    for path in sorted(Path(folder).glob("*.xlsx"), key=lambda p: (p.stem.split(" (")[0], len(p.name))):
        if path.name.startswith("~$"):
            continue  # Excel's temporary lock files
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        if digest in seen:
            reason = f"Skipped: duplicate of {seen[digest]}"
            log.append({"file": path.name, "rows": 0, "status": reason})
            continue
        seen[digest] = path.name
        df, status = read_one(path)
        log.append({"file": path.name, "rows": 0 if df is None else len(df), "status": status if df is not None else f"Skipped: {status}"})
        if df is not None:
            frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    data["date"] = pd.to_datetime(data["date"])
    data["month"] = data["date"].dt.strftime("%Y-%m")
    return data, pd.DataFrame(log)


def write(data, log, out):
    summary = data.pivot_table(index="month", columns="branch", values="amount", aggfunc="sum", fill_value=0).round(2)
    summary["Total"] = summary.sum(axis=1)
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        data.to_excel(xw, sheet_name="All data", index=False)
        summary.to_excel(xw, sheet_name="Monthly summary")
        log.to_excel(xw, sheet_name="File log", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(12, min(45, max(len(str(c.value or "")) for c in col) + 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=str(Path(__file__).parent / "monthly_files"))
    ap.add_argument("--out", default="master_sales.xlsx")
    a = ap.parse_args()
    data, log = combine(a.folder)
    write(data, log, a.out)
    used = (log["status"] == "OK").sum()
    print(f"Files found: {len(log)}  |  combined: {used}  |  skipped: {len(log) - used}")
    print(f"Rows in master file: {len(data)}  |  branches: {data['branch'].nunique()}  |  months: {data['month'].nunique()}")
    for _, r in log[log["status"] != "OK"].iterrows():
        print(f"  {r['file']}: {r['status']}")
    print(f"Saved: {a.out}")


if __name__ == "__main__":
    main()
