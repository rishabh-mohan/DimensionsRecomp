#!/usr/bin/env python3
"""Self-test for mc_smoke_check.py on synthetic runs (writes only under build/agent4/r2t6/selftest)."""
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


def unrec_rows(extra_guest=None):
    rows = []
    for f in range(10, 40):
        rows.append((f * 10.0, f, 'unrecognized_shader', 1, 'guest= 2890175800 stage= 6 '))
        rows.append((f * 10.0, f, 'unrecognized_shader', 1, 'guest= 2890174248 stage= 7 '))
    if extra_guest:
        rows.append((500.0, 50, 'unrecognized_shader', 1, f'guest= {extra_guest} stage= 6 '))
    return rows


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
    cases = [  # name, off events, on events, on log, on draws, expected exit, expected substrings
        ('pass', unrec_rows(), unrec_rows() + ins, None, None, 0, ['RESULT: PASS', 'as expected']),
        ('c1fail', unrec_rows(), unrec_rows() + ins, game_log(placement_ps=3), None, 1, ['fails: C1']),
        ('c3fail', unrec_rows(), unrec_rows(123) + ins, None, None, 1, ['fails: C3']),
        ('c4off', unrec_rows() + ins[:1], unrec_rows() + ins, None, None, 1, ['fails: C4-OFF']),
        ('noarm', unrec_rows(), unrec_rows() + ins[:1], None, None, 0, ['RESULT: PASS', 'NO-ARM']),
        ('thrash', unrec_rows(), unrec_rows() + thrash, None, None, 0, ['RESULT: PASS', 'THRASH']),
        ('c2check', unrec_rows(), unrec_rows() + ins, None, [220] * 50 + [300] * 50, 0, ['C2 CHECK']),
    ]
    ok = 0
    for name, off_ev, on_ev, on_log, on_draws, want_rc, want in cases:
        off, on = make(name, off_ev, on_ev, on_log, on_draws)
        p = subprocess.run([sys.executable, CHECK, '--off', off, '--on', on], capture_output=True, text=True)
        good = p.returncode == want_rc and all(w in p.stdout for w in want)
        ok += good
        last = [line for line in p.stdout.splitlines() if line.startswith('RESULT')]
        print(f'{"ok  " if good else "BAD "} {name:8s} rc={p.returncode} {last[0] if last else p.stderr[-300:]}')
    print(f'selftest: {ok}/{len(cases)} ok')
    return 0 if ok == len(cases) else 1


if __name__ == '__main__':
    sys.exit(main())
