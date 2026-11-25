#!/usr/bin/env python3
"""test_mp.py - selftest of mp2_same_frames.py and mp3_query_seq.py on synthetic run dirs (stdlib unittest).

Run: python -B build/agent7/session3/mp/test_mp.py -v  (output kept in selftest.out.txt)
Each tool gets PASS, FAIL and INCOMPLETE cases, through main() so the exit codes and --json are covered.
"""
import importlib.util
import io
import json
import os
import random
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MP2 = _load('mp2_same_frames', 'mp2_same_frames.py')
MP3 = _load('mp3_query_seq', 'mp3_query_seq.py')

BASE_LOG = [
    ('info', 'core', 'GPU route: direct native D3D-to-RHI; PM4 disabled'),
    ('info', 'core', 'Startup: overlays ready'),
    ('info', 'core', 'Native GPU: pipeline cache loaded 123 entries'),
    ('warning', 'core', 'Native GPU: texture format 0x1A emulated'),
    ('info', 'core', 'Title terminated; hard-exiting process.'),
]


def log_line(i, lvl, cat, msg):
    return '[2026-11-25 01:%02d:%02d.%03d] [%s] [%s] [t%d] %s\n' % (i // 3600 % 60, i // 60 % 60, i % 1000, lvl, cat,
                                                                  1000 + i % 7, msg)


def write_run(root, name, draws=None, fts=None, log=None, source='perf', share=None, first=10, extra_files=None,
              no_perf=False):
    d = os.path.join(root, 'runs', name)
    os.makedirs(d, exist_ok=True)
    if draws is not None and not no_perf:
        fts = fts or [3000 + (i % 5) * 1000 for i in range(len(draws))]
        with open(os.path.join(d, 'perf.csv'), 'w', newline='\n') as fh:
            fh.write('frame_time_us,fps,draw_calls,command_buffer_stalls\n')
            for i in range(first):
                fh.write('%d,0,%d,0\n' % (0 if i == 0 else 30000, 50))
            for ft, dc in zip(fts, draws):
                fh.write('%d,0,%d,0\n' % (ft, dc))
            fh.write('20000,0,9999,0\n')  # after the window: must be ignored
        win = {'first_row': first, 'rows': len(draws)}
        fj = {'source': source, 'column': 'frame_time_us', 'window': win, 'light_ms': 4.5}
        if share is not None:
            fj['share_lt_light'] = share
        with open(os.path.join(d, 'frames.json'), 'w') as fh:
            json.dump(fj, fh)
    lines = log if log is not None else BASE_LOG
    with open(os.path.join(d, 'game.log'), 'w', newline='\n') as fh:
        for i, (lvl, cat, msg) in enumerate(lines):
            fh.write(log_line(i, lvl, cat, msg))
    for fn, txt in (extra_files or {}).items():
        with open(os.path.join(d, fn), 'w', newline='\n') as fh:
            fh.write(txt)
    return d


def draws_dist(seed, shift=0, n=600):
    rnd = random.Random(seed)
    return [max(1, int(rnd.gauss(800 + shift, 60))) for _ in range(n)]


