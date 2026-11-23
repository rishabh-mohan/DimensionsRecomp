"""Agent 2 - S4b inputs (board run 2, task #1 = old #28, Agent 1). S4b = snap1 at S4a (STATE-S4a-1325.tsv, the trees
behind devoff4-bin and native4-bin) + 16 files:
  rexglue-sdk, 13 files from 5 staged diffs, git-applied in this order to copies of the S4a snap1 files (order o1 of
    s4b-compose-check.py): C1 v2|v3 (Agent 12, 5 files) -> M1 (Agent 5) -> P2c (Agent 12) -> r1r2 (#18/#20, Agent 7;
    command_processor.cpp chained after P2c, final = Agent 10's composite 027204B5...) -> #26 tool (Agent 9,
    db16cyc_pause, default OFF; codegen files only, the game builds keep the pinned S1 generated output);
  rexlego/src/gpu_native/memory_watch.cpp (C1's game file; native builds only; CRLF): the staged after-file is copied
    (Agent 10's landing rule: the LF diff does not apply to the CRLF file), and it is proven equal to
    keep-watch-rexlego.diff applied to the LF form of the S4a file, converted back to CRLF;
  S4c, the last step (Agent 9, s4c-24-30.diff: rexlego/CMakeLists.txt + the new rexlego/src/gpu_wait_backoff.cpp; #24
    hooks for OFF builds only + #30's CMake option, both OFF; fallback --s4c 24-only).
The hash records are s4b-compose-check.py's (loaded from it, one place). Nothing is copied from live and live is never
written. git runs in a scratch tree build/agent2/s4b/work-HHMMSS with GIT_CEILING_DIRECTORIES=<repo root> and
core.autocrlf=false.
  python build\\agent2\\prep-s4b.py --c1 v3 --dry-run   all checks + the scratch results; nothing written outside s4b/work-*
  python build\\agent2\\prep-s4b.py --c1 v3             the same, then backups (build/agent2/snap1-backup-S4b), the 16 snap1
                                                       copies (mtime = now), snap1/PATCHES-S4b.tsv, snap1/STATE-S4b-HHMM.tsv,
                                                       build/agent2/S4b-notes.txt + S4b-strings.tsv, s4b/HASHES.txt, then
                                                       snap-patch.py verify S4b
--c1 defaults to env S4B_C1; with neither, nothing is done. Any FAIL before the apply and nothing is written to snap1.
"""
import argparse
import bisect
import glob
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snap as S  # noqa: E402  (R, SNAP_ROOT)

R = S.R
A = os.path.join(R, 'build', 'agent2')
OUT = os.path.join(A, 's4b')
TAG = 'S4b'
BASE = 'STATE-S4a-1325.tsv'
NOTES = os.path.join(A, 'S4b-notes.txt')
STRINGS = os.path.join(A, 'S4b-strings.tsv')
BACKUP = os.path.join(A, 'snap1-backup-%s' % TAG, 'DimensionsRecomp')
MW_AFTER_FILE = 'build/agent12/s4-c1/new/game/rexlego/src/gpu_native/memory_watch.cpp'
MW_AFTER_PREFIX = '70829846C4F321A9'


