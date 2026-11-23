#!/usr/bin/env python3
"""fediff v2: (b) helper (Agent 10, task #17). Read-only and targeted: no tree scans.

For each guest ADDR, one sequential pass over each link map finds the generated TU of the function:
the exact sub_ADDR, or else the containing function (the highest __imp__sub_ start <= ADDR). The body
is then read from that one TU in snap1 (A, located with the native3d map) and in snapB3 (B, located
with the nativeB map). TU numbers differ between the two builds, so each side uses its own map.

Writes, per function F:
  OUT/A-F.txt, OUT/B-F.txt   the bodies (CRLF -> LF)
  OUT/F.diff                 difflib unified diff A -> B
  OUT/F-insn.txt             each guest instruction (the "// insn" comments) whose C++ differs after
                             dropping "ctx.", with its class (below)
and appends to OUT/summary.txt: counts (lines, insns, loads, stores, calls, tail calls, lr writes,
timebase reads, ctx refs), callees, and the class tally.

Classes (v2), so that only real differences need a human:
  decl   prologue differs only by B's local declarations (ctr / xer / reserved / crN)
  cr     A "crN.compare<T>(a, b, xer)" == B "crN.compare<T>(a, b, {})" (CR as a local, SO = 0)
  tail   A "X(ctx, base); return;" == B "[[clang::musttail]] return X(ctx, base);"
  flush  only lines mentioning flush mode differ
  rlw    rlw*/shift-mask family, PROVEN equal by executing A's and B's C++ statements with C++ integer
         semantics (32/64-bit, signed/unsigned, usual conversions, u32 stores keep the upper half) on
         2000 states (random 64-bit registers plus edge values); compares every written register
  RLW-MISMATCH  an rlw* block whose A and B results differ (printed with a counterexample)
  OTHER  anything else, for manual review
  SEQ    the guest instruction sequences differ
Compares count SO as 0 on both sides in the rlw proof (the cr class assumption; see the SO-writer flag).

Usage: fediff.py ADDR [ADDR ...] [--out DIR] [--mapA M] [--mapB M] [--genA D] [--genB D] [--ctx N]
       fediff.py --selftest
"""
import argparse, bisect, difflib, os, random, re, sys

DEF = dict(
    mapA=r'build\agent2\native3d-bin\legodimensions.map',
    mapB=r'build\agent2\nativeB-bin\legodimensions.map',
    genA=r'build\agent2\snap1\DimensionsRecomp\rexlego\generated\default',
    genB=r'build\agent2\snapB3\DimensionsRecomp\rexlego\generated\default',
    out=r'build\agent10\fe\out')
TU_RE = re.compile(r'legodimensions_recomp\.(\d+)\.cpp\.obj$')
NEXT_DEF = re.compile(rb'^(?:DEFINE_REX_FUNC\(|PPC_FUNC_IMPL\(|PPC_FUNC\()', re.M)
INSN = re.compile(r'^\s*// (.*)$')
CALL = re.compile(r'\b([A-Za-z_]\w*)\(ctx, base\)')
TAIL = re.compile(r'musttail|\breturn\s+[A-Za-z_]\w*\(ctx, base\)')
TB_INSN = re.compile(r'^(?:mftbu?\b|mfspr\s+\S+,\s*26[89]\b)')
TB_CODE = re.compile(r'(?i)rdtsc|QueryPerformance|timebase|mftb')
RLW = re.compile(r'^(?:rlwinm|rlwimi|rlwnm|rotlwi|rotrwi|rotlw|slwi|srwi|clrlwi|clrrwi|clrlslwi|extlwi|extrwi'
                 r'|inslwi|insrwi)\.?\s')
SO_WRITER = re.compile(r'^(?:(?:add|addc|adde|addme|addze|subf|subfc|subfe|subfme|subfze|neg|mullw|mulld|divw'
                       r'|divwu|divd|divdu)o\.?|mtxer)\s|^mtspr\s+(?:1|xer),')
LOCAL_DECL = re.compile(r'^PPC(?:CR|XER)?Register (?:ctr|xer|reserved|cr\d)\{\};$')
TAILPAT = re.compile(r'\b([A-Za-z_]\w*)\(ctx, base\); return;')
M64 = (1 << 64) - 1


