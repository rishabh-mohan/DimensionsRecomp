"""Agent 2 - "Build inventory" for perf-notes/agent2-baseline.md (Agent 1, 04:39): one row per staged bin (snapshot /
patch level, exe sha256, MANIFEST sha256, native GPU fingerprint, disk size, what it is for) and one row per clone /
snapshot / work dir (size, files, role, could it be deleted later). READ-ONLY on every build dir: it deletes, moves and
rewrites nothing there. It writes build/agent2/inventory.md (the tables) and build/agent2/inventory.tsv (raw rows);
with --insert it also puts the tables into the notes file between the inventory markers (backup first, LF kept).
  python build\\agent2\\inventory.py [--light] [--insert]
--light : no exe re-hash and no recursive walk (Agent 1, 05:31: no scans of build trees while a game runs): exe hashes
          and bin sizes come from the MANIFEST rows, dir sizes are left out; only single-directory listings are made.
default : also re-hash every staged exe (must equal its MANIFEST row) and size every dir (scandir walk, no hashing;
          junctions and symlinks are not followed, so baseline/'s generated code is counted once, under baseline/).
          Run it only when no game is running (Agent 8's all-clear).
"""
import hashlib
import os
import re
import shutil
import stat
import sys
import time

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
LIGHT = '--light' in sys.argv[1:]
INSERT = '--insert' in sys.argv[1:]
BEGIN, END = '<!-- inventory:begin -->', '<!-- inventory:end -->'

# label, dir (relative to R), snapshot / patch level, what it is for
BINS = [
    ('baseline', r'build\baseline-bin', 'pristine 127e04b + SDK 2897c31 (no sprint patch), OFF',
     'reference: the unpatched game (perf and functional baseline)'),
    ('devoff1', r'build\agent2\devoff1-bin', 'S1, OFF (p1 and p2 touch only native files; p2 came after it)',
     'history: first dev OFF build (superseded by devoff2, devoff3)'),
    ('native', r'build\agent2\native-bin', 'S1 + p1 device.cpp + p2 plume_d3d12, native',
     'history: first native build (superseded)'),
    ('devoff2', r'build\agent2\devoff2-bin', 'S2 (S1+p1/p2 + 18 rows), OFF',
     'the A side of build B (devoffB vs devoff2); superseded by devoff3'),
    ('native2', r'build\agent2\native2-bin', 'S2, native', 'history: superseded by native3'),
    ('devoffB', r'build\agent2\devoffB-bin', 'B = S2 + codegen batch-nolr, OFF (snapB)',
     'codegen option B; B gate PASS'),
    ('devoff3', r'build\agent2\devoff3-bin', 'S3 (game 001336f + SDK c5fe668 + plume/simde edits), OFF; also the OFF '
     'build of S3d/S3e (OFF builds skip draw.cpp)', 'current dev OFF build'),
    ('native3', r'build\agent2\native3-bin', 'S3, native', 'S3 native; the reference native3d was compared with'),
    ('native3d', r'build\agent2\native3d-bin', 'S3d = S3 + Agent 4 draw.cpp 5EA1F357 (= game 08933a7 + SDK c5fe668 + '
     'plume/simde edits), native',
     'current native build (n-rows PASS, 0 hash=0 lines in n0/n2/n3: Agents 8 and 10, 05:00); reference for nativeB'),
    ('nativeB', r'build\agent2\nativeB-bin', 'S3d + codegen batch-nolr, native (snapB3)',
     "codegen B on native: Agent 10's native-hook checks (1a static PASS, Agents 9 and 10; 1b route pair PASS vs "
     "native3d, Agent 10 05:24) and Agent 8's nativeB pair"),
    ('native3e', r'build\agent2\native3e-bin', "S3e = S3d + Agent 4 draw.cpp ('|| !vs' variant), native",
     "only if built (Agent 1's GO): the draw.cpp variant"),
]

