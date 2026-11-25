#!/usr/bin/env python3
"""test_soak_check.py - self-test of soak_check.py on synthetic game.log lines (M7, session 3, S3T-7).

Run (Below Normal): python -B build/agent7/s4-r1s2/soak-check/test_soak_check.py
Writes only build/agent7/s4-r1s2/soak-check/selftest-tmp/ (deleted at the end) and selftest.out.txt.
Exit 0 = every case gave its expected verdict.

The synthetic generator mimics the patched code: per frame a few splits fall due; a due split is held for a query
(held_query) or goes async (chunks += 1, then splits += 1); each family logs at most every 10 s, the async line
inside EndSubmissionAsync (before ++splits), the split line after it; queued_max is a running max <= 3.
"""
import io
import os
import shutil
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import soak_check as sc  # noqa: E402

TMP = os.path.join(HERE, 'selftest-tmp')
OUT = os.path.join(HERE, 'selftest.out.txt')


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return '[2026-11-26 %02d:%02d:%06.3f]' % (10 + int(h), int(m), s)


def gen(seconds=600, fps=60, splits_per_frame=2, query_every=7, full_every=0, init=True, split_init=True):
    """Return a list of game.log lines for a healthy async-split run."""
    L = []
    t0 = 5.0
    if split_init:
        L.append('%s [info] [gpu] [t4242] d3d12_submit_split_kb: splitting submissions at 64 KB of deferred commands' % ts(t0))
    if init:
        L.append('%s [info] [gpu] [t4242] d3d12_async_submit: submitting splits on the submit thread (3 slots)' % ts(t0))
    st = dict(frame=0, submission=1, chunks=0, queued_max=0, full_waits=0, full_wait_us=0, drains_waited=0,
              drain_wait_us=0, worker_us=0, splits=0, failed=0, held_query=0, held_scratch=0, held_pipelines=0)
    last_a = last_s = -1e9
    due = 0
    for fr in range(seconds * fps):
        t = t0 + 1.0 + fr / fps
        st['frame'] = fr
        for k in range(splits_per_frame):
            due += 1
            if query_every and due % query_every == 0:
                st['held_query'] += 1
            else:
                # EndSubmissionAsync
                if full_every and due % full_every == 0:
                    st['full_waits'] += 1
                    st['full_wait_us'] += 150
                st['chunks'] += 1
                st['queued_max'] = max(st['queued_max'], 1 + (due % 3))
                st['worker_us'] += 90
                st['submission'] += 1
                if t - last_a >= 10:
                    last_a = t
                    L.append('%s [info] [gpu] [t4242] d3d12_async_submit: frame=%d submission=%d chunks=%d queued_max=%d '
                             'full_waits=%d full_wait_us=%d drains_waited=%d drain_wait_us=%d worker_us=%d'
                             % (ts(t), st['frame'], st['submission'], st['chunks'], st['queued_max'], st['full_waits'],
                                st['full_wait_us'], st['drains_waited'], st['drain_wait_us'], st['worker_us']))
                st['splits'] += 1
            if t - last_s >= 10:
                last_s = t
                L.append('%s [info] [gpu] [t4242] d3d12_submit_split: frame=%d submission=%d splits=%d failed=%d '
                         'held_query=%d held_scratch=%d held_pipelines=%d'
                         % (ts(t), st['frame'], st['submission'], st['splits'], st['failed'], st['held_query'],
                            st['held_scratch'], st['held_pipelines']))
        # end of frame: swap drains the queue now and then
        if fr % 5 == 0:
            st['drains_waited'] += 1
            st['drain_wait_us'] += 40
        st['submission'] += 1
        if fr % 600 == 0:
            L.append('%s [info] [gpu] [t4242] unrelated line frame=%d' % (ts(t), fr))
    L.append('%s [info] [kernel] [t4242] Title terminated; hard-exiting process' % ts(t0 + seconds + 2))
    return L


def mutate(lines, pred, fn, which=0):
    """Apply fn to the which-th line matching pred."""
    out, n = [], 0
    for ln in lines:
        if pred(ln):
            if n == which:
                ln = fn(ln)
            n += 1
        out.append(ln)
    return out


def is_async(ln):
    return 'd3d12_async_submit: frame=' in ln


def is_split(ln):
    return 'd3d12_submit_split: frame=' in ln


def sub_kv(key, val):
    import re
    return lambda ln: re.sub(r'\b%s=\d+' % key, '%s=%d' % (key, val), ln)


def write_run(name, files):
    d = os.path.join(TMP, name)
    os.makedirs(d, exist_ok=True)
    for fn, lines in files.items():
        with open(os.path.join(d, fn), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + ('\n' if lines else ''))
    return d


