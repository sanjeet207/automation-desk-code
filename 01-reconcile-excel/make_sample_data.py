"""Generate FICTIONAL sample data for the reconciliation demo.

Nothing here is real: supplier names, GSTINs and amounts are invented so you
can show the video on screen without exposing any client or employer data.

Run:  python make_sample_data.py
Creates: data/purchase_register.xlsx  (what your books say)
         data/portal_data.xlsx        (what the supplier-reported portal data says)
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
GST_RATE = 0.18
OUT_DIR = Path(__file__).parent / "data"

SUPPLIERS = [
    ("Shree Ganesh Traders", "07AAAFS1111A1Z1"),
    ("Northstar Packaging", "07AAAFN2222B1Z2"),
    ("Bharat Office Supplies", "06AAAFB3333C1Z3"),
    ("Lotus Logistics", "09AAAFL4444D1Z4"),
    ("Orbit Electronics", "07AAAFO5555E1Z5"),
    ("Kaveri Stationers", "06AAAFK6666F1Z6"),
]


def _row(rng: random.Random, n: int) -> dict:
    name, gstin = rng.choice(SUPPLIERS)
    taxable = round(rng.uniform(5_000, 250_000), 2)
    inv_date = date(2026, 10, 1) + timedelta(days=rng.randint(0, 29))
    return {
        "invoice_no": f"INV/{n:04d}",
        "invoice_date": inv_date,
        "supplier_name": name,
        "supplier_gstin": gstin,
        "taxable_value": taxable,
        "gst_amount": round(taxable * GST_RATE, 2),
    }


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = random.Random(SEED)
    base = [_row(rng, n) for n in range(1, 61)]  # 60 invoices

    books = [dict(r) for r in base]
    portal = [dict(r) for r in base]

    # 1) Amount mismatches: taxable value differs (5 invoices)
    for i in (3, 11, 19, 27, 35):
        delta = rng.choice([-1, 1]) * round(rng.uniform(500, 8_000), 2)
        portal[i]["taxable_value"] = round(portal[i]["taxable_value"] + delta, 2)
        portal[i]["gst_amount"] = round(portal[i]["taxable_value"] * GST_RATE, 2)

    # 2) Invoice-number formatting differences: same invoice, typed differently (4)
    for i, new in ((5, "inv-6"), (13, "INV 0014"), (21, "Inv/22"), (29, "INV-030")):
        portal[i]["invoice_no"] = new

    # 2b) Real typos in the invoice number (digits swapped): the cleaner cannot fix these,
    #     so the script pairs them by supplier + amount instead (2)
    portal[37]["invoice_no"] = "INV/0083"  # should be INV/0038
    portal[51]["invoice_no"] = "INV/0502"  # should be INV/0052

    # 3) In books but not on the portal: supplier has not filed (4)
    for i in sorted((7, 15, 23, 31), reverse=True):
        portal.pop(i)

    # 4) On the portal but not in books: not booked yet (4)
    for k in range(4):
        extra = _row(rng, 101 + k)
        portal.append(extra)

    # 5) Duplicate entry in books: same invoice booked twice (2)
    books.append(dict(books[40]))
    books.append(dict(books[45]))

    return pd.DataFrame(books), pd.DataFrame(portal)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    books, portal = build()
    books.to_excel(OUT_DIR / "purchase_register.xlsx", index=False)
    portal.to_excel(OUT_DIR / "portal_data.xlsx", index=False)
    print(f"Wrote {len(books)} rows to purchase_register.xlsx")
    print(f"Wrote {len(portal)} rows to portal_data.xlsx")


if __name__ == "__main__":
    main()
