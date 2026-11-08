"""Organise a messy folder: sort by type and month, clean the names, and set duplicates aside.
Nothing is deleted, and nothing moves until you say so.

  python organise.py                        dry run: shows the plan and saves organise_plan.csv
  python organise.py --apply                does the moves, and saves undo_log.csv
  python organise.py --undo                 puts every file back where it was
  python organise.py --folder ~/Downloads   use your own folder
"""
import argparse
import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
TYPES = {
    "PDFs": [".pdf"], "Spreadsheets": [".xlsx", ".xls", ".csv"], "Documents": [".docx", ".doc", ".txt"],
    "Images": [".jpg", ".jpeg", ".png", ".heic"], "Archives": [".zip", ".rar"],
}
FOLDER_FOR = {ext: folder for folder, exts in TYPES.items() for ext in exts}


def clean_name(path, when):
    """'WhatsApp Image 2026-03-04 (1).jpg' -> '2026-03-04_whatsapp-image.jpg'"""
    stem = re.sub(r"\(\d+\)|- copy|\d{4}-\d{2}-\d{2}", "", path.stem, flags=re.I)
    stem = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "file"
    return f"{when:%Y-%m-%d}_{stem}{path.suffix.lower()}"


def make_plan(folder):
    folder = Path(folder)
    files = sorted((p for p in folder.iterdir() if p.is_file() and not p.name.startswith(".")),
                   key=lambda p: (len(p.name), p.name))  # shortest name first = the original
    seen, rows, taken = {}, [], set()
    for p in files:
        digest = hashlib.md5(p.read_bytes()).hexdigest()
        when = datetime.fromtimestamp(p.stat().st_mtime)
        if digest in seen:
            dest, reason = folder / "_duplicates" / p.name, f"duplicate of {seen[digest]}"
        else:
            seen[digest] = p.name
            sub = FOLDER_FOR.get(p.suffix.lower(), "Other")
            dest = folder / sub / f"{when:%Y-%m}" / clean_name(p, when)
            reason = sub
        n = 2
        while dest in taken:  # two files that clean to the same name
            dest = dest.with_name(f"{dest.stem}_{n}{dest.suffix}"); n += 1
        taken.add(dest)
        rows.append({"from": str(p), "to": str(dest), "reason": reason})
    return pd.DataFrame(rows)


def apply(plan, undo_log):
    for _, r in plan.iterrows():
        dest = Path(r["to"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise SystemExit(f"Stopped: {dest} already exists. Nothing was overwritten.")
        Path(r["from"]).rename(dest)
    plan.to_csv(undo_log, index=False)


def undo(undo_log):
    plan = pd.read_csv(undo_log)
    for _, r in plan.iloc[::-1].iterrows():
        Path(r["to"]).rename(r["from"])
    for d in sorted({Path(t).parent for t in plan["to"]}, key=lambda p: -len(p.parts)):
        for x in (d, d.parent):
            if x.exists() and not any(x.iterdir()):
                x.rmdir()
    Path(undo_log).unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=str(HERE / "messy_downloads"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--undo", action="store_true")
    a = ap.parse_args()
    undo_log = Path(a.folder) / "undo_log.csv"
    if a.undo:
        undo(undo_log); print("Undone. Every file is back where it was."); return
    plan = make_plan(a.folder)
    dups = plan["reason"].str.startswith("duplicate").sum()
    print(f"Files: {len(plan)}  |  to sort: {len(plan) - dups}  |  duplicates set aside: {dups}")
    for kind, n in plan[plan["reason"].isin(list(TYPES) + ["Other"])]["reason"].value_counts().items():
        print(f"  {kind}: {n}")
    print("Examples:")
    names = plan["from"].map(lambda f: Path(f).name)
    for pattern in ("WhatsApp", r"\(1\)", "- Copy"):
        r = plan[names.str.contains(pattern)].iloc[0]
        print(f"  {Path(r['from']).name}  ->  {Path(r['to']).relative_to(a.folder)}")
    if a.apply:
        apply(plan, undo_log)
        print(f"Done. Moved {len(plan)} files. Nothing deleted. To reverse: python organise.py --undo")
    else:
        plan.to_csv(HERE / "organise_plan.csv", index=False)
        print("DRY RUN: nothing moved. Full plan saved to organise_plan.csv")


if __name__ == "__main__":
    main()
