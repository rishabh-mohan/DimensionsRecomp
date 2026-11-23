#!/usr/bin/env python3
"""make_pool.py (Agent 8, task #20): pool run-matrix passes of one window into one pseudo matrix dir, read-only on
the inputs. The pseudo dir holds matrix.json (copied from the first pass; every pass must have the same sha256) and a
merged results.csv: rows in pass order, seq renumbered 1..N, scored rounds of pass k shifted by the number of rounds
of the passes before it (pass 2 rounds 1-5 -> 6-10), rep shifted the same way; cold rows keep round 0. run_dir
stays absolute, so Agent 7's readout.py (resolve_run_dir) reads each run's own folder in place. Nothing is copied
from runs/ and nothing in the pass folders is written.

Usage: python -B make_pool.py OUTDIR PASSDIR [PASSDIR ...]
"""
import csv
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest().upper()


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    out, dirs = argv[1], argv[2:]
    shas = [sha(os.path.join(d, 'matrix.json')) for d in dirs]
    if len(set(shas)) != 1:
        raise SystemExit('matrix.json differs between passes: %s' % shas)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(dirs[0], 'matrix.json'), 'rb') as f:
        mj = f.read()
    with open(os.path.join(out, 'matrix.json'), 'wb') as f:
        f.write(mj)
    header, rows_out, off, seq, info = None, [], 0, 0, []
    for d in dirs:
        with open(os.path.join(d, 'results.csv'), newline='', encoding='utf-8-sig') as f:
            rd = csv.DictReader(f)
            if header is None:
                header = rd.fieldnames
            if rd.fieldnames != header:
                raise SystemExit('results.csv columns differ in %s' % d)
            rows = list(rd)
        maxr = 0
        for r in rows:
            seq += 1
            r = dict(r)
            r['seq'] = str(seq)
            rv = (r.get('round') or '').strip()
            # the cold run is round 0 / rep 0 / scored False in every pass: it keeps round 0
            if rv.isdigit() and int(rv) >= 1:
                maxr = max(maxr, int(rv))
                r['round'] = str(int(rv) + off)
                if (r.get('rep') or '').strip().isdigit() and int(r['rep']) >= 1:
                    r['rep'] = str(int(r['rep']) + off)
            rows_out.append(r)
        info.append({'pass_dir': os.path.abspath(d), 'rows': len(rows), 'rounds': maxr, 'round_offset': off,
                     'results_sha256': sha(os.path.join(d, 'results.csv'))})
        off += maxr
    with open(os.path.join(out, 'results.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows_out)
    meta = {'tool': 'make_pool.py', 'matrix_sha256': shas[0], 'passes': info, 'rows': len(rows_out),
            'rounds': off}
    with open(os.path.join(out, 'pool.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    print('pooled %d rows, %d rounds from %d passes -> %s' % (len(rows_out), off, len(dirs), out))


if __name__ == '__main__':
    main(sys.argv)
