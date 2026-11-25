#!/usr/bin/env python3
"""Tests for diagd_report.py on synthetic game.logs (stdlib unittest).

Builds build/agent6/s33-popin/test-diagd/ from scratch: a fake matrix dir
(runs/<name>/game.log + run.json, arms ond and offd) whose diag lines come from
a Python copy of NoteResolveAfterDrop (s33-diagd-on-nohunk5.patch), plus bad
logs for the WARN cases, a run rotated over game.2/game.1/game.log and harness
style YYYYMMDD-HHMMSS-<tag> dirs. The report runs in-process (one python process).

Usage: python -B build/agent6/s33-popin/test_diagd_report.py
"""
import contextlib
import io
import json
import os
import shutil
import sys
import unittest
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diagd_report  # noqa: E402

ROOT = os.path.join(HERE, 'test-diagd')
MATRIX = os.path.join(ROOT, 'matrix')
BASE = datetime(2026, 11, 25, 1, 0, 0)
A, B, C, D, E = 'A0000000', 'B0001000', 'C0002000', 'D0003000', 'E0004000'


class Sim:
    """Mirror of the patch's NoteResolveAfterDrop + skipped-draw counter."""
    MAX = 4096

    def __init__(self):
        self.drops = self.resolves = self.after = self.healed = self.lines = 0
        self.tainted = {}
        self.t = 0.0
        self.out = ['[2026-11-25 00:59:59.000] [info] [gpu] [t100] DXGI adapter: fake',
                    '* a continuation line without prefix']

    def log(self, msg):
        ts = (BASE + timedelta(seconds=round(self.t, 3))).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.out.append('[%s] [info] [gpu] [t12748] %s' % (ts, msg))

    def skip(self, n=1):
        self.drops += n

    def resolve(self, dest, copies=True, dt=0.1):
        """Returns (ordinal, time) of this resolve."""
        self.t += dt
        self.resolves += 1
        drops, self.drops = self.drops, 0
        if not copies:
            return self.resolves, self.t
        tail = 'after drops %d, healed %d, tainted %d'
        d = int(dest, 16)
        if drops:
            self.after += 1
            first = dest not in self.tainted
            self.tainted[dest] = self.resolves
            if self.lines < self.MAX:
                self.lines += 1
                self.log(('resolve after drop: dest %08X after %d skipped draws (%s) | resolves %d, '
                          + tail) % (d, drops, 'new' if first else 'again', self.resolves,
                                     self.after, self.healed, len(self.tainted)))
        elif self.tainted.pop(dest, None) is not None:
            self.healed += 1
            if self.lines < self.MAX:
                self.lines += 1
                self.log(('resolve after drop: dest %08X resolved clean again | resolves %d, ' + tail)
                         % (d, self.resolves, self.after, self.healed, len(self.tainted)))
        if self.lines == self.MAX:
            self.lines += 1
            self.log('resolve after drop: %d lines logged, no more from here on' % self.MAX)
        return self.resolves, self.t

    def end(self, dt=1.0):
        self.t += dt
        self.log('Window closing, shutting down...')


