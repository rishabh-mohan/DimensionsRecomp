# addr_scan.py -- Agent 9 (run 2, task #11 = #41 step 1, 13:40). Read-only, 1 thread, A tree.
# Per function: constant tracking as arm_scan.py (lis / addi / addis / ori / mr), but it reports
#   form  - a register gets a value inside a window (address formation, e.g. a struct base);
#   ld/st - a d-form load/store whose EA is inside a window;
#   x     - an indexed (x-form) load/store whose base or index register holds a window value;
#   arg   - a bl with r3-r10 holding a window value (pointer passed to a callee).
# Only functions whose text has a matching lis immediate are tracked (fast prefilter).
# usage: python addr_scan.py <generated-root> LO-HI[,LO-HI...] <out.txt>
import os, re, sys, time

root, out = sys.argv[1], sys.argv[3]
wins = [tuple(int(x, 16) for x in w.split('-')) for w in sys.argv[2].split(',')]
his = set()
for lo, hi in wins:
    for v in range(lo >> 16, (hi >> 16) + 2):
        his.update((str(v - 65536 if v >= 0x8000 else v), str(v), '0x%X' % v, '0x%x' % v))
re_lis = re.compile(r'lis r\d+, ?(?:%s)\b' % '|'.join(re.escape(s) for s in sorted(his)))
re_func = re.compile(r'^DEFINE_REX_FUNC\((?:__imp__)?(sub_[0-9A-Fa-f]{8})\)')
re_asm = re.compile(r'^\t// ([a-z.]+) ?(.*)$')
re_mem = re.compile(r'^(r\d+),(-?(?:0x[0-9a-fA-F]+|\d+))\((r\d+)\)$')
VOL = ['r0'] + ['r%d' % i for i in range(3, 13)]


def ival(s):
    return int(s, 16) if s.lower().startswith(('0x', '-0x')) else int(s)


def inwin(v):
    return v is not None and any(lo <= v <= hi for lo, hi in wins)


t0 = time.time()
hits, nf, nfun = [], 0, 0
for fn in sorted(os.listdir(root), key=lambda n: (len(n), n)):
    if not fn.endswith('.cpp'):
        continue
    nf += 1
    with open(os.path.join(root, fn), encoding='utf-8', errors='replace') as f:
        data = f.read()
    if not re_lis.search(data):
        continue
    tu = fn.split('.')[1] if fn.count('.') >= 2 else fn
    base_ln = 1
    for chunk in data.split('\nDEFINE_REX_FUNC('):
        start_ln = base_ln
        base_ln += chunk.count('\n') + 1
        if not re_lis.search(chunk):
            continue
        nfun += 1
        lines = chunk.split('\n')
        m = re.match(r'(?:__imp__)?(sub_[0-9A-Fa-f]{8})\)', lines[0])
        func = m.group(1) if m else lines[0][:24]
        val = {}
        for i, line in enumerate(lines):
            m = re_asm.match(line)
            if not m:
                continue
            ln = start_ln + i
            op, args = m.group(1).rstrip('.+-'), m.group(2).replace(' ', '')
            a = args.split(',') if args else []
            try:
                if op == 'lis' and len(a) == 2:
                    val[a[0]] = (ival(a[1]) << 16) & 0xFFFFFFFF
                    if inwin(val[a[0]]):
                        hits.append((func, tu, ln, 'form', op, args, val[a[0]]))
                    continue
                if op in ('addi', 'addis', 'subi') and len(a) == 3 and a[1] in val:
                    k = ival(a[2]) << (16 if op == 'addis' else 0)
                    val[a[0]] = (val[a[1]] + (-k if op == 'subi' else k)) & 0xFFFFFFFF
                    if inwin(val[a[0]]):
                        hits.append((func, tu, ln, 'form', op, args, val[a[0]]))
                    continue
                if op == 'ori' and len(a) == 3 and a[1] in val:
                    val[a[0]] = val[a[1]] | (ival(a[2]) & 0xFFFF)
                    if inwin(val[a[0]]):
                        hits.append((func, tu, ln, 'form', op, args, val[a[0]]))
                    continue
                if op == 'mr' and len(a) == 2:
                    if a[1] in val:
                        val[a[0]] = val[a[1]]
                        if inwin(val[a[0]]):
                            hits.append((func, tu, ln, 'form', op, args, val[a[0]]))
                    else:
                        val.pop(a[0], None)
                    continue
            except ValueError:
                val.pop(a[0], None) if a else None
                continue
            if op in ('bl', 'bctrl', 'blrl'):
                for r in ('r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10'):
                    if inwin(val.get(r)):
                        hits.append((func, tu, ln, 'arg', op, args + ' ' + r, val[r]))
                for r in VOL:
                    val.pop(r, None)
                continue
            if (op.startswith(('st', 'l')) and len(a) == 2 and '(' in a[1]):
                mm = re_mem.match(args)
                if mm:
                    rb = mm.group(3)
                    b0 = 0 if rb == 'r0' else val.get(rb)
                    ea = None if b0 is None else (b0 + ival(mm.group(2))) & 0xFFFFFFFF
                    if inwin(ea):
                        hits.append((func, tu, ln, 'st' if op.startswith('st') else 'ld', op, args, ea))
                    if op.endswith('u') and rb != 'r0':
                        if ea is None:
                            val.pop(rb, None)
                        else:
                            val[rb] = ea
                    if op.startswith('l'):
                        val.pop(a[0], None)
                    continue
            if op.startswith(('st', 'l')) and op.endswith(('x', 'xu', 'ux')) and len(a) == 3:
                bA = 0 if a[1] == 'r0' else val.get(a[1])
                bB = val.get(a[2])
                if inwin(bA) or inwin(bB):
                    hits.append((func, tu, ln, 'x', op, args,
                                 bA if inwin(bA) else bB))
                if op.startswith('l'):
                    val.pop(a[0], None)
                continue
            if op.startswith(('st', 'cmp', 'b', 'tw', 'dcb', 'mt', 'sync', 'isync', 'lwsync', 'eieio', 'c')):
                continue
            if a:
                val.pop(a[0], None)

with open(out, 'w', newline='\n') as f:
    f.write('# addr_scan.py %s windows %s; %d files, %d functions tracked, %.1f s\n'
            % (root, ','.join('%08X-%08X' % w for w in wins), nf, nfun, time.time() - t0))
    f.write('# kinds: form (register := window value), st/ld (d-form EA in window), x (indexed, base/idx in window), arg (bl with rN in window)\n')
    for func, tu, ln, kind, op, args, v in hits:
        f.write('%s TU%s:%d  %-4s %s %s  -> 0x%08X\n' % (func, tu, ln, kind, op, args, v))
print('hits %d, files %d, functions %d, %.1f s -> %s' % (len(hits), nf, nfun, time.time() - t0, out))
