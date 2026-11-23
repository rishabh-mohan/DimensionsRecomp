"""Agent 2 - make the S3e tool clones (prepared, NOT run). S3e = snap1 at S3d + exactly Agent 4's next live write of
rexlego/src/gpu_native/draw.cpp (the '|| !vs' variant) -> native3e-bin, native only, compared with native3d-bin. Only at
Agent 1's explicit GO with the new draw.cpp sha256, and only before 08:30.
  python build\\agent2\\make-s3e-clones.py [--force]
Generates prep-s3e.py and run-s3e.ps1 from prep-s3d.py and run-s3d.ps1 by placeholder token swaps (S3d -> S3e, the
S3 base -> S3d, native3d -> native3e, native3 -> native3d) plus exact replacements, each with an expected count (any
mismatch and nothing is written). Adds run-s3e.ps1 to stop-snap.ps1's driver list (backup stop-snap.ps1.pre-S3e).
Writes unified diffs to build/agent2/S3e-diffs/. Refuses to overwrite anything without --force.
stage-snap-bin.ps1 is NOT changed: for a suffixed tag it lists the PATCHES rows of S1..S<N> and then its own tag, so
native3e's MANIFEST lists S1, S2, S3 and S3e. S3d's one row (draw.cpp) is superseded by S3e's anyway (the last row per
file wins in its checks); the S3e notes file says so.
"""
import difflib
import hashlib
import os
import re
import shutil
import sys

A = r'<workspace>\build\agent2'
FORCE = '--force' in sys.argv[1:]
DIFFS = os.path.join(A, 'S3e-diffs')


def load(name):
    with open(os.path.join(A, name), 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw[3:].decode('utf-8') if bom else raw.decode('utf-8')
    crlf = '\r\n' in text
    return text.replace('\r\n', '\n'), bom, crlf, raw


def dump(text, bom, crlf):
    if crlf:
        text = text.replace('\n', '\r\n')
    b = text.encode('utf-8')
    return (b'\xef\xbb\xbf' + b) if bom else b


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16].upper()


def swap(t):
    t = t.replace('native3d', '@N3E@')
    t = t.replace('native3-bin', 'native3d-bin').replace("native3's", "native3d's")
    t = t.replace('@N3E@', 'native3e')
    t = t.replace('S3d', '@S3E@').replace('s3d', 's3e').replace('snap3d', 'snap3e')
    t = re.sub(r'S3(?![0-9A-Za-z@])', 'S3d', t)
    return t.replace('@S3E@', 'S3e')


def rep(t, old, new, n, what, errs):
    c = t.count(old)
    if c != n:
        errs.append('%s: expected %d match(es), found %d' % (what, n, c))
        return t
    return t.replace(old, new)


errs = []

# prep-s3e.py
p_src, p_bom, p_crlf, p_raw = load('prep-s3d.py')
p_sw = swap(p_src)
p = p_sw
p = rep(p, '"""Agent 2 - S3e inputs, at Agent 1\'s explicit GO (after Agent 4\'s live draw.cpp write).',
        '"""Agent 2 - S3e inputs, at Agent 1\'s explicit GO (after Agent 4\'s next live draw.cpp write, the \'|| !vs\'\n'
        'variant; cloned from prep-s3d.py by make-s3e-clones.py).', 1, 'prep docstring line 1', errs)
p = rep(p, '(3 lines, for', '(4 lines, for', 1, 'prep docstring notes count', errs)
p = rep(p, '"S3e build inputs: S3d (%s: game commit 001336f',
        '"S3e build inputs: S3d (%s: S3 = game commit 001336f', 1, 'prep notes line 1a', errs)
p = rep(p, '"edits) + exactly Agent 4\'s live write of %s, %s -> %s (%d B, live mtime %s); Agent 1\'s GO %s."',
        '"edits, plus Agent 4\'s S3d draw.cpp write in PATCHES-S3d.tsv) + exactly Agent 4\'s next live write of %s "\n'
        '        "(the \'|| !vs\' variant), %s -> %s (%d B, live mtime %s); Agent 1\'s GO %s."', 1, 'prep notes line 1b', errs)
p = rep(p, "only build B uses '", "only builds B and nativeB use '", 1, 'prep notes line 3', errs)
p = rep(p, "        'install/batch-nolr.',\n    ]",
        "        'install/batch-nolr.',\n"
        "        \"Patch rows: stage-snap-bin.ps1 lists those of S1, S2, S3 and S3e; S3d's one row (draw.cpp) is superseded \"\n"
        "        \"by S3e's, whose before-hash is S3d's after-hash.\",\n    ]", 1, 'prep notes line 4', errs)

# run-s3e.ps1
r_src, r_bom, r_crlf, r_raw = load('run-s3d.ps1')
r_sw = swap(r_src)
r = r_sw
r = rep(r, "# Agent 4's live write of rexlego/src/gpu_native/draw.cpp: prep-s3e.py",
        "# Agent 4's next live write (the '|| !vs' variant) of rexlego/src/gpu_native/draw.cpp: prep-s3e.py", 1,
        'run header line 2', errs)
r = rep(r, '# build/agent2/stop-snap.ps1 kills it.\n',
        '# build/agent2/stop-snap.ps1 kills it. Cloned from run-s3d.ps1 by make-s3e-clones.py; -CompareBin is native3d-bin.\n',
        1, 'run header clone line', errs)
