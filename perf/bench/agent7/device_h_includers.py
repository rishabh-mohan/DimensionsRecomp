"""List the translation units in build/dev/compile_commands.json that include gpu_native/device.h,
directly or through other headers under rexlego/src (regex include graph, quoted and angle includes
resolved against the including file's directory and rexlego/src).

Usage: python bench\\agent7\\device_h_includers.py [--db build\\dev\\compile_commands.json] [--header gpu_native/device.h]
Prints the headers that pull in the target, then one TU per line (repo-relative), then the count.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "DimensionsRecomp", "rexlego", "src")
INC = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.M)


def norm(p):
    return os.path.normcase(os.path.abspath(p))


def includes_of(path, cache):
    key = norm(path)
    if key in cache:
        return cache[key]
    out = []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        cache[key] = out
        return out
    base = os.path.dirname(path)
    for name in INC.findall(text):
        for cand in (os.path.join(base, name), os.path.join(SRC, name)):
            if os.path.isfile(cand):
                out.append(norm(cand))
                break
    cache[key] = out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "build", "dev", "compile_commands.json"))
    ap.add_argument("--header", default="gpu_native/device.h")
    a = ap.parse_args()
    target = norm(os.path.join(SRC, a.header))
    entries = json.load(open(a.db, encoding="utf-8"))
    tus = []
    for e in entries:
        f = e["file"]
        if not os.path.isabs(f):
            f = os.path.join(e.get("directory", ""), f)
        tus.append(norm(f))
    tus = sorted(set(tus))
    cache = {}
    memo = {}

    def reaches(path, stack):
        if path == target:
            return True
        if path in memo:
            return memo[path]
        if path in stack:
            return False
        stack.add(path)
        r = any(reaches(c, stack) for c in includes_of(path, cache))
        stack.discard(path)
        memo[path] = r
        return r

    hits = [t for t in tus if t != target and reaches(t, set())]
    headers = sorted(p for p, r in memo.items() if r and p.endswith((".h", ".hpp", ".inl")) and p != target)
    print("headers that include %s (directly or not): %d" % (a.header, len(headers)))
    for h in headers:
        print("  " + os.path.relpath(h, ROOT))
    print("TUs in %s: %d of %d" % (os.path.relpath(a.db, ROOT), len(hits), len(tus)))
    for t in hits:
        print(os.path.relpath(t, ROOT))
    print("count=%d" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
