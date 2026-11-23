"""Follow-up to skiplr_scan.py (read-only).

1. off3: for each mflr r12 whose value has no textual use before it is
   overwritten, name the first call after it (expected: __savegprlr_N /
   __savefpr_N, which store r12 at -8(r1)). For stored values, the base
   register of the store (expected: r1).
2. batch (skip_lr on): every function body that still mentions ctx.lr.
"""
import collections
import os
import re
import sys

OFF = sys.argv[1]
BATCH = sys.argv[2]
OUT = sys.argv[3]

func_re = re.compile(r'^DEFINE_REX_FUNC\((\w+)\)')
mflr12 = re.compile(r'^\tctx\.r12\.u64 = ctx\.lr;\s*$')
assign12 = re.compile(r'^\tctx\.r12\.(u64|s64|u32|s32|u16|u8|f64)\s*=')
use12 = re.compile(r'ctx\.r12\.')
store12 = re.compile(r'REX_STORE_U(?:32|64)\(ctx\.(r\d+)\.u32 \+ (-?\d+), ctx\.r12\.u(?:32|64)\);')
call_re = re.compile(r'^\t(\w+)\(ctx, base\);\s*$')

first_call = collections.Counter()
store_base = collections.Counter()
store_off = collections.Counter()


def norm(name):
    return re.sub(r'\d+$', 'N', name) if name.startswith('__') else re.sub(r'_[0-9A-F]+$', '_X', name)


def scan_off(lines):
    for i, l in enumerate(lines):
        if not mflr12.match(l):
            continue
        used = False
        call = None
        for j in range(i + 1, len(lines)):
            lj = lines[j]
            if lj.startswith('\t//'):
                continue
            if assign12.match(lj):
                break
            m = store12.search(lj)
            if m:
                used = True
                store_base[m.group(1)] += 1
                store_off[m.group(2)] += 1
                break
            if use12.search(lj):
                used = True
                break
            cm = call_re.match(lj)
            if cm and call is None:
                call = cm.group(1)
                break
            if lj.startswith('\treturn;'):
                break
        if not used:
            first_call[norm(call) if call else '(none: return/overwrite)'] += 1


def walk(d, fn):
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.cpp'):
            continue
        with open(os.path.join(d, fname), 'r', encoding='latin-1') as f:
            cur = None
            buf = []
            start = 0
            for ln, line in enumerate(f):
                line = line.rstrip('\r\n')
                m = func_re.match(line)
                if m:
                    if cur:
                        fn(cur, fname, start, buf)
                    cur, start, buf = m.group(1), ln + 1, [line]
                elif cur is not None:
                    buf.append(line)
            if cur:
                fn(cur, fname, start, buf)


walk(OFF, lambda n, f, s, b: scan_off(b))

lr_funcs = []
lr_outside = collections.Counter()


def scan_batch(name, fname, start, lines):
    hits = [l.strip() for l in lines if 'ctx.lr' in l]
    if hits:
        lr_funcs.append((name, fname, start, len(hits), hits[:12]))


walk(BATCH, scan_batch)
for fname in sorted(os.listdir(BATCH)):
    p = os.path.join(BATCH, fname)
    if os.path.isfile(p) and not fname.endswith('.cpp') and fname.endswith(('.h', '.inl', '.hpp')):
        with open(p, 'r', encoding='latin-1') as f:
            c = sum(1 for l in f if 'ctx.lr' in l or ' lr' in l and 'skip_lr' in l)
            if c:
                lr_outside[fname] = c

with open(OUT, 'w', encoding='utf-8') as o:
    o.write('off3: mflr r12 with no textual use -> first call after it:\n')
    for k, v in first_call.most_common():
        o.write(f'  {k}\t{v}\n')
    o.write('off3: mflr r12 stored -> base register: ' + ', '.join(f'{k}={v}' for k, v in store_base.most_common()) + '\n')
    o.write('off3: mflr r12 stored -> offset (top 8): ' + ', '.join(f'{k}={v}' for k, v in store_off.most_common(8)) + '\n')
    o.write(f'batch: functions mentioning ctx.lr: {len(lr_funcs)}\n')
    for t in lr_funcs[:20]:
        o.write(f'  {t[0]} {t[1]}:{t[2]} hits={t[3]}\n')
        for h in t[4]:
            o.write(f'      {h}\n')
    o.write('batch: headers mentioning lr: ' + ', '.join(f'{k}={v}' for k, v in lr_outside.items()) + '\n')
print(open(OUT, encoding='utf-8').read())
