"""Budget vs actual, with every variance labelled and explained in a sentence.
Run: python variance.py                         (uses budget_actual.xlsx, latest month)
     python variance.py --excel my_file.xlsx --month 2026-10 --pct 10 --amount 5000
Sheets needed: Budget (month, type, line, budget) and Actual (month, type, line, actual).
"""
import argparse
from pathlib import Path

import pandas as pd


def compare(budget, actual, pct, amount):
    df = budget.merge(actual, on=["month", "type", "line"], how="outer").fillna({"budget": 0, "actual": 0})
    df["variance"] = (df["actual"] - df["budget"]).round(2)
    df["variance %"] = (df["variance"] / df["budget"].where(df["budget"] != 0) * 100).round(1)
    # more revenue is good news; more expense is bad news
    good = ((df["type"] == "Revenue") & (df["variance"] > 0)) | ((df["type"] == "Expense") & (df["variance"] < 0))
    df["result"] = good.map({True: "Favourable", False: "Unfavourable"}).where(df["variance"] != 0, "On budget")
    # only explain what matters: big in percent AND big in money
    df["material"] = (df["variance %"].abs() >= pct) & (df["variance"].abs() >= amount)
    df["comment"] = df.apply(lambda r: explain(r) if r["material"] else "", axis=1)
    return df


def streaks(full, month):
    """How many months in a row each line has been materially off budget in the same direction."""
    out = {}
    for line, g in full[full["month"] <= month].sort_values("month").groupby("line"):
        n, last = 0, None
        for _, r in g.iloc[::-1].iterrows():
            if not r["material"] or (last and r["result"] != last):
                break
            n, last = n + 1, r["result"]
        out[line] = n
    return out


def explain(r):
    word = "over" if r["variance"] > 0 else "under"
    return f"{r['line']} is {abs(r['variance']):,.0f} ({abs(r['variance %']):.0f}%) {word} budget: {r['result'].lower()}."


def totals(df):
    t = df.groupby("type")[["budget", "actual"]].sum()
    profit_b = t.loc["Revenue", "budget"] - t.loc["Expense", "budget"]
    profit_a = t.loc["Revenue", "actual"] - t.loc["Expense", "actual"]
    return t, profit_b, profit_a


def write(month_df, ytd_df, out, month):
    cols = ["type", "line", "budget", "actual", "variance", "variance %", "result", "comment"]
    with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
        wb = xw.book
        green = wb.add_format({"bg_color": "#E2F4EC", "font_color": "#0B6B3A"})
        red = wb.add_format({"bg_color": "#FBE4E4", "font_color": "#9C1C1C"})
        money = wb.add_format({"num_format": "#,##0"})
        for name, df in ((f"Month {month}", month_df), ("Year to date", ytd_df)):
            df[cols].to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            ws.set_column("A:A", 10); ws.set_column("B:B", 16); ws.set_column("C:E", 13, money); ws.set_column("F:G", 13); ws.set_column("H:H", 60)
            n = len(df)
            ws.conditional_format(1, 6, n, 6, {"type": "cell", "criteria": "==", "value": '"Favourable"', "format": green})
            ws.conditional_format(1, 6, n, 6, {"type": "cell", "criteria": "==", "value": '"Unfavourable"', "format": red})
            ws.freeze_panes(1, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", default=str(Path(__file__).parent / "budget_actual.xlsx"))
    ap.add_argument("--month", default=None, help="e.g. 2026-10 (default: latest)")
    ap.add_argument("--pct", type=float, default=10, help="material if at least this % off budget ...")
    ap.add_argument("--amount", type=float, default=5000, help="... and at least this much money")
    ap.add_argument("--out", default="budget_vs_actual.xlsx")
    a = ap.parse_args()
    budget = pd.read_excel(a.excel, sheet_name="Budget"); actual = pd.read_excel(a.excel, sheet_name="Actual")
    month = a.month or max(actual["month"])
    full = compare(budget, actual, a.pct, a.amount)
    month_df = full[full["month"] == month].drop(columns="month").sort_values(["type", "line"], ascending=[False, True])
    run = streaks(full, month)
    month_df["comment"] = month_df.apply(lambda r: r["comment"] + (f" {run[r['line']]} months in a row." if run[r["line"]] >= 2 else ""), axis=1)
    ytd = full[full["month"] <= month].groupby(["type", "line"], as_index=False)[["budget", "actual"]].sum()
    ytd = ytd.assign(month="ytd")
    ytd_df = compare(ytd.drop(columns="actual"), ytd.drop(columns="budget"), a.pct, a.amount).drop(columns="month").sort_values(["type", "line"], ascending=[False, True])
    write(month_df, ytd_df, a.out, month)
    _, pb, pa = totals(month_df)
    print(f"{pd.Period(month).strftime('%B %Y')}: profit {pa:,.0f} vs budget {pb:,.0f}  ({pa - pb:+,.0f})")
    flagged = month_df[month_df["material"]].sort_values("variance", key=abs, ascending=False)
    print(f"Material variances: {len(flagged)} of {len(month_df)} lines  (rule: {a.pct:.0f}% and {a.amount:,.0f})")
    for c in flagged["comment"]:
        print("  " + c)
    print(f"Saved: {a.out}  (this month + year to date, colour-coded)")


if __name__ == "__main__":
    main()
