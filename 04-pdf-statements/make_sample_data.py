"""Creates customers.xlsx: 24 fictional customers and their October transactions, with a few planted problems.
Run: python make_sample_data.py"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "customers.xlsx"
NAMES = ["Asha Traders", "Blue Fern Cafe", "Cedar Dental", "Delta Print House", "Evergreen Clinic", "Fable Books",
         "Granite Builders", "Harbour Logistics", "Indigo Studio", "Juniper Hotels", "Kite Electronics", "Lotus Bakery",
         "Maple Interiors", "Nimbus Travel", "Orchid Salon", "Pioneer Motors", "Quartz Labs", "Riverbend School",
         "Saffron Kitchen", "Tidal Fitness", "Umber Textiles", "Vista Opticals", "Willow Pharmacy", "Zephyr Events"]


def main():
    rng = random.Random(5)
    customers, tx = [], []
    for i, name in enumerate(NAMES, 1):
        cid = f"C-{i:03d}"
        email = "accounts@" + name.lower().replace(" ", "") + ".example"
        if cid == "C-007":
            email = ""  # nobody saved this customer's email
        if cid == "C-015":
            email = "accounts@orchidsalon"  # typo: the .example part is missing
        customers.append({"customer_id": cid, "name": name, "email": email, "opening_balance": round(rng.uniform(0, 60000), 2)})
        if cid == "C-019":
            continue  # no activity this month
        for _ in range(rng.randint(3, 12)):
            day = rng.randint(1, 31)
            if rng.random() < 0.7:
                tx.append({"customer_id": cid, "date": pd.Timestamp(2026, 10, day), "reference": f"INV-{rng.randint(1000, 9999)}",
                           "description": "Invoice", "debit": round(rng.uniform(800, 25000), 2), "credit": 0.0})
            else:
                tx.append({"customer_id": cid, "date": pd.Timestamp(2026, 10, day), "reference": f"RCPT-{rng.randint(100, 999)}",
                           "description": "Payment received", "debit": 0.0, "credit": round(rng.uniform(1000, 30000), 2)})
    # two rows typed with a customer id that doesn't exist
    for ref in ("INV-5521", "INV-5522"):
        tx.append({"customer_id": "C-099", "date": pd.Timestamp(2026, 10, 14), "reference": ref, "description": "Invoice", "debit": 4200.0, "credit": 0.0})
    with pd.ExcelWriter(OUT) as xw:
        pd.DataFrame(customers).to_excel(xw, sheet_name="Customers", index=False)
        pd.DataFrame(tx).sort_values(["customer_id", "date"]).to_excel(xw, sheet_name="Transactions", index=False)
    print(f"Created {OUT.name}: {len(customers)} customers, {len(tx)} transactions")


if __name__ == "__main__":
    main()
