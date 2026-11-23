"""skip_lr exposure scan: functions that read their incoming LR as data.

With skip_lr, a caller stores no return address into ctx.lr, so an `mflr rX` reads a stale
ctx.lr. That is harmless when rX only goes to the stack (prologue save) and back to LR
(epilogue `mtlr`), because `blr` is `return;` either way. This scan flags every other use.

For each function (DEFINE_REX_FUNC ... next DEFINE_REX_FUNC) it walks the PPC comment lines in
text order. After each `mflr rX` it collects the reads of rX up to the next write of rX:
  - OK: rX is the stored value of a store whose base is r1 (stw/std/stwu rX,d(r1));
        rX goes back to LR (mtlr rX).
  - FLAG: any other read (rX as an argument, an address, mtctr, a compare, a move...).
Text order is not control flow, so this over-approximates (a flag needs a look by eye).
Usage: py -3 build/agent9/lrscan.py GENERATED_DIR OUT_TSV
"""
import glob
import os
import re
import sys

FN = re.compile(rb'DEFINE_REX_FUNC\((\w+)\) \{')
CMT = re.compile(rb'^\t// ([a-z][a-z0-9.+-]*)\s*(.*)$')
REG = re.compile(rb'\br([0-9]|[12][0-9]|3[01])\b')
STORE = re.compile(rb'^st[a-z]*$')
KEEP_LR = re.compile(rb'^\t\{ auto old_lr = ctx\.lr;', re.M)


def classify(mn, ops):
    """(dest regs, source regs, stored reg, base reg) of one instruction."""
    regs = [int(m.group(1)) for m in REG.finditer(ops)]
    if not regs:
        return set(), set(), None, None
    if STORE.match(mn) and not mn.startswith(b'stf') and not mn.startswith(b'stv'):
        # stw rS,d(rA) | stwx rS,rA,rB | stwu rS,d(rA)
        stored = regs[0]
        base = regs[1] if len(regs) > 1 else None
        srcs = set(regs)
        dests = {base} if (mn.endswith(b'u') or mn.endswith(b'ux')) and base is not None else set()
        return dests, srcs, stored, base
    if mn.startswith(b'stf') or mn.startswith(b'stv') or mn.startswith(b'lf') or mn.startswith(b'lv') or mn.startswith(b'dcb') or mn.startswith(b'icb'):
        return set(), set(regs), None, None  # FPR/VR forms: GPRs are address sources
    if mn in (b'mtlr', b'mtctr', b'mtxer', b'mtcr', b'mtcrf', b'mtspr', b'mtmsrd', b'mtmsr', b'mtfsf') or mn.startswith(b'cmp') or mn.startswith(b'tw') or mn.startswith(b'td') or mn.startswith(b'b'):
        return set(), set(regs), None, None
    return {regs[0]}, set(regs[1:]), None, None


def scan_function(name, text, out):
    lines = text.split(b'\n')
    flagged = []
    pending = {}  # reg -> mflr line
    for ln in lines:
        m = CMT.match(ln)
        if not m:
            continue
        mn, ops = m.group(1), m.group(2)
        mn = mn.rstrip(b'.')
        if mn == b'mflr':
            regs = [int(x.group(1)) for x in REG.finditer(ops)]
            if regs:
                pending[regs[0]] = ln.strip()
            continue
        if not pending:
            continue
        dests, srcs, stored, base = classify(mn, ops)
        for r in list(pending):
            if r in srcs:
                ok = (mn == b'mtlr') or (stored == r and base == 1 and r != base)
                if not ok:
                    flagged.append((pending[r].decode(), ln.strip().decode()))
                    del pending[r]
                    continue
            if r in dests:
                del pending[r]
    if flagged:
        keeps = bool(KEEP_LR.search(text))
        for mf, use in flagged:
            out.write(f'{name}\t{"keeps_lr" if keeps else "skip_lr"}\t{mf}\t{use}\n')
    return len(flagged)


def main():
    root, out_path = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(root, 'legodimensions_recomp.*.cpp')), key=lambda p: int(p.rsplit('.', 2)[1]))
    nfn = nflag_fn = nflag = nmflr = 0
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('function\tlr_mode\tmflr\tfirst_non_save_use\n')
        for path in files:
            data = open(path, 'rb').read()
            starts = [(m.start(), m.group(1).decode()) for m in FN.finditer(data)]
            for i, (pos, name) in enumerate(starts):
                end = starts[i + 1][0] if i + 1 < len(starts) else len(data)
                text = data[pos:end]
                nfn += 1
                nmflr += text.count(b'\t// mflr ')
                k = scan_function(name, text, out)
                if k:
                    nflag_fn += 1
                    nflag += k
    print(f'{root}: {len(files)} TUs, {nfn} functions, {nmflr} mflr, {nflag} flagged uses in {nflag_fn} functions -> {out_path}')


if __name__ == '__main__':
    main()
