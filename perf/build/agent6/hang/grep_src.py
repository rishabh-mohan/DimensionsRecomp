"""grep_src.py -- read-only regex search over a source tree (task #16 follow-up, 22:36).

Usage: python -B build/agent6/hang/grep_src.py <root> <regex> [context_lines]
Searches .cpp/.cc/.c/.h/.hpp/.inl files under <root>; prints path:line: text (hits marked '>').
"""
import os
import re
import sys

EXTS = (".cpp", ".cc", ".c", ".h", ".hpp", ".inl")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root, rx = argv[0], re.compile(argv[1])
    ctx = int(argv[2]) if len(argv) > 2 else 0
    nfiles = nhits = 0
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            if not f.endswith(EXTS):
                continue
            p = os.path.join(dp, f)
            nfiles += 1
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    lines = fh.read().splitlines()
            except OSError:
                continue
            hits = [i for i, l in enumerate(lines) if rx.search(l)]
            if not hits:
                continue
            nhits += len(hits)
            hs = set(hits)
            shown = set()
            for i in hits:
                for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                    if j in shown:
                        continue
                    shown.add(j)
                    mark = ">" if j in hs else " "
                    print(f"{os.path.relpath(p, root)}:{j + 1}:{mark} {lines[j].rstrip()[:220]}")
    print(f"-- {nhits} hits in {nfiles} files under {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
