"""#33 row 3 post: pair each screenshot with the arm's slow-frame log at that moment (M3).
Usage: python -B row3_post.py [--row3 <dir>] [--arm off=<run dir>] [--arm on=<run dir>] [--selftest]
  --row3   kit dir (default: this script's dir). Reads <row3>/shots/, writes <row3>/post/.
  --arm    run dir per arm; default: the newest <row3>/runs/*-s33-row3-<arm> for off and on.
Shots:
  auto     <row3>/shots/auto/<arm>/index.csv (row3-watch.ps1: file,time,a3d_s,window).
  manual   <row3>/shots/<arm>-<n>.png|jpg (the Overseer's computer-cli screenshots). Time = <row3>/shots/times.csv
           (name,time with 'HH:MM:SS.fff' or 'YYYY-MM-DD HH:MM:SS.fff') if listed, else the file's mtime.
Per shot: the frame on screen ~ the last slow-frame line at or before the shot time ('dropped draws at this moment'),
the max over the last 0.1 s (presentation lags 1-3 frames), and the +-0.5 s window (dropped sum, frames dropping, new
pipelines, resolve-after-drop lines with the (d) bin). A3D = the first 3D frame (row3_log.events 'first-3d').
Outputs: post/shots.csv, post/captions.txt (one line per shot, for the user), post/pairs.txt and post/sbs-*.jpg
(ON | OFF side by side per window: the ON shot with the most drops vs the OFF shot nearest in A3D time; manual
shots paired by <n>). Exit 0 ok, 1 selftest failed, 2 usage.
"""
import argparse, bisect, csv, datetime, glob, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import row3_log

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--row3', default=HERE)
ap.add_argument('--arm', action='append', default=[])
ap.add_argument('--selftest', action='store_true')
a = ap.parse_args()
SCHED = json.load(open(os.path.join(HERE, 'row3-schedule.json'), encoding='utf-8'))


def newest(arm):
    c = sorted(glob.glob(os.path.join(a.row3, 'runs', '*-s33-row3-%s*' % arm)))
    return c[-1] if c else None


def parse_time(s, day):
    s = s.strip()
    for f in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, f)
        except ValueError:
            pass
    for f in ('%H:%M:%S.%f', '%H:%M:%S'):
        try:
            t = datetime.datetime.strptime(s, f).time()
            return datetime.datetime.combine(day, t)
        except ValueError:
            pass
    raise ValueError('bad time %r' % s)


def window_name(rel):
    for w in SCHED['windows']:
        hi = w['to'] if w['kind'] == 'burst' else w['from'] + 0.65
        if w['from'] - 0.05 <= rel <= hi + 0.05:
            return w['name']
    return '-'


def load_shots(arm, day):
    shots = []
    idx = os.path.join(a.row3, 'shots', 'auto', arm, 'index.csv')
    if os.path.exists(idx):
        for r in csv.DictReader(open(idx, encoding='utf-8-sig')):
            shots.append({'file': os.path.join(os.path.dirname(idx), r['file']), 'kind': 'auto', 'n': None,
                          't': parse_time(r['time'], day), 'window': r['window']})
    times = {}
    tc = os.path.join(a.row3, 'shots', 'times.csv')
    if os.path.exists(tc):
        for row in csv.reader(open(tc, encoding='utf-8-sig')):
            if len(row) >= 2 and not row[0].startswith('#') and row[0].lower() != 'name':
                times[row[0].strip().lower()] = row[1]
    for p in sorted(glob.glob(os.path.join(a.row3, 'shots', '%s-*.*' % arm))):
        m = re.match(r'^%s-(\d+)\.(png|jpe?g)$' % arm, os.path.basename(p), re.I)
        if not m:
            continue
        nm = os.path.basename(p).lower()
        t = parse_time(times[nm], day) if nm in times else datetime.datetime.fromtimestamp(os.path.getmtime(p))
        shots.append({'file': p, 'kind': 'manual', 'n': int(m.group(1)), 't': t, 'window': None})
    return shots


def annotate(d, a3d, s):
    fr = d['frames']
    ts = [x[0] for x in fr]
    i = bisect.bisect_right(ts, s['t']) - 1
    now = fr[i] if i >= 0 else None
    near = [x for x in fr if s['t'] - datetime.timedelta(seconds=0.1) <= x[0] <= s['t']]
    w = row3_log.window(d, s['t'] - datetime.timedelta(seconds=0.5), s['t'] + datetime.timedelta(seconds=0.5))
    s['rel'] = (s['t'] - a3d).total_seconds() if a3d else None
    if not s['window']:
        s['window'] = window_name(s['rel']) if s['rel'] is not None else '-'
    s['k_now'] = now[4] if now else 0
    s['frame'] = now[1] if now else None
    s['ms'] = now[2] if now else None
    s['k_near'] = max([x[4] for x in near] or [0])
    s['w'] = w
    return s


