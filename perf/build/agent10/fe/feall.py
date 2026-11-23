#!/usr/bin/env python3
"""feall: whole-tree classification of B's codegen differences (Agent 10, task #17 (b)). Read-only.

Pass 1 indexes every function definition in the B tree (snapB3): name -> (TU, start, end), where the
body ends at the first column-0 "}" after its definition line. Pass 2 walks the A tree (snap1) TU by TU
(only TUs with index % N == K for --part K/N), pairs every function with its B body and classifies the
difference with fediff's rules:
  fast path: drop "ctx.", rewrite A's "crN.compare<T>(a, b, xer)" to "{}" and A's "X(ctx, base); return;"
             to "[[clang::musttail]] return X(ctx, base);", drop B's local declarations; equal -> mechanical
  slow path: fediff.insn_diff per guest instruction (cr / tail / decl / flush / rlw proven by evaluation /
             RLW-MISMATCH / OTHER / SEQ); rlw proofs are cached on register-canonicalised text
Writes OUT/part-K.json and OUT/feall-other-K.txt (every OTHER / RLW-MISMATCH / SEQ block, capped);
--merge combines the parts into OUT/feall-summary.txt.

Usage: feall.py --part K/N [--genA D] [--genB D] [--out DIR] [--trials T]
       feall.py --merge [--out DIR]
"""
import argparse, glob, json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fediff as F  # noqa: E402

DEF_RE = re.compile(rb'^(?:DEFINE_REX_FUNC\((sub_[0-9A-F]{8})\)|PPC_FUNC_IMPL\(__imp__(sub_[0-9A-F]{8})\)'
                    rb'|PPC_FUNC\((sub_[0-9A-F]{8})\))', re.M)
CTX_RE = re.compile(r'\bctx\.')
CR_RE = re.compile(r'(?m)^(\s*cr\d\.compare<.*), xer\);$')
TAIL_RE = re.compile(r'\b([A-Za-z_]\w*)\(ctx, base\);\s+return;')
DECL_RE = re.compile(r'(?m)^\s*PPC(?:CR|XER)?Register (?:ctr|xer|reserved|cr\d)\{\};\n')
SO_RE = re.compile(r'(?m)^\s*// ((?:add|addc|adde|addme|addze|subf|subfc|subfe|subfme|subfze|neg|mullw|mulld'
                   r'|divw|divwu|divd|divdu)o\.?|mtxer|mtspr\s+(?:1|xer),)')
HDR = re.compile(r'^\[(\d+)\] (.*)   \((.+)\)$')


def defs(data):
    out = []
    for m in DEF_RE.finditer(data):
        name = (m.group(1) or m.group(2) or m.group(3)).decode()
        e = data.find(b'\n}', m.start())
        out.append((name, m.start(), (e + 2) if e >= 0 else len(data)))
    return out


def tus(gendir):
    r = []
    for fn in os.listdir(gendir):
        m = re.match(r'^legodimensions_recomp\.(\d+)\.cpp$', fn)
        if m:
            r.append(int(m.group(1)))
    return sorted(r)


def canon_prove(trials):
    orig = F.prove

    def p(la, lb, trials_=None):
        mp = {}

        def sub(m):
            r = m.group(1)
            if r not in mp:
                mp[r] = 'r%d' % len(mp)
            return mp[r] + '.'
        ca = [re.sub(r'\b(r\d+)\.', sub, x) for x in la]
        cb = [re.sub(r'\b(r\d+)\.', sub, x) for x in lb]
        return orig(ca, cb, trials)
    F.prove = p


