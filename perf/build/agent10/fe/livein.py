#!/usr/bin/env python3
"""livein: whole-tree checks for (b) that feall can't make (Agent 10, task #17). Read-only.

feall compares A and B per guest instruction after dropping "ctx.", so it treats ctx.cr6 and the local
cr6 as the same thing. That is right only if B's locals never carry a value across a function boundary.

  livein.py B   (v2) For every snapB3 function with local declarations (PPC(CR|XER)?Register ctr/xer/
                reserved/crN{}), walk the code lines (not the "//" instruction comments) in text order and
                classify each use of each local (each CR bit, each xer field, separately):
                  writes: crN.compare / compare<T> / setFromMask / set_raw, crN = ..., crN.bit = ...,
                          ctr|reserved[.view] = ..., xer.f = ..., xer[.view] = ... (all fields)
                  reads:  everything else that names it (crN.raw(), crN.bit, ...; RHS of a self-update)
                check 1: the first use is a read  -> B reads its zero initialiser where A reads ctx.
                         'read-loop' = a backward goto from below reaches a label at/before the read.
                check 2: a read of a call-volatile local (cr0 cr1 cr5 cr6 cr7 ctr xer reserved) whose last
                         textual write comes before a non-tail call (not __save*/__rest* helpers) -> A reads
                         what the callee left in ctx, B its own pre-call value.
  livein.py A   Over snap1, every function with an XER.SO writer (o-form arithmetic, mtxer, mtspr 1), every
                XER/CR-SO reader (mfxer, mcrxr, bso/bns family), and every function whose stwcx./stdcx.
                has no lwarx/ldarx in the same function (a reservation from the caller).

Writes build/agent10/fe/livein-A.txt or livein-B2.txt (v1's livein-B.txt is kept; v1 missed the
compare(double)/setFromMask/set_raw writes).
"""
import os, re, sys, time

DEF_RE = re.compile(rb'^(?:DEFINE_REX_FUNC\((sub_[0-9A-F]{8})\)|PPC_FUNC_IMPL\(__imp__(sub_[0-9A-F]{8})\)'
                    rb'|PPC_FUNC\((sub_[0-9A-F]{8})\))', re.M)
DECL = re.compile(r'^\s*PPC(?:CR|XER)?Register (ctr|xer|reserved|cr\d)\{\};\s*$')
INSN = re.compile(r'^\s*// (\S+)')
SO_W = re.compile(r'^(?:add|addc|adde|addme|addze|subf|subfc|subfe|subfme|subfze|neg|mullw|mulld|divw|divwu|divd'
                  r'|divdu)o\.?$|^mtxer$')
SO_R = re.compile(r'^(?:mfxer|mcrxr|bso|bns|bsolr|bnslr|bsoctr|bnsctr|bsol|bnsl|bsoa|bnsa)[+-]?$')
CRBITS = ('lt', 'gt', 'eq', 'so')
XERF = ('so', 'ov', 'ca')
VOLATILE = {'cr0', 'cr1', 'cr5', 'cr6', 'cr7', 'ctr', 'xer', 'reserved'}
CALL = re.compile(r'(?<![\w.])(\w+)\(ctx, base\)|(REX_CALL_INDIRECT_FUNC|PPC_CALL_INDIRECT_FUNC)\(')
GOTO = re.compile(r'goto (loc_[0-9A-Fa-f]+);')
LABEL = re.compile(r'^\s*(loc_[0-9A-Fa-f]+):')
GEN = dict(A=r'build\agent2\snap1\DimensionsRecomp\rexlego\generated\default',
           B=r'build\agent2\snapB3\DimensionsRecomp\rexlego\generated\default')


def tus(d):
    return sorted(int(m.group(1)) for m in (re.match(r'^legodimensions_recomp\.(\d+)\.cpp$', f)
                                             for f in os.listdir(d)) if m)


def funcs(d):
    for tu in tus(d):
        with open(os.path.join(d, 'legodimensions_recomp.%d.cpp' % tu), 'rb') as f:
            data = f.read()
        for m in DEF_RE.finditer(data):
            name = (m.group(1) or m.group(2) or m.group(3)).decode()
            e = data.find(b'\n}', m.start())
            yield tu, name, data[m.start():(e + 2) if e >= 0 else len(data)].decode('utf-8', 'replace').split('\n')


