"""Agent 2 - S3d tool edits (native3d = S3 + Agent 4's live draw.cpp write, built at Agent 1's explicit GO), applied
by exact search/replace (each search text must occur exactly once). Run once:
  python build\\agent2\\patch-s3d-tools.py
stage-snap-bin.ps1:
  - S<N><suffix> tags (S3d) list the PATCHES rows of S1..S<N>, then their own. Before, any tag other than S<N> listed
    S1's rows, then its own, so S2's and S3's rows would have been missing from native3d's MANIFEST and freshness
    checks. S<N> tags, S0b/CHK-style tags and S1<suffix> are unchanged;
  - -CompareWhy TEXT says why the exe must differ from the -CompareBin one (default 'the generated code changed', build
    B's reason, so the B wording is unchanged); native3d vs native3 passes 'S3d changed rexlego/src/gpu_native/draw.cpp'.
Backs the file up to stage-snap-bin.ps1.pre-S3d first (refuses if that backup exists) and writes
S3d-diffs/stage-snap-bin.ps1.S3d.diff. Test: build/agent2/s3d-tools-test.ps1.
"""
import difflib
import hashlib
import os

A = os.path.dirname(os.path.abspath(__file__))
NAME = 'stage-snap-bin.ps1'

EDITS = [
    # header: document S<N><suffix> tags
    (r"""#                     newest STATE-S<N>-*.tsv written by snap-patch.py apply (+ PATCHES-S1.tsv ... PATCHES-S<N>.tsv)
""",
     r"""#                     newest STATE-S<N>-*.tsv written by snap-patch.py apply (+ PATCHES-S1.tsv ... PATCHES-S<N>.tsv);
#                     S<N><suffix> (S3d = S3 + one file) = the newest STATE-S3d-*.tsv (+ PATCHES-S1.tsv ...
#                     PATCHES-S<N>.tsv, then PATCHES-S3d.tsv); give it -BuildTag and -OutDir (the defaults would be
#                     snap-s3d and devoffS3d-bin / nativeS3d-bin)
"""),
    # header: native3d usage and -CompareWhy
    (r"""#   the MANIFEST text.
""",
     r"""#   the MANIFEST text.
# native3d (run-s3d.ps1): -SnapTag S3d -BuildTag snap3d -OutDir build\agent2\native3d-bin -CompareBin
#   build\agent2\native3-bin -CompareWhy 'S3d changed rexlego/src/gpu_native/draw.cpp' (-CompareWhy: why the exe must
#   differ from the -CompareBin one; default 'the generated code changed', build B's reason).
"""),
    # param block
    (r"""    [string]$WhatText = '', [string]$CodegenNote = '', [string]$ManifestNotesFile = '')
""",
     r"""    [string]$WhatText = '', [string]$CodegenNote = '', [string]$ManifestNotesFile = '',
    [string]$CompareWhy = 'the generated code changed')
"""),
    # the PATCHES files of a tag
    (r"""# patches applied to snap1 since S1: S<N> (N >= 2) lists the rows of every tag S1..S<N> (S3 = S1 + S2 + S3, so S2's
# rows stay in S3's MANIFEST and freshness checks); any other tag lists S1's rows, then its own
$patchTags = $(if ($SnapN -ge 2) { @(1..$SnapN | ForEach-Object { "S$_" }) } else { @('S1', $SnapTag) })
""",
     r"""# patches applied to snap1 since S1: S<N> (N >= 2) lists the rows of every tag S1..S<N> (S3 = S1 + S2 + S3, so S2's
# rows stay in S3's MANIFEST and freshness checks); S<N><suffix> lists S1..S<N>, then its own (S3d = S1 + S2 + S3 +
# S3d); any other tag lists S1's rows, then its own
$SnapBaseN = $(if ($SnapTag -match '^S(\d+)[A-Za-z]+$') { [int]$Matches[1] } else { 0 })
$patchTags = $(if ($SnapN -ge 2) { @(1..$SnapN | ForEach-Object { "S$_" }) } elseif ($SnapBaseN -ge 1) { @(1..$SnapBaseN | ForEach-Object { "S$_" }) + @($SnapTag) } else { @('S1', $SnapTag) })
"""),
    # -CompareBin comment
    (r"""# -CompareBin (build B vs A): the same snapshot and SDK, so everything but the exe and map must be identical
""",
     r"""# -CompareBin (build B vs A; native3d vs native3): the same SDK build, so everything but the exe and map must be
# identical; -CompareWhy says why the exe must differ
"""),
    # -CompareBin exe check
    (r"""{ Check (-not $same) "legodimensions.exe differs from the one in $cl (the generated code changed)" }""",
     r"""{ Check (-not $same) "legodimensions.exe differs from the one in $cl ($CompareWhy)" }"""),
]


def main():
    path = os.path.join(A, NAME)
    backup = path + '.pre-S3d'
    if os.path.exists(backup):
        raise SystemExit('%s exists: already patched? nothing written' % backup)
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    body = raw[3:] if bom else raw
    crlf = b'\r\n' in body
    if crlf and body.count(b'\r\n') != body.count(b'\n'):
        raise SystemExit('%s has mixed line endings; nothing written' % NAME)
    old = body.decode('utf-8').replace('\r\n', '\n')
    new = old
    for i, (s, r) in enumerate(EDITS):
        n = new.count(s)
        if n != 1:
            raise SystemExit('edit %d: search text found %d times in %s (want 1); nothing written' % (i, n, NAME))
        new = new.replace(s, r)
    out = new.replace('\n', '\r\n') if crlf else new
    out = (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')
    with open(backup, 'wb') as f:
        f.write(raw)
    if open(backup, 'rb').read() != raw:
        raise SystemExit('backup readback mismatch; %s left unchanged' % NAME)
    tmp = path + '.new'
    with open(tmp, 'wb') as f:
        f.write(out)
    os.replace(tmp, path)
    ddir = os.path.join(A, 'S3d-diffs')
    os.makedirs(ddir, exist_ok=True)
    diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), NAME + '.pre-S3d', NAME, n=2))
    dpath = os.path.join(ddir, NAME + '.S3d.diff')
    with open(dpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(diff)
    sha = lambda b: hashlib.sha256(b).hexdigest().upper()[:16]
    print('patched %s: %d edits | %s -> %s | backup %s | diff %s (%d B, sha256 %s) | %s, %s' % (
        NAME, len(EDITS), sha(raw), sha(open(path, 'rb').read()), os.path.basename(backup), dpath, os.path.getsize(dpath),
        sha(open(dpath, 'rb').read()), 'CRLF' if crlf else 'LF', 'BOM' if bom else 'no BOM'))


if __name__ == '__main__':
    main()
