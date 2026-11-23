"""S3.4 (task #12 (c)): by-name comparison of two COFF objects (control vs patched shaders.cpp.obj).

objdiff.py pairs sections by index, which shifts as soon as the patch adds comdat sections. This script
pairs functions by (normalized) name instead and compares their normalized disassembly:
  - names: anonymous-namespace tag (0x########) -> 0x*, <lambda_N> -> <lambda_#>, dtor$N/catch$N/fin$N -> $#
  - code: absolute branch/call targets dropped (the <symbol+off> part kept), rip-comment addresses dropped,
    nop and trailing int3 padding dropped
and also compares the string literals in the .rdata sections (log/probe format strings, env var names).

Usage: python objcheck.py A.obj B.obj
Needs llvm-objdump on PATH (dot-source env/devshell.ps1 first).
"""
import argparse
import difflib
import re
import struct
import subprocess
from collections import Counter, defaultdict

HDR_RE = re.compile(r"^([0-9a-fA-F]+) <(.*)>:\s*$")
INS_RE = re.compile(r"^\s*[0-9a-fA-F]+:\s*(.*)$")
ABS_RE = re.compile(r"\b0x[0-9a-fA-F]+ <")
RIP_RE = re.compile(r"#\s*0x[0-9a-fA-F]+")


def norm_name(name):
    name = re.sub(r"0x[0-9A-Fa-f]{8}", "0x*", name)
    name = re.sub(r"<lambda_\d+>", "<lambda_#>", name)
    name = re.sub(r"(dtor|catch|fin)\$\d+", r"\1$#", name)
    name = re.sub(r"\$ehgcr_\d+_\d+", "$ehgcr_#", name)
    return name


def norm_ins(text):
    return norm_name(RIP_RE.sub("#", ABS_RE.sub("<", text)).strip())


def disasm(path):
    out = subprocess.run(["llvm-objdump", "-d", "-C", "--no-show-raw-insn", path],
                         check=True, capture_output=True, text=True, errors="replace").stdout
    funcs = defaultdict(list)
    state = {"cur": None, "body": []}

    def flush():
        if state["cur"] is not None:
            body = state["body"]
            while body and body[-1].startswith("int3"):
                body.pop()
            funcs[state["cur"]].append(tuple(body))
        state["cur"], state["body"] = None, []

    for line in out.splitlines():
        m = HDR_RE.match(line)
        if m:
            name = norm_name(m.group(2))
            # $ehgcr_* are EH continuation labels inside a function, not functions: keep the body going.
            if name.startswith("$ehgcr") and state["cur"] is not None:
                state["body"].append("<" + name + ">")
                continue
            flush()
            state["cur"] = name
            continue
        if line.startswith("Disassembly of section"):
            flush()
            continue
        if state["cur"] is None:
            continue
        m = INS_RE.match(line)
        if m and m.group(1):
            ins = norm_ins(m.group(1))
            if not ins.startswith("nop"):
                state["body"].append(ins)
    flush()
    return funcs


def rdata_strings(path):
    data = open(path, "rb").read()
    sig1, sig2 = struct.unpack_from("<HH", data, 0)
    if sig1 == 0 and sig2 == 0xFFFF:  # /bigobj header
        nsec = struct.unpack_from("<I", data, 44)[0]
        off = 56
    else:
        nsec = struct.unpack_from("<H", data, 2)[0]
        off = 20 + struct.unpack_from("<H", data, 16)[0]
    strings = Counter()
    for i in range(nsec):
        name, _vsize, _vaddr, rawsize, rawptr = struct.unpack_from("<8sIIII", data, off + 40 * i)
        if not name.rstrip(b"\0").startswith(b".rdata") or not rawptr:
            continue
        for s in re.findall(rb"[\x20-\x7e]{6,}(?=\x00)", data[rawptr:rawptr + rawsize]):
            strings[s.decode("ascii")] += 1
    return strings


LINE_IMM_RE = re.compile(r"^movl\t\$0x([0-9a-fA-F]+), (.*?)\s*# imm = 0x[0-9a-fA-F]+$")


def line_map(before, after):
    """1-based line numbers of before -> after, through the unchanged blocks of a line diff."""
    a = open(before, encoding="utf-8", errors="replace").read().splitlines()
    b = open(after, encoding="utf-8", errors="replace").read().splitlines()
    out = {}
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            out[blk.a + k + 1] = blk.b + k + 1
    return out