def run(path, *args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = sc.main([path] + list(args))
    return rc, buf.getvalue()


def main():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    good = gen()
    na = sum(1 for l in good if is_async(l))
    ns = sum(1 for l in good if is_split(l))
    cases = []

    def case(name, files, expect, *args, must=None):
        cases.append((name, files, expect, args, must))

    case('good soak', {'game.log': good}, 0, must=['RESULT: PASS', 'per frame'])
    case('good soak as a file path', None, 0)
    case('row j with full waits', {'game.log': gen(seconds=120, full_every=11)}, 0, '--row', 'j')
    case('row j without full waits', {'game.log': gen(seconds=120)}, 1, '--row', 'j', must=['row j: full_waits > 0'])
    case('no log at all', {}, 2)
    case('log without any #19 line', {'game.log': ['[2026-11-26 10:00:00.000] [info] [gpu] [t1] hello']}, 2)
    case('init only, no counter lines', {'game.log': gen(seconds=0)}, 1)  # no split line -> held_query FAIL
    case('async counter decreases', {'game.log': mutate(good, is_async, sub_kv('worker_us', 0), which=5)}, 1,
         must=['async counters never decrease'])
    case('drains_waited decreases', {'game.log': mutate(good, is_async, sub_kv('drains_waited', 0), which=7)}, 1)
    case('queued_max = 4', {'game.log': mutate(good, is_async, sub_kv('queued_max', 4), which=na - 1)}, 1,
         must=['queued_max <= 3'])
    case('chunks = 0 at the end', {'game.log': [l for l in gen(seconds=0)] +
                                   ['[2026-11-26 10:01:00.000] [info] [gpu] [t4242] d3d12_async_submit: frame=1 submission=2 '
                                    'chunks=0 queued_max=0 full_waits=0 full_wait_us=0 drains_waited=0 drain_wait_us=0 worker_us=0'] * 2},
         1, must=['chunks > 0'])
    case('split failed = 1', {'game.log': mutate(good, is_split, sub_kv('failed', 1), which=ns // 2)}, 1,
         must=['failed = 0'])
    case('no held_query', {'game.log': gen(seconds=60, query_every=0)}, 1, must=['held_query > 0'])
    case('missing key in an async line', {'game.log': mutate(good, is_async, lambda l: l.replace(' worker_us=', ' worker='), 3)},
         1, must=['has the 9 keys'])
    case('missing key in a split line', {'game.log': mutate(good, is_split, lambda l: l.replace(' held_scratch=', ' hs='), 3)},
         1, must=['has the 7 keys'])
    case("'failed to create the submit thread'", {'game.log': gen(seconds=60, init=False) +
                                                  ['[2026-11-26 11:00:00.000] [error] [gpu] [t4242] d3d12_async_submit: '
                                                   'failed to create the submit thread, staying off']}, 1)
    case("'needs d3d12_submit_split_kb above 0'", {'game.log': ['[2026-11-26 10:00:00.000] [warning] [gpu] [t4242] '
                                                                'd3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off']}, 1)
    case('init line missing, no rotation', {'game.log': gen(seconds=60, init=False)}, 1, must=['async init line before'])
    rot = gen(seconds=120)
    cut = len(rot) // 2
    case('rotated, init in a dropped file', {'game.1.log': rot[cut - 10:cut], 'game.log': rot[cut:]}, 2,
         must=['INCOMPLETE', 'log rotated'])
    case('rotated, both files kept', {'game.1.log': rot[:cut], 'game.log': rot[cut:]}, 0)
    case('rotated files in the wrong order (game.log older)', {'game.1.log': rot[cut:], 'game.log': rot[:cut]}, 1)
    case('second SetupContext (two segments)', {'game.log': gen(seconds=60) + gen(seconds=60)}, 1, must=['one segment'])
    # X1: a split line whose frame went back relative to the async line before it
    case('merged frame order broken', {'game.log': mutate(good, is_split, sub_kv('frame', 0), which=ns - 1)}, 1,
         must=['frame and submission never decrease'])
    # X2: a split that did not go async (splits ran ahead of chunks)
    def bump_splits(ln):
        import re
        v = int(re.search(r'splits=(\d+)', ln).group(1))
        return re.sub(r'splits=\d+', 'splits=%d' % (v + 1000), ln)
    x2 = mutate(good, is_split, bump_splits, which=ns - 2)
    case('chunks/splits inconsistent', {'game.log': x2}, 1, must=['chunks/splits consistent'])
    first_async = next(i for i, l in enumerate(good) if is_async(l))
    one = [l for i, l in enumerate(good) if not is_async(l) or i == first_async]
    case('one async line only (min-lines 2)', {'game.log': one}, 2, must=['at least 2 async counter lines'])
    case('CRLF log', None, 0)

    os.makedirs(TMP, exist_ok=True)
    out, bad = [], 0
    for name, files, expect, args, must in cases:
        if name == 'good soak as a file path':
            p = os.path.join(write_run('fp', {'game.log': good}), 'game.log')
        elif name == 'CRLF log':
            d = os.path.join(TMP, 'crlf')
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, 'game.log'), 'w', encoding='utf-8', newline='\r\n') as fh:
                fh.write('\n'.join(good) + '\n')
            p = d
        elif files == {}:
            p = os.path.join(TMP, 'empty-dir')
            os.makedirs(p, exist_ok=True)
        else:
            p = write_run(name.replace(' ', '_').replace("'", '').replace('/', '_').replace('(', '').replace(')', '')
                          .replace('=', ''), files)
        rc, text = run(p, *args)
        # a 'must' text has to sit on a line tagged with the expected verdict (FAIL / INCOMPLETE); for PASS cases
        # it may sit anywhere (RESULT line, rule-5 report)
        tag = {1: 'FAIL', 2: 'INCOMPLETE'}.get(expect)
        tl = text.splitlines()
        ok = rc == expect and all(any(m in l and (tag is None or l.startswith(tag)) for l in tl) for m in (must or []))
        bad += not ok
        out.append('%s rc=%d expect=%d  %s' % ('ok  ' if ok else 'BAD ', rc, expect, name))
        if not ok or name == 'good soak':
            out.extend('      | ' + l for l in text.rstrip().splitlines())
    shutil.rmtree(TMP)
    out.append('')
    out.append('SELFTEST: %s (%d of %d cases as expected)' % ('PASS' if not bad else 'FAIL', len(cases) - bad, len(cases)))
    text = '\n'.join(out) + '\n'
    print(text, end='')
    with open(OUT, 'w', encoding='ascii', newline='\n') as fh:
        fh.write(text)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
