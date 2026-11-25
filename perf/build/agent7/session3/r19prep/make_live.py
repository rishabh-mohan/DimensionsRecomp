#!/usr/bin/env python3
"""make_live.py - builds r19prep/queue-r19-live.jsonl from ../queue-r19.jsonl (A17F398B, rated by M10) (M7, r19prep).

Changes (and nothing else): comment lines dropped (M3's live files are pure JSON lines); rows i, c, g, f get the path
marker r19-pathN + "unless" r19-path16; new rows i16 (after i) and g16 (after g) per M10 C2 with r19-path16 + "unless"
r19-pathN; notes say N=4 (ready-N 03:09) and point to LAUNCH-R19.md. Args, needs order and est of the old rows are
unchanged. Run: python -B build/agent7/session3/r19prep/make_live.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'queue-r19.jsonl')
DST = os.path.join(HERE, 'queue-r19-live.jsonl')
G = 'build\\agent3\\session3\\'
PN, P16 = G + 'r19-pathN', G + 'r19-path16'
L = ' Gate: r19prep\\LAUNCH-R19.md.'

NOTES = {
    'r19r11': '#19 ref for rows j and i16 = S4b row 11 (never ran). s4b_check --row s4b11 --base s4b01 --allow-new '
              "'d3d12_submit_split'; r19_gate --row i --n 16 --bin devoff4b-bin: split init 'at 16 KB' x1, failed=0, "
              'splits > 0.' + L,
    'r19r10': '#19 ref for rows i and c = S4b row 10 at N=4 (never ran). PATH DECISION ROW: r19_gate --row i --n 4 '
              'exit 0 -> M3 writes r19-pathN; INCOMPLETE with only the splits>0 entry -> r19-path16 (M10 C2); else '
              'neither (stop).' + L,
    'r19r13': '#19 ref for row f = S4b row 13 at N=4 (never ran). s4b_check --row s4b13 --base s4b01 --allow-new '
              "'d3d12_submit_split'." + L,
    'r19r15': '#19 ref for rows g and g16 = S4b row 15 at N=4 (never ran). s4b_check --row s4b15 (DRED line x>=1, no '
              "debug-layer enable failure); base s4b01 --allow-new 'd3d12_submit_split'." + L,
    'r19r25': '#19 ref for row d = S4b row 25 at N=4 (never ran). s4b_check --row s4b25 --base '
              '20261125-014239-s4b-N16-title-split16. s4bN4 split on the title (101351 splits), so splits are '
              'expected.' + L,
    'r19a': '#19 row a, FIRST run on the #19 bin: OFF identity vs s4b01; r19_gate --row a --bin '
            'build\\agent2\\devoff4b-r19-bin (rexgpu 5DCDD8CB). FAIL -> stop, no r19-ok-a.' + L,
    'r19b': "#19 row b: async on, split 0 -> exactly 1 [warning] 'staying off'. r19_gate --row b --bin "
            'devoff4b-r19-bin.' + L,
    'r19i': '#19 row i (path N): split 4, OFF, vs r19r10; r19_gate --row i --n 4 --bin devoff4b-r19-bin. Last OFF row: '
            'go-r19on only after r19-ok-i.' + L,
    'r19i16': '#19 row i16 (path 16, M10 C2: replaces i when r19r10 shows no split at N): split 16, OFF, vs r19r11; '
              'r19_gate --row i --n 16 --bin devoff4b-r19-bin. PASS -> M3 writes r19-ok-i (slot i, text "i16").' + L,
    'r19c': '#19 row c (path N), first ON row, vs r19r10; r19_gate --row c --n 4 --bin devoff4b-r19-bin. Path 16: '
            'dropped, M3 writes r19-ok-c "held no-op (C2)". Hang = FAIL.' + L,
    'r19g': '#19 row g (path N), debug layer, vs r19r15; s4b_check --row s4b15; r19_gate --row g --n 4 --bin '
            'devoff4b-r19-bin. Hang = FAIL.' + L,
    'r19g16': '#19 row g16 (path 16, M10 C2): debug + split 16 + async vs r19r15 (--allow-new '
              "'d3d12_(async_submit|submit_split)'); s4b_check --row s4b15; r19_gate --row j --n 16 --j1-info --bin "
              'devoff4b-r19-bin. PASS -> M3 writes r19-ok-g (slot g, text "g16"). Hang = FAIL.' + L,
    'r19j': '#19 row j stress (split 16 + async) vs r19r11: r19_gate --row j --n 16 --bin devoff4b-r19-bin; '
            'full_waits = 0 -> INCOMPLETE (stop, Overseer decides). First real-split proof needed by W7.' + L,
    'r19d': '#19 row d = W7 s19 arm, functional only, vs r19r25: r19_gate --row d --n 4 --bin devoff4b-r19-bin. A '
            'no-op marker only under M10 C1 (exact rule in LAUNCH-R19.md). Hang = FAIL.' + L,
    'r19f': '#19 row f (path N): memexport readback drain vs r19r13; r19_gate --row f --n 4 --bin devoff4b-r19-bin. '
            'Path 16: dropped, M3 writes r19-ok-f "held no-op (C2)"; then no ON use may set '
            'd3d12_readback_memexport. Hang = FAIL.' + L,
    'r19e': '#19 row e = 10-min level soak vs s4bL0 (--allow-new d3d12_(async_submit|submit_split)): r19_gate --row e '
            '--n 4 --bin devoff4b-r19-bin. INCOMPLETE ends the chain (C3); W7 needs j + e PASS with real splits.' + L,
}


def main():
    rows = []
    with open(SRC, 'r', encoding='utf-8') as fh:
        for line in fh:
            s = line.strip()
            if s and not s.startswith('#'):
                rows.append(json.loads(s))
    out = []
    for r in rows:
        rid = r['id']
        r = dict(r)
        if rid in ('r19i', 'r19c', 'r19g', 'r19f'):
            r['needs'] = r['needs'] + [PN]
            r = with_unless(r, P16)
        r['note'] = NOTES[rid]
        out.append(r)
        if rid == 'r19i':
            out.append(sub16(r, 'r19i16', 'r19i16-split16', 'd3d12_submit_split_kb=16'))
        if rid == 'r19g':
            out.append(sub16(r, 'r19g16', 'r19g16-dbg-async-16',
                             'd3d12_debug=true;d3d12_submit_split_kb=16;d3d12_async_submit=true'))
    with open(DST, 'w', encoding='utf-8', newline='\n') as fh:
        for r in out:
            fh.write(json.dumps(r) + '\n')
    print('wrote %s (%d rows)' % (DST, len(out)))


def with_unless(r, path):
    # key order id, est, [toypad], needs, unless, args, note
    o = {}
    for k, v in r.items():
        o[k] = v
        if k == 'needs':
            o['unless'] = path
    return o


def sub16(r, rid, tag, cvar):
    needs = [x for x in r['needs'] if x not in ('build\\agent3\\s4b\\ready-N', PN)] + [P16]
    args = list(r['args'])
    args[args.index('-Tag') + 1] = tag
    args[args.index('-Cvar') + 1] = cvar
    o = {'id': rid, 'est': r['est'], 'needs': needs, 'unless': PN, 'args': args, 'note': NOTES[rid]}
    return o


if __name__ == '__main__':
    main()
