"""Creates budget_actual.xlsx: a fictional company's monthly budget and actuals by line, January to October 2026.
Run: python make_sample_data.py"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "budget_actual.xlsx"
LINES = [("Revenue", "Product sales", 260000), ("Revenue", "Services", 110000), ("Revenue", "Subscriptions", 42000),
         ("Expense", "Salaries", 150000), ("Expense", "Rent", 35000), ("Expense", "Marketing", 30000),
         ("Expense", "Software", 12000), ("Expense", "Travel", 9000), ("Expense", "Utilities", 5000), ("Expense", "Office supplies", 3000)]
# what really happened this year, so the variances tell a story
STORY = {"Marketing": {8: 1.25, 9: 1.30, 10: 1.38}, "Product sales": {10: 0.86}, "Travel": {10: 0.55}, "Subscriptions": {9: 1.15, 10: 1.22}, "Software": {10: 1.45}}


def main():
    rng = random.Random(8)
    budget, actual = [], []
    for m in range(1, 11):
        for typ, line, base in LINES:
            b = round(base * (1 + 0.01 * m), -2)
            a = b * rng.uniform(0.95, 1.05) * STORY.get(line, {}).get(m, 1.0)
            budget.append({"month": f"2026-{m:02d}", "type": typ, "line": line, "budget": b})
            actual.append({"month": f"2026-{m:02d}", "type": typ, "line": line, "actual": round(a, 2)})
    with pd.ExcelWriter(OUT) as xw:
        pd.DataFrame(budget).to_excel(xw, sheet_name="Budget", index=False)
        pd.DataFrame(actual).to_excel(xw, sheet_name="Actual", index=False)
    print(f"Created {OUT.name}: {len(LINES)} lines x 10 months")


if __name__ == "__main__":
    main()
