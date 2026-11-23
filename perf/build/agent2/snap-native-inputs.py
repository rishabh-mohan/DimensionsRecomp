"""Agent 2 - copy explicit native ON inputs into the snapshot (batch 1 = S1 plus explicit inputs and patches).

Usage: python build\\agent2\\snap-native-inputs.py <TAG> <relpath> [<relpath> ...]
  <relpath> is relative to DimensionsRecomp/ and names a file or a directory (copied recursively, without .git and
  __pycache__). For every file:
    - the live source is hashed before and after the copy; a source that changes meanwhile is an error;
    - it is copied to build/agent2/snap1/DimensionsRecomp/<relpath> with mtime = now (so ninja rebuilds whatever
      depends on it), unless the snapshot already holds an identical file ('same');
    - it is listed in build/agent2/snap1/NATIVE-INPUTS-<TAG>-<HHMM>.tsv (relpath, size, mtime, sha256, action).
snap.py never deletes these copies: its removals come from its own previous manifest, and rexlego/out is excluded.
"""
import hashlib, os, shutil, sys, time

R = r'<workspace>'
LIVE = os.path.join(R, 'DimensionsRecomp')
SNAP = os.path.join(R, r'build\agent2\snap1\DimensionsRecomp')
SKIP = {'.git', '__pycache__'}


def L(p):
    return '\\\\?\\' + os.path.abspath(p)


def sha(p):
    h = hashlib.sha256()
    with open(L(p), 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def files_of(rel):
    src = os.path.join(LIVE, rel)
    if os.path.isfile(L(src)):
        yield os.path.normpath(rel)
    elif os.path.isdir(L(src)):
        for dp, dn, fn in os.walk(L(src)):
            dn[:] = sorted(d for d in dn if d not in SKIP)
            for f in sorted(fn):
                yield os.path.relpath(os.path.join(dp, f), L(LIVE))
    else:
        raise SystemExit('missing input: ' + src)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    tag, rels = sys.argv[1], sys.argv[2:]
    t0 = time.time()
    rows, counts, total = [], {'copied': 0, 'replaced': 0, 'same': 0}, 0
    for rel in rels:
        for r in files_of(rel):
            s, d = os.path.join(LIVE, r), os.path.join(SNAP, r)
            st = os.stat(L(s))
            h = sha(s)
            if os.path.isfile(L(d)) and sha(d) == h:
                kind = 'same'
            else:
                kind = 'replaced' if os.path.exists(L(d)) else 'copied'
                os.makedirs(L(os.path.dirname(d)), exist_ok=True)
                shutil.copyfile(L(s), L(d))
                st2 = os.stat(L(s))
                if st2.st_mtime_ns != st.st_mtime_ns or st2.st_size != st.st_size or sha(s) != h:
                    raise SystemExit('source changed during the copy: ' + r)
                if sha(d) != h:
                    raise SystemExit('copy differs from its source: ' + r)
            counts[kind] += 1
            total += st.st_size
            rows.append((r.replace('\\', '/'), st.st_size,
                         time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)), h, kind))
    out = os.path.join(os.path.dirname(SNAP), 'NATIVE-INPUTS-%s-%s.tsv' % (tag, time.strftime('%H%M')))
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# native ON inputs copied into build/agent2/snap1 by Agent 2 (%s, %s); relpath is under '
                'DimensionsRecomp/\n' % (tag, time.strftime('%Y-%m-%d %H:%M:%S')))
        f.write('# inputs: %s\n' % ' '.join(rels))
        f.write('# relpath\tsize\tmtime\tsha256\taction\n')
        for row in rows:
            f.write('%s\t%d\t%s\t%s\t%s\n' % row)
    print('native inputs %s: files=%d bytes=%d copied=%d replaced=%d same=%d wall=%.1fs' % (
        tag, len(rows), total, counts['copied'], counts['replaced'], counts['same'], time.time() - t0))
    for row in rows:
        if row[4] != 'same' or len(rows) <= 40:
            print('  %-8s %12d  %s  %s' % (row[4], row[1], row[3][:16], row[0]))
    h = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    print('list: %s sha256=%s' % (out, h))


if __name__ == '__main__':
    main()
