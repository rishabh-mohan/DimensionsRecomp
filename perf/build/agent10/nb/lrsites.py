"""lrsites.py (Agent 10, task #17 item 1a): LR-gated call sites and mid-asm hook call sites in two generated
LEGO trees. Read-only; one thread; writes only the --out report.

  python lrsites.py <treeA> <treeB> [--out report.txt] [--context N]

A = the codegen tree native3d is built from (the pinned S1 output), B = the one nativeB is built from
(install/batch-nolr). A tree is an install root (generated/default/...), a generated dir (default/...) or the
default dir itself.

Per tree it collects:
  * every `ctx.lr = 0x<C>;` store whose constant is a return address host code tests or logs:
      0x83F9B660  sub_83FC49E8 hook: pool-copy drain + "placement buffer relocation" (hooks_buffer.cpp:273, :400)
      0x839D11B0  sub_839C4D08 hook: extra pause-menu Options rows (settings_native_hooks.cpp:174)
      0x82A33FC4  slot-heap Grow thunk (native_slot_growth.cpp:63), an indirect call (bctrl)
      0x82A3B88C  slot-heap Release thunk (native_slot_growth.cpp:76), an indirect call (bctrl)
      0x82BD2B44  pool-copy hook: caller read from r1+152 when lr is this (hooks_buffer.cpp:309)
      0x82B5819C  the pool-copy caller logged in every native run ("caller=82B5819C")
    with the enclosing DEFINE_REX_FUNC, the call that follows (first statement with "(ctx, base)",
    REX_CALL_INDIRECT or PPC_CALL_INDIRECT, at most 12 lines) and the gap = number of statements between the
    store and the call (comments and blank lines skipped; must be 0, so the callee sees ctx.lr == C);
  * every line that names a mid-asm hook (NativeCelShading*, MissingAdventureTimeLookupNode,
    RepairDialogueLockReleaseOperand), split into calls (with the enclosing function) and extern declarations.

Call lines are compared after dropping the `ctx.` prefix of register names (B keeps ctr/cr/r locals:
`REX_CALL_INDIRECT_FUNC(ctx.ctr.u32)` in A is `REX_CALL_INDIRECT_FUNC(ctr.u32)` in B).
PASS when every constant is present, both trees have the same LR records (constant, function, normalized call,
gap), every gap is 0, and the hook-call records (hook, function, normalized call) match. TU file names are
ignored (B re-partitions the TUs). Exit 0 PASS, 1 differs.
"""
import argparse
import collections
import os
import re
import sys
import time

CONSTS = {
    '83F9B660': 'sub_83FC49E8 drain + placement relocation line',
    '839D11B0': 'sub_839C4D08 pause-menu rows',
    '82A33FC4': 'slot-heap Grow (indirect)',
    '82A3B88C': 'slot-heap Release (indirect)',
    '82BD2B44': 'pool-copy caller test',
    '82B5819C': 'pool-copy caller (logged)',
}
LR_RE = re.compile(rb'^\tctx\.lr = 0x(' + b'|'.join(c.encode() for c in CONSTS) + rb');[ \t]*$', re.M | re.I)
HOOK_RE = re.compile(rb'^.*\b(NativeCelShading\w+|MissingAdventureTimeLookupNode|RepairDialogueLockReleaseOperand)\b.*$',
                     re.M)
FUNC_RE = re.compile(rb'DEFINE_REX_FUNC\(([^)]+)\)')
TU = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp$')
CALL_KEYS = ('(ctx, base)', 'REX_CALL_INDIRECT', 'PPC_CALL_INDIRECT')
NORM = re.compile(r'\bctx\.(?=(?:r\d+|f\d+|v\d+|cr\d|ctr|xer)\b)')


def gendir(t):
    for sub in ('generated/default', 'default', ''):
        p = os.path.normpath(os.path.join(t, sub))
        if os.path.exists(os.path.join(p, 'legodimensions_init.cpp')):
            return p
    raise SystemExit('no codegen output under ' + t)


def enclosing(data, pos):
    i = data.rfind(b'DEFINE_REX_FUNC(', 0, pos)
    if i < 0:
        return '<none>'
    m = FUNC_RE.match(data, i)
    return m.group(1).decode('latin-1') if m else '<?>'


def is_decl(line):
    return line.startswith('extern') or line.startswith('void ') or (line.endswith(');') and 'PPCRegister' in line)


