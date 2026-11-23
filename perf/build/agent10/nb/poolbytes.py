#!/usr/bin/env python3
"""poolbytes: CPU pool copy byte sequences per run (Agent 10, task #17 1b tie-break).
Usage: poolbytes.py RUNDIR [RUNDIR ...]  -> count, total bytes, size histogram, first index where
each run's sequence departs from the first run's. Read-only; one thread."""
import collections
import os
import re
import sys

RX = re.compile(r'CPU pool copy dst=([0-9A-F]+) src=([0-9A-F]+) bytes=(\d+)')
seqs = []
for d in sys.argv[1:]:
    seq = []
    with open(os.path.join(d, 'game.log'), encoding='utf-8', errors='replace') as f:
        for line in f:
            m = RX.search(line)
            if m:
                seq.append((int(m.group(3)), m.group(1), m.group(2)))
    seqs.append((d, seq))
ref = seqs[0][1]
for d, seq in seqs:
    sizes = [s for s, _, _ in seq]
    hist = collections.Counter(sizes)
    first_diff = next((i for i, (a, b) in enumerate(zip(sizes, [s for s, _, _ in ref])) if a != b), None)
    same_addr = sum(1 for a, b in zip(seq, ref) if a[1:] == b[1:])
    print(f"{os.path.basename(d)}: n={len(seq)} total={sum(sizes)} hist={dict(sorted(hist.items()))} "
          f"first_size_diff_vs_ref={first_diff} same_dst_src_vs_ref={same_addr}/{min(len(seq), len(ref))}")
    print('   sizes: ' + ' '.join(str(s // 4096) for s in sizes))
