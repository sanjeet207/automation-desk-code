"""Measure, don't guess: compare each approach with the answer key the sample data was made from.
Run: python evaluate.py"""
from pathlib import Path

import pandas as pd

import categorise as c

HERE = Path(__file__).parent


def score(pred, truth):
    placed = pred["category"] != "Uncategorised"
    right = (pred["category"] == truth.fillna("(no answer)")) & placed
    return {"categorised": f"{placed.mean() * 100:.0f}%", "correct when categorised": f"{right.sum() / max(placed.sum(), 1) * 100:.0f}%",
            "left for a person": int((~placed).sum())}


def main():
    df = pd.read_excel(HERE / "bank_statement.xlsx")
    truth = pd.read_csv(HERE / "answer_key.csv")["true_category"]
    rules = [(str(k).upper(), v) for k, v in pd.read_csv(HERE / "rules.csv").itertuples(index=False, name=None)]
    learned = rules + [(str(k).upper(), v) for k, v in pd.read_csv(HERE / "rules_after_review.csv").itertuples(index=False, name=None)]
    rows = {"1. Rules only": score(c.categorise(df, rules, min_score=1.01), truth),
            "2. Rules + fuzzy (0.75)": score(c.categorise(df, rules, min_score=0.75), truth),
            "3. Rules + fuzzy (0.60)": score(c.categorise(df, rules, min_score=0.60), truth),
            "4. Rules + fuzzy (0.50)": score(c.categorise(df, rules, min_score=0.50), truth),
            "5. After review: 6 new rules": score(c.categorise(df, learned, min_score=0.75), truth)}
    table = pd.DataFrame(rows).T
    print(table.to_string())
    table.to_csv(HERE / "evaluation.csv")


if __name__ == "__main__":
    main()
