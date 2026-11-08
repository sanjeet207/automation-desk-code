# Organise a messy folder (video 6)
Sorts every file by type and month, renames it to date_clean-name, and moves duplicates to _duplicates/.
Nothing is deleted, and nothing moves until you add --apply.

    python make_messy_folder.py                 # 120 fictional files in messy_downloads/
    python organise.py                          # DRY RUN: prints the plan, saves organise_plan.csv
    python organise.py --apply                  # moves files, saves undo_log.csv
    python organise.py --undo                   # puts every file back
    python organise.py --folder ~/Downloads     # your own folder (try it on a copy first)
    python test_organise.py