def only_line_constants(x, y, lmap):
    """True if x and y differ only in `movl $LINE, slot` stores (spdlog source_loc) with LINE mapped by the patch."""
    if len(x) != len(y) or x == y:
        return False
    for p, q in zip(x, y):
        if p == q:
            continue
        mp, mq = LINE_IMM_RE.match(p), LINE_IMM_RE.match(q)
        if not (mp and mq and mp.group(2) == mq.group(2)):
            return False
        if lmap.get(int(mp.group(1), 16)) != int(mq.group(1), 16):
            return False
    return True


def bodies_match_modulo_lines(a_bodies, b_bodies, lmap):
    if len(a_bodies) != len(b_bodies):
        return False
    rest = list(b_bodies)
    for x in a_bodies:
        hit = next((i for i, y in enumerate(rest) if x == y or only_line_constants(x, y, lmap)), None)
        if hit is None:
            return False
        rest.pop(hit)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--before", help="control source, to map spdlog source_loc line constants")
    ap.add_argument("--after", help="patched source")
    ap.add_argument("--show", nargs="*", default=[], help="print a diff of the changed functions whose name contains one of these")
    ap.add_argument("--lines", type=int, default=60)
    ns = ap.parse_args()
    lmap = line_map(ns.before, ns.after) if ns.before and ns.after else {}
    fa, fb = disasm(ns.a), disasm(ns.b)
    sa, sb = rdata_strings(ns.a), rdata_strings(ns.b)
    print(f"A {ns.a}: {len(fa)} function names, {sum(len(v) for v in fa.values())} bodies, {sum(sa.values())} .rdata strings")
    print(f"B {ns.b}: {len(fb)} function names, {sum(len(v) for v in fb.values())} bodies, {sum(sb.values())} .rdata strings")

    def ins(bodies):
        return "+".join(str(len(b)) for b in bodies)

    added = sorted(set(fb) - set(fa))
    removed = sorted(set(fa) - set(fb))
    both = sorted(set(fa) & set(fb))
    changed = [k for k in both if sorted(fa[k]) != sorted(fb[k])]
    lines_only = [k for k in changed if lmap and bodies_match_modulo_lines(fa[k], fb[k], lmap)]
    code = [k for k in changed if k not in lines_only]
    print(f"\nfunctions only in B (added): {len(added)}")
    for k in added:
        print(f"  {ins(fb[k]):>8} ins  {k[:170]}")
    print(f"\nfunctions only in A (removed): {len(removed)}")
    for k in removed:
        print(f"  {ins(fa[k]):>8} ins  {k[:170]}")
    print(f"\nfunctions in both, code differs: {len(code)}")
    for k in code:
        print(f"  {ins(fa[k]):>8} -> {ins(fb[k]):<8} ins  {k[:170]}")
    print(f"\nfunctions in both, differ ONLY in spdlog source_loc line constants, each = control line mapped through the patch: {len(lines_only)}")
    for k in lines_only:
        print(f"  {ins(fa[k]):>8} ins  {k[:170]}")
    print(f"\nfunctions in both, normalized code identical: {len(both) - len(changed)}")

    for k in changed:
        if not any(s in k for s in ns.show):
            continue
        a_bodies, b_bodies = sorted(fa[k]), sorted(fb[k])
        print(f"\n--- diff of {k[:150]}")
        for i, (x, y) in enumerate(zip(a_bodies, b_bodies)):
            if x == y:
                continue
            lines = list(difflib.unified_diff(list(x), list(y), lineterm="", n=2))
            print(f"  body {i}: {len(lines)} diff lines")
            for line in lines[: ns.lines]:
                print("    " + line[:200])

    only_a = sa - sb
    only_b = sb - sa
    print(f"\n.rdata strings only in A: {sum(only_a.values())}")
    for s, n in sorted(only_a.items()):
        print(f"  x{n} {s[:200]!r}")
    print(f"\n.rdata strings only in B: {sum(only_b.values())}")
    for s, n in sorted(only_b.items()):
        print(f"  x{n} {s[:200]!r}")


if __name__ == "__main__":
    main()
