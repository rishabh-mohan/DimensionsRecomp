#!/usr/bin/env python3
"""Self-test for mc_smoke_check.py on synthetic runs (writes only under build/agent4/r2t6/selftest).
v1 = task #6 (7 cases). v2 = task #25: adds the C3 heap-address pairing cases."""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'selftest')
CHECK = os.path.join(HERE, 'mc_smoke_check.py')
TS = '[2026-11-22 04:52:19.516] [warning] [core] [t95192] Native GPU: '
VS_P = ('placement vertex shader 0xAC449538 backing 0xED23D3E0 prefix=0xDCD4AD8441398283 '
        'words=F2556004 600A1200 12000000 00006010 missing from AOT index')
PS_P = ('placement pixel shader 0xAC448F28 backing 0xED23D540 prefix=0xC77B3ABB6F87ACD9 '
        'words=00000000 00000000 00000000 00000000 missing from AOT index')
VS_U, PS_U = 'unrecognized vertex shader resource 0xAC449538', 'unrecognized pixel shader resource 0xAC448F28'
INS_VS = 'stage= 6 guest= 2890175800 physical= 3978548192 span= 408 prefix= 15912534166948381315 '
INS_PS = 'stage= 7 guest= 2890174248 physical= 3978548544 span= 2024 prefix= 14374147212387527897 '
# Heap-address keys from Agent 3's r6 pair: OFF address -> ON address.
H_VS_OFF, H_VS_ON, H_PS_OFF, H_PS_ON = 0xA7E1F740, 0xA7E44490, 0xAB13F250, 0xABB69980


def game_log(placement_ps=4):
    lines = [TS + 'shader not present in AOT cache, hash=0xA58EBA123EFB541C',
             TS + 'shader not present in AOT cache, hash=0x93B9F93B535E7CCA',
             TS.replace('[warning]', '[info]') + 'adopted vertex shader 0x12345678, hash=0x0123456789ABCDEF']
    for i in range(8):
        if i < 4:
            lines.append(TS + VS_P)
        lines.append(TS + VS_U)
        if i < placement_ps:
            lines.append(TS + PS_P)
        lines.append(TS + PS_U)
    return '\n'.join(lines) + '\n'


def frames(draws):
    return 'frame,interval_ms,draw_calls\n' + ''.join(f'{i},5.0,{d}\n' for i, d in enumerate(draws))


def events(rows):
    return 'elapsed_ms\tframe\tevent\tanomaly_candidate\tdetails\n' + ''.join(
        f'{ms:.3f}\t{fr}\t{kind}\t{an}\t{det}\n' for ms, fr, kind, an, det in rows)


def unrec_rows(extra_guest=None, ps_guest=2890174248):
    rows = []
    for f in range(10, 40):
        rows.append((f * 10.0, f, 'unrecognized_shader', 1, 'guest= 2890175800 stage= 6 '))
        rows.append((f * 10.0, f, 'unrecognized_shader', 1, f'guest= {ps_guest} stage= 7 '))
    if extra_guest:
        rows.append((500.0, 50, 'unrecognized_shader', 1, f'guest= {extra_guest} stage= 6 '))
    return rows


def heap_rows(guest, stage, per_frame=2, f0=60, f1=70):
    """per_frame unrecognized_shader rows for (stage, guest) in each frame f0..f1-1, at frame * 10 ms."""
    return [(f * 10.0, f, 'unrecognized_shader', 1, f'guest= {guest} stage= {stage} ')
            for f in range(f0, f1) for _ in range(per_frame)]


def shifted(rows, ms):
    return [(r[0] + ms,) + tuple(r[1:]) for r in rows]


def make(case, off_ev, on_ev, on_log=None, on_draws=None):
    base = os.path.join(ROOT, case)
    for arm, ev, log, draws in (('off', off_ev, game_log(), [226] * 50 + [300] * 50),
                                ('on', on_ev, on_log or game_log(), on_draws or [226] * 50 + [300] * 50)):
        d = os.path.join(base, arm)
        os.makedirs(os.path.join(d, 'trace'), exist_ok=True)
        open(os.path.join(d, 'game.log'), 'w', newline='\n').write(log)
        open(os.path.join(d, 'frames.csv'), 'w', newline='\n').write(frames(draws))
        open(os.path.join(d, 'trace', 'events.tsv'), 'w', newline='\n').write(events(ev))
    return os.path.join(base, 'off'), os.path.join(base, 'on')


