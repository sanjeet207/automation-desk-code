"""Email every customer their own PDF statement, safely.

Modes (default is a dry run, which sends NOTHING):
  python send_statements.py                          dry run: writes each email to outbox/ so you can check it
  python send_statements.py --test-to you@gmail.com  sends every email to YOU only
  python send_statements.py --send                   sends to customers (asks you to type SEND first)

For real sending, set two environment variables (Gmail: use an App Password, not your normal password):
  export SMTP_USER="you@gmail.com"
  export SMTP_PASSWORD="your-16-letter-app-password"
"""
import argparse
import os
import re
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
STATEMENTS = HERE.parent / "04-pdf-statements"
COMPANY = "Brightdesk Supplies"
MONTH = "October 2026"
EMAIL_OK = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 465

BODY = """Hello {name},

Please find attached your statement for {month}.

{balance_line}

If anything looks wrong, just reply to this email.

Thank you,
Accounts team, {company}
"""


def balance_line(closing):
    if closing < 0:
        return f"Your account is in credit by {abs(closing):,.2f}. We owe you this amount."
    return f"The amount due is {closing:,.2f}."


def build_message(sender, to, row, pdf):
    msg = EmailMessage()
    msg["From"], msg["To"] = sender, to
    msg["Subject"] = f"Your {MONTH} statement from {COMPANY}"
    msg.set_content(BODY.format(name=row["name"], month=MONTH, company=COMPANY, balance_line=balance_line(row["closing_balance"])))
    msg.add_attachment(pdf.read_bytes(), maintype="application", subtype="pdf", filename=pdf.name)
    return msg


def plan(statements_dir):
    """Decide, for every customer, whether we can send, and if not, why."""
    log = pd.read_excel(statements_dir / "statements" / "statements_log.xlsx")
    customers = pd.read_excel(statements_dir / "customers.xlsx", sheet_name="Customers")
    df = customers[["customer_id", "email"]].merge(log, on="customer_id", how="left")
    reasons = []
    for _, r in df.iterrows():
        pdf = statements_dir / "statements" / str(r["file"])
        if not isinstance(r["file"], str) or not pdf.exists():
            reasons.append("Skip: no statement")
        elif not isinstance(r["email"], str) or not r["email"].strip():
            reasons.append("Skip: no email address")
        elif not EMAIL_OK.match(r["email"].strip()):
            reasons.append(f"Skip: email looks wrong ({r['email']})")
        else:
            reasons.append("Ready")
    df["plan"] = reasons
    return df


def run(df, statements_dir, mode, test_to=None, sent_log=HERE / "sent_log.csv", outbox=HERE / "outbox", smtp=None):
    already = set(pd.read_csv(sent_log)["customer_id"]) if (mode == "send" and sent_log.exists()) else set()
    sender = os.environ.get("SMTP_USER", "accounts@brightdesk.example")
    results = []
    for _, r in df.iterrows():
        if r["plan"] != "Ready":
            results.append((r["customer_id"], r["plan"])); continue
        if r["customer_id"] in already:
            results.append((r["customer_id"], "Skip: already sent earlier")); continue
        to = test_to or r["email"].strip()
        msg = build_message(sender, to, r, statements_dir / "statements" / r["file"])
        if mode == "dry":
            outbox.mkdir(exist_ok=True)
            (outbox / f"{r['customer_id']}.eml").write_bytes(bytes(msg))
            results.append((r["customer_id"], f"Written to outbox ({to})"))
        else:
            smtp.send_message(msg)
            results.append((r["customer_id"], f"Sent to {to}"))
            if mode == "send":  # remember it, so a re-run never sends twice
                pd.DataFrame([{"customer_id": r["customer_id"], "email": to, "time": pd.Timestamp.now()}]).to_csv(
                    sent_log, mode="a", header=not sent_log.exists(), index=False)
            time.sleep(1)  # be gentle with the mail server
    return pd.DataFrame(results, columns=["customer_id", "result"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--statements", default=str(STATEMENTS), help="folder with customers.xlsx and statements/")
    ap.add_argument("--test-to", help="send every email to this address only")
    ap.add_argument("--send", action="store_true", help="really send to customers")
    a = ap.parse_args()
    folder = Path(a.statements)
    df = plan(folder)
    ready = (df["plan"] == "Ready").sum()
    print(f"Customers: {len(df)}  |  ready to email: {ready}  |  skipped: {len(df) - ready}")
    for _, r in df[df["plan"] != "Ready"].iterrows():
        print(f"  {r['customer_id']} {r['name']}: {r['plan']}")
    mode = "send" if a.send else ("test" if a.test_to else "dry")
    if mode == "dry":
        res = run(df, folder, "dry")
        print(f"DRY RUN: nothing was sent. {res['result'].str.startswith('Written').sum()} emails written to outbox/ for you to check.")
        return
    if mode == "send" and input(f"Send {ready} emails to real customers? Type SEND to continue: ") != "SEND":
        print("Cancelled. Nothing was sent."); return
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        res = run(df, folder, mode, a.test_to, smtp=smtp)
    print(res["result"].value_counts().to_string())


if __name__ == "__main__":
    main()