def norm(s):
    return re.sub(r'0x[0-9A-Fa-f]+|\b\d+\b', 'N', re.sub(r'\b(?:r|f|v)\d+\b', 'R', s.strip()))[:150]


def mk_classifier(v, f):
    """Return cls(s) -> 'W', 'R' or None for local v, field f (CR bit, xer field or None)."""
    b = r'(?<![\w.])' + v
    if v.startswith('cr'):
        alt = 'so|un' if f == 'so' else f
        w_all = re.compile(r'^%s(?:\.(?:compare|setFromMask|set_raw)\b|\s*=(?!=))' % v)
        w_bit = re.compile(r'^%s\.(lt|gt|eq|so|un)\s*=(?!=)(.*)$' % v)
        rd = re.compile(r'%s\.(?:%s)\b|%s\.raw\(|%s\b(?!\.)' % (b, alt, b, b))

        def cls(s):
            if w_all.match(s):
                return 'W'
            m = w_bit.match(s)
            if m:
                if rd.search(m.group(2)):
                    return 'R'
                bit = 'so' if m.group(1) == 'un' else m.group(1)
                return 'W' if bit == f else None
            return 'R' if rd.search(s) else None
        return cls
    if v == 'xer':
        w_all = re.compile(r'^xer(?:\.(?:u64|u32|s64|s32))?\s*=(?!=)')
        w_f = re.compile(r'^xer\.(so|ov|ca)\s*=(?!=)(.*)$')
        rd = re.compile(r'%s\.%s\b|%s\.(?:u64|u32|s64|s32)\b|%s\b(?!\.)' % (b, f, b, b))

        def cls(s):
            if w_all.match(s):
                return 'W'
            m = w_f.match(s)
            if m:
                if rd.search(m.group(2)):
                    return 'R'
                return 'W' if m.group(1) == f else None
            return 'R' if rd.search(s) else None
        return cls
    w = re.compile(r'^%s(?:\.\w+)?\s*=(?!=)(.*)$' % v)
    rd = re.compile(b + r'\b')

    def cls(s):
        m = w.match(s)
        if m:
            return 'R' if rd.search(m.group(1)) else 'W'
        return 'R' if rd.search(s) else None
    return cls


