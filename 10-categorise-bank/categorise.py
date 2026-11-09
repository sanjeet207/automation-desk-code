"""Categorise bank transactions in layers: your rules, then fuzzy matching, then (optionally) AI.
Only the uncertain rows ever reach the AI, with digits masked, and every AI answer is checked
against your list of categories and sent to "Needs review", never accepted blindly.

Run: python categorise.py                          (uses bank_statement.xlsx and rules.csv)
     python categorise.py --excel my_statement.xlsx --rules my_rules.csv --min-score 0.75
     python categorise.py --ai                     (optional: needs ANTHROPIC_API_KEY)
"""
import argparse
import difflib
import json
import logging
import os
import re
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ValidationError

HERE = Path(__file__).parent
log = logging.getLogger("categorise")


def normalise(desc):
    """'UPI/ZOMATO/48213' -> 'UPI ZOMATO': drop numbers and symbols, so variants of one merchant look alike."""
    return re.sub(r"\s+", " ", re.sub(r"[\d*/@#.\-]+", " ", str(desc).upper())).strip()


def mask(desc):
    """Hide every digit before text leaves your computer: phone numbers, card and reference numbers."""
    return re.sub(r"\d", "#", str(desc))


def by_rules(desc, rules):
    d = str(desc).upper()
    for kw, cat in rules:
        if kw in d:
            return cat, 1.0, f"rule: {kw}"
    return None, 0.0, None


def by_fuzzy(desc, known, min_score):
    """Closest description already categorised by a rule, with a similarity score from 0 to 1."""
    best, score = None, 0.0
    for k in known:
        s = difflib.SequenceMatcher(None, normalise(desc), k).ratio()
        if s > score:
            best, score = k, s
    if best and score >= min_score:
        return known[best], round(score, 2), f"similar to '{best}'"
    return None, round(score, 2), None


class Suggestion(BaseModel):
    description: str
    category: str
    reason: str


def by_ai(descriptions, categories):
    """Structured output: the model must return JSON we can validate; anything outside the categories is dropped."""
    import anthropic
    Allowed = Literal[tuple(categories)]  # noqa: N806

    class Checked(Suggestion):
        category: Allowed

    prompt = ("Categorise these business bank transactions. Allowed categories: " + ", ".join(categories) +
              ". Reply with only a JSON list of objects with keys description, category, reason (max 8 words). "
              "If you are not confident, use the category Unknown.\n\n" + "\n".join(descriptions))
    msg = anthropic.Anthropic().messages.create(model=os.environ.get("AGENT_MODEL", "claude-haiku-4-5"), max_tokens=2000,
                                                messages=[{"role": "user", "content": prompt}])
    text = msg.content[0].text
    out = {}
    for item in json.loads(text[text.find("["): text.rfind("]") + 1]):
        try:
            s = Checked(**item)
            out[s.description] = (s.category, "AI: " + s.reason)
        except ValidationError:
            log.warning("AI answer rejected (not an allowed category): %s", item)
    return out


def categorise(df, rules, min_score=0.75, use_ai=False, ai=by_ai):
    df = df.copy()
    found = [by_rules(d, rules) for d in df["description"]]
    df["category"], df["confidence"], df["how"] = zip(*found)
    known = {normalise(d): c for d, c in zip(df["description"], df["category"]) if isinstance(c, str)}
    for i in df.index[df["category"].isna()]:
        df.loc[i, ["category", "confidence", "how"]] = by_fuzzy(df.at[i, "description"], known, min_score)
    df["status"] = ["OK" if isinstance(h, str) and h.startswith("rule") else "Check: fuzzy match" if isinstance(h, str) else "Needs review"
                    for h in df["how"]]
    unsure = df["status"] == "Needs review"
    log.info("rules: %d, fuzzy: %d, unsure: %d", (df["status"] == "OK").sum(), (df["status"] == "Check: fuzzy match").sum(), unsure.sum())
    if use_ai and unsure.any():
        cats = sorted({c for _, c in rules})
        masked = df.loc[unsure, "description"].map(mask)
        answers = ai(sorted(set(masked)), cats)
        for i in df.index[unsure]:
            if masked[i] in answers:
                df.at[i, "category"], df.at[i, "how"] = answers[masked[i]]
                df.at[i, "status"] = "Check: AI suggestion"
    df["category"] = df["category"].fillna("Uncategorised")
    return df


def main():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", default=str(HERE / "bank_statement.xlsx"))
    ap.add_argument("--rules", default=str(HERE / "rules.csv"))
    ap.add_argument("--min-score", type=float, default=0.75, help="fuzzy matches below this score are not used")
    ap.add_argument("--ai", action="store_true", help="ask AI about the rows rules and fuzzy matching could not place")
    ap.add_argument("--out", default="categorised.xlsx")
    a = ap.parse_args()
    df = pd.read_excel(a.excel)
    missing = {"date", "description", "debit", "credit"} - set(df.columns)
    if missing:
        raise SystemExit(f"Your file is missing these columns: {', '.join(sorted(missing))}")
    rules = [(str(k).upper(), c) for k, c in pd.read_csv(a.rules).itertuples(index=False, name=None)]
    out = categorise(df, rules, a.min_score, a.ai)
    out["month"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m")
    spend = out[out["debit"].notna()].pivot_table(index="category", columns="month", values="debit", aggfunc="sum", fill_value=0).round(0)
    spend["Total"] = spend.sum(axis=1); spend = spend.sort_values("Total", ascending=False)
    with pd.ExcelWriter(a.out, engine="xlsxwriter") as xw:
        out.drop(columns="month").to_excel(xw, sheet_name="Transactions", index=False)
        spend.to_excel(xw, sheet_name="Spend by category")
        out[out["status"] != "OK"].drop(columns="month").to_excel(xw, sheet_name="Needs review", index=False)
        for ws in xw.sheets.values():
            ws.set_column("A:A", 12); ws.set_column("B:B", 28); ws.set_column("C:H", 15); ws.freeze_panes(1, 0)
    c = out["status"].value_counts()
    print(f"Transactions: {len(out)}  |  by your rules: {c.get('OK', 0)}  |  fuzzy matches to check: {c.get('Check: fuzzy match', 0)}"
          f"  |  AI suggestions to check: {c.get('Check: AI suggestion', 0)}  |  needs review: {c.get('Needs review', 0)}")
    print(f"Categorised: {(out['category'] != 'Uncategorised').mean() * 100:.0f}%  |  would go to AI with --ai: {c.get('Needs review', 0)} of {len(out)} rows")
    print("Top spend (3 months):", ", ".join(f"{k} {v:,.0f}" for k, v in spend["Total"].head(3).items()))
    print(f"Saved: {a.out}  (Transactions, Spend by category, Needs review)")


if __name__ == "__main__":
    main()
