"""M8 smoke checker for the installed runner improvements (m8-runner-rating.md C08604D8 items 3-10).
Usage: python check_smoke.py <matrix out dir>
"""
import csv, json, math, os, re, sys

out = sys.argv[1]
EVERY = ['nongame_cores', 'game_cores', 'disk_MBps']
SNAP = ['proc_nongame_cores', 'nongame_io_MBps', 'top_cpu', 'top_io']
NEWCOLS = ['kind', 'over8', 'over10', 'over16_7', 'frames_lt_light', 'light_share']
fails = []


def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (': ' + info if info else ''))
    if not ok:
        fails.append(name)


def rj(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


# ---- results.csv (items 3, 4)
with open(os.path.join(out, 'results.csv'), encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
cols = list(rows[0].keys()) if rows else []
check('4 results.csv new columns', all(c in cols for c in NEWCOLS), 'missing=' + ','.join(c for c in NEWCOLS if c not in cols))
for r in rows:
    print('     row: ' + ' '.join(f"{k}={r.get(k, '')}" for k in ['seq', 'arm', 'round', 'kind', 'scored', 'status', 'excluded', 'median_ms', 'over8', 'over10', 'over16_7', 'frames_lt_light', 'light_share', 'flags_excluding', 'flags_info'] if k in r) + ' dir=' + os.path.basename(r.get('run_dir', '')))
warm = [r for r in rows if r.get('kind') == 'warm']
check('3 one warm row, kind=warm scored=False round=0 tag warm1-<arm>', len(warm) == 1 and warm[0].get('scored') == 'False' and warm[0].get('round') == '0' and re.search(r'-warm1-\w+$', warm[0].get('run_dir', '')) is not None,
      f"n={len(warm)} " + (f"scored={warm[0].get('scored')} round={warm[0].get('round')} dir={os.path.basename(warm[0].get('run_dir', ''))}" if warm else ''))
ids = [r.get('arm') for r in rows if r.get('kind') != 'cold']
check('4 new columns filled in scored rows', all(r.get(c, '') != '' for r in rows if r.get('scored') == 'True' for c in NEWCOLS), '')
check('10 nongame_load never in flags_excluding', all('nongame_load' not in r.get('flags_excluding', '') for r in rows), '')
check('3 no arm twice in a row across warm/round-1', all(a != b for a, b in zip(ids, ids[1:])), ' '.join(ids))
ls = [r.get('light_share', '') for r in rows if r.get('light_share')]
check('4 light_share full precision', any(len(x.split('.')[-1]) > 3 for x in ls), ' '.join(ls))
sm = open(os.path.join(out, 'summary.md'), encoding='utf-8-sig').read() if os.path.exists(os.path.join(out, 'summary.md')) else ''
check('3 summary.md shows the warm run as warm', bool(re.search(r'\bwarm\b', sm)), '')

# ---- per run (items 6-10)
rundir = os.path.join(out, 'runs')
for rn in sorted(os.listdir(rundir)):
    d = os.path.join(rundir, rn)
    print(f'--- {rn}')
    # sys.csv
    with open(os.path.join(d, 'sys.csv'), encoding='utf-8-sig', newline='') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split(',')
    data = [l.split(',') for l in lines[1:] if l]
    bad = [i for i, x in enumerate(data) if len(x) != 31]
    check(f'6 {rn} sys.csv 31 cols every row', len(hdr) == 31 and not bad, f'hdr={len(hdr)} rows={len(data)} bad={len(bad)}')
    ci = {c: hdr.index(c) for c in EVERY + SNAP}
    miss_every = sum(1 for x in data if len(x) == 31 and any(x[ci[c]] == '' for c in EVERY))
    snap_rows = [i for i, x in enumerate(data) if len(x) == 31 and all(x[ci[c]] != '' for c in SNAP)]
    snap_any = [i for i, x in enumerate(data) if len(x) == 31 and any(x[ci[c]] != '' for c in SNAP)]
    exp = list(range(0, len(data), 5))
    check(f'6 {rn} every-row cols filled', miss_every == 0, f'rows missing={miss_every}')
    check(f'6 {rn} snapshot cols on rows 0,5,10,... only', snap_any == exp and snap_rows == exp, f'snap rows={snap_any[:12]}{"..." if len(snap_any) > 12 else ""} expected={exp[:12]}')
    # sys.out.txt
    so = open(os.path.join(d, 'sys.out.txt'), encoding='utf-8-sig', errors='replace').read()
    start = next((l for l in so.splitlines() if 'sys-csv: start ' in l), '')
    timing = next((l for l in so.splitlines() if 'sys-csv: timing ' in l), '')
    stop = next((l for l in so.splitlines() if 'sys-csv: stop ' in l), '')
    def kv(line, k):
        m = re.search(r'(?:^|\s)' + re.escape(k) + r'=(\S+)', line)
        return m.group(1) if m else None
    check(f'7 {rn} start line dll cached + proc every=5', 'dll=LdSys-4efd5c91.dll(cached)' in start and 'proc=[every=5' in start,
          (re.search(r'dll=\S+', start).group(0) if 'dll=' in start else 'no dll') + ' ' + (re.search(r'proc=\[[^\]]*\]', start).group(0) if 'proc=[' in start else 'no proc'))
    pf = kv(timing, 'proc_fails'); ps = kv(timing, 'proc_snaps')
    check(f'6 {rn} proc_fails=0', pf == '0', f'proc_snaps={ps} proc_fails={pf}')
    sk = kv(stop, 'skipped'); st = kv(stop, 'steady_cpu_pct'); smx = kv(stop, 'sample_ms_max'); rs = kv(stop, 'reason')
    check(f'8 {rn} stop line: skipped=0 steady<=0.5', sk == '0' and st is not None and float(st) <= 0.5, f'reason={rs} rows={kv(stop, "rows")} skipped={sk} steady_cpu_pct={st}')
    smf = float(smx) if smx else 1e9
    print(('INFO ' if smf < 50 else ('WARN ' if smf <= 200 else 'FAIL ')) + f'8 {rn} sample_ms_max={smx} (target < 50, > 200 -> ProcEvery 0)')
    if smf > 200:
        fails.append(f'8 {rn} sample_ms_max')
    # run.json
    if os.path.exists(os.path.join(d, 'run.json')):
        J = rj(os.path.join(d, 'run.json'))
        def find(o, key, path=''):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == key:
                        yield path + '.' + k, v
                    yield from find(v, key, path + '.' + k)
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    yield from find(v, key, f'{path}[{i}]')
        sl = list(find(J, 'stop_line'))
        check(f'7 {rn} run.json has stop_line', bool(sl) and bool(sl[0][1]), sl[0][0] if sl else 'none')
    else:
        print(f'INFO 7 {rn} no run.json (warm runs may keep it elsewhere)')
    # sys.json flags (item 10)
    if os.path.exists(os.path.join(d, 'sys.json')):
        S = rj(os.path.join(d, 'sys.json'))
        fl = S.get('flags', []); fi = S.get('flags_info', [])
        check(f'10 {rn} nongame_load only in flags_info', 'nongame_load' not in fl, f'flags={fl} flags_info={fi}')
        check(f'8 {rn} no sample_gaps flag', 'sample_gaps' not in fl and 'sample_gaps' not in fi, '')
    # periodicity (item 9): frames > 8 ms folded modulo 5 s (cumulative frame time; no absolute clock needed)
    fr = rj(os.path.join(d, 'frames.json')) if os.path.exists(os.path.join(d, 'frames.json')) else None
    pc = os.path.join(d, 'perf.csv')
    if os.path.exists(pc):
        with open(pc, encoding='utf-8-sig', newline='') as f:
            rd = csv.DictReader(f)
            ft = [float(r['frame_time_us']) for r in rd if r.get('frame_time_us') not in (None, '')]
        t = 0.0; times = []
        # skip the first 5 s of frames (boot/loading), then fold frames > 8 ms
        for x in ft:
            t += x / 1e6
            if t > 5 and x > 8000:
                times.append(t)
        n = len(times)
        if n >= 10:
            for per in (5.0, 1.0, 3.0, 7.0):
                c = sum(math.cos(2 * math.pi * tt / per) for tt in times); s = sum(math.sin(2 * math.pi * tt / per) for tt in times)
                R = math.hypot(c, s) / n; z = n * R * R; p = math.exp(-z) * (1 + (2 * z - z * z) / (4 * n) - (24 * z - 132 * z * z + 76 * z ** 3 - 9 * z ** 4) / (288 * n * n))
                print(f'     9 {rn} period {per:g} s: n>{8}ms={n} of {len(ft)} frames over {t:.0f} s, Rayleigh R={R:.3f} p={max(p, 0):.3g}')
            # bins of the 5 s phase
            bins = [0] * 10
            for tt in times:
                bins[int(((tt % 5.0) / 5.0) * 10) % 10] += 1
            print(f'     9 {rn} 5 s phase bins (0.5 s each): {bins}')
        else:
            print(f'INFO 9 {rn} only {n} frames > 8 ms')

print('RESULT: ' + ('ALL PASS' if not fails else 'FAIL: ' + '; '.join(fails)))
sys.exit(1 if fails else 0)