def write_run(parent, name, lines, run_json, logs=None):
    """Writes game.log (or logs: {file name: lines}) and run.json; returns the game.log path."""
    d = os.path.join(parent, name)
    os.makedirs(d)
    for fn, ls in (logs or {'game.log': lines}).items():
        with open(os.path.join(d, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(ls) + '\n')
    if run_json is not None:
        with open(os.path.join(d, 'run.json'), 'w', encoding='utf-8') as f:
            json.dump(run_json, f)
    return os.path.join(d, 'game.log')


def run_report(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = diagd_report.main(argv)
    return code, buf.getvalue()


EXP = {}


def build():
    shutil.rmtree(ROOT, ignore_errors=True)
    runs = os.path.join(MATRIX, 'runs')
    # ond r1: A taints+heals every frame; B one-off never healed; C heals late
    # (tainted at frame 2, again at frame 10, clean at frame 20); D clear-only
    # resolve after a skip (no line); E clean resolve of a clean dest (no line).
    s = Sim()
    for i in range(30):
        s.skip()
        s.resolve(A)
        s.resolve(A)
        if i == 2:
            s.skip(3)
            EXP['c_start'] = s.resolve(C)
        if i == 3:
            s.skip()
            EXP['b_taint'] = s.resolve(B)
        if i == 5:
            s.skip()
            s.resolve(D, copies=False)
            s.resolve(E)
        if i == 10:
            s.skip()
            s.resolve(C)
        if i == 20:
            EXP['c_heal'] = s.resolve(C)
    s.end()
    EXP['r1_end'] = s.t
    EXP['r1_final'] = (s.resolves, s.after, s.healed, len(s.tainted))
    EXP['r1_lines'] = s.lines
    write_run(runs, '0101-ond-r1', s.out, {'tag': 'ond-r1'})
    # ond r2 (run.json "arm", dir name that isn't NNNN-...): B tainted first,
    # then A taint/heal until the 4096-line cap (A is tainted at the cap).
    s = Sim()
    s.skip()
    s.resolve(B)
    for _ in range(2100):
        s.skip()
        s.resolve(A)
        s.resolve(A)
    s.end()
    write_run(runs, 'capped-run', s.out, {'arm': 'ond', 'tag': 'whatever-r9'})
    # offd r1: no diag lines at all.
    s = Sim()
    s.end()
    write_run(runs, '0103-offd-r1', s.out, {'tag': 'offd-r1'})
    # offd r2: A taint/heal only, ends clean.
    s = Sim()
    for _ in range(5):
        s.skip()
        s.resolve(A)
        s.resolve(A)
    s.end()
    write_run(runs, '0104-offd-r2', s.out, {'tag': 'offd-r2'})
    # Bad: one heal line with a wrong healed counter.
    s = Sim()
    for _ in range(5):
        s.skip()
        s.resolve(A)
        s.resolve(A)
    s.end()
    s.out[5] = s.out[5].replace('healed 2,', 'healed 7,')
    assert 'resolved clean again' in s.out[5] and 'healed 7,' in s.out[5]
    EXP['bad_counter'] = write_run(ROOT, 'bad-counter', s.out, None)
    # Bad: an out-of-order resolves ordinal and a malformed diag line.
    s = Sim()
    for _ in range(5):
        s.skip()
        s.resolve(A)
        s.resolve(A)
    s.end()
    s.out[6] = s.out[6].replace('resolves 5,', 'resolves 1,')
    assert 'resolves 1,' in s.out[6]
    s.out.insert(8, '[2026-11-25 01:00:00.950] [info] [gpu] [t12748] resolve after drop: dest '
                    'ZZZ garbage')
    EXP['bad_order'] = write_run(ROOT, 'bad-order', s.out, None)
    # Rotated run: B tainted in game.2.log (oldest), A traffic in game.1.log,
    # B healed in game.log (newest). Written in a shuffled order on purpose.
    s = Sim()
    s.skip()
    EXP['rot_taint'] = s.resolve(B)
    for _ in range(10):
        s.skip()
        s.resolve(A)
        s.resolve(A)
    EXP['rot_heal'] = s.resolve(B)
    s.end()
    assert 'B0001000 after' in s.out[2] and 'B0001000 resolved clean' in s.out[23]
    EXP['rot'] = write_run(ROOT, 'rot-run', None, {'tag': 'ond-r5'}, logs={
        'game.log': s.out[15:], 'game.1.log': s.out[5:15], 'game.2.log': s.out[:5]})
    # Harness-style dirs (Agent 3's run-game.ps1): YYYYMMDD-HHMMSS-<tag>.
    s = Sim()
    s.skip()
    s.resolve(A)
    s.resolve(A)
    s.end()
    EXP['harness1'] = os.path.dirname(write_run(
        os.path.join(ROOT, 'harness'), '20261125-013000-s33-ond', s.out, {'tag': 's33-ond'}))
    EXP['harness2'] = os.path.dirname(write_run(
        os.path.join(ROOT, 'harness'), '20261125-014500-s33-offd-r2', s.out, None))


class DiagdReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.out_txt = os.path.join(ROOT, 'report.txt')
        cls.out_json = os.path.join(ROOT, 'report.json')
        cls.code, cls.text = run_report(['--out', cls.out_txt, '--json', cls.out_json, MATRIX])
        with open(cls.out_json, encoding='utf-8') as f:
            cls.j = json.load(f)
        cls.runs = {r['name']: r for r in cls.j['runs']}

    def test_exit_and_outputs(self):
        self.assertEqual(self.code, 0, self.text)
        self.assertIn('TOTAL: 4 run(s), 2 arm(s), 0 WARN(s)', self.text)
        with open(self.out_txt, encoding='utf-8') as f:
            self.assertEqual(f.read(), self.text)

    def test_arms(self):
        self.assertEqual({r: x['arm'] for r, x in self.runs.items()}, {
            '0101-ond-r1': 'ond', 'capped-run': 'ond',
            '0103-offd-r1': 'offd', '0104-offd-r2': 'offd'})

    def test_run1_counters_and_dests(self):
        r = self.runs['0101-ond-r1']
        self.assertFalse(r['cap_hit'])
        self.assertEqual(r['lines'], EXP['r1_lines'])
        self.assertEqual(r['lines'], 30 * 2 + 2 + 1 + 1)   # A x60, C taint x2 + heal, B
        f = r['final']
        self.assertEqual((f['resolves'], f['after_drops'], f['healed'], f['tainted']), EXP['r1_final'])
        self.assertEqual(EXP['r1_final'], (66, 33, 31, 1))
        self.assertEqual(sorted(r['dests']), [A, B, C])
        a, b, c = r['dests'][A], r['dests'][B], r['dests'][C]
        self.assertEqual((a['taints'], a['episodes'], a['heals']), (30, 30, 30))
        self.assertEqual(set(a['lat_resolves']), {1})
        self.assertAlmostEqual(max(a['lat_seconds']), 0.1, places=3)
        self.assertFalse(a['tainted_at_end'])
        self.assertEqual((b['taints'], b['heals'], b['tainted_at_end']), (1, 0, True))
        self.assertEqual((c['taints'], c['episodes'], c['heals']), (2, 1, 1))
        self.assertEqual(c['lat_resolves'], [EXP['c_heal'][0] - EXP['c_start'][0]])
        self.assertAlmostEqual(c['lat_seconds'][0], EXP['c_heal'][1] - EXP['c_start'][1], places=3)
        self.assertFalse(c['tainted_at_end'])
        st = r['still_tainted']
        self.assertEqual([x['dest'] for x in st], [B])
        self.assertFalse(st[0]['healed_before'])
        self.assertAlmostEqual(st[0]['since_last_taint_s'], EXP['r1_end'] - EXP['b_taint'][1], places=3)
        lat = r['latency']['resolves']
        self.assertEqual((lat['n'], lat['median'], lat['p95']), (31, 1, 1))
        self.assertEqual(lat['max'], EXP['c_heal'][0] - EXP['c_start'][0])
        self.assertEqual(r['warns'], [])

    def test_cap_run(self):
        r = self.runs['capped-run']
        self.assertTrue(r['cap_hit'])
        self.assertEqual(r['lines'], 4097)
        self.assertEqual(r['final']['tainted'], 2)
        self.assertEqual(sorted(x['dest'] for x in r['still_tainted']), [A, B])
        self.assertEqual({x['dest']: x['healed_before'] for x in r['still_tainted']}, {A: True, B: False})
        self.assertIn('note: cap hit', self.text)
        self.assertEqual(r['warns'], [])

    def test_no_diag_run(self):
        r = self.runs['0103-offd-r1']
        self.assertEqual((r['lines'], r['final'], r['dests'], r['warns']), (0, None, {}, []))

    def test_arm_union(self):
        on, off = self.j['arms']['ond'], self.j['arms']['offd']
        self.assertEqual(on['runs'], 2)
        self.assertEqual(on['cap_hits'], 1)
        self.assertEqual(on['end_dests'], {B: {'runs': 2, 'never_healed_runs': 2},
                                           A: {'runs': 1, 'never_healed_runs': 0}})
        self.assertEqual(off['end_dests'], {})
        self.assertEqual((off['runs'], off['with_diag'], off['healed']), (2, 1, 5))
        self.assertIn('B0001000 in 2/2 runs (never healed in 2)', self.text)

    def test_bad_counter(self):
        code, text = run_report([EXP['bad_counter']])
        self.assertEqual(code, 1, text)
        self.assertIn('healed 7 in line, replay 2', text)

    def test_bad_order_and_malformed(self):
        code, text = run_report([os.path.dirname(EXP['bad_order'])])
        self.assertEqual(code, 1, text)
        self.assertIn('game.log:7: resolves ordinal 1 not after previous 4', text)
        self.assertIn('game.log:9: malformed diag line', text)

    def test_rotated_logs_one_stream(self):
        code, text = run_report(['--json', os.path.join(ROOT, 'rot.json'), os.path.dirname(EXP['rot'])])
        self.assertEqual(code, 0, text)
        self.assertIn('game.2.log (+ game.1.log, game.log)', text)
        with open(os.path.join(ROOT, 'rot.json'), encoding='utf-8') as f:
            r = json.load(f)['runs'][0]
        self.assertEqual([os.path.basename(p) for p in r['logs']], ['game.2.log', 'game.1.log', 'game.log'])
        self.assertEqual(r['arm'], 'ond')
        self.assertEqual(r['warns'], [])
        b = r['dests'][B]
        self.assertEqual((b['taints'], b['heals'], b['tainted_at_end']), (1, 1, False))
        self.assertEqual(b['lat_resolves'], [EXP['rot_heal'][0] - EXP['rot_taint'][0]])
        self.assertEqual(b['lat_resolves'], [21])
        self.assertAlmostEqual(b['lat_seconds'][0], EXP['rot_heal'][1] - EXP['rot_taint'][1], places=3)
        self.assertAlmostEqual(b['lat_seconds'][0], 2.1, places=3)
        self.assertEqual(r['final'], {'resolves': 22, 'after_drops': 11, 'healed': 11, 'tainted': 0})
        # game.log alone (given as a file) misses the taint: the replay must WARN.
        code, text = run_report([EXP['rot']])
        self.assertEqual(code, 1, text)
        self.assertIn('WARN game.log:1: after drops 8 in line, replay 1', text)

    def test_harness_dirs(self):
        code, text = run_report([EXP['harness1'], EXP['harness2']])
        self.assertEqual(code, 0, text)
        self.assertIn('== run 20261125-013000-s33-ond  (arm ond)', text)
        self.assertIn('== run 20261125-014500-s33-offd-r2  (arm offd)', text)

    def test_arm_override(self):
        code, text = run_report(['--arm', 'Forced=' + EXP['harness1']])
        self.assertEqual(code, 0, text)
        self.assertIn('(arm forced)', text)
        # Same path positional and via --arm: one run, the --arm label wins.
        code, text = run_report([EXP['harness1'], '--arm', 'x1=' + EXP['harness1']])
        self.assertEqual(code, 0, text)
        self.assertIn('TOTAL: 1 run(s), 1 arm(s), 0 WARN(s)', text)
        self.assertIn('(arm x1)', text)
        # A matrix dir: every run gets the label.
        code, text = run_report(['--arm', 'all=' + MATRIX])
        self.assertIn('TOTAL: 4 run(s), 1 arm(s), 0 WARN(s)', text)

    def test_arm_malformed(self):
        for bad in ('noequals', '=' + MATRIX, 'name=', ' ='):
            code, text = run_report(['--arm', bad, MATRIX])
            self.assertEqual(code, 2, bad)
            self.assertIn('--arm wants NAME=PATH', text)
        self.assertEqual(run_report([MATRIX, '--arm'])[0], 2)

    def test_single_file_input(self):
        code, text = run_report([os.path.join(MATRIX, 'runs', '0101-ond-r1', 'game.log')])
        self.assertEqual(code, 0, text)
        self.assertIn('(arm ond)', text)
        self.assertIn('TOTAL: 1 run(s), 1 arm(s), 0 WARN(s)', text)

    def test_usage_errors(self):
        self.assertEqual(run_report([])[0], 2)
        self.assertEqual(run_report([os.path.join(ROOT, 'no-such-dir')])[0], 2)
        self.assertEqual(run_report(['--bogus', MATRIX])[0], 2)
        self.assertEqual(run_report(['--out'])[0], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
