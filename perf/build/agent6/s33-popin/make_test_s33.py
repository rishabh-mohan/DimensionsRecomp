"""#33 pop-in (E5.1 for M6, 2026-11-25): synthetic tests of expect-s33.json, RUN-S33-LOGDIFF.cmd and w6_kit.py's
harness mode. Builds build/agent6/s33-popin/test-s33/ from copies of real night runs (game*.log, run.json, sys.csv
only; build/agent8 is read, never written), with the #33 lines injected just before 'Window closing':
  matrix/       matrix-mode folder (runs/HHMM-<arm>-r1 + matrix.json from matrix-s33-draft.json), must pass
  matrix-neg/   INFO line in the off arm, WARN missing in the gasync arm: must FAIL
  harness/      fake Agent 3 harness run dirs <yyyyMMdd-HHmmss>-s33-<arm> (harness-style run.json; arms and cvars
                from harness-s33.json), must pass
  harness-neg/  onsf without INFO, offwarm with INFO, gthr0 with an unlisted d3d12_bindless cvar, base with an
                unlisted slow_frame_log_ms, onstop killed: must FAIL
  hyphen-expect.json  expect-s33.json with offsf renamed off-sf: the kit must refuse it (exit 2)
Usage: python -B build/agent6/s33-popin/make_test_s33.py           (build)
       python -B build/agent6/s33-popin/make_test_s33.py --check   (check the out-* folders and EXITCODES.txt that
                                                                    build/agent6/wnight/s3-regress/run_test_s33.ps1
                                                                    wrote into test-s33/)
"""
import glob
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
HERE = os.path.join(ROOT, 'build', 'agent6', 's33-popin')
DST = os.path.join(HERE, 'test-s33')
NIGHT = os.path.join(ROOT, 'build', 'agent8', 'matrix')
CLEAN = ('20261123-0108', '0110-off-r1')   # W9 off, PASS, W/E/C 40/0/0
RACE = ('20261123-0401', '0429-off-r3')    # W9 off, the benign 'Execution complete' race (INFO)
INFO = ('d3d12_pipeline_creation_no_wait: not waiting for pipeline creation at the end of submissions; draws stay '
        'skipped until their pipeline is ready')
WARN = ('d3d12_pipeline_creation_no_wait ignored: it needs async_shader_compilation, pipeline creation threads and '
        'bindless resources')
SF_OLD = ('slow frame #%d: 19.4 ms | gpu-thread idle 1.7 | host-gpu wait 0.0 (0x) | shader translate 0.0 (0x) | '
          'pipeline create 0.0 (0x), new 0 | texture load 0.0 (1x) | readback 0x 0 KB, 0 stalled | cpu-write '
          'invalidations 5x 20 KB (on memexport pages 0x 0 KB) | memexport syncs 0 (0 KB), on demand 0 (0 KB) | '
          'memexport full-buffer 0x (total 0)')
SF_NEW = SF_OLD + ' | dropped draws %d | forced pipeline waits 0.0 (0x)'
RAD = 'resolve after drop: dest 1F2E3000 after 3 skipped draws (pipeline in creation) | resolves 2, skipped draws 3'
LINE_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d [0-9:.]+)\] ')
# per arm: slow-frame format (None / 'old' / 'new') and the extra lines
KIND = {
    'base': (None, []), 'off': (None, []), 'basesf': ('old', []), 'offsf': ('new', []), 'offwarm': ('new', []),
    'offd': ('new', [('info', RAD), ('info', RAD)]),
    'onsf': ('new', [('info', INFO)]), 'onwarm': ('new', [('info', INFO)]), 'onstop': ('new', [('info', INFO)]),
    'ond': ('new', [('info', INFO), ('info', RAD), ('info', RAD)]),
    'gthr0': ('new', [('warning', WARN)]), 'gasync': ('new', [('warning', WARN)]), 'gbindful': ('new', [('warning', WARN)]),
}


def arms_of(fn):
    with open(os.path.join(HERE, fn), encoding='utf-8-sig') as fh:
        return {a['id']: a for a in json.load(fh)['arms']}


def copy_run(src, d, kind, drop=(), add=(), sys_csv=True):
    """Copy game*.log (+ sys.csv) of night run src into d, injecting the arm's lines before 'Window closing'."""
    os.makedirs(d)
    sfmt, extra = KIND[kind]
    extra = [x for x in extra if x[1] not in drop] + list(add)
    s = os.path.join(NIGHT, src[0], 'runs', src[1])
    for f in sorted(glob.glob(os.path.join(s, 'game*.log'))):
        with open(f, encoding='utf-8', errors='replace', newline='') as fh:
            lines = fh.read().splitlines(True)
        if os.path.basename(f).lower() == 'game.log':
            at = next((i for i, x in enumerate(lines) if 'Window closing, shutting down' in x), len(lines) - 1)
            m = LINE_RE.match(lines[at - 1]) or LINE_RE.match(lines[0])
            ts = m.group(1) if m else '2026-11-25 01:00:00.000'
            new = [('info', SF_OLD % (100 + k) if sfmt == 'old' else SF_NEW % (100 + k, k % 3))
                   for k in range(3)] if sfmt else []
            lines[at:at] = ['[%s] [%s] [gpu] [t999] %s\n' % (ts, lvl, msg) for lvl, msg in extra + new]
        with open(os.path.join(d, os.path.basename(f)), 'w', encoding='utf-8', newline='') as fh:
            fh.writelines(lines)
    if sys_csv and os.path.exists(os.path.join(s, 'sys.csv')):
        shutil.copy2(os.path.join(s, 'sys.csv'), d)
    with open(os.path.join(s, 'run.json'), encoding='utf-8-sig') as fh:
        return json.load(fh)


