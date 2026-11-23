"""lrdiff.py: check that a regenerated LEGO codegen tree differs from the 23:28 batch tree
only in LR bookkeeping (Agent 10; reads other agents' trees, writes only build/agent10/).

  python lrdiff.py scan <tree> <out.pkl>
  python lrdiff.py compare <A.pkl> <B.pkl> <ref.pkl|-> <report.txt>

<tree> is an install root (generated/default/...) or a generated dir (default/...).
Per DEFINE_REX_FUNC body, scan removes the LR statements
    \tctx.lr = 0x...;        (bl/bctrl/blrl return address)
    \tctx.lr = ctx.rN.u64;   (mtlr)
    \tctx.rN.u64 = ctx.lr;   (mflr)
and trailing blank lines, then hashes the rest ("norm") and, separately, the removed LR
lines in order ("lrseq"). compare checks A.norm == B.norm for every function (so B = A plus
LR statements only) and B.lrseq == ref.lrseq (ref = the all-options-off output of the same
tool, so B's LR bookkeeping is exactly the default one). TUs are re-partitioned when the
output size changes, so the per-TU headers are compared as a set of lines and the TU
preambles without their TU numbers; the other files are compared one by one.
"""
import collections
import difflib
import hashlib
import os
import pickle
import re
import sys

FUNC = b'\nDEFINE_REX_FUNC('
LRALL = re.compile(rb'^\tctx\.lr = (?:0x[0-9A-Fa-f]+|ctx\.r\d+\.u64);\n|^\tctx\.r\d+\.u64 = ctx\.lr;\n', re.M)
TU = re.compile(r'^legodimensions_recomp\.(\d+)\.cpp$')
TUH = re.compile(r'^legodimensions_funcs\.(\d+)\.h$')
TUNUM = re.compile(rb'legodimensions_(?:recomp|funcs)\.\d+\.')
SMALL = ['legodimensions_pch.h', 'legodimensions_init.h', 'sources.cmake', 'codegen.d']
BIG = ['legodimensions_funcs.h', 'legodimensions_init.cpp', 'legodimensions_register.cpp',
       'codegen.partition.json', 'codegen.stamp', 'codegen.build.stamp']


def gendir(t):
    for sub in ('generated/default', 'default', ''):
        p = os.path.normpath(os.path.join(t, sub))
        if os.path.exists(os.path.join(p, 'legodimensions_init.cpp')):
            return p
    raise SystemExit('no codegen output under ' + t)


def numbered(d, rx):
    out = []
    for f in os.listdir(d):
        m = rx.match(f)
        if m:
            out.append((int(m.group(1)), f))
    return [f for _, f in sorted(out)]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().replace(b'\r\n', b'\n')


def split_funcs(data):
    parts = (b'\n' + data).split(FUNC)
    funcs = []
    for p in parts[1:]:
        funcs.append((p[:p.index(b')')].decode(), b'DEFINE_REX_FUNC(' + p))
    return parts[0], funcs


def norm_chunk(chunk):
    lr = LRALL.findall(chunk)
    norm = LRALL.sub(b'', chunk).rstrip(b'\n') + b'\n'
    return norm, lr


def scan(tree, out):
    d = gendir(tree)
    S = {'tree': tree, 'dir': d, 'funcs': {}, 'dups': [], 'other_lr': [], 'pre': collections.Counter(),
         'n': collections.Counter(), 'tus': 0, 'small': {}, 'big': {}, 'hdr': set(), 'config': None}
    for f in numbered(d, TU):
        S['tus'] += 1
        pre, funcs = split_funcs(read(os.path.join(d, f)))
        for l in pre.split(b'\n'):
            S['pre'][TUNUM.sub(b'legodimensions_X.N.', l)] += 1
        for name, chunk in funcs:
            norm, lr = norm_chunk(chunk)
            for l in lr:
                if l.startswith(b'\tctx.lr = 0x'):
                    S['n']['lr_const'] += 1
                elif l.startswith(b'\tctx.lr = '):
                    S['n']['lr_mtlr'] += 1
                else:
                    S['n']['mflr'] += 1
            if lr:
                S['n']['funcs_with_lr'] += 1
            if b'ctx.lr' in norm:
                for l in norm.split(b'\n'):
                    if b'ctx.lr' in l:
                        S['other_lr'].append((name, l.decode('latin-1')))
            if name in S['funcs']:
                S['dups'].append(name)
            S['funcs'][name] = (hashlib.sha1(norm).digest()[:12], hashlib.sha1(b''.join(lr)).digest()[:12], len(lr), f)
    for f in numbered(d, TUH):
        for l in read(os.path.join(d, f)).split(b'\n'):
            S['hdr'].add(TUNUM.sub(b'legodimensions_X.N.', l))
    for f in SMALL:
        p = os.path.join(d, f)
        S['small'][f] = read(p) if os.path.exists(p) else None
    for f in BIG:
        p = os.path.join(d, f)
        S['big'][f] = (hashlib.sha256(read(p)).hexdigest(), p) if os.path.exists(p) else None
    for c in (os.path.join(tree, 'legodimensions_config.toml'), os.path.join(d, '..', 'legodimensions_config.toml'),
              os.path.join(d, '..', '..', 'legodimensions_config.toml')):
        if os.path.exists(c):
            S['config'] = (os.path.normpath(c), read(c))
            break
    with open(out, 'wb') as o:
        pickle.dump(S, o, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"{tree}: {S['tus']} TUs, {len(S['funcs'])} functions, dups {len(S['dups'])}, {dict(S['n'])}, "
          f"other ctx.lr lines {len(S['other_lr'])}, header lines {len(S['hdr'])}")


