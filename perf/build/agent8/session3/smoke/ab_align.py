"""M8 item 9: align frames > 8 ms with sys.csv rows (snapshot rows 0,5,10,... vs the other rows).
Frame wall time: the frame at frames.json window.first_row is placed at run.json measure_start.epoch_s (the mark lags the
true frame by <= 59 rows, about 0.2 s here); later frames add their frame_time_us. Each sys.csv row is one sample at
epoch_s. For every row we count frames > 8 ms (and their excess ms over 8) within +-W s of the row's epoch_s, then compare
snapshot rows (index % 5 == 0) with the other rows. With ProcEvery 0 the same index sets act as a control.
Usage: python ab_align.py <run dir> [<run dir> ...]
"""
import csv, json, os, sys

W = 0.35
TH = 8000.0


def rj(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def one(d):
    fr = rj(os.path.join(d, 'frames.json')); run = rj(os.path.join(d, 'run.json'))
    with open(os.path.join(d, 'perf.csv'), encoding='utf-8-sig', newline='') as f:
        ft = [float(r['frame_time_us']) for r in csv.DictReader(f) if r.get('frame_time_us') not in (None, '')]
    first = fr['window']['first_row']; n = fr['window']['rows']
    t0 = run['measure_start']['epoch_s']; t1 = run['measure_end']['epoch_s']
    # perf.csv rows are 1-based after the header in frames.json's counting; first_row is the first window row index (0-based data row)
    times = []; t = t0
    for x in ft[first:first + n]:
        t += x / 1e6
        times.append((t, x))
    with open(os.path.join(d, 'sys.csv'), encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    snap = {'n': 0, 'cnt': 0, 'exc': 0.0}; oth = {'n': 0, 'cnt': 0, 'exc': 0.0}
    phase = [0] * 10
    e0 = float(rows[0]['epoch_s'])
    for i, r in enumerate(rows):
        e = float(r['epoch_s'])
        if e - W < t0 or e + W > t1:
            continue
        g = snap if i % 5 == 0 else oth
        g['n'] += 1
        for tt, x in times:
            if x > TH and abs(tt - e) <= W:
                g['cnt'] += 1; g['exc'] += (x - TH) / 1000
    for tt, x in times:
        if x > TH:
            phase[int((((tt - e0) % 5.0) / 5.0) * 10) % 10] += 1
    big = sum(1 for _, x in times if x > TH)
    srt = sorted(x for _, x in times)
    med = srt[len(srt) // 2] / 1000 if srt else float('nan'); p99 = srt[min(len(srt) - 1, int(0.99 * len(srt)))] / 1000 if srt else float('nan')
    so = open(os.path.join(d, 'sys.out.txt'), encoding='utf-8-sig', errors='replace').read()
    import re
    m = re.search(r'sample_ms_max=(\S+)', so); smx = m.group(1) if m else '?'
    m = re.search(r'steady_cpu_pct=(\S+)', so); st = m.group(1) if m else '?'
    m = re.search(r'proc=\[([^\]]*)\]', so); pr = m.group(1) if m else 'none'
    m = re.search(r'parts_max_ms=\[([^\]]*)\]', so); pm = m.group(1) if m else ''
    rate = lambda g: (g['cnt'] / g['n'] if g['n'] else float('nan'), g['exc'] / g['n'] if g['n'] else float('nan'))
    rs, rx = rate(snap); os_, ox = rate(oth)
    print(f"{os.path.basename(d)}: proc=[{pr}] frames={len(times)} median={med:.3f} p99={p99:.3f} >8ms={big} sample_ms_max={smx} steady={st}")
    print(f"   rows +-{W}s: snapshot-index rows n={snap['n']} >8ms/row={rs:.2f} excess_ms/row={rx:.1f} | other rows n={oth['n']} >8ms/row={os_:.2f} excess_ms/row={ox:.1f} | ratio={rs / os_ if os_ else float('nan'):.2f}")
    print(f"   5 s phase bins from row 0 (0.5 s each): {phase}")
    print(f"   parts_max_ms=[{pm}]")


for d in sys.argv[1:]:
    try:
        one(d)
    except Exception as ex:
        print(f'{d}: ERROR {ex!r}')