def run_part(a):
    k, n = (int(x) for x in a.part.split('/'))
    t0 = time.time()
    canon_prove(a.trials)
    index = {}
    for tu in tus(a.genB):
        p = os.path.join(a.genB, 'legodimensions_recomp.%d.cpp' % tu)
        with open(p, 'rb') as f:
            data = f.read()
        for name, s, e in defs(data):
            index.setdefault(name, (tu, s, e))
    t1 = time.time()
    print('B index: %d functions in %.1f s' % (len(index), t1 - t0), flush=True)
    handles = {}
    cnt = dict(funcs=0, identical=0, fast=0, slow=0, missing=0, with_other=0, with_mismatch=0, with_seq=0)
    cls, hist, ex, mism, so_cr, other_funcs = {}, {}, {}, [], [], []
    seen = set()
    det = open(os.path.join(a.out, 'feall-other-%d.txt' % k), 'w', newline='\n')
    det_lines = 0
    mine = [tu for i, tu in enumerate(tus(a.genA)) if i % n == k]
    for j, tu in enumerate(mine):
        with open(os.path.join(a.genA, 'legodimensions_recomp.%d.cpp' % tu), 'rb') as f:
            data = f.read()
        for name, s, e in defs(data):
            if name in seen:
                continue
            seen.add(name)
            cnt['funcs'] += 1
            ib = index.get(name)
            if ib is None:
                cnt['missing'] += 1
                continue
            fh = handles.get(ib[0])
            if fh is None:
                fh = handles[ib[0]] = open(os.path.join(a.genB, 'legodimensions_recomp.%d.cpp' % ib[0]), 'rb')
            fh.seek(ib[1])
            tb = fh.read(ib[2] - ib[1]).replace(b'\r\n', b'\n').decode('utf-8', 'replace')
            ta = data[s:e].replace(b'\r\n', b'\n').decode('utf-8', 'replace')
            if ta == tb:
                cnt['identical'] += 1
                continue
            na, nb = CTX_RE.sub('', ta), CTX_RE.sub('', tb)
            na, ncr = CR_RE.subn(r'\1, {});', na)
            na, ntail = TAIL_RE.subn(r'[[clang::musttail]] return \1(ctx, base);', na)
            na2, nda = DECL_RE.subn('', na)
            nb2, ndb = DECL_RE.subn('', nb)
            so = SO_RE.findall(ta)
            if na2 == nb2:
                cnt['fast'] += 1
                for c, v in (('cr', ncr), ('tail', ntail), ('decl', 1 if (nda or ndb) else 0)):
                    if v:
                        cls[c] = cls.get(c, 0) + v
                if so and ncr:
                    so_cr.append('%s (%s)' % (name, ', '.join(sorted(set(so)))))
                continue
            cnt['slow'] += 1
            la = [l.rstrip() for l in ta.split('\n')]
            lb = [l.rstrip() for l in tb.split('\n')]
            tally, out, _so = F.insn_diff(la, lb)
            for c, v in tally.items():
                cls[c] = cls.get(c, 0) + v
            if so and tally.get('cr'):
                so_cr.append('%s (%s)' % (name, ', '.join(sorted(set(so)))))
            flags = [c for c in ('OTHER', 'RLW-MISMATCH', 'SEQ') if tally.get(c)]
            if not flags:
                continue
            for c in flags:
                cnt['with_' + {'OTHER': 'other', 'RLW-MISMATCH': 'mismatch', 'SEQ': 'seq'}[c]] += 1
            if len(other_funcs) < 5000:
                other_funcs.append('%s %s' % (name, ' '.join('%s=%d' % (c, tally[c]) for c in flags)))
            cur = None
            for ln in out + ['== end']:
                m = HDR.match(ln)
                start = m or ln.startswith('==')
                if start and cur is not None:
                    key, text = cur
                    hist[key] = hist.get(key, 0) + 1
                    ex.setdefault(key, [])
                    if len(ex[key]) < 3:
                        ex[key].append(text)
                    if 'RLW-MISMATCH' in text and len(mism) < 300:
                        mism.append(text)
                    if det_lines < 60000:
                        det.write(text + '\n')
                        det_lines += text.count('\n') + 1
                    cur = None
                if m and any(c in m.group(3) for c in ('OTHER', 'RLW-MISMATCH')):
                    cur = ['%s:%s' % ('MISMATCH' if 'RLW-MISMATCH' in m.group(3) else 'OTHER', m.group(2).split()[0]),
                           '%s %s' % (name, ln)]
                elif ln.startswith('== prologue differs (OTHER)'):
                    cur = ['OTHER:prologue', '%s %s' % (name, ln)]
                elif ln.startswith('== INSN SEQUENCE'):
                    cur = ['SEQ', '%s %s' % (name, ln)]
                elif cur is not None and not start:
                    cur[1] += '\n' + ln
        if j % 20 == 0:
            print('A TU %d (%d/%d): funcs %d identical %d fast %d slow %d other-funcs %d  %.0f s' % (
                tu, j + 1, len(mine), cnt['funcs'], cnt['identical'], cnt['fast'], cnt['slow'],
                cnt['with_other'], time.time() - t0), flush=True)
    det.close()
    res = dict(part=a.part, cnt=cnt, cls=cls, hist=hist, ex=ex, mism=mism, so_cr=so_cr, other_funcs=other_funcs,
               proofs=len(F.PROOF_CACHE), proof_fail=sum(1 for v in F.PROOF_CACHE.values() if not v[0]),
               secs=round(time.time() - t0, 1))
    with open(os.path.join(a.out, 'part-%d.json' % k), 'w', newline='\n') as f:
        json.dump(res, f, indent=1)
    print('done part %s: %s cls %s proofs %d (failed %d) in %.0f s' % (
        a.part, cnt, cls, res['proofs'], res['proof_fail'], res['secs']), flush=True)
    return 0


