"""Creates fictional sample PDF bills in bills/ (two different layouts, a few planted problems).

Planted on purpose, so the video has something real to catch:
  - 2 bills whose subtotal + tax does not equal the printed total
  - 1 bill with no invoice number
  - the same bill saved twice under different file names
"""
import random
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SEED = 7
OUT = Path(__file__).parent / "bills"
SUPPLIERS = ["Kaveri Stationers", "Northstar Packaging", "Orbit Electronics", "Bharat Office Supplies",
             "Shree Ganesh Traders", "Bluewave Logistics", "Lotus Print House"]
ITEMS = ["A4 paper ream", "Printer toner", "Packing tape", "Cardboard boxes", "USB cable",
         "Delivery charges", "Office chairs", "Labels roll", "Notebook pack", "Ink cartridge"]


def money(x: float) -> str:
    return f"{x:,.2f}"


def draw_layout_a(c, b):
    c.setFont("Helvetica-Bold", 20); c.drawString(50, 790, b["supplier"])
    c.setFont("Helvetica", 11)
    c.drawString(50, 765, "TAX INVOICE")
    if b["invoice_no"]:
        c.drawString(380, 790, f"Invoice No: {b['invoice_no']}")
    c.drawString(380, 772, f"Date: {b['date']:%d-%m-%Y}")
    y = 720
    c.setFont("Helvetica-Bold", 11); c.drawString(50, y, "Item"); c.drawString(300, y, "Qty"); c.drawString(450, y, "Amount")
    c.setFont("Helvetica", 11)
    for item, qty, amt in b["lines"]:
        y -= 20; c.drawString(50, y, item); c.drawString(300, y, str(qty)); c.drawRightString(520, y, money(amt))
    y -= 40
    c.drawString(350, y, "Subtotal:"); c.drawRightString(520, y, money(b["subtotal"]))
    c.drawString(350, y - 18, "Tax (18%):"); c.drawRightString(520, y - 18, money(b["tax"]))
    c.setFont("Helvetica-Bold", 12); c.drawString(350, y - 40, "Total:"); c.drawRightString(520, y - 40, money(b["total"]))


def draw_layout_b(c, b):
    c.setFont("Helvetica", 10)
    c.drawString(50, 800, "BILL")
    c.setFont("Helvetica-Bold", 16); c.drawString(50, 780, b["supplier"].upper())
    c.setFont("Helvetica", 10)
    if b["invoice_no"]:
        c.drawString(50, 750, f"Bill #  {b['invoice_no']}")
    c.drawString(50, 735, f"Bill date  {b['date']:%d %b %Y}")
    y = 690
    for item, qty, amt in b["lines"]:
        c.drawString(50, y, f"{qty} x {item}"); c.drawRightString(540, y, money(amt)); y -= 16
    y -= 30
    c.drawString(360, y, "Sub total"); c.drawRightString(540, y, money(b["subtotal"]))
    c.drawString(360, y - 15, "Tax"); c.drawRightString(540, y - 15, money(b["tax"]))
    c.setFont("Helvetica-Bold", 11); c.drawString(360, y - 35, "Amount due"); c.drawRightString(540, y - 35, money(b["total"]))


def build(n: int = 40) -> list[dict]:
    rng = random.Random(SEED)
    bills = []
    for i in range(1, n + 1):
        lines = []
        for _ in range(rng.randint(1, 4)):
            qty = rng.randint(1, 20)
            lines.append((rng.choice(ITEMS), qty, round(qty * rng.uniform(80, 2500), 2)))
        subtotal = round(sum(a for _, _, a in lines), 2)
        tax = round(subtotal * 0.18, 2)
        bills.append({"file": f"bill_{i:03d}.pdf", "supplier": rng.choice(SUPPLIERS), "invoice_no": f"INV-{1000 + i}",
                      "date": date(2026, 10, 1) + timedelta(days=rng.randint(0, 30)), "lines": lines,
                      "subtotal": subtotal, "tax": tax, "total": round(subtotal + tax, 2), "layout": "a" if i % 3 else "b"})
    bills[11]["total"] = round(bills[11]["total"] + 500, 2)      # total doesn't add up
    bills[27]["total"] = round(bills[27]["total"] - 90.5, 2)     # total doesn't add up
    bills[19]["invoice_no"] = ""                                 # missing invoice number
    dup = dict(bills[5]); dup["file"] = "bill_006_copy.pdf"      # same bill saved twice
    bills.append(dup)
    return bills


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.pdf"):
        old.unlink()
    bills = build()
    for b in bills:
        c = canvas.Canvas(str(OUT / b["file"]), pagesize=A4)
        (draw_layout_a if b["layout"] == "a" else draw_layout_b)(c, b)
        c.showPage(); c.save()
    print(f"Wrote {len(bills)} fictional sample bills to {OUT}")


if __name__ == "__main__":
    main()