def caption(arm, s, rad_on):
    rel = 'A3D%+.2f s' % s['rel'] if s['rel'] is not None else 'A3D ?'
    c = '%s: %s at %s (%s) - dropped draws at this moment: %d (frame #%s, %.1f ms; max in the last 0.1 s: %d); within +-0.5 s: %d in %d frame(s), %d new pipeline(s)' % (
        os.path.basename(s['file']), arm.upper(), rel, s['window'], s['k_now'], s['frame'], s['ms'] or 0.0, s['k_near'],
        s['w']['dropped'], s['w']['frames_dropping'], s['w']['new'])
    if rad_on:
        c += ', %d resolve-after-drop line(s)' % s['w']['rad']
    return c


def sbs(on, off, out, title):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    ims = []
    for s in (on, off):
        if s is None:
            ims.append((Image.new('RGB', (960, 540), (40, 40, 40)), 'no shot'))
            continue
        im = Image.open(s['file']).convert('RGB')
        if im.width > 960:
            im = im.resize((960, round(im.height * 960 / im.width)))
        ims.append((im, '%s %s: dropped now %d (0.1 s max %d), +-0.5 s %d' % (
            'ON' if s is on else 'OFF', 'A3D%+.2f' % s['rel'], s['k_now'], s['k_near'], s['w']['dropped'])))
    h = max(i.height for i, _ in ims) + 44
    canvas = Image.new('RGB', (sum(i.width for i, _ in ims) + 8, h), (0, 0, 0))
    x = 0
    dr = ImageDraw.Draw(canvas)
    for im, lab in ims:
        canvas.paste(im, (x, 44))
        dr.text((x + 6, 24), lab, fill=(255, 255, 0))
        x += im.width + 8
    dr.text((6, 4), title, fill=(255, 255, 255))
    canvas.save(out, quality=88)
    return True


