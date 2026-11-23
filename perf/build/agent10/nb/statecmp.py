"""statecmp.py (Agent 10, task #17 item 1a): check a snapshot tree against Agent 2's snap1 STATE file, i.e. prove a
copy (snapB3) has exactly the S3d build inputs outside the generated code. Read-only; one thread.

  python statecmp.py --state build/agent2/snap1/STATE-S3d-0342.tsv --root <snap>/DimensionsRecomp [--full] [--out F]
                     [--override REL=SHA256 ...] [--skip RELDIR ...]

STATE rows (snap-patch.py): rel, live size, live mtime_ns, live sha256, snap1 size, snap1 mtime_ns, snap1 sha256,
origin. generated/ is not listed; rexlego/generated is skipped here (check it with sumscheck.py against batch-nolr's
SHA256SUMS.txt). Default: sha256 of every file under rexlego/ (outside generated) and of any file whose size or mtime
differs from the snap1 columns; --full hashes every listed file. Reports missing, extra (outside .git and the skipped
dirs), size differences and sha differences. Exit 0 when the tree matches, 1 otherwise.

Known STATE quirk (04:06 self-test on snap1): the row for rexlego/legodimensions_manifest.toml carries snap1 size 771
but the *live* sha (838cff24..., 762 B). snap1's real file is 771 B, sha 14a59e33..., i.e. live with game_root
rewritten to "../../../../../game/disc" for the deeper snapshot path. The default override covers it (an override
compares the sha only). rexglue-sdk/out (in-tree SDK build output, not an input) is skipped and counted.
Files under rexlego/out that STATE doesn't list (the native build's out/native-gpu/*-linked-dxil-cache.cpp) are
reported with size and sha but don't fail; the 15 STATE-listed native-bank files there are compared normally.
For snapB3 add --override rexlego/legodimensions_config.toml=<batch-nolr config sha> (prep-nb step 3 writes it).
"""
import argparse
import hashlib
import os
import sys
import time

SKIP_DIRS = {'.git'}
SKIP_REL = {'rexlego/generated', 'generated', 'rexglue-sdk/out'}
BUILD_OUTPUT_PREFIXES = ('rexlego/out/',)
DEFAULT_OVERRIDES = {
    'rexlego/legodimensions_manifest.toml': '14a59e33c0f89d12800e7d890ec5c88d8337bc50350cec2cccbbe3ee0b2d73c6'}


def sha(p):
    d = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    return d.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--state', required=True)
    ap.add_argument('--root', required=True)
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--skip', action='append', default=[], help='extra rel dir to skip (counted)')
    ap.add_argument('--override', action='append', default=[], help='REL=SHA256 expected instead of the STATE row')
    ap.add_argument('--no-default-override', action='store_true')
    o = ap.parse_args()
    skip_rel = SKIP_REL | {s.replace('\\', '/').strip('/') for s in o.skip}
    overrides = {} if o.no_default_override else dict(DEFAULT_OVERRIDES)
    for kv in o.override:
        k, v = kv.split('=', 1)
        overrides[k.replace('\\', '/')] = v.lower()
    skipped = {}
    t0 = time.time()
    rows, header, absent = {}, '', 0
    with open(o.state, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if line.startswith('#'):
                header = header or line[:200]
                continue
            p = line.split('\t')
            if len(p) < 7:
                continue
            if p[4] == '-' or p[6] == '-':  # not in the snapshot (e.g. live-only): absent rows count as extra if present
                absent += 1
                continue
            rows[p[0].replace('\\', '/')] = (int(p[4]), int(p[5]), p[6].lower(), p[7] if len(p) > 7 else '')
    on_disk = {}
    for root, dirs, files in os.walk(o.root):
        rel_root = os.path.relpath(root, o.root).replace('\\', '/')
        rel_root = '' if rel_root == '.' else rel_root + '/'
        keep = []
        for d in dirs:
            if d in SKIP_DIRS:
                continue
            if (rel_root + d) in skip_rel:
                skipped[rel_root + d] = sum(len(fs) for _, _, fs in os.walk(os.path.join(root, d)))
                continue
            keep.append(d)
        dirs[:] = keep
        for fn in files:
            on_disk[rel_root + fn] = os.path.join(root, fn)
    missing = sorted(set(rows) - set(on_disk))
    extra_all = sorted(set(on_disk) - set(rows))
    built = [r for r in extra_all if r.startswith(BUILD_OUTPUT_PREFIXES)]
    extra = [r for r in extra_all if not r.startswith(BUILD_OUTPUT_PREFIXES)]
    built_info = []
    for r in built:
        st = os.stat(on_disk[r])
        built_info.append(f'{r} {st.st_size:,} B {sha(on_disk[r])[:16]}')
    size_diff, sha_diff, over_ok, hashed, hbytes = [], [], [], 0, 0
    for rel in sorted(set(rows) & set(on_disk)):
        size, mtime, h, origin = rows[rel]
        st = os.stat(on_disk[rel])
        if rel in overrides:  # expected content differs from the STATE row: compare the sha only
            hashed += 1
            hbytes += st.st_size
            got = sha(on_disk[rel])
            if got != overrides[rel]:
                sha_diff.append((rel, overrides[rel][:16], origin + ' override; got ' + got[:16]))
            else:
                over_ok.append(f'{rel} {st.st_size:,} B == {got[:16]} (STATE row {h[:16]}, {size:,} B)')
            continue
        if st.st_size != size:
            size_diff.append((rel, size, st.st_size, origin))
            continue
        if o.full or rel.startswith('rexlego/') or st.st_mtime_ns != mtime:
            hashed += 1
            hbytes += st.st_size
            if sha(on_disk[rel]) != h:
                sha_diff.append((rel, h[:16], origin))
    mode = ' (--full)' if o.full else ' (rexlego/ + size/mtime changes)'
    W = [f'STATE {o.state}: {len(rows):,} rows, {absent} not-in-snapshot rows ({header[:120]}...)',
         f'root  {o.root}: {len(on_disk):,} files outside .git and skipped dirs; skipped (not compared): '
         + (', '.join(f'{k} {v:,} files' for k, v in sorted(skipped.items())) or 'none'),
         f'overrides matched: {len(over_ok)}/{len(overrides)} ' + '; '.join(over_ok),
         f'hashed {hashed:,} files ({hbytes:,} B){mode}; {time.time() - t0:.1f}s',
         f'missing in root: {len(missing)} {missing[:20]}',
         f'build outputs not in STATE (not inputs, not failing): {len(built)} ' + '; '.join(built_info[:20]),
         f'extra in root: {len(extra)} {extra[:20]}',
         f'size differs: {len(size_diff)} ' + '; '.join(f'{r} {a}->{b} [{g}]' for r, a, b, g in size_diff[:30]),
         f'sha differs: {len(sha_diff)} ' + '; '.join(f'{r} (want {h}) [{g}]' for r, h, g in sha_diff[:30])]
    ok = not (missing or extra or size_diff or sha_diff)
    W.append(f'RESULT {"MATCH" if ok else "DIFFERENT"}')
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
