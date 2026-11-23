"""Agent 10 (task #9, session 3): READ-ONLY scan of the live DimensionsRecomp tree against build/agent2/snap1/STATE-S2-2315.tsv.
Compares each live file with the snap1 sha256 (STATE-S2 column 7), using snap.py's walk rules (top-level files plus
rexglue-sdk, rexlego, thirdparty, tools; minus rexglue-sdk/out, rexlego/out, rexlego/generated and .git/__pycache__ dirs).
It never writes anywhere except stdout.

Usage: python build\\agent10\\s3\\scan-vs-s2.py [--full] > build\\agent10\\s3\\scan-vs-s2-<HHMM>.txt
  default: a file whose size and mtime_ns equal STATE-S2's live columns, and whose STATE-S2 live sha256 equals the
           snap1 sha256, counts as unchanged without hashing; every other file is hashed.
  --full:  hash every live file.
"""
import hashlib
import os
import sys
import time

R = r'<workspace>'
LIVE = os.path.join(R, 'DimensionsRecomp')
STATE = os.path.join(R, 'build', 'agent2', 'snap1', 'STATE-S2-2315.tsv')
TOP_DIRS = ['rexglue-sdk', 'rexlego', 'thirdparty', 'tools']
EXCL_REL = {'rexglue-sdk/out', 'rexlego/out', 'rexlego/generated'}
EXCL_NAMES = {'.git', '__pycache__'}
REPARSE = 0x400
LP = '\\\\?\\'


def lp(rel):
    return LP + os.path.join(LIVE, rel.replace('/', os.sep))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def num(x):
    try:
        return int(x)
    except ValueError:
        return None


def ts(ns):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ns / 1e9)) if ns else '-'


def walk():
    files, skipped = {}, []
    for e in os.scandir(LIVE):
        if e.is_file(follow_symlinks=False) and e.name not in EXCL_NAMES:
            st = e.stat(follow_symlinks=False)
            files[e.name] = (st.st_size, st.st_mtime_ns)
    for top in TOP_DIRS:
        stack = [top]
        while stack:
            rel = stack.pop()
            with os.scandir(lp(rel)) as it:
                for e in it:
                    r = rel + '/' + e.name
                    if r in EXCL_REL:
                        continue
                    if e.name in EXCL_NAMES and e.is_dir(follow_symlinks=False):
                        continue
                    st = e.stat(follow_symlinks=False)
                    if getattr(st, 'st_file_attributes', 0) & REPARSE:
                        try:
                            if e.is_file():
                                tst = e.stat()
                                files[r] = (tst.st_size, tst.st_mtime_ns)
                            else:
                                skipped.append(r)
                        except OSError:
                            skipped.append(r)
                        continue
                    if e.is_dir(follow_symlinks=False):
                        stack.append(r)
                    else:
                        files[r] = (st.st_size, st.st_mtime_ns)
    return files, skipped


def main():
    full = '--full' in sys.argv
    t0 = time.time()
    s2 = {}
    with open(STATE, encoding='utf-8') as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip():
                continue
            c = ln.rstrip('\r\n').split('\t')
            s2[c[0]] = c
    live, skipped = walk()
    changed, new, gone, hashed = [], [], [], 0
    for rel in sorted(live):
        size, mt = live[rel]
        c = s2.get(rel)
        if c is None:
            new.append((rel, size, mt, sha(lp(rel))))
            hashed += 1
            continue
        l_size, l_mt, l_sha, s_size, s_sha = num(c[1]), num(c[2]), c[3], num(c[4]), c[6]
        if not full and size == l_size and mt == l_mt and l_sha == s_sha:
            continue
        h = sha(lp(rel))
        hashed += 1
        if h != s_sha:
            changed.append((rel, size, mt, h, s_size, s_sha, c[7] if len(c) > 7 else '-'))
    for rel in sorted(set(s2) - set(live)):
        c = s2[rel]
        if c[6] not in ('', '-'):
            gone.append((rel, c[6]))
    print('# Agent 10 scan-vs-s2.py %s, mode %s: live DimensionsRecomp vs %s (snap1 sha256); snap.py walk rules'
          % (time.strftime('%Y-%m-%d %H:%M:%S'), 'full' if full else 'fast', os.path.basename(STATE)))
    print('# live files %d; STATE-S2 rows %d; hashed %d; CHANGED %d; NEW %d; GONE %d; SKIPPED (dir links) %d; %.1f s'
          % (len(live), len(s2), hashed, len(changed), len(new), len(gone), len(skipped), time.time() - t0))
    print('kind\trel\tlive_size\tlive_mtime\tlive_sha256\ts2_size\ts2_sha256\ts2_origin')
    for rel, size, mt, h, s_size, s_sha, origin in changed:
        print('CHANGED\t%s\t%d\t%s\t%s\t%s\t%s\t%s' % (rel, size, ts(mt), h, s_size, s_sha, origin))
    for rel, size, mt, h in new:
        print('NEW\t%s\t%d\t%s\t%s\t-\t-\t-' % (rel, size, ts(mt), h))
    for rel, s_sha in gone:
        print('GONE\t%s\t-\t-\t-\t-\t%s\t-' % (rel, s_sha))
    for rel in skipped:
        print('SKIPPED\t%s\t-\t-\t-\t-\t-\t-' % rel)


if __name__ == '__main__':
    main()
