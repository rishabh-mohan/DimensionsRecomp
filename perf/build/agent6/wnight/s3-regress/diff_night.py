"""Task s3 (2026-11-25, E5.1 for M6): diff the re-run night kit outputs (s3-regress/) against the stored night outputs.
Read-only on the stored files. Writes build/agent6/wnight/s3-regress/DIFF.txt (also printed).
Per dir: run and arm verdict changes and reason changes from w6-data.json, then a unified diff of the summaries with
the runtime, the timing and the output path normalized. Exit 0 = every difference is one of the allowed kinds:
  A: a run's 'log does not end with the clean-exit lines' NOTE became the 'Execution complete' race INFO (and a logdiff
     GONE 'Execution complete' NOTE became INFO); its run/arm verdict may go NOTE -> PASS.
  B: the watchdog run 0128-off-r2 (W9 20261123-0108) gets the WATCHDOG NOTE, which replaces its levels and tail NOTEs.
Exit 1 = some other difference. Usage: python -B build/agent6/wnight/s3-regress/diff_night.py
"""
import difflib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = [  # (window, dir, stored summary, stored out dir)
    ('W6', '20261123-0009', 'build/agent6/w6/night-W6-0009.out.txt', 'build/agent6/w6/out-20261123-0009'),
    ('W6', '20261123-0313', 'build/agent6/w6/night-W6-0313.out.txt', 'build/agent6/w6/out-20261123-0313'),
    ('W9', '20261123-0108', 'build/agent6/wnight/night-W9-0108.out.txt', 'build/agent6/wnight/out-W9-20261123-0108'),
    ('W9', '20261123-0401', 'build/agent6/wnight/night-W9-0401.out.txt', 'build/agent6/wnight/out-W9-20261123-0401'),
    ('W5B', '20261123-0155', 'build/agent6/wnight/night-W5B-0155.out.txt', 'build/agent6/wnight/out-W5B-20261123-0155'),
    ('W5B', '20261123-0451', 'build/agent6/wnight/night-W5B-0451.out.txt', 'build/agent6/wnight/out-W5B-20261123-0451'),
    ('W4C', '20261123-0239', 'build/agent6/wnight/night-W4C-0239.out.txt', 'build/agent6/wnight/out-W4C-20261123-0239'),
]
WATCHDOG_RUN = ('20261123-0108', '0128-off-r2')
TAIL = 'log does not end with the clean-exit lines'
GONE_EC = 'logdiff GONE: [info] [core] Execution complete'


def load(p):
    with open(os.path.join(ROOT, p), encoding='utf-8-sig') as fh:
        return json.load(fh)


def lines(p):
    with open(os.path.join(ROOT, p), encoding='utf-8', errors='replace') as fh:
        out = []
        for x in fh.read().splitlines():
            x = re.sub(r'(exit \S+ in )[0-9.]+ s', r'\1# s', x)
            x = re.sub(r'runtime [0-9.]+ s', 'runtime # s', x)
            x = re.sub(r'build\\agent6\\(w6|wnight)\\(s3-regress\\)?out-', r'<out>\\out-', x)
            out.append(x)
        return out


def main():
    o, bad = [], 0
    w = o.append
    w('Night regression diff (task s3, 2026-11-25): stored night outputs vs re-run in build/agent6/wnight/s3-regress/')
    for win, d, stored_txt, stored_out in DIRS:
        new_out = 'build/agent6/wnight/s3-regress/out-%s-%s' % (win, d)
        new_txt = 'build/agent6/wnight/s3-regress/%s-%s.out.txt' % (win, d)
        S, N = load(stored_out + '/w6-data.json'), load(new_out + '/w6-data.json')
        w('')
        w('== %s %s' % (win, d))
        if sorted(S['runs']) != sorted(N['runs']):
            w('  BAD: run sets differ')
            bad += 1
        for rn in sorted(S['runs']):
            s, n = S['runs'][rn], N['runs'].get(rn) or {}
            gone_notes = [x for x in s['note'] if x not in n.get('note', [])]
            new_notes = [x for x in n.get('note', []) if x not in s['note']]
            new_info = n.get('info', [])
            if not (gone_notes or new_notes or new_info or s['verdict'] != n.get('verdict') or s['fail'] != n.get('fail')):
                continue
            kind = '?'
            if (d, rn) == WATCHDOG_RUN:
                ok = (len(new_notes) == 1 and new_notes[0].startswith('WATCHDOG: shutdown watchdog fired (3 s after WM_CLOSE)')
                      and all(x.startswith('levels W/E/C 41/0/0') or x.startswith(TAIL) for x in gone_notes)
                      and not new_info and s['verdict'] == n['verdict'] == 'NOTE')
                kind = 'B' if ok else 'BAD'
            else:
                ok = (not new_notes and len(gone_notes) == 1 and gone_notes[0].startswith(TAIL) and len(new_info) == 1
                      and new_info[0].startswith('no "Execution complete" line, benign hard-exit race')
                      and s['fail'] == n['fail'] and n['verdict'] in ('PASS', s['verdict']))
                kind = 'A' if ok else 'BAD'
            bad += kind == 'BAD'
            w('  run %-16s %s: verdict %s -> %s; NOTE removed %s; NOTE added %s; INFO added %s' % (
                rn, kind, s['verdict'], n.get('verdict'), [x[:70] for x in gone_notes], [x[:150] for x in new_notes],
                [x[:70] for x in new_info]))
        for arm in sorted(S['arms']):
            s, n = S['arms'][arm], N['arms'].get(arm) or {}
            if s['verdict'] != n.get('verdict') or s['fail'] != n.get('fail'):
                gone = [x for x in s['note'] if x not in n.get('note', [])]
                ok = (s['fail'] == n.get('fail') and n.get('verdict') == 'PASS' and s['verdict'] == 'NOTE' and not n.get('note')
                      and all(x.startswith(GONE_EC) or TAIL in x for x in gone))
                bad += not ok
                w('  arm %-8s %s: verdict %s -> %s (removed NOTEs: %s)' % (arm, 'A' if ok else 'BAD', s['verdict'],
                                                                         n.get('verdict'), [x[:60] for x in gone]))
            elif s['note'] != n.get('note'):
                w('  arm %-8s verdict %s unchanged, NOTEs changed: -%s +%s' % (
                    arm, s['verdict'], [x[:60] for x in s['note'] if x not in n['note']],
                    [x[:150] for x in n['note'] if x not in s['note']]))
        w('  watchdog_runs %s; race_runs %s' % (N.get('watchdog_runs'), N.get('race_runs')))
        diff = list(difflib.unified_diff(lines(stored_txt), lines(new_txt), stored_txt, new_txt, n=0, lineterm=''))
        w('  summary diff (runtime/timing/out path normalized): %d line(s)' % len(diff))
        for x in diff:
            w('    ' + x[:260])
    w('')
    w('RESULT: %s' % ('only the allowed A/B differences' if not bad else '%d unexpected difference(s)' % bad))
    txt = '\n'.join(o)
    with open(os.path.join(HERE, 'DIFF.txt'), 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    print(txt)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
