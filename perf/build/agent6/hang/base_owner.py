#!/usr/bin/env python3
"""Resolve STUCK-LOCK call sites to guest functions and show the generated code (read-only).

usage: python base_owner.py MAP ADDR [ADDR ...] [--body-n 5] [--gendir DIR] [--tu-map MAP2]
                            [--out FILE] [--full 700] [--ctx 14]

1. One sequential read of MAP: every sub_XXXXXXXX / __imp__sub_XXXXXXXX symbol and the
   object that defines it (last token of the map line).
2. For each ADDR: the containing sub_ (closest at or below), the offset, the next sub_ and
   the defining objects.
3. For the functions containing the first --body-n ADDRs: read only the generated TU the map
   names (no tree scan), find DEFINE_REX_FUNC(sub_X) and print
     - every call site in it ('ctx.lr = 0x...;' + the callee on the next line),
     - every backward branch (goto loc_Y with Y below the branch's own address comment),
     - the whole body if it has at most --full lines, else +-ctx lines around each ADDR.
   If the TU in MAP's partition does not hold the function and --tu-map is given, MAP2 is
   read once for the TU names of the missing functions only.
Single-threaded, stdlib only; writes nothing except --out (UTF-8, LF).
"""
import argparse
import bisect
import os
import re
import sys

TOK = re.compile(r'(?<![\w])((?:__imp__)?sub_([0-9A-Fa-f]{8}))(?![\w])')
NEXT_DEF = re.compile(rb'^(?:DEFINE_REX_FUNC\(|PPC_FUNC_IMPL\(|PPC_FUNC\()', re.M)
GEN_OBJ = re.compile(r'(legodimensions_recomp\.\d+\.cpp)\.obj$')
LR_SET = re.compile(r'ctx\.lr = 0x([0-9A-Fa-f]{8});')
CALLEE = re.compile(r'\b((?:__imp__)?sub_[0-9A-Fa-f]{8}|__\w+)\s*\(ctx, base\)')
ASM = re.compile(r'^\s*// (.*)$')
LABEL = re.compile(r'^loc_([0-9A-Fa-f]{8}):')
GOTO = re.compile(r'goto loc_([0-9A-Fa-f]{8});')

ap = argparse.ArgumentParser()
ap.add_argument('map')
ap.add_argument('addrs', nargs='+')
ap.add_argument('--body-n', type=int, default=5)
ap.add_argument('--gendir', default=os.path.join('DimensionsRecomp', 'rexlego', 'generated', 'default'))
ap.add_argument('--tu-map', default=None)
ap.add_argument('--out', default=None)
ap.add_argument('--full', type=int, default=700)
ap.add_argument('--ctx', type=int, default=14)
a = ap.parse_args()

OUT = []


def p(s=''):
    print(s)
    OUT.append(s)


def read_map(path, want=None):
    """guest addr -> {symbol: object}; restricted to the addrs in `want` if given."""
    objs = {}
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'sub_' not in line:
                continue
            obj = line.rsplit(None, 1)[-1]
            for m in TOK.finditer(line):
                ad = int(m.group(2), 16)
                if want is not None and ad not in want:
                    continue
                if m.group(1) == obj:  # the token is the last field: not a symbol line
                    continue
                objs.setdefault(ad, {}).setdefault(m.group(1), obj)
    return objs


def gen_tu(o):
    for name in sorted(o, key=lambda n: not n.startswith('__imp__')):
        m = GEN_OBJ.search(o[name])
        if m:
            return m.group(1)
    return None


def find_body(tu, fn):
    path = os.path.join(a.gendir, tu)
    if not os.path.exists(path):
        return None, None
    with open(path, 'rb') as f:
        data = f.read()
    for key in (b'DEFINE_REX_FUNC(%s)' % fn.encode(), b'PPC_FUNC_IMPL(__imp__%s)' % fn.encode(),
                b'PPC_FUNC(%s)' % fn.encode()):
        k = data.find(key)
        if k < 0:
            continue
        ls = data.rfind(b'\n', 0, k) + 1
        le = data.find(b'\n', k)
        nxt = NEXT_DEF.search(data, le)
        end = nxt.start() if nxt else len(data)
        body = data[ls:end].replace(b'\r\n', b'\n').decode('utf-8', 'replace').splitlines()
        return data.count(b'\n', 0, ls) + 1, body
    return None, None