def side_b(out):
    t0 = time.time()
    n = dict(funcs=0, with_locals=0, keys=0, never_used=0, write_first=0, read_first=0, read_loop_first=0,
             read_after_call=0, funcs_read_after_call=0)
    pats, ex, rows, pats2, ex2, rows2 = {}, {}, [], {}, {}, []
    for tu, name, lines in funcs(GEN['B']):
        n['funcs'] += 1
        locs = [m.group(1) for m in (DECL.match(l) for l in lines[1:40]) if m]
        if not locs:
            continue
        n['with_locals'] += 1
        code = [(i, l.rstrip('\r')) for i, l in enumerate(lines) if not INSN.match(l) and not DECL.match(l)]
        labels = {}
        for i, l in code:
            mm = LABEL.match(l)
            if mm:
                labels[mm.group(1)] = i
        keys = []
        for v in locs:
            fl = CRBITS if v.startswith('cr') else (XERF if v == 'xer' else (None,))
            for f in fl:
                keys.append((v, f, mk_classifier(v, f)))
        n['keys'] += len(keys)
        state = {(v, f): 'none' for v, f, _ in keys}
        first = {}
        rac = False
        for ci, (i, l) in enumerate(code):
            s = l.strip()
            cm = CALL.search(s)
            if cm:
                nm = cm.group(1) or cm.group(2)
                nxt = next((code[j][1].strip() for j in range(ci + 1, len(code)) if code[j][1].strip()), '')
                tail = 'return' in s or nxt.startswith('return')
                if not tail and not nm.startswith('__save') and not nm.startswith('__rest'):
                    for k in state:
                        if state[k] == 'w':
                            state[k] = 'stale'
                continue
            for v, f, cls in keys:
                if v not in s:
                    continue
                c = cls(s)
                if c is None:
                    continue
                k = (v, f)
                if k not in first:
                    first[k] = (c, i, s)
                if c == 'W':
                    state[k] = 'w'
                elif state[k] == 'stale' and v in VOLATILE:
                    n['read_after_call'] += 1
                    rac = True
                    kk = '%s%s: %s' % (v, '.' + f if f else '', norm(s))
                    pats2[kk] = pats2.get(kk, 0) + 1
                    ex2.setdefault(kk, [])
                    if len(ex2[kk]) < 4:
                        ex2[kk].append('%s (TU %d, line +%d)' % (name, tu, i))
                    if len(rows2) < 3000:
                        rows2.append('%s %s%s line +%d: %s' % (name, v, '.' + f if f else '', i, s))
                    state[k] = 'w'  # report once per write->call->read chain
        if rac:
            n['funcs_read_after_call'] += 1
        for v, f, _ in keys:
            k = (v, f)
            if k not in first:
                n['never_used'] += 1
                continue
            c, i, s = first[k]
            if c == 'W':
                n['write_first'] += 1
                continue
            back = any(GOTO.search(l) and labels.get(GOTO.search(l).group(1), 10**9) <= i
                       for j, l in code if j > i)
            kind = 'read-loop' if back else 'read'
            n['read_loop_first' if back else 'read_first'] += 1
            kk = '%s %s%s: %s' % (kind, v, '.' + f if f else '', norm(s))
            pats[kk] = pats.get(kk, 0) + 1
            ex.setdefault(kk, [])
            if len(ex[kk]) < 4:
                ex[kk].append('%s (TU %d, line +%d)' % (name, tu, i))
            if len(rows) < 3000:
                rows.append('%s %s %s%s line +%d: %s' % (kind, name, v, '.' + f if f else '', i, s))
    L = ['livein B v2 (snapB3): %s  (%.0f s)' % (' '.join('%s=%d' % kv for kv in n.items()), time.time() - t0),
         '', 'check 1: first use is a read, by pattern (kind var: normalised line) count, examples:']
    for k, c in sorted(pats.items(), key=lambda kv: -kv[1]):
        L.append('  %6d  %s   e.g. %s' % (c, k, '; '.join(ex[k])))
    L += ['', 'check 2: read of a volatile local after a non-tail call, last write before the call, by pattern:']
    for k, c in sorted(pats2.items(), key=lambda kv: -kv[1]):
        L.append('  %6d  %s   e.g. %s' % (c, k, '; '.join(ex2[k])))
    L += ['', 'check 1 rows (first 3000):'] + rows + ['', 'check 2 rows (first 3000):'] + rows2
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L[:80]))


def side_a(out):
    t0 = time.time()
    n = dict(funcs=0, so_writer_funcs=0, so_reader_funcs=0, stcx_funcs=0, stcx_without_larx=0)
    w, r, x = [], [], []
    for tu, name, lines in funcs(GEN['A']):
        n['funcs'] += 1
        ins = [m.group(1) for m in (INSN.match(l) for l in lines[1:]) if m]
        ws = sorted({i for i in ins if SO_W.match(i)} | {'mtspr xer' for l in lines if re.match(r'^\s*// mtspr\s+(?:1|xer),', l)})
        rs = sorted({i for i in ins if SO_R.match(i)})
        if ws:
            n['so_writer_funcs'] += 1
            w.append('%s TU %d: %s' % (name, tu, ', '.join(ws)))
        if rs:
            n['so_reader_funcs'] += 1
            r.append('%s TU %d: %s' % (name, tu, ', '.join(rs)))
        st = [i for i in ins if i in ('stwcx.', 'stdcx.')]
        if st:
            n['stcx_funcs'] += 1
            if not any(i in ('lwarx', 'ldarx') for i in ins):
                n['stcx_without_larx'] += 1
                x.append('%s TU %d: %d stcx, no larx' % (name, tu, len(st)))
    L = ['livein A (snap1): %s  (%.0f s)' % (' '.join('%s=%d' % kv for kv in n.items()), time.time() - t0),
         '', 'XER.SO writers:'] + w + ['', 'SO readers (mfxer, mcrxr, bso/bns):'] + r + \
        ['', 'stwcx./stdcx. without lwarx/ldarx in the same function:'] + x
    open(out, 'w', newline='\n').write('\n'.join(L) + '\n')
    print('\n'.join(L[:80]))


if __name__ == '__main__':
    s = sys.argv[1]
    if s == 'A':
        side_a(os.path.join('build', 'agent10', 'fe', 'livein-A.txt'))
    else:
        side_b(os.path.join('build', 'agent10', 'fe', 'livein-B2.txt'))
