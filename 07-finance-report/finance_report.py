"""Turn a sheet of transactions into a finished monthly finance report with charts.
Run: python finance_report.py                    (uses transactions.xlsx)
     python finance_report.py --excel my_transactions.xlsx --out report.xlsx --as-of 2026-10-31
Columns needed: date, description, category, type (Income/Expense), amount (expenses negative).
"""
import argparse
from pathlib import Path

import pandas as pd


def load_and_check(path, as_of):
    df = pd.read_excel(path)
    df["date"] = pd.to_datetime(df["date"])
    issues = []
    dup = df.duplicated(keep="first")
    for _, r in df[dup].iterrows():
        issues.append({"date": r["date"].date(), "description": r["description"], "amount": r["amount"], "problem": "Duplicate row, left out"})
    df = df[~dup]
    future = df["date"] > as_of
    for _, r in df[future].iterrows():
        issues.append({"date": r["date"].date(), "description": r["description"], "amount": r["amount"], "problem": "Dated in the future, left out"})
    df = df[~future].copy()
    blank = df["category"].isna()
    for _, r in df[blank].iterrows():
        issues.append({"date": r["date"].date(), "description": r["description"], "amount": r["amount"], "problem": "No category, counted as Uncategorised"})
    df["category"] = df["category"].fillna("Uncategorised")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df, pd.DataFrame(issues)


def summarise(df):
    pnl = df.pivot_table(index="month", columns="type", values="amount", aggfunc="sum", fill_value=0)
    pnl = pd.DataFrame({"Revenue": pnl.get("Income", 0), "Expenses": -pnl.get("Expense", 0)})
    pnl["Profit"] = pnl["Revenue"] - pnl["Expenses"]
    pnl["Margin %"] = (pnl["Profit"] / pnl["Revenue"] * 100).round(1)
    pnl["Revenue growth %"] = (pnl["Revenue"].pct_change() * 100).round(1)
    last = df[df["month"] == pnl.index[-1]]
    by_cat = (-last[last["type"] == "Expense"].groupby("category")["amount"].sum()).sort_values(ascending=False)
    return pnl.round(2), by_cat.round(2)


def write(pnl, by_cat, issues, out):
    with pd.ExcelWriter(out, engine="xlsxwriter") as xw:
        wb = xw.book
        money, pct = wb.add_format({"num_format": "#,##0"}), wb.add_format({"num_format": "0.0"})
        bold = wb.add_format({"bold": True, "font_size": 14})
        # Summary sheet: headline numbers for the latest month
        ws = wb.add_worksheet("Summary"); xw.sheets["Summary"] = ws
        latest, prev = pnl.iloc[-1], pnl.iloc[-2]
        ws.write("A1", f"Finance report: {pnl.index[-1]}", bold)
        for i, (label, val, before) in enumerate([("Revenue", latest["Revenue"], prev["Revenue"]), ("Expenses", latest["Expenses"], prev["Expenses"]), ("Profit", latest["Profit"], prev["Profit"])]):
            ws.write(2 + i, 0, label); ws.write(2 + i, 1, val, money)
            ws.write(2 + i, 2, (val - before) / abs(before) * 100 if before else 0, pct); ws.write(2 + i, 3, "% vs last month")
        ws.write(5, 0, "Margin %"); ws.write(5, 1, latest["Margin %"], pct)
        ws.set_column("A:A", 14); ws.set_column("B:B", 14)
        # Monthly P&L with a chart
        pnl.to_excel(xw, sheet_name="Monthly P&L")
        pl = xw.sheets["Monthly P&L"]; pl.set_column("A:A", 10); pl.set_column("B:D", 13, money); pl.set_column("E:F", 16, pct)
        n = len(pnl)
        pl.conditional_format(1, 5, n, 5, {"type": "cell", "criteria": "<", "value": 0, "format": wb.add_format({"font_color": "#C00000"})})
        line = wb.add_chart({"type": "line"})
        for col, colour in ((1, "#00A88C"), (2, "#E46C0A"), (3, "#1F4E79")):
            line.add_series({"name": ["Monthly P&L", 0, col], "categories": ["Monthly P&L", 1, 0, n, 0],
                             "values": ["Monthly P&L", 1, col, n, col], "line": {"color": colour, "width": 2.5}})
        line.set_title({"name": "Revenue, expenses and profit"}); line.set_size({"width": 720, "height": 360})
        ws.insert_chart("F2", line)
        # Expenses by category for the latest month
        by_cat.to_frame("Amount").to_excel(xw, sheet_name="Expenses by category")
        ec = xw.sheets["Expenses by category"]; ec.set_column("A:A", 18); ec.set_column("B:B", 13, money)
        bar = wb.add_chart({"type": "bar"})
        bar.add_series({"name": "Expenses", "categories": ["Expenses by category", 1, 0, len(by_cat), 0],
                        "values": ["Expenses by category", 1, 1, len(by_cat), 1], "fill": {"color": "#00A88C"}})
        bar.set_title({"name": f"Expenses by category, {pnl.index[-1]}"}); bar.set_legend({"none": True}); bar.set_size({"width": 720, "height": 360})
        bar.set_y_axis({"reverse": True})
        ws.insert_chart("F21", bar)
        (issues if len(issues) else pd.DataFrame([{"problem": "None"}])).to_excel(xw, sheet_name="Data issues", index=False)
        xw.sheets["Data issues"].set_column("A:E", 22)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", default=str(Path(__file__).parent / "transactions.xlsx"))
    ap.add_argument("--out", default="finance_report.xlsx")
    ap.add_argument("--as-of", default="2026-10-31", help="ignore transactions after this date")
    a = ap.parse_args()
    df, issues = load_and_check(a.excel, pd.Timestamp(a.as_of))
    pnl, by_cat = summarise(df)
    write(pnl, by_cat, issues, a.out)
    last = pnl.iloc[-1]
    print(f"Transactions used: {len(df)}  |  months: {len(pnl)}  |  data issues: {len(issues)}")
    print(f"{pd.Period(pnl.index[-1]).strftime('%B %Y')}: revenue {last['Revenue']:,.0f} ({last['Revenue growth %']:+.1f}% vs last month), "
          f"expenses {last['Expenses']:,.0f}, profit {last['Profit']:,.0f}, margin {last['Margin %']:.1f}%")
    print(f"Biggest expense: {by_cat.index[0]} ({by_cat.iloc[0]:,.0f})")
    if len(issues):
        print(issues["problem"].value_counts().to_string())
    print(f"Saved: {a.out}  (Summary with 2 charts, Monthly P&L, Expenses by category, Data issues)")


if __name__ == "__main__":
    main()
