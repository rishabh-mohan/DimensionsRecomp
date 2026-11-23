"""nativelines.py (Agent 10, task #17 item 1b): the native-only log lines of a native3d (base) / nativeB (cand)
route pair, for the nativeB gate. Read-only; one thread; writes only the --out report.

  python nativelines.py --base RUNDIR --cand RUNDIR [--out report.txt]

Logs per run: game.2.log, game.1.log, game.log (oldest first). Items (agent10-codegen-review.md, "B native game
gate: proposal", fail list and must-match list):
  slot registered   "Native slot heap: registered slot=.. heap=.. initial_bytes=.."   compare initial_bytes multiset
  slot extended     "Native slot heap: extended heap=.. slot=.. owned_regions=.."     LR-gated Grow (0x82A33FC4)
  placement         "Native GPU: placement buffer relocation type .. type=.. lr=.."  LR-gated (0x83F9B660), (type, lr)
  pool copy         "Native GPU: CPU pool copy .. bytes=.. lr=.. caller=.. VS=.."      (lr, caller, VS) multiset; bytes
  cel / bloom       "Native cel observer active" / "Native cel selection" / "Native bloom binding" (diagnostics only)
  memexport warn    "Native GPU: captured memexport begin" (first 8 only)
  hash=0x0          "Native GPU shader cache miss: hash=0x0"
Verdict per item: MATCH (equal, non-zero), DIFF, NOT COVERED (zero in both runs).
Fail lines (must be 0 in cand): not in any registered module, pool copy unsupported, POINTLIST contract mismatch,
external detach verification failed, byte verification failed, ordered pool copy skipped / unsupported GPU
dependency, slot heap retained owned regions. Unimplemented-instruction lines: cand must not exceed base.
Exit 0 when no item is DIFF and no fail line is in cand, else 1. Crashes, hangs and general warning types are
logdiff.py's job (build/agent10/bgate/logdiff.py).
"""
import argparse
import collections
import os
import re
import sys

REG = re.compile(r'Native slot heap: registered slot=([0-9A-Fa-f]+) heap=([0-9A-Fa-f]+) initial_bytes=(\d+)')
EXT = re.compile(r'Native slot heap: extended heap=([0-9A-Fa-f]+) slot=([0-9A-Fa-f]+) owned_regions=(\d+)')
PLACE = re.compile(r'placement buffer relocation type resource=([0-9A-Fa-f]+) type=(\S+) lr=([0-9A-Fa-f]+)')
POOL = re.compile(r'CPU pool copy dst=([0-9A-Fa-f]+) src=([0-9A-Fa-f]+) bytes=(\d+) physical=\S+ '
                  r'lr=([0-9A-Fa-f]+) caller=([0-9A-Fa-f]+) VS=([0-9A-Fa-f]+) verify=(\w+)')
CEL = ('Native cel observer active', 'Native cel selection', 'Native bloom binding')
MEMEXP = 'Native GPU: captured memexport begin'
HASH0 = 'Native GPU shader cache miss: hash=0x0'
FAILS = ('not in any registered module', 'Native GPU: pool copy unsupported', 'pool copy POINTLIST contract mismatch',
         'Native slot heap: external detach verification failed', 'pool copy byte verification failed',
         'ordered pool copy skipped', 'ordered pool copy unsupported GPU dependency', 'Native slot heap: retained')
UNIMPL = re.compile(r'unimplemented', re.I)
INFO = re.compile(r'Native GPU: threaded recording \w+|Native draw batches: [^\r\n]*')


def logs(run):
    return [os.path.join(run, n) for n in ('game.2.log', 'game.1.log', 'game.log')
            if os.path.isfile(os.path.join(run, n))]


