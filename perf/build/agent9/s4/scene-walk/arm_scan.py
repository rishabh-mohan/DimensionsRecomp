# arm_scan.py -- Agent 9 (S4.2.5 scan, 07:35). Read-only, 1 thread, A tree.
# Finds word stores whose EA resolves to a target through simple per-function constant tracking
# (lis / addi / addis / ori / mr), which fq.py's constant-EA index may miss (e.g. lis + addi base + stw d(rA)).
import os, re, sys

root = sys.argv[1]
targets = [int(t, 16) for t in sys.argv[2].split(",")]
re_func = re.compile(r"^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
re_asm = re.compile(r"^\t// ([a-z.]+) ?(.*)$")
re_mem = re.compile(r"^(r\d+),(-?\d+)\((r\d+)\)$")

def ival(s):
    return int(s, 16) if s.lower().startswith(("0x", "-0x")) else int(s)

hits = []
for fn in sorted(os.listdir(root)):
    if not fn.endswith(".cpp"):
        continue
    with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as f:
        data = f.read()
    if "lis r" not in data:
        continue
    func = None
    val = {}
    for ln, line in enumerate(data.split("\n"), 1):
        m = re_func.match(line)
        if m:
            func = m.group(1)
            val = {}
            continue
        m = re_asm.match(line)
        if not m:
            continue
        op, args = m.group(1), m.group(2).strip()
        a = [x.strip() for x in args.split(",")] if args else []
        try:
            if op == "lis" and len(a) == 2:
                val[a[0]] = (ival(a[1]) << 16) & 0xFFFFFFFF
                continue
            if op in ("addi", "addis") and len(a) == 3 and a[1] in val:
                k = ival(a[2]) << (16 if op == "addis" else 0)
                val[a[0]] = (val[a[1]] + k) & 0xFFFFFFFF
                continue
            if op == "ori" and len(a) == 3 and a[1] in val:
                val[a[0]] = val[a[1]] | ival(a[2])
                continue
            if op == "mr" and len(a) == 2:
                if a[1] in val:
                    val[a[0]] = val[a[1]]
                else:
                    val.pop(a[0], None)
                continue
        except ValueError:
            pass
        if op in ("stw", "stwu", "sth", "sthu", "stb", "stbu") and len(a) == 2:
            mm = re_mem.match(args.replace(" ", ""))
            if mm and mm.group(3) in val:
                ea = (val[mm.group(3)] + int(mm.group(2))) & 0xFFFFFFFF
                if ea in targets:
                    hits.append((fn, ln, func, op, args, ea))
            if op.endswith("u") and mm:
                val.pop(mm.group(3), None)
            continue
        if op.startswith(("st", "cmp", "b", "tw", "dcb", "mt", "sync", "isync", "lwsync", "eieio")) or op.startswith("c"):
            continue
        if a:
            val.pop(a[0], None)  # most other ops write their first operand

print("stores resolved to %s: %d" % (",".join("0x%08X" % t for t in targets), len(hits)))
for fn, ln, func, op, args, ea in hits:
    print("  %s TU%s:%d  %s %s  -> 0x%08X" % (func, fn.split(".")[1], ln, op, args, ea))