def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    ins = [(100.0, 10, 'shader_miss_cache_insert', 0, INS_VS), (100.5, 10, 'shader_miss_cache_insert', 0, INS_PS)]
    thrash = [(100.0 + i * 100, 10 + i, 'shader_miss_cache_insert', 0, INS_VS if i % 2 else INS_PS)
              for i in range(64)]
    heap_off = unrec_rows() + heap_rows(H_VS_OFF, 6) + heap_rows(H_PS_OFF, 7)
    heap_on = unrec_rows() + heap_rows(H_VS_ON, 6) + heap_rows(H_PS_ON, 7) + ins
    cases = [  # name, off events, on events, on log, on draws, expected exit, expected substrings[, extra args]
        ('pass', unrec_rows(), unrec_rows() + ins, None, None, 0, ['RESULT: PASS', 'as expected']),
        ('c1fail', unrec_rows(), unrec_rows() + ins, game_log(placement_ps=3), None, 1, ['fails: C1']),
        ('c3fail', unrec_rows(), unrec_rows(123) + ins, None, None, 1, ['fails: C3']),
        ('c4off', unrec_rows() + ins[:1], unrec_rows() + ins, None, None, 1, ['fails: C4-OFF']),
        ('noarm', unrec_rows(), unrec_rows() + ins[:1], None, None, 0, ['RESULT: PASS', 'NO-ARM']),
        ('thrash', unrec_rows(), unrec_rows() + thrash, None, None, 0, ['RESULT: PASS', 'THRASH']),
        ('c2check', unrec_rows(), unrec_rows() + ins, None, [220] * 50 + [300] * 50, 0, ['C2 CHECK']),
        # v2 (task #25): C3 heap-address pairing.
        ('heap', heap_off, heap_on, None, None, 0,
         ['RESULT: PASS', '2 heap pairs', 'VS 0xA7E1F740 -> VS 0xA7E44490', 'PS 0xAB13F250 -> PS 0xABB69980']),
        ('heapwin', heap_off,
         unrec_rows() + shifted(heap_rows(H_VS_ON, 6), 100000.0) + heap_rows(H_PS_ON, 7) + ins, None, None, 1,
         ['fails: C3', 'unmatched OFF-only keys: 1', 'unmatched ON-only keys: 1', 'last row by 100.0 s']),
        ('heaprpf', heap_off, unrec_rows() + heap_rows(H_VS_ON, 6, per_frame=3) + heap_rows(H_PS_ON, 7) + ins,
         None, None, 1, ['fails: C3', 'rows/frame off by 33.3 %']),
        ('heapstage', unrec_rows() + heap_rows(H_VS_OFF, 6), unrec_rows() + heap_rows(H_VS_ON, 7) + ins,
         None, None, 1, ['fails: C3', 'no ON-only VS key', 'no OFF-only PS key']),
        ('fixedgone', unrec_rows(), unrec_rows(ps_guest=0xA7E3E180) + ins, None, None, 1,
         ['fails: C3', 'PS 0xAC448F28', 'fixed address, never paired']),
        ('offset', heap_off, shifted(heap_on, 30000.0), None, None, 0,
         ['RESULT: PASS', 'offset OFF - ON: -30.00 s', '2 heap pairs']),
        ('fixedarg', heap_off, heap_on, None, None, 1, ['fails: C3', 'fixed address, never paired'],
         ['--fixed', '0xA7E1F740']),
        ('badfixed', heap_off, heap_on, None, None, 2, ['bad input: --fixed'], ['--fixed', 'zz']),
    ]
    ok = 0
    for case in cases:
        name, off_ev, on_ev, on_log, on_draws, want_rc, want = case[:7]
        extra = list(case[7]) if len(case) > 7 else []
        off, on = make(name, off_ev, on_ev, on_log, on_draws)
        p = subprocess.run([sys.executable, CHECK, '--off', off, '--on', on] + extra, capture_output=True, text=True)
        good = p.returncode == want_rc and all(w in p.stdout for w in want)
        ok += good
        last = [line for line in p.stdout.splitlines() if line.startswith('RESULT')]
        tail = last[0] if last else (p.stdout.strip().splitlines() or [p.stderr[-300:]])[-1]
        print(f'{"ok  " if good else "BAD "} {name:9s} rc={p.returncode} {tail}')
        if not good:
            print('\n'.join('       ' + line for line in (p.stdout + p.stderr).splitlines()[-30:]))
    print(f'selftest: {ok}/{len(cases)} ok')
    return 0 if ok == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
