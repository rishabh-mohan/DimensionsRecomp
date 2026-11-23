#!/usr/bin/env python3
"""bin_manifest_check.py - check a staged bin dir against its MANIFEST.txt (Agent 7, task #22).

  python bench/agent7/bin_manifest_check.py build/agent2/native3d-bin [--manifest PATH] [--no-hash] [-o OUT]

MANIFEST.txt data lines (Agent 2's format): name<TAB>size<TAB>mtime<TAB>sha256<TAB>source.
Lines starting with '#' are comments. PASS means two things:
- every listed file exists with the same size and sha256;
- the dir holds nothing else, apart from MANIFEST.txt itself. Every extra file or subdirectory is
  reported with its size and mtime.
MANIFEST.txt's own sha256 and mtime are printed, so two checks can be compared.
Read-only, single thread, stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import os
import sys


def sha256(path: str, bufsize: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(bufsize)
            if not block:
                break
            h.update(block)
    return h.hexdigest().upper()


def parse_manifest(path: str) -> dict[str, tuple[int, str, str]]:
    entries: dict[str, tuple[int, str, str]] = {}
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            try:
                size = int(parts[1])
            except ValueError:
                continue
            entries[os.path.normpath(parts[0])] = (size, parts[2], parts[3].strip().upper())
    return entries


def mtime_str(path: str) -> str:
    return _dt.datetime.fromtimestamp(os.stat(path).st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def check(bin_dir: str, manifest: str, do_hash: bool = True) -> tuple[list[str], int]:
    out: list[str] = []
    problems = 0
    if not os.path.isfile(manifest):
        return [f"FAIL no manifest: {manifest}"], 1
    entries = parse_manifest(manifest)
    out.append(f"bin_manifest_check: {bin_dir} vs {manifest} ({len(entries)} listed files, "
               f"hash {'on' if do_hash else 'off'})")
    out.append(f"  MANIFEST sha256 {sha256(manifest)[:16]} mtime {mtime_str(manifest)}")
    if not entries:
        out.append("FAIL manifest lists no files")
        problems += 1
    for name, (size, mtime, digest) in sorted(entries.items()):
        path = os.path.join(bin_dir, name)
        if not os.path.isfile(path):
            out.append(f"FAIL missing  {name}")
            problems += 1
            continue
        actual_size = os.stat(path).st_size
        if actual_size != size:
            out.append(f"FAIL size     {name}: {actual_size} != listed {size}")
            problems += 1
            continue
        if do_hash:
            actual = sha256(path)
            if actual != digest:
                out.append(f"FAIL sha256   {name}: {actual[:16]} != listed {digest[:16]}")
                problems += 1
                continue
        out.append(f"ok            {name} {size} {digest[:16]} (mtime {mtime_str(path)}, listed {mtime})")
    listed = {os.path.normcase(n) for n in entries}
    listed.add(os.path.normcase("MANIFEST.txt"))
    listed_dirs: set[str] = set()
    for n in listed:
        parent = os.path.dirname(n)
        while parent:
            listed_dirs.add(parent)
            parent = os.path.dirname(parent)
    newest = (0.0, "")
    for root, dirs, files in os.walk(bin_dir):
        for d in sorted(dirs):
            rel = os.path.normcase(os.path.relpath(os.path.join(root, d), bin_dir))
            if rel not in listed_dirs:
                out.append(f"FAIL extra dir  {rel} (mtime {mtime_str(os.path.join(root, d))})")
                problems += 1
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.normcase(os.path.relpath(full, bin_dir))
            st = os.stat(full)
            if st.st_mtime > newest[0]:
                newest = (st.st_mtime, rel)
            if rel not in listed:
                out.append(f"FAIL extra file {rel} {st.st_size} (mtime {mtime_str(full)})")
                problems += 1
    if newest[1]:
        out.append(f"  newest file: {newest[1]} "
                   f"({_dt.datetime.fromtimestamp(newest[0]).strftime('%Y-%m-%d %H:%M:%S')})")
    out.append(f"RESULT: {'PASS' if problems == 0 else 'FAIL'} ({problems} problem(s))")
    return out, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bin_dir")
    ap.add_argument("--manifest", default=None, help="default: <bin_dir>/MANIFEST.txt")
    ap.add_argument("--no-hash", action="store_true", help="sizes only (fast)")
    ap.add_argument("-o", "--out", default=None, help="also write the report here")
    args = ap.parse_args(argv)
    manifest = args.manifest or os.path.join(args.bin_dir, "MANIFEST.txt")
    lines, problems = check(args.bin_dir, manifest, not args.no_hash)
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