def scan(run):
    r = {'files': [], 'reg': [], 'ext': [], 'place': collections.Counter(), 'pool': [], 'cel': collections.Counter(),
         'memexp': 0, 'hash0': 0, 'fails': collections.Counter(), 'unimpl': 0, 'info': collections.Counter(),
         'lines': 0}
    for p in logs(run):
        r['files'].append(f'{os.path.basename(p)} {os.path.getsize(p):,} B')
        with open(p, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                r['lines'] += 1
                if 'Native' not in line and 'registered module' not in line and 'nimplemented' not in line:
                    continue
                if HASH0 in line:
                    r['hash0'] += 1
                    continue
                m = POOL.search(line)
                if m:
                    r['pool'].append((m.group(4).upper(), m.group(5).upper(), m.group(6).upper(), int(m.group(3))))
                    continue
                m = REG.search(line)
                if m:
                    r['reg'].append((m.group(1).upper(), m.group(2).upper(), int(m.group(3))))
                m = EXT.search(line)
                if m:
                    r['ext'].append((m.group(1).upper(), m.group(2).upper(), int(m.group(3))))
                m = PLACE.search(line)
                if m:
                    r['place'][(m.group(2), m.group(3).upper())] += 1
                for c in CEL:
                    if c in line:
                        r['cel'][c] += 1
                if MEMEXP in line:
                    r['memexp'] += 1
                for f in FAILS:
                    if f in line:
                        r['fails'][f] += 1
                if UNIMPL.search(line):
                    r['unimpl'] += 1
                m = INFO.search(line)
                if m:
                    r['info'][m.group(0).strip()] += 1
    return r


def verdict(a, b):
    if not a and not b:
        return 'NOT COVERED'
    return 'MATCH' if a == b else 'DIFF'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--out')
    o = ap.parse_args()
    A, B = scan(o.base), scan(o.cand)
    W = []
    w = W.append
    w(f'base {o.base}: {", ".join(A["files"]) or "no game.log"}; {A["lines"]:,} lines')
    w(f'cand {o.cand}: {", ".join(B["files"]) or "no game.log"}; {B["lines"]:,} lines')
    w('')
    bad = False
    rows = []

    def row(name, ka, kb, sa, sb, note=''):
        nonlocal bad
        v = verdict(ka, kb)
        bad |= v == 'DIFF'
        rows.append((name, sa, sb, v, note))

    ra = sorted(x[2] for x in A['reg'])
    rb = sorted(x[2] for x in B['reg'])
    row('slot heap registered', ra, rb, f'{len(A["reg"])} bytes={ra}', f'{len(B["reg"])} bytes={rb}',
        'addresses: base ' + ','.join(f'{s}/{h}' for s, h, _ in A['reg'][:4])
        + ' cand ' + ','.join(f'{s}/{h}' for s, h, _ in B['reg'][:4]))
    ea, eb = len(A['ext']), len(B['ext'])
    row('slot heap extended (Grow, lr 82A33FC4)', ea, eb, str(ea), str(eb),
        'owned_regions max base %s cand %s' % (max((x[2] for x in A['ext']), default='-'),
                                               max((x[2] for x in B['ext']), default='-')))
    row('placement relocation (lr 83F9B660)', dict(A['place']), dict(B['place']),
        f'{sum(A["place"].values())} {dict(A["place"])}', f'{sum(B["place"].values())} {dict(B["place"])}')
    pa = collections.Counter((lr, c, vs) for lr, c, vs, _ in A['pool'])
    pb = collections.Counter((lr, c, vs) for lr, c, vs, _ in B['pool'])
    row('pool copy (lr, caller, VS)', dict(pa), dict(pb),
        f'{len(A["pool"])} ' + '; '.join(f'lr={k[0]} caller={k[1]} VS={k[2][:8]}..x{v}' for k, v in sorted(pa.items())),
        f'{len(B["pool"])} ' + '; '.join(f'lr={k[0]} caller={k[1]} VS={k[2][:8]}..x{v}' for k, v in sorted(pb.items())))
    ba = [x[3] for x in A['pool']]
    bb = [x[3] for x in B['pool']]
    row('pool copy bytes (in order)', ba, bb, str(ba[:12]), str(bb[:12]),
        'same multiset' if sorted(ba) == sorted(bb) and ba != bb else '')
    row('cel/bloom diagnostics', dict(A['cel']), dict(B['cel']), str(dict(A['cel'])), str(dict(B['cel'])),
        'logged only with native effects diagnostics on (off by default)')
    row('memexport begin warnings', A['memexp'], B['memexp'], str(A['memexp']), str(B['memexp']))
    w(f'{"item":42} {"verdict":12} base | cand')
    for name, sa, sb, v, note in rows:
        w(f'{name:42} {v:12} {sa} | {sb}' + (f'   [{note}]' if note else ''))
    w('')
    w(f'hash=0x0 cache-miss lines: base {A["hash0"]:,}, cand {B["hash0"]:,} '
      f'({"same" if A["hash0"] == B["hash0"] else "differ; timing-dependent, informational"})')
    w('info lines: base ' + '; '.join(f'{k} x{v}' for k, v in sorted(A['info'].items()))
      + ' | cand ' + '; '.join(f'{k} x{v}' for k, v in sorted(B['info'].items())))
    w('')
    w('Fail lines (cand must be 0):')
    for f in FAILS:
        fa, fb = A['fails'][f], B['fails'][f]
        bad |= fb > 0
        w(f'  {f:55} base {fa}, cand {fb}  {"FAIL" if fb else "ok"}')
    ub = B['unimpl'] > A['unimpl']
    bad |= ub
    w(f'  {"unimplemented-instruction lines":55} base {A["unimpl"]}, cand {B["unimpl"]}  {"FAIL" if ub else "ok"}')
    w('')
    covered = [n for n, _, _, v, _ in rows if v == 'MATCH']
    missing = [n for n, _, _, v, _ in rows if v == 'NOT COVERED']
    w('covered: ' + (', '.join(covered) or 'none'))
    w('not covered: ' + (', '.join(missing) or 'none'))
    w(f'RESULT {"DIFF/FAIL" if bad else "PASS"}')
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
