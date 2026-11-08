# Email every customer their own PDF (video 5)
Uses the statements from 04-pdf-statements (run that folder first).

    python send_statements.py                          # DRY RUN (default): writes emails to outbox/, sends nothing
    python send_statements.py --test-to you@gmail.com  # sends every email to you only
    python send_statements.py --send                   # real customers, after you type SEND
    python test_send.py                                # uses a fake mail server, sends nothing

For real sending set SMTP_USER and SMTP_PASSWORD (Gmail: an App Password, never your normal password).
A sent_log.csv is written as each email goes, so a re-run never emails anyone twice.
Check your provider's daily sending limit. Fictional sample data.
