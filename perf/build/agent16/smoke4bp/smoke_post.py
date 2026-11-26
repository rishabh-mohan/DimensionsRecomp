#!/usr/bin/env python3
"""smoke_post.py (M16, S5 phase 0.4c): read-only check of a native4bp attract smoke against nativefinal2.

usage:
  smoke_post.py --arm 4bp=RUN_DIR,TRACE_DIR,SHOTS_DIR [--arm nf2=RUN_DIR,TRACE_DIR,SHOTS_DIR]
                --before EVENTS_TSV [--before-log GAME_LOG] [--expect-fp HEX] [--threshold 300] --out REPORT.txt
  smoke_post.py --selftest EVENTS_TSV --out REPORT.txt       (trace parser only, on an old trace)

The first --arm is the bin under test (native4bp). The "before" missing-draw numbers come from the nf2 arm of the
same smoke if given (same env: trace on, miss cache at its default), else from --before (the 0.4a dump run's
trace; there the miss cache was OFF, so per-frame misses can differ slightly).
First 3D (trace time) = the first frame with draw_calls >= --threshold (front end <= 8, the attract load 59-61;
the 3D attract runs 190-6000). The 3D window = every frame from there on.
Checks: clean exit, route ran, fingerprint (4bp != 1616ce65e973c583 and == --expect-fp), first 3D reached with
>= 60 s after it, AOT-miss log lines, trace draw_missing_* in the 3D window (want 0), recorded draws/frame
(after >= before), new warning types vs the before log, screenshots present.
Exit 0 = report written; the RESULT line is PASS, PASS-WITH-CHECKS or FAIL.
"""
import argparse, collections, hashlib, json, os, re, statistics, sys

NF2_FP = '1616ce65e973c583'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def q(v, p):
    s = sorted(v)
    return s[min(len(s) - 1, int(p * len(s)))] if s else 0


