# Clean messy Excel data in one run (video 9)
Fixes the usual mess in an export (spaces and capitals, phone formats, upper-case emails, three date formats
in one column, amounts stored as text with currency signs, duplicates, blank rows, a TOTAL row) and logs
every change. Anything code should not guess goes to a "Needs a human" sheet.

    python make_messy_data.py       # messy_customers.xlsx: 501 fictional rows
    python clean_data.py            # writes clean_customers.xlsx (Clean data, What changed, Needs a human)
    python clean_data.py --excel my_export.xlsx --out clean.xlsx
    python test_clean.py

Change the column names in clean_data.py to match your file. Fictional sample data.
