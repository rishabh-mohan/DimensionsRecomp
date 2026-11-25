#!/usr/bin/env python3
"""Synthetic check of s33_fields.py (M6). Builds test-fields/ and checks the report and exit codes."""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(HERE, 'test-fields')
PRE = '[2026-11-25 01:00:%02d.000] [info] [gpu] [t100] '
OLD = ('slow frame #{f}: {ms} ms | gpu-thread idle 0.0 | host-gpu wait 0.0 (0x) | shader translate 0.0 (0x) | '
       'pipeline create 0.1 (2x), new {new} | texture load 0.0 (0x) | readback 0x 0 KB, 0 stalled | '
       'cpu-write invalidations 0x 0 KB (on memexport pages 0x 0 KB) | memexport syncs 0 (0 KB), on demand 0 (0 KB)')
NEW = OLD + ' | memexport full-buffer 0x (total 0) | dropped draws {dd} | forced pipeline waits {fw} ({fn}x)'


def w(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for i, l in enumerate(lines):
            f.write(PRE % (i % 60) + l + '\n')


def main():
    if os.path.isdir(T):
        shutil.rmtree(T)
    on = os.path.join(T, '20261125-010000-s33-onsf')
    # rotation: game.2.log oldest (latch + burst), game.1.log, game.log newest (late drop)
    w(os.path.join(on, 'game.2.log'), [
        'd3d12_pipeline_creation_no_wait: not waiting for pipeline creation at the end of submissions; x',
        NEW.format(f=10, ms='300.0', new=67, dd=5, fw='0.0', fn=0),
        NEW.format(f=11, ms='20.0', new=0, dd=40, fw='12.5', fn=1)])
    w(os.path.join(on, 'game.1.log'), [NEW.format(f=12, ms='18.0', new=0, dd=3, fw='0.0', fn=2)])
    w(os.path.join(on, 'game.log'), [NEW.format(f=500, ms='17.5', new=0, dd=1, fw='0.0', fn=0),
                                     NEW.format(f=501, ms='120.0', new=0, dd=0, fw='0.0', fn=0)])
    old = os.path.join(T, '0101-base-r1')
    w(os.path.join(old, 'game.log'), [OLD.format(f=10, ms='400.0', new=67)])
    bad = os.path.join(T, '0102-off-r1')
    w(os.path.join(bad, 'game.log'), [OLD.format(f=10, ms='30.0', new=1) + ' | dropped draws x | forced'])
    empty = os.path.join(T, 'empty')
    os.makedirs(empty)
    py = [sys.executable, '-B', os.path.join(HERE, 's33_fields.py')]
    fails = []

    def run(args, want_rc, want_txt=()):
        p = subprocess.run(py + args, capture_output=True, text=True)
        ok = p.returncode == want_rc and all(t in p.stdout for t in want_txt)
        print('%s rc %d (want %d) %s' % ('ok  ' if ok else 'FAIL', p.returncode, want_rc, ' '.join(args)[-80:]))
        if not ok:
            fails.append(args)
            print(p.stdout)
        return p.stdout

    out = run([on, old], 0, [
        '(arm onsf)  logs 3', 'latch: INFO not-waiting 1, WARN ignored 0',
        'frames >=100 ms 2 (420.0 ms), >=250 ms 1 (300.0 ms); misses 67',
        'dropped draws 49 in 4 frames, last at frame 500; late drops 1 (max gap 490 frames)',
        'forced pipeline waits 12.5 ms total (3 calls), max 12.5 ms in one frame',
        '(arm base)', '#33 fields: n/a'])
    run(['--arm', 'xyz=' + on, '--late-frames', '1000'], 0, ['(arm xyz)', 'late drops 0'])
    run([bad], 1, ['WARN unparsed #33 fields at game.log:1'])
    run([empty], 1, ['WARN no game*.log'])
    run([], 2)
    run(['--arm', 'a-b=' + on], 2)
    run(['--late-frames', 'x', on], 2)
    run([os.path.join(T, 'missing')], 2)
    run(['--bogus', on], 2)
    with open(os.path.join(T, 'report.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print('RESULT %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