KEEP = 'no (keep)'
S3D_OK = 'yes (S3d is accepted and committed: game 08933a7)'
# dir (relative to R), role, could it be deleted later?
DIRS = [
    (r'build\agent2\snap1', 'snapshot of DimensionsRecomp at the current patch level (S3d); the base of every snapshot '
     'build and of snap-patch.py', KEEP),
    (r'build\agent2\snap1-sdk', 'SDK build + install of snap1 (rexruntime.dll, rexgpu-xenos.dll)', KEEP),
    (r'build\agent2\snap1-off', 'OFF game tree of snap1 (devoff1/2/3)', KEEP),
    (r'build\agent2\snap1-on', 'native game tree of snap1 (native, native2, native3, native3d, native3e)', KEEP),
    (r'build\agent2\snap1-backup-S2', 'snap-patch.py apply backup: the snap1 files S2 replaced (for revert)', S3D_OK),
    (r'build\agent2\snap1-backup-S3', 'apply backup of S3 (for revert)', S3D_OK),
    (r'build\agent2\snap1-backup-S3d', 'apply backup of S3d (for revert)', S3D_OK),
    (r'build\agent2\snap1-backup-S3e', 'apply backup of S3e (only if S3e was applied)', 'yes, once S3e is accepted'),
    (r'build\agent2\snapB', 'snap1 at S2 + install/batch-nolr: the source of build B', 'yes, after the B decision'),
    (r'build\agent2\snapB-off', 'OFF game tree of build B (devoffB)', 'yes, after the B decision'),
    (r'build\agent2\snapB3', 'snap1 at S3d + batch-nolr: the source of nativeB (and of the unbuilt rb1/rb2 rollbacks)',
     'yes, after the nativeB checks / B decision'),
    (r'build\agent2\snapB3-on', 'native game tree of nativeB', 'yes, after the nativeB checks / B decision'),
    (r'build\agent2\codegen-frozen', 'codegen stand-ins (codegen-frozen/-frozen2.exe) used by every snapshot build',
     KEEP),
    (r'build\agent2\codegen-tool', 'frozen rexglue.exe + DLLs (baseline / dev configure, codegen-watch)', KEEP),
    (r'build\agent2\compat', 'CMake project include + native_lock_elide_compat.h, used by build-snap.ps1', KEEP),
    (r'build\agent2\live-backup', 'backup of my one live edit (plume_d3d12.cpp B88E4E86)', KEEP),
    (r'build\agent2\gen-noflag', 'session-1 codegen output check (887 files); the pinned code is in baseline/',
     'yes (test output)'),
    (r'build\agent2\c1-sweep', 'session-1 compile-one sweep outputs', 'yes (test output)'),
    (r'build\agent2\cf2-test', 'task #1 codegen-frozen2 test', 'yes (test output)'),
    (r'build\agent2\compile-one-test', 'session-1 compile-one test', 'yes (test output)'),
    (r'build\agent2\nmtest', 'session-1 nm pipe test', 'yes (test output)'),
    (r'build\agent2\ppcmap-test', 'step 6 PPC .map fix test (its logs are the evidence)', 'yes, after the report'),
    (r'build\agent2\probe-toggle', 'session-1 find_package toggle probe tree', 'yes (test output)'),
    (r'build\agent2\scratch-inc', 'session-1 scratch include test', 'yes (test output)'),
    (r'build\agent2\recovered', 'notes recovered after a restart', 'yes (history)'),
    (r'build\agent2\__pycache__', 'Python bytecode cache', 'yes'),
    (r'build\agent2\notes-backup', 'backups of perf-notes/agent2-baseline.md', 'later (small)'),
    (r'build\agent2\rbt-logs', 'tool test logs (rb-tools-test, S3e guard test)', 'later (small)'),
    (r'build\agent2\B-diffs', 'review diffs (build B tools)', 'later (small)'),
    (r'build\agent2\RB-diffs', 'review diffs (rb1/rb2/nb tools)', 'later (small)'),
    (r'build\agent2\S3-diffs', 'review diffs (S3 tools)', 'later (small)'),
    (r'build\agent2\S3d-diffs', 'review diffs (S3d tools)', 'later (small)'),
    (r'build\agent2\S3e-diffs', 'review diffs (S3e tools)', 'later (small)'),
    (r'build\baseline', 'baseline game build tree (the source of baseline-bin)', KEEP),
    (r'build\sdk', 'SDK baseline build; its compile_commands.json is compile-one\'s default DB and snap-gate uses it',
     KEEP),
    (r'build\dev', 'session-1 NATIVE_GPU=ON configure of the live repo (compile-one -Db build\\dev\\...)',
     'later, once no agent uses compile-one on it'),
    (r'build\sdk-dev', 'session-1 SDK dev configure (configure only, tests ON)', 'later, if nobody uses its DB'),
    (r'baseline', 'baseline snapshot (127e04b + SDK 2897c31); its rexlego/generated is the pinned generated code '
     '(the live repo junctions to it; gen-check reference)', KEEP),
]
LEGEND = ('- Patch levels (applied to the snapshot `build/agent2/snap1`; rows in `PATCHES-S*.tsv`, listed in every '
          'MANIFEST): S1 = p1 device.cpp + p2 plume_d3d12.cpp; S2 = S1 + 18 rows; S3 = S2 + 28 rows = game 001336f + '
          'SDK c5fe668 + the uncommitted plume/simde edits; S3d = S3 + Agent 4 draw.cpp = game 08933a7 (same SDK and '
          "edits). B = Agent 9's codegen option batch-nolr (`build/agent9/install/batch-nolr`, 430 TUs). OFF = "
          'NATIVE_GPU=OFF, native = NATIVE_GPU=ON.')

