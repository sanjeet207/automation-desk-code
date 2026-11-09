"""Creates bank_statement.xlsx: 3 months of a fictional small business's bank transactions.
Run: python make_sample_data.py"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "bank_statement.xlsx"
# (description pattern, category, low, high, debit?)
TX = [("UPI/ZOMATO/{n}", "Meals", 250, 1800, True), ("UPI/SWIGGY/{n}", "Meals", 200, 1500, True),
      ("UBER *TRIP {n}", "Travel", 150, 900, True), ("OLA CABS {n}", "Travel", 120, 800, True), ("INDIGO AIR {n}", "Travel", 4500, 12000, True),
      ("AWS EMEA {n}", "Software", 3000, 9000, True), ("GOOGLE*WORKSPACE", "Software", 1380, 1380, True), ("NOTION LABS {n}", "Software", 800, 1600, True),
      ("AMAZON PAY IN {n}", "Office supplies", 300, 6000, True), ("RENT TRANSFER OCT", "Rent", 45000, 45000, True),
      ("NEFT/ACME RETAIL/{n}", "Sales receipts", 20000, 90000, False), ("IMPS/BLUEFERN CAFE/{n}", "Sales receipts", 8000, 40000, False),
      ("UPI/RAZORPAY SETTLE/{n}", "Sales receipts", 5000, 30000, False), ("ATM WDL {n}", "Cash withdrawal", 2000, 10000, True),
      ("BESCOM ELECTRICITY {n}", "Utilities", 2500, 6000, True), ("AIRTEL BROADBAND {n}", "Utilities", 1179, 1179, True),
      ("SALARY/STAFF/{n}", "Salaries", 25000, 45000, True), ("BANK CHARGES {n}", "Bank charges", 59, 590, True)]
# descriptions no simple rule will catch
ODD = [("ZMT*ORDER {n} BLR", "Meals"), ("UBR* PENDING {n}", "Travel"), ("AMZN MKTP IN*{n}", "Office supplies"), ("GOOGLE *CLOUD {n}", "Software"),
       ("POS 4021 CHAI POINT", "Meals"), ("NEFT/RAJ TRADERS/{n}", None), ("UPI/9876543210@YBL", None), ("CANVA* {n}", "Software")]


def main():
    rng = random.Random(10)
    rows = []
    for m in (8, 9, 10):
        for desc, cat, lo, hi, debit in TX:
            for _ in range(1 if lo == hi or desc.startswith("RENT") else rng.randint(1, 7) if lo < 10000 else rng.randint(2, 3)):
                amt = round(rng.uniform(lo, hi), 2)
                rows.append({"date": pd.Timestamp(2026, m, rng.randint(1, 28)), "description": desc.format(n=rng.randint(10000, 99999)).replace("OCT", ["AUG", "SEP", "OCT"][m - 8]),
                             "debit": amt if debit else None, "credit": None if debit else amt, "true_category": cat})
        for desc, cat in rng.sample(ODD, 6):
            rows.append({"date": pd.Timestamp(2026, m, rng.randint(1, 28)), "description": desc.format(n=rng.randint(1000, 9999)),
                         "debit": round(rng.uniform(200, 8000), 2), "credit": None, "true_category": cat})
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df.drop(columns="true_category").to_excel(OUT, index=False)
    df.to_csv(Path(__file__).parent / "answer_key.csv", index=False)  # only for the test
    print(f"Created {OUT.name}: {len(df)} transactions, Aug to Oct 2026")


if __name__ == "__main__":
    main()