def write_json(p, d):
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, indent=1)


def build_matrix(name, neg):
    arms = arms_of('matrix-s33-draft.json')
    top = os.path.join(DST, name)
    for i, (arm, a) in enumerate(sorted(arms.items())):
        src = RACE if arm == 'offd' else CLEAN
        drop = (WARN,) if (neg and arm == 'gasync') else ()
        add = [('info', INFO)] if (neg and arm == 'off') else []
        d = os.path.join(top, 'runs', '%04d-%s-r1' % (100 + i, arm))
        rj = copy_run(src, d, arm, drop, add)
        rj['bin_dir'] = os.path.join(ROOT, a['bin'].replace('/', os.sep))
        rj['cvars'] = list(a['cvars'])
        rj.setdefault('params', {})['cvar'] = list(a['cvars'])
        rj['tag'] = '%s-r1' % arm
        write_json(os.path.join(d, 'run.json'), rj)
        print('%s/%s <- %s/%s%s%s' % (name, os.path.basename(d), src[0], src[1], ' drop WARN' if drop else '',
                                      ' + INFO' if add else ''))
    write_json(os.path.join(top, 'matrix.json'), {
        'title': '%sTEST ONLY (E5.1, make_test_s33.py): arms of matrix-s33-draft.json on copies of night runs'
                 % ('NEGATIVE ' if neg else ''),
        'reference': 'offsf', 'arms': [dict(id=k, bin=a['bin'], cvars=a['cvars'], env=a.get('env') or {})
                                       for k, a in sorted(arms.items())]})


def build_harness(name, neg):
    arms = arms_of('harness-s33.json')
    top = os.path.join(DST, name)
    plan = [(arm, 1) for arm in sorted(arms)] + ([('onstop', 2)] if not neg else [])
    if neg:
        plan = [('offsf', 1), ('onsf', 1), ('offwarm', 1), ('gthr0', 1), ('base', 1), ('onstop', 1)]
    for i, (arm, k) in enumerate(plan):
        a = arms[arm]
        drop = (INFO,) if (neg and arm == 'onsf') else ()
        add = [('info', INFO)] if (neg and arm == 'offwarm') else []
        d = os.path.join(top, '20261125-01%02d00-s33-%s%s' % (i, arm, '-%d' % k if k > 1 else ''))
        copy_run(CLEAN, d, arm, drop, add, sys_csv=(arm != 'onwarm'))
        cv = dict(x.split('=', 1) for x in a['cvars'])
        if neg and arm == 'gthr0':
            cv['d3d12_bindless'] = 'false'
        if neg and arm == 'base':
            cv['slow_frame_log_ms'] = '1'
        killed = neg and arm == 'onstop'
        secs = a['seconds'][k - 1] if isinstance(a['seconds'], list) else a['seconds']
        write_json(os.path.join(d, 'run.json'), {
            'harness': 'harness/run-game.ps1', 'mode': 'FUNCTIONAL ONLY (TEST, make_test_s33.py), NOT FOR TIMING',
            'tag': 's33-%s' % arm, 'run_dir': d, 'bin_dir': os.path.join(ROOT, a['bin'].replace('/', os.sep)),
            'env': {'LEGO_NATIVE_FRAME_METRICS': os.path.join(d, 'frames.csv'), 'AGENT3_VPAD': os.path.join(d, 'vpad-state.bin')},
            'cvars': cv, 'started': '2026-11-25T01:%02d:00-06:00' % i, 'seconds_requested': secs,
            'exited_early': False, 'exit_code': 1 if killed else 0, 'exit_code_hex': '0x%08X' % (1 if killed else 0),
            'close_method': 'kill' if killed else 'wm_close', 'close_seconds': 60.0 if killed else 1.1,
            'wer_seen': False, 'crash_events': [], 'dumps': []})
        print('%s/%s <- %s/%s cvars %s%s%s%s' % (name, os.path.basename(d), CLEAN[0], CLEAN[1], cv,
                                                 ' drop INFO' if drop else '', ' + INFO' if add else '',
                                                 ' KILLED' if killed else ''))


