# cmp-snap1.py (M2): read-only. Compare snap1's copy of DimensionsRecomp (+ rexglue-sdk) against the live working
# trees, file by file over `git ls-files` (thirdparty/ skipped), to show whether the trees the final/s33 bins were
# built from equal the live commits. Writes nothing; prints a summary.
import hashlib, os, subprocess, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
LIVE = os.path.join(R, 'DimensionsRecomp')
SNAP = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp')


def h(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16].upper()


def files(repo):
    out = subprocess.run(['git', '-C', repo, 'ls-files', '-z'], capture_output=True, check=True).stdout
    return [x.decode('utf-8') for x in out.split(b'\0') if x]


for name, live, snap in (('superproject', LIVE, SNAP),
                         ('rexglue-sdk', os.path.join(LIVE, 'rexglue-sdk'), os.path.join(SNAP, 'rexglue-sdk'))):
    same = diff = missing = skipped = 0
    diffs, miss = [], []
    for rel in files(live):
        if rel.startswith('thirdparty/') or rel == 'rexglue-sdk':
            skipped += 1
            continue
        lp, sp = os.path.join(live, rel), os.path.join(snap, rel)
        if not os.path.isfile(lp):
            skipped += 1  # gitlink / submodule dir
            continue
        if not os.path.isfile(sp):
            missing += 1
            miss.append(rel)
            continue
        if h(lp) == h(sp):
            same += 1
        else:
            diff += 1
            diffs.append(rel)
    print('%s: %d same, %d differ, %d missing in snap1, %d skipped (thirdparty/gitlink)' % (name, same, diff, missing, skipped))
    for d in diffs[:40]:
        print('  DIFF', d)
    for m in miss[:20]:
        print('  MISSING', m)
    if len(miss) > 20:
        print('  ... %d more missing' % (len(miss) - 20))