def load_compose_check():
    # the staging records live in one place, s4b-compose-check.py (STEPS, C1_VARIANTS, S4C, ...); its main() is not run
    spec = importlib.util.spec_from_file_location('s4b_compose_check', os.path.join(A, 's4b-compose-check.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CC = load_compose_check()
OWNER = {'c1v2': 'A12', 'c1v3': 'A12', 'm1': 'A5', 'p2c': 'A12', 'r1r2': 'A7', 'n26': 'A9'}
WHAT = {'c1v2': 'C1 v2 keep-watch (#4)', 'c1v3': 'C1 v3 keep-watch (#4)', 'm1': 'M1 non-temporal upload copy',
        'p2c': 'P2 counter (memexport full-buffer counter)', 'r1r2': '#18/#20 r1r2',
        'n26': '#26 db16cyc_pause codegen option'}
CVAR_RE = re.compile(r'REXCVAR_DEFINE_(\w+)\(\s*(\w+)\s*,\s*("(?:[^"\\]|\\.)*"|[^,]+?)\s*,')
ENV_RE = re.compile(r'"(LEGO_[A-Z0-9_]+)"')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def snapf(rel):
    return os.path.join(S.SNAP_ROOT, 'DimensionsRecomp', *rel.split('/'))


def livef(rel):
    return os.path.join(R, 'DimensionsRecomp', *rel.split('/'))


def rr(p):
    return os.path.relpath(p, R).replace('\\', '/')


ENV = dict(os.environ)
for _k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CEILING_DIRECTORIES'):
    ENV.pop(_k, None)
ENV['GIT_CEILING_DIRECTORIES'] = R.replace('\\', '/')


def git(args, cwd):
    p = subprocess.run(['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false'] + args, cwd=cwd, env=ENV,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def diff_pairs(data):
    # (old, new) path pairs of a unified diff: a '--- ' line directly followed by a '+++ ' line
    lines = [ln.rstrip(b'\r') for ln in data.split(b'\n')]
    out = []
    for i in range(len(lines) - 1):
        if lines[i].startswith(b'--- ') and lines[i + 1].startswith(b'+++ '):
            out.append((lines[i][4:].split(b'\t')[0].decode(), lines[i + 1][4:].split(b'\t')[0].decode()))
    return out


def target(rel):
    if rel.startswith('rexglue-sdk/src/graphics/'):
        return 'rexgpu-xenos.dll'
    if rel.startswith(('rexglue-sdk/src/system/', 'rexglue-sdk/src/core/')):
        return 'rexruntime.dll'
    if rel.startswith('rexglue-sdk/src/codegen/'):
        return 'codegen tool'
    if rel.startswith('rexglue-sdk/include/'):
        return 'header'
    if rel.startswith('rexlego/src/gpu_native/'):
        return 'native exe'
    if rel == CC.TU:
        return 'OFF exe'
    return 'build script'


def cvars(text):
    return {m.group(2): (m.group(1), m.group(3).strip()) for m in CVAR_RE.finditer(text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--c1', choices=['v2', 'v3'], default=None, help='C1 variant; default: env S4B_C1, else refuse')
    ap.add_argument('--s4c', choices=['24-30', '24-only'], default='24-30', help='S4c diff; default 24-30')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    c1 = a.c1 or os.environ.get('S4B_C1', '').strip().lower()
    if c1 not in ('v2', 'v3'):
        print('REFUSED: give --c1 v2|v3 or set S4B_C1 (Agent 1 sets the C1 variant at build time); nothing done')
        sys.exit(2)
    c1src = '--c1' if a.c1 else 'env S4B_C1'
    t0 = time.time()
    res = []

    def check(ok, text):
        res.append((bool(ok), text))
        print('%s %s' % ('PASS' if ok else 'FAIL', text), flush=True)
        return bool(ok)

    def note(text):
        print('NOTE %s' % text, flush=True)

    def stop_if_failed(where):
        n = sum(1 for ok, _ in res if not ok)
        if n:
            print('REFUSED (%s): %d of %d check(s) failed; nothing was written to snap1' % (where, n, len(res)))
            sys.exit(1)

    print('prep-s4b.py %s, %s: C1 %s (%s), S4c %s' % ('--dry-run' if a.dry_run else 'APPLY',
                                                      time.strftime('%Y-%m-%d %H:%M:%S'), c1, c1src, a.s4c))
    # ---- base: snap1 is at S4a
    states = sorted([p for p in glob.glob(os.path.join(S.SNAP_ROOT, 'STATE-*.tsv'))
                     if 'reverted' not in os.path.basename(p)], key=os.path.getmtime)
    newest = os.path.basename(states[-1]) if states else 'none'
    check(newest == BASE, 'the newest STATE record in snap1 is %s (%s)' % (BASE, newest))
    done = sorted(os.path.basename(p) for p in glob.glob(os.path.join(S.SNAP_ROOT, 'PATCHES-%s*' % TAG))
                  + glob.glob(os.path.join(S.SNAP_ROOT, 'STATE-%s-*' % TAG)))
    check(not done, 'no %s record in snap1 yet%s' % (TAG, ' (found %s)' % ', '.join(done) if done else ''))
    check(not os.path.exists(os.path.dirname(BACKUP)), 'no %s yet' % rr(os.path.dirname(BACKUP)))
    if not a.dry_run:
        for p in (NOTES, STRINGS):
            check(not os.path.exists(p), 'no %s yet' % rr(p))
    base_rows, order = {}, []
    with open(os.path.join(S.SNAP_ROOT, BASE), encoding='utf-8-sig') as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip():
                continue
            c = ln.rstrip('\r\n').split('\t')
            base_rows[c[0]] = c
            order.append(c[0])
    vp = subprocess.run([sys.executable, os.path.join(A, 'snap-patch.py'), 'verify', 'S4a'], capture_output=True,
                        text=True)
    vout = (vp.stdout + vp.stderr).strip().splitlines()
    check(vp.returncode == 0 and 'RESULT: PASS' in [x.strip() for x in vout],
          'snap-patch.py verify S4a (all of snap1 == %s): %s' % (BASE, vout[0] if vout else 'no output'))
    for x in vout[1:]:
        if x.strip().startswith('BAD'):
            print('   ' + x.strip())

    # ---- scratch tree, no git repository discoverable from it
    stamp = time.strftime('%H%M%S')
    work = os.path.join(OUT, 'work-' + stamp)
    wd = os.path.join(work, 'DimensionsRecomp')
    wsdk = os.path.join(wd, 'rexglue-sdk')
    os.makedirs(wsdk)
    rc, out = git(['rev-parse', '--git-dir'], wsdk)
    check(rc != 0, 'no git repository is discovered from %s (GIT_CEILING_DIRECTORIES=%s; rev-parse: %s)'
          % (rr(wsdk), ENV['GIT_CEILING_DIRECTORIES'], (out.splitlines() or ['?'])[0][:90]))
    stop_if_failed('base')

    # ---- rexglue-sdk: C1 -> M1 -> P2c -> r1r2 -> #26
    seq = ['c1' + c1, 'm1', 'p2c', 'r1r2', 'n26']
    files, first_before, steps_of = [], {}, {}
    for k in seq:
        for f, (b, _) in CC.STEPS[k][3].items():
            if f not in first_before:
                files.append(f)
                first_before[f] = b.lower()
            steps_of.setdefault(f, []).append(k)
    befores, sizes, diffs, wpath = {}, {}, {}, {}
    for f in files:
        rel = 'rexglue-sdk/' + f
        sp = snapf(rel)
        hs = sha(sp)
        row = base_rows.get(rel)
        check(row is not None and row[6].lower() == hs == first_before[f],
              'base %s: snap1 %s == the %s row (%s) == the first staged before (%s)'
              % (rel, hs[:16].upper(), BASE, row[6][:16].upper() if row else 'none', first_before[f][:16].upper()))
        hl = sha(livef(rel))
        note('%s: live %s %s snap1 (live is not read for S4b and not written)'
             % (rel, hl[:16].upper(), '==' if hl == hs else '!='))
        wf = os.path.join(wsdk, *f.split('/'))
        os.makedirs(os.path.dirname(wf), exist_ok=True)
        shutil.copyfile(sp, wf)
        befores[rel], sizes[rel], wpath[rel] = hs, os.path.getsize(sp), wf
    stop_if_failed('S4b SDK bases')
    cur = dict(first_before)
    for k in seq:
        name, drel, dsha, fmap = CC.STEPS[k]
        dp = os.path.join(R, drel)
        hd = sha(dp)
        diffs[k] = (drel.replace('\\', '/'), hd)
        check(hd == dsha.lower(), '%s: diff %s sha256 %s == the staging record' % (name, diffs[k][0], hd[:16].upper()))
        pairs = diff_pairs(open(dp, 'rb').read())
        news = sorted(p[1] for p in pairs)
        olds_ok = all(p[0] in ('a/' + p[1][2:], '/dev/null') for p in pairs)
        check(news == sorted('b/' + f for f in fmap) and olds_ok, '%s: the diff patches exactly its %d recorded file(s): %s'
              % (name, len(fmap), ', '.join(p[1][2:] for p in pairs)))
        for f, (b, _) in fmap.items():
            h = sha(os.path.join(wsdk, *f.split('/')))
            chained = cur[f] != b.lower()
            check(h == cur[f], '%s: %s before %s == %s' % (name, f, h[:16].upper(), 'the staging record' if not chained
                  else 'the previous step result (chained; the lone-apply record is %s)' % b[:16].upper()))
        rc, out = git(['apply', '--check', '--whitespace=nowarn', dp], wsdk)
        if check(rc == 0, '%s: git apply --check in the scratch rexglue-sdk%s' % (name, (': ' + out.replace('\n', ' | ')) if rc else '')):
            rc, out = git(['apply', '--verbose', '--whitespace=nowarn', dp], wsdk)
            offs = [x.strip() for x in out.splitlines() if 'offset' in x.lower() or 'fuzz' in x.lower()]
            check(rc == 0, '%s: git apply exit %d%s' % (name, rc, ('; ' + '; '.join(offs)) if offs else ', no offsets'))
        for f, (b, aft) in fmap.items():
            h = sha(os.path.join(wsdk, *f.split('/')))
            if cur[f] == b.lower():
                check(h == aft.lower(), '%s: %s after %s == the staging record' % (name, f, h[:16].upper()))
            else:
                note('%s: %s after %s (chained; the lone-apply record is %s)' % (name, f, h[:16].upper(), aft[:16].upper()))
            cur[f] = h
    check(cur[CC.CP].upper().startswith(CC.AGENT10_CP_COMPOSITE), '%s final %s starts with Agent 10\'s P2c + r1r2 '
          'composite %s' % (CC.CP, cur[CC.CP][:16].upper(), CC.AGENT10_CP_COMPOSITE))
    check(cur[CC.XM] == CC.C1_VARIANTS[c1][2].lower(), '%s final %s == the C1 %s after' % (CC.XM, cur[CC.XM][:16].upper(), c1))
    cdir = os.path.join(A, 's4b-check', 'o1-' + c1)
    same = [f for f in files if os.path.isfile(os.path.join(cdir, *f.split('/')))
            and sha(os.path.join(cdir, *f.split('/'))) == cur[f]]
    check(len(same) == len(files), 'all %d SDK results == s4b-compose-check.py\'s %s results (%d equal)'
          % (len(files), rr(cdir), len(same)))
    stop_if_failed('SDK steps')

    # ---- rexlego/src/gpu_native/memory_watch.cpp (C1's game file, CRLF): the staged after-file, proven
    mw = CC.MW_REL
    sp = snapf(mw)
    hs = sha(sp)
    row = base_rows.get(mw)
    check(row is not None and row[6].lower() == hs == CC.MW_LIVE.lower(), 'base %s: snap1 %s == the %s row == %s'
          % (mw, hs[:16].upper(), BASE, CC.MW_LIVE[:16]))
    base = open(sp, 'rb').read()
    ncr = base.count(b'\r\n')
    nlf = base.count(b'\n') - ncr
    af = os.path.join(R, *MW_AFTER_FILE.split('/'))
    after = open(af, 'rb').read()
    ha = hashlib.sha256(after).hexdigest()
    check(ha.upper().startswith(MW_AFTER_PREFIX), 'staged after-file %s: %s (%d B) starts with %s (Agent 10)'
          % (MW_AFTER_FILE, ha[:16].upper(), len(after), MW_AFTER_PREFIX))
    dp = os.path.join(R, CC.MW_DIFF)
    hd = sha(dp)
    diffs['mw'] = (CC.MW_DIFF.replace('\\', '/'), hd)
    check(hd == CC.MW_DIFF_SHA.lower(), 'C1 rexlego diff %s sha256 %s == the staging record' % (diffs['mw'][0], hd[:16].upper()))
    pairs = diff_pairs(open(dp, 'rb').read())
    check(pairs == [('a/' + mw, 'b/' + mw)], 'C1 rexlego diff patches exactly %s (%s)' % (mw, pairs))
    pd = os.path.join(work, 'mw-lf', 'DimensionsRecomp')
    pf = os.path.join(pd, *mw.split('/'))
    os.makedirs(os.path.dirname(pf))
    with open(pf, 'wb') as f:
        f.write(base.replace(b'\r\n', b'\n'))
    rc, out = git(['apply', '--whitespace=nowarn', dp], pd)
    proof = rc == 0 and open(pf, 'rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') == after
    acr = after.count(b'\r\n')
    check(nlf == 0 and proof, 'proof: keep-watch-rexlego.diff applied to the LF form of the S4a file (%d CRLF, %d bare LF), '
          'converted back to CRLF, == the staged after-file (%d CRLF, %d bare LF)%s'
          % (ncr, nlf, acr, after.count(b'\n') - acr, (' (git apply: %s)' % out.replace('\n', ' | ')) if rc else ''))
    wf = os.path.join(wd, *mw.split('/'))
    os.makedirs(os.path.dirname(wf), exist_ok=True)
    shutil.copyfile(af, wf)
    befores[mw], sizes[mw], wpath[mw] = hs, len(base), wf

    # ---- S4c, the last step: rexlego/CMakeLists.txt + the new rexlego/src/gpu_wait_backoff.cpp
    s4rel, s4sha, cml_after, newdir = CC.S4C[a.s4c]
    cml, tu = CC.CML, CC.TU
    dp = os.path.join(R, s4rel)
    hd = sha(dp)
    diffs['s4c'] = (s4rel.replace('\\', '/'), hd)
    check(hd == s4sha.lower(), 'S4c %s: diff %s sha256 %s == Agent 9\'s record' % (a.s4c, diffs['s4c'][0], hd[:16].upper()))
    pairs = diff_pairs(open(dp, 'rb').read())
    check(sorted(pairs) == sorted([('a/' + cml, 'b/' + cml), ('/dev/null', 'b/' + tu)]),
          'S4c diff patches %s and adds %s (%s)' % (cml, tu, pairs))
    sp = snapf(cml)
    hs = sha(sp)
    row = base_rows.get(cml)
    check(row is not None and row[6].lower() == hs == CC.CML_BEFORE.lower(), 'base %s: snap1 %s == the %s row == %s'
          % (cml, hs[:16].upper(), BASE, CC.CML_BEFORE[:16]))
    trow = base_rows.get(tu)
    check(not os.path.exists(snapf(tu)) and (trow is None or trow[6] == '-'),
          'the new %s is not in snap1 and has no %s row (%s)' % (tu, BASE, 'none' if trow is None else trow[6][:16]))
    note('%s in live: %s (live is not read for S4b)' % (tu, 'present' if os.path.exists(livef(tu)) else 'absent'))
    wf = os.path.join(wd, *cml.split('/'))
    os.makedirs(os.path.dirname(wf), exist_ok=True)
    shutil.copyfile(sp, wf)
    befores[cml], sizes[cml], wpath[cml] = hs, os.path.getsize(sp), wf
    rc, out = git(['apply', '--check', '--whitespace=nowarn', dp], wd)
    if check(rc == 0, 'S4c: git apply --check in the scratch DimensionsRecomp%s' % ((': ' + out.replace('\n', ' | ')) if rc else '')):
        rc, out = git(['apply', '--verbose', '--whitespace=nowarn', dp], wd)
        offs = [x.strip() for x in out.splitlines() if 'offset' in x.lower() or 'fuzz' in x.lower()]
        check(rc == 0, 'S4c: git apply exit %d%s' % (rc, ('; ' + '; '.join(offs)) if offs else ', no offsets'))
    hc = sha(wf)
    hn = sha(os.path.join(R, newdir, 'rexlego', 'CMakeLists.txt'))
    data = open(wf, 'rb').read()
    check(hc == cml_after.lower() == hn, 'S4c: %s after %s (%d B, %d CRLF) == Agent 9\'s record == Agent 9\'s new/ copy (%s)'
          % (cml, hc[:16].upper(), len(data), data.count(b'\r\n'), hn[:16].upper()))
    text = data.decode('utf-8', 'replace')
    if a.s4c == '24-30':
        hit = [x.strip() for x in text.splitlines() if 'option(LEGODIMENSIONS_SCENE_WALK_PROBE' in x]
        check(len(hit) == 1 and hit[0].rstrip(')').rstrip().endswith('OFF'), 'S4c #30 option, default OFF: %s' % ' | '.join(hit))
    blk = [x.strip() for x in text.splitlines() if 'gpu_wait_backoff.cpp' in x or 'LEGO_GPU_WAIT_HOOK_GETDATA' in x
           or x.strip().startswith('if(NOT LEGODIMENSIONS_NATIVE_GPU)')]
    check(any('if(NOT LEGODIMENSIONS_NATIVE_GPU)' in x for x in blk) and any('LEGO_GPU_WAIT_HOOK_GETDATA=1' in x for x in blk),
          'S4c #24 block (OFF builds only, GETDATA hooks on): %s' % ' | '.join(blk)[:300])
    tf = os.path.join(wd, *tu.split('/'))
    ht = sha(tf) if os.path.isfile(tf) else 'absent'
    ok = ht.upper() in (CC.TU_LF, CC.TU_CRLF)
    if a.s4c == '24-30':
        hn2 = sha(os.path.join(R, newdir, 'rexlego', 'src', 'gpu_wait_backoff.cpp'))
        ok = ok and hn2 == ht
    check(ok, 'S4c: %s %s (%s)%s' % (tu, ht[:16].upper(), 'LF form 01D9F8F3' if ht.upper() == CC.TU_LF else (
        'CRLF form 34D281E0' if ht.upper() == CC.TU_CRLF else 'want 01D9F8F3 or 34D281E0'),
        ' == Agent 9\'s new/ TU' if a.s4c == '24-30' else ''))
    tt = open(tf, encoding='utf-8', errors='replace').read() if os.path.isfile(tf) else ''
    check('std::getenv("LEGO_GPU_WAIT_BACKOFF_US")' in tt and 'unset or empty = OFF' in tt,
          'S4c #24 back-off is OFF unless LEGO_GPU_WAIT_BACKOFF_US is set (the TU says: unset or empty = OFF)')
    wpath[tu] = tf
    sizes[tu] = 0
    stop_if_failed('memory_watch.cpp / S4c')

    # ---- new switches and strings (cvars and LEGO_* environment names new against S4a)
    rels = ['rexglue-sdk/' + f for f in files] + [mw, cml, tu]
    srows, cvrows = [], []
    for rel in rels:
        new_t = open(wpath[rel], encoding='utf-8', errors='replace').read()
        old_t = open(snapf(rel), encoding='utf-8', errors='replace').read() if os.path.exists(snapf(rel)) else ''
        nc, oc = cvars(new_t), cvars(old_t)
        for n in nc:
            if n not in oc:
                typ, dflt = nc[n]
                srows.append((n, 'cvar %s, default %s' % (typ, dflt), rel, target(rel), len(n)))
                cvrows.append((n, typ, dflt, rel))
                okd = dflt == 'false' if typ == 'BOOL' else dflt in ('0', '0u', '""')
                check(okd, 'new cvar %s (%s, %s) in %s: default %s (OFF)' % (n, typ, target(rel), rel, dflt))
        for n in sorted(set(ENV_RE.findall(new_t)) - set(ENV_RE.findall(old_t))):
            srows.append((n, 'env', rel, target(rel), len(n)))
            note('new environment name %s in %s (%s)' % (n, rel, target(rel)))
    dcl = open(wpath['rexglue-sdk/src/graphics/d3d12/deferred_command_list.cpp'], encoding='utf-8', errors='replace').read()
    check('#ifndef REX_D3D12_DEFERRED_COUNTERS' in dcl and '#define REX_D3D12_DEFERRED_COUNTERS 0' in dcl,
          'r1r2: deferred_command_list.cpp compiles its counters out by default (REX_D3D12_DEFERRED_COUNTERS 0)')
    cfgh = open(wpath['rexglue-sdk/include/rex/codegen/config.h'], encoding='utf-8', errors='replace').read()
    cfgc = open(wpath['rexglue-sdk/src/codegen/config.cpp'], encoding='utf-8', errors='replace').read()
    hits = [x.strip() for x in cfgh.splitlines() if 'db16cycPause' in x]
    hitc = [x.strip() for x in cfgc.splitlines() if 'db16cyc_pause' in x]
    check(len(hits) == 1 and 'bool db16cycPause = false;' in hits[0] and any('value_or(false)' in x for x in hitc),
          '#26: config.h %s; config.cpp reads toml key db16cyc_pause with value_or(false) (default OFF)' % ' | '.join(hits)[:120])
    toml = 'rexlego/legodimensions_config.toml'
    hto = sha(snapf(toml))
    row = base_rows.get(toml)
    tot = open(snapf(toml), encoding='utf-8', errors='replace').read()
    check(hto.upper().startswith('7F775847') and row is not None and row[6].lower() == hto and 'db16cyc_pause' not in tot,
          '#26 stays OFF in the game builds: snap1 %s %s == the %s row, starts with 7F775847 (Agent 10 gate 1), no '
          'db16cyc_pause line; S4b does not touch it' % (toml, hto[:16].upper(), BASE))
    stop_if_failed('switches')

    # ---- records (scratch first)
    now_s = time.strftime('%Y-%m-%d %H:%M:%S')
    after_h, after_n = {}, {}
    for rel in rels:
        after_h[rel] = sha(wpath[rel])
        after_n[rel] = os.path.getsize(wpath[rel])

    def owner_item(rel):
        if rel.startswith('rexglue-sdk/'):
            ks = steps_of[rel[len('rexglue-sdk/'):]]
            own = '+'.join(dict.fromkeys(OWNER[k] for k in ks))
            return own, ' + '.join(WHAT[k] for k in ks), ' -> '.join('%s (%s)' % (diffs[k][0], diffs[k][1][:16].upper()) for k in ks)
        if rel == mw:
            return 'A12', 'C1 %s keep-watch, rexlego file (native builds only)' % c1, (
                'copy of the staged after-file %s (== %s (%s) applied to the LF form, CRLF kept)'
                % (MW_AFTER_FILE, diffs['mw'][0], diffs['mw'][1][:16].upper()))
        return 'A9', 'S4c %s (#24 GPU wait back-off, OFF builds only%s)' % (a.s4c, '; #30 option' if a.s4c == '24-30' else ''), (
            '%s (%s)' % (diffs['s4c'][0], diffs['s4c'][1][:16].upper()))

    def switch(rel):
        cv = ['%s (%s, default %s)' % (n, t, d) for n, t, d, r in cvrows if r == rel]
        if cv:
            return 'cvar ' + ', '.join(cv)
        if rel == tu:
            return 'env LEGO_GPU_WAIT_BACKOFF_US unset = OFF'
        if rel == cml:
            return 'LEGODIMENSIONS_SCENE_WALK_PROBE default OFF' if a.s4c == '24-30' else 'no option'
        if rel.endswith('deferred_command_list.cpp'):
            return 'REX_D3D12_DEFERRED_COUNTERS 0'
        if '/codegen/' in rel:
            return 'codegen option db16cyc_pause, default OFF'
        return 'no switch of its own'

    hashes = ['# S4b inputs, written %s by build/agent2/prep-s4b.py: base snap1 at S4a (%s); C1 %s (%s); S4c %s. Per file: '
              'owner, relpath under DimensionsRecomp/, before sha256 (size), after sha256 (size), item, source, switch'
              % (now_s, BASE, c1, c1src, a.s4c)]
    for rel in rels:
        own, item, src = owner_item(rel)
        hashes.append('\t'.join([own, rel, ('%s (%d B)' % (befores[rel].upper(), sizes[rel])) if rel in befores else 'ABSENT',
                                 '%s (%d B)' % (after_h[rel].upper(), after_n[rel]), item, src, switch(rel)]))
    with open(os.path.join(work, 'HASHES.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(hashes) + '\n')
    with open(os.path.join(work, 'S4b-strings.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# new strings of S4b (prep-s4b.py %s): name, kind, relpath, target binary, length (the stage checks use '
                'the ones of 16+ chars in the game binaries)\n' % now_s)
        for r_ in srows:
            f.write('\t'.join(str(x) for x in r_) + '\n')
    cvtext = '; '.join('%s (%s, %s, default %s)' % (n, target(r), t, d) for n, t, d, r in cvrows)
    note_lines = [
        'S4b build inputs (board run 2, task #1 = old #28): snap1 at S4a (%s; the trees behind devoff4-bin and native4-bin) '
        '+ %d files. rexglue-sdk: %d files, made by git apply of the staged diffs in the order C1 %s -> M1 -> P2c -> r1r2 -> '
        '#26 to the S4a snap1 copies, each step hash-checked against its staging record (command_processor.cpp: P2c then '
        'r1r2, final %s = Agent 10 composite); nothing was copied from live and live was not written.'
        % (BASE, len(rels), len(files), c1, cur[CC.CP][:16].upper()),
        'C1 = %s (Agent 12, %s sha256 %s; %s): include/rex/graphics/shared_memory.h, include/rex/system/xmemory.h (PCH '
        'closure: a full rebuild), src/graphics/primitive_processor.cpp, src/graphics/shared_memory.cpp, src/system/xmemory.cpp; '
        'rexlego/src/gpu_native/memory_watch.cpp (native builds only) = the staged CRLF after-file %s (== keep-watch-rexlego.diff '
        'applied to the LF form).' % (c1, diffs['c1' + c1][0], diffs['c1' + c1][1][:16].upper(), c1src, ha[:16].upper()),
        'M1 (Agent 5): src/graphics/d3d12/shared_memory.cpp. P2c (Agent 12) + r1r2 (#18/#20, Agent 7): command_processor.cpp/.h, '
        'deferred_command_list.cpp/.h (REX_D3D12_DEFERRED_COUNTERS 0: counters compiled out). #26 (Agent 9): codegen tool '
        'option db16cyc_pause, default OFF; the game builds keep the pinned S1 generated output (gen-check against baseline/).',
        'New switches, all OFF by default: %s.' % cvtext,
        'S4c, the last step (Agent 9, %s sha256 %s): rexlego/CMakeLists.txt + new rexlego/src/gpu_wait_backoff.cpp (%s): #24 GPU '
        'wait back-off hooks on sub_83FBF7D0, sub_83FAF180, sub_83FB09E8, sub_83FC0C10, OFF builds only '
        '(LEGO_GPU_WAIT_HOOK_GETDATA=1); env LEGO_GPU_WAIT_BACKOFF_US unset = OFF (every hook calls the original at once), '
        'LEGO_GPU_WAIT_SPIN_US, LEGO_GPU_WAIT_STATS%s.'
        % (diffs['s4c'][0], diffs['s4c'][1][:16].upper(), ht[:8].upper(),
           '; #30 CMake option LEGODIMENSIONS_SCENE_WALK_PROBE, default OFF' if a.s4c == '24-30' else ''),
        'B4 deferred. Per-file hashes: build/agent2/s4b/HASHES.txt; new strings: build/agent2/S4b-strings.tsv.',
    ]
    for rel in rels:
        own, item, _ = owner_item(rel)
        note('%-62s %s -> %s  %s: %s; %s' % (rel, befores[rel][:16].upper() if rel in befores else 'ABSENT          ',
                                             after_h[rel][:16].upper(), own, item, switch(rel)))
    if a.dry_run:
        print('--dry-run: %d checks PASS; scratch results in %s (HASHES.txt, S4b-strings.tsv); nothing written to snap1; '
              'would write %s:' % (len(res), rr(work), rr(NOTES)))
        print('\n'.join('  ' + x for x in note_lines))
        print('wall %.1fs' % (time.time() - t0))
        return

    # ---- apply: backups, snap1 copies (mtime = now), PATCHES, STATE, notes
    for rel in rels:
        if rel not in befores:
            continue
        bp = os.path.join(BACKUP, *rel.split('/'))
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        shutil.copy2(snapf(rel), bp)
        if sha(bp) != befores[rel]:
            raise SystemExit('backup of %s does not hash to %s; stopping (snap1 unchanged)' % (rel, befores[rel][:16]))
    now = time.time()
    patched = {}
    for rel in rels:
        dst = snapf(rel)
        if os.path.exists(dst):
            os.chmod(dst, 0o666)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(wpath[rel], dst)
        os.utime(dst, (now, now))
        h = sha(dst)
        if h != after_h[rel]:
            raise SystemExit('snap1 copy of %s hashes to %s, not %s; stopping (revert: snap-patch.py revert S4b after '
                             'PATCHES-S4b.tsv exists, else restore from %s)' % (rel, h[:16], after_h[rel][:16], BACKUP))
        st = os.stat(dst)
        patched[rel] = (st.st_size, st.st_mtime_ns, h)
        print('patched snap1 %s: %s -> %s (%s -> %d B)' % (rel, befores[rel][:16].upper() if rel in befores else 'ABSENT',
                                                         h[:16].upper(), sizes[rel] if rel in befores else '-', st.st_size))
    suffix = ''.join('; note: %s' % n for n in note_lines)
    pt = os.path.join(S.SNAP_ROOT, 'PATCHES-%s.tsv' % TAG)
    with open(pt, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# patches applied to build/agent2/snap1 for %s by build/agent2/prep-s4b.py (relpath under '
                'DimensionsRecomp/, sha256 before, sha256 after, source, time, note)%s\n' % (TAG, suffix))
        for rel in rels:
            own, item, src = owner_item(rel)
            if rel in befores:
                bnote = 'backup ' + rr(os.path.join(BACKUP, *rel.split('/'))).replace('/', '\\')
                srcx = '%s, applied to the S4a snap1 copy' % src
            else:
                bnote = 'new file (revert deletes it)'
                srcx = 'new file from %s' % src
            f.write('\t'.join([rel, befores[rel].upper() if rel in befores else 'ABSENT', after_h[rel].upper(), srcx, now_s,
                               '%s %s: %s (%s); == staging record; %s' % (TAG, own, item, switch(rel), bnote)]) + '\n')
    sp = os.path.join(S.SNAP_ROOT, 'STATE-%s-%s.tsv' % (TAG, time.strftime('%H%M')))
    if os.path.exists(sp):
        raise SystemExit('%s exists; stopping (snap1 copies and PATCHES-S4b.tsv are written)' % sp)
    rows = []
    for rel in order:
        c = base_rows[rel]
        if rel in patched:
            lp = livef(rel)
            lst = os.stat(lp)
            c = [rel, str(lst.st_size), str(lst.st_mtime_ns), sha(lp), str(patched[rel][0]), str(patched[rel][1]),
                 patched[rel][2], TAG]
        rows.append(c)
    if tu not in base_rows:
        lp = livef(tu)
        if os.path.exists(lp):
            lst = os.stat(lp)
            lv = [str(lst.st_size), str(lst.st_mtime_ns), sha(lp)]
        else:
            lv = ['-', '-', '-']
        newrow = [tu] + lv + [str(patched[tu][0]), str(patched[tu][1]), patched[tu][2], TAG]
        keys = [c[0] for c in rows]
        if keys == sorted(keys):
            rows.insert(bisect.bisect(keys, tu), newrow)
        else:
            rows.append(newrow)
    with open(sp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# snap1 state after prep-s4b.py %s apply %s: %d files (rel, live size, live mtime_ns, live sha256, '
                'snap1 size, snap1 mtime_ns, snap1 sha256, origin); generated/ not listed; note: %s with the %d S4b '
                'rows replaced or added (live columns re-read now; - = not in live; every other row keeps the S4a '
                'record)%s\n' % (TAG, now_s, len(rows), BASE, len(patched), suffix))
        f.write('\n'.join('\t'.join(c) for c in rows) + '\n')
    with open(NOTES, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(note_lines) + '\n')
    shutil.copyfile(os.path.join(work, 'S4b-strings.tsv'), STRINGS)
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, 'HASHES.txt')
    if os.path.exists(hp) and sha(hp) != sha(os.path.join(work, 'HASHES.txt')):
        hp = os.path.join(OUT, 'HASHES-%s.txt' % stamp)
    shutil.copyfile(os.path.join(work, 'HASHES.txt'), hp)
    for p in (hp, pt, sp, NOTES, STRINGS):
        print('wrote %s (sha256 %s)' % (rr(p), sha(p)[:16].upper()))
    vp = subprocess.run([sys.executable, os.path.join(A, 'snap-patch.py'), 'verify', TAG], capture_output=True,
                        text=True)
    print((vp.stdout + vp.stderr).strip())
    print('apply done, wall %.1fs; verify %s exit %d' % (time.time() - t0, TAG, vp.returncode))
    sys.exit(vp.returncode)


if __name__ == '__main__':
    main()
