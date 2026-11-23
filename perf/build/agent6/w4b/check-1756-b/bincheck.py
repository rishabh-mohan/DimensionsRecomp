#!/usr/bin/env python3
"""Checker B, task #13, B2 binary cross-check: which log/cvar strings are in the S3d binaries (build/agent2/devoff3-bin)
and the S4a binaries (build/agent2/devoff4-bin), and the full set difference of printable ASCII strings (>= 8 chars)
between the two builds, per file (rexruntime.dll, rexgpu-xenos.dll, legodimensions.exe). Read-only; stdlib only.
Output: bincheck-out.txt next to this file."""
import sys
sys.dont_write_bytecode = True
import hashlib
import os
import re
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
B3 = os.path.join(ROOT, 'build', 'agent2', 'devoff3-bin')
B4 = os.path.join(ROOT, 'build', 'agent2', 'devoff4-bin')
OUT = os.path.join(HERE, 'bincheck-out.txt')
FILES = ['rexruntime.dll', 'rexgpu-xenos.dll', 'legodimensions.exe']
KEYS = [b'Host timer resolution set to', b'Could not set the host timer resolution',
        b'Timer resolution power throttling opt-out failed', b'TimerQueue: precise wait', b'REX_TIMER_WAIT_BLOCKING',
        b'timer_queue_precise_wait', b'host_timer_resolution_ms', b'host_timer_throttling_optout', b'S4 upload hash',
        b'shared_memory_upload_hash_log', b'shared_memory_single_hold_rearm', b'physical_protect_hold_global_lock',
        b'physical_protect_keep_watch', b'C1 keep-watch', b'Reserving the guest memory arena',
        b'LEGO_NATIVE_SHADER_MISS_CACHE', b'shader_miss_cache_insert', b'missing from AOT index',
        b'IoDismountVolumeByFileHandle']
PAT = re.compile(rb'[\x20-\x7e]{8,}')
LIMIT = 250
O = []


def w(s=''):
    O.append(s)


def main():
    for fn in FILES:
        p3, p4 = os.path.join(B3, fn), os.path.join(B4, fn)
        with open(p3, 'rb') as fh:
            d3 = fh.read()
        with open(p4, 'rb') as fh:
            d4 = fh.read()
        w('== %s: S3d %d B sha256 %s | S4a %d B sha256 %s' % (fn, len(d3), hashlib.sha256(d3).hexdigest()[:16], len(d4),
                                                            hashlib.sha256(d4).hexdigest()[:16]))
        for k in KEYS:
            w('  %-52s S3d %3d  S4a %3d' % (k.decode(), d3.count(k), d4.count(k)))
        s3 = set(PAT.findall(d3))
        s4 = set(PAT.findall(d4))
        del d3, d4
        new = sorted(s4 - s3, key=lambda s: (-len(s), s))
        gone = sorted(s3 - s4, key=lambda s: (-len(s), s))
        w('  printable strings >= 8 chars: S3d %d, S4a %d; only in S4a %d; only in S3d %d (listed longest first, '
          'up to %d each)' % (len(s3), len(s4), len(new), len(gone), LIMIT))
        for s in new[:LIMIT]:
            w('    + %s' % s.decode('ascii')[:220])
        for s in gone[:LIMIT]:
            w('    - %s' % s.decode('ascii')[:220])
        w()


if __name__ == '__main__':
    rc = 0
    try:
        main()
    except Exception:
        w('!!! EXCEPTION')
        w(traceback.format_exc())
        rc = 1
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(O) + '\n')
    print('bincheck rc %d, %d lines -> %s' % (rc, len(O), OUT))
    sys.exit(rc)
