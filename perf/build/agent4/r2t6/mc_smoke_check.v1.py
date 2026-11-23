#!/usr/bin/env python3
"""READ-ONLY checker. Agent 4, board run 2 task #6: the miss-cache ON smoke for native4 (b2r S18 and S15.2).

usage:
  python build/agent4/r2t6/mc_smoke_check.py --off OFF_RUN --on ON_RUN [--off-trace DIR] [--on-trace DIR]
         [--thrash-s 60] [--out FILE]

OFF_RUN and ON_RUN are run dirs (game.log, plus frames.csv or native-frames.csv) from the same bin and the same
route; only LEGO_NATIVE_SHADER_MISS_CACHE differs. events.tsv is read from --off-trace / --on-trace (each run's
LEGO_NATIVE_TRACE_DIR), else <run>/trace, else <run>. logdiff.py and warntypes.py stay separate: the commands are
printed at the end.

Checks (exit 0 = no FAIL, 1 = a FAIL, 2 = bad input):
  C1 hard  The shaders.cpp warning lines that share g_shader_warning_count (placement missing, unrecognized, cannot
           adopt) and "shader not present in AOT cache", counted by exact text without timestamp and thread:
           ON == OFF.
  C2 soft  frames.csv draw_calls over frames with draws: p10/p50/p90 and the common values (>= 0.5 % of frames).
           SAME or CHECK. Fewer draws in ON is the stale-miss symptom, so look at a CHECK before passing.
  C3 hard  events.tsv unrecognized_shader: the same (guest, stage) set ON vs OFF (needs both traces). Rows per
           frame-with-rows are printed: they should match, while raw counts follow the uncapped fps.
  C4       events.tsv shader_miss_cache_insert: OFF has 0 rows (hard). ON has a row for VS 0xAC449538 (stage 6) and
           PS 0xAC448F28 (stage 7), else NO-ARM: nothing to time in W8a, not a safety fail. The 64-row probe cap
           reached within --thrash-s seconds of the first row = THRASH (a W8a note, not a fail).
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict

VS_GUEST, PS_GUEST = 0xAC449538, 0xAC448F28
# (stage, guest) -> (physical, span, prefix): native2/native3d n0 game.logs and the AOT index (span = the largest
# microcodeSize in the stage's prefix bucket, at least 16). A different physical address is INFO only.
EXPECTED = {
    (6, VS_GUEST): (0xED23D3E0, 408, 0xDCD4AD8441398283),
    (7, PS_GUEST): (0xED23D540, 2024, 0xC77B3ABB6F87ACD9),
}
STAGE = {6: 'VS', 7: 'PS'}
PROBE_CAP = 64
MSG_RE = re.compile(r'\[(warning|error|info|debug|critical)\][^\n]*?Native GPU: (.*)$')
C1_RE = re.compile(r'^(placement (vertex|pixel) shader 0x[0-9A-F]{8} backing .*missing from AOT index'
                   r'|unrecognized (vertex|pixel) shader resource 0x[0-9A-F]{8}'
                   r'|cannot adopt (vertex|pixel) shader 0x[0-9A-F]{8}.*'
                   r'|shader not present in AOT cache, hash=0x[0-9A-F]{16})$')
ADOPTED_RE = re.compile(r'^adopted (vertex|pixel) shader 0x([0-9A-F]{8}), hash=0x([0-9A-F]{16})$')
HASH0 = 'Native GPU shader cache miss: hash=0x0000000000000000'

out_lines = []


def say(text=''):
    out_lines.append(text)
    print(text)


def pick_trace(run, explicit):
    for d in ([explicit] if explicit else []) + [os.path.join(run, 'trace'), run]:
        if d and os.path.isfile(os.path.join(d, 'events.tsv')):
            return os.path.join(d, 'events.tsv')
    return None


def read_log(run):
    path = os.path.join(run, 'game.log')
    c1, adopted, hash0, lines = Counter(), set(), 0, 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            lines += 1
            if HASH0 in line:
                hash0 += 1
            m = MSG_RE.search(line.rstrip('\r\n'))
            if not m:
                continue
            level, msg = m.group(1), m.group(2).strip()
            if C1_RE.match(msg):
                c1[f'[{level}] {msg}'] += 1
            else:
                a = ADOPTED_RE.match(msg)
                if a:
                    adopted.add((a.group(1), a.group(2), a.group(3)))
    return dict(path=path, c1=c1, adopted=adopted, hash0=hash0, lines=lines)


def read_frames(run):
    for name in ('frames.csv', 'native-frames.csv'):
        path = os.path.join(run, name)
        if os.path.isfile(path):
            draws = []
            with open(path, newline='', encoding='utf-8', errors='replace') as f:
                for row in csv.DictReader(f):
                    try:
                        value = int(float(row.get('draw_calls') or 0))
                    except ValueError:
                        continue
                    if value > 0:
                        draws.append(value)
            return path, draws
    return None, []


def details(text):
    tokens, result, i = text.split(), {}, 0
    while i < len(tokens):
        if tokens[i].endswith('=') and i + 1 < len(tokens):
            result[tokens[i][:-1]] = tokens[i + 1]
            i += 2
        else:
            i += 1
    return result


def read_events(path):
    unrec, inserts, kinds, max_frame = defaultdict(list), [], Counter(), 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) < 5 or parts[0] == 'elapsed_ms':
                continue
            try:
                ms, frame = float(parts[0]), int(parts[1])
            except ValueError:
                continue
            kind = parts[2]
            kinds[kind] += 1
            max_frame = max(max_frame, frame)
            if kind == 'unrecognized_shader':
                d = details(parts[4])
                unrec[(int(d.get('stage', -1)), int(d.get('guest', -1)))].append(frame)
            elif kind == 'shader_miss_cache_insert':
                d = details(parts[4])
                inserts.append(dict(ms=ms, frame=frame, anomaly=parts[3], stage=int(d.get('stage', -1)),
                                    guest=int(d.get('guest', -1)), physical=int(d.get('physical', -1)),
                                    span=int(d.get('span', -1)), prefix=int(d.get('prefix', -1))))
    return dict(path=path, unrec=unrec, inserts=inserts, kinds=kinds, max_frame=max_frame)


def pct(values, p):
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))]


def key_name(key):
    stage, guest = key
    return f'{STAGE.get(stage, stage)} 0x{guest & 0xFFFFFFFF:08X}'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--off', required=True)
    ap.add_argument('--on', required=True)
    ap.add_argument('--off-trace')
    ap.add_argument('--on-trace')
    ap.add_argument('--thrash-s', type=float, default=60.0)
    ap.add_argument('--out')
    a = ap.parse_args()
    for run in (a.off, a.on):
        if not os.path.isfile(os.path.join(run, 'game.log')):
            print(f'bad input: no game.log in {run}')
            return 2
    fails, flags = [], []
    say(f'mc_smoke_check  OFF={a.off}  ON={a.on}')

    # C1: warning lines.
    log = {'OFF': read_log(a.off), 'ON': read_log(a.on)}
    say('\nC1 shaders.cpp warning lines (exact text, count OFF / ON):')
    keys = sorted(set(log['OFF']['c1']) | set(log['ON']['c1']))
    for k in keys:
        o, n = log['OFF']['c1'][k], log['ON']['c1'][k]
        say(f'  {"  " if o == n else "!!"} {o:4d} / {n:4d}  {k[:150]}')
    tot = (sum(log['OFF']['c1'].values()), sum(log['ON']['c1'].values()))
    c1_ok = log['OFF']['c1'] == log['ON']['c1']
    say(f'  total {tot[0]} / {tot[1]}; hash=0 lines {log["OFF"]["hash0"]} / {log["ON"]["hash0"]}; '
        f'game.log lines {log["OFF"]["lines"]} / {log["ON"]["lines"]}')
    say(f'  C1 {"PASS" if c1_ok else "FAIL"}')
    if not c1_ok:
        fails.append('C1')
    ad_off, ad_on = log['OFF']['adopted'], log['ON']['adopted']
    say(f'  info: adopted shaders {len(ad_off)} / {len(ad_on)}; OFF-only {len(ad_off - ad_on)}, '
        f'ON-only {len(ad_on - ad_off)} (route timing can explain a few; many OFF-only = look)')

    # C2: draws per frame.
    say('\nC2 draws/frame (frames.csv draw_calls, frames with draws > 0):')
    fr = {}
    for arm, run in (('OFF', a.off), ('ON', a.on)):
        path, draws = read_frames(run)
        fr[arm] = draws
        if path:
            say(f'  {arm:3s} {len(draws):7d} frames  p10/p50/p90 {pct(draws, 10)}/{pct(draws, 50)}/{pct(draws, 90)}'
                f'  max {max(draws) if draws else None}  ({os.path.basename(path)})')
        else:
            say(f'  {arm:3s} no frames.csv / native-frames.csv')
    if fr['OFF'] and fr['ON']:
        same = all(pct(fr['OFF'], p) == pct(fr['ON'], p) for p in (10, 50, 90))
        co, cn = Counter(fr['OFF']), Counter(fr['ON'])
        common = sorted(v for v in set(co) | set(cn)
                        if co[v] >= 0.005 * len(fr['OFF']) or cn[v] >= 0.005 * len(fr['ON']))
        say('  common values (share OFF / ON):')
        for v in common:
            say(f'    {v:6d}  {100.0 * co[v] / len(fr["OFF"]):5.1f}% / {100.0 * cn[v] / len(fr["ON"]):5.1f}%')
        say(f'  C2 {"SAME" if same else "CHECK"}')
        if not same:
            flags.append('C2 CHECK')
    else:
        say('  C2 SKIP (no frames)')
        flags.append('C2 SKIP')

    # C3 and C4: events.tsv.
    tr = {'OFF': pick_trace(a.off, a.off_trace), 'ON': pick_trace(a.on, a.on_trace)}
    ev = {arm: (read_events(p) if p else None) for arm, p in tr.items()}
    for arm in ('OFF', 'ON'):
        e = ev[arm]
        if e:
            top = ', '.join(f'{k} {v}' for k, v in e['kinds'].most_common(6))
            say(f'\n{arm} events.tsv {e["path"]}: last frame {e["max_frame"]}; {top}')
        else:
            say(f'\n{arm} events.tsv: none (no LEGO_NATIVE_TRACE_DIR)')
    if bool(ev['OFF']) != bool(ev['ON']):
        say('  WARNING: trace on one arm only. The trace dir turns off buffer/texture reuse and some draw fast paths,'
            ' so C1/C2 are indicative only.')
        flags.append('one-sided trace')

    say('\nC3 unrecognized_shader (rows, frames with rows, rows per frame-with-rows), OFF | ON:')
    if ev['OFF'] and ev['ON']:
        ku = sorted(set(ev['OFF']['unrec']) | set(ev['ON']['unrec']))
        for k in ku:
            cells = []
            for arm in ('OFF', 'ON'):
                frames = ev[arm]['unrec'].get(k, [])
                nf = len(set(frames))
                cells.append(f'{len(frames):7d} {nf:6d} {len(frames) / nf if nf else 0:5.2f}')
            say(f'  {key_name(k):14s} {cells[0]} | {cells[1]}')
        c3_ok = set(ev['OFF']['unrec']) == set(ev['ON']['unrec'])
        say(f'  C3 {"PASS" if c3_ok else "FAIL"} (same (guest, stage) set)')
        if not c3_ok:
            fails.append('C3')
    else:
        say('  C3 SKIP (needs both traces)')
        flags.append('C3 SKIP')

    say('\nC4 shader_miss_cache_insert:')
    if ev['OFF']:
        n_off = len(ev['OFF']['inserts'])
        say(f'  OFF rows {n_off} -> {"PASS" if n_off == 0 else "FAIL (the OFF arm had the cache ON)"}')
        if n_off:
            fails.append('C4-OFF')
    else:
        say('  OFF: no trace')
    if ev['ON']:
        ins = ev['ON']['inserts']
        by_key = defaultdict(list)
        for r in ins:
            by_key[(r['stage'], r['guest'])].append(r)
        for k in sorted(by_key):
            rows = by_key[k]
            r0 = rows[0]
            exp = EXPECTED.get(k)
            note = ''
            if exp:
                note = ('as expected' if (r0['physical'], r0['span'], r0['prefix']) == exp else
                        f'expected physical 0x{exp[0]:08X} span {exp[1]} prefix 0x{exp[2]:016X}')
            gaps = [b['ms'] - a_['ms'] for a_, b in zip(rows, rows[1:])]
            gap = f'; re-inserts {len(rows) - 1}, median gap {pct(gaps, 50) / 1000.0:.1f} s' if gaps else ''
            say(f'  {key_name(k):14s} rows {len(rows):2d}  physical 0x{r0["physical"] & 0xFFFFFFFF:08X} span '
                f'{r0["span"]} prefix 0x{r0["prefix"] & 0xFFFFFFFFFFFFFFFF:016X}  first {r0["ms"] / 1000.0:.1f} s '
                f'(frame {r0["frame"]}){gap}  {note}')
        anomalies = sum(1 for r in ins if r['anomaly'] != '0')
        if anomalies:
            say(f'  !! {anomalies} insert rows with anomaly != 0')
        armed = all(k in by_key for k in EXPECTED)
        thrash = len(ins) >= PROBE_CAP and (ins[PROBE_CAP - 1]['ms'] - ins[0]['ms']) < a.thrash_s * 1000.0
        say(f'  ON rows {len(ins)} (probe cap {PROBE_CAP}); VS and PS armed: {"yes" if armed else "NO"}'
            f'{"; THRASH: the cap was reached within %.0f s" % a.thrash_s if thrash else ""}')
        if not armed:
            flags.append('C4 NO-ARM (nothing to time)')
        if thrash:
            flags.append('C4 THRASH (W8a note)')
    else:
        say('  ON: no trace, so arming is unknown')
        flags.append('C4 SKIP')

    result = 'FAIL' if fails else 'PASS'
    say(f'\nRESULT: {result}' + (f'  fails: {", ".join(fails)}' if fails else '') +
        (f'  flags: {"; ".join(flags)}' if flags else ''))
    say('Also run (not done here):')
    say(f'  python build\\agent10\\bgate\\logdiff.py --base {a.off} --cand {a.on}   (NEW 0 / MORE 0)')
    say(f'  python build\\agent10\\nb\\warntypes.py --run OFF={a.off} --run ON={a.on}   (equal counts)')
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out_lines) + '\n')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