def merge(a):
    parts = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(a.out, 'part-*.json')))]
    cnt, cls, hist, ex, mism, so_cr, of = {}, {}, {}, {}, [], [], []
    for p in parts:
        for d, src in ((cnt, p['cnt']), (cls, p['cls']), (hist, p['hist'])):
            for kk, v in src.items():
                d[kk] = d.get(kk, 0) + v
        for kk, v in p['ex'].items():
            ex.setdefault(kk, []).extend(v)
        mism += p['mism']
        so_cr += p['so_cr']
        of += p['other_funcs']
    L = ['feall summary: %d parts (%s), A = %s, B = %s' % (len(parts), ', '.join(
        '%s %.0f s, %d proofs / %d failed' % (p['part'], p['secs'], p['proofs'], p['proof_fail']) for p in parts),
        a.genA, a.genB),
        'functions: ' + ' '.join('%s=%d' % kv for kv in sorted(cnt.items())),
        'classes:   ' + ' '.join('%s=%d' % kv for kv in sorted(cls.items())),
        'SO-writer functions with SO=0 compares (%d): %s' % (len(so_cr), ' '.join(so_cr[:60])),
        '', 'OTHER / MISMATCH / SEQ blocks by mnemonic:']
    for kk, v in sorted(hist.items(), key=lambda kv: -kv[1]):
        L.append('  %-28s %d' % (kk, v))
    L += ['', 'RLW-MISMATCH blocks (%d):' % len(mism)] + mism[:100]
    L += ['', 'Examples (up to 3 per key):']
    for kk in sorted(ex, key=lambda x: -hist.get(x, 0)):
        L.append('--- %s' % kk)
        L += ex[kk][:3]
    L += ['', 'Functions with OTHER / MISMATCH / SEQ (%d, first 400):' % len(of)] + of[:400]
    with open(os.path.join(a.out, 'feall-summary.txt'), 'w', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('\n'.join(L[:8 + min(len(hist), 40)]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--part')
    ap.add_argument('--merge', action='store_true')
    ap.add_argument('--genA', default=F.DEF['genA'])
    ap.add_argument('--genB', default=F.DEF['genB'])
    ap.add_argument('--out', default=r'build\agent10\fe\all')
    ap.add_argument('--trials', type=int, default=300)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.merge:
        return merge(a)
    return run_part(a)


if __name__ == '__main__':
    sys.exit(main())
