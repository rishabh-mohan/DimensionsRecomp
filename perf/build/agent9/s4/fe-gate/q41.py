# q41.py -- Agent 9 (run 2, task #11 = #41 step 1, 13:40). Read-only, 1 thread, A tree; uses fq.py's pickle.
# usage: python q41.py summary|show
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'b-clock')))
import fq  # noqa: E402

d = fq.load()
rev = {}
for k, r in d.items():
    for c in r[2]:
        rev.setdefault(c, []).append(k)


def callers(a):
    lst = sorted(rev.get(a, []))
    print('callers of sub_%08X %s (%d):' % (a, fq.loc(d, a), len(lst)))
    for c in lst:
        print('   sub_%08X %s' % (c, fq.loc(d, c)))


def acc(kind, lo, hi):
    idx = 3 if kind == 'readers' else 4
    hits = sorted((k, sorted(e for e in r[idx] if lo <= e <= hi)) for k, r in d.items()
                  if any(lo <= e <= hi for e in r[idx]))
    print('%s of %08X-%08X (%d):' % (kind, lo, hi, len(hits)))
    for k, es in hits:
        print('   sub_%08X %s  %s' % (k, fq.loc(d, k), ' '.join('0x%08X' % e for e in es)))


mode = sys.argv[1] if len(sys.argv) > 1 else 'summary'
if mode == 'summary':
    print('# A tree; fq.py pickle; %d functions' % len(d))
    for lo, hi in ((0x849004E8, 0x849004EF), (0x848E2EA0, 0x848E2EA3), (0x848E2E80, 0x848E2EBF)):
        acc('writers', lo, hi)
        acc('readers', lo, hi)
    for a in (0x82A83570, 0x82A832F8, 0x829D4390, 0x82A7EC08, 0x82A75FD8, 0x82A7EAA0):
        callers(a)
else:
    for x in sys.argv[2:]:
        a, _, n = x.partition(':')
        fq.show(d, fq.h(a), int(n) if n else 400)