# ---------------------------------------------------------------- C++ integer evaluator (rlw proofs)
class V:
    __slots__ = ('v', 'b', 's')

    def __init__(self, v, b=32, s=True):
        v &= (1 << b) - 1
        if s and v >> (b - 1):
            v -= 1 << b
        self.v, self.b, self.s = v, b, s

    def _bin(self, o, f):
        if not isinstance(o, V):
            o = V(o, 32, True)
        b, s = common(self, o)
        return V(f(self.v, o.v), b, s)

    def __and__(self, o): return self._bin(o, lambda x, y: x & y)
    def __or__(self, o): return self._bin(o, lambda x, y: x | y)
    def __xor__(self, o): return self._bin(o, lambda x, y: x ^ y)
    def __add__(self, o): return self._bin(o, lambda x, y: x + y)
    def __sub__(self, o): return self._bin(o, lambda x, y: x - y)
    def __mul__(self, o): return self._bin(o, lambda x, y: x * y)

    def __lshift__(self, o):
        p = prom(self)
        return V(p.v << (o.v if isinstance(o, V) else o), p.b, p.s)

    def __rshift__(self, o):
        p = prom(self)
        return V(p.v >> (o.v if isinstance(o, V) else o), p.b, p.s)

    def __invert__(self):
        p = prom(self)
        return V(~p.v, p.b, p.s)

    def __neg__(self):
        p = prom(self)
        return V(-p.v, p.b, p.s)

    def __pos__(self):
        return prom(self)


def prom(a):
    return V(a.v, 32, True) if a.b < 32 else a


def common(a, o):
    a, o = prom(a), prom(o)
    if (a.b, a.s) == (o.b, o.s):
        return a.b, a.s
    if a.s == o.s:
        return max(a.b, o.b), a.s
    us, sg = (a, o) if not a.s else (o, a)
    return (us.b, False) if us.b >= sg.b else (sg.b, True)


CT = {'uint8_t': (8, False), 'uint16_t': (16, False), 'uint32_t': (32, False), 'uint64_t': (64, False),
      'int8_t': (8, True), 'int16_t': (16, True), 'int32_t': (32, True), 'int64_t': (64, True)}
ST = {}


def G(r, f):
    return V(ST[r], int(f[1:]), f[0] == 's')


def C(t, x):
    b, s = CT[t]
    return V(x.v, b, s)


def ROTL64(x, n):
    x, n = V(x.v, 64, False).v, (n.v if isinstance(n, V) else n) & 63
    return V(((x << n) | (x >> (64 - n))) if n else x, 64, False)


def ROTL32(x, n):
    x, n = V(x.v, 32, False).v, (n.v if isinstance(n, V) else n) & 31
    return V(((x << n) | (x >> (32 - n))) if n else x, 32, False)


def L(t):
    m = re.match(r'^(0[xX][0-9A-Fa-f]+|\d+)([uU]?[lL]{0,2}|[lL]{1,2}[uU])$', t)
    num, suf = m.group(1), m.group(2).lower()
    hexa = num[:2] in ('0x', '0X')
    v = int(num, 16) if hexa else int(num)
    cands = [(32, True), (32, False), (64, True), (64, False)]
    if 'u' in suf:
        cands = [c for c in cands if not c[1]]
    elif not hexa:
        cands = [c for c in cands if c[1]]
    if 'll' in suf:
        cands = [c for c in cands if c[0] == 64]
    for b, s in cands:
        if v < ((1 << (b - 1)) if s else (1 << b)):
            return V(v, b, s)
    return V(v, 64, False)


ENV = {'G': G, 'C': C, 'ROTL64': ROTL64, 'ROTL32': ROTL32, 'L': L, '__builtins__': {}}
TOK = re.compile(r'''\s*(?:
  (?P<reg>(?:ctx\.)?(?:r\d+|temp|ctr|reserved)\.(?:u8|u16|u32|u64|s8|s16|s32|s64))\b
 |(?P<cast>u?int(?:8|16|32|64)_t)\s*\(
 |(?P<fn>__builtin_rotateleft(?:32|64))\s*\(
 |(?P<num>(?:0[xX][0-9A-Fa-f]+|\d+)(?:[uU][lL]{0,2}|[lL]{1,2}[uU]?)?)\b
 |(?P<op><<|>>|[-+*&|^~(),])
)''', re.X)
ASSIGN = re.compile(r'^(?:ctx\.)?(r\d+|temp|ctr|reserved)\.(u8|u16|u32|u64|s8|s16|s32|s64)\s*=\s*(.+);$')
CMPL = re.compile(r'^(?:ctx\.)?(cr\d)\.compare<(u?int(?:32|64)_t)>\((.+)\);$')


