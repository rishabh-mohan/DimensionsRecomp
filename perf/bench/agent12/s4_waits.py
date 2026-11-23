#!/usr/bin/env python3
"""S4 helper (Agent 12, task #21). Read-only, single-threaded.

Uses Agent 7's profile reader (bench/agent7/prof_main_compare.py) on one profiled run and writes:
  1. folded stacks (root first) of the WAIT/IO samples of the threads matching --thread-re,
  2. folded stacks of the BUSY samples of those threads (for cross-checking Agent 7's folds),
  3. for ALL threads: samples whose stack holds a mutex/SRW acquire or release frame, with the
     thread name and the 6 frames above the lock frame (who waits on / hands off which lock).
Weights: w = 1000 / (rounds * fps) ms per frame per sample, as in Agent 7's tools.
"""
import argparse
import collections
import os
import re
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent7'))
import prof_main_compare as pmc  # noqa: E402

LOCK_RE = re.compile(r'_Mtx_lock|_Mtx_unlock|AcquireSRWLock|ReleaseSRWLock|RtlpWaitOnAddress|'
                     r'NtWaitForAlertByThreadId|RtlpWakeSRWLock|EnterCriticalSection|'
                     r'LeaveCriticalSection')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('run_dir')
    p.add_argument('--label', default='x')
    p.add_argument('--thread-re', default=r'^GPU Commands')
    p.add_argument('-o', '--output', required=True)
    args = p.parse_args(argv)
    warns = []
    side = pmc.resolve_side(args.run_dir, args.label, None, None, warns)
    ap = pmc.load_ap()
    ns = types.SimpleNamespace(no_undname=False, keep_params=False, bin_dir=side['bin_dir'],
                               search=[], driverstore=False, extra_map=[],
                               trigger_latency=ap.TRIGGER_LATENCY_S)
    an = ap.Analysis(side['profile'], side['map'], ns, duration_s=side['duration_fallback'],
                     meta=None)
    funcs = an.funcs()
    names = an.prof.thread_names
    rounds = an.duration.get('rounds') or an.duration.get('rounds_estimated') or 0
    w = 1000.0 / (rounds * side['fps'])
    tre = re.compile(args.thread_re)
    sel = {t for t, nm in names.items() if tre.search(nm or '')}
    cache = {}

    def S(fid):
        s = cache.get(fid)
        if s is None:
            s = cache[fid] = pmc.short_name(funcs[fid].name)
        return s

    folded = {'wait': collections.Counter(), 'busy': collections.Counter()}
    locks = collections.Counter()
    for (t, fsid), n in an.agg.items():
        fs = an.fstacks[fsid]          # leaf first
        leaf = funcs[fs[0]]
        cls = leaf.cls
        names_leaf_first = [S(f) for f in fs]
        if t in sel:
            key = 'busy' if cls == 'busy' else 'wait'
            folded[key][';'.join(reversed(names_leaf_first))] += n
        for i, nm in enumerate(names_leaf_first):
            if LOCK_RE.search(nm):
                # first lock frame from the root side = the outermost lock call
                j = max(k for k, x in enumerate(names_leaf_first) if LOCK_RE.search(x))
                above = names_leaf_first[j + 1:j + 7]
                locks[(names.get(t, str(t)), cls, names_leaf_first[j],
                       ' < '.join(above))] += n
                break
    with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# s4_waits: {side["run_dir"]}\n# fps {side["fps"]:.2f} rounds {rounds} '
                f'w {w:.6f} ms/f per sample; threads /{args.thread_re}/ -> '
                f'{sorted((t, names.get(t)) for t in sel)}\n')
        for key in ('wait', 'busy'):
            tot = sum(folded[key].values())
            f.write(f'\n## {key} samples of the selected threads: {tot} ({tot * w:.3f} ms/f)\n')
            for st, n in folded[key].most_common():
                f.write(f'{st} {n}\n')
        f.write('\n## all threads: samples with a lock frame (thread | class | outermost lock '
                'frame | callers above it, nearest first) count ms/f\n')
        for (tn, cls, lk, above), n in locks.most_common():
            f.write(f'{tn} | {cls} | {lk} | {above} {n} {n * w:.3f}\n')
        for wmsg in warns:
            f.write(f'# warning: {wmsg}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
