"""stage.py (Agent 9, run-2 task #22, 2026-11-22): the S4c package for #24 (GPU-wait back-off) plus #30's CMake option.

  python stage.py stage    reads the live rexlego CMakeLists.txt (must hash to BASE_SHA: game 1bd322e; = snap1 = snapB)
                           and the rated draft (DRAFT_SHA, LF, b2r row 33), and writes
                             base/rexlego/CMakeLists.txt           copy of live (CRLF)
                             new/rexlego/CMakeLists.txt            + #30's option block after :154 (TT_LOCK_TRACE's
                                                                   endif() and its blank line), + #24's block before
                                                                   :168 if(WIN32) (after DEV_PROBES' endif() at :166
                                                                   and its blank line)
                             new/rexlego/src/gpu_wait_backoff.cpp  byte copy of the draft (LF)
                             new-24only/rexlego/CMakeLists.txt     + #24's block only (fallback if #30's option is
                                                                   not wanted; same new TU)
                             s4c-24-30.diff, s4c-24-only.diff      -p1 from DimensionsRecomp/; pure insertions, hunks
                                                                   written at the insertion points with 3 context
                                                                   lines. The CMakeLists.txt hunk lines keep CRLF (the
                                                                   file is CRLF); the new-file lines are LF (= the
                                                                   draft). Never re-save the diffs in an editor.
  python stage.py verify   applies each diff to scratch copies of base/ outside any git work tree
                           (GIT_CEILING_DIRECTORIES = scratch/):
                             git -c core.autocrlf=false apply --check -v, apply, then apply -R --check on the result;
                             GNU patch --binary --dry-run, then apply;
                           every result must equal new/ (or new-24only/) by sha256, with no stray files.
                           -> apply-check.txt
  python stage.py hashes   HASHES.txt for every package file (+ the inputs).
Read-only on the live and snap trees; writes only under this folder. No build and no git write (git apply runs on
scratch copies outside any repository).
"""
import hashlib, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(HERE, *(['..'] * 5)))


def P(*a):
    return os.path.join(R, *a)


def H(*a):
    return os.path.join(HERE, *a)


LIVE_CML = P('DimensionsRecomp', 'rexlego', 'CMakeLists.txt')
OTHER_CML = [('snap1 (S4a tree)', P('build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego', 'CMakeLists.txt')),
             ('snapB (B tree)', P('build', 'agent2', 'snapB', 'DimensionsRecomp', 'rexlego', 'CMakeLists.txt'))]
DRAFT = P('build', 'agent9', 's4', 'fence-wait', 'gpu_wait_backoff.cpp.draft')
BASE_SHA = '3690D5D76AA9FBED39D3559163C9F87D380124D9657FE450896AAD1F21607429'
DRAFT_SHA = '01D9F8F3464C861401C3BE98F797938619C5DD85B1AEA166B6D9CED053FA19DD'
CML, TU = 'rexlego/CMakeLists.txt', 'rexlego/src/gpu_wait_backoff.cpp'
PATCH_EXE = r'C:\Program Files\Git\usr\bin\patch.exe'
VARIANTS = [('s4c-24-30.diff', 'new', True), ('s4c-24-only.diff', 'new-24only', False)]

# #30 (S4.2.4 spec): option after :154, the :143-154 pattern; source-scoped define, so the generated TUs never rebuild.
BLOCK30 = [
    '# Scene-walk call-count probe (S4 #30): a separate diagnostic build, never',
    '# timed; no probe hooks in a normal build. Turning it on needs',
    '# src/scene_walk_probe.cpp, and the configure stops if that file is missing.',
    'option(LEGODIMENSIONS_SCENE_WALK_PROBE "Build the scene-walk call-count probe" OFF)',
    'if(LEGODIMENSIONS_SCENE_WALK_PROBE)',
    '    if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/scene_walk_probe.cpp")',
    '        message(FATAL_ERROR "LEGODIMENSIONS_SCENE_WALK_PROBE: src/scene_walk_probe.cpp is missing (S4 #30)")',
    '    endif()',
    '    list(APPEND LEGODIMENSIONS_SOURCES src/scene_walk_probe.cpp)',
    '    set_property(SOURCE src/native_memops.cpp src/native_skin_diagnostics.cpp',
    '        APPEND PROPERTY COMPILE_DEFINITIONS LEGODIMENSIONS_SCENE_WALK_PROBE=1)',
    'endif()',
    '',
]
# #24: the code lines are the draft header's block (gpu_wait_backoff.cpp.draft:29-33, rated in b2r row 33).
BLOCK24 = [
    '# GPU-wait back-off (S4 #24): pass-through hooks on the fence and query polls,',
    '# Xenos builds only (native builds never reach those waits). Off unless',
    '# LEGO_GPU_WAIT_BACKOFF_US is set: unset, every hook calls __imp__ at once.',
    'if(NOT LEGODIMENSIONS_NATIVE_GPU)',
    '    list(APPEND LEGODIMENSIONS_SOURCES src/gpu_wait_backoff.cpp)',
    '    set_property(SOURCE src/gpu_wait_backoff.cpp APPEND PROPERTY',
    '        COMPILE_DEFINITIONS LEGO_GPU_WAIT_HOOK_GETDATA=1)',
    'endif()',
    '',
]


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def wr(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b)