def udiff(a, b, na='A', nb='B', cap=60):
    al = a.decode('latin-1').split('\n') if a is not None else ['<missing>']
    bl = b.decode('latin-1').split('\n') if b is not None else ['<missing>']
    return list(difflib.unified_diff(al, bl, na, nb, n=1, lineterm=''))[:cap]


def extract(d, f, name):
    _, funcs = split_funcs(read(os.path.join(d, f)))
    for n, c in funcs:
        if n == name:
            return norm_chunk(c)
    return None, []


def setdiff(w, label, a, b, cap=25):
    oa, ob = sorted(a - b), sorted(b - a)
    w(f'{label}: {len(oa)} lines only in A, {len(ob)} only in B')
    for l in oa[:cap]:
        w('  - ' + l.decode('latin-1')[:200])
    for l in ob[:cap]:
        w('  + ' + l.decode('latin-1')[:200])


def compare(pa, pb, pr, out):
    A = pickle.load(open(pa, 'rb'))
    B = pickle.load(open(pb, 'rb'))
    R = pickle.load(open(pr, 'rb')) if pr != '-' else None
    W = []
    w = W.append
    for tag, S in (('A', A), ('B', B), ('ref', R)):
        if S:
            w(f"{tag} {S['tree']} ({S['dir']}): {S['tus']} TUs, {len(S['funcs'])} functions, duplicates {len(S['dups'])}, "
              f"LR lines {dict(S['n'])}, other ctx.lr lines {len(S['other_lr'])}")
    fa, fb = A['funcs'], B['funcs']
    onlyA, onlyB = sorted(set(fa) - set(fb)), sorted(set(fb) - set(fa))
    common = [n for n in fa if n in fb]
    ne = [n for n in common if fa[n][0] != fb[n][0]]
    ident = sum(1 for n in common if fa[n][0] == fb[n][0] and fa[n][1] == fb[n][1])
    w(f'functions only in A {len(onlyA)} {onlyA[:10]}, only in B {len(onlyB)} {onlyB[:10]}')
    w(f'common {len(common)}: body minus LR statements EQUAL {len(common) - len(ne)}, DIFFERENT {len(ne)}; '
      f'fully identical (same LR statements too) {ident}')
    w(f"A functions with LR statements: {sum(1 for n in fa if fa[n][2])} {[n for n in fa if fa[n][2]][:10]}")
    for n in ne[:12]:
        na, _ = extract(A['dir'], fa[n][3], n)
        nb, _ = extract(B['dir'], fb[n][3], n)
        w(f'DIFF {n} (A {fa[n][3]}, B {fb[n][3]}):')
        W.extend('    ' + l[:200] for l in udiff(na, nb))
    if R:
        fr = R['funcs']
        lne = [n for n in fb if n in fr and fb[n][1] != fr[n][1]]
        w(f"B LR statements vs ref: EQUAL {sum(1 for n in fb if n in fr and fb[n][1] == fr[n][1])}, DIFFERENT {len(lne)}, "
          f"B functions missing in ref {sum(1 for n in fb if n not in fr)}")
        for n in lne[:8]:
            _, lb = extract(B['dir'], fb[n][3], n)
            _, lr = extract(R['dir'], fr[n][3], n)
            w(f'LRDIFF {n} (B {len(lb)} vs ref {len(lr)} LR statements):')
            W.extend('    ' + l[:200] for l in udiff(b''.join(lr), b''.join(lb), 'ref', 'B', cap=30))
    oa = collections.Counter(A['other_lr'])
    ob = collections.Counter(B['other_lr'])
    w(f'other ctx.lr lines (kept in the body): A {sum(oa.values())}, B {sum(ob.values())}, same multiset {oa == ob}')
    for (n, l), c in sorted((ob | oa).items())[:20]:
        w(f'  {n}: {l.strip()[:160]} (A {oa[(n, l)]}, B {ob[(n, l)]})')
    setdiff(w, 'TU preambles (TU numbers masked)', set(A['pre']), set(B['pre']))
    setdiff(w, 'per-TU headers as a line set (TU numbers masked)', A['hdr'], B['hdr'])
    for f in SMALL:
        a, b = A['small'].get(f), B['small'].get(f)
        if a == b:
            w(f'{f}: identical')
        else:
            w(f'{f}: DIFFERENT')
            W.extend('    ' + l[:200] for l in udiff(a, b, cap=40))
    for f in BIG:
        a, b = A['big'].get(f), B['big'].get(f)
        if a and b and a[0] == b[0]:
            w(f'{f}: identical ({a[0][:16]})')
        elif a and b:
            la, lb = read(a[1]).split(b'\n'), read(b[1]).split(b'\n')
            setdiff(w, f'{f}: DIFFERENT ({a[0][:16]} vs {b[0][:16]}), {len(la)} vs {len(lb)} lines; line set', set(la), set(lb), cap=8)
        else:
            w(f'{f}: missing on one side (A {bool(a)}, B {bool(b)})')
    ca, cb = A['config'], B['config']
    w(f"config: A {ca[0] if ca else None}, B {cb[0] if cb else None}")
    if ca and cb:
        W.extend('    ' + l[:200] for l in udiff(ca[1], cb[1], cap=40))
    with open(out, 'w', encoding='utf-8') as o:
        o.write('\n'.join(W) + '\n')
    print('\n'.join(W)[:9000])


if __name__ == '__main__':
    if sys.argv[1] == 'scan':
        scan(sys.argv[2], sys.argv[3])
    else:
        compare(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