# a '|' in a table cell would split it: escape it (GitHub tables render the escaped form as '|')
BINS = [(a, b, c.replace('|', chr(92) + '|'), d.replace('|', chr(92) + '|')) for a, b, c, d in BINS]
DIRS = [(a, b.replace('|', chr(92) + '|'), c.replace('|', chr(92) + '|')) for a, b, c in DIRS]


def sha(p, n=None):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    d = h.hexdigest().upper()
    return d[:n] if n else d


def walk(top):
    """(bytes, files, dirs, links skipped); never follows junctions or symlinks."""
    tot = nf = nd = nl = 0
    stack = [top]
    while stack:
        d = stack.pop()
        try:
            it = os.scandir(d)
        except OSError:
            continue
        with it:
            for e in it:
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                if getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    nl += 1
                    continue
                if stat.S_ISDIR(st.st_mode):
                    nd += 1
                    stack.append(e.path)
                else:
                    nf += 1
                    tot += st.st_size
    return tot, nf, nd, nl


def human(b):
    return '%.2f GiB' % (b / 2 ** 30) if b >= 2 ** 30 else '%.1f MiB' % (b / 2 ** 20)


t0 = time.time()
now = time.strftime('%H:%M')
rows, problems, info = [], [], []
for label, rel, level, why in BINS:
    d = os.path.join(R, rel)
    man = os.path.join(d, 'MANIFEST.txt')
    if not os.path.isdir(d):
        if label != 'native3e':
            problems.append('%s: %s is missing' % (label, rel))
        continue
    if not os.path.isfile(man):
        problems.append('%s: no MANIFEST.txt' % label)
        continue
    with open(man, 'r', encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    exe_row = None
    rt16 = '-'
    mf_b = mf_n = 0
    for line in text.splitlines():
        c = line.split('\t')
        if len(c) >= 4 and not line.startswith('#') and re.fullmatch(r'[0-9A-Fa-f]{64}', c[3]):
            if c[1].isdigit():
                mf_b += int(c[1])
            else:
                problems.append('%s: MANIFEST row %s has no byte size' % (label, c[0]))
            mf_n += 1
            if c[0] == 'legodimensions.exe':
                exe_row = c
            elif c[0] == 'rexruntime.dll':
                rt16 = c[3][:16].upper()
    m = re.search(r'# staged (\d{4})-(\d\d)-(\d\d) (\d\d:\d\d)', text)
    staged = '%s-%s %s' % (m.group(2), m.group(3), m.group(4)) if m else '?'
    m = re.search(r'at (S\w*) \(((?:STATE|MANIFEST)-[\w-]+)\.tsv', text)
    rec = '%s' % m.group(2) if m else ''
    m = re.search(r'build tag (\w+)', text)
    tag = m.group(1) if m else ''
    m = re.search(r'native GPU ([0-9a-f]{16})', text)
    fp = m.group(1) if m else 'n/a (OFF)'
    if not exe_row:
        problems.append('%s: no legodimensions.exe row in MANIFEST.txt' % label)
        continue
    exe_sha = exe_row[3].upper()
    man_b = os.path.getsize(man)
    rehash = '-'
    if LIGHT:
        size, nfile = mf_b + man_b, mf_n + 1
    else:
        got = sha(os.path.join(d, 'legodimensions.exe'))
        rehash = 'match' if got == exe_sha else 'MISMATCH %s' % got[:16]
        if got != exe_sha:
            problems.append('%s: exe re-hash %s != MANIFEST %s' % (label, got[:16], exe_sha[:16]))
        size, nfile, _, _ = walk(d)
        if (size, nfile) != (mf_b + man_b, mf_n + 1):
            info.append('%s holds %d files, %d B; its MANIFEST lists %d files, + MANIFEST.txt = %d B'
                        % (label, nfile, size, mf_n, mf_b + man_b))
    rows.append(dict(label=label, rel=rel, level=level, why=why, staged=staged, rec=rec, tag=tag, fp=fp,
                     exe16=exe_sha[:16], exe=exe_sha, exe_size=int(exe_row[1]), man16=sha(man, 16), rt16=rt16,
                     rehash=rehash, size=size, nfile=nfile))

# dirs: single-directory listings in both modes; the recursive size walk only in the full run
listed = {os.path.normcase(os.path.join(R, r)) for r, _, _ in DIRS}
binset = {os.path.normcase(os.path.join(R, r)) for _, r, _, _ in BINS}
extra = []
for e in os.scandir(A):
    if e.is_dir(follow_symlinks=False) and os.path.normcase(e.path) not in listed | binset:
        extra.append((os.path.relpath(e.path, R), '(not in the list; check)', '?'))
drows = []
for rel, role, dele in DIRS + extra:
    p = os.path.join(R, rel)
    if not os.path.isdir(p):
        if 'S3e' not in rel:
            problems.append('dir %s is missing' % rel)
        continue
    b = nf = None
    nl = 0
    if not LIGHT:
        b, nf, _, nl = walk(p)
    drows.append(dict(rel=rel, role=role, dele=dele, size=b, nfile=nf, nlink=nl))
top_b = top_n = 0
for e in os.scandir(A):
    if e.is_file(follow_symlinks=False):
        top_b += e.stat(follow_symlinks=False).st_size
        top_n += 1
drows.append(dict(rel=r'build\agent2\*.* (top-level files)', role='scripts, logs, rules, notes, PATCHES copies',
                  dele='later (small); keep the scripts', size=top_b, nfile=top_n, nlink=0))
others = sorted((e.name for e in os.scandir(os.path.join(R, 'build')) if e.is_dir(follow_symlinks=False) and
                 os.path.normcase(e.path) not in listed | binset | {os.path.normcase(A)}), key=lambda s: (len(s), s))

free = shutil.disk_usage('C:\\').free
md = [BEGIN,
      '**Build inventory** (generated %s by `build/agent2/inventory.py`%s; sizes are file bytes in MiB/GiB (2^20/2^30 B, as Explorer shows them), '
      'bin file counts include MANIFEST.txt; delete nothing until Agent 1 or the user says so)'
      % (now, ' --light: exe hashes and bin sizes from the MANIFEST rows, no re-hash; dir sizes not measured (no scans '
         'of build trees while a game runs, Agent 1 05:31)' if LIGHT else ''),
      '',
      '| Bin | Snapshot / patch level | exe sha256 (16) | MANIFEST sha256 (16) | Native GPU fingerprint | Disk size | '
      'What it is for |',
      '|---|---|---|---|---|---|---|']
for r in rows:
    lvl = r['level'] + ('; %s' % r['rec'] if r['rec'] else '') + (', tag %s' % r['tag'] if r['tag'] else '') + \
        '; staged %s' % r['staged']
    sz = '%s (%d files)' % (human(r['size']), r['nfile'])
    md.append('| `%s` | %s | %s | %s | %s | %s | %s |' % (r['rel'].replace('\\', '/'), lvl, r['exe16'], r['man16'],
                                                         r['fp'], sz, r['why']))
nb = sum(r['size'] for r in rows)
md.append('')
if LIGHT:
    md.append('- exe sha256 and bin sizes are the MANIFEST rows (not re-hashed or walked). Staged bins total %s. '
              'rexruntime.dll per bin is in `build/agent2/inventory.tsv`.' % human(nb))
else:
    md.append('- Every exe re-hashed at %s: %s. Staged bins total %s. rexruntime.dll per bin is in '
              '`build/agent2/inventory.tsv`.' % (now, 'all %d match their MANIFEST rows' % len(rows)
                                                 if all(r['rehash'] == 'match' for r in rows) else 'MISMATCHES, see '
                                                 'below', human(nb)))
for s in info:
    md.append('- Note: ' + s)
md.append(LEGEND)
md.append('')
md.append('| Dir | Size | Files | Role | Could be deleted later? |')
md.append('|---|---|---|---|---|')
for r in drows:
    md.append('| `%s` | %s | %s%s | %s | %s |' % (r['rel'].replace('\\', '/'),
                                                 'not measured' if r['size'] is None else human(r['size']),
                                                 '-' if r['nfile'] is None else '%d' % r['nfile'],
                                                 ' (+%d links not followed)' % r['nlink'] if r['nlink'] else '',
                                                 r['role'], r['dele']))
md.append('')
if LIGHT:
    md.append('- Dir sizes come with the full run (`inventory.py --insert`, without --light) when no game is running. '
              'Free C: %.1f GiB at %s.' % (free / 2 ** 30, now))
else:
    dl = sum(r['size'] for r in drows if r['dele'].startswith('yes'))
    ag = sum(r['size'] for r in drows if r['rel'].startswith('build\\agent2')) + nb - sum(
        r['size'] for r in rows if not r['rel'].startswith('build\\agent2'))
    md.append('- Total of the "yes" rows (could be deleted later): %s. build/agent2 in total (dirs, top-level files and '
              'its staged bins): %s. Free C: %.1f GiB at %s.' % (human(dl), human(ag), free / 2 ** 30, now))
if others:
    md.append("- Not sized here: %s under build/ (the other agents' dirs; not mine to judge)." % ', '.join(others))
if problems:
    md.append('- PROBLEMS: ' + '; '.join(problems))
md.append(END)
block = '\n'.join(md) + '\n'

with open(os.path.join(A, 'inventory.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(block)
with open(os.path.join(A, 'inventory.tsv'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('kind\tname\tsize\tfiles\texe_sha256\tmanifest16\trexruntime16\tfingerprint\trehash\n')
    for r in rows:
        f.write('bin\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (r['rel'], r['size'], r['nfile'], r['exe'], r['man16'],
                                                          r['rt16'], r['fp'], r['rehash']))
    for r in drows:
        f.write('dir\t%s\t%s\t%s\t\t\t\t\t\n' % (r['rel'], r['size'], r['nfile']))
print(block)
print('%d bins, %d dirs, %d problem(s), %d note(s), %.1f s, %s; wrote build/agent2/inventory.md and inventory.tsv'
      % (len(rows), len(drows), len(problems), len(info), time.time() - t0, 'light' if LIGHT else 'full'))

if INSERT:
    with open(NOTES, 'rb') as f:
        raw = f.read()
    if b'\r\n' in raw:
        sys.exit('REFUSED: the notes file has CRLF line ends')
    t = raw.decode('utf-8')
    if t.count(BEGIN) == 1 and t.count(END) == 1:
        i, j = t.index(BEGIN), t.index(END) + len(END) + 1
        t = t[:i] + block + t[j:]
    elif BEGIN not in t and END not in t and t.count('\n**Staged bins**') == 1:
        t = t.replace('\n**Staged bins**', '\n' + block + '\n**Staged bins**')
    else:
        sys.exit('REFUSED: markers or the **Staged bins** anchor not found exactly once (nothing written)')
    t = re.sub(r'(?m)\A(# Agent 2: build pipeline - RESUME NOTE \(.*?; updated )\d\d:\d\d\)', r'\g<1>%s)' % now, t)
    bk = os.path.join(A, 'notes-backup', 'agent2-baseline.md.' + time.strftime('%H%M%S'))
    shutil.copy2(NOTES, bk)
    b = t.encode('utf-8')
    with open(NOTES, 'wb') as f:
        f.write(b)
    print('inserted into %s (backup %s): %d B, sha256 %s' % (NOTES, bk, len(b), hashlib.sha256(b).hexdigest()[:16].upper()))
if problems:
    sys.exit(2)