def main():
    arms = dict(x.split('=', 1) for x in a.arm)
    for arm in ('off', 'on'):
        if arm not in arms and newest(arm):
            arms[arm] = newest(arm)
    if not arms:
        print('no runs: give --arm off=<dir> --arm on=<dir> or run the kit first'); return 2
    post = os.path.join(a.row3, 'post'); os.makedirs(post, exist_ok=True)
    caps, rows, per = [], [], {}
    for arm, run in sorted(arms.items(), key=lambda kv: kv[0] != 'on'):
        d = row3_log.parse(run)
        if not d['frames']:
            print('%s: no slow-frame lines in %s' % (arm, run)); return 2
        ev = row3_log.events(d)
        a3d = d['ff'] + datetime.timedelta(seconds=ev['first-3d']) if 'first-3d' in ev else None
        rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig')) if os.path.exists(os.path.join(run, 'run.json')) else {}
        hdr = '== %s %s: FF %s, A3D %s, frames %d, dropped draws total %d, resolve-after-drop lines %d; cvars %s; desktop %s' % (
            arm.upper(), run, d['ff'].strftime('%H:%M:%S.%f')[:-3], a3d.strftime('%H:%M:%S.%f')[:-3] if a3d else '?',
            len(d['frames']), sum(x[4] for x in d['frames']), len(d['rad']), json.dumps(rj.get('cvars')), rj.get('desktop'))
        print(hdr); caps.append(hdr)
        shots = [annotate(d, a3d, s) for s in load_shots(arm, d['ff'].date())]
        shots.sort(key=lambda s: s['t'])
        per[arm] = shots
        for s in shots:
            caps.append(caption(arm, s, bool(d['rad'])))
            rows.append([arm, s['kind'], os.path.basename(s['file']), s['t'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                         '%.3f' % s['rel'] if s['rel'] is not None else '', s['window'], s['frame'], s['k_now'], s['k_near'],
                         s['w']['dropped'], s['w']['frames_dropping'], s['w']['new'], s['w']['rad']])
        caps.append('   %s: %d shot(s), %d with drops in the frame on screen' % (arm.upper(), len(shots), sum(1 for s in shots if s['k_now'] > 0)))
    with open(os.path.join(post, 'shots.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['arm', 'kind', 'file', 'time', 'a3d_s', 'window', 'frame', 'dropped_now', 'dropped_max_0.1s',
                    'dropped_pm0.5s', 'frames_dropping_pm0.5s', 'new_pm0.5s', 'rad_pm0.5s'])
        w.writerows(rows)
    with open(os.path.join(post, 'captions.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(caps) + '\n')
    pairs = []
    on, off = per.get('on', []), per.get('off', [])
    for win in sorted({s['window'] for s in on if s['kind'] == 'auto'}):
        cand = [s for s in on if s['kind'] == 'auto' and s['window'] == win]
        best = max(cand, key=lambda s: (s['k_now'], s['k_near']))
        offc = [s for s in off if s['kind'] == 'auto' and s['rel'] is not None]
        mate = min(offc, key=lambda s: abs(s['rel'] - best['rel'])) if offc else None
        out = os.path.join(post, 'sbs-%s.jpg' % win)
        ok = sbs(best, mate, out, '#33 row 3 %s: ON (no_wait) left | OFF right; same A3D offset' % win)
        pairs.append('%s: ON %s (now %d) | OFF %s (now %d)%s' % (win, os.path.basename(best['file']), best['k_now'],
                     os.path.basename(mate['file']) if mate else '-', mate['k_now'] if mate else 0, ' -> ' + os.path.basename(out) if ok else ''))
    for s in [x for x in on if x['kind'] == 'manual']:
        mate = next((x for x in off if x['kind'] == 'manual' and x['n'] == s['n']), None)
        out = os.path.join(post, 'sbs-manual-%d.jpg' % s['n'])
        ok = sbs(s, mate, out, '#33 row 3 manual shot %d: ON left | OFF right' % s['n'])
        pairs.append('manual %d: ON now %d | OFF %s%s' % (s['n'], s['k_now'], ('now %d' % mate['k_now']) if mate else '-', ' -> ' + os.path.basename(out) if ok else ''))
    with open(os.path.join(post, 'pairs.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(pairs) + '\n')
    print('shots: %s; captions %s; pairs %d' % (', '.join('%s %d' % (k, len(v)) for k, v in per.items()), os.path.join(post, 'captions.txt'), len(pairs)))
    return 0, per


def selftest():
    """Synthetic shots at known frames of two existing runs; checks the pairing end to end."""
    arms = dict(x.split('=', 1) for x in a.arm)
    if set(arms) != {'off', 'on'}:
        print('--selftest needs --arm off=<dir> --arm on=<dir>'); return 2
    from PIL import Image
    if os.path.isdir(os.path.join(a.row3, 'shots')):
        shutil.rmtree(os.path.join(a.row3, 'shots'))
    expect = {}
    for arm, run in arms.items():
        d = row3_log.parse(run)
        ev = row3_log.events(d)
        a3d = d['ff'] + datetime.timedelta(seconds=ev['first-3d'])
        top = max(d['frames'], key=lambda x: x[4])            # the frame with the most dropped draws
        calm = next(x for x in d['frames'] if (x[0] - a3d).total_seconds() > 12 and x[4] == 0)
        sd = os.path.join(a.row3, 'shots', 'auto', arm); os.makedirs(sd, exist_ok=True)
        with open(os.path.join(sd, 'index.csv'), 'w', encoding='ascii', newline='\n') as f:
            f.write('file,time,a3d_s,window\n')
            for j, (fr, win) in enumerate(((top, 'w02-drop576'), (calm, 's10-still12'))):
                t = fr[0] + datetime.timedelta(milliseconds=1)
                nm = '%s_%04d_%s.jpg' % (arm, j + 1, win)
                Image.new('RGB', (320, 180), (20, 60 + 80 * j, 120)).save(os.path.join(sd, nm))
                f.write('%s,%s,%.3f,%s\n' % (nm, t.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], (t - a3d).total_seconds(), win))
        mp = os.path.join(a.row3, 'shots', '%s-1.png' % arm)
        Image.new('RGB', (320, 180), (90, 20, 20)).save(mp)
        ts = (top[0] + datetime.timedelta(milliseconds=1)).timestamp()
        os.utime(mp, (ts, ts))
        expect[arm] = (top[4], top[1])
    r = main()
    if not isinstance(r, tuple):
        return 2
    rc, per = r
    errs = []
    for arm, (k, n) in expect.items():
        auto = {s['window']: s for s in per[arm] if s['kind'] == 'auto'}   # list is time-sorted; pick by window
        man = [s for s in per[arm] if s['kind'] == 'manual']
        hot, calm = auto.get('w02-drop576'), auto.get('s10-still12')
        if not hot or hot['k_now'] != k or hot['frame'] != n:
            errs.append('%s auto shot 1: want dropped %d frame %d, got %s' % (arm, k, n, hot['k_now'] if hot else None))
        if not calm or calm['k_now'] != 0:
            errs.append('%s auto shot 2 (calm): want dropped 0, got %s' % (arm, calm['k_now'] if calm else None))
        if not man or man[0]['k_now'] != k:
            errs.append('%s manual shot (mtime): want dropped %d, got %s' % (arm, k, man[0]['k_now'] if man else None))
    cap = open(os.path.join(a.row3, 'post', 'captions.txt'), encoding='utf-8').read()
    if 'dropped draws at this moment: %d' % expect['on'][0] not in cap:
        errs.append('caption text missing for ON')
    for f in ('sbs-w02-drop576.jpg', 'sbs-manual-1.jpg', 'shots.csv', 'pairs.txt'):
        if not os.path.exists(os.path.join(a.row3, 'post', f)):
            errs.append('missing post/' + f)
    for e in errs:
        print('SELFTEST FAIL: ' + e)
    if not errs:
        print('SELFTEST ok: ON top frame #%d dropped %d, OFF top frame #%d dropped %d; calm shots 0; manual mtime pairing ok; sbs written'
              % (expect['on'][1], expect['on'][0], expect['off'][1], expect['off'][0]))
    return 1 if errs else rc


if __name__ == '__main__':
    if a.selftest:
        sys.exit(selftest())
    r = main()
    sys.exit(r[0] if isinstance(r, tuple) else r)
