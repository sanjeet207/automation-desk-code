"""Creates transactions.xlsx: 10 months of fictional income and expenses for a small business, with planted problems.
Run: python make_sample_data.py"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "transactions.xlsx"
INCOME = {"Product sales": (60000, 160000), "Services": (20000, 70000), "Subscriptions": (8000, 20000)}
EXPENSE = {"Salaries": (90000, 95000), "Rent": (35000, 35000), "Marketing": (8000, 40000), "Software": (6000, 12000),
           "Travel": (2000, 18000), "Utilities": (3000, 7000), "Office supplies": (1000, 6000)}


def main():
    rng = random.Random(21)
    rows = []
    for m in range(1, 11):  # January to October 2026
        growth = 1 + 0.035 * m
        for cat, (lo, hi) in INCOME.items():
            for _ in range(rng.randint(4, 9)):
                rows.append([pd.Timestamp(2026, m, rng.randint(1, 28)), f"{cat} receipt", cat, "Income", round(rng.uniform(lo, hi) * growth / 4, 2)])
        for cat, (lo, hi) in EXPENSE.items():
            n = 1 if cat in ("Salaries", "Rent") else rng.randint(2, 6)
            for _ in range(n):
                amt = rng.uniform(lo, hi) / (1 if n == 1 else n / 2)
                rows.append([pd.Timestamp(2026, m, rng.randint(1, 28)), f"{cat} payment", cat, "Expense", round(-amt, 2)])
    df = pd.DataFrame(rows, columns=["date", "description", "category", "type", "amount"])
    blanks = df.sample(6, random_state=1).index
    df.loc[blanks, "category"] = None                         # nobody filled in the category
    dupes = df.sample(3, random_state=2)                       # the same rows exported twice
    future = pd.DataFrame([[pd.Timestamp(2026, 12, 15), "Software payment", "Software", "Expense", -9800.0],
                           [pd.Timestamp(2026, 12, 20), "Services receipt", "Services", "Income", 41000.0]], columns=df.columns)
    df = pd.concat([df, dupes, future]).sample(frac=1, random_state=3).reset_index(drop=True)
    df.to_excel(OUT, index=False, sheet_name="Transactions")
    print(f"Created {OUT.name}: {len(df)} transactions")


if __name__ == "__main__":
    main()
