# Monthly finance report with charts (video 7)
Turns a sheet of transactions into a finished Excel report: Summary (with 2 live charts), Monthly P&L,
Expenses by category, and Data issues (duplicates, future-dated rows, blank categories).

    python make_sample_data.py      # transactions.xlsx: 410 fictional transactions, Jan to Oct 2026
    python finance_report.py        # writes finance_report.xlsx
    python finance_report.py --excel my_transactions.xlsx --out report.xlsx --as-of 2026-10-31
    python test_report.py

Columns needed: date, description, category, type (Income/Expense), amount (expenses negative).
Fictional sample data. Not financial, accounting or tax advice.
