# Combine many Excel files into one (video 3)
Combines a folder of Excel files into one master file, even when the columns are named differently,
some files have a title row above the table, or the same file was saved twice.

    python make_sample_data.py      # 50 fictional files in monthly_files/
    python combine.py               # writes master_sales.xlsx (All data, Monthly summary, File log)
    python combine.py --folder my_files --out master.xlsx
    python test_combine.py

Result on the sample: 50 files found, 47 combined into 1,140 rows, 3 skipped with a reason
(an empty month, a duplicate copy, and a contacts file that isn't sales data).
Add your own column names to COLUMN_NAMES. All data is fictional.