def run_main(mod, args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main(list(args) + ['--normal-priority'])
    return rc, buf.getvalue()


class MP2Tests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='mp2-')

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def make_matrix(self, cand_shift=0, cand_share=0.30, cand_log=None, ref2=True):
        # equivalent candidates reuse the ref seeds (1, 2), so their percentiles sit on a ref run's; a fresh seed
        # would fall outside a 2-run [min, max] band about 2 times in 3 (see test_literal_band_is_tight)
        write_run(self.root, '0100-n0-r1', draws_dist(1), share=0.28)
        if ref2:
            write_run(self.root, '0105-n0-r2', draws_dist(2), share=0.33)
        for k, seed in ((1, 1), (2, 2)):
            write_run(self.root, '01%d0-th3-r%d' % (k, k), draws_dist(seed, cand_shift), share=cand_share,
                      log=cand_log)
            write_run(self.root, '01%d5-th3cp3-r%d' % (k, k), draws_dist(3 - seed, cand_shift), share=cand_share,
                      log=cand_log)

    def test_literal_band_is_tight(self):
        # a fresh draw from the same distribution: the literal band may fail it, --spread-k reports/relaxes it
        write_run(self.root, '0100-n0-r1', draws_dist(1), share=0.30)
        write_run(self.root, '0105-n0-r2', draws_dist(2), share=0.31)
        write_run(self.root, '0110-th3-r1', draws_dist(3), share=0.305)
        rc, out = run_main(MP2, ['--dir', self.root, '--arms', 'th3'])
        self.assertIn(rc, (0, 1))
        if rc == 1:
            self.assertIn('x the ref spread', out)
        rc2, out2 = run_main(MP2, ['--dir', self.root, '--arms', 'th3', '--spread-k', '5'])
        self.assertEqual(rc2, 0, out2)

    def test_pass_dir(self):
        self.make_matrix()
        js = os.path.join(self.root, 'out.json')
        rc, out = run_main(MP2, ['--dir', self.root, '--json', js])
        self.assertEqual(rc, 0, out)
        self.assertIn('RESULT: PASS', out)
        with open(js) as fh:
            j = json.load(fh)
        self.assertEqual(j['verdict'], 'PASS')
        self.assertEqual(len(j['groups']), 2)
        self.assertEqual(j['groups'][0]['runs'][0]['dc']['n'], 600)  # 9999 row after the window ignored

    def test_fail_draw_calls_shift(self):
        self.make_matrix(cand_shift=200)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('FAIL       th3 0110-th3-r1 DC: draw_calls p50', out)

    def test_fail_light_share(self):
        self.make_matrix(cand_share=0.50)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('LS: light share 0.500', out)
        rc2, out2 = run_main(MP2, ['--dir', self.root, '--ls-pad', '0.2'])
        self.assertEqual(rc2, 0, out2)

    def test_fail_new_warning_and_allow(self):
        log = BASE_LOG[:-1] + [('warning', 'core', 'Native GPU: query 0x30001000 invalidated by failed draw'),
                               BASE_LOG[-1]]
        self.make_matrix(cand_log=log)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('no NEW key at >= warning (1)', out)
        rc2, out2 = run_main(MP2, ['--dir', self.root, '--allow-new', 'invalidated by failed draw'])
        self.assertEqual(rc2, 0, out2)

    def test_info_new_is_not_gated(self):
        log = BASE_LOG[:-1] + [('info', 'core', 'Native GPU: chain priority recorder tid=12 priority=1 ecoqos=opt-out'),
                               BASE_LOG[-1]]
        self.make_matrix(cand_log=log)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 0, out)
        self.assertIn('NEW 1', out)

    def test_fail_gone_warning_and_clean_exit(self):
        log = [x for x in BASE_LOG if x[0] != 'warning' and 'terminated' not in x[2]]
        self.make_matrix(cand_log=log)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('no GONE key at >= warning outside the noise (1)', out)
        self.assertIn('FAIL       th3 0110-th3-r1 LOG: clean-exit line present', out)

    def test_gone_explained_by_noise(self):
        many = [('warning', 'core', 'Native GPU: retry 1')] * 20
        write_run(self.root, '0100-n0-r1', draws_dist(1), share=0.3, log=BASE_LOG + many)
        write_run(self.root, '0105-n0-r2', draws_dist(2), share=0.31,
                  log=BASE_LOG + [('warning', 'core', 'Native GPU: retry 1')])
        write_run(self.root, '0110-th3-r1', draws_dist(1), share=0.305, log=BASE_LOG)
        rc, out = run_main(MP2, ['--dir', self.root, '--arms', 'th3'])
        self.assertEqual(rc, 0, out)
        self.assertIn('noise-explained', out)

    def test_incomplete_one_ref(self):
        self.make_matrix(ref2=False)
        rc, out = run_main(MP2, ['--dir', self.root])
        self.assertEqual(rc, 2, out)
        self.assertIn('INCOMPLETE ref runs: 1', out)

    def test_incomplete_native_source_and_fallback(self):
        write_run(self.root, '0100-n0-r1', draws_dist(1), share=0.3, source='native')
        write_run(self.root, '0105-n0-r2', draws_dist(2), share=0.31, source='native')
        write_run(self.root, '0110-th3-r1', draws_dist(3), share=0.305, source='native')
        rc, out = run_main(MP2, ['--dir', self.root, '--arms', 'th3'])
        self.assertEqual(rc, 2, out)
        self.assertIn('no perf.csv scored window', out)
        rc2, out2 = run_main(MP2, ['--dir', self.root, '--arms', 'th3', '--perf-fallback', 'whole', '--dc-pad', '0.5'])
        self.assertIn('whole perf.csv', out2)
        self.assertIn(rc2, (0, 1))

    def test_incomplete_missing_arm_explicit(self):
        r1 = write_run(self.root, 'a-r1', draws_dist(1), share=0.3)
        r2 = write_run(self.root, 'a-r2', draws_dist(2), share=0.31)
        rc, out = run_main(MP2, ['--ref', r1, '--ref', r2, '--cand', os.path.join(self.root, 'nope')])
        self.assertEqual(rc, 2, out)
        self.assertIn('no run dir', out)
        c = write_run(self.root, 'b-r1', draws_dist(2), share=0.305)
        rc, out = run_main(MP2, ['--ref', r1, '--ref', r2, '--cand', c])
        self.assertEqual(rc, 0, out)

    def test_light_share_fallback_from_perf(self):
        fts = [3000] * 300 + [6000] * 300
        r1 = write_run(self.root, 'a-r1', draws_dist(1), fts=fts)
        r2 = write_run(self.root, 'a-r2', draws_dist(2), fts=fts)
        x = MP2.run_metrics(r1)
        self.assertAlmostEqual(x['ls'], 0.5)
        self.assertIn('perf.csv frame_time_us', x['ls_src'])
        rc, out = run_main(MP2, ['--ref', r1, '--ref', r2, '--cand', r2, '--no-logdiff'])
        self.assertEqual(rc, 0, out)

    def test_zero_draw_calls_native_route(self):
        # native route: perf.csv draw_calls is 0 on every frame -> DC proxy vacuous -> INCOMPLETE unless --zero-dc info
        z = [0] * 600
        r1 = write_run(self.root, 'a-r1', z, share=0.30)
        r2 = write_run(self.root, 'a-r2', z, share=0.31)
        c = write_run(self.root, 'b-r1', z, share=0.305)
        rc, out = run_main(MP2, ['--ref', r1, '--ref', r2, '--cand', c])
        self.assertEqual(rc, 2, out)
        self.assertIn('INCOMPLETE DC proxy vacuous', out)
        rc, out = run_main(MP2, ['--ref', r1, '--ref', r2, '--cand', c, '--zero-dc', 'info'])
        self.assertEqual(rc, 0, out)

    def test_nearest_rank(self):
        self.assertEqual(MP2.nearest_rank(list(range(1, 11)), 0.5), 5)
        self.assertEqual(MP2.nearest_rank(list(range(1, 11)), 0.9), 9)
        self.assertEqual(MP2.nearest_rank(list(range(1, 11)), 0.1), 1)

    def test_logdiff_source(self):
        LD, src = MP2.load_logdiff()
        self.assertTrue(hasattr(LD, 'read'))
        LD2, src2 = MP2.load_logdiff(os.path.join(self.root, 'missing.py'))
        self.assertEqual(src2, 'embedded copy of logdiff.py')
        p = os.path.join(self.root, 'g.log')
        with open(p, 'w') as fh:
            for i, x in enumerate(BASE_LOG):
                fh.write(log_line(i, *x))
        self.assertEqual(LD.read(p)[0], LD2.read(p)[0])  # the embedded copy parses like logdiff.py