r = rep(r, "foreach ($t in 'S1', 'S2', 'S3d', 'S3e')", "foreach ($t in 'S1', 'S2', 'S3', 'S3e')", 1, 'run patch-row tags',
        errs)
r = rep(r, r"'run-b\.ps1|b-chain\.ps1|prep-b\.py|run-s2\.ps1|run-s3\.ps1|build-snap\.ps1|stage-snap-bin\.ps1'",
        r"'run-b\.ps1|b-chain\.ps1|prep-b\.py|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|build-snap\.ps1|stage-snap-bin\.ps1|"
        r"rb-chain\.ps1|run-rb\d\.ps1|prep-rb\d\.py|run-nb\.ps1|prep-nb\.py'", 1, 'run driver guard', errs)
r = rep(r, "'native build 3d (S3d + the Agent 4 draw.cpp write): NATIVE_GPU=ON with Agent 6 AOT inputs'",
        "'native build 3e (S3d + the second Agent 4 draw.cpp write): NATIVE_GPU=ON with Agent 6 AOT inputs'", 1,
        'run WhatText', errs)

# stop-snap.ps1
s_src, s_bom, s_crlf, s_raw = load('stop-snap.ps1')
s = rep(s_src, r'run-s3d\.ps1|', r'run-s3d\.ps1|run-s3e\.ps1|', 1, 'stop-snap drivers', errs)
s = rep(s, "\n$drivers = '", "\n# 04:5x: run-s3e.ps1, the native3e driver (S3e = S3d + Agent 4's next draw.cpp write; Agent 1's GO only).\n"
        "$drivers = '", 1, 'stop-snap comment', errs)

# leftovers that the swap should have caught (checked on the swap output, before the exact replacements, which add
# intentional mentions of prep-s3d.py / run-s3d.ps1); every s3d / snap3d / native3-bin line of the result is listed
for name, sw, t in (('prep-s3e.py', p_sw, p), ('run-s3e.ps1', r_sw, r)):
    left = sorted(set(re.findall(r'native3d-bin|native3e-bin|native3-bin|S3d|S3e|snap3d|snap3e|s3d', t)))
    print('%s tokens after the swap + replacements: %s' % (name, ', '.join(left)))
    if 'snap3d' in sw or 's3d' in sw or 'native3-bin' in sw:
        errs.append('%s: the swap output still has snap3d / s3d / native3-bin' % name)
    for i, line in enumerate(t.split('\n'), 1):
        if 's3d' in line or 'snap3d' in line or 'native3-bin' in line:
            print('  %s:%d keeps: %s' % (name, i, line.strip()[:150]))

if errs:
    print('REFUSED (nothing written):')
    for e in errs:
        print('  ' + e)
    sys.exit(1)

outs = {'prep-s3e.py': dump(p, p_bom, p_crlf), 'run-s3e.ps1': dump(r, r_bom, r_crlf)}
bk = os.path.join(A, 'stop-snap.ps1.pre-S3e')
if not FORCE:
    for n in list(outs) + ['stop-snap.ps1.pre-S3e']:
        if os.path.exists(os.path.join(A, n)):
            print('REFUSED: %s exists (use --force); nothing written' % n)
            sys.exit(1)
os.makedirs(DIFFS, exist_ok=True)
for n, b in outs.items():
    with open(os.path.join(A, n), 'wb') as f:
        f.write(b)
if not os.path.exists(bk):
    shutil.copy2(os.path.join(A, 'stop-snap.ps1'), bk)
with open(os.path.join(A, 'stop-snap.ps1'), 'wb') as f:
    f.write(dump(s, s_bom, s_crlf))


def udiff(a_text, b_text, a_name, b_name, out):
    d = ''.join(difflib.unified_diff(a_text.splitlines(True), b_text.splitlines(True), a_name, b_name, n=1))
    with open(os.path.join(DIFFS, out), 'w', encoding='utf-8', newline='\n') as f:
        f.write(d)
    adds = sum(1 for l in d.splitlines() if l.startswith('+') and not l.startswith('+++'))
    dels = sum(1 for l in d.splitlines() if l.startswith('-') and not l.startswith('---'))
    return '%s +%d/-%d sha %s' % (out, adds, dels, sha16(d.encode('utf-8')))


print(udiff(p_src, p, 'prep-s3d.py', 'prep-s3e.py', 'prep-s3e.py.vs-s3d.diff'))
print(udiff(r_src, r, 'run-s3d.ps1', 'run-s3e.ps1', 'run-s3e.ps1.vs-s3d.diff'))
print(udiff(s_src, s, 'stop-snap.ps1.pre-S3e', 'stop-snap.ps1', 'stop-snap.ps1.S3e.diff'))
for n in ('prep-s3e.py', 'run-s3e.ps1', 'stop-snap.ps1', 'stop-snap.ps1.pre-S3e'):
    with open(os.path.join(A, n), 'rb') as f:
        print('%s sha256 %s' % (n, sha16(f.read())))
print('sources: prep-s3d.py %s, run-s3d.ps1 %s (unchanged)' % (sha16(p_raw), sha16(r_raw)))