def trace(path, th):
    frames = {}                      # frame -> (ms, draw_calls)
    miss = collections.Counter()     # frame -> missing draw events
    guests = collections.Counter()   # (stage, guest) -> events
    first = {}
    with open(path, encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            p = line.rstrip('\r\n').split('\t')
            if len(p) < 5:
                continue
            ev = p[2]
            if ev != 'frame' and not ev.startswith('draw_missing_'):
                continue
            try:
                fr = int(p[1]); ms = float(p[0])
            except ValueError:
                continue
            d = p[4].split()
            if ev == 'frame':
                if 'draw_calls=' in d:
                    try:
                        frames[fr] = (ms, float(d[d.index('draw_calls=') + 1]))
                    except (IndexError, ValueError):
                        pass
            else:
                miss[fr] += 1
                st = 'VS' if 'vertex' in ev else 'PS' if 'pixel' in ev else ev
                k = (st, d[1] if len(d) > 1 else '?')
                guests[k] += 1
                first.setdefault(k, ms)
    r = {'frames': len(frames), 'missing_events_total': sum(miss.values()),
         'guests_total': len(guests)}
    order = sorted(frames)
    f3 = next((fr for fr in order if frames[fr][1] >= th), None)
    if f3 is None:
        return r, guests, first
    t3 = frames[f3][0]
    win = [fr for fr in order if frames[fr][0] >= t3]
    mm = [miss.get(fr, 0) for fr in win]
    dd = [frames[fr][1] for fr in win]
    r.update(first3d_ms=t3, first3d_frame=f3, window_frames=len(win),
             window_s=round((frames[win[-1]][0] - t3) / 1000, 1),
             missing_total=sum(mm), missing_median=statistics.median(mm), missing_p90=q(mm, 0.9),
             frames_with_missing=sum(1 for m in mm if m), draws_median=statistics.median(dd),
             draws_p90=q(dd, 0.9), draws_mean=round(sum(dd) / len(dd), 1),
             submitted_median_est=statistics.median(m + d for m, d in zip(mm, dd)))
    return r, guests, first


def norm_warn(line):
    m = re.match(r'^\[[^\]]*\] \[(warning|warn|error|critical)\] \[(\w+)\] \[t\d+\] (.*)$', line.rstrip('\r\n'))
    if not m:
        return None
    s = re.sub(r'0x[0-9A-Fa-f]+', '0x#', m.group(3))
    s = re.sub(r'\b[0-9A-Fa-f]{8,}\b', '#', s)
    s = re.sub(r'\d+', '#', s)
    s = re.sub(r"'[^']*'", "'*'", s)
    return f'[{m.group(1)}] [{m.group(2)}] {s[:140]}'


def warn_types(path):
    c = collections.Counter()
    if path and os.path.exists(path):
        for line in open(path, encoding='utf-8', errors='replace'):
            k = norm_warn(line)
            if k:
                c[k] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', action='append', default=[])
    ap.add_argument('--before'); ap.add_argument('--before-log'); ap.add_argument('--expect-fp')
    ap.add_argument('--threshold', type=float, default=300); ap.add_argument('--selftest')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = []; fails = []; checks = []
    say = out.append

    def check(ok, name, detail, soft=False):
        tag = 'PASS' if ok else ('CHECK' if soft else 'FAIL')
        say(f'{tag} {name}: {detail}')
        if not ok:
            (checks if soft else fails).append(name)

    if a.selftest:
        r, g, _ = trace(a.selftest, a.threshold)
        say(f'selftest trace {a.selftest}'); say('  ' + json.dumps(r))
        ok = 'first3d_ms' in r and r['frames'] > 0
        say(f'RESULT: selftest {"ok" if ok else "FAILED"}')
        open(a.out, 'w', encoding='utf-8').write('\n'.join(out) + '\n'); print('\n'.join(out))
        return 0 if ok else 1

    arms = []
    for s in a.arm:
        name, _, rest = s.partition('=')
        parts = (rest.split(',') + ['', '', ''])[:3]
        arms.append((name, *parts))
    if not arms:
        print('no --arm'); return 2
    results = {}
    for name, run, tdir, shots in arms:
        say(f'== arm {name}: run {run}')
        is_test = name == arms[0][0]
        rj = os.path.join(run, 'run.json')
        j = {}
        try:
            j = json.load(open(rj, encoding='utf-8-sig'))
        except Exception as e:  # noqa
            check(False, f'{name} run.json', f'unreadable: {e}')
        if j:
            ins = j.get('input_script') or {}
            check(j.get('exit_code') == 0 and not j.get('exited_early') and not j.get('wer_seen')
                  and not j.get('crash_events') and not j.get('dumps') and j.get('close_method') == 'wm_close',
                  f'{name} clean exit', f"exit {j.get('exit_code_hex')} early {j.get('exited_early')} close {j.get('close_method')} "
                  f"{j.get('close_seconds')} s wer {j.get('wer_seen')} crash {len(j.get('crash_events') or [])} dumps {len(j.get('dumps') or [])}")
            check(ins.get('timeouts') == 0 and not ins.get('error'), f'{name} route ran',
                  f"steps {ins.get('steps_done')}/{ins.get('steps_total')} timeouts {ins.get('timeouts')} error {ins.get('error')}")
            say(f"INFO {name} desktop {j.get('desktop')} elapsed {j.get('elapsed_s')} s peak_ws {((j.get('process') or {}).get('peak_ws_mb'))} MB exe {str(j.get('exe_sha256'))[:16]}")
        gl = os.path.join(run, 'game.log')
        fp = None; aot = collections.Counter(); mc = None; lines = 0
        if os.path.exists(gl):
            for line in open(gl, encoding='utf-8', errors='replace'):
                lines += 1
                if fp is None:
                    m = re.search(r'Native GPU \[([0-9a-f]{16})\]', line)
                    if m:
                        fp = m.group(1)
                m = re.search(r'shader not present in AOT cache, hash=0x([0-9A-Fa-f]+)', line)
                if m:
                    aot['create ' + m.group(1).upper()] += 1
                m = re.search(r'placement (vertex|pixel) shader (0x[0-9A-Fa-f]+) .*prefix=(0x[0-9A-Fa-f]+).*missing from AOT index', line)
                if m:
                    aot[f'placement {m.group(1)} {m.group(2)} {m.group(3)}'] += 1
                if 'shader miss cache' in line and mc is None:
                    mc = line.split('Native GPU:')[-1].strip()[:80]
        else:
            check(False, f'{name} game.log', 'missing')
        if is_test:
            check(bool(fp) and fp != NF2_FP and (not a.expect_fp or fp == a.expect_fp.lower()), f'{name} fingerprint',
                  f'{fp} (must differ from nativefinal2 {NF2_FP}{"; expected " + a.expect_fp if a.expect_fp else ""})')
            check(not aot, f'{name} AOT-miss log lines', f'{sum(aot.values())} lines, {len(aot)} unique' +
                  ''.join(f'\n    {k} x{n}' for k, n in aot.most_common(20)), soft=bool(aot) and all(k.startswith('create ') for k in aot))
        else:
            check(fp == NF2_FP, f'{name} fingerprint', f'{fp} (want {NF2_FP})')
            say(f'INFO {name} AOT-miss log lines: {sum(aot.values())} ({len(aot)} unique)')
        say(f'INFO {name} miss cache line: {mc}; game.log {lines} lines')
        r = {}
        ev = os.path.join(tdir, 'events.tsv') if tdir else ''
        if ev and os.path.exists(ev):
            r, g, first = trace(ev, a.threshold)
            say(f'INFO {name} trace: ' + json.dumps(r))
            if 'first3d_ms' in r:
                check(r['first3d_ms'] <= 200000 and r['window_s'] >= 60, f'{name} first 3D',
                      f"trace {r['first3d_ms'] / 1000:.1f} s (frame {r['first3d_frame']}), {r['window_s']} s of 3D after it")
            else:
                check(False, f'{name} first 3D', f'no frame with draw_calls >= {a.threshold:g}')
            if is_test:
                for (st, k), n in g.most_common(30):
                    try:
                        k2 = f'0x{int(k):08X}'
                    except ValueError:
                        k2 = k
                    say(f'    still missing {st} guest {k2}: {n} events (whole run), first {first.get((st, k), 0) / 1000:.1f} s')
        else:
            check(False, f'{name} trace', f'no events.tsv in {tdir}')
        n_shots = []
        if shots and os.path.isdir(shots):
            n_shots = sorted(f for f in os.listdir(shots) if f.lower().endswith(('.png', '.jpg')))
        check(len(n_shots) >= 3, f'{name} screenshots', f'{len(n_shots)} in {shots}' +
              ''.join(f'\n    {f} {sha(os.path.join(shots, f))[:16]}' for f in n_shots), soft=True)
        results[name] = (r, fp, warn_types(gl))

    test = arms[0][0]
    rt = results[test][0]
    ref = next((n for n, *_ in arms if n != test), None)
    if ref and 'first3d_ms' in results[ref][0]:
        rb, src = results[ref][0], f'arm {ref} (same smoke)'
        wb = results[ref][2]
    elif a.before and os.path.exists(a.before):
        rb, _, _ = trace(a.before, a.threshold); src = f'0.4a dump trace {a.before} (miss cache OFF there)'
        wb = warn_types(a.before_log)
    else:
        rb, src, wb = {}, 'none', collections.Counter()
    say(f'== before vs after (before = {src})')
    if 'first3d_ms' in rb and 'first3d_ms' in rt:
        say(f"  before: 3D from {rb['first3d_ms'] / 1000:.1f} s, {rb['window_frames']} frames; missing/frame median "
            f"{rb['missing_median']:g} p90 {rb['missing_p90']:g}, total {rb['missing_total']}, frames with misses "
            f"{rb['frames_with_missing']}; recorded draws/frame median {rb['draws_median']:g} (mean {rb['draws_mean']})")
        say(f"  after : 3D from {rt['first3d_ms'] / 1000:.1f} s, {rt['window_frames']} frames; missing/frame median "
            f"{rt['missing_median']:g} p90 {rt['missing_p90']:g}, total {rt['missing_total']}, frames with misses "
            f"{rt['frames_with_missing']}; recorded draws/frame median {rt['draws_median']:g} (mean {rt['draws_mean']})")
        check(rt['missing_total'] == 0, 'missing draws in the 3D window (after)',
              f"{rt['missing_total']} (before {rb['missing_total']})", soft=0 < rt['missing_total'] < 0.01 * max(1, rb['missing_total']))
        check(rt['draws_median'] >= rb['draws_median'], 'recorded draws/frame median after >= before',
              f"{rt['draws_median']:g} vs {rb['draws_median']:g} (scene mix differs per run: soft)", soft=True)
    else:
        check(False, 'before/after comparison', 'a 3D window is missing in one of the traces')
    new = sorted(set(results[test][2]) - set(wb))
    check(not new, 'no new warning types vs before', f'{len(new)} new' + ''.join(f'\n    {k} x{results[test][2][k]}' for k in new[:25]), soft=True)
    verdict = 'FAIL: ' + '; '.join(fails) if fails else ('PASS-WITH-CHECKS: ' + '; '.join(checks) if checks else 'PASS')
    say(f'RESULT: {verdict}')
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
