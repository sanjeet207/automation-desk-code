"""Make one PDF statement for every customer from one Excel file.
Run: python make_statements.py                       (uses customers.xlsx)
     python make_statements.py --excel my_file.xlsx --out statements
"""
import argparse
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

COMPANY = "Brightdesk Supplies (sample company)"
PERIOD = "1 to 31 October 2026"
TEAL = colors.HexColor("#00a88c")


def money(x):
    return f"{x:,.2f}"


def statement_rows(opening, tx):
    """Running balance: start from the opening balance, add debits, subtract credits."""
    rows, balance = [["Date", "Reference", "Description", "Debit", "Credit", "Balance"],
                     ["", "", "Opening balance", "", "", money(opening)]], opening
    for _, t in tx.iterrows():
        balance += t["debit"] - t["credit"]
        rows.append([t["date"].strftime("%d %b"), t["reference"], t["description"],
                     money(t["debit"]) if t["debit"] else "", money(t["credit"]) if t["credit"] else "", money(balance)])
    return rows, round(balance, 2)


def build_pdf(path, customer, rows, closing):
    st = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm)
    head = Table([[Paragraph(f"<b>{COMPANY}</b>", st["Title"]), ""]], colWidths=[130 * mm, 44 * mm])
    info = Table([["Statement for", customer["name"]], ["Customer ID", customer["customer_id"]], ["Period", PERIOD]],
                 colWidths=[35 * mm, 139 * mm])
    info.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (0, -1), colors.grey)]))
    body = Table(rows, colWidths=[18 * mm, 28 * mm, 52 * mm, 25 * mm, 25 * mm, 26 * mm], repeatRows=1)
    body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f4")]),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    label = "Amount due" if closing >= 0 else "In credit (we owe you)"
    total = Table([[label, money(abs(closing))]], colWidths=[148 * mm, 26 * mm])
    total.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 12),
                               ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LINEABOVE", (0, 0), (-1, 0), 1.5, TEAL)]))
    note = Paragraph("This statement was generated automatically. If anything looks wrong, reply to this email. "
                     "Fictional sample data.", st["Normal"])
    doc.build([head, Spacer(1, 6), info, Spacer(1, 10), body, Spacer(1, 6), total, Spacer(1, 14), note])


def make_all(excel, out):
    customers = pd.read_excel(excel, sheet_name="Customers")
    tx = pd.read_excel(excel, sheet_name="Transactions").fillna({"debit": 0, "credit": 0})
    out = Path(out); out.mkdir(exist_ok=True)
    known = set(customers["customer_id"])
    unknown = tx[~tx["customer_id"].isin(known)]
    log = []
    for _, c in customers.iterrows():
        mine = tx[tx["customer_id"] == c["customer_id"]].sort_values("date")
        if mine.empty:
            log.append({**c[["customer_id", "name"]], "file": "", "closing_balance": c["opening_balance"], "status": "Skipped: no transactions"})
            continue
        rows, closing = statement_rows(c["opening_balance"], mine)
        safe = "".join(ch for ch in c["name"] if ch.isalnum() or ch == " ").replace(" ", "_")
        pdf = out / f"{c['customer_id']}_{safe}.pdf"
        build_pdf(pdf, c, rows, closing)
        email_ok = "@" in str(c["email"])
        log.append({**c[["customer_id", "name"]], "file": pdf.name, "closing_balance": closing,
                    "status": "OK" if email_ok else "Created, but no email address"})
    for _, t in unknown.iterrows():
        log.append({"customer_id": t["customer_id"], "name": "?", "file": "", "closing_balance": None,
                    "status": f"Unknown customer ID on {t['reference']}"})
    return pd.DataFrame(log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", default=str(Path(__file__).parent / "customers.xlsx"))
    ap.add_argument("--out", default="statements")
    a = ap.parse_args()
    log = make_all(a.excel, a.out)
    log.to_excel(Path(a.out) / "statements_log.xlsx", index=False)
    made = log["file"].astype(bool).sum()
    print(f"Customers: {(log['name'] != '?').sum()}  |  PDF statements created: {made}")
    for _, r in log[log["status"] != "OK"].iterrows():
        print(f"  {r['customer_id']} {r['name']}: {r['status']}")
    print(f"Saved to: {a.out}/   (log: statements_log.xlsx)")


if __name__ == "__main__":
    main()
