"""Compare two COFF objects section by section (sizes) and name the symbols in the sections that differ.

Usage: python objdiff.py A.obj B.obj [--top N]
Needs llvm-objdump on PATH (dot-source env/devshell.ps1 first).
"""
import argparse
import re
import subprocess
import sys
from collections import defaultdict

SEC_RE = re.compile(r"^\s*(\d+)\s+(\S+)\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s*(.*)$")
SYM_RE = re.compile(r"^\[\s*\d+\]\(sec\s+(-?\d+)\)\(fl [^)]*\)\(ty\s+([0-9a-fA-F]+)\)\(scl\s+(\d+)\)\s*\(nx\s+\d+\)\s+0x[0-9a-fA-F]+\s+(.*)$")


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, errors="replace").stdout


def sections(path):
    out = []
    for line in run(["llvm-objdump", "-h", path]).splitlines():
        m = SEC_RE.match(line)
        if m:
            out.append((int(m.group(1)), m.group(2), int(m.group(3), 16)))
    return out


SYM_VAL_RE = re.compile(r"^\[\s*\d+\]\(sec\s+(-?\d+)\)\(fl [^)]*\)\(ty\s+([0-9a-fA-F]+)\)\(scl\s+(\d+)\)\s*\(nx\s+\d+\)\s+0x([0-9a-fA-F]+)\s+(.*)$")


def symbols(path):
    by_sec = defaultdict(list)
    for line in run(["llvm-objdump", "-t", "-C", path]).splitlines():
        m = SYM_RE.match(line.strip())
        if not m:
            continue
        sec = int(m.group(1))
        scl = int(m.group(3))
        name = m.group(4).strip()
        if sec <= 0 or scl == 3 and name.startswith("."):
            continue
        by_sec[sec].append(name)
    return by_sec


def function_sizes(path, sec, sec_size):
    """Sizes of the function symbols in one section, from the gaps between their offsets."""
    syms = []
    for line in run(["llvm-objdump", "-t", "-C", path]).splitlines():
        m = SYM_VAL_RE.match(line.strip())
        if not m or int(m.group(1)) != sec:
            continue
        ty = int(m.group(2), 16)
        # The anonymous-namespace tag (?A0x########, demangled as ::0x########::) hashes the source path,
        # so a copy in another directory gets a different tag; drop it so the same function pairs up.
        name = re.sub(r"0x[0-9A-Fa-f]{8}", "0x*", m.group(5).strip())
        if ty != 0x20 or name.startswith("."):
            continue
        syms.append((int(m.group(4), 16), name))
    syms.sort()
    sizes = {}
    for i, (off, name) in enumerate(syms):
        end = syms[i + 1][0] if i + 1 < len(syms) else sec_size
        sizes[name] = sizes.get(name, 0) + (end - off)
    return sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--top", type=int, default=40)
    ns = ap.parse_args()
    sa, sb = sections(ns.a), sections(ns.b)
    syma, symb = symbols(ns.a), symbols(ns.b)
    print(f"A {ns.a}: {len(sa)} sections, {sum(s[2] for s in sa)} B in sections")
    print(f"B {ns.b}: {len(sb)} sections, {sum(s[2] for s in sb)} B in sections")
    if len(sa) != len(sb) or any(x[1] != y[1] for x, y in zip(sa, sb)):
        print("section lists differ in count or names; pairing by index anyway", file=sys.stderr)
    by_kind = defaultdict(int)
    diffs = []
    for x, y in zip(sa, sb):
        if x[2] != y[2]:
            delta = y[2] - x[2]
            by_kind[x[1]] += delta
            names = symb.get(y[0] + 1) or syma.get(x[0] + 1) or []
            diffs.append((delta, x[0], x[1], x[2], y[2], names))
    print(f"{len(diffs)} sections differ in size; net {sum(d[0] for d in diffs):+d} B")
    print("net delta by section name:")
    for kind, delta in sorted(by_kind.items(), key=lambda kv: kv[1]):
        print(f"  {kind:<16} {delta:+d}")
    print(f"largest {ns.top} by |delta|:")
    for delta, idx, name, sza, szb, names in sorted(diffs, key=lambda d: -abs(d[0]))[: ns.top]:
        label = "; ".join(n[:110] for n in names[:2]) if names else "-"
        print(f"  [{idx}] {name:<10} {sza:>8} -> {szb:>8} ({delta:+d})  {label}")
    for delta, idx, name, sza, szb, names in diffs:
        if name != ".text":
            continue
        fa = function_sizes(ns.a, idx + 1, sza)
        fb = function_sizes(ns.b, idx + 1, szb)
        changed = [(fb.get(k, 0) - fa.get(k, 0), k, fa.get(k), fb.get(k)) for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]
        print(f"functions in .text [{idx}]: A {len(fa)}, B {len(fb)}; {len(changed)} changed size, net {sum(c[0] for c in changed):+d} B")
        for d, k, a_sz, b_sz in sorted(changed, key=lambda c: -abs(c[0]))[: ns.top]:
            print(f"  {d:+6d}  {a_sz} -> {b_sz}  {k[:150]}")


if __name__ == "__main__":
    main()
