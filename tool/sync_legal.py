#!/usr/bin/env python3
"""Copy legal documents from the product repositories into content/legal/.

The source of truth for a policy stays in the product's own repository, because
the product also ships the same text inside the app. This script mirrors those
files here so the site can be built without the product repositories present.

    python tool/sync_legal.py           # copy
    python tool/sync_legal.py --check   # fail if the copies have drifted

If a source repository is missing the file is left alone - the site still builds
from whatever is already in content/legal/.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (source file, destination inside content/legal/)
SOURCES: list[tuple[Path, Path]] = [
    (Path(r"C:\dev\companion_app\docs\legal\PRIVACY_POLICY.md"),
     ROOT / "content" / "legal" / "meloom" / "privacy.en.md"),
    (Path(r"C:\dev\companion_app\docs\legal\PRIVACY_POLICY_KO.md"),
     ROOT / "content" / "legal" / "meloom" / "privacy.ko.md"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    problems: list[str] = []
    skipped = 0

    for src, dst in SOURCES:
        rel = dst.relative_to(ROOT).as_posix()
        if not src.exists():
            print(f"skip {rel} (source not present: {src})")
            skipped += 1
            continue
        if args.check:
            if not dst.exists():
                problems.append(f"{rel} is missing")
            elif dst.read_bytes() != src.read_bytes():
                problems.append(f"{rel} differs from {src}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"synced {rel}")

    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        return 1
    if args.check:
        print(f"check ok ({skipped} skipped)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
