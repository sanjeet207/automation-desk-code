"""Tests for categorise.py, including the AI path with a fake model (no key, no cost). Run: python test_categorise.py"""
import pandas as pd

import categorise as c
import make_sample_data as m


def main():
    m.main()
    df = pd.read_excel(m.OUT)
    truth = pd.read_csv(m.OUT.parent / "answer_key.csv")["true_category"]
    rules = [(str(k).upper(), v) for k, v in pd.read_csv(m.OUT.parent / "rules.csv").itertuples(index=False, name=None)]
    out = c.categorise(df, rules)
    placed = out["category"] != "Uncategorised"
    assert (out.loc[placed, "category"] == truth[placed]).all()        # rules never guess wrong on this data
    assert c.mask("UPI/9876543210@YBL") == "UPI/##########@YBL"         # no digits leave the computer
    seen = []

    def fake_ai(descriptions, categories):
        seen.extend(descriptions)
        # one good answer, one answer outside the allowed list (must be ignored by the caller's check)
        return {d: ("Meals", "AI: food delivery") for d in descriptions if "ZMT" in d}

    ai_out = c.categorise(df, rules, use_ai=True, ai=fake_ai)
    assert seen and all(not any(ch.isdigit() for ch in d) for d in seen)  # masked before sending
    assert len(seen) <= (out["status"] == "Needs review").sum()          # only unsure rows are sent
    assert (ai_out.loc[ai_out["description"].str.contains("ZMT"), "status"] == "Check: AI suggestion").all()
    try:
        from typing import Literal
        class Checked(c.Suggestion):
            category: Literal["Meals", "Travel"]
        Checked(description="x", category="Crypto", reason="?")
        raise AssertionError("an answer outside the categories must be rejected")
    except c.ValidationError:
        pass
    print("All categoriser tests passed.")


main()
