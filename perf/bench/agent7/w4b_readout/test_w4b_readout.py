#!/usr/bin/env python3
"""Tests for w4b_readout.py (stdlib unittest): python bench\\agent7\\w4b_readout\\test_w4b_readout.py
The frames.json files of the synthetic matrix come from Agent 8's own frame_summary.summarise (imported read-only), so
the per-run check tests agreement with the runner's numbers. W4B_SKIP_PS=1 skips the timerq_slowstate.ps1 test."""
import csv
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w4b_readout as wr  # noqa: E402

FS = wr.load_module('frame_summary', os.path.join(wr.REPO, 'bench', 'agent8', 'run', 'frame_summary.py'))
PERF_HEADER = ('frame_time_us,fps,draw_calls,command_buffer_stalls,vertices_processed,xma_frames_decoded,'
               'audio_frame_latency_us,buffer_queue_depth,functions_dispatched,interrupt_dispatches,active_threads,'
               'apc_queue_depth,critical_region_contentions,texture_cache_hits,texture_cache_misses,'
               'pipeline_cache_hits,pipeline_cache_misses')
COLS = ['seq', 'round', 'arm', 'group', 'rep', 'scored', 'status', 'valid_timing', 'frames', 'window_s', 'median_ms',
        'p99_ms', 'over33', 'fps_mean', 'excluded', 'flags_excluding', 'flags_info', 'light_share',
        'install_dat_fail', 'light_phase', 'run_dir', 'notes']
BOOT = 50      # good rows before the window (the first one has frame_time_us 0, like perf.csv's first swap)
FF = 1000.0    # first-frame epoch; the window is FF+60 .. FF+80 in run.json
NAME = '20990101-0000'


def frames(ms):
    """1000 window frames of `ms` ms, every 50th one 40 ms (20 frames over 33 ms)."""
    return [40.0 if i % 50 == 25 else ms for i in range(1000)]


def draws(base, jitter=0):
    return [base[0] + jitter] * 500 + [base[1] + jitter] * 500


def write_run(mdir, name, ft_ms, dc, native=False, slow=False, excluded=False, busy=0.5):
    """One synthetic run dir. sys.csv: 1 s rows at epoch FF + t, the busy share `busy` (cpu_util_pct = 100 x busy at
    cpu_perf_pct 100); proc.csv: the game at 2.0 cores, t_s = epoch - FF - 2, 'measure start' at t_s 58 = run.json
    measure_start.epoch_s FF + 60, where the scored window starts (12 logical CPUs, so background = 12 x busy - 2)."""
    rd = os.path.join(mdir, 'runs', name)
    os.makedirs(rd)
    if native:
        path = os.path.join(rd, 'native-frames.csv')
        with open(path, 'w', newline='\n') as fh:
            fh.write('frame,interval_ms,draw_calls\n')
            for k in range(BOOT):
                fh.write('%d,20.5,7\n' % k)
            for k, t in enumerate(ft_ms):
                fh.write('%d,%.4f,7\n' % (BOOT + k, t))
    else:
        path = os.path.join(rd, 'perf.csv')
        with open(path, 'w', newline='\n') as fh:
            fh.write(PERF_HEADER + '\n')
            fh.write('0,0,49' + ',0' * 14 + '\n')
            for _ in range(BOOT - 1):
                fh.write('20000,50,100' + ',0' * 14 + '\n')
            fh.write('bad,row\n')  # skipped by frame_summary's rules, so it is not counted in first_row
            for t, d in zip(ft_ms, dc):
                fh.write('%d,0,%d' % (round(t * 1000), d) + ',0' * 14 + '\n')
            fh.write('5000,0,1')  # partial last row: dropped
    fj = FS.summarise(path, skip_rows=BOOT, rows_limit=len(ft_ms), label='TIMING')
    with open(os.path.join(rd, 'frames.json'), 'w') as fh:
        json.dump(fj, fh)
    rj = {'pid': 4242, 'params': {'seconds': 20}, 'ff_signal_epoch_s': FF, 'problems': [],
          'sys': {'window_start_epoch': FF + 60, 'window_end_epoch': FF + 80},
          'measure_start': {'name': 'measure_start', 'epoch_s': FF + 60},
          'measure_end': {'name': 'measure_end', 'epoch_s': FF + 80}, 'logical_cpus': 12,
          'excluded': excluded, 'flags_excluding': ['light_phase'] if excluded else [], 'flags_info': []}
    with open(os.path.join(rd, 'run.json'), 'w') as fh:
        json.dump(rj, fh)
    with open(os.path.join(rd, 'sys.csv'), 'w', newline='\n') as fh:
        fh.write('t_s,epoch_s,e_eff_mhz,fg_game,cpu_util_pct,cpu_perf_pct\n')
        for t in range(86):
            fh.write('%d,%.3f,%d,1,%.2f,100.00\n' % (t, FF + t, 500 if slow and 65 <= t <= 70 else 1500, 100.0 * busy))
    with open(os.path.join(rd, 'proc.csv'), 'w', newline='\n') as fh:
        fh.write('t_s,phase,alive,cpu_cores,cpu_s,note\n')
        for k in range(84):
            fh.write('%d.00,%s,1,2.00,%.2f,%s\n' % (k, 'measure' if k >= 58 else 'warmup', 2.0 * k,
                                                    'measure start; driver' if k == 58 else ''))
    return rd, fj


