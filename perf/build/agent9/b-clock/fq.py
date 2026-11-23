"""Function query tool over the A generated tree (read-only, 1 thread).

  python fq.py build                 # one scan (~40 s) using s6_clock_scan.Scan; writes s6-funcs.pkl
  python fq.py loc X [X...]          # TU:line of functions (X = sub_XXXXXXXX or hex)
  python fq.py callers X [X...]      # direct static callers (bl / tail b / sub_X( calls)
  python fq.py callees X [X...]
  python fq.py readers G [G...]      # functions with a constant-EA load of G (hex), G may be LO-HI range
  python fq.py writers G [G...]
  python fq.py show X [max_insns]    # asm of X with guest addresses (resynced at loc_ labels)
"""
import os, pickle, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKL = os.path.join(HERE, 's6-funcs.pkl')
sys.path.insert(0, HERE)


def h(s):
    s = s.strip()
    if s.lower().startswith('sub_'):
        s = s[4:]
    return int(s, 16)


def load():
    with open(PKL, 'rb') as f:
        return pickle.load(f)


def build():
    import glob, time
    import s6_clock_scan as s6
    files = sorted(glob.glob(os.path.join(s6.GEN, 'legodimensions_recomp.*.cpp')),
                   key=lambda p: int(os.path.basename(p).split('.')[1]))
    t0 = time.time()
    sc = s6.Scan()
    for p in files:
        sc.scan_file(p)
    d = {a: (r.tu, r.ln, r.callees, r.loads, r.stores, r.mftb, r.imps, r.fcmp, r.fadd)
         for a, r in sc.funcs.items()}
    with open(PKL, 'wb') as f:
        pickle.dump(d, f, protocol=pickle.HIGHEST_PROTOCOL)
    print('built %d functions from %d files in %.1f s -> %s' % (len(d), len(files), time.time() - t0, PKL))


def loc(d, a):
    r = d.get(a)
    return 'TU%s:%d' % (r[0], r[1]) if r else '(none)'


def show(d, a, maxn):
    import s6_clock_scan as s6
    r = d.get(a)
    if not r:
        print('sub_%08X not found' % a)
        return
    path = os.path.join(s6.GEN, 'legodimensions_recomp.%s.cpp' % r[0])
    print('== sub_%08X TU%s:%d' % (a, r[0], r[1]))
    pc = a
    n = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if i < r[1]:
                continue
            if i > r[1] and line.startswith('}'):
                break
            if line.startswith('loc_'):
                s = line.strip().rstrip(':')
                try:
                    t = int(s[4:], 16)
                    if t != pc:
                        print('   (resync %08X -> %08X)' % (pc, t))
                    pc = t
                except ValueError:
                    pass
                print(' %s:' % s)
            elif line.startswith('\t// '):
                body = line[4:].rstrip()
                print('  %08X  %s' % (pc, body))
                pc += 4
                n += 1
                if n >= maxn:
                    print('  ... (truncated at %d insns)' % maxn)
                    break


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'build':
        build()
        return
    d = load()
    if cmd == 'loc':
        for x in args:
            a = h(x)
            print('sub_%08X %s' % (a, loc(d, a)))
    elif cmd in ('callers', 'callees'):
        if cmd == 'callers':
            rev = {}
            for k, r in d.items():
                for c in r[2]:
                    rev.setdefault(c, []).append(k)
        for x in args:
            a = h(x)
            lst = sorted(rev.get(a, [])) if cmd == 'callers' else list(d.get(a, (0, 0, ()))[2])
            print('%s of sub_%08X (%d):' % (cmd, a, len(lst)))
            for c in lst:
                print('   sub_%08X %s' % (c, loc(d, c)))
    elif cmd in ('readers', 'writers'):
        idx = 3 if cmd == 'readers' else 4
        for x in args:
            if '-' in x:
                lo, hi = (int(p, 16) for p in x.split('-'))
            else:
                lo = hi = int(x, 16)
            hits = sorted((k, sorted(e for e in r[idx] if lo <= e <= hi)) for k, r in d.items()
                          if any(lo <= e <= hi for e in r[idx]))
            print('%s of %s (%d):' % (cmd, x, len(hits)))
            for k, es in hits:
                print('   sub_%08X %s  %s' % (k, loc(d, k), ' '.join('0x%08X' % e for e in es)))
    elif cmd == 'show':
        maxn = int(args[1]) if len(args) > 1 else 400
        show(d, h(args[0]), maxn)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
