#!/usr/bin/env python3
# stage-variant.py (Agent 2, board run 2 task #1): stage a variant bin = a staged base bin with some files replaced.
#
#   python build/agent2/stage-variant.py --base build/agent2/devoff4b-bin --out build/agent2/devoff4b-ctr-bin
#          --replace rexgpu-xenos.dll=build/agent2/ctr/link-on/rexgpu-xenos.dll [--replace NAME=FILE ...]
#          --title "one line" [--note "line" ...] [--dry-run]
#
# Copies every file of --base except MANIFEST.txt (a replaced NAME comes from FILE instead), sets each copy's mtime
# to now (Agent 4's 14:41 finding), checks every copy against its source by sha256, and writes MANIFEST.txt in the
# stage-snap-bin row format (name TAB size TAB mtime TAB sha256 TAB source) with the provenance as # lines.
# Refuses an existing --out, a NAME that is not in --base, and runs while perf-notes/WINDOW-HOLD.txt exists.
import argparse, hashlib, os, shutil, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def rel(p):
    return os.path.relpath(os.path.abspath(p), R)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--replace', action='append', default=[])
    ap.add_argument('--title', required=True)
    ap.add_argument('--note', action='append', default=[])
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    base, out = os.path.abspath(a.base), os.path.abspath(a.out)
    if os.path.exists(out):
        print('FAIL: %s exists' % rel(out))
        return 2
    bm = os.path.join(base, 'MANIFEST.txt')
    rows = {}
    with open(bm, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('#') or '\t' not in line:
                continue
            c = line.rstrip('\r\n').split('\t')
            if len(c) >= 5:
                rows[c[0]] = c
    files = sorted(os.path.relpath(os.path.join(dp, fn), base) for dp, _, fns in os.walk(base) for fn in fns
                   if not (dp == base and fn == 'MANIFEST.txt'))
    rep = {}
    for r_ in a.replace:
        n, _, src = r_.partition('=')
        if n not in files:
            print('FAIL: %s is not a file of %s' % (n, rel(base)))
            return 2
        if not os.path.isfile(src):
            print('FAIL: replacement %s does not exist' % src)
            return 2
        rep[n] = os.path.abspath(src)
    # the base must still match its own MANIFEST
    for n in files:
        if n not in rows:
            print('FAIL: %s/%s is not in its MANIFEST' % (rel(base), n))
            return 2
        if sha(os.path.join(base, n)) != rows[n][3]:
            print('FAIL: %s/%s does not match its MANIFEST row' % (rel(base), n))
            return 2
    print('base %s: %d files match its MANIFEST (sha256 %s)' % (rel(base), len(files), sha(bm)))
    plan = [(n, rep.get(n, os.path.join(base, n))) for n in files]
    for n, src in plan:
        print('  %s <- %s%s' % (n, rel(src), '  (REPLACED)' if n in rep else ''))
    if a.dry_run:
        print('dry run: nothing staged')
        return 0
    t0 = time.time()
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    lines, checks = [], []
    for n, src in plan:
        dst = os.path.join(tmp, n)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        now = time.time()
        os.utime(dst, (now, now))
        hs, hd = sha(src), sha(dst)
        if hs != hd:
            print('FAIL: copy of %s differs from %s' % (n, rel(src)))
            return 3
        srcdesc = (rel(src) if n in rep else rows[n][4])
        lines.append('%s\t%d\t%s\t%s\t%s' % (n, os.path.getsize(dst), time.strftime('%Y-%m-%d %H:%M:%S',
                                                                                  time.localtime(now)), hd, srcdesc))
        checks.append('#   PASS staged copy identical: %s%s' % (n, ' (replaced: base %s -> %s)' % (
            rows[n][3][:16], hd[:16]) if n in rep else ''))
    hdr = ['# %s - Agent 2 (board run 2 task #1). %s' % (rel(out), a.title),
           '# staged %s from %s (MANIFEST sha256 %s); every file copied with mtime = now; replaced: %s.' % (
               time.strftime('%Y-%m-%d %H:%M:%S'), rel(base), sha(bm),
               ', '.join('%s <- %s' % (n, rel(s)) for n, s in sorted(rep.items())) or 'none')]
    hdr += ['# ' + x for x in a.note]
    hdr.append('# files: name, size, mtime, sha256, source')
    with open(os.path.join(tmp, 'MANIFEST.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(hdr + lines + ['# checks:'] + checks) + '\n')
    os.replace(tmp, out)
    mf = os.path.join(out, 'MANIFEST.txt')
    print('\n'.join(lines))
    print('staged %s in %.1f s; MANIFEST.txt sha256 %s' % (rel(out), time.time() - t0, sha(mf)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
