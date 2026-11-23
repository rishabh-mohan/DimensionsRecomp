#!/usr/bin/env python3
# rehash-w5.py (Agent 2, board run 2 task #1): re-hash W5's inputs and compare with Agent 1's list, and check that
# devoff3-bin and devoff4-bin are unchanged (every file against its own MANIFEST.txt row, and no extra files).
#
#   python build/agent2/s4b/rehash-w5.py [--list build/agent1/w5/W5-INPUTS-1731.txt] --out REPORT
#
# List rows: SHA256 SIZE PATH (PATH relative to the workspace). MANIFEST rows: name TAB size TAB mtime TAB sha256 TAB
# source. Read-only, one thread (run it at Below Normal). Exit 0 = everything unchanged.
import argparse, hashlib, os, re, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
BINS = ['build/agent2/devoff3-bin', 'build/agent2/devoff4-bin']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', default=os.path.join(R, 'build', 'agent1', 'w5', 'W5-INPUTS-1731.txt'))
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    out, bad = [], 0
    say = out.append
    say('# rehash-w5 (Agent 2, run 2 task #1)  %s  list %s (sha256 %s)' % (
        time.strftime('%Y-%m-%d %H:%M:%S'), os.path.relpath(a.list, R), sha(a.list)[:16]))
    n = 0
    with open(a.list, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'^([0-9A-F]{64})\s+(\d+)\s+(.+?)\s*$', line.strip())
            if not m:
                continue
            n += 1
            want, size, rel = m.group(1), int(m.group(2)), m.group(3)
            p = os.path.join(R, rel)
            if not os.path.isfile(p):
                say('MISSING %s' % rel)
                bad += 1
                continue
            got, gs = sha(p), os.path.getsize(p)
            ok = got == want and gs == size
            bad += 0 if ok else 1
            say('%s %s %d %s%s' % ('OK  ' if ok else 'DIFF', got[:16], gs, rel,
                                    '' if ok else '  (list: %s %d)' % (want[:16], size)))
    say('W5 list: %d row(s), %d changed or missing' % (n, bad))
    for b in BINS:
        bd = os.path.join(R, b)
        mf = os.path.join(bd, 'MANIFEST.txt')
        rows = {}
        with open(mf, encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('#') or '\t' not in line:
                    continue
                c = line.rstrip('\r\n').split('\t')
                if len(c) >= 4 and re.match(r'^[0-9A-F]{64}$', c[3]):
                    rows[c[0]] = (int(c[1]), c[3])
        files = sorted(os.path.relpath(os.path.join(dp, fn), bd) for dp, _, fns in os.walk(bd) for fn in fns)
        bb = 0
        for rel in files:
            if rel == 'MANIFEST.txt':
                continue
            p = os.path.join(bd, rel)
            if rel not in rows:
                say('  EXTRA %s/%s (not in its MANIFEST)' % (b, rel))
                bb += 1
                continue
            got = sha(p)
            if (os.path.getsize(p), got) != rows[rel]:
                say('  DIFF %s/%s %s (MANIFEST %s)' % (b, rel, got[:16], rows[rel][1][:16]))
                bb += 1
        for rel in sorted(set(rows) - set(files)):
            say('  MISSING %s/%s' % (b, rel))
            bb += 1
        say('%s: %d MANIFEST row(s), %d file(s) + MANIFEST.txt (sha256 %s): %s' % (
            b, len(rows), len(files) - 1, sha(mf)[:16], 'unchanged' if not bb else '%d problem(s)' % bb))
        bad += bb
    say('RESULT: %s  (%.1f s)' % ('PASS (W5 inputs and devoff3-bin/devoff4-bin unchanged)' if not bad else
                                 'FAIL (%d)' % bad, time.time() - t0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
