#!/usr/bin/env python3
"""READ-ONLY checker. Agent 4, board run 2: the miss-cache ON smoke for native4 (b2r S18 and S15.2).
v1 = task #6. v2 = task #25: C3 pairs heap-address shader keys by stage, rows per frame and time window instead of
requiring the same key set; fixed addresses still match exactly; unmatched keys are listed with the reason.

usage:
  python build/agent4/r2t6/mc_smoke_check.py --off OFF_RUN --on ON_RUN [--off-trace DIR] [--on-trace DIR]
         [--thrash-s 60] [--c3-window-s 10] [--c3-rpf-tol 0.10] [--fixed HEX[,HEX...]] [--out FILE]

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
  C3 hard  events.tsv unrecognized_shader keys (stage, guest), OFF vs ON (needs both traces).
           - A key seen in both arms matches itself (exact).
           - Fixed addresses match only themselves: the placement VS 0xAC449538 and PS 0xAC448F28, plus any --fixed
             address (any stage). A fixed key seen in one arm only stays unmatched.
           - Any other key seen in one arm only is a heap address, which moves between processes (r6: PS 0xAB13F250
             in OFF is PS 0xABB69980 in ON). Each OFF-only heap key is paired one-to-one with an ON-only key of the
             same stage whose rows per frame-with-rows differ by at most --c3-rpf-tol (relative) and whose first and
             last rows are both within --c3-window-s seconds once the ON times are shifted by the median first-row
             offset of the exact keys (elapsed_ms starts at each process's first probe call). The matching is
             maximal; candidates are tried cheapest first (first-row gap + last-row gap in s + 10 x rows/frame gap).
           PASS = no unmatched key. Rows per frame of exact keys are printed, not compared: route timing moves them
           (r6: up to 14 %), and raw counts follow the uncapped fps.
  C4       events.tsv shader_miss_cache_insert: OFF has 0 rows (hard). ON has a row for VS 0xAC449538 (stage 6) and
           PS 0xAC448F28 (stage 7), else NO-ARM: nothing to time in W8a, not a safety fail. The 64-row probe cap
           reached within --thrash-s seconds of the first row = THRASH (a W8a note, not a fail).
"""
import argparse
import csv
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

VERSION = 'v2'
VS_GUEST, PS_GUEST = 0xAC449538, 0xAC448F28
# (stage, guest) -> (physical, span, prefix): native2/native3d n0 game.logs and the AOT index (span = the largest
# microcodeSize in the stage's prefix bucket, at least 16). A different physical address is INFO only.
EXPECTED = {
    (6, VS_GUEST): (0xED23D3E0, 408, 0xDCD4AD8441398283),
    (7, PS_GUEST): (0xED23D540, 2024, 0xC77B3ABB6F87ACD9),
}
STAGE = {6: 'VS', 7: 'PS'}
PROBE_CAP = 64
PARTNER_JACCARD = 0.9  # C3 info only: exact keys whose frame sets overlap a heap pair's this much in both arms
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


def new_stats():
    return dict(rows=0, frames=set(), first=None, last=None)


def read_events(path):
    unrec, inserts, kinds, max_frame = defaultdict(new_stats), [], Counter(), 0
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
                s = unrec[(int(d.get('stage', -1)), int(d.get('guest', -1)))]
                s['rows'] += 1
                s['frames'].add(frame)
                if s['first'] is None or ms < s['first']:
                    s['first'] = ms
                if s['last'] is None or ms > s['last']:
                    s['last'] = ms
            elif kind == 'shader_miss_cache_insert':
                d = details(parts[4])
                inserts.append(dict(ms=ms, frame=frame, anomaly=parts[3], stage=int(d.get('stage', -1)),
                                    guest=int(d.get('guest', -1)), physical=int(d.get('physical', -1)),
                                    span=int(d.get('span', -1)), prefix=int(d.get('prefix', -1))))
    return dict(path=path, unrec=dict(unrec), inserts=inserts, kinds=kinds, max_frame=max_frame)


def pct(values, p):
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))]


def key_name(key):
    stage, guest = key
    return f'{STAGE.get(stage, stage)} 0x{guest & 0xFFFFFFFF:08X}'


def rows_per_frame(s):
    return s['rows'] / len(s['frames']) if s and s['frames'] else 0.0