targets = [int(x, 16) for x in a.addrs]
objs = read_map(a.map)
srt = sorted(objs)
p(f'map {a.map}: {len(srt)} distinct guest function addresses')
funcs = []  # (func addr, [target addrs inside])
for t in targets:
    i = bisect.bisect_right(srt, t) - 1
    lo = srt[i] if i >= 0 else 0
    hi = srt[i + 1] if i + 1 < len(srt) else 0
    o = objs.get(lo, {})
    p(f'{t:08X}: in sub_{lo:08X} (+0x{t - lo:X}); next sub_{hi:08X}; '
      + ', '.join(f'{k}={v}' for k, v in sorted(o.items())))
    if len(funcs) < a.body_n or any(f[0] == lo for f in funcs):
        for f in funcs:
            if f[0] == lo:
                f[1].append(t)
                break
        else:
            if len(funcs) < a.body_n and targets.index(t) < a.body_n:
                funcs.append((lo, [t]))

tus = {fa: gen_tu(objs.get(fa, {})) for fa, _ in funcs}
bodies = {}
missing = []
for fa, _ in funcs:
    fn = f'sub_{fa:08X}'
    ln, body = find_body(tus[fa], fn) if tus[fa] else (None, None)
    if body is None:
        missing.append(fa)
    else:
        bodies[fa] = (tus[fa], ln, body)
if missing and a.tu_map:
    p(f'-- not in the TU named by {os.path.basename(a.map)}: '
      + ', '.join(f'sub_{x:08X} ({tus[x]})' for x in missing) + f'; reading {a.tu_map}')
    o2 = read_map(a.tu_map, want=set(missing))
    for fa in missing:
        tu = gen_tu(o2.get(fa, {}))
        ln, body = find_body(tu, f'sub_{fa:08X}') if tu else (None, None)
        if body is not None:
            bodies[fa] = (tu, ln, body)

for fa, inside in funcs:
    fn = f'sub_{fa:08X}'
    p('')
    if fa not in bodies:
        p(f'== {fn}: definition not found (TU {tus[fa]}) in {a.gendir}')
        continue
    tu, ln, body = bodies[fa]
    marks = {f'{t:08X}' for t in inside} | {f'{t - 4:08X}' for t in inside}
    mark_re = re.compile(r'(?i)\b(?:0x|loc_)?(' + '|'.join(sorted(marks)) + r')\b')
    p(f'== {fn} in {tu}:{ln}, {len(body)} lines; marks ' + ', '.join(sorted(marks)))
    # call sites
    calls = []
    for j, line in enumerate(body):
        m = LR_SET.search(line)
        if m:
            callee = '?'
            for k in range(j + 1, min(j + 4, len(body))):
                c = CALLEE.search(body[k])
                if c:
                    callee = c.group(1)
                    break
            calls.append((m.group(1).upper(), callee))
    p('  call sites (return address -> callee): '
      + (', '.join(f'{r}->{c}' for r, c in calls) if calls else 'none'))
    # labels and backward branches
    labels = {}
    for j, line in enumerate(body):
        m = LABEL.match(line.strip())
        if m:
            labels[m.group(1).upper()] = j
    back = []
    for j, line in enumerate(body):
        m = GOTO.search(line)
        if m and m.group(1).upper() in labels and labels[m.group(1).upper()] < j:
            asm = ''
            for k in range(j - 1, max(j - 4, -1), -1):
                am = ASM.match(body[k])
                if am:
                    asm = am.group(1)
                    break
            back.append(f'L{j + 1} goto loc_{m.group(1).upper()} (label at L{labels[m.group(1).upper()] + 1}; {asm})')
    p('  backward branches: ' + ('; '.join(back) if back else 'none'))
    hit = [j for j, line in enumerate(body) if mark_re.search(line)]
    if len(body) <= a.full:
        show = range(len(body))
    else:
        keep = set()
        for j in hit:
            keep.update(range(max(0, j - a.ctx), min(len(body), j + a.ctx + 1)))
        show = sorted(keep)
    prev = None
    for j in show:
        if prev is not None and j != prev + 1:
            p('   ...')
        tag = '   <<<' if j in hit else ''
        p(f'{j + 1:5d}  {body[j].rstrip()}{tag}')
        prev = j

if a.out:
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(OUT) + '\n')
    print(f'-> {a.out}')
