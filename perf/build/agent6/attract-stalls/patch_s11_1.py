#!/usr/bin/env python3
"""Add section 11.1 (S11 arm A/B results) to perf-notes/agent6-attract-stalls.md.

One-shot and guarded: refuses to run twice, checks every target occurs exactly
once, keeps UTF-8 / LF / no BOM, and backs up the note first.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOTE = HERE.parents[2] / 'perf-notes' / 'agent6-attract-stalls.md'
BAK = HERE / 'agent6-attract-stalls.md.bak-0620'
ADD = HERE / 's11_1.md'

raw = NOTE.read_bytes()
t = raw.decode('utf-8')
if '### 11.1 ' in t:
    sys.exit('already patched')
if b'\r\n' in raw or raw.startswith(b'\xef\xbb\xbf') or not t.endswith('\n'):
    sys.exit('unexpected encoding or line endings')
if not BAK.exists():
    shutil.copyfile(NOTE, BAK)

reps = [
    ("added ~05:05 at Agent 1's request.**",
     "added ~05:05 at Agent 1's request; §11.1 (results of both §11 arms: skip §10.1) added ~06:25.**"),
    ("(§11 arm B decides)",
     "(it isn't: §11.1 measured a translate share of 0.01-0.03, so skip (a))"),
    ("- (a) only if §11 arm B shows translation is ≥ ~40% of the 67-miss burst.",
     "- (a) only if §11 arm B shows translation is ≥ ~40% of the 67-miss burst. "
     "§11.1: it showed 1-3% on the bursts it reached, so skip (a)."),
]
for old, new in reps:
    n = t.count(old)
    if n != 1:
        sys.exit(f'target found {n}x: {old[:60]!r}')
    t = t.replace(old, new)

add_raw = ADD.read_bytes()
if b'\r\n' in add_raw or add_raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('s11_1.md has CRLF or a BOM')
add = add_raw.decode('utf-8')
if not add.endswith('\n'):
    add += '\n'
t = t + '\n' + add
NOTE.write_bytes(t.encode('utf-8'))
print(f'patched: {len(raw)} -> {len(t.encode("utf-8"))} B, backup {BAK.name}')
