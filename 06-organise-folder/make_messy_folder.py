"""Creates messy_downloads/: 120 fictional files with messy names, mixed types, dates and duplicates.
Run: python make_messy_folder.py"""
import os
import random
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

OUT = Path(__file__).parent / "messy_downloads"
KINDS = {
    ".pdf": ["Invoice {n}", "Scan {d}", "statement_{n}", "Bank letter", "Ticket {n}", "report FINAL"],
    ".xlsx": ["Budget {n}", "sales data", "Copy of tracker", "expenses {d}"],
    ".docx": ["Letter draft", "meeting notes {d}", "Proposal v{n}", "CV"],
    ".jpg": ["IMG_{n}", "WhatsApp Image {d}", "photo {n}"],
    ".png": ["Screenshot {d}", "logo", "diagram {n}"],
    ".csv": ["export_{n}", "contacts"],
    ".zip": ["archive {n}", "photos backup"],
    ".txt": ["notes", "todo {n}"],
}


def fake_bytes(ext, rng):
    if ext in (".jpg", ".png"):
        from io import BytesIO
        b = BytesIO()
        Image.new("RGB", (40, 30), tuple(rng.randint(0, 255) for _ in range(3))).save(b, "JPEG" if ext == ".jpg" else "PNG")
        return b.getvalue()
    return f"{ext} sample {rng.random()}".encode() * rng.randint(5, 50)


def main():
    rng = random.Random(3)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    made = []
    while len(made) < 111:
        ext = rng.choice(list(KINDS))
        when = datetime(2026, rng.randint(1, 10), rng.randint(1, 28), rng.randint(8, 20))
        name = rng.choice(KINDS[ext]).format(n=rng.randint(1, 999), d=when.strftime("%Y-%m-%d"))
        path = OUT / f"{name}{ext}"
        if path.exists():
            path = OUT / f"{name} (1){ext}"  # the browser's way of saying "again"
        if path.exists():
            continue
        path.write_bytes(fake_bytes(ext, rng))
        os.utime(path, (when.timestamp(), when.timestamp()))
        made.append(path)
    # 9 files downloaded twice under a different name
    for src in rng.sample(made, 9):
        dup = OUT / f"{src.stem} - Copy{src.suffix}"
        shutil.copy2(src, dup)
    print(f"Created {len(list(OUT.iterdir()))} files in {OUT.name}/")


if __name__ == "__main__":
    main()