def rel(p):
    return os.path.relpath(p, R).replace('\\', '/')


def eol(b):
    return 'CR=%d LF=%d' % (b.count(b'\r'), b.count(b'\n'))


def crlf_lines(b):
    t = b.decode('latin-1')
    if not t.endswith('\r\n'):
        raise SystemExit('CMakeLists.txt does not end in CRLF')
    body = t[:-2].split('\r\n')
    if any('\r' in x or '\n' in x for x in body):
        raise SystemExit('CMakeLists.txt has a lone CR or LF')
    return body


def find(lines, pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise SystemExit('anchor not found after line %d' % (start + 1))


def plan(lines):
    """Insertion points as 'number of base lines before the block': after the blank line that follows
    TT_LOCK_TRACE's endif() (:154 -> 155) and after the blank line that follows DEV_PROBES' endif() (:166 -> 167)."""
    i_tt = find(lines, lambda s: s.startswith('option(LEGODIMENSIONS_TT_LOCK_TRACE '))
    e_tt = find(lines, lambda s: s == 'endif()', i_tt)
    i_dev = find(lines, lambda s: s.startswith('option(LEGODIMENSIONS_DEV_PROBES '), e_tt)
    e_dev = find(lines, lambda s: s == 'endif()', i_dev)
    if (i_tt, e_tt, i_dev, e_dev) != (143, 153, 160, 165):
        raise SystemExit('anchors moved: %r' % ((i_tt + 1, e_tt + 1, i_dev + 1, e_dev + 1),))
    if not (lines[e_tt + 1] == '' and lines[e_dev + 1] == '' and lines[e_dev + 2] == 'if(WIN32)'):
        raise SystemExit('unexpected text around the anchors')
    if any('gpu_wait_backoff' in s or 'SCENE_WALK' in s for s in lines):
        raise SystemExit('base already mentions gpu_wait_backoff or SCENE_WALK')
    return e_tt + 2, e_dev + 2


def apply_inserts(lines, inserts):
    out, prev = [], 0
    for k, block in inserts:
        out += lines[prev:k] + block
        prev = k
    return out + lines[prev:]


def insert_diff(a, inserts, name, ctx=3):
    """Unified diff of pure insertions; a = base lines with EOL, inserts = [(k, block lines with EOL)], sorted."""
    out = ['--- a/%s\n' % name, '+++ b/%s\n' % name]
    added, last_end = 0, 0
    for k, block in inserts:
        s, e = max(0, k - ctx), min(len(a), k + ctx)
        if s < last_end:
            raise SystemExit('hunks overlap')
        out.append('@@ -%d,%d +%d,%d @@\n' % (s + 1, e - s, s + 1 + added, e - s + len(block)))
        out += [' ' + l for l in a[s:k]] + ['+' + l for l in block] + [' ' + l for l in a[k:e]]
        added, last_end = added + len(block), e
    return out


def keep(t):
    parts = t.split('\n')
    res = [x + '\n' for x in parts[:-1]]
    if parts[-1]:
        res.append(parts[-1])
    return res


def stage():
    base = rd(LIVE_CML)
    if sha(base) != BASE_SHA:
        raise SystemExit('live CMakeLists.txt is %s, not the recorded base %s' % (sha(base), BASE_SHA))
    tu = rd(DRAFT)
    if sha(tu) != DRAFT_SHA:
        raise SystemExit('draft is %s, not the rated %s' % (sha(tu), DRAFT_SHA))
    if b'\r' in tu or not tu.endswith(b'\n'):
        raise SystemExit('draft is not LF-only with a final LF')
    lines = crlf_lines(base)
    print('base  %s  %s  %d B  %d lines  %s' % (rel(LIVE_CML), sha(base)[:16], len(base), len(lines), eol(base)))
    for tag, p in OTHER_CML:
        b = rd(p)
        print('      %-17s %s  %s' % (tag, sha(b)[:16], 'same as live' if b == base else 'DIFFERENT'))
    wr(H('base', 'rexlego', 'CMakeLists.txt'), base)
    wr(H('new', 'rexlego', 'src', 'gpu_wait_backoff.cpp'), tu)
    tu_lines = keep(tu.decode('latin-1'))
    k30, k24 = plan(lines)
    for diff_name, new_dir, with30 in VARIANTS:
        inserts = ([(k30, BLOCK30)] if with30 else []) + [(k24, BLOCK24)]
        new_lines = apply_inserts(lines, inserts)
        nb = ('\r\n'.join(new_lines) + '\r\n').encode('latin-1')
        wr(H(new_dir, 'rexlego', 'CMakeLists.txt'), nb)
        parts = ['diff --git a/%s b/%s\n' % (CML, CML)]
        parts += insert_diff([l + '\r\n' for l in lines], [(k, [l + '\r\n' for l in b]) for k, b in inserts], CML)
        parts += ['diff --git a/%s b/%s\n' % (TU, TU), 'new file mode 100644\n', '--- /dev/null\n', '+++ b/%s\n' % TU,
                  '@@ -0,0 +1,%d @@\n' % len(tu_lines)] + ['+' + l for l in tu_lines]
        d = ''.join(parts).encode('latin-1')
        wr(H(diff_name), d)
        adds = sum(1 for l in d.split(b'\n') if l.startswith(b'+') and not l.startswith(b'+++'))
        dels = sum(1 for l in d.split(b'\n') if l.startswith(b'-') and not l.startswith(b'---'))
        print('%-17s %s  %d B  +%d -%d lines (CMake +%d at base :%s); %s/%s %s  %d B  %d lines  %s' % (
            diff_name, sha(d)[:16], len(d), adds, dels, sum(len(b) for _, b in inserts),
            '+'.join(str(k) for k, _ in inserts), new_dir, CML, sha(nb)[:16], len(nb), len(new_lines), eol(nb)))
    print('new TU %s  %s  %d B  %s (= draft)' % (TU, sha(tu)[:16], len(tu), eol(tu)))


def run(cmd, cwd, env):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def tree(d):
    out = {}
    for root, dirs, files in os.walk(d):
        for f in files:
            full = os.path.join(root, f)
            out[os.path.relpath(full, d).replace('\\', '/')] = sha(rd(full))
    return out


def verify():
    out, bad = [], 0

    def say(s):
        out.append(s)
        print(s)

    say('# apply check (S4c #24 package; Agent 9, task #22)  ' + time.strftime('%Y-%m-%d %H:%M:%S'))
    scratch = H('scratch')
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)
    env = dict(os.environ)
    env['GIT_CEILING_DIRECTORIES'] = scratch
    base = rd(H('base', 'rexlego', 'CMakeLists.txt'))
    tu = rd(H('new', 'rexlego', 'src', 'gpu_wait_backoff.cpp'))
    say('base %s %s (live %s); new TU %s (draft %s)' % (CML, sha(base)[:16], sha(rd(LIVE_CML))[:16], sha(tu)[:16],
                                                       DRAFT_SHA[:16]))
    if sha(base) != BASE_SHA or sha(tu) != DRAFT_SHA:
        bad += 1
        say('  BASE OR TU HASH MISMATCH')
    _, gv = run(['git', '--version'], scratch, env)
    _, pv = run([PATCH_EXE, '--version'], scratch, env)
    say('tools: %s; %s' % (gv, pv.splitlines()[0] if pv else '?'))
    for diff_name, new_dir, with30 in VARIANTS:
        dpath = H(diff_name)
        want = {CML: sha(rd(H(new_dir, 'rexlego', 'CMakeLists.txt'))), TU: sha(tu)}
        say('--- %s  %s  (expect %s %s, %s %s)' % (diff_name, sha(rd(dpath))[:16], CML, want[CML][:16], TU,
                                                  want[TU][:16]))
        for tool in ('git', 'patch'):
            d = os.path.join(scratch, diff_name[:-5] + '-' + tool)
            wr(os.path.join(d, 'rexlego', 'CMakeLists.txt'), base)
            rc, msg = run(['git', 'rev-parse', '--is-inside-work-tree'], d, env)
            if rc == 0:
                bad += 1
                say('  %s: scratch dir is inside a git work tree (%s); skipped' % (tool, msg))
                continue
            dr = os.path.relpath(dpath, d).replace('\\', '/')
            if tool == 'git':
                steps = [('apply --check -v', ['git', '-c', 'core.autocrlf=false', 'apply', '--check', '-v', '-p1', dr]),
                         ('apply', ['git', '-c', 'core.autocrlf=false', 'apply', '-p1', dr])]
            else:
                steps = [('--dry-run', [PATCH_EXE, '--binary', '-p1', '--dry-run', '-i', dr]),
                         ('apply', [PATCH_EXE, '--binary', '-p1', '--no-backup-if-mismatch', '-i', dr])]
            for label, cmd in steps:
                rc, msg = run(cmd, d, env)
                if rc != 0:
                    bad += 1
                say('  %-5s %-17s exit %d  %s' % (tool, label, rc, ' | '.join(msg.splitlines()) if msg else ''))
            got = tree(d)
            ok = got == want
            if not ok:
                bad += 1
            say('  %-5s result: %s' % (tool, 'both files == %s/ (sha256), no stray files' % new_dir if ok else
                                       'MISMATCH %r' % {k: v[:16] for k, v in got.items()}))
            if tool == 'git':
                rc, msg = run(['git', '-c', 'core.autocrlf=false', 'apply', '-R', '--check', '-p1', dr], d, env)
                if rc != 0:
                    bad += 1
                say('  git   apply -R --check   exit %d  %s' % (rc, ' | '.join(msg.splitlines()) if msg else
                                                           '(reverses cleanly to base)'))
        # EOL discipline inside the diff: CMakeLists.txt hunk lines CRLF, new-file lines LF
        raw = rd(dpath)
        cut = raw.index(b'diff --git a/' + TU.encode())
        cm = [l for l in raw[:cut].split(b'\n')[:-1] if l[:1] in (b' ', b'+', b'-') and not l.startswith((b'+++', b'---'))]
        tl = [l for l in raw[cut:].split(b'\n')[:-1] if l.startswith(b'+') and not l.startswith(b'+++')]
        e_ok = all(l.endswith(b'\r') for l in cm) and not any(l.endswith(b'\r') for l in tl)
        if not e_ok:
            bad += 1
        say('  EOL in the diff: %d CMakeLists.txt hunk lines all CRLF, %d new-file lines all LF: %s' % (
            len(cm), len(tl), 'yes' if e_ok else 'NO'))
    for tag, p in OTHER_CML:
        same = rd(p) == base
        say('%s CMakeLists.txt == base: %s (so both diffs apply there the same way)' % (tag, same))
    say('RESULT: %s' % ('PASS' if not bad else 'FAIL (%d)' % bad))
    with open(H('apply-check.txt'), 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    shutil.rmtree(scratch)
    return 1 if bad else 0


def hashes():
    rows = ['# HASHES (S4c package for #24 + #30\'s CMake option; Agent 9, task #22)  ' + time.strftime(
        '%Y-%m-%d %H:%M:%S'),
            '# sha256  bytes  EOL  path (relative to the workspace root)',
            '## inputs']
    for p in [LIVE_CML] + [q for _, q in OTHER_CML] + [DRAFT]:
        b = rd(p)
        rows.append('%s  %7d  %-15s  %s' % (sha(b), len(b), eol(b), rel(p)))
    rows.append('## package')
    for root, dirs, files in os.walk(HERE):
        dirs[:] = sorted(x for x in dirs if x not in ('scratch', 'syntax', '__pycache__'))
        for f in sorted(files):
            if f == 'HASHES.txt':
                continue
            full = os.path.join(root, f)
            b = rd(full)
            rows.append('%s  %7d  %-15s  %s' % (sha(b), len(b), eol(b), rel(full)))
    tu = rd(H('new', 'rexlego', 'src', 'gpu_wait_backoff.cpp'))
    tc = tu.replace(b'\n', b'\r\n')
    rows.append('## info')
    rows.append('%s  %7d  %-15s  %s' % (sha(tc), len(tc), eol(tc),
                                         'gpu_wait_backoff.cpp in CRLF form (what git apply or a checkout writes '
                                         'inside the live repo: core.autocrlf=true, * text=auto); same text'))
    with open(H('HASHES.txt'), 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(rows) + '\n')
    print('\n'.join(rows))


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    rc = 0
    if what in ('stage', 'all'):
        stage()
    if what in ('verify', 'all'):
        rc = verify()
    if what in ('hashes', 'all'):
        hashes()
    sys.exit(rc)