def make_matrix(root):
    mdir = os.path.join(root, NAME)
    os.makedirs(os.path.join(mdir, 'runs'))
    with open(os.path.join(mdir, 'matrix.json'), 'w') as fh:
        json.dump({'title': 'synthetic W4b', 'reference': 'd0', 'arms': [
            {'id': 'd0', 'group': 'w4', 'ref': True}, {'id': 'B', 'group': 'w4'}, {'id': 'd3', 'group': 'w4'},
            {'id': 'n0', 'group': 'w4', 'frames': 'native'}]}, fh)
    heavy = (200, 900)
    spec = [  # seq, round, arm, rep, scored, frame ms, draws, kwargs, valid
        (1, 0, 'd0', 0, False, frames(5.0), draws(heavy), {}, True),
        (2, 1, 'd0', 1, True, frames(5.0), draws(heavy), {}, True),
        (3, 1, 'B', 1, True, frames(4.8), draws(heavy, 1), {}, True),
        (4, 1, 'd3', 1, True, frames(5.5), draws(heavy), {'busy': 1.0}, True),       # CPU saturated (SAT)
        (5, 2, 'B', 2, True, frames(4.82), [50] * 1000, {}, True),          # another scene
        (6, 2, 'd0', 2, True, frames(5.02), draws(heavy, 1), {}, True),
        (7, 2, 'd3', 2, True, frames(3.0), [50] * 1000, {'excluded': True}, True),  # light phase, excluded
        (8, 3, 'd0', 3, True, frames(4.98), draws(heavy), {'busy': 0.75}, True),     # background 7 cores (BG+)
        (9, 3, 'B', 3, True, frames(4.78), draws(heavy), {'slow': True}, True),  # slow state in the window
        (10, 3, 'n0', 1, True, frames(6.0), None, {'native': True}, False),  # functional only
    ]
    rows = []
    for seq, rnd, arm, rep, scored, ft, dc, kw, valid in spec:
        name = '00%02d-%s-%s' % (seq, 'cold-' + arm if not scored else arm, 'r%d' % rep if scored else '')
        name = name.rstrip('-')
        rd, fj = write_run(mdir, name, ft, dc or [0] * len(ft), **kw)
        rows.append({'seq': seq, 'round': rnd, 'arm': arm, 'group': 'w4', 'rep': rep, 'scored': str(scored),
                     'status': 'OK', 'valid_timing': str(valid), 'frames': fj['frames'], 'window_s': fj['window_s'],
                     'median_ms': fj['median_ms'], 'p99_ms': fj['p99_ms'], 'over33': fj['over_33ms'],
                     'fps_mean': '%.3f' % fj['mean_fps'], 'excluded': str(bool(kw.get('excluded'))),
                     'flags_excluding': 'light_phase' if kw.get('excluded') else '', 'flags_info': '',
                     'light_share': '0.5', 'install_dat_fail': '28' if kw.get('excluded') else '34',
                     'light_phase': str(bool(kw.get('excluded'))), 'run_dir': rd, 'notes': ''})
    with open(os.path.join(mdir, 'results.csv'), 'w', newline='') as fh:
        wtr = csv.DictWriter(fh, COLS, quoting=csv.QUOTE_ALL)
        wtr.writeheader()
        wtr.writerows(rows)
    return mdir


