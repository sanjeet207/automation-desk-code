"""Creates messy_customers.xlsx: 500 fictional customer orders with the mess real exports have.
Run: python make_messy_data.py"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent / "messy_customers.xlsx"
FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Sara", "Arjun", "Isha", "Neel", "Tara", "Omar", "Leah", "Jas", "Nina", "Vikram"]
LAST = ["Sharma", "Gill", "Patel", "Khan", "Singh", "Brown", "Mehta", "Rao", "Kapoor", "Smith", "Dhillon", "Iyer"]
CITIES = ["Delhi", "Mumbai", "Toronto", "London", "Pune", "Chandigarh", "Bengaluru"]


def main():
    rng = random.Random(9)
    rows = []
    for i in range(1, 486):
        f, l = rng.choice(FIRST), rng.choice(LAST)
        d = pd.Timestamp(2026, rng.randint(1, 10), rng.randint(1, 28))
        amt = round(rng.uniform(300, 25000), 2)
        name = f"{f} {l}"
        city = rng.choice(CITIES)
        phone = f"98{rng.randint(10000000, 99999999)}"
        email = f"{f}.{l}{i}@example.com".lower()
        # the mess
        r = rng.random()
        if r < 0.15: name = f"  {name.upper()} "
        elif r < 0.25: name = name.lower() + "  "
        if rng.random() < 0.2: city = rng.choice([city.lower(), city.upper(), f" {city}"])
        p = rng.random()
        if p < 0.2: phone = f"+91 {phone[:5]} {phone[5:]}"
        elif p < 0.35: phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
        elif p < 0.4: phone = f"0{phone}"
        dp = rng.random()
        date = d.strftime("%Y-%m-%d") if dp < 0.5 else d.strftime("%d/%m/%Y") if dp < 0.75 else d.strftime("%d %b %Y") if dp < 0.95 else "TBC"
        ap = rng.random()
        amount = amt if ap < 0.6 else f"₹{amt:,.2f}" if ap < 0.8 else f"{amt:,.2f}" if ap < 0.95 else f"Rs. {amt:,.0f}"
        if rng.random() < 0.08: email = email.upper()
        if rng.random() < 0.02: email = email.replace("@", " at ")
        rows.append({"Order ID": f"ORD-{i:04d}", "Customer Name": name, "City": city, "Phone": phone, "Email": email, "Order Date": date, "Amount": amount})
    df = pd.DataFrame(rows)
    dupes = df.sample(12, random_state=4).copy()
    dupes["Customer Name"] = dupes["Customer Name"].str.strip().str.title() + " "   # same order, typed again slightly differently
    blank = pd.DataFrame([{c: None for c in df.columns}] * 3)
    total = pd.DataFrame([{"Order ID": "TOTAL", "Amount": "see above"}])
    df = pd.concat([df, dupes, blank], ignore_index=True).sample(frac=1, random_state=5)
    df = pd.concat([df, total], ignore_index=True)
    df.to_excel(OUT, index=False)
    print(f"Created {OUT.name}: {len(df)} rows")


if __name__ == "__main__":
    main()
