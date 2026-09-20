#!/usr/bin/env python3
"""Verify every released data file against data/checksums.sha256.

Usage
-----
    python scripts/verify_checksums.py            # verify
    python scripts/verify_checksums.py --write    # (re)generate the manifest
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "checksums.sha256"
SKIP = {"checksums.sha256", "README.md"}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def released_files() -> list[Path]:
    return sorted(
        p for p in DATA.rglob("*")
        if p.is_file() and p.name not in SKIP
    )


def write_manifest() -> int:
    lines = [f"{sha256(p)}  {p.relative_to(DATA).as_posix()}" for p in released_files()]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} checksums to {MANIFEST.relative_to(ROOT)}")
    return 0


def verify() -> int:
    if not MANIFEST.exists():
        print(f"missing manifest: {MANIFEST}", file=sys.stderr)
        print("run with --write to generate it", file=sys.stderr)
        return 2

    expected = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, _, name = line.partition("  ")
            expected[name] = digest

    actual = {p.relative_to(DATA).as_posix(): p for p in released_files()}

    ok = missing = changed = extra = 0
    for name, digest in sorted(expected.items()):
        path = actual.pop(name, None)
        if path is None:
            print(f"MISSING   {name}")
            missing += 1
        elif sha256(path) != digest:
            print(f"CHANGED   {name}")
            changed += 1
        else:
            ok += 1
    for name in sorted(actual):
        print(f"UNTRACKED {name}")
        extra += 1

    print(f"\n{ok} ok, {missing} missing, {changed} changed, {extra} untracked")
    if missing or changed:
        print("\nDownstream numbers will not reproduce. Re-download the release.")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the manifest")
    args = parser.parse_args()
    raise SystemExit(write_manifest() if args.write else verify())
