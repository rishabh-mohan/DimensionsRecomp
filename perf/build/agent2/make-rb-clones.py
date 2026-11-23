"""Agent 2 - task #14: make the S3-base clones of the build-B tools (run once; refuses to overwrite).
  python build\\agent2\\make-rb-clones.py
Agent 1, 03:11: the base of the B rollback and of nativeB is snap1's current tree (S3, or S3d once applied) in the new
copy build/agent2/snapB3 (snapB and snapB-off stay untouched); the rollback is compared with devoff3-bin, nativeB with
native3d-bin (native3-bin if S3d is not applied when the copy is made). Nothing here copies or builds anything.
  build/agent9/repin/rb1-nolocal/{prep-b.py,run-b.ps1}    -> build/agent2/prep-rb1.py, run-rb1.ps1
  build/agent9/repin/rb2-nomusttail/{prep-b.py,run-b.ps1} -> build/agent2/prep-rb2.py, run-rb2.ps1
  build/agent2/prep-b.py (batch-nolr)                     -> build/agent2/prep-nb.py (run-nb.ps1 is written by hand)
Every source must have its pinned sha256 prefix (Agent 9's repin README; prep-b.py C0067F18). 'snapB' is renamed
'snapB3' everywhere, then each listed edit must match exactly once, and the pinned lines (VARIANT, SUMS_SHA, CFG_SHA,
TOOL_SHA, the entry count, $nolr, the two pins, the -Install default) must survive unchanged (apart from that rename).
Unified diffs (source -> clone) go to build/agent2/RB-diffs, plus run-nb.ps1 against run-b.ps1 for reference.
Also patches stop-snap.ps1 (backup stop-snap.ps1.pre-RB): the task #14 drivers join $drivers.
"""
import difflib, hashlib, os, sys

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
REPIN = os.path.join(R, 'build', 'agent9', 'repin')
DIFFS = os.path.join(A, 'RB-diffs')


def sha16(b):
    return hashlib.sha256(b).hexdigest().upper()[:16]


def load(p, want):
    b = open(p, 'rb').read()
    if want and not sha16(b).startswith(want):
        sys.exit('STOP: %s is %s, expected %s' % (p, sha16(b), want))
    t = b.decode('utf-8')
    bom = t.startswith('\ufeff')
    if bom:
        t = t[1:]
    crlf = '\r\n' in t
    return t.replace('\r\n', '\n'), bom, crlf


def dump(t, bom, crlf):
    if crlf:
        t = t.replace('\n', '\r\n')
    return (('\ufeff' if bom else '') + t).encode('utf-8')


def fill(s, m):
    for k, v in m.items():
        s = s.replace('@%s@' % k, v)
    return s


def clone(name, src, edits, pins):
    n = src.count('snapB')
    t = src.replace('snapB', 'snapB3')
    for i, (tgt, rep) in enumerate(edits, 1):
        c = t.count(tgt)
        if c != 1:
            sys.exit('STOP: %s edit %d matches %d times (want 1): %r' % (name, i, c, tgt[:100]))
        t = t.replace(tgt, rep)
    lines = set(t.split('\n'))
    kept = 0
    for pre in pins:
        hits = [l for l in src.split('\n') if l.lstrip().startswith(pre)]
        if not hits:
            sys.exit('STOP: %s: no source line starts with %r' % (name, pre))
        for l in hits:
            if l.replace('snapB', 'snapB3') not in lines:
                sys.exit('STOP: %s: pinned line changed: %r' % (name, l[:100]))
            kept += 1
    print('%s: snapB -> snapB3 x%d, %d edits, %d pinned lines unchanged' % (name, n, len(edits), kept))
    return t


def udiff(a_name, b_name, a, b):
    return ''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), a_name, b_name, n=2))