def to_py(e):
    out, i, e = [], 0, e.strip()
    while i < len(e):
        m = TOK.match(e, i)
        if not m or m.end() == i:
            raise ValueError('token at %r' % e[i:i + 24])
        i = m.end()
        if m.group('reg'):
            r, f = m.group('reg').replace('ctx.', '').split('.')
            out.append('G(%r,%r)' % (r, f))
        elif m.group('cast'):
            out.append('C(%r,' % m.group('cast'))
        elif m.group('fn'):
            out.append('ROTL%s(' % m.group('fn')[-2:])
        elif m.group('num'):
            out.append('L(%r)' % m.group('num'))
        else:
            out.append(m.group('op'))
    return ''.join(out)


def split_top(s):
    parts, depth, cur = [], 0, ''
    for ch in s:
        depth += (ch == '(') - (ch == ')')
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    return [p.strip() for p in parts + [cur]]


def compile_block(lines):
    prog = []
    for ln in (x.strip() for x in lines):
        if not ln or ln == '}' or re.match(r'^loc_[0-9A-Fa-f]+:$', ln):
            continue
        m = ASSIGN.match(ln)
        if m:
            prog.append(('set', m.group(1), m.group(2), compile(to_py(m.group(3)), '<e>', 'eval')))
            continue
        m = CMPL.match(ln)
        if m:
            a, b, _x = split_top(m.group(3))
            prog.append(('cmp', m.group(1), m.group(2), compile(to_py(a), '<e>', 'eval'),
                         compile(to_py(b), '<e>', 'eval')))
            continue
        raise ValueError('cannot evaluate: ' + ln)
    return prog


def execute(prog, st):
    global ST
    ST = dict(st)
    for p in prog:
        if p[0] == 'set':
            _, r, f, code = p
            bits = int(f[1:])
            nv = eval(code, ENV).v & ((1 << bits) - 1)
            ST[r] = nv if bits == 64 else (ST[r] & ~((1 << bits) - 1) & M64) | nv
        else:
            _, cr, t, ca, cb = p
            b, s = CT[t]
            x, y = V(eval(ca, ENV).v, b, s).v, V(eval(cb, ENV).v, b, s).v
            ST[cr] = (x < y, x > y, x == y, 0)
    return ST


EDGES = [0, M64, 1, 0x80000000, 0x7FFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF00000000, 0x8000000000000000,
         0x00000000FFFFFFFE, 0x0000000100000000, 0x00000000F0000000, 0x0F0F0F0F0F0F0F0F]
PROOF_CACHE = {}


def prove(la, lb, trials=2000):
    key = (tuple(la), tuple(lb))
    if key in PROOF_CACHE:
        return PROOF_CACHE[key]
    try:
        pa, pb = compile_block(la), compile_block(lb)
        regs = sorted(set(re.findall(r'\b(r\d+|temp|ctr|reserved)\.', ' '.join(la + lb))))
        written = sorted({p[1] for p in pa + pb if p[1] != 'temp'})
        rnd = random.Random(0xB3)
        res = (True, None)
        for _ in range(trials):
            st = {r: (rnd.choice(EDGES) if rnd.random() < 0.3 else rnd.getrandbits(64)) for r in regs}
            sa, sb = execute(pa, st), execute(pb, st)
            bad = [k for k in written if sa.get(k) != sb.get(k)]
            if bad:
                k = bad[0]
                res = (False, 'mismatch %s: in {%s} A=%s B=%s' % (
                    k, ', '.join('%s:%016X' % (r, v) for r, v in sorted(st.items())),
                    ('%016X' % sa[k]) if isinstance(sa.get(k), int) else sa.get(k),
                    ('%016X' % sb[k]) if isinstance(sb.get(k), int) else sb.get(k)))
                break
    except Exception as e:  # unparsable -> not proven
        res = (False, 'eval: %s' % e)
    PROOF_CACHE[key] = res
    return res


