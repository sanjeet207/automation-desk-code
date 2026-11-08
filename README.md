# The Automation Desk: code from the videos

Real, tested Python automations from the YouTube channel **The Automation Desk**.
Every folder matches one video. All sample data is fictional, and nothing here is tax, legal or investment advice.

| # | Video | Folder |
|---|---|---|
| 1 | Reconcile two Excel files automatically | [01-reconcile-excel](01-reconcile-excel) |
| 2 | PDF bills → one Excel file | [02-pdf-bills-to-excel](02-pdf-bills-to-excel) |

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

Each folder has a test you can run, e.g. `python test_extract.py`.

MIT licensed. Use it, change it, share it.
