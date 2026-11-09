# Categorise bank transactions: rules, fuzzy matching, optional AI (video 10)
Layers, cheapest and most reliable first:
1. Your rules (rules.csv: keyword -> category). Exact and explainable.
2. Fuzzy matching against descriptions your rules already placed, with a confidence score and a threshold.
3. Optional AI (--ai) for the rows still unsure: digits masked, only descriptions sent, every answer validated
   against your categories with Pydantic, and marked "Check: AI suggestion", never accepted blindly.

    python make_sample_data.py      # bank_statement.xlsx: 190 fictional transactions + answer_key.csv
    python categorise.py            # writes categorised.xlsx (Transactions, Spend by category, Needs review)
    python evaluate.py              # measures each approach against the answer key
    python categorise.py --ai       # optional, needs ANTHROPIC_API_KEY
    python test_categorise.py

Synthetic data only. Never put real bank logins, account numbers or statements into code you share.
Not financial, accounting or tax advice.
