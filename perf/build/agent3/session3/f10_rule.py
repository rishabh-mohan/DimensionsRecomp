"""f10_rule.py - M3 (session 3, S3T-3): the finding-10 rule (SESSION2 L3128-3132) on one or more run dirs.

A STUCK-LOCK event is WARN (finding 10, known, self-recovering) only if ALL hold:
  1. critical section 0x84959EDC
  2. the owner is parked in sub_83FAF180 at lr 83FAF188 or 83FAF200
  3. the waiter's first caller is lr 82A2A270
  4. it self-recovers: frames advance for >= 10 s after the event (perf.csv bytes grow between two input.csv steps
     >= 10 s apart from the event on; M10 review S2 - a later game.log line is not enough). If no such step pair
     exists (route inside a wait_log, M12 02:07): perf.csv frames (one row per frame) advance for >= 10 s after
     the frame in progress at the event, at >= max(2, half the pre-event 10 s count) frames (see perf_frames)
and the run has no crash (run.json exit_code 0, wer_seen false, crash_events empty) and reaches the level
(input.csv mark 'vortex'). Any other event, or a crash, or no level -> FAIL. No event (+ no crash, level) -> PASS.
s4b_check.py only tests the owner lr range 83FAF180-83FAF25F; this is the strict rule.

Usage: python -B f10_rule.py <run dir> [<run dir> ...] [--json out.json] [--no-level]
  --no-level: do not require the 'vortex' mark (menu routes).
Exit: 0 = all PASS, 1 = any WARN (no FAIL), 2 = any FAIL, 4 = error. Read-only on run dirs.
"""
import csv
import datetime
import json
import os
import re
import sys

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
CS = re.compile(r'STUCK-LOCK: critical section 0x([0-9a-fA-F]+)')
OWNER = re.compile(r'STUCK-LOCK: the owner is tid (0x[0-9a-fA-F]+).*?parked at lr=([0-9A-Fa-f]+)')
WAITER = re.compile(r"STUCK-LOCK: waiter's callers: lr=([0-9A-Fa-f]+)")
DUMP = re.compile(r'Minidump written to (hang-\d+\.dmp)')
OWNER_LR_OK = ('83FAF188', '83FAF200')
WAITER_LR_OK = '82A2A270'
CS_OK = '84959EDC'


def ts(line):
    m = TS.match(line)
    return datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') if m else None


def log_lines(run):
    names = sorted(n for n in os.listdir(run) if re.match(r'game(\.\d+)?\.log$', n))
    # rotated logs: game.N.log are older than game.log; sort by first timestamp
    out = []
    for n in names:
        with open(os.path.join(run, n), encoding='utf-8', errors='replace') as f:
            for line in f:
                t = ts(line)
                if t:
                    out.append((t, line.rstrip('\n')))
    out.sort(key=lambda x: x[0])
    return out


def marks(run):
    p = os.path.join(run, 'input.csv')
    if not os.path.exists(p):
        return []
    with open(p, newline='', encoding='utf-8-sig') as f:
        return [(float(r['t_s']), r['args']) for r in csv.DictReader(f) if r.get('cmd') == 'mark']


