# Budget vs actual variance report (video 8)
Compares budget with actual for every line, marks each variance Favourable or Unfavourable, explains the
material ones in a sentence (big in % AND in money), and flags lines that have been off for several months.

    python make_sample_data.py      # budget_actual.xlsx: 10 lines x 10 months, fictional
    python variance.py              # writes budget_vs_actual.xlsx (this month + year to date)
    python variance.py --excel my_file.xlsx --month 2026-10 --pct 10 --amount 5000
    python test_variance.py

Sheets needed: Budget (month, type, line, budget) and Actual (month, type, line, actual); type = Revenue or Expense.
Fictional sample data. Not financial or accounting advice.