def scan(tree, ctx_lines):
    d = gendir(tree)
    tus = sorted((int(TU.match(f).group(1)), f) for f in os.listdir(d) if TU.match(f))
    lr, calls, decls, ctx = [], [], collections.Counter(), {}
    nbytes = 0
    for _, f in tus:
        with open(os.path.join(d, f), 'rb') as fh:
            data = fh.read().replace(b'\r\n', b'\n')
        nbytes += len(data)
        for m in LR_RE.finditer(data):
            const = m.group(1).decode().upper()
            func = enclosing(data, m.start())
            tail = data[m.end() + 1:m.end() + 1 + 4000].split(b'\n')
            seq, call, gap, used = [], '<no call within 12 lines>', None, 0
            for line in tail[:12]:
                used += 1
                s = line.decode('latin-1').strip()
                if not s or s.startswith('//'):
                    continue
                seq.append(s)
                if any(k in s for k in CALL_KEYS):
                    call, gap = s, len(seq) - 1
                    break
            lr.append((const, func, NORM.sub('', call), gap, call, f))
            key = (const, func)
            if key not in ctx:
                head = data[:m.start()].rsplit(b'\n', ctx_lines + 1)[1:]
                ctx[key] = ([h.decode('latin-1').rstrip() for h in head]
                            + [m.group(0).decode('latin-1').rstrip()]
                            + [t.decode('latin-1').rstrip() for t in tail[:used + 2]])
        for m in HOOK_RE.finditer(data):
            line = m.group(0).decode('latin-1').strip()
            name = m.group(1).decode()
            if is_decl(line):
                decls[name] += 1
            else:
                calls.append((name, enclosing(data, m.start()), NORM.sub('', line), line, f))
    return {'dir': d, 'tus': len(tus), 'bytes': nbytes, 'lr': lr, 'calls': calls, 'decls': decls, 'ctx': ctx}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--out')
    ap.add_argument('--context', type=int, default=3)
    o = ap.parse_args()
    t0 = time.time()
    A, B = scan(o.a, o.context), scan(o.b, o.context)
    W = []
    w = W.append
    for tag, S in (('A', A), ('B', B)):
        w(f"{tag} {S['dir']}: {S['tus']} TUs, {S['bytes']:,} B; LR stores {len(S['lr'])}, hook calls "
          f"{len(S['calls'])}, hook declarations {sum(S['decls'].values())}")
    ok = True
    w('')
    w('LR-gated sites (constant: purpose -> A records / B records; gap = statements between store and call):')
    for c, why in CONSTS.items():
        ra = sorted((x[1], x[2], x[3]) for x in A['lr'] if x[0] == c)
        rb = sorted((x[1], x[2], x[3]) for x in B['lr'] if x[0] == c)
        same = ra == rb
        gaps0 = all(g == 0 for _, _, g in ra + rb)
        ok &= same and bool(ra) and gaps0
        w(f"  0x{c} ({why}): A {len(ra)}, B {len(rb)} -> {'SAME' if same else 'DIFFERENT'}"
          f"{'' if ra else '  (ABSENT in A)'}{'' if gaps0 else '  (CALL NOT IMMEDIATE)'}")
        for tag, S in (('A', A), ('B', B)):
            for x in sorted(x for x in S['lr'] if x[0] == c):
                w(f'      {tag} {x[1]}: gap {x[3]}: {x[4]}   [{x[5]}]')
    w('')
    w('Mid-asm hook calls (hook: A / B):')
    names = sorted({x[0] for x in A['calls']} | {x[0] for x in B['calls']})
    for n in names:
        ra = sorted((x[1], x[2]) for x in A['calls'] if x[0] == n)
        rb = sorted((x[1], x[2]) for x in B['calls'] if x[0] == n)
        same = ra == rb
        ok &= same
        w(f"  {n}: A {len(ra)}, B {len(rb)} -> {'SAME' if same else 'DIFFERENT'}")
        for tag, S in (('A', A), ('B', B)):
            for x in sorted(x for x in S['calls'] if x[0] == n):
                w(f'      {tag} {x[1]}: {x[3]}   [{x[4]}]')
    ok &= bool(names)
    w('  declarations: A ' + ', '.join(f'{k} {v}' for k, v in sorted(A['decls'].items()))
      + ' | B ' + ', '.join(f'{k} {v}' for k, v in sorted(B['decls'].items())))
    w('')
    w('Context, first site per (constant, function), A then B:')
    for key in sorted(set(A['ctx']) | set(B['ctx'])):
        for tag, S in (('A', A), ('B', B)):
            lines = S['ctx'].get(key)
            w(f'  [{tag}] 0x{key[0]} in {key[1]}:' + ('' if lines else ' <absent>'))
            for l in lines or []:
                w('      ' + l[:180])
    w('')
    w(f"RESULT {'PASS' if ok else 'DIFFERENT'} ({time.time() - t0:.1f}s)")
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
