# stall_check.py <run dir> [event t_s ...] (M12, session 3): read-only. Does the game advance after a STUCK-LOCK event?
# perf.csv rows are frames; their time axis is the cumulative frame_time_us from the first row, anchored at the
# input.csv first-frame mark (run-relative t_s). Prints frames and fps per window after each event, the game.log line
# rate after it, STUCK-LOCK line times, and input.csv steps after it.
import csv, datetime, glob, json, os, re, sys

run = sys.argv[1]
rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
t0 = datetime.datetime.fromisoformat(rj['started'][:26])
ff = None
steps = []
for row in csv.reader(open(os.path.join(run, 'input.csv'), encoding='utf-8', errors='replace')):
    if len(row) > 3 and row[0] != 't_s':
        steps.append((float(row[0]), row[2], row[3], row[4] if len(row) > 4 else ''))
        if row[2] == 'mark' and row[3] == 'first-frame' and ff is None:
            ff = float(row[0])
ts, acc = [], 0.0
rd = csv.DictReader(open(os.path.join(run, 'perf.csv'), encoding='utf-8', errors='replace'))
for r in rd:
    try:
        acc += float(r['frame_time_us']) / 1e6
    except (ValueError, KeyError):
        continue
    ts.append(acc)
print('run %s: exit %s close %s elapsed %s; first-frame mark %.2f s; perf rows %d spanning %.1f s -> last frame at t %.1f s' % (
    os.path.basename(run), rj.get('exit_code_hex'), rj.get('close_method'), rj.get('elapsed_s'), ff or -1, len(ts), acc,
    (ff or 0) + acc))
LT = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]')
lines = []
for p in sorted(glob.glob(os.path.join(run, 'game*.log'))):
    for line in open(p, encoding='utf-8', errors='replace'):
        m = LT.match(line)
        if m:
            t = (datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') - t0).total_seconds()
            lines.append((t, line.rstrip()))
stuck = sorted(set(round(t, 1) for t, l in lines if 'STUCK-LOCK' in l))
print('STUCK-LOCK line times (s): %s' % stuck)
evs = [float(a) for a in sys.argv[2:]] or stuck[:1]
for e in evs:
    print('--- event at t %.1f s' % e)
    for a, b in ((e - 10, e - 5), (e - 5, e), (e, e + 5), (e + 5, e + 10), (e + 10, e + 20), (e + 20, e + 40), (e + 40, e + 60)):
        n = sum(1 for x in ts if a <= (ff or 0) + x < b)
        print('  frames in [%.0f, %.0f) s: %d (%.1f fps)' % (a, b, n, n / (b - a)))
    after = [(t, l) for t, l in lines if t > e + 0.5]
    print('  game.log lines after the event: %d; last at t %.1f s' % (len(after), after[-1][0] if after else -1))
    for t, l in after[:8]:
        print('    %.1f %s' % (t, l[:200]))
    print('  input.csv rows after the event: %s' % [(s[0], s[1], s[2], s[3][:30]) for s in steps if s[0] > e][:10])
