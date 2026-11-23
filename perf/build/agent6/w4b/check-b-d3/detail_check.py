#!/usr/bin/env python3
"""check-b-d3 detail (Agent 6 task #5, read-only checker): follow-ups on independent_check.py (imported; run with
python -B so no __pycache__ is written). Prints: the distinct values of the address/value-carrying lines over all
runs; the full Toypad trace of every run whose Write sequence does not start 'B0 C0'; which runs share each
deterministic Toypad payload set; the distinct orders of the non-Toypad lines (difflib vs the most common order) and
the line just before the first Toypad write; and the context of the IoDismountVolumeByFileHandle lines.
Writes detail_check.txt next to this script."""
import difflib
import os
import re
from collections import Counter, OrderedDict

import independent_check as ic

TID = re.compile(r'\] \[(t\d+)\] ')


def main():
    P = OrderedDict((n, ic.parse_run(n)) for g, names in ic.GROUPS.items() for n in names)
    out = []
    w = out.append

    w('== A. distinct values of address/value lines over all %d runs (value -> runs) ==' % len(P))
    for pat in ('Function table initialized', 'SetInterruptCallback', 'Skip cutscenes', 'IoDismountVolumeByFileHandle',
                'Stub XFileFsDeviceInformation', 'Guest memory arena mapped', 'XEX patch applied', 'audio endpoint',
                'DXGI adapter', 'SDL GameControllerDB', 'Toypad listener active', 'detected frame offset',
                'pad 0 mode', 'UI font loaded', 'Initializing shader storage'):
        vals = OrderedDict()
        for n, p in P.items():
            v = tuple(sorted(Counter(r['msg'] for r in p['recs'] if pat in r['msg']).items()))
            vals.setdefault(v, []).append(n)
        w('  %s: %d distinct' % (pat, len(vals)))
        for v, runs in vals.items():
            w('     %s <- %s' % ('; '.join('%dx %s' % (c, m) for m, c in v) or 'ABSENT',
                                 'all' if len(runs) == len(P) else ' '.join(runs)))

    w('')
    w('== B. Toypad traces of runs whose Write sequence does not start B0 C0 (s after first Toypad write) ==')
    for n, p in P.items():
        writes = [r for r in p['recs'] if r['tpdir'] == 'Write']
        if [r['tpbytes'][4] for r in writes[:2]] == ['B0', 'C0']:
            continue
        t0 = writes[0]['ts']
        w('  %s' % n)
        for r in p['recs']:
            if not (r['tpdir'] or 'Toypad' in r['msg']):
                continue
            b = r['tpbytes']
            if b and ((r['tpdir'] == 'Write' and b[4] in ('B1', 'B3')) or b[:4] == ['0B', '0C', '55', '09']):
                shown = '%s %s .. (challenge)' % (r['tpdir'], ' '.join(b[:6]))
            elif b:
                shown = '%s %s' % (r['tpdir'], ' '.join(b[:12]))
            else:
                shown = r['msg']
            m = TID.search(r['raw'])
            w('     %+8.3f %-7s %s' % ((r['ts'] - t0).total_seconds(), m.group(1) if m else '', shown))

    w('')
    w('== C. deterministic Toypad payload sets (B0/C0 writes + their reads, all bytes, in log order) ==')
    sets = OrderedDict()
    for n, p in P.items():
        sets.setdefault(tuple(ic.toypad(p)['det_payloads']), []).append(n)
    for i, (k, runs) in enumerate(sets.items()):
        w('  set %d (%d runs): %s' % (i, len(runs), ' '.join(runs)))
        for x in k:
            w('     %s' % x[:71])

    w('')
    w('== D. order of the non-Toypad lines (keys) per run ==')
    seqs = OrderedDict()
    for n, p in P.items():
        s = tuple(r['key'] for r in p['recs'] if not r['tpdir'] and 'Toypad' not in r['msg'])
        seqs.setdefault(s, []).append(n)
    ranked = sorted(seqs.items(), key=lambda kv: -len(kv[1]))
    ref = ranked[0][0]
    w('  %d distinct orders; most common (%d lines) <- %s' % (len(seqs), len(ref), ' '.join(ranked[0][1])))
    for s, runs in ranked[1:]:
        w('  variant <- %s' % ' '.join(runs))
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ref, s, autojunk=False).get_opcodes():
            if tag != 'equal':
                w('     %s ref[%d:%d] %s -> [%d:%d] %s' % (tag, i1, i2, [x[:70] for x in ref[i1:i2]][:3], j1, j2,
                                                       [x[:70] for x in s[j1:j2]][:3]))
    w('  line just before the first Toypad write, per run:')
    prev = OrderedDict()
    for n, p in P.items():
        idx = next(i for i, r in enumerate(p['recs']) if r['tpdir'] == 'Write')
        prev.setdefault(p['recs'][idx - 1]['key'][:90], []).append(n)
    for k, runs in prev.items():
        w('     %s <- %s' % (k, ' '.join(runs)))

    w('')
    w('== E. context of IoDismountVolumeByFileHandle (+-3 lines around the first one) ==')
    for n in ('1600-d3-r3', '1604-d0-r3', '1615-d3-r4'):
        recs = P[n]['recs']
        i = next(k for k, r in enumerate(recs) if 'IoDismountVolumeByFileHandle' in r['msg'])
        w('  %s' % n)
        for r in recs[max(0, i - 3):i + 6]:
            w('     %s' % r['raw'][:160])
    txt = '\n'.join(out)
    with open(os.path.join(ic.HERE, 'detail_check.txt'), 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