# ---------------------------------------------------------------- prep edits (targets are after the snapB3 rename)
HEAD_T = r'''"""Agent 2 - prepare Agent 9's codegen build B (perf-notes/agent9-codegen.md, 'Session 2: regen+build recipe', steps
3-5) in a separate source tree, so snap1 (S2, the base for S3) and its build trees stay untouched and A =
build/agent2/devoff2-bin stays the exact reference (Agent 1, 23:40: base snapB3 on S2). Copies and hashing only.
  python build\\agent2\\prep-b.py [--resync] [--skip-copy] [--install DIR]
'''
HEAD_RB = r'''"""Agent 2 - rollback build @VU@ on an S3 base, at Agent 1's GO only (task #14): a clone of
build/agent9/repin/@TREE@/prep-b.py (Agent 9's re-pin of build/agent2/prep-b.py for recipe step @STEP@), made by
build/agent2/make-rb-clones.py (diffs: build/agent2/RB-diffs). Agent 1, 03:11: the base is snap1's current tree (S3,
or S3d once applied; snap1-sdk/install is the S3 SDK and no S2 SDK install was kept) in the new copy
build/agent2/snapB3; snapB and snapB-off stay untouched; A = build/agent2/devoff3-bin. Changed from the re-pin: the
copy dir and the log and notes names (snapB -> snapB3), the snapshot tag (the newest PATCHES file, S3 or S3d, with its
STATE file; the PATCHES pattern now takes S3d, whose row then counts), --check-only, and the notes text. Step 1's text
below still names batch-nolr's pins; the code checks @TREE@'s (VARIANT, SUMS_SHA, CFG_SHA, @ENT@ entries).
Copies and hashing only.
  python build\\agent2\\prep-@V@.py [--resync] [--skip-copy] [--check-only] [--install DIR]
  --check-only: step 1 (the install tree, read only) and the snapshot tag, then stop before the copy.
'''
HEAD_NB = r'''"""Agent 2 - nativeB, at Agent 1's GO only (task #14; decided ~04:15, only if the B gate passes): prepare a native
build of Agent 9's batch-nolr codegen on an S3 base, for the native-hook checks Agent 10 left open. A clone of
build/agent2/prep-b.py made by build/agent2/make-rb-clones.py (diff: build/agent2/RB-diffs/prep-nb.py.diff);
run-nb.ps1 builds and stages it. Agent 1, 03:11: the base is snap1's current tree (S3, or S3d once applied;
snap1-sdk/install is the S3 SDK) in the new copy build/agent2/snapB3; snapB and snapB-off stay untouched; A =
build/agent2/native3d-bin when copied at S3d, native3-bin at S3. Changed from prep-b.py: the copy dir and the log and
notes names (snapB -> snapB3), rexlego/out is copied (Agent 6's native banks, which the native flags read), the
snapshot tag (the newest PATCHES file, S3 or S3d, with its STATE file; the PATCHES pattern now takes S3d, whose row
then counts), --check-only, and the notes text. Copies and hashing only.
  python build\\agent2\\prep-nb.py [--resync] [--skip-copy] [--check-only] [--install DIR]
  --check-only: step 1 (the install tree, read only) and the snapshot tag, then stop before the copy.
'''
DOC2_T = r'''2. Copy build/agent2/snap1/DimensionsRecomp -> build/agent2/snapB3/DimensionsRecomp with robocopy (/E, mtimes kept;
   --resync: /MIR after a new S-batch on snap1), except rexglue-sdk/out (snap1-sdk's output dir), rexlego/out
   (Agent 6's native banks; the OFF build never reads them: snap1-off/build.ninja names none), rexlego/generated and
   rexlego/legodimensions_config.toml (step 3 writes those). Then every copied file must match snap1 in size and mtime,
'''
DOC2_NB = r'''2. Copy build/agent2/snap1/DimensionsRecomp -> build/agent2/snapB3/DimensionsRecomp with robocopy (/E, mtimes kept;
   --resync: /MIR after a new S-batch on snap1), except rexglue-sdk/out (snap1-sdk's output dir), rexlego/generated
   and rexlego/legodimensions_config.toml (step 3 writes those); rexlego/out (Agent 6's native banks) is copied: the
   native flags read it. Then every copied file must match snap1 in size and mtime,
'''
EXCL_T = "EXCL_DIRS = [r'rexglue-sdk\\out', r'rexlego\\out', r'rexlego\\generated']\n"
EXCL_NB = ("EXCL_DIRS = [r'rexglue-sdk\\out', r'rexlego\\generated']  # nativeB: rexlego/out (Agent 6's native banks) "
           "is copied\n")
