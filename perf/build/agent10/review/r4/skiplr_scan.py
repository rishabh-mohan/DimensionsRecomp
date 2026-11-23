"""skip_lr exposure scan over an all-off LEGO output (read-only).

Under skip_lr, `mflr rD` in a body that is not an LR user emits nothing, so rD
keeps a stale value. That is harmless when rD only carries the return address
to the stack (stw/std) or back into LR (mtlr). This scan lists every mflr in
the all-off output whose destination is used any other way before it is
overwritten (linear scan, so it over-reports across branches), and marks the
bodies that the new rule keeps LR in (a bclrl, or a bl emitted as a goto).
"""
import collections
import os
import re
import sys

D = sys.argv[1]
OUT = sys.argv[2]

func_re = re.compile(r'^DEFINE_REX_FUNC\((\w+)\)')
mflr_re = re.compile(r'^\tctx\.(r\d+)\.u64 = ctx\.lr;\s*$')
mtlr_re = re.compile(r'^\tctx\.lr = ctx\.(r\d+)\.u64;\s*$')
bclrl_re = re.compile(r'^\t// b[a-z]*lrl[+-]?(\s|$)')
blc_re = re.compile(r'^\t// bl 0x[0-9a-fA-F]+\s*$')
call_re = re.compile(r'^\t(\w+)\(ctx, base\);\s*$')
store_re_t = r'REX_STORE_U(32|64)\((.*), ctx\.{r}\.u(32|64)\);'

funcs = 0
lr_users = set()
mflr_total = 0
dest_hist = collections.Counter()
cls_hist = collections.Counter()
flagged = []
mtlr_then_mflr = []
nonprologue = []


def scan_func(name, fname, start, lines):
    global mflr_total
    has_bclrl = any(bclrl_re.match(l) for l in lines)
    has_local_bl = False
    for i, l in enumerate(lines):
        if blc_re.match(l):
            for k in range(i + 1, min(i + 4, len(lines))):
                if lines[k].startswith('\tgoto '):
                    has_local_bl = True
                    break
                if lines[k].startswith('\t//'):
                    break
    user = has_bclrl or has_local_bl
    if user:
        lr_users.add(name)
    seen_mtlr = None
    ninsn = 0
    for i, l in enumerate(lines):
        if l.startswith('\t// '):
            ninsn += 1
        mt = mtlr_re.match(l)
        if mt:
            seen_mtlr = i
            continue
        if call_re.match(l) or l.startswith('\treturn;'):
            seen_mtlr = None
        m = mflr_re.match(l)
        if not m:
            continue
        r = m.group(1)
        mflr_total += 1
        dest_hist[r] += 1
        if seen_mtlr is not None:
            mtlr_then_mflr.append((name, fname, start + i + 1, user))
        if ninsn > 3:
            nonprologue.append((name, fname, start + i + 1, r, ninsn, user))
        assign_re = re.compile(r'^\tctx\.' + r + r'\.(u64|s64|u32|s32|u16|u8|f64)\s*=')
        use_re = re.compile(r'ctx\.' + r + r'\.')
        store_re = re.compile(store_re_t.format(r=r))
        kinds = []
        uses = []
        for j in range(i + 1, len(lines)):
            lj = lines[j]
            if lj.startswith('\t//'):
                continue
            if assign_re.match(lj):
                break
            cm = call_re.match(lj)
            if cm and r in ('r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10'):
                kinds.append('call-live-arg')
                uses.append(lj.strip())
                continue
            if lj.startswith('\treturn;') and r in ('r3', 'r4'):
                kinds.append('return-live')
                uses.append(lj.strip())
                continue
            if use_re.search(lj):
                if store_re.search(lj):
                    kinds.append('store')
                elif mtlr_re.match(lj):
                    kinds.append('mtlr')
                else:
                    kinds.append('other')
                uses.append(lj.strip())
        key = '+'.join(sorted(set(kinds))) or 'unused'
        cls_hist[(r if r in ('r12', 'r0') else 'other-reg', key)] += 1
        bad = r not in ('r12', 'r0') or any(k not in ('store', 'mtlr') for k in kinds)
        if bad:
            flagged.append((name, fname, start + i + 1, r, key, user, uses[:6]))


for fname in sorted(os.listdir(D)):
    if not fname.endswith('.cpp'):
        continue
    with open(os.path.join(D, fname), 'r', encoding='latin-1') as f:
        cur = None
        start = 0
        buf = []
        for ln, line in enumerate(f):
            line = line.rstrip('\r\n')
            m = func_re.match(line)
            if m:
                if cur:
                    funcs += 1
                    scan_func(cur, fname, start, buf)
                cur = m.group(1)
                start = ln
                buf = [line]
            elif cur is not None:
                buf.append(line)
        if cur:
            funcs += 1
            scan_func(cur, fname, start, buf)

with open(OUT, 'w', encoding='utf-8') as o:
    o.write(f'dir {D}\nfunctions {funcs}\nmflr {mflr_total}\nlr_users {len(lr_users)}\n')
    o.write('dest histogram: ' + ', '.join(f'{k}={v}' for k, v in dest_hist.most_common()) + '\n')
    o.write('classes:\n')
    for (r, k), v in sorted(cls_hist.items(), key=lambda x: -x[1]):
        o.write(f'  {r}\t{k}\t{v}\n')
    o.write(f'mtlr then mflr (no call/return between, linear): {len(mtlr_then_mflr)}\n')
    for t in mtlr_then_mflr[:50]:
        o.write(f'  {t}\n')
    o.write(f'mflr after insn 3: {len(nonprologue)}\n')
    for t in nonprologue[:80]:
        o.write(f'  {t}\n')
    o.write(f'flagged: {len(flagged)} (of which in LR-user bodies: {sum(1 for t in flagged if t[5])})\n')
    for t in flagged:
        o.write(f'  {t[0]} {t[1]}:{t[2]} {t[3]} {t[4]} user={t[5]}\n')
        for u in t[6]:
            o.write(f'      {u}\n')
print(open(OUT, encoding='utf-8').read()[:6000])
