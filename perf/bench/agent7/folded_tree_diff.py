#!/usr/bin/env python3
"""folded_tree_diff.py - diff two folded-stack files (analyze_profile.py --folded) as a call tree.

Agent 7, task #13. Profile data only (never timing). Single process, stdlib only.

  python bench/agent7/folded_tree_diff.py A.folded WA B.folded WB [--root REGEX]
         [--depth N] [--min N] [--guest-only] [--leaves] [--labels a,b]

WA/WB = ms/frame per sample (prof_main_compare.py prints it as "-> w ...").
Rows are prefixes of the call path below the first frame that matches --root
(default: the outermost frame).  '~' marks |delta| < 2se (Poisson).
--guest-only drops host frames *between* guest frames (trampolines) and keeps
the first host frame below the deepest guest frame as the leaf ("boundary").
--leaves adds a table of leaves (guest self, or the guest->host boundary).
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter

GUEST_RE = re.compile(r"^(sub_[0-9A-Fa-f]{8}) \[(?:guest|hook of guest) 0x[0-9A-Fa-f]{8}\]$")
HOOK_RE = re.compile(r"^(sub_[0-9A-Fa-f]{8}) \[hook of guest 0x[0-9A-Fa-f]{8}\]$")
SAVEREST_RE = re.compile(r"^__(save|rest)(gpr|fpr|vmx)(lr)?_\d+$")


def is_guest(frame: str) -> bool:
    return bool(GUEST_RE.match(frame)) or frame == "xstart" or bool(SAVEREST_RE.match(frame))


def short(frame: str, width: int = 70) -> str:
    m = HOOK_RE.match(frame)
    if m:
        return "hook:" + m.group(1)
    m = GUEST_RE.match(frame)
    if m:
        return m.group(1)
    frame = re.sub(r"\(near [^)]*\)", "", frame).strip()
    return frame if len(frame) <= width else frame[: width - 3] + "..."


def parse(path: str) -> list[tuple[list[str], int]]:
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            i = line.rfind(" ")
            try:
                n = int(line[i + 1 :])
            except ValueError:
                continue
            out.append((line[:i].split(";"), n))
    return out


def reroot(stacks, root_re, guest_only):
    """Yield (path, count) below the root; path[0] is the root frame. None = root absent."""
    for frames, n in stacks:
        start = 0
        if root_re is not None:
            start = next((k for k, f in enumerate(frames) if root_re.search(f)), None)
            if start is None:
                yield None, n
                continue
        path = frames[start:]
        if guest_only:
            last_g = max((k for k, f in enumerate(path) if is_guest(f)), default=-1)
            kept = [f for f in path[: last_g + 1] if is_guest(f)]
            if last_g + 1 < len(path):
                kept.append(path[last_g + 1])  # boundary host frame
            path = kept or path[:1]
        yield [short(f) for f in path], n


def leaf_key(path):
    leaf = path[-1]
    if leaf.startswith("sub_") or leaf == "xstart" or SAVEREST_RE.match(leaf):
        return leaf + "  (guest self)"
    g = [f for f in path if f.startswith("sub_") or f.startswith("hook:")]
    return f"{leaf}  <- {g[-1] if g else '?'}"


def fmt_row(na, nb, wa, wb):
    a, b = na * wa, nb * wb
    d = b - a
    se2 = 2.0 * math.sqrt(na * wa * wa + nb * wb * wb)
    tilde = "~" if abs(d) < se2 else " "
    return f"{a:7.3f} {b:7.3f} {d:+8.3f}{tilde} {se2:6.3f} {na:4d} {nb:4d}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("wa", type=float)
    ap.add_argument("b")
    ap.add_argument("wb", type=float)
    ap.add_argument("--root", default=None, help="regex for the root frame (first match from the outside)")
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--min", type=int, default=2, help="min samples (A or B) for a row")
    ap.add_argument("--guest-only", action="store_true")
    ap.add_argument("--leaves", action="store_true")
    ap.add_argument("--labels", default="A,B")
    args = ap.parse_args(argv)
    la, lb = (args.labels.split(",") + ["B"])[:2]
    root_re = re.compile(args.root) if args.root else None

    sides = []
    for path_file in (args.a, args.b):
        stacks = parse(path_file)
        total = sum(n for _, n in stacks)
        tree, leaves, outside = Counter(), Counter(), 0
        for path, n in reroot(stacks, root_re, args.guest_only):
            if path is None:
                outside += n
                continue
            for d in range(1, min(len(path), args.depth) + 1):
                tree[tuple(path[:d])] += n
            leaves[leaf_key(path)] += n
        sides.append((total, outside, tree, leaves))

    (ta, oa, tree_a, leaves_a), (tb, ob, tree_b, leaves_b) = sides
    print(f"folded_tree_diff: A={la} ({args.a}) B={lb} ({args.b})")
    print(f"  w ms/frame/sample: A {args.wa:.6f}, B {args.wb:.6f}; root {args.root or '(outermost)'}; "
          f"depth {args.depth}; guest_only {args.guest_only}")
    print(f"  samples: A total {ta} (outside root {oa}), B total {tb} (outside root {ob})")
    print(f"  total ms/f: A {ta * args.wa:.3f}, B {tb * args.wb:.3f}; under root: "
          f"A {(ta - oa) * args.wa:.3f}, B {(tb - ob) * args.wb:.3f}")
    print()
    print(f"{la + ' ms/f':>7} {lb + ' ms/f':>7} {'delta':>9} {'2se':>6} {'nA':>4} {'nB':>4}  path (indent = depth)")

    # DFS over the union tree, children by B+A count descending
    keys = set(tree_a) | set(tree_b)
    children: dict[tuple, list[tuple]] = {}
    for k in keys:
        children.setdefault(k[:-1], []).append(k)

    def visit(prefix):
        kids = sorted(children.get(prefix, []), key=lambda k: -(tree_a[k] + tree_b[k]))
        for k in kids:
            na, nb = tree_a[k], tree_b[k]
            if max(na, nb) < args.min:
                continue
            print(f"{fmt_row(na, nb, args.wa, args.wb)}  {'  ' * (len(k) - 1)}{k[-1]}")
            visit(k)

    visit(())

    if args.leaves:
        print()
        print("== leaves under root (guest self, or host boundary <- deepest guest), by |delta| ==")
        print(f"{la + ' ms/f':>7} {lb + ' ms/f':>7} {'delta':>9} {'2se':>6} {'nA':>4} {'nB':>4}  leaf")
        lk = set(leaves_a) | set(leaves_b)
        rows = sorted(lk, key=lambda k: -abs(leaves_b[k] * args.wb - leaves_a[k] * args.wa))
        for k in rows:
            na, nb = leaves_a[k], leaves_b[k]
            if max(na, nb) < max(1, args.min - 1):
                continue
            print(f"{fmt_row(na, nb, args.wa, args.wb)}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