ARG_T = "    a = ap.parse_args()\n"
ARG_R = ("    ap.add_argument('--check-only', action='store_true', help='step 1 and the snapshot tag only: nothing is "
         "copied')\n    a = ap.parse_args()\n")
START_T = "    log('START prep-b: install tree %s, snapshot copy %s' % (I, DST))\n"
START_R = "    log('START prep-@V@: install tree %s, snapshot copy %s' % (I, DST))\n"
STEP2_T = ("    # 2. snapB3 = snap1 (S2) minus the excluded dirs and the config. Every write below goes under "
           "build/agent2/snapB3:\n")
STEP2_R = r'''    # snapshot tag (task #14): the newest PATCHES-S<N>[suffix].tsv in apply order (S1, S2, S3, S3d); the newest STATE
    # file must be that tag's (snap-patch.py apply writes both), and only an S3 or S3d base is accepted
    pfiles = sorted((f for f in os.listdir(os.path.join(A, 'snap1')) if re.fullmatch(r'PATCHES-S\d+[a-z]*\.tsv', f)),
                    key=lambda f: (int(re.match(r'PATCHES-S(\d+)', f)[1]), f))
    snap_tag = pfiles[-1][8:-4] if pfiles else '?'
    states = sorted((f for f in os.listdir(os.path.join(A, 'snap1')) if re.fullmatch(r'STATE-S\d+[a-z]*-\d{4}\.tsv', f)),
                    key=lambda f: os.stat(os.path.join(A, 'snap1', f)).st_mtime_ns)
    if snap_tag not in ('S3', 'S3d') or not states or not states[-1].startswith('STATE-%s-' % snap_tag):
        fail('snap1: newest PATCHES tag %s, newest STATE file %s: an S3 or S3d base with its STATE file is required'
             % (snap_tag, states[-1] if states else None))
    log('snapshot tag %s: PATCHES %s; newest STATE file %s' % (snap_tag, ', '.join(f[8:-4] for f in pfiles), states[-1]))
    if a.check_only:
        log('DONE --check-only: step 1 passed, snapshot tag %s; nothing copied (%s %s)'
            % (snap_tag, DST, 'exists' if os.path.exists(DST) else 'does not exist yet'))
        return 0
    # 2. snapB3 = snap1 (S3 or S3d) minus the excluded dirs and the config. Every write below goes under build/agent2/snapB3:
'''
PF_T = r'''    pfiles = sorted((f for f in os.listdir(os.path.join(A, 'snap1')) if re.fullmatch(r'PATCHES-S\d+\.tsv', f)),
                    key=lambda f: int(f[9:-4]))
'''
FIRST_T = ("        \"codegen build B (Agent 9's codegen option; perf-notes/agent9-codegen.md 'Session 2: regen+build "
           "recipe'): \"\n")
FIRST_RB = ("        \"rollback build @VU@ (recipe step @STEP@) = codegen build B (Agent 9's codegen option; \"\n"
            "        \"perf-notes/agent9-codegen.md 'Session 2: regen+build recipe'): \"\n")
FIRST_NB = ("        \"nativeB = native codegen build B (Agent 9's codegen option; \"\n"
            "        \"perf-notes/agent9-codegen.md 'Session 2: regen+build recipe'): \"\n")