def run_main(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = wr.main(args)
    return rc, buf.getvalue()


class PureFunctions(unittest.TestCase):
    def test_nearest_rank(self):
        s = list(range(1, 101))
        self.assertEqual(wr.nearest_rank(s, 1, 2), 50)
        self.assertEqual(wr.nearest_rank(s, 99, 100), 99)
        self.assertEqual(wr.nearest_rank([7], 99, 100), 7)

    def test_window_stats(self):
        st = wr.window_stats([10000] * 198 + [50000] * 2 + [0])
        self.assertEqual(st['frames'], 200)
        self.assertAlmostEqual(st['window_s'], 2.08)
        self.assertAlmostEqual(st['fps'], 200 / 2.08)
        self.assertAlmostEqual(st['p50_ms'], 10.0)
        self.assertAlmostEqual(st['p99_ms'], 10.0)        # sorted[197]: the 2 slow frames sit above p99
        self.assertEqual(st['low1_frames'], 2)
        self.assertAlmostEqual(st['low1_fps'], 20.0)      # mean of the slowest max(1, 200 // 100) = 2 frames
        self.assertEqual(st['over33'], 2)
        self.assertAlmostEqual(st['over33_min'], 2 / 2.08 * 60)
        self.assertIsNone(wr.window_stats([0, -1]))

    def test_stat_bins(self):
        b = wr.stat_bins([1e6] * 25)                     # 25 s: 0-10, 10-20, 20-25 (5 s = half a bin: kept)
        self.assertEqual([x['frames'] for x in b], [10, 10, 5])
        self.assertEqual([(x['t0'], x['t1']) for x in b], [(0.0, 10.0), (10.0, 20.0), (20.0, 25.0)])
        b = wr.stat_bins([1e6] * 24 + [0.5e6, 0, -1])   # 24.5 s: the 4.5 s tail joins 10-20; frames <= 0 left out
        self.assertEqual([x['frames'] for x in b], [10, 15])
        self.assertEqual(b[-1]['t1'], 24.5)
        b = wr.stat_bins([1e6] * 5 + [17e6] + [1e6] * 8)  # a 17 s frame: no frame ends in 10-20
        self.assertEqual([x['frames'] for x in b], [5, 0, 9])
        self.assertNotIn('p99_ms', b[1])
        # each bin carries window_stats of its own frames: 10 s of 5 ms frames, then 1800 x 5 ms + 25 x 40 ms
        fts = [5000] * 2000 + [5000] * 1800 + [40000] * 25
        b = wr.stat_bins(fts)
        self.assertEqual(len(b), 2)
        self.assertEqual(b[0], dict(wr.window_stats(fts[:2000]), bin=0, t0=0.0, t1=10.0))
        self.assertEqual(b[1]['frames'], 1825)
        self.assertEqual(b[1]['over33'], 25)
        self.assertAlmostEqual(b[1]['p99_ms'], 40.0)      # sorted[ceil(0.99 x 1825) - 1] = sorted[1806]: slow
        self.assertAlmostEqual(b[1]['low1_fps'], 25.0)    # slowest 1825 // 100 = 18 frames, all 40 ms
        self.assertAlmostEqual(b[1]['over33_min'], 25 * 60 / 10.0)
        self.assertEqual(wr.stat_bins([]), [])

    def test_scene_distance(self):
        self.assertAlmostEqual(wr.w1_log({217: 1.0}, {217: 1.0}), 0.0)
        self.assertAlmostEqual(wr.w1_log({217: 1.0}, {218: 1.0}), math.log(219 / 218))
        self.assertGreater(wr.w1_log({200: 0.5, 900: 0.5}, {50: 1.0}), 1.0)
        # default floor: window 3's light phase (218 vs 226 draws) is flagged, 1-draw jitter is not
        self.assertGreater(wr.w1_log({218: 1.0}, {226: 1.0}), wr.SCENE_FLOOR)
        self.assertLess(wr.w1_log({226: 1.0}, {227: 1.0}), wr.SCENE_FLOOR)
        h = wr.scene_hist([100, 200, 200, None], [3e6, 3.5e6, 3.5e6, 1e6])
        self.assertAlmostEqual(h[100], 0.3)
        self.assertEqual(wr.wquantile(h, 0.5), 200)
        self.assertAlmostEqual(wr.wmean(h), 170.0)
        self.assertEqual(wr.draws_bins([10] * 10 + [20] * 5, [1e6] * 15), [10.0, 20.0])
        p = wr.pool([{1: 1.0}, {3: 1.0}])
        self.assertEqual(p, {1: 0.5, 3: 0.5})

    def test_parse_timerq(self):
        text = ('\nmatrix        run          blocking onset_s slow_pct span_s fg\n'
                '------        ---          -------- ------- -------- ------ --\n'
                '20990101-0000 0002-d0-r1      False -              0     85 1\n'
                '20990101-0000 0009-B-r3        True 65             7     85 0/1\n'
                '20990102-0000 0001-x-r1       False 3             90     85 1\n')
        rows = wr.parse_timerq(text, NAME)
        self.assertEqual(sorted(rows), ['0002-d0-r1', '0009-B-r3'])
        self.assertEqual(rows['0009-B-r3']['onset_s'], '65')
        self.assertEqual(rows['0009-B-r3']['fg'], '0/1')
        self.assertEqual(rows['0002-d0-r1']['slow_pct'], '0')

    def test_no_bytecode(self):
        self.assertTrue(sys.dont_write_bytecode)

    def test_interp(self):
        self.assertAlmostEqual(wr.interp([0, 1, 2], [0, 10, 20], 1.5), 15.0)
        self.assertEqual(wr.interp([0, 1, 2], [0, 10, 20], 2), 20)
        self.assertIsNone(wr.interp([0, 1, 2], [0, 10, 20], 2.1))
        self.assertIsNone(wr.interp([], [], 0))

    def test_game_window_fallback(self):
        tmp = tempfile.mkdtemp()
        try:
            rd, _ = write_run(tmp, 'r', frames(5.0), [0] * 1000)
            with open(os.path.join(rd, 'proc.csv'), 'w', newline='\n') as fh:  # ends 1 s into the window
                fh.write('t_s,cpu_s,note\n58.00,116.00,measure start\n59.00,118.00,\n')
            rj = wr.load_json(os.path.join(rd, 'run.json'))
            fj = wr.load_json(os.path.join(rd, 'frames.json'))
            self.assertEqual(wr.game_window(rd, rj, fj)[:2], (None, 'proc.csv does not cover the window'))
            rj['window_cpu_cores_mean'] = 1.5
            self.assertEqual(wr.game_window(rd, rj, fj)[:2], (1.5, 'run.json window_cpu_cores_mean'))
            b, note = wr.bg_load(rd, rj, fj)
            self.assertEqual(note, 'ok')
            self.assertAlmostEqual(b['bg_cores'], 12 * 0.5 - 1.5)  # the window value replaces the missing slopes
            os.remove(os.path.join(rd, 'sys.csv'))
            self.assertEqual(wr.bg_load(rd, rj, fj), (None, 'no sys.csv'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.mdir = make_matrix(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_report(self):
        out, js = os.path.join(self.tmp, 'out.md'), os.path.join(self.tmp, 'out.json')
        rc, text = run_main([self.mdir, '--no-timerq', '--bg-ref', 'none', '-o', out, '--json', js])
        self.assertEqual(rc, 0)
        with open(out, encoding='utf-8') as fh:
            self.assertEqual(fh.read(), text)
        with open(js, encoding='utf-8') as fh:
            J = json.load(fh)
        runs = {x['name']: x for x in J['runs']}
        # every run with a window agrees with frame_summary's frames.json and results.csv
        self.assertTrue(all(x['check'] == [] for x in J['runs']), [x['check'] for x in J['runs']])
        self.assertIn('10 of 10 runs with a window agree', text)
        # kept: d0 x3, B x3, d3 x1; not kept: the cold run, the excluded run, the functional n0 run
        self.assertEqual(J['n_kept'], 7)
        self.assertFalse(runs['0001-cold-d0']['keep'])
        self.assertIn('EXCLUDED: light_phase', '; '.join(runs['0007-d3-r2']['why']))
        self.assertIn('not timing', '; '.join(runs['0010-n0-r1']['why']))
        self.assertEqual(J['arms']['d0']['n'], 3)
        self.assertTrue(J['arms']['d3']['n_lt3'])
        self.assertNotIn('n0', J['arms'])
        self.assertIn('| d3 |  | 1 n<3! |', text)
        # numbers: d0-r1 = 980 x 5 ms + 20 x 40 ms
        st = runs['0002-d0-r1']['stats']
        self.assertAlmostEqual(st['fps'], 1000 / 5.7)
        self.assertAlmostEqual(st['p50_ms'], 5.0)
        self.assertAlmostEqual(st['p99_ms'], 40.0)
        self.assertAlmostEqual(st['low1_fps'], 25.0)
        self.assertAlmostEqual(st['over33_min'], 20 / 5.7 * 60)
        self.assertAlmostEqual(J['arms']['d0']['fps']['med'], 1000 / 5.7)
        self.assertAlmostEqual(J['run_matrix_fps']['d0'], round(1000 / 5.7, 3))
        self.assertNotIn('DIFFERENT', text)
        # deltas: B faster in every run; p99 equal (overlap)
        self.assertEqual(J['deltas']['B']['fps']['verdict'], 'better')
        self.assertEqual(J['deltas']['B']['p50_ms']['verdict'], 'better')
        self.assertEqual(J['deltas']['B']['p99_ms']['verdict'], 'overlap')
        self.assertEqual(J['deltas']['B']['paired_fps_pct']['n'], 3)
        self.assertEqual(J['deltas']['B']['paired_fps_pct']['up'], 3)
        # scene: only B-r2 (and the excluded light-phase d3-r2) show another scene; jitter of 1 draw does not count
        flagged = sorted(x['name'] for x in J['runs'] if x['scene_flag'])
        self.assertEqual(flagged, ['0005-B-r2', '0007-d3-r2'])
        self.assertLess(runs['0003-B-r1']['scene_d'], 0.01)
        self.assertTrue(runs['0006-d0-r2']['scene_loo'])
        self.assertIn('n/a (native frames)', text)
        self.assertEqual(runs['0003-B-r1']['draws_p50'], 201)
        # slow state from matrix_recheck.slow_state: onset 65 s, 6 of 21 window samples
        self.assertTrue(runs['0009-B-r3']['slow_win'])
        self.assertEqual(runs['0009-B-r3']['slow_txt'], '65 s / 29% !')
        self.assertEqual(runs['0002-d0-r1']['slow_txt'], 'no')
        self.assertIn('scored runs with the slow state in the window: 0009-B-r3', text)
        # the arm table is repeated without B-r2 (scene), B-r3 (slow), d0-r3 (BG+) and d3-r1 (SAT)
        self.assertEqual(J['arms_clean']['B']['n'], 1)
        self.assertEqual(J['arms_clean']['d0']['n'], 2)
        self.assertNotIn('d3', J['arms_clean'])
        self.assertIn('## Arms without runs that have the slow state in the window, a scene flag or a background flag',
                      text)
        self.assertNotIn('FUNCTIONAL ONLY', text)
        # background: 12 x busy - 2 game cores over the 6 sys.csv samples in the window
        b = runs['0002-d0-r1']['bg']
        self.assertEqual(b['samples'], 6)
        self.assertAlmostEqual(b['busy_med'], 0.5)
        self.assertAlmostEqual(b['game_cores'], 2.0)
        self.assertAlmostEqual(b['bg_cores'], 4.0)
        self.assertFalse(b['sat'])
        self.assertAlmostEqual(runs['0002-d0-r1']['game_cores'], 2.0)
        self.assertEqual(runs['0002-d0-r1']['bg_flags'], [])
        self.assertEqual(runs['0008-d0-r3']['bg_flags'], ['BG+'])
        self.assertAlmostEqual(runs['0008-d0-r3']['bg']['bg_cores'], 7.0)
        self.assertEqual(runs['0004-d3-r1']['bg_flags'], ['SAT'])
        self.assertAlmostEqual(runs['0004-d3-r1']['bg']['bg_cores'], 10.0)
        self.assertAlmostEqual(J['bg']['ref'], 4.0)
        self.assertFalse(J['bg']['all_sat'])
        self.assertIn("reference: median of this matrix's 8 unsaturated scored runs = 4.00 cores", text)
        self.assertIn('- SAT runs: 0004-d3-r1', text)
        self.assertIn('- BG+ runs: 0008-d0-r3 (7.0 cores)', text)
        self.assertIn('> **CPU SATURATED**: 1 of 7 kept runs with sys.csv', text)
        self.assertIn('| 4.0 (4.0..7.0) (1 / 0) |', text)   # d0's background cell in the arm table
        self.assertIn('| >=10.0 (10.0..10.0) (0 / 1) |', text)   # d3: its only kept run is SAT, so a floor
        self.assertIn('threshold: max(floor 0.015, 2.0 x largest leave-one-out distance 0.003) = 0.015', text)
        self.assertIn('| 2.00 | 4.0 (p90 4.0; busy 50%) |', text)
        self.assertIn('>=10.0 (p90 10.0; busy 100%) SAT', text)
        # task #9 bins: the 5.7 s windows give one 10 s bin each, equal to the whole window
        sb = runs['0002-d0-r1']['stat_bins']
        self.assertEqual(len(sb), 1)
        self.assertAlmostEqual(sb[0]['p99_ms'], 40.0)
        self.assertAlmostEqual(sb[0]['t1'], 5.7)
        self.assertEqual(sb[0]['frames'], st['frames'])
        self.assertIn("## 10 s bins of each run's scored window", text)
        self.assertIn('### p99 ms per 10 s', text)
        self.assertEqual(J['bins']['arms']['d0']['n'], 3)

    def test_bins_option(self):
        js = os.path.join(self.tmp, 'bins.json')
        rc, text = run_main([self.mdir, '--no-timerq', '--bg-ref', 'none', '--bin-s', '2', '--json', js])
        self.assertEqual(rc, 0)
        with open(js, encoding='utf-8') as fh:
            J = json.load(fh)
        sb = {x['name']: x for x in J['runs']}['0002-d0-r1']['stat_bins']
        # 5.7 s: 0-2, 2-4, 4-5.7 (1.7 s >= half a bin: kept); every frame and every slow frame in exactly one bin
        self.assertEqual([(b['t0'], round(b['t1'], 6)) for b in sb], [(0.0, 2.0), (2.0, 4.0), (4.0, 5.7)])
        self.assertEqual(sum(b['frames'] for b in sb), 1000)
        self.assertEqual(sum(b['over33'] for b in sb), 20)
        self.assertIn('| 0-2 s | 2-4 s | 4-6 s | whole window |', text)
        self.assertIn('**d0** median, 3 kept', text)

    def test_background_reference_dir_and_cores(self):
        ref = os.path.join(self.tmp, 'refcopy', NAME)
        shutil.copytree(self.mdir, ref)
        rc, text = run_main([self.mdir, '--no-timerq', '--bg-ref', ref])
        self.assertEqual(rc, 0)
        self.assertIn('reference: median of the 8 unsaturated scored runs of %s = 4.00 cores' % NAME, text)
        self.assertIn('- reference dir %s: 9 scored runs, 9 with sys.csv (1 of them SAT); game cores there' % NAME, text)
        self.assertIn('d0 2.00 (n=3)', text)
        rc, text = run_main([self.mdir, '--no-timerq', '--bg-ref', 'none', '--bg-ref-cores', '2.5'])
        self.assertIn('reference: --bg-ref-cores = 2.50 cores', text)
        self.assertIn('0002-d0-r1 (4.0 cores)', text)   # 4.0 > 2.5 + 1.0
        self.assertNotIn('0004-d3-r1 (', text.split('- BG+ runs:')[1].splitlines()[0])  # SAT, not BG+

    def test_all_keeps_functional_runs(self):
        rc, text = run_main([self.mdir, '--no-timerq', '--bg-ref', 'none', '--all'])
        self.assertEqual(rc, 0)
        self.assertIn('FUNCTIONAL ONLY', text)
        self.assertIn('| n0 |  | 1 n<3! |', text)

    def test_mismatch_is_reported(self):
        mdir = os.path.join(self.tmp, 'tampered', NAME)
        shutil.copytree(self.mdir, mdir)
        res = os.path.join(mdir, 'results.csv')
        with open(res, newline='') as fh:
            rows = list(csv.DictReader(fh))
        rows[1]['fps_mean'] = '170.000'
        for r in rows:  # point run_dir at a missing path: the tool falls back to <dir>\runs\<name>
            r['run_dir'] = os.path.join('Z:\\gone', os.path.basename(r['run_dir']))
        with open(res, 'w', newline='') as fh:
            wtr = csv.DictWriter(fh, COLS, quoting=csv.QUOTE_ALL)
            wtr.writeheader()
            wtr.writerows(rows)
        rc, text = run_main([mdir, '--no-timerq', '--bg-ref', 'none'])
        self.assertEqual(rc, 0)
        self.assertIn('9 of 10 runs with a window agree', text)
        self.assertIn('MISMATCH: 0002-d0-r1: results.csv fps_mean', text)

    @unittest.skipIf(os.environ.get('W4B_SKIP_PS') == '1' or shutil.which('powershell') is None,
                     'timerq_slowstate.ps1 test skipped')
    def test_timerq_integration(self):
        rows, note = wr.run_timerq(self.mdir, 800, 3)
        self.assertIsNotNone(rows, note)
        self.assertEqual(rows['0009-B-r3']['onset_s'], '65')
        self.assertEqual(rows['0009-B-r3']['slow_pct'], '7')   # 6 of the 86 samples from the first frame on
        self.assertEqual(rows['0002-d0-r1']['onset_s'], '-')
        self.assertEqual(len(rows), 10)


if __name__ == '__main__':
    unittest.main(verbosity=1)
