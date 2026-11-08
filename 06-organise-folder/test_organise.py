"""Apply, check, then undo, on a temporary copy. Run: python test_organise.py"""
import hashlib
import shutil
import tempfile
from pathlib import Path

import make_messy_folder as m
import organise as o


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): hashlib.md5(p.read_bytes()).hexdigest()
            for p in folder.rglob("*") if p.is_file()}


def main():
    tmp = Path(tempfile.mkdtemp()) / "messy"
    m.OUT = tmp
    m.main()
    before = snapshot(tmp)
    plan = o.make_plan(tmp)
    assert len(plan) == 120 and plan["reason"].str.startswith("duplicate").sum() == 9
    assert plan["to"].is_unique  # no two files land on the same name
    assert snapshot(tmp) == before  # making a plan moves nothing
    o.apply(plan, tmp / "undo_log.csv")
    after = snapshot(tmp)
    assert sorted(v for k, v in after.items() if k != "undo_log.csv") == sorted(before.values())  # nothing lost
    assert len(list((tmp / "_duplicates").iterdir())) == 9
    assert all(n.split("/")[0] in list(o.TYPES) + ["_duplicates", "Other", "undo_log.csv"] for n in after)
    o.undo(tmp / "undo_log.csv")
    assert snapshot(tmp) == before  # undo puts every file back
    shutil.rmtree(tmp.parent)
    print("All organise tests passed.")


main()
