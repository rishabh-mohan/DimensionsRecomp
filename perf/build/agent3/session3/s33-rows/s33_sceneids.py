"""#33 ruling (a3) read (M3 draft; M10 s33-rows-rating C1): an ON-row mark LOOK where only the scene ids differ.

Usage: s33_sceneids.py --row <queue id> <base run> <cand run>

Marks and scene ids come from s4a_check.marks() (the median perf.csv draw_calls/vertices_processed at each input.csv
mark), the same as s4b_check. The judged marks are also the same: the marks up to up-2, or the non-idle marks other
than 'end'.

"Occurs in a run" means the id is a stable scene in that run's perf.csv (a run of >= 10 identical frames, as in
s4a_check.scenes()), i.e. stable > 0.0 s. A row count alone does not count.

PASS? (exit 0) needs all of these:
- the row is an ON row (s33onsf, s33stop1-7, s33onw, s33ond);
- the cand's judged marks have the same names, in the same order, as the base's;
- every judged mark is within 1 s (t_s from input.csv);
- every id of every differing mark is a stable scene in both runs.
Anything else gives STOP (exit 1). On gate/OFF rows, any differing judged mark is a STOP, because (a3) does not apply.

For each differing mark it prints the name, base id -> cand id, t_s in both runs, and each id's rows/stable seconds in
both runs. It also gives a SHOULD note: is the cand id next to the base id in the base's scene order?
Exit 2 = usage, or no marks / no perf.csv. It is read-only.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 's4a'))
import s4a_check as A  # noqa: E402

ON_ROWS = {'s33onsf', 's33onw', 's33ond'} | {'s33stop%d' % i for i in range(1, 8)}


def perf_scenes(run):
    """key -> rows, key -> stable seconds, and the base's stable-scene order (consecutive duplicates removed)."""
    p = os.path.join(run, 'perf.csv')
    if not os.path.isfile(p):
        return None
    cnt, stable, order = {}, {}, []
    cur, n, secs = None, 0, 0.0

    def close():
        if cur is not None and n >= 10:
            stable[cur] = stable.get(cur, 0.0) + secs
            if not order or order[-1] != cur:
                order.append(cur)
    with open(p, newline='', encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            try:
                key = '%d/%d' % (int(float(row['draw_calls'])), int(float(row['vertices_processed'])))
                dt = float(row['frame_time_us']) / 1e6
            except (KeyError, ValueError, TypeError):
                continue
            cnt[key] = cnt.get(key, 0) + 1
            if key != cur:
                close()
                cur, n, secs = key, 0, 0.0
            n += 1
            secs += dt
    close()
    return cnt, stable, order


def judged(names):
    if 'up-2' in names:
        return names[:names.index('up-2') + 1]
    return [k for k in names if not k.startswith('idle-') and k != 'end']


def main(argv):
    if len(argv) != 5 or argv[1] != '--row':
        print(__doc__)
        return 2
    row, base, cand = argv[2], argv[3], argv[4]
    mb, mc = A.marks(base, False, 'off'), A.marks(cand, False, 'off')
    pb, pc = perf_scenes(base), perf_scenes(cand)
    if not mb or not mc or pb is None or pc is None:
        print('no marks or no perf.csv (base marks %s, cand marks %s)' % (bool(mb), bool(mc)))
        return 2
    nb, nc = os.path.basename(base.rstrip('\\/')), os.path.basename(cand.rstrip('\\/'))
    jb, jc = judged(list(mb.keys())), judged(list(mc.keys()))
    stop = []
    print('row %s (%s); base %s, cand %s' % (row, 'ON: (a3) applies' if row in ON_ROWS else 'not ON: (a3) does not apply', nb, nc))
    print('judged marks base: %s' % ' '.join(jb))
    if jc != jb:
        stop.append('judged mark names/order differ (cand: %s)' % ' '.join(jc))
    for k in jb:
        if k in mc and abs(mc[k][0] - mb[k][0]) >= 1.0:
            stop.append('mark %s t_s %.2f vs %.2f (>= 1 s)' % (k, mb[k][0], mc[k][0]))
    diff = [k for k in jb if k in mc and mc[k][2] != mb[k][2]]
    print('differing judged marks: %d' % len(diff))
    for k in diff:
        ib, ic = mb[k][2], mc[k][2]
        print('  %s: %s -> %s; t_s base %.2f cand %.2f (delta %.2f s)' % (k, ib, ic, mb[k][0], mc[k][0], mc[k][0] - mb[k][0]))
        for i in (ib, ic):
            sb, sc = pb[1].get(i, 0.0), pc[1].get(i, 0.0)
            print('    %-16s base rows %d stable %.1fs; cand rows %d stable %.1fs' % (i, pb[0].get(i, 0), sb, pc[0].get(i, 0), sc))
            if sb <= 0.0 or sc <= 0.0:
                stop.append('%s %s not a stable scene in %s' % (k, i, ' and '.join(n for n, s in ((nb, sb), (nc, sc)) if s <= 0.0)))
        o = pb[2]
        adj = any(o[j] == ib and ((j > 0 and o[j - 1] == ic) or (j + 1 < len(o) and o[j + 1] == ic)) for j in range(len(o)))
        print('    SHOULD: cand id next to base id in base scene order: %s' % ('yes' if adj else 'NO'))
    if diff and row not in ON_ROWS:
        stop.append('%d judged mark(s) differ on a row that is not ON' % len(diff))
    if stop:
        print('RESULT: STOP ' + '; '.join(stop))
        return 1
    print('RESULT: PASS? (%s)' % ('no differing judged marks' if not diff else '(a3) conditions hold for %d mark(s)' % len(diff)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