# ---------------------------------------------------------------- body handling
def read_map(path):
    imp, hooked = {}, {}
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'sub_' not in line:
                continue
            t = line.split()
            if len(t) < 4:
                continue
            name, obj = t[1], t[-1]
            try:
                if name.startswith('__imp__sub_') and len(name) == 19:
                    m = TU_RE.search(obj)
                    if m:
                        imp.setdefault(int(name[11:], 16), int(m.group(1)))
                elif name.startswith('sub_') and len(name) == 12 and 'legodimensions_recomp.' not in obj:
                    hooked.setdefault(int(name[4:], 16), obj)
            except ValueError:
                pass
    return imp, hooked


def resolve(addr, imp, starts):
    if addr in imp:
        return addr
    i = bisect.bisect_right(starts, addr) - 1
    return starts[i] if i >= 0 else None


def extract(gendir, tu, func):
    p = os.path.join(gendir, 'legodimensions_recomp.%d.cpp' % tu)
    if not os.path.exists(p):
        return None, p
    with open(p, 'rb') as f:
        data = f.read()
    name = b'sub_%08X' % func
    for key in (b'DEFINE_REX_FUNC(' + name + b')', b'PPC_FUNC_IMPL(__imp__' + name + b')', b'PPC_FUNC(' + name + b')'):
        k = data.find(key)
        if k < 0:
            continue
        ls = data.rfind(b'\n', 0, k) + 1
        nxt = NEXT_DEF.search(data, data.find(b'\n', k))
        body = data[ls:nxt.start() if nxt else len(data)].replace(b'\r\n', b'\n').decode('utf-8', 'replace')
        return [l.rstrip() for l in body.splitlines()], '%s:%d' % (os.path.basename(p), data.count(b'\n', 0, ls) + 1)
    return None, p


def blocks(body):
    pro, out, cur = [], [], None
    for ln in body[1:]:
        m = INSN.match(ln)
        if m:
            cur = [m.group(1).strip(), []]
            out.append(cur)
        elif cur is None:
            pro.append(ln.strip())
        elif ln.strip():
            cur[1].append(ln.strip())
    return pro, out


def norm(s):
    return re.sub(r'\bctx\.', '', s)


def classify(insn, la, lb):
    na, nb = [norm(x) for x in la], [norm(x) for x in lb]
    tags, ma = set(), []
    for x in na:
        if re.match(r'^cr\d\.compare<', x) and x.endswith(', xer);'):
            x = x[:-len(', xer);')] + ', {});'
            tags.add('cr')
        ma.append(x)
    ja = TAILPAT.sub(r'[[clang::musttail]] return \1(ctx, base);', ' '.join(ma))
    if ja != ' '.join(ma):
        tags.add('tail')
    if ja == ' '.join(nb):
        return '+'.join(sorted(tags)) or 'same', None
    fa = [x for x in ma if not re.search(r'(?i)flush', x)]
    fb = [x for x in nb if not re.search(r'(?i)flush', x)]
    if (len(fa) != len(ma) or len(fb) != len(nb)) and \
            TAILPAT.sub(r'[[clang::musttail]] return \1(ctx, base);', ' '.join(fa)) == ' '.join(fb):
        return '+'.join(sorted(tags | {'flush'})), None
    if RLW.match(insn + ' '):
        ok, info = prove(la, lb)
        return ('+'.join(sorted(tags | {'rlw'})), None) if ok else ('RLW-MISMATCH', info)
    return 'OTHER', None