NOTES_T = r'''        '(the S2 snapshot config is %s).' % (sums_sha, len(sums), sums_time, cfg, s2cfg),
        'snapB3 = build/agent2/snap1/DimensionsRecomp at S2, copied by prep-b.py (robocopy, mtimes kept) without '
        'rexglue-sdk/out and rexlego/out: %d files, %d bytes, all equal to snap1 in size and mtime; the %d patched '
        'files hash-equal their PATCHES rows.' % (len(df), nb, len(rows) - len(skipped)),
'''
NOTES_R = r'''        '(the %s snapshot config is %s).' % (sums_sha, len(sums), sums_time, cfg, snap_tag, s2cfg),
        'snapB3 = build/agent2/snap1/DimensionsRecomp at %s, copied by prep-@V@.py (robocopy, mtimes kept) without '
        '@WITHOUT@: %d files, %d bytes, all equal to snap1 in size and mtime; the %d patched '
        'files hash-equal their last PATCHES row (%s).' % (snap_tag, len(df), nb, len(rows) - len(skipped),
                                                          ', '.join(f[8:-4] for f in pfiles)),
'''
A_T = "        'A (the same snapshot and SDK, pinned 0.0.23.3 codegen): build/agent2/devoff2-bin.',\n"
A_RB = ("        'A (the same snapshot and SDK, pinned 0.0.23.3 codegen): build/agent2/devoff3-bin (the S3 OFF build; S3d '\n"
        "        'changes only rexlego/src/gpu_native/draw.cpp, which OFF builds do not compile).',\n")
A_NB = ("        'A (the same snapshot and SDK, pinned 0.0.23.3 codegen): build/agent2/%s.'\n"
        "        % ('native3d-bin' if snap_tag == 'S3d' else 'native3-bin'),\n")
PREP_PINS = ['VARIANT = ', 'SUMS_SHA = ', 'CFG_SHA = ', 'TOOL_SHA = ', 'if sums_sha != SUMS_SHA or len(sums) != ',
             "fail('SHA256SUMS.txt sha256 %s with %d entries; build B expects the pinned"]