def build():
    assert os.path.normpath(DST).startswith(os.path.normpath(HERE) + os.sep)
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    build_matrix('matrix', False)
    build_matrix('matrix-neg', True)
    build_harness('harness', False)
    build_harness('harness-neg', True)
    with open(os.path.join(HERE, 'expect-s33.json'), encoding='utf-8-sig') as fh:
        ex = json.load(fh)
    ex['arms'] = {('off-sf' if k == 'offsf' else k): v for k, v in ex['arms'].items()}
    write_json(os.path.join(DST, 'hyphen-expect.json'), ex)
    print('wrote', os.path.relpath(DST, ROOT))


# --check: expected results per out folder: (exit code, {arm: (verdicts allowed, texts that must be in its
# fail+note+info, texts that must not be in its notes)})
CHECKS = {
    'matrix': (0, {
        'offsf': (('PASS',), [], []), 'onsf': (('PASS',), [], []), 'off': (('PASS', 'NOTE'), [], []),
        'gthr0': (('PASS',), [], ['levels W/E/C', 'NEW warning']), 'gasync': (('PASS',), [], ['levels W/E/C', 'NEW warning']),
        'gbindful': (('PASS',), [], ['levels W/E/C', 'NEW warning']), 'ond': (('PASS',), [], []),
        'basesf': (('NOTE',), ['logdiff GONE: [info] [gpu] slow frame #'], []),
        'offd': (('PASS', 'NOTE'), ['benign hard-exit race'], [])}),
    'matrix-neg': (1, {
        'off': (('FAIL',), ['forbidden "d3d12_pipeline_creation_no_wait"'], []),
        'gasync': (('FAIL',), ['missing required "d3d12_pipeline_creation_no_wait ignored"'], []),
        'onsf': (('PASS',), [], []), 'gthr0': (('PASS',), [], [])}),
    'harness': (0, {
        'offsf': (('PASS',), ['slow state skipped (harness run: run.json has no ff_signal_epoch_s)'], []),
        'onwarm': (('PASS',), ['slow state skipped (harness run: no sys.csv)'], []),
        'onstop': (('PASS',), [], []), 'gthr0': (('PASS',), [], ['levels W/E/C']), 'base': (('PASS', 'NOTE'), [], []),
        'offwarm': (('PASS',), [], []), 'ond': (('PASS',), [], [])}),
    'harness-neg': (1, {
        'offsf': (('PASS',), [], []),
        'onsf': (('FAIL',), ['missing required "d3d12_pipeline_creation_no_wait: not waiting'], []),
        'offwarm': (('FAIL',), ['forbidden "d3d12_pipeline_creation_no_wait"'], []),
        'gthr0': (('FAIL',), ["unlisted s33 keys ['d3d12_bindless=false']"], []),
        'base': (('FAIL',), ["unlisted s33 keys ['slow_frame_log_ms=1']"], []),
        'onstop': (('FAIL',), ["status BAD, problems ['exit code 1', 'close_method kill']"], [])}),
}
EXIT_ONLY = {'hyphen-expect': 2, 'hyphen-run': 2, 'mixed': 2, 'none': 2, 'noargs': 2}


def check():
    with open(os.path.join(DST, 'EXITCODES.txt'), encoding='utf-8-sig') as fh:
        rc = dict(x.split('=', 1) for x in fh.read().split() if '=' in x)
    bad = []
    for k, want in sorted(EXIT_ONLY.items()):
        if rc.get(k) != str(want):
            bad.append('%s: exit %s, want %d' % (k, rc.get(k), want))
    for name, (want, arms) in sorted(CHECKS.items()):
        if rc.get(name) != str(want):
            bad.append('%s: exit %s, want %d' % (name, rc.get(name), want))
        with open(os.path.join(DST, 'out-' + name, 'w6-data.json'), encoding='utf-8') as fh:
            data = json.load(fh)
        if data.get('mode') != ('harness' if name.startswith('harness') else 'matrix'):
            bad.append('%s: mode %s' % (name, data.get('mode')))
        for arm, (verdicts, must, mustnot) in sorted(arms.items()):
            A = data['arms'].get(arm)
            if A is None:
                bad.append('%s/%s: no such arm' % (name, arm))
                continue
            allr = A['fail'] + A['note'] + A['info']
            if A['verdict'] not in verdicts:
                bad.append('%s/%s: verdict %s, want %s: %s' % (name, arm, A['verdict'], verdicts, [x[:120] for x in allr]))
            for t in must:
                if not any(t in x for x in allr):
                    bad.append('%s/%s: no reason with %r' % (name, arm, t))
            for t in mustnot:
                if any(t in x for x in A['note']):
                    bad.append('%s/%s: a NOTE with %r' % (name, arm, t))
        print('%s: exit %s; %s' % (name, rc.get(name), '; '.join('%s %s' % (k, v['verdict']) for k, v in sorted(data['arms'].items()))))
    print('exit-only cases: %s' % ', '.join('%s=%s' % (k, rc.get(k)) for k in sorted(EXIT_ONLY)))
    for b in bad:
        print('BAD', b)
    print('RESULT: %s' % ('FAIL (%d)' % len(bad) if bad else 'PASS'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(check() if '--check' in sys.argv[1:] else (build() or 0))
