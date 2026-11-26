#!/usr/bin/env python3
# stage6_inputs.py - M16 (S5), build/agent16/pack: stage the native6pack pack inputs from a dump run (PLAN-dump6 v2 §6).
#
#   python -B build\agent16\pack\stage6_inputs.py --dump-dir <kit shader-dumps-native-<stamp>> [--dry]
#
# Reads (never writes) <dump-dir>\placement-containers\{vs,ps}-<16 hex>.bin. Only that subdir is read: root
# create-path dumps and placement-raw are never staged (D-C2). A container is NEW when its name is not in the base
# pack input pack-input-combined-20261126-053440 (SHA256SUMS FA99EB7D, 141 files) and its bytes are not either.
# Writes (refuses existing dirs; nothing with --dry):
#   <out-root>\pack-input-zone-<stamp>\       the NEW containers (copies) + SHA256SUMS.txt
#   <out-root>\pack-input-combined6-<stamp>\  base + NEW, deduped by name, + SHA256SUMS.txt; the base rows of
#                                             category "root" (vs-A58EBA12, ps-93B9F93B) are left out (D-C2)
#   <out-root>\stage6-<stamp>.txt             the log (also printed)
# <out-root> defaults to build\agent16\dump. Every source file is sha256-checked before and after the copy.
# FAIL (exit 1): base SUMS sha or a base file changed; a dump container with a base name but different bytes
# (name collision); a bad file name in placement-containers; a copy that differs. 0 NEW containers = exit 3 (nothing
# to pack; no dirs written). Exit 2 = refused (bad args / existing out dir).
import argparse, datetime, hashlib, os, re, shutil, sys

W = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
DUMP = os.path.join(W, 'build', 'agent16', 'dump')
BASE = os.path.join(DUMP, 'pack-input-combined-20261126-053440')
BASE_SUMS = 'FA99EB7D'  # sha256 prefix of BASE\SHA256SUMS.txt
NAME = re.compile(r'^(vs|ps)-[0-9A-F]{16}\.bin$')
LINE = re.compile(r'^([0-9A-Fa-f]{64})\s+(\S+)\s*(?:\((.*)\))?\s*$')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def read_sums(d):
    rows = {}
    for line in open(os.path.join(d, 'SHA256SUMS.txt'), encoding='utf-8'):
        m = LINE.match(line.strip())
        if m:
            rows[m.group(2)] = (m.group(1).upper(), m.group(3) or '')
        elif line.strip():
            raise ValueError('unparsed SUMS line: %s' % line.strip())
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump-dir', required=True, help='kit dump dir with a placement-containers subdir')
    ap.add_argument('--base', default=BASE)
    ap.add_argument('--base-sums', default=BASE_SUMS, help='sha256 prefix the base SHA256SUMS.txt must have')
    ap.add_argument('--out-root', default=DUMP)
    ap.add_argument('--dry', action='store_true', help='list only, write nothing')
    a = ap.parse_args()
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    pc = os.path.join(os.path.abspath(a.dump_dir), 'placement-containers')
    zone = os.path.join(a.out_root, 'pack-input-zone-' + stamp)
    comb = os.path.join(a.out_root, 'pack-input-combined6-' + stamp)
    logp = os.path.join(a.out_root, 'stage6-%s.txt' % stamp)
    if not os.path.isdir(pc) or not os.path.isdir(a.base) or not os.path.isdir(a.out_root):
        print('REFUSED: missing %s' % ', '.join(p for p in (pc, a.base, a.out_root) if not os.path.isdir(p)))
        return 2
    if any(os.path.exists(p) for p in (zone, comb, logp)):
        print('REFUSED: out dir exists')
        return 2
    out, fails = [], []

    def log(s):
        out.append(s)
        print(s, flush=True)

    log('stage6_inputs.py sha256=%s dump=%s base=%s out-root=%s%s' % (
        sha(os.path.abspath(__file__)), a.dump_dir, a.base, a.out_root, ' DRY' if a.dry else ''))
    bs = sha(os.path.join(a.base, 'SHA256SUMS.txt'))
    if not bs.startswith(a.base_sums.upper()):
        fails.append('base SHA256SUMS.txt %s is not %s' % (bs[:8], a.base_sums))
    base = read_sums(a.base)
    for n, (h, _) in base.items():
        if sha(os.path.join(a.base, n)) != h:
            fails.append('base file %s differs from its SUMS line' % n)
    bysha = {h: n for n, (h, _) in base.items()}
    roots = sorted(n for n, (_, cat) in base.items() if cat.split(';')[0].strip().lower() == 'root')
    log('base: %d files, SUMS %s; %d root file(s) not carried into combined6 (D-C2): %s' % (
        len(base), bs[:8], len(roots), ', '.join(roots) or '-'))
    new, same, dupsha = [], 0, []
    names = sorted(os.listdir(pc))
    for n in names:
        p = os.path.join(pc, n)
        if not os.path.isfile(p) or not NAME.match(n):
            fails.append('unexpected entry in placement-containers: %s' % n)
            continue
        h = sha(p)
        if n in base:
            if base[n][0] == h:
                same += 1
            else:
                fails.append('name collision: %s in the dump differs from the base copy' % n)
            continue
        if h in bysha:
            dupsha.append('%s = base %s' % (n, bysha[h]))
            continue
        new.append((n, h, os.path.getsize(p)))
    log('dump placement-containers: %d files; %d already in base (same bytes); %d same bytes as a base file under '
        'another name; %d NEW' % (len(names), same, len(dupsha), len(new)))
    for d in dupsha:
        log('DUP  %s' % d)
    for n, h, sz in new:
        log('NEW  %s %s %d B' % (n, h, sz))
    for f in fails:
        log('FAIL %s' % f)
    rc = 1 if fails else (3 if not new else 0)
    if not a.dry and rc == 0:
        src_tag = os.path.basename(os.path.normpath(a.dump_dir))
        os.makedirs(zone)
        os.makedirs(comb)
        zl, cl = [], []
        for n, h, _ in new:
            for d in (zone, comb):
                shutil.copyfile(os.path.join(pc, n), os.path.join(d, n))
            zl.append('%s  %s  (placement-containers; from %s)' % (h, n, src_tag))
            cl.append((n, '%s  %s  (placement-containers; from %s)' % (h, n, os.path.basename(zone))))
        for n, (h, cat) in base.items():
            if n in roots:
                continue
            shutil.copyfile(os.path.join(a.base, n), os.path.join(comb, n))
            cl.append((n, '%s  %s  (%s)' % (h, n, cat) if cat else '%s  %s' % (h, n)))
        with open(os.path.join(zone, 'SHA256SUMS.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sorted(zl, key=lambda s: s[66:])) + '\n')
        with open(os.path.join(comb, 'SHA256SUMS.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(l for _, l in sorted(cl)) + '\n')
        for d in (zone, comb):
            rows = read_sums(d)
            bad = [n for n, (h, _) in rows.items() if sha(os.path.join(d, n)) != h]
            extra = sorted(set(os.listdir(d)) - set(rows) - {'SHA256SUMS.txt'})
            if bad or extra:
                fails.append('%s: %d copy mismatch(es), %d unlisted file(s)' % (os.path.basename(d), len(bad), len(extra)))
            log('WROTE %s: %d files, SHA256SUMS.txt %s' % (d, len(rows), sha(os.path.join(d, 'SHA256SUMS.txt'))))
        for n, h, _ in new:
            if sha(os.path.join(pc, n)) != h:
                fails.append('dump source %s changed during the copy' % n)
        rc = 1 if fails else 0
        for f in fails:
            log('FAIL %s' % f)
    log('RESULT %s (NEW %d, base %d, root dropped %d, combined %d)' % (
        {0: 'PASS', 1: 'FAIL', 3: 'NOTHING-NEW'}[rc], len(new), len(base), len(roots), len(base) - len(roots) + len(new)))
    if not a.dry:
        with open(logp, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
    return rc


if __name__ == '__main__':
    sys.exit(main())