def overlap(a, b):
    """Jaccard index of two frame sets."""
    inter = len(a & b)
    union = len(a) + len(b) - inter
    return inter / union if union else 0.0


def span_text(s, shift=0.0):
    return f'{s["first"] / 1000.0 + shift:.1f}-{s["last"] / 1000.0 + shift:.1f} s'


def match_c3(uo, un, fixed, window_s, rpf_tol):
    """C3 v2. uo / un: (stage, guest) -> stats for OFF / ON. Returns the exact keys, the time-base offset (s),
    the heap pairs (off key, on key, gaps, candidate count, partner keys) and the unmatched keys with reasons."""
    exact = sorted(set(uo) & set(un))
    offset = statistics.median([(uo[k]['first'] - un[k]['first']) / 1000.0 for k in exact]) if exact else 0.0
    only = {'OFF': sorted(set(uo) - set(un)), 'ON': sorted(set(un) - set(uo))}
    pool = {arm: [k for k in keys if k[1] not in fixed] for arm, keys in only.items()}

    def dist(o, n):  # OFF key, ON key -> (relative rows/frame gap, first-row gap s, last-row gap s, cost)
        ro, rn = rows_per_frame(uo[o]), rows_per_frame(un[n])
        drel = abs(ro - rn) / max(ro, rn) if max(ro, rn) > 0 else 0.0
        dfirst = abs(uo[o]['first'] / 1000.0 - un[n]['first'] / 1000.0 - offset)
        dlast = abs(uo[o]['last'] / 1000.0 - un[n]['last'] / 1000.0 - offset)
        return drel, dfirst, dlast, dfirst + dlast + 10.0 * drel

    def fits(d):
        return d[0] <= rpf_tol and d[1] <= window_s and d[2] <= window_s

    cands = {}
    for o in pool['OFF']:
        found = []
        for n in pool['ON']:
            if n[0] == o[0]:
                d = dist(o, n)
                if fits(d):
                    found.append((d[3], n))
        if found:
            cands[o] = sorted(found)
    match_on = {}  # ON key -> OFF key

    def augment(o, seen):  # Kuhn's augmenting path, cheapest candidate first
        for _, n in cands[o]:
            if n not in seen:
                seen.add(n)
                if n not in match_on or augment(match_on[n], seen):
                    match_on[n] = o
                    return True
        return False

    for o in sorted(cands, key=lambda k: (cands[k][0][0], k)):
        augment(o, set())
    mate = {('OFF', o): n for n, o in match_on.items()}
    mate.update({('ON', n): o for n, o in match_on.items()})

    def partners(o, n):
        return [e for e in exact if overlap(uo[o]['frames'], uo[e]['frames']) >= PARTNER_JACCARD
                and overlap(un[n]['frames'], un[e]['frames']) >= PARTNER_JACCARD]

    def reason(arm, k):
        if k[1] in fixed:
            return 'fixed address, never paired'
        other = 'ON' if arm == 'OFF' else 'OFF'
        opts = [m for m in pool[other] if m[0] == k[0]]
        if not opts:
            return f'no {other}-only {STAGE.get(k[0], k[0])} key to pair with'
        scored = [((dist(k, m) if arm == 'OFF' else dist(m, k)), m) for m in opts]
        d, m = min(scored, key=lambda x: (not fits(x[0]), x[0][3], x[1]))
        why = (f'closest {key_name(m)}: rows/frame off by {100.0 * d[0]:.1f} %, first row by {d[1]:.1f} s, '
               f'last row by {d[2]:.1f} s')
        if fits(d) and (other, m) in mate:
            why += f' (within limits, but paired with {key_name(mate[(other, m)])})'
        return why

    pairs = [(o, n, dist(o, n), len(cands[o]), partners(o, n))
             for o, n in sorted((o, n) for n, o in match_on.items())]
    unmatched = {arm: [(k, reason(arm, k)) for k in keys if (arm, k) not in mate] for arm, keys in only.items()}
    return dict(exact=exact, offset=offset, pairs=pairs, unmatched=unmatched)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--off', required=True)
    ap.add_argument('--on', required=True)
    ap.add_argument('--off-trace')
    ap.add_argument('--on-trace')
    ap.add_argument('--thrash-s', type=float, default=60.0)
    ap.add_argument('--c3-window-s', type=float, default=10.0,
                    help='C3: max first-row and last-row gap of a heap pair, in s after the offset (10)')
    ap.add_argument('--c3-rpf-tol', type=float, default=0.10,
                    help='C3: max relative rows-per-frame gap of a heap pair (0.10)')
    ap.add_argument('--fixed', help='C3: more fixed guest addresses, comma-separated hex; never paired')
    ap.add_argument('--out')
    a = ap.parse_args()
    for run in (a.off, a.on):
        if not os.path.isfile(os.path.join(run, 'game.log')):
            print(f'bad input: no game.log in {run}')
            return 2
    fixed = {VS_GUEST, PS_GUEST}
    for tok in (a.fixed or '').split(','):
        tok = tok.strip()
        if tok:
            try:
                fixed.add(int(tok, 16))
            except ValueError:
                print(f'bad input: --fixed {tok!r} is not a hex address')
                return 2
    if a.c3_window_s < 0 or a.c3_rpf_tol < 0:
        print('bad input: --c3-window-s and --c3-rpf-tol must be >= 0')
        return 2
    fails, flags = [], []
    say(f'mc_smoke_check {VERSION}  OFF={a.off}  ON={a.on}')

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

    say('\nC3 unrecognized_shader (rows, frames with rows, rows per frame-with-rows), OFF | ON '
        '(tag: blank = same key, ~ = heap pair, !! = unmatched):')
    if ev['OFF'] and ev['ON']:
        uo, un = ev['OFF']['unrec'], ev['ON']['unrec']
        c3 = match_c3(uo, un, fixed, a.c3_window_s, a.c3_rpf_tol)
        off = c3['offset']
        paired = {k for p in c3['pairs'] for k in p[:2]}
        for k in sorted(set(uo) | set(un)):
            tag = '  ' if k in uo and k in un else '~ ' if k in paired else '!!'
            cells = []
            for s in (uo.get(k), un.get(k)):
                rows, nf = (s['rows'], len(s['frames'])) if s else (0, 0)
                cells.append(f'{rows:7d} {nf:6d} {rows / nf if nf else 0:5.2f}')
            say(f'  {tag} {key_name(k):14s} {cells[0]} | {cells[1]}')
        n_ex = len(c3['exact'])
        say(f'  exact keys (same stage and address in both arms): {n_ex}')
        say(f'  time-base offset OFF - ON: {off:+.2f} s ' +
            (f'(median first-row difference over {n_ex} exact keys)' if n_ex else '(no exact keys, none applied)'))
        fixed_txt = ', '.join(f'0x{g:08X}' for g in sorted(fixed))
        say(f'  heap pairs (same stage, rows/frame within {100.0 * a.c3_rpf_tol:g} %, first and last row within '
            f'{a.c3_window_s:g} s after the offset; never paired: {fixed_txt}): {len(c3["pairs"])}')
        for o, n, d, ncand, mates in c3['pairs']:
            so, sn = uo[o], un[n]
            mtxt = ', '.join(key_name(e) for e in mates[:4]) + (f' +{len(mates) - 4}' if len(mates) > 4 else '')
            say(f'    {key_name(o)} -> {key_name(n)}  rows/frame {rows_per_frame(so):.2f} / {rows_per_frame(sn):.2f}'
                f'  OFF {span_text(so)}, ON {span_text(sn)} (aligned {span_text(sn, off)})  candidates {ncand}'
                f'  partners {mtxt or "none"}')
        for arm, stats in (('OFF', uo), ('ON', un)):
            items = c3['unmatched'][arm]
            say(f'  unmatched {arm}-only keys: {len(items)}')
            for k, why in items:
                s = stats[k]
                al = f' (aligned {span_text(s, off)})' if arm == 'ON' else ''
                say(f'    !! {key_name(k):14s} rows {s["rows"]} frames {len(s["frames"])} rows/frame '
                    f'{rows_per_frame(s):.2f}  {arm} {span_text(s)}{al}: {why}')
        n_un = sum(len(v) for v in c3['unmatched'].values())
        c3_ok = n_un == 0
        say(f'  C3 {"PASS" if c3_ok else "FAIL"} ({n_ex} exact, {len(c3["pairs"])} heap pairs, {n_un} unmatched)')
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
