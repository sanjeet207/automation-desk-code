# A PDF statement for every customer (video 4)
Reads one Excel file (sheets: Customers, Transactions) and makes one PDF statement per customer:
opening balance, every invoice and payment, a running balance, and the amount due (or "in credit").

    python make_sample_data.py      # customers.xlsx: 24 fictional customers, 161 transactions
    python make_statements.py       # PDFs + statements_log.xlsx in statements/
    python make_statements.py --excel my_file.xlsx --out statements
    python test_statements.py

Result on the sample: 23 statements, plus 4 problems logged (a missing email, a customer with no
transactions, and 2 invoices with an unknown customer ID). Change COMPANY and PERIOD at the top.
Fictional sample data. Not accounting or tax advice.
