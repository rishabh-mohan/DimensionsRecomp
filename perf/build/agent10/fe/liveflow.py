#!/usr/bin/env python3
"""liveflow: CFG may-analysis of B's locals on chosen functions (Agent 10, task #17, read-only).

  liveflow.py --from build/agent10/fe/livein-B2.txt [--also NAME ...]
      takes every function named in livein-B2's check-1/check-2 pattern lists, plus --also names.

Per local key (CR bit, xer field, ctr, reserved) the facts at each line are a subset of
  U          unwritten since entry (B reads its zero initialiser; A reads the caller's ctx value)
  W          written since the last call
  S@callee   written before a non-tail call (not __save*/__rest*) and not rewritten since
Entry {U}. A write gives {W} (self-updates like --ctr / cr6.eq = cr6.lt | cr6.eq read first). A call maps
W -> S@callee. Edges: fallthrough, every 'goto loc_X', 'if (...) {' blocks; 'return'/'goto' end a path.
Reports reads that may see U, and reads of call-volatile locals (cr0 cr1 cr5 cr6 cr7 ctr xer reserved) that
may see S@callee. For each S@callee it then checks in snap1 (A) whether the callee, or anything it calls to
depth 4, writes ctx.<field>: only then can A and B read different values.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livein

IDX = os.path.join('build', 'agent10', 'fe', 'idxA.json')


def index_a():
    if os.path.exists(IDX):
        return json.load(open(IDX))
    d = livein.GEN['A']
    idx = {}
    for tu in livein.tus(d):
        with open(os.path.join(d, 'legodimensions_recomp.%d.cpp' % tu), 'rb') as f:
            data = f.read()
        for m in livein.DEF_RE.finditer(data):
            idx[(m.group(1) or m.group(2) or m.group(3)).decode()] = [tu, m.start()]
    json.dump(idx, open(IDX, 'w'))
    return idx


def body_a(idx, name, cache={}):
    if name in cache:
        return cache[name]
    if name not in idx:
        cache[name] = None
        return None
    tu, off = idx[name]
    with open(os.path.join(livein.GEN['A'], 'legodimensions_recomp.%d.cpp' % tu), 'rb') as f:
        f.seek(off)
        data = f.read(4 << 20)
    e = data.find(b'\n}')
    cache[name] = data[:(e + 2) if e >= 0 else len(data)].decode('utf-8', 'replace')
    return cache[name]


def selfwrite(s, v, f):
    if v.startswith('cr'):
        m = re.match(r'^%s\.(lt|gt|eq|so|un)\s*=(?!=)' % v, s)
        return bool(m) and ('so' if m.group(1) == 'un' else m.group(1)) == f
    if v == 'xer':
        m = re.match(r'^xer\.(so|ov|ca)\s*=(?!=)', s)
        return (bool(m) and m.group(1) == f) or bool(re.match(r'^xer(?:\.(?:u64|u32|s64|s32))?\s*=(?!=)', s))
    return bool(re.match(r'^(?:(?:--|\+\+)%s(?:\.\w+)?\s*;|%s(?:\.\w+)?\s*(?:[-+|&^]?=(?!=)|--|\+\+))' % (v, v), s))


def cfg(code):
    n = len(code)
    labels = {}
    for k, (i, l) in enumerate(code):
        m = livein.LABEL.match(l)
        if m:
            labels[m.group(1)] = k
    stack, close = [], {}
    for k, (i, l) in enumerate(code):
        s = l.strip()
        if k > 0 and s.endswith('{'):
            stack.append(k)
        elif s.startswith('}') and stack:
            close[stack.pop()] = k
    succ = [set() for _ in range(n)]
    for k, (i, l) in enumerate(code):
        s = l.strip()
        for g in livein.GOTO.finditer(s):
            if g.group(1) in labels:
                succ[k].add(labels[g.group(1)])
        uncond = s.startswith('goto ') or s.startswith('return') or s.startswith('[[clang::musttail]] return')
        if k in close:
            succ[k].add(k + 1)
            if close[k] + 1 < n:
                succ[k].add(close[k] + 1)
        elif not uncond and k + 1 < n:
            succ[k].add(k + 1)
    return succ


def calls_of(code):
    out = []
    for k, (i, l) in enumerate(code):
        s = l.strip()
        cm = livein.CALL.search(s)
        c = None
        if cm:
            nm = cm.group(1) or cm.group(2)
            nxt = next((code[j][1].strip() for j in range(k + 1, len(code)) if code[j][1].strip()), '')
            tail = 'return' in s or nxt.startswith('return')
            if not tail and not nm.startswith('__save') and not nm.startswith('__rest'):
                c = '%s@%d' % (nm, i)
        out.append(c)
    return out


def analyse(lines):
    code = [(i, l.rstrip('\r')) for i, l in enumerate(lines) if not livein.INSN.match(l) and not livein.DECL.match(l)]
    locs = [m.group(1) for m in (livein.DECL.match(l) for l in lines[1:40]) if m]
    succ, calls = cfg(code), calls_of(code)
    res = []
    for v in locs:
        for f in (livein.CRBITS if v.startswith('cr') else (livein.XERF if v == 'xer' else (None,))):
            cls = livein.mk_classifier(v, f)
            IN = [None] * len(code)
            IN[0] = frozenset(['U'])
            work = [0]
            while work:
                k = work.pop()
                st = set(IN[k])
                s = code[k][1].strip()
                c = cls(s) if v in s else None
                if c == 'W' or (c == 'R' and selfwrite(s, v, f)):
                    st = {'W'}
                if calls[k]:
                    st = {('S@' + calls[k]) if x == 'W' else x for x in st}
                st = frozenset(st)
                for j in succ[k]:
                    nst = st if IN[j] is None else (IN[j] | st)
                    if nst != IN[j]:
                        IN[j] = nst
                        work.append(j)
            for k, (i, l) in enumerate(code):
                s = l.strip()
                if IN[k] is None or v not in s or cls(s) != 'R':
                    continue
                if 'U' in IN[k]:
                    res.append(('U', v, f, i, s, []))
                ss = sorted(x[2:] for x in IN[k] if x.startswith('S@'))
                if ss and v in livein.VOLATILE:
                    res.append(('S', v, f, i, s, ss))
    return res


A_WRITE = '(?:ctx\\.%s\\.(?:compare|setFromMask|set_raw)\\b|ctx\\.%s\\.%s\\s*=(?!=)|ctx\\.%s\\s*=(?!=))'


def callee_writes(idx, callee, v, f, depth=4, seen=None):
    """Does callee (A body) write ctx.v(.f), directly or through calls to depth? Returns a path or None."""
    seen = set() if seen is None else seen
    if callee in seen or depth < 0:
        return None
    seen.add(callee)
    b = body_a(idx, callee)
    if b is None:
        return ['%s (not a generated function: import/hook, unknown)' % callee]
    if v.startswith('cr'):
        pat = A_WRITE % (v, v, f if f != 'so' else '(?:so|un)', v)
    elif v == 'xer':
        pat = r'ctx\.xer\.%s\s*=(?!=)|ctx\.xer(?:\.(?:u64|u32))?\s*=(?!=)' % f
    else:
        pat = r'ctx\.%s(?:\.\w+)?\s*=(?!=)|--ctx\.%s\b' % (v, v)
    if re.search(pat, b):
        return [callee]
    for nm in sorted(set(re.findall(r'(?<![\w.])(sub_[0-9A-F]{8})\(ctx, base\)', b))):
        p = callee_writes(idx, nm, v, f, depth - 1, seen)
        if p:
            return [callee] + p
    if 'CALL_INDIRECT' in b:
        return [callee, '(indirect call: unknown)']
    return None


def main():
    names = []
    if '--from' in sys.argv:
        src = sys.argv[sys.argv.index('--from') + 1]
        for l in open(src, encoding='utf-8'):
            if l.startswith('check 1 rows'):
                break
            names += re.findall(r'(sub_[0-9A-F]{8}) \(TU (\d+)', l)
    if '--also' in sys.argv:
        names += [(n, None) for n in sys.argv[sys.argv.index('--also') + 1:]]
    seen, todo = set(), []
    for n, tu in names:
        if n not in seen:
            seen.add(n)
            todo.append((n, int(tu) if tu else None))
    import show
    idx = index_a()
    tot = dict(funcs=0, U=0, S=0, S_callee_writes=0, S_callee_unknown=0)
    out = []
    for n, tu in todo:
        t, lines = show.find('B', n, tu)
        tot['funcs'] += 1
        res = analyse(lines)
        if not res:
            out.append('%s TU %s: clean (no U read, no S read)' % (n, t))
            continue
        for kind, v, f, i, s, ss in res:
            key = v + ('.' + f if f else '')
            if kind == 'U':
                tot['U'] += 1
                out.append('%s TU %s line +%d U %s: %s' % (n, t, i, key, s))
                continue
            tot['S'] += 1
            verdicts = []
            for c in ss:
                cal = c.split('@')[0]
                if cal.startswith('REX_CALL_INDIRECT') or cal.startswith('PPC_CALL_INDIRECT'):
                    verdicts.append('%s: indirect, unknown' % c)
                    tot['S_callee_unknown'] += 1
                    continue
                p = callee_writes(idx, cal, v, f)
                if p and any('unknown' in x for x in p):
                    tot['S_callee_unknown'] += 1
                    verdicts.append('%s: UNKNOWN via %s' % (c, ' -> '.join(p)))
                elif p:
                    tot['S_callee_writes'] += 1
                    verdicts.append('%s: WRITES ctx.%s via %s' % (c, key, ' -> '.join(p)))
                else:
                    verdicts.append('%s: does not write ctx.%s (depth 4)' % (c, key))
            out.append('%s TU %s line +%d S %s: %s   | %s' % (n, t, i, key, s, '; '.join(verdicts)))
    print('liveflow: %s' % ' '.join('%s=%d' % kv for kv in tot.items()))
    print('\n'.join(out))


if __name__ == '__main__':
    main()