# ---------------------------------------------------------------- run-b edits (targets are after the snapB3 rename)
R1_T = "# Agent 2 - codegen build B (Agent 9's codegen option, perf-notes/agent9-codegen.md \"Session 2: regen+build recipe\")\n"
R1_R = r'''# Agent 2 - rollback build @VU@ on an S3 base, at Agent 1's GO only (task #14): a clone of
# build/agent9/repin/@TREE@/run-b.ps1 (Agent 9's re-pin of run-b.ps1 for recipe step @STEP@), made by
# build/agent2/make-rb-clones.py (diffs: build/agent2/RB-diffs). Agent 1, 03:11: the base is snap1's current tree (S3
# or S3d) in the new copy build\agent2\snapB3 (prep-@V@.py); snapB and snapB-off stay untouched; A = devoff3-bin.
# Changed from the re-pin: snapB -> snapB3 (copy, game tree snapB3-off, build tag, logs, notes), -Out
# devoff@VU@-bin, -SnapTag (default: the tag prep-@V@.py copied, read from snapB3-manifest-notes.txt; another value
# is refused), -Compare devoff3-bin (it must be staged; -Out must not be), the S3 exe string (as devoff3), the guards
# (08:30-12:00, -Jobs <= 10, no other snapshot build driver) and the staged-hash log lines.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-@V@.ps1 [-Jobs 10] [-SkipConfigure] [-NoBuild]
# The re-pin's text follows (snapB renamed snapB3).
# Agent 2 - codegen build B (Agent 9's codegen option, perf-notes/agent9-codegen.md "Session 2: regen+build recipe")
'''
R2_T = r'''# 3. stage-snap-bin.ps1 -Variant off -SnapTag S2 -BuildTag snapB3 -GameTree snapB3-off -OutDir build\agent2\devoffB-bin
#    -GameSnap snapB3\DimensionsRecomp -CompareBin build\agent2\devoff2-bin (A) -ManifestNotesFile snapB3-manifest-notes.txt
'''
R2_R = r'''# 3. stage-snap-bin.ps1 -Variant off -SnapTag <prep tag> -BuildTag snapB3 -GameTree snapB3-off -OutDir build\agent2\devoff@VU@-bin
#    -GameSnap snapB3\DimensionsRecomp -CompareBin build\agent2\devoff3-bin (A) -ManifestNotesFile snapB3-manifest-notes.txt
'''
R3_T = r'''param([int]$Jobs = 10, [switch]$SkipConfigure, [switch]$NoBuild, [string]$Out = 'devoffB-bin', [string]$SnapTag = 'S2',
    [string]$Compare = 'devoff2-bin', [string]$Install = 'build\agent9\install\@TREE@')
'''
R3_R = r'''param([int]$Jobs = 10, [switch]$SkipConfigure, [switch]$NoBuild, [string]$Out = 'devoff@VU@-bin', [string]$SnapTag = '',
    [string]$Compare = 'devoff3-bin', [string]$Install = 'build\agent9\install\@TREE@')
'''
R4_T = r'''# the same SDK as devoff2 (S2): Agent 12's #22 cvar name and description are in rexruntime.dll
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
'''
R4_R = r'''# the S3 SDK, as devoff3 (run-s3.ps1): Agent 12's #22 cvar name and description are in rexruntime.dll, and the tail of
# Agent 12's pause_safe_order description (share/rex_app.cpp, compiled into the game) is in the exe
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
$exeStrings = 'which can hang when the guest pauses'
'''
R5_T = r'''$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START codegen build B from $SnapTag (snapshot copy $snapB3, game tree $gameB, -j $Jobs, install tree $Install)"
'''
R5_R = r'''# guards (task #14): no start 08:30-12:00 (no builds from 08:30), -Jobs capped at 10, no other snapshot build driver
# (\bb-chain: not this script's own rb-chain.ps1 parent)
$tod = (Get-Date).TimeOfDay
if ($tod -ge [TimeSpan]'08:30:00' -and $tod -lt [TimeSpan]'12:00:00') { Log 'STOP: no builds from 08:30 (session-3 rule)'; exit 3 }
if ($Jobs -gt 10) { Log "-Jobs $Jobs capped at 10"; $Jobs = 10 }
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|\bb-chain\.ps1|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|run-@OTHER@\.ps1|run-nb\.ps1|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Log "STOP: another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START rollback build @VU@ (snapshot copy $snapB3, game tree $gameB, -j $Jobs, install tree $Install)"
'''
R6_T = "if (-not (Test-Path $notes)) { Log 'STOP: run prep-b.py first (no snapB3-manifest-notes.txt)'; exit 2 }\n"
R6_R = r'''if (-not (Test-Path $notes)) { Log 'STOP: run prep-@V@.py first (no snapB3-manifest-notes.txt)'; exit 2 }
$tl = @(Select-String -LiteralPath $notes -Pattern '^snapB3 = build/agent2/snap1/DimensionsRecomp at (S\d+[a-z]*), copied by prep-@V@\.py ')
if ($tl.Count -ne 1) { Log 'STOP: snapB3-manifest-notes.txt was not written by prep-@V@.py (no snapshot tag line)'; exit 2 }
$prepTag = $tl[0].Matches[0].Groups[1].Value
if (-not $SnapTag) { $SnapTag = $prepTag } elseif ($SnapTag -ne $prepTag) { Log "STOP: -SnapTag $SnapTag, but prep-@V@.py copied snap1 at $prepTag"; exit 3 }
if (-not (Test-Path -LiteralPath "$A\$Compare\MANIFEST.txt")) { Log "STOP: $Compare is not staged (no MANIFEST.txt; it is the -CompareBin reference)"; exit 4 }
if (Test-Path -LiteralPath "$A\$Out\MANIFEST.txt") { Log "STOP: $Out is already staged (MANIFEST.txt exists); pass another -Out"; exit 4 }
Log "snapshot tag $SnapTag (the prep-@V@.py copy); A = $Compare; out $Out"
'''
R7_T = r'''    '-OutDir', "$A\$Out", '-GameSnap', $snapB3, '-CompareBin', "$A\$Compare", '-RuntimeStrings', $rtStrings,
    '-WhatText', $what, '-CodegenNote', $cgNote, '-ManifestNotesFile', $notes)
'''
R7_R = r'''    '-OutDir', "$A\$Out", '-GameSnap', $snapB3, '-CompareBin', "$A\$Compare", '-RuntimeStrings', $rtStrings,
    '-ExeStrings', $exeStrings, '-WhatText', $what, '-CodegenNote', $cgNote, '-ManifestNotesFile', $notes)
'''
R8_T = r'''if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
Log ("DONE codegen build B -> $Out, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
'''
R8_R = r'''if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
foreach ($f in 'legodimensions.exe', 'legodimensions.map', 'rexruntime.dll', 'rexgpu-xenos.dll', 'MANIFEST.txt') {
    $p = "$A\$Out\$f"
    if (Test-Path -LiteralPath $p) { Log ("  staged {0}: {1} B, sha256 {2}" -f $f, (Get-Item -LiteralPath $p).Length, (Get-FileHash -LiteralPath $p).Hash) }
}
$man = @(Get-Content -Encoding UTF8 -LiteralPath "$A\$Out\MANIFEST.txt")
$cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
$np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
$nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
Log ("DONE rollback build @VU@ -> $Out, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
'''
RUN_PINS = ['$nolr = ', 'if ($sumsSha -ne ', 'if ($cfgSha -ne ', '$cgNote = ', '$what = ']

