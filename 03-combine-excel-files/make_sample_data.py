"""Creates 48 fictional monthly sales files (4 branches x 12 months) with real-world mess. Run: python make_sample_data.py"""
import random
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

OUT = Path(__file__).parent / "monthly_files"
BRANCHES = ["North", "South", "East", "West"]
PRODUCTS = ["Laptop stand", "USB-C hub", "Desk lamp", "Office chair", "Monitor arm", "Keyboard", "Webcam"]
# different people name the columns differently
HEADERS = {
    "North": ["Date", "Product", "Qty", "Amount"],
    "South": ["Order Date", "Item", "Quantity", "Sales Amount"],
    "East": ["date", "product", "qty", "total"],
    "West": ["Date", "Product Name", "Units", "Net Amount"],
}


def main():
    rng = random.Random(11)
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.xlsx"):
        old.unlink()
    for b in BRANCHES:
        for m in range(1, 13):
            rows = []
            for _ in range(rng.randint(18, 30)):
                q = rng.randint(1, 9)
                rows.append([pd.Timestamp(2026, m, rng.randint(1, 28)), rng.choice(PRODUCTS), q, round(q * rng.uniform(900, 4200), 2)])
            name = OUT / f"{b}_2026-{m:02d}.xlsx"
            if (b, m) == ("East", 7):  # nobody filled this one in
                rows = []
            pd.DataFrame(rows, columns=HEADERS[b]).to_excel(name, index=False, sheet_name="Sales")
            if b == "South":  # South puts a report title above the table
                wb = load_workbook(name); ws = wb["Sales"]
                ws.insert_rows(1, 2); ws["A1"] = f"South branch sales, month {m}"
                wb.save(name)
    # someone saved the same file twice
    (OUT / "North_2026-03 (1).xlsx").write_bytes((OUT / "North_2026-03.xlsx").read_bytes())
    # a file that is not sales data at all
    pd.DataFrame({"Name": ["A. Rao", "K. Gill"], "Phone": ["98xxxxxx01", "98xxxxxx02"]}).to_excel(OUT / "contacts_old.xlsx", index=False)
    print(f"Created {len(list(OUT.glob('*.xlsx')))} files in {OUT}")


if __name__ == "__main__":
    main()
