#!/usr/bin/env python3
"""log_types.py - read-only: game*.log line types (all levels, normalised like scan_matrix.py) that are not in every
run of a matrix or whose count differs between runs. Usage: python -B log_types.py <matrix dir> <out .txt in a scan dir>
(helper of Agent 8, 2026-11-23; stdlib only)."""
import csv
import glob
import os
import re
import sys

sys.dont_write_bytecode = True
LOG_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d [0-9:.]+)\] \[(?P<lvl>[^\]]+)\] \[(?P<cat>[^\]]+)\] '
                    r'(?:\[t\d+\] )?(?P<msg>.*)$')


def norm(msg, rd):
    s = re.sub(re.escape(rd), '<RUN>', msg, flags=re.I)
    s = re.sub(r'(?:\b[0-9A-Fa-f]{2}\b ?){4,}', '<hex bytes> ', s)  # Toypad[Read ]/[Write] payload dumps
    s = re.sub(r'0x[0-9A-Fa-f]+', '0x#', s)
    s = re.sub(r'\b(?=[0-9A-Fa-f]*\d)[0-9A-Fa-f]{6,}\b', '#', s)
    s = re.sub(r'\d+(?:\.\d+)?', '#', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    d, outp = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if '\\readout\\' not in outp.lower() or os.path.basename(os.path.dirname(outp)).lower() != 'scan':
        sys.exit('refusing to write outside a ...\\readout\\<w>\\scan dir: %s' % outp)
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    runs = []
    for r in rows:
        name = os.path.basename((r.get('run_dir') or '').rstrip('\\/'))
        rd = os.path.join(d, 'runs', name)
        lab = r['arm'] + ('' if (r.get('scored') or '').lower() == 'true' else '(cold)')
        types, first = {}, {}
        for p in sorted(glob.glob(os.path.join(glob.escape(rd), 'game*.log'))):
            with open(p, encoding='utf-8', errors='replace') as fh:
                lines = fh.read().splitlines()
            for ln in lines:
                m = LOG_RE.match(ln)
                if m:
                    k = '[%s] %s: %s' % (m.group('lvl').lower(), m.group('cat'), norm(m.group('msg'), rd)[:170])
                else:
                    k = '(no level) ' + norm(ln, rd)[:170]
                types[k] = types.get(k, 0) + 1
                first.setdefault(k, ln.strip()[:220])
        runs.append((name, lab, types, first))
    n = len(runs)
    allk = sorted(set(k for _, _, t, _ in runs for k in t))
    out = ['# game*.log line types (normalised) missing from some runs or with differing counts; %d runs; %s' % (n, d),
           '# counts per run in results.csv order, grouped by arm (cold run separate); one raw example line each', '']
    same = 0
    for k in allk:
        have = [nm for nm, _, t, _ in runs if k in t]
        cnts = set(t.get(k, 0) for _, _, t, _ in runs)
        if len(cnts) == 1:
            same += 1
            continue
        by = {}
        for nm, lab, t, _ in runs:
            by.setdefault(lab, []).append(str(t.get(k, 0)))
        ex = next(fr[k] for _, _, t, fr in runs if k in fr)
        out.append('%s\n    in %d/%d runs; counts: %s\n    e.g. %s' % (k, len(have), n, '; '.join(
            '%s %s' % (lab, '/'.join(v)) for lab, v in by.items()), ex))
    out.append('')
    out.append('# %d types with the same count in every run; %d types listed above' % (same, len(allk) - same))
    text = '\n'.join(out) + '\n'
    with open(outp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    print(text)


if __name__ == '__main__':
    main()