# ---------------------------------------------------------------- stop-snap.ps1
SS_T1 = "#    driver and run-s3.ps1; 02:59: run-s3d.ps1, the native3d driver.)\n"
SS_R1 = ("#    driver and run-s3.ps1; 02:59: run-s3d.ps1, the native3d driver; 03:25: task #14's rb-chain.ps1, run-rb1.ps1,\n"
         "#    run-rb2.ps1, prep-rb1.py, prep-rb2.py, run-nb.ps1 and prep-nb.py; their trees build/agent2/snapB3* match the\n"
         "#    orphan pattern already.)\n")
SS_T2 = "$drivers = 'build-snap\\.ps1|run-s2\\.ps1|run-s3\\.ps1|run-s3d\\.ps1|run-b\\.ps1|prep-b\\.py|b-chain\\.ps1'\n"
SS_R2 = ("$drivers = 'build-snap\\.ps1|run-s2\\.ps1|run-s3\\.ps1|run-s3d\\.ps1|run-b\\.ps1|prep-b\\.py|b-chain\\.ps1|"
         "rb-chain\\.ps1|run-rb\\d\\.ps1|prep-rb\\d\\.py|run-nb\\.ps1|prep-nb\\.py'\n")


def main():
    force = '--force' in sys.argv[1:]
    trees = [('rb1', 'RB1', 'rb1-nolocal', '9.1', '880', 'rb2', '392748EA2A1D969E', '68A9BEF7D0F1F1C8'),
             ('rb2', 'RB2', 'rb2-nomusttail', '9.2', '870', 'rb1', 'AE352887A3968096', 'DC03630FBA10347B')]
    outs = {}
    diffs = {}
    for v, vu, tree, step, ent, other, psha, rsha in trees:
        m = {'V': v, 'VU': vu, 'TREE': tree, 'STEP': step, 'ENT': ent, 'OTHER': other,
             'WITHOUT': 'rexglue-sdk/out and rexlego/out'}
        sp = os.path.join(REPIN, tree, 'prep-b.py')
        sr = os.path.join(REPIN, tree, 'run-b.ps1')
        ps, pb, pc = load(sp, psha)
        rs, rb, rc = load(sr, rsha)
        pe = [(HEAD_T, fill(HEAD_RB, m)), (ARG_T, ARG_R), (START_T, fill(START_R, m)), (STEP2_T, STEP2_R), (PF_T, ''),
              (FIRST_T, fill(FIRST_RB, m)), (NOTES_T, fill(NOTES_R, m)), (A_T, A_RB)]
        pt = clone('prep-%s.py' % v, ps, pe, PREP_PINS)
        re_ = [(R1_T, fill(R1_R, m)), (R2_T, R2_R.replace('@VU@', vu)), (fill(R3_T, m), fill(R3_R, m)), (R4_T, R4_R),
               (R5_T, fill(R5_R, m)), (R6_T, fill(R6_R, m)), (R7_T, R7_R), (R8_T, fill(R8_R, m))]
        rt = clone('run-%s.ps1' % v, rs, re_, RUN_PINS)
        if ("[string]$Install = 'build\\agent9\\install\\%s')" % tree) not in rt:
            sys.exit('STOP: run-%s.ps1: the -Install default changed' % v)
        outs['prep-%s.py' % v] = dump(pt, pb, pc)
        outs['run-%s.ps1' % v] = dump(rt, rb, rc)
        diffs['prep-%s.py.diff' % v] = udiff('build/agent9/repin/%s/prep-b.py' % tree, 'build/agent2/prep-%s.py' % v, ps, pt)
        diffs['run-%s.ps1.diff' % v] = udiff('build/agent9/repin/%s/run-b.ps1' % tree, 'build/agent2/run-%s.ps1' % v, rs, rt)
    # nativeB prep from build/agent2/prep-b.py (batch-nolr pins)
    m = {'V': 'nb', 'WITHOUT': 'rexglue-sdk/out (rexlego/out, the native banks, copied)'}
    ns, nbom, ncrlf = load(os.path.join(A, 'prep-b.py'), 'C0067F18C299D551')
    ne = [(HEAD_T, HEAD_NB), (DOC2_T, DOC2_NB), (EXCL_T, EXCL_NB), (ARG_T, ARG_R), (START_T, fill(START_R, m)),
          (STEP2_T, STEP2_R), (PF_T, ''), (FIRST_T, FIRST_NB), (NOTES_T, fill(NOTES_R, m)), (A_T, A_NB)]
    nt = clone('prep-nb.py', ns, ne, PREP_PINS)
    outs['prep-nb.py'] = dump(nt, nbom, ncrlf)
    diffs['prep-nb.py.diff'] = udiff('build/agent2/prep-b.py', 'build/agent2/prep-nb.py', ns, nt)
    # stop-snap.ps1
    ssp = os.path.join(A, 'stop-snap.ps1')
    ss, sbom, scrlf = load(ssp, 'B9AECC6A')
    st = ss
    for tgt, rep in ((SS_T1, SS_R1), (SS_T2, SS_R2)):
        if st.count(tgt) != 1:
            sys.exit('STOP: stop-snap.ps1 target matches %d times: %r' % (st.count(tgt), tgt[:80]))
        st = st.replace(tgt, rep)
    diffs['stop-snap.ps1.RB.diff'] = udiff('build/agent2/stop-snap.ps1.pre-RB', 'build/agent2/stop-snap.ps1', ss, st)
    # run-nb.ps1 against run-b.ps1, for reference (run-nb.ps1 is written by hand)
    nbp = os.path.join(A, 'run-nb.ps1')
    if os.path.isfile(nbp):
        rbs = load(os.path.join(A, 'run-b.ps1'), '0D159651')[0]
        diffs['run-nb.ps1.vs-run-b.diff'] = udiff('build/agent2/run-b.ps1', 'build/agent2/run-nb.ps1', rbs, load(nbp, '')[0])
    # write (nothing is written unless every check above passed)
    exists = [k for k in outs if os.path.exists(os.path.join(A, k))]
    if os.path.exists(ssp + '.pre-RB'):
        exists.append('stop-snap.ps1.pre-RB')
    if exists and not force:
        sys.exit('STOP: already made (%s); nothing written (use --force to remake the clones)' % ', '.join(exists))
    os.makedirs(DIFFS, exist_ok=True)
    for k, b in outs.items():
        open(os.path.join(A, k), 'wb').write(b)
        print('wrote build/agent2/%s: %d B, sha256 %s' % (k, len(b), sha16(b)))
    if not os.path.exists(ssp + '.pre-RB'):
        open(ssp + '.pre-RB', 'wb').write(open(ssp, 'rb').read())
        nb_ = dump(st, sbom, scrlf)
        open(ssp, 'wb').write(nb_)
        print('patched build/agent2/stop-snap.ps1 (backup stop-snap.ps1.pre-RB): sha256 %s' % sha16(nb_))
    for k, d in diffs.items():
        b = d.encode('utf-8')
        open(os.path.join(DIFFS, k), 'wb').write(b)
        print('diff build/agent2/RB-diffs/%s: %d lines, sha256 %s' % (k, d.count('\n'), sha16(b)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