def insn_diff(ba, bb):
    pa, ia = blocks(ba)
    pb, ib = blocks(bb)
    out, tally = [], {}

    def bump(k):
        tally[k] = tally.get(k, 0) + 1

    na, nb = [norm(x) for x in pa], [norm(x) for x in pb]
    if na != nb:
        ok = [x for x in na if not LOCAL_DECL.match(x)] == [x for x in nb if not LOCAL_DECL.match(x)]
        bump('decl' if ok else 'OTHER')
        out.append('== prologue differs (%s)' % ('decl' if ok else 'OTHER'))
        out += ['  A| ' + x for x in pa] + ['  B| ' + x for x in pb]
    sm = difflib.SequenceMatcher(None, [x[0] for x in ia], [x[0] for x in ib], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            bump('SEQ')
            out.append('== INSN SEQUENCE %s A[%d:%d] B[%d:%d]   (SEQ)' % (tag, i1 + 1, i2, j1 + 1, j2))
            out += ['  A: ' + x[0] for x in ia[i1:i2]] + ['  B: ' + x[0] for x in ib[j1:j2]]
            continue
        for k in range(i2 - i1):
            xa, xb = ia[i1 + k], ib[j1 + k]
            if [norm(x) for x in xa[1]] == [norm(x) for x in xb[1]]:
                continue
            cls, info = classify(xa[0], xa[1], xb[1])
            for c in cls.split('+'):
                bump(c)
            out.append('[%d] %s   (%s)' % (i1 + k + 1, xa[0], cls))
            out += ['  A| ' + x for x in xa[1]] + ['  B| ' + x for x in xb[1]]
            if info:
                out.append('  !! ' + info)
    so = sorted({x[0] for x in ia if SO_WRITER.match(x[0] + ' ')})
    return tally, out, so


def feats(body):
    insn = [INSN.match(l).group(1).strip() for l in body if INSN.match(l)]
    code = [l for l in body if not INSN.match(l)]
    callees = [m.group(1) for l in code for m in CALL.finditer(l)]
    return dict(lines=len(body), insn=len(insn),
                loads=sum(l.count('REX_LOAD_') for l in code), stores=sum(l.count('REX_STORE_') for l in code),
                calls=len(callees), tail=sum(1 for l in code if TAIL.search(l)),
                lr=sum(1 for l in code if re.search(r'\bctx\.lr\s*=', l)),
                tb=sum(1 for i in insn if TB_INSN.match(i)) + sum(1 for l in code if TB_CODE.search(l)),
                ctx=sum(len(re.findall(r'\bctx\.', l)) for l in code), callees=callees, insns=insn)


def selftest():
    a = ['ctx.r8.u64 = __builtin_rotateleft64(ctx.r3.u32 | (ctx.r3.u64 << 32), 3) & 0xFFFFFFF8;']
    cases = [
        ('rlwinm 3,0,28 -> u32<<3', a, ['ctx.r8.u64 = ctx.r3.u32 << 3;'], True),
        ('wrong shift', a, ['ctx.r8.u64 = ctx.r3.u32 << 4;'], False),
        ('wrap mask keeps the upper half',
         ['ctx.r8.u64 = __builtin_rotateleft64(ctx.r3.u32 | (ctx.r3.u64 << 32), 3) & 0xFFFFFFFF0000000F;'],
         ['ctx.r8.u64 = (ctx.r3.u32 << 3) & 0xF;'], False),
        ('srwi', ['ctx.r29.u64 = __builtin_rotateleft64(ctx.r30.u32 | (ctx.r30.u64 << 32), 24) & 0xF;'],
         ['ctx.r29.u64 = (ctx.r30.u32 >> 8) & 0xF;'], True),
        ('u32 store keeps the upper half', ['ctx.r4.u64 = ctx.r5.u32 & 0xFF;'], ['ctx.r4.u32 = ctx.r5.u32 & 0xFF;'], False),
        ('record form, SO=0', ['ctx.r3.u64 = ctx.r4.u32 & 0xFF;', 'ctx.cr0.compare<int32_t>(ctx.r3.s32, 0, ctx.xer);'],
         ['ctx.r3.u64 = ctx.r4.u32 & 0xFF;', 'cr0.compare<int32_t>(ctx.r3.s32, 0, {});'], True),
    ]
    bad = 0
    for name, la, lb, want in cases:
        PROOF_CACHE.clear()
        ok, info = prove(la, lb)
        print('%-34s expect %-5s got %-5s %s' % (name, want, ok, '' if ok == want else 'FAIL ' + str(info)))
        bad += ok != want
    print('selftest %s' % ('PASS' if not bad else 'FAIL (%d)' % bad))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('addr', nargs='*')
    for k, v in DEF.items():
        ap.add_argument('--' + k, default=v)
    ap.add_argument('--ctx', type=int, default=3, help='unified diff context lines')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    addrs = [int(x.lower().replace('sub_', '').replace('loc_', '').replace('0x', ''), 16) for x in a.addr]
    os.makedirs(a.out, exist_ok=True)
    side = {}
    for s, mp, gd in (('A', a.mapA, a.genA), ('B', a.mapB, a.genB)):
        imp, hooked = read_map(mp)
        side[s] = (imp, hooked, sorted(imp), gd)
        print('map %s: %s (%d __imp__sub_, %d hooked publics)' % (s, mp, len(imp), len(hooked)))
    rows, total = [], {}
    for addr in addrs:
        res = {}
        for s in 'AB':
            imp, hooked, starts, gd = side[s]
            f = resolve(addr, imp, starts)
            if f is None:
                res[s] = (None, None, None, 'no function <= %08X' % addr)
                continue
            body, where = extract(gd, imp[f], f)
            res[s] = (f, body, where, 'hooked:' + hooked[f] if f in hooked else '')
        fa, fb = res['A'][0], res['B'][0]
        head = '### %08X: A func %s %s %s | B func %s %s %s' % (
            addr, 'sub_%08X' % fa if fa else '-', res['A'][2], res['A'][3],
            'sub_%08X' % fb if fb else '-', res['B'][2], res['B'][3])
        print(head)
        if fa != fb or res['A'][1] is None or res['B'][1] is None:
            print('   cannot diff (function differs or body not found)')
            rows.append(head + '\n   cannot diff')
            continue
        ba, bb = res['A'][1], res['B'][1]
        name = 'sub_%08X' % fa
        for s, b in (('A', ba), ('B', bb)):
            with open(os.path.join(a.out, '%s-%s.txt' % (s, name)), 'w', newline='\n') as f:
                f.write('\n'.join(b) + '\n')
        ud = list(difflib.unified_diff(ba, bb, 'A/snap1/' + name, 'B/snapB3/' + name, n=a.ctx, lineterm=''))
        with open(os.path.join(a.out, name + '.diff'), 'w', newline='\n') as f:
            f.write('\n'.join(ud) + '\n')
        tally, idl, so = insn_diff(ba, bb)
        for k, v in tally.items():
            total[k] = total.get(k, 0) + v
        tstr = ' '.join('%s=%d' % kv for kv in sorted(tally.items())) or 'identical'
        with open(os.path.join(a.out, name + '-insn.txt'), 'w', newline='\n') as f:
            f.write('%s: classes %s; SO writers: %s\n' % (name, tstr, ', '.join(so) or 'none'))
            f.write('\n'.join(idl) + '\n')
        fA, fB = feats(ba), feats(bb)
        lines = [head, '   addr is %s' % ('the function start' if fa == addr else 'inside it (+0x%X)' % (addr - fa))]
        for k in ('lines', 'insn', 'loads', 'stores', 'calls', 'tail', 'lr', 'tb', 'ctx'):
            lines.append('   %-6s A %6d   B %6d%s' % (k, fA[k], fB[k], '' if fA[k] == fB[k] else '   *'))
        lines.append('   same insn sequence: %s; unified diff %d lines' % (fA['insns'] == fB['insns'], len(ud)))
        lines.append('   classes: %s; SO writers: %s' % (tstr, ', '.join(so) or 'none'))
        ca, cb = sorted(set(fA['callees'])), sorted(set(fB['callees']))
        lines.append('   callees A: %s' % ' '.join(ca))
        if ca != cb:
            lines.append('   callees B: %s   *' % ' '.join(cb))
        tbl = [i for i in fA['insns'] if TB_INSN.match(i)]
        if tbl:
            lines.append('   timebase insns: %s' % '; '.join(tbl))
        print('\n'.join(lines[1:]))
        rows.append('\n'.join(lines))
    tot = 'TOTAL classes over %d addresses: %s' % (len(addrs), ' '.join('%s=%d' % kv for kv in sorted(total.items())))
    print(tot)
    with open(os.path.join(a.out, 'summary.txt'), 'a', newline='\n') as f:
        f.write('\n'.join(rows + [tot]) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
