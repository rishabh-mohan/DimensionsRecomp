#!/usr/bin/env python3
"""bincheck.py - Agent 3 (run-2 task 2): read-only check that a staged bin has what the S4b queue relies on.

Usage (repo root, at Below Normal):
    python -B build/agent3/s4b/bincheck.py build/agent2/devoff4b-bin [--set off|nat|ctr|cg26]
Prints the bin's files and sizes, the MANIFEST.txt lines that name a patch/switch, and for each needle (cvar names and
log-line literals) the files that contain it (ASCII or UTF-16LE). A missing literal can also mean the text is built at
run time, so a MISS is a lead to read, not a verdict by itself.
Exit 0 = every needle of the set was found; 1 = one or more missing; 2 = no bin dir, MANIFEST.txt or legodimensions.exe.
"""
import argparse
import os
import re
import sys

# cvars and log literals the W6 untimed runs and rows 7, 20, 23 use (devoff4b)
CORE = [
    'shared_memory_single_hold_rearm', 'physical_protect_hold_global_lock', 'physical_protect_keep_watch',
    'physical_protect_keep_watch_verify', 'slow_frame_log_ms', 'shared_memory_upload_hash_log',
    'shared_memory_upload_nontemporal_copy',
    'C1 keep-watch: on (with', 'first kept protect at', 'protects kept so far', 'C1 verify: on',
    'changed since its upload', 'memexport full-buffer',
]
# framerate_limit is not a needle: no bin has it as a literal (devoff4 neither), yet framerate_limit = 0 in the run's
# legodimensions.toml works (S4a udiag title run: perf.csv fps 374-424)
OFF_MORE = ['d3d12_submit_split_kb', 'd3d12_readback_memexport', 'd3d12_debug', 'LEGO_GPU_WAIT_STATS', 'LEGO_GPU_WAIT_BACKOFF_US']
NAT = ['native_settings_frontend', 'physical_protect_keep_watch', 'physical_protect_hold_global_lock', 'Native GPU [',
       'Native draw batches', 'Native write tracking']
CTR = ['deferred_counters', 'd3d12_submit_split_kb', 'slow_frame_log_ms', 'shared_memory_single_hold_rearm', 'memexport full-buffer']
CG26 = ['shared_memory_single_hold_rearm', 'slow_frame_log_ms']
SETS = {'off': CORE + OFF_MORE, 'nat': NAT, 'ctr': CTR, 'cg26': CG26}
ALL = list(dict.fromkeys(CORE + OFF_MORE + NAT + CTR + CG26))
BIN_EXT = ('.exe', '.dll')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('bin')
    ap.add_argument('--set', choices=sorted(SETS), default=None, help='needle set that decides the exit code (default from the dir name)')
    a = ap.parse_args()
    d = a.bin
    name = os.path.basename(os.path.normpath(d)).lower()
    st = a.set or ('nat' if name.startswith('native') else 'ctr' if 'ctr' in name else 'cg26' if 'cg26' in name else 'off')
    if not os.path.isdir(d):
        print(f'NO BIN DIR {d}'); return 2
    files = sorted(os.listdir(d))
    print(f'bin {d} (set {st}): {len(files)} files')
    for f in files:
        p = os.path.join(d, f)
        if os.path.isfile(p):
            print(f'  {f:32s} {os.path.getsize(p):>12,d}')
    for need in ('MANIFEST.txt', 'legodimensions.exe'):
        if need not in files:
            print(f'MISSING {need}'); return 2
    with open(os.path.join(d, 'MANIFEST.txt'), encoding='utf-8', errors='replace') as fh:
        man = fh.read().splitlines()
    print(f'MANIFEST.txt: {len(man)} lines; first line: {man[0][:200] if man else ""}')
    rx = re.compile(r'patch|s4b|S4b|switch|cvar|fingerprint|commit|HEAD|branch|flags|config', re.I)
    hits = [ln for ln in man[:400] if rx.search(ln)]
    for ln in hits[:45]:
        print(f'  | {ln[:220]}')
    if len(hits) > 45:
        print(f'  | ... {len(hits) - 45} more matching lines')
    blobs = {}
    for f in files:
        if f.lower().endswith(BIN_EXT):
            with open(os.path.join(d, f), 'rb') as fh:
                blobs[f] = fh.read()
    req = SETS[st]
    miss = []
    print('needles (* = in the exit-code set):')
    for n in ALL:
        a8, a16 = n.encode('ascii'), n.encode('utf-16-le')
        where = [f for f, b in blobs.items() if b.find(a8) >= 0 or b.find(a16) >= 0]
        star = '*' if n in req else ' '
        print(f' {star} {"ok  " if where else "MISS"} {n!r:44s} {", ".join(where)}')
        if n in req and not where:
            miss.append(n)
    print(f'RESULT: {"PASS" if not miss else "MISS " + str(len(miss)) + ": " + ", ".join(miss)} ({st} set, {len(req)} needles)')
    return 0 if not miss else 1


if __name__ == '__main__':
    sys.exit(main())
