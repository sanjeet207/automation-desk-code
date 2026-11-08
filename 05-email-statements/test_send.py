"""Tests the email script without sending anything real (uses a fake mail server). Run: python test_send.py"""
import tempfile
from pathlib import Path

import send_statements as s

s.time.sleep = lambda _: None  # no waiting in tests


class FakeSMTP:
    def __init__(self): self.sent = []
    def send_message(self, msg): self.sent.append(msg)


def main():
    tmp = Path(tempfile.mkdtemp())
    df = s.plan(s.STATEMENTS)
    plans = dict(zip(df["customer_id"], df["plan"]))
    assert (df["plan"] == "Ready").sum() == 21
    assert plans["C-007"] == "Skip: no email address"
    assert plans["C-015"].startswith("Skip: email looks wrong")
    assert plans["C-019"] == "Skip: no statement"
    # dry run writes files and sends nothing
    res = s.run(df, s.STATEMENTS, "dry", outbox=tmp / "outbox")
    assert len(list((tmp / "outbox").glob("*.eml"))) == 21
    # test mode: everything goes to one address only
    fake = FakeSMTP()
    s.run(df, s.STATEMENTS, "test", test_to="me@example.com", smtp=fake)
    assert len(fake.sent) == 21 and {m["To"] for m in fake.sent} == {"me@example.com"}
    # real mode twice: the second run must send nothing
    log = tmp / "sent_log.csv"
    fake1, fake2 = FakeSMTP(), FakeSMTP()
    s.run(df, s.STATEMENTS, "send", sent_log=log, smtp=fake1)
    res2 = s.run(df, s.STATEMENTS, "send", sent_log=log, smtp=fake2)
    assert len(fake1.sent) == 21 and len(fake2.sent) == 0
    assert (res2["result"] == "Skip: already sent earlier").sum() == 21
    # each customer gets their own PDF, never someone else's
    for m in fake1.sent:
        pdf = next(m.iter_attachments()).get_filename()
        cid = pdf.split("_")[0]
        assert df.set_index("customer_id").loc[cid, "email"] == m["To"], (pdf, m["To"])
    print("All email tests passed.")


main()
