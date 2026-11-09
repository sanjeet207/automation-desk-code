# The Automation Desk: code from the videos

Real, tested Python automations from the YouTube channel **The Automation Desk**.
Every folder matches one video. All sample data is fictional, and nothing here is tax, legal or investment advice.

| # | Video | Folder |
|---|---|---|
| 1 | Reconcile two Excel files automatically | [01-reconcile-excel](01-reconcile-excel) |
| 2 | PDF bills → one Excel file | [02-pdf-bills-to-excel](02-pdf-bills-to-excel) |
| 3 | Combine many Excel files into one | [03-combine-excel-files](03-combine-excel-files) |
| 4 | A PDF statement for every customer | [04-pdf-statements](04-pdf-statements) |
| 5 | Email every customer their own PDF | [05-email-statements](05-email-statements) |
| 6 | Organise a messy folder | [06-organise-folder](06-organise-folder) |
| 7 | Monthly finance report with charts | [07-finance-report](07-finance-report) |
| 8 | Budget vs actual variance report | [08-budget-vs-actual](08-budget-vs-actual) |
| 9 | Clean messy Excel data | [09-clean-messy-data](09-clean-messy-data) |
| 10 | Categorise bank transactions: rules, fuzzy, AI | [10-categorise-bank](10-categorise-bank) |

## Setup (once)
    python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

## Video 1: reconcile two Excel files
    cd 01-reconcile-excel
    python reconcile.py                 # uses the sample files in data/
    python reconcile.py --books my_books.xlsx --portal supplier.xlsx

## Video 2: PDF bills to Excel
    cd 02-pdf-bills-to-excel
    python make_sample_bills.py         # creates 41 fictional sample PDF bills in bills/
    python extract_bills.py             # writes bills_summary.xlsx
    python extract_bills.py --folder my_bills --out my_bills.xlsx

Videos 3 onward: see the README inside each folder.

Each folder has a test you can run, e.g. `python test_extract.py`.

MIT licensed. Use it, change it, share it.