def qline(frame, addr, draws, samples, fsr='false', size='1920x1080'):
    return ('info', 'core', 'Native query value frame=%d fsr=%s size=%s query=%08X draws=%d samples=%d'
            % (frame, fsr, size, addr, draws, samples))


def qseq(seed, n=120, perturb=0.0, reorder=False, zero_out=0.0, base=0x30230000):
    """A synthetic trace: 6 queries read round-robin, one per frame; samples drift slowly."""
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        q = i % 6
        draws = 1 + q % 3
        samples = 0 if q == 5 else 1000 * (q + 1) + (i // 6) * 10
        if perturb and samples > 0 and rnd.random() < perturb:
            samples += rnd.choice((-1, 1)) * 7
        if zero_out and rnd.random() < zero_out:
            samples = 0
        rows.append([i + 3 + (1 if rnd.random() < 0.1 else 0), base + q * 0x1000, draws, samples])
    if reorder:
        rnd2 = random.Random(seed + 99)
        for k in range(0, n - 1, 2):
            if rnd2.random() < 0.6:
                rows[k][1:], rows[k + 1][1:] = rows[k + 1][1:], rows[k][1:]
    return [qline(*r) for r in rows]


class MP3Tests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='mp3-')

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def make(self, th3=None, cp3=None, ref2=True, refq=None):
        head, tail = BASE_LOG[:2], BASE_LOG[-1:]
        write_run(self.root, '0100-n0q-r1', log=head + (refq or qseq(1, perturb=0.05)) + tail)
        if ref2:
            write_run(self.root, '0102-n0q-r2', log=head + qseq(2, perturb=0.05) + tail)
        for k in (1, 2):
            write_run(self.root, '010%d-th3q-r%d' % (k + 3, k), log=head + (th3 or qseq(10 + k, perturb=0.05)) + tail)
        write_run(self.root, '0108-th3cp3q-r1', log=head + (cp3 or qseq(20, perturb=0.05)) + tail)

    def test_pass(self):
        self.make()
        js = os.path.join(self.root, 'q.json')
        rc, out = run_main(MP3, ['--dir', self.root, '--json', js])
        self.assertEqual(rc, 0, out)
        with open(js) as fh:
            j = json.load(fh)
        self.assertEqual(j['verdict'], 'PASS')
        self.assertEqual(len(j['comparisons']), 2)
        self.assertEqual(j['runs']['0100-n0q-r1']['lines'], 120)

    def test_fail_reorder(self):
        self.make(cp3=qseq(20, perturb=0.05, reorder=True))
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('FAIL       Q3 th3cp3q vs th3q 0108-th3cp3q-r1: order agreement', out)

    def test_fail_zero_samples(self):
        self.make(th3=qseq(11, perturb=0.05, zero_out=0.3))
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('visible agreement', out)

    def test_fail_unsupported(self):
        bad = qseq(11, perturb=0.05) + [('error', 'core', 'Native GPU: unsupported query GetData size=8 '
                                                         '(no fabricated result)')]
        self.make(th3=bad)
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn("FAIL       Q2 0104-th3q-r1: 0 'unsupported query' lines (1)", out)

    def test_fail_failed_draw(self):
        bad = qseq(11, perturb=0.05) + [('warning', 'core', 'Native GPU: query 0x3027C000 invalidated by failed draw')] * 6
        self.make(th3=bad)
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 1, out)
        self.assertIn('Q4 th3q vs n0q 0104-th3q-r1: failed-draw invalidations 6', out)

    def test_incomplete_no_query_lines(self):
        self.make(th3=[('info', 'core', 'nothing traced')])
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 2, out)
        self.assertIn('UNCLEAR', out)

    def test_incomplete_one_ref_and_missing_arm(self):
        self.make(ref2=False)
        os.rename(os.path.join(self.root, 'runs', '0108-th3cp3q-r1'), os.path.join(self.root, 'runs', 'x-gone'))
        rc, out = run_main(MP3, ['--dir', self.root])
        self.assertEqual(rc, 2, out)
        self.assertIn('INCOMPLETE ref runs: 1', out)
        self.assertIn('INCOMPLETE th3cp3q vs th3q: candidate runs found: 0', out)

    def test_explicit_mode_and_address_renaming(self):
        r1 = write_run(self.root, 'a', log=qseq(1, perturb=0.05))
        r2 = write_run(self.root, 'b', log=qseq(2, perturb=0.05))
        c = write_run(self.root, 'c', log=qseq(3, perturb=0.05, base=0x40100000))  # other guest addresses
        rc, out = run_main(MP3, ['--ref', r1, '--ref', r2, '--cand', c])
        self.assertEqual(rc, 0, out)
        x = MP3.read_run(c)
        self.assertEqual(x['slots'][:7], [0, 1, 2, 3, 4, 5, 0])

    def test_rotated_logs_order(self):
        d = os.path.join(self.root, 'rot')
        os.makedirs(d)
        with open(os.path.join(d, 'game.1.log'), 'w') as fh:
            fh.write(log_line(0, *qline(1, 0x10, 1, 5)))
        with open(os.path.join(d, 'game.log'), 'w') as fh:
            fh.write(log_line(1, *qline(2, 0x20, 2, 6)))
        x = MP3.read_run(d)
        self.assertEqual([r[0] for r in x['seq']], [1, 2])

    def test_trace_regex_matches_source_format(self):
        # format string of queries.cpp:67: "Native query value frame={} fsr={} size={}x{} query={:08X} draws={} samples={}"
        ln = '[2026-11-25 01:00:00.000] [info] [core] [t5] Native query value frame=12 fsr=true size=1280x720 ' \
             'query=3023A000 draws=3 samples=4567'
        m = MP3.TRACE.search(ln)
        self.assertEqual(m.groups(), ('12', 'true', '1280', '720', '3023A000', '3', '4567'))


if __name__ == '__main__':
    unittest.main()