def steps(run):
    # every input.csv step: (t_s from the harness start, perf.csv bytes, pad reads) - the game's progress over time
    p = os.path.join(run, 'input.csv')
    if not os.path.exists(p):
        return []
    out = []
    with open(p, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            try:
                out.append((float(r['t_s']), int(r.get('perf_bytes') or -1), int(r.get('pad_reads') or -1)))
            except ValueError:
                pass
    return out


def perf_frames(run, t_rel, st):
    # M12 (02:07): when no input.csv step pair follows the event (the route sits in a wait_log), judge recovery
    # from perf.csv itself. One row per frame, frame_time_us = that frame's wall time, so the end time of row k is
    # (anchor step time) + (sum of frame times since the anchor row). Anchor = last input.csv step at or before
    # t_rel, located in perf.csv by its perf_bytes. e = the frame in progress at the event (ends after t_rel; a
    # stall shows as its long frame time). Recovered = the rows after e cover >= 10 s and hold at least
    # max(2, half) as many frames as the 10 s before the event. A hang until close never writes e or later.
    p = os.path.join(run, 'perf.csv')
    anc = [x for x in st if x[1] >= 0 and x[0] <= t_rel]
    if not os.path.exists(p) or not anc:
        return None, 'perf.csv frame fallback: no perf.csv or no anchor step'
    t_a, b_a = anc[-1][0], anc[-1][1]
    with open(p, 'rb') as f:
        data = f.read()
    hdr = data.find(b'\n') + 1
    row0 = data.count(b'\n', hdr, max(hdr, b_a))  # data rows complete at the anchor
    ft = []
    for ln in data[hdr:].split(b'\n'):
        try:
            ft.append(int(ln.split(b',', 1)[0]) / 1e6)
        except ValueError:
            pass
    t, e = t_a, None
    ends = []
    for k in range(row0, len(ft)):
        t += ft[k]
        ends.append((k, t))
        if e is None and t > t_rel:
            e = k
    if e is None:
        return False, 'perf.csv frame fallback: no frame ends after the event (anchor %.0f s, row %d)' % (t_a, row0)
    t_e = dict(ends)[e]
    post = [k for k, tk in ends if k > e and tk <= t_e + 10]
    covered = sum(ft[k] for k in range(e + 1, len(ft)))
    # pre pace: frames ending in [t_rel - 10, t_rel], walking back from e with the same per-frame times
    pre, tb = 0, t_e - ft[e]
    for k in range(e - 1, -1, -1):
        if tb < t_rel - 10:
            break
        pre += 1
        tb -= ft[k]
    need = max(2, pre // 2)
    ok = covered >= 10 and len(post) >= need
    return ok, ('perf.csv frame fallback (no step pair; anchor %.0f s row %d): frame at the event %d ends %.1f s '
                '(%.2f s long); next 10 s: %d frames (need >= %d; pre-event 10 s: %d); rows after cover %.1f s'
                % (t_a, row0, e, t_e, ft[e], len(post), need, pre, covered))


def check(run, need_level=True):
    rj = {}
    p = os.path.join(run, 'run.json')
    if os.path.exists(p):
        with open(p, encoding='utf-8-sig') as f:
            rj = json.load(f)
    lines = log_lines(run)
    events = []
    for i, (t, line) in enumerate(lines):
        if 'STUCK-LOCK' not in line:
            continue
        if events and (t - events[-1]['t_last']).total_seconds() <= 3:
            ev = events[-1]
        else:
            ev = {'t0': t, 't_last': t, 'cs': None, 'owner_tid': None, 'owner_lr': None, 'waiter_lr': None,
                  'dump': None, 'i_last': i}
            events.append(ev)
        ev['t_last'], ev['i_last'] = t, i
        for rx, keys in ((CS, ('cs',)), (OWNER, ('owner_tid', 'owner_lr')), (WAITER, ('waiter_lr',))):
            m = rx.search(line)
            if m:
                for k, v in zip(keys, m.groups()):
                    ev[k] = v.upper() if k != 'owner_tid' else v
    start = rj.get('started_epoch_s')
    mk = marks(run)
    st = steps(run)
    for ev in events:
        end = ev['t_last']
        for t, line in lines[ev['i_last'] + 1:]:
            if (t - ev['t_last']).total_seconds() > 15:
                break
            m = DUMP.search(line)
            if m:
                ev['dump'], end = m.group(1), t
                break
        nxt = next(((t, line) for t, line in lines if t > end and 'STUCK-LOCK' not in line and not DUMP.search(line)), None)
        ev['next_line'] = (nxt[0].strftime('%H:%M:%S.%f')[:-3] + ' ' + nxt[1][-120:]) if nxt else None
        ev['next_mark'] = None
        # M10 review S2 (01:58): a later log line is not recovery (the detector logs no "acquired" line, and the
        # WM_CLOSE shutdown lines come after any stall). Recovered = frames advance for >= 10 s after the event:
        # perf.csv bytes grow between two input.csv steps >= 10 s apart from the event on.
        ev['recovered'] = False
        ev['progress'] = None
        if start:
            # input.csv t_s is from the harness start (about started_epoch_s); log stamps are local time
            t_rel = ev['t0'].timestamp() - float(start)
            ev['t_rel_s'] = round(t_rel, 1)
            later = [(s, a) for s, a in mk if s > t_rel]
            ev['next_mark'] = '%s @ %.0f s' % (later[0][1], later[0][0]) if later else None
            ok_st = [x for x in st if x[1] >= 0]
            # baseline: the first step after t0 (the stall is already on at t0), else the last step at most 15 s before
            # t0 (an older baseline would count frames from before the stall); then the first step >= 10 s later
            b = next((x for x in ok_st if x[0] > t_rel), None)
            a = next((x for x in ok_st if b and x[0] >= b[0] + 10), None)
            if a is None:
                prev = [x for x in ok_st if t_rel - 15 <= x[0] <= t_rel]
                b = prev[-1] if prev else None
                a = next((x for x in ok_st if b and x[0] >= t_rel + 10), None)
            if b and a:
                ev['recovered'] = a[1] > b[1]
                ev['progress'] = 'perf.csv bytes %d @ %.0f s -> %d @ %.0f s; pad reads %d -> %d' % (b[1], b[0], a[1], a[0], b[2], a[2])
            else:
                ok, ev['progress'] = perf_frames(run, t_rel, ok_st)
                ev['recovered'] = bool(ok)
        why = []
        if ev['cs'] != CS_OK:
            why.append('cs %s != %s' % (ev['cs'], CS_OK))
        if ev['owner_lr'] not in OWNER_LR_OK:
            why.append('owner lr %s not in %s' % (ev['owner_lr'], '/'.join(OWNER_LR_OK)))
        if ev['waiter_lr'] != WAITER_LR_OK:
            why.append('waiter lr %s != %s' % (ev['waiter_lr'], WAITER_LR_OK))
        if not ev['recovered']:
            why.append('frames did not advance for >= 10 s after the event (did not self-recover: %s)' % ev['progress'])
        ev['finding10'] = not why
        ev['why'] = why
        ev['t0'] = ev['t0'].strftime('%H:%M:%S.%f')[:-3]
        del ev['t_last'], ev['i_last']
    crash = []
    if rj:
        if rj.get('exit_code') not in (0, None):
            crash.append('exit_code %s' % rj.get('exit_code_hex', rj.get('exit_code')))
        if rj.get('wer_seen'):
            crash.append('wer_seen')
        if rj.get('crash_events'):
            crash.append('crash_events %d' % len(rj['crash_events']))
    else:
        crash.append('no run.json')
    names = [a for _s, a in mk]
    level = 'vortex' in names
    fails = [e for e in events if not e['finding10']]
    if crash or fails or (need_level and not level):
        verdict = 'FAIL'
    elif events:
        verdict = 'WARN'
    else:
        verdict = 'PASS'
    return {'run': os.path.basename(os.path.normpath(run)), 'verdict': verdict, 'events': events, 'crash': crash,
            'level': level, 'marks': names, 'elapsed_s': rj.get('elapsed_s'), 'exit': rj.get('exit_code_hex'),
            'close_method': rj.get('close_method')}


def main(argv):
    out_json, need_level, runs = None, True, []
    it = iter(argv)
    for a in it:
        if a == '--json':
            out_json = next(it)
        elif a == '--no-level':
            need_level = False
        else:
            runs.append(a)
    if not runs:
        print(__doc__)
        return 4
    res = []
    for r in runs:
        try:
            res.append(check(r, need_level))
        except Exception as e:  # noqa: BLE001
            print('ERROR %s: %s' % (r, e))
            return 4
    for r in res:
        print('%s: %s  (events %d, level %s, crash %s, exit %s, close %s, elapsed %s s)' % (
            r['run'], r['verdict'], len(r['events']), r['level'], r['crash'] or 'none', r['exit'], r['close_method'],
            r['elapsed_s']))
        for e in r['events']:
            print('  event %s (t %s s): cs %s owner %s lr %s waiter lr %s dump %s recovered %s -> %s%s' % (
                e['t0'], e.get('t_rel_s'), e['cs'], e['owner_tid'], e['owner_lr'], e['waiter_lr'], e['dump'],
                e['recovered'], 'finding 10' if e['finding10'] else 'NOT finding 10: ' + '; '.join(e['why']),
                ('; next mark ' + e['next_mark']) if e['next_mark'] else ''))
            print('    progress: %s' % e.get('progress'))
    v = [r['verdict'] for r in res]
    print('RESULT: %s' % ('FAIL' if 'FAIL' in v else 'WARN' if 'WARN' in v else 'PASS'))
    if out_json:
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=1)
    return 2 if 'FAIL' in v else 1 if 'WARN' in v else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
