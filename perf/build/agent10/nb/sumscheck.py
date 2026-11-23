"""sumscheck.py (Agent 10, task #17 item 1a): verify a snapshot's generated code against an install's SHA256SUMS.txt
when the sums file lives outside the tree (review/r5/verify_sums.py only checks <tree>/SHA256SUMS.txt against itself).
Read-only; one thread.

  python sumscheck.py --sums build/agent9/install/batch-nolr/SHA256SUMS.txt --root <snap>/DimensionsRecomp/rexlego
                      [--extras-dir generated] [--out F]

SUMS lines are "<sha256>  <rel>" with rel relative to the install root (generated/default/..., generated/rexglue.cmake,
legodimensions_config.toml); here they resolve against --root. Reports missing, mismatched and extra files (extras =
files under <root>/<extras-dir> that SUMS does not list), plus TU count/bytes of generated/default. Exit 0 on MATCH.
"""
import argparse
import hashlib
import os
import sys
import time

DEPFILE = 'generated/default/codegen.d'


def sha(p):
    d = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            d.update(chunk)
    return d.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sums', required=True)
    ap.add_argument('--root', required=True)
    ap.add_argument('--extras-dir', default='generated')
    ap.add_argument('--out')
    o = ap.parse_args()
    t0 = time.time()
    want = {}
    with open(o.sums, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if not line.strip() or line.startswith('#'):
                continue
            h, rel = line.split(None, 1)
            rel = rel.lstrip('*').strip().replace('\\', '/')
            want[rel] = h.lower()
    missing, bad, nbytes, dep_note = [], [], 0, 'not in SUMS'
    for rel in sorted(want):
        p = os.path.join(o.root, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        nbytes += os.path.getsize(p)
        got = sha(p)
        if rel == DEPFILE:
            # gen-check.py rewrites codegen.d once: the reference's --base-rex path -> the snapshot's rexlego path
            ref = open(os.path.join(os.path.dirname(os.path.abspath(o.sums)), rel), 'rb').read()
            base_rex = None
            for ln in ref.decode('utf-8', 'replace').splitlines():
                ln = ln.strip().rstrip('\\').strip()
                if ln.endswith('/legodimensions_config.toml'):
                    base_rex = ln[:-len('/legodimensions_config.toml')]
                    break
            snap_rex = os.path.abspath(o.root).replace('\\', '/')
            if hashlib.sha256(ref).hexdigest() != want[rel]:
                bad.append((rel, want[rel][:16], 'reference file differs from SUMS'))
            elif base_rex is None:
                bad.append((rel, want[rel][:16], 'reference names no legodimensions_config.toml'))
            else:
                exp = hashlib.sha256(ref.replace(base_rex.encode(), snap_rex.encode())).hexdigest()
                if got == exp:
                    dep_note = f'== reference with {base_rex} -> {snap_rex} ({got[:16]})'
                elif got == want[rel]:
                    bad.append((rel, want[rel][:16], 'still the reference bytes (not rewritten to snapshot paths)'))
                else:
                    bad.append((rel, exp[:16] + ' (rewritten)', got[:16]))
            continue
        if got != want[rel]:
            bad.append((rel, want[rel][:16], got[:16]))
    extras, tus, tu_bytes = [], 0, 0
    base = os.path.join(o.root, o.extras_dir)
    for root, dirs, files in os.walk(base):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, o.root).replace('\\', '/')
            if rel not in want:
                extras.append(rel)
            if rel.startswith('generated/default/') and fn.endswith('.cpp') and '/' not in rel[len('generated/default/'):]:
                tus += 1
                tu_bytes += os.path.getsize(full)
    ok = not (missing or bad or extras)
    W = [f'SUMS {o.sums}: {len(want):,} entries (sha256 {sha(o.sums)[:16]})',
         f'root {o.root}: hashed {len(want) - len(missing):,} files ({nbytes:,} B) in {time.time() - t0:.1f}s; '
         f'generated/default: {tus} *.cpp files, {tu_bytes:,} B',
         f'codegen.d: {dep_note}',
         f'missing: {len(missing)} {missing[:20]}',
         f'mismatched: {len(bad)} ' + '; '.join(f'{r} want {a} got {b}' for r, a, b in bad[:20]),
         f'extra under {o.extras_dir}/: {len(extras)} {extras[:20]}',
         f'RESULT {"MATCH" if ok else "DIFFERENT"}']
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
