"""Agent 2 - S4a inputs (task #4, board run 2). S4a = snap1 at S3d (STATE-S3d-0342.tsv, the trees behind devoff3-bin
and native3d-bin) + 5 rexglue-sdk files (#7 u diag, #8 P2, #5 fix (i), #38 precise wait: new switches, all default
false; #32 warm-boot fix: always on, no switch) + #2 miss cache (rexlego/src/gpu_native/shaders.cpp, native only: OFF
builds compile no gpu_native file). Nothing is copied from live and live is never written: each result is made by
git apply of the staged diff to a copy of the S3d snap1 file in a scratch tree (build/agent2/s4a/work-HHMMSS) and must
hash-equal its staging record (input hash before, output hash after). #32 has no staged diff: line 564 is replaced
here, and the 1-line diff written for it (pc-warmboot.diff) is what git apply applies to the scratch copy.
git runs with GIT_CEILING_DIRECTORIES=<repo root> (the workspace sits inside a parent repo) and core.autocrlf=false.
  python build\\agent2\\prep-s4a.py --dry-run   all checks + the scratch results; nothing written outside s4a/work-*
  python build\\agent2\\prep-s4a.py             the same, then backups (build/agent2/snap1-backup-S4a), the 6 snap1
                                                copies, snap1/PATCHES-S4a.tsv, snap1/STATE-S4a-HHMM.tsv,
                                                build/agent2/S4a-notes.txt, s4a/HASHES.txt + s4a/pc-warmboot.diff,
                                                then snap-patch.py verify S4a
Any FAIL before the apply and nothing is written to snap1 (no hand merges: a base or result mismatch is a stop).
"""
import argparse
import difflib
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snap as S  # noqa: E402  (R, SNAP_ROOT)

R = S.R
A = os.path.join(R, 'build', 'agent2')
OUT = os.path.join(A, 's4a')
TAG = 'S4a'
BASE = 'STATE-S3d-0342.tsv'
NOTES = os.path.join(A, 'S4a-notes.txt')
BACKUP = os.path.join(A, 'snap1-backup-%s' % TAG, 'DimensionsRecomp')
OLD32 = b'while (creation_threads_.size() < creation_thread_original_count) {'
NEW32 = b'while (creation_threads_.size() < creation_thread_needed_count) {'
PC32 = 'rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp'
# root: where git apply runs, relative to the scratch tree (the diff's path root)
ITEMS = [
    dict(item='#7 u diag', owner='A12', rel='rexglue-sdk/src/graphics/d3d12/shared_memory.cpp',
         diff='build/agent12/s4-diag/upload-hash-log.diff', dsha='D290530197427138', root='DimensionsRecomp/rexglue-sdk',
         before='b120d07c6709d0d2a7836b532ed06b2032a418cbd4a71808cd318c7e6eb6cfbc',
         after='bb0838ce3909e18a63099b47b4e852cb9d2307eb2bf2535c3bc8ff38bfd64587', after_file=None,
         cvar='shared_memory_upload_hash_log', switch='cvar shared_memory_upload_hash_log, default false'),
    dict(item='#8 P2', owner='A12', rel='rexglue-sdk/src/graphics/shared_memory.cpp',
         diff='build/agent12/s4-p2/single-hold-rearm.diff', dsha='77BEB64E1325B854', root='DimensionsRecomp/rexglue-sdk',
         before='15c89edb4b197c17487a9d45208d5ce624de98abe416f86942c5d14ed43eb282',
         after='0be4badcac666bee80f656669d072eda8b55c2d25d25c448bc4c29e12bd503f4', after_file=None,
         cvar='shared_memory_single_hold_rearm', switch='cvar shared_memory_single_hold_rearm, default false'),
    dict(item='#5 fix (i)', owner='A12', rel='rexglue-sdk/src/system/xmemory.cpp',
         diff='build/agent12/s4-fixi/protect-hold-g.diff', dsha='80CAD795EEEF7AD4', root='DimensionsRecomp/rexglue-sdk',
         before='6e8fa1ba80ef9271d4433dd1bb2cad0403360e222b22ced78aa4c7951d811db4',
         after='141fb1a947d59156eb40a835b27e64f94ee22a3f5be0e0f70f17bc85c676c87a', after_file=None,
         cvar='physical_protect_hold_global_lock', switch='cvar physical_protect_hold_global_lock, default false'),
    dict(item='#38 precise wait', owner='A11', rel='rexglue-sdk/src/core/timer_queue.cpp',
         diff='build/agent11/timerq/stage/timerq.diff', dsha='D07A2DC4878DAE8D', root='',
         before='d8724b29c43286b0e7d7614c713154e3694ee96827ed847701ad6cc1a876d9ec',
         after='015c04a22dacc592b8da0f5bb395353a4dd813e1f847775b584cb974f6e98846',
         after_file='build/agent11/timerq/stage/timer_queue.cpp',
         cvar='timer_queue_precise_wait', switch='cvar timer_queue_precise_wait, default false, init only'),
    dict(item='#32 warm-boot fix', owner='A1', rel=PC32, diff=None, dsha=None, root='DimensionsRecomp/rexglue-sdk',
         before='5dbed81f611e25b17ebbe7fe2779ed5540fd94651f2d29a631d1c8ab74ae5213', after=None, after_file=None,
         cvar=None, switch='always on, no switch; L564 creation_thread_original_count -> creation_thread_needed_count '
                           '(Agent 10 b2r S27: output-identical, SAFE)'),
    dict(item='#2 miss cache', owner='A4', rel='rexlego/src/gpu_native/shaders.cpp',
         diff='build/agent4/s34/shaders-s34.patch', dsha='328BDAE19ABFC6C8', root='DimensionsRecomp',
         before='e87a2dee43d38d8ebbee8efd663de70a293f7826b5ac0231b8b8a08e6a7e916d',
         after='9567fe3f3b63637d9595d6b74b72567e1caea2d1a071e872d12660dfb37e1efa',
         after_file='build/agent4/s34/shaders.cpp',
         cvar=None, switch='env LEGO_NATIVE_SHADER_MISS_CACHE, default off; native only'),
]
NOTE_LINES = [
    'S4a build inputs (task #4, board run 2): snap1 at S3d (STATE-S3d-0342.tsv; the trees behind devoff3-bin and '
    'native3d-bin) + 6 files, each made by git apply of the staged diff to the S3d snap1 copy and hash-checked against '
    'its staging record (input hash before, output hash after); nothing was copied from live and live was not written.',
    'rexglue-sdk, new switches, all OFF by default: #7 u diag (Agent 12, src/graphics/d3d12/shared_memory.cpp, cvar '
    'shared_memory_upload_hash_log=false); #8 P2 (Agent 12, src/graphics/shared_memory.cpp, cvar '
    'shared_memory_single_hold_rearm=false); #5 fix (i) (Agent 12, src/system/xmemory.cpp, cvar '
    'physical_protect_hold_global_lock=false); #38 precise wait (Agent 11, src/core/timer_queue.cpp, cvar '
    'timer_queue_precise_wait=false, init only).',
    'rexglue-sdk, always on (no switch): #32 warm-boot fix, src/graphics/d3d12/pipeline_cache.cpp L564 '
    'creation_thread_original_count -> creation_thread_needed_count in the while (creation_threads_.size() < ...) loop '
    '(Agent 10, b2r S27: output-identical, SAFE); 1-line diff build/agent2/s4a/pc-warmboot.diff.',
    'Native only: #2 miss cache (Agent 4, build/agent4/s34/shaders-s34.patch on rexlego/src/gpu_native/shaders.cpp, env '
    'LEGO_NATIVE_SHADER_MISS_CACHE, default off); OFF builds compile no gpu_native file, so devoff4 does not contain it.',
    'Left out of S4a: C1 (#4: changes xmemory.h, a full rebuild), the #24 hook, the P2 counter, #18/#20, #26. Generated '
    'code: the pinned S1 output (gen-check against baseline/), as in S1-S3d. Per-file hashes: build/agent2/s4a/HASHES.txt.',
]


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
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

    # ---- base: snap1 is at S3d
    states = sorted([p for p in glob.glob(os.path.join(S.SNAP_ROOT, 'STATE-*.tsv'))
                     if 'reverted' not in os.path.basename(p)], key=os.path.getmtime)
    newest = os.path.basename(states[-1]) if states else 'none'
    check(newest == BASE, 'the newest STATE record in snap1 is %s (%s)' % (BASE, newest))
    done = sorted(os.path.basename(p) for p in glob.glob(os.path.join(S.SNAP_ROOT, 'PATCHES-%s*' % TAG))
                  + glob.glob(os.path.join(S.SNAP_ROOT, 'STATE-%s-*' % TAG)))
    check(not done, 'no %s record in snap1 yet%s' % (TAG, ' (found %s)' % ', '.join(done) if done else ''))
    check(not os.path.exists(os.path.dirname(BACKUP)), 'no %s yet' % rr(os.path.dirname(BACKUP)))
    if not a.dry_run:
        check(not os.path.exists(NOTES), 'no %s yet' % rr(NOTES))
    base_rows, order = {}, []
    with open(os.path.join(S.SNAP_ROOT, BASE), encoding='utf-8-sig') as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip():
                continue
            c = ln.rstrip('\r\n').split('\t')
            base_rows[c[0]] = c
            order.append(c[0])
    vp = subprocess.run([sys.executable, os.path.join(A, 'snap-patch.py'), 'verify', 'S3d'], capture_output=True,
                        text=True)
    vout = (vp.stdout + vp.stderr).strip().splitlines()
    check(vp.returncode == 0 and 'RESULT: PASS' in [x.strip() for x in vout],
          'snap-patch.py verify S3d (all of snap1 == %s): %s' % (BASE, vout[0] if vout else 'no output'))
    for x in vout[1:]:
        if x.strip().startswith('BAD'):
            print('   ' + x.strip())

    # ---- scratch tree, no git repository discoverable from it
    stamp = time.strftime('%H%M%S')
    work = os.path.join(OUT, 'work-' + stamp)
    os.makedirs(os.path.join(work, 'DimensionsRecomp'))
    rc, out = git(['rev-parse', '--git-dir'], work)
    check(rc != 0, 'no git repository is discovered from %s (GIT_CEILING_DIRECTORIES=%s; rev-parse: %s)'
          % (rr(work), ENV['GIT_CEILING_DIRECTORIES'], (out.splitlines() or ['?'])[0][:90]))
    stop_if_failed('base')

    results, sizes, diffsha = {}, {}, {}
    for it in ITEMS:
        rel = it['rel']
        sp, lp = snapf(rel), livef(rel)
        hs = sha(sp)
        row = base_rows.get(rel)
        check(row is not None and row[6].lower() == hs == it['before'],
              '%s %s: snap1 %s == the %s row (%s) == the staging record before-hash (%s)'
              % (it['item'], rel, hs[:16].upper(), BASE, (row[6][:16].upper() if row else 'none'),
                 it['before'][:16].upper()))
        hl = sha(lp)
        note('%s: live %s %s snap1 (live is not read for S4a and not written)'
             % (rel, hl[:16].upper(), '==' if hl == hs else '!='))
        wf = os.path.join(work, 'DimensionsRecomp', *rel.split('/'))
        os.makedirs(os.path.dirname(wf), exist_ok=True)
        shutil.copyfile(sp, wf)
        aroot = os.path.join(work, *it['root'].split('/')) if it['root'] else work
        want = os.path.relpath(wf, aroot).replace('\\', '/')
        if it['diff']:
            dp = os.path.join(R, *it['diff'].split('/'))
        else:
            # #32: replace the one line, write the 1-line diff, then git apply it like the staged ones
            data = open(wf, 'rb').read()
            idx = data.find(OLD32)
            line = data[:idx].count(b'\n') + 1 if idx >= 0 else 0
            check(data.count(OLD32) == 1 and line == 564, '#32: exactly one "%s" in %s, at L564 (%d found, first L%d)'
                  % (OLD32.decode(), rel, data.count(OLD32), line))
            new = data.replace(OLD32, NEW32)
            it['after'] = hashlib.sha256(new).hexdigest()
            al = data.decode('latin-1').splitlines(keepends=True)
            bl = new.decode('latin-1').splitlines(keepends=True)
            d = ''.join(difflib.unified_diff(al, bl, 'a/' + want, 'b/' + want, n=3)).encode('latin-1')
            dl = [x for x in d.split(b'\n') if x[:1] in (b'-', b'+') and not x.startswith((b'--- ', b'+++ '))]
            check(dl == [b'-' + data.splitlines()[563], b'+' + new.splitlines()[563]],
                  '#32 diff: one removed line and one added line (L564), %d B' % len(d))
            dp = os.path.join(work, 'pc-warmboot.diff')
            with open(dp, 'wb') as f:
                f.write(d)
            it['dsha'] = sha(dp)[:16].upper()
        hd = sha(dp)
        diffsha[rel] = (dp, hd)
        check(hd.upper().startswith(it['dsha']), '%s diff %s: sha256 %s starts with %s'
              % (it['item'], rr(dp), hd[:16].upper(), it['dsha']))
        pairs = diff_pairs(open(dp, 'rb').read())
        check(pairs == [('a/' + want, 'b/' + want)], '%s diff patches exactly one file, %s under %s (%s)'
              % (it['item'], want, it['root'] or 'the repo root', pairs))
        rc, out = git(['apply', '--check', '--whitespace=nowarn', dp], aroot)
        if check(rc == 0, '%s git apply --check in %s%s' % (it['item'], rr(aroot), (': ' + out) if out else '')):
            rc, out = git(['apply', '--whitespace=nowarn', dp], aroot)
            check(rc == 0, '%s git apply%s' % (it['item'], (': ' + out) if out else ''))
        hr = sha(wf)
        sizes[rel] = (os.path.getsize(sp), os.path.getsize(wf))
        ok = hr == it['after']
        txt = 'result %s (%d B) == the staging record after-hash %s' % (hr[:16].upper(), sizes[rel][1],
                                                                       it['after'][:16].upper())
        if it['after_file']:
            hf = sha(os.path.join(R, *it['after_file'].split('/')))
            ok = ok and hf == hr
            txt += ' == %s (%s)' % (it['after_file'], hf[:16].upper())
        if not it['diff']:
            txt = 'result %s (%d B) == the line-564 replacement made in memory' % (hr[:16].upper(), sizes[rel][1])
        check(ok, '%s %s' % (it['item'], txt))
        results[rel] = wf
        # switch default (source)
        text = open(wf, encoding='utf-8', errors='replace').read()
        base_text = open(sp, encoding='utf-8', errors='replace').read()
        if it['cvar']:
            m = re.findall(r'REXCVAR_DEFINE_BOOL\(\s*%s\s*,\s*(\w+)' % re.escape(it['cvar']), text)
            check(m == ['false'] and it['cvar'] not in base_text,
                  '%s defines the new cvar %s once, default %s (not in the S3d file)'
                  % (it['item'], it['cvar'], '/'.join(m) or 'none'))
        elif it['diff']:
            hits = [ln.strip() for ln in text.splitlines() if 'LEGO_NATIVE_SHADER_MISS_CACHE' in ln]
            check(hits and 'LEGO_NATIVE_SHADER_MISS_CACHE' not in base_text,
                  '%s: LEGO_NATIVE_SHADER_MISS_CACHE is new in shaders.cpp: %s' % (it['item'], ' | '.join(hits)[:200]))
        else:
            check(text.count('creation_thread_needed_count') == base_text.count('creation_thread_needed_count') + 1,
                  '#32: creation_thread_needed_count %d -> %d uses; creation_thread_original_count %d -> %d'
                  % (base_text.count('creation_thread_needed_count'), text.count('creation_thread_needed_count'),
                     base_text.count('creation_thread_original_count'), text.count('creation_thread_original_count')))
    stop_if_failed('scratch results')

    now_s = time.strftime('%Y-%m-%d %H:%M:%S')
    hashes = ['# S4a inputs, written %s by build/agent2/prep-s4a.py: base snap1 at S3d (%s); per file: item, owner, '
              'relpath under DimensionsRecomp/, diff (sha256), before sha256 (size), after sha256 (size), switch'
              % (now_s, BASE)]
    for it in ITEMS:
        rel = it['rel']
        dp, hd = diffsha[rel]
        hashes.append('\t'.join([it['item'], it['owner'], rel, '%s (%s)' % (rr(dp) if it['diff'] else
                                 'build/agent2/s4a/pc-warmboot.diff', hd.upper()),
                                 '%s (%d B)' % (it['before'].upper(), sizes[rel][0]),
                                 '%s (%d B)' % (it['after'].upper(), sizes[rel][1]), it['switch']]))
    with open(os.path.join(work, 'HASHES.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(hashes) + '\n')
    if a.dry_run:
        print('--dry-run: %d checks PASS; scratch results in %s (HASHES.txt, pc-warmboot.diff); nothing written to '
              'snap1; would write %s:' % (len(res), rr(work), rr(NOTES)))
        print('\n'.join('  ' + x for x in NOTE_LINES))
        print('wall %.1fs' % (time.time() - t0))
        return

    # ---- apply: backups, snap1 copies, PATCHES, STATE, notes
    for it in ITEMS:
        rel = it['rel']
        bp = os.path.join(BACKUP, *rel.split('/'))
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        shutil.copy2(snapf(rel), bp)
        if sha(bp) != it['before']:
            raise SystemExit('backup of %s does not hash to %s; stopping (snap1 unchanged)' % (rel, it['before'][:16]))
    now = time.time()
    patched = {}
    for it in ITEMS:
        rel = it['rel']
        dst = snapf(rel)
        os.chmod(dst, 0o666)
        shutil.copyfile(results[rel], dst)
        os.utime(dst, (now, now))
        h = sha(dst)
        if h != it['after']:
            raise SystemExit('snap1 copy of %s hashes to %s, not %s; stopping (revert: snap-patch.py revert S4a after '
                             'PATCHES-S4a.tsv exists, else restore from %s)' % (rel, h[:16], it['after'][:16], BACKUP))
        st = os.stat(dst)
        patched[rel] = (st.st_size, st.st_mtime_ns, h)
        print('patched snap1 %s: %s -> %s (%d -> %d B)' % (rel, it['before'][:16].upper(), h[:16].upper(),
                                                          sizes[rel][0], st.st_size))
    suffix = ''.join('; note: %s' % n for n in NOTE_LINES)
    pt = os.path.join(S.SNAP_ROOT, 'PATCHES-%s.tsv' % TAG)
    with open(pt, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# patches applied to build/agent2/snap1 for %s by build/agent2/prep-s4a.py (relpath under '
                'DimensionsRecomp/, sha256 before, sha256 after, source, time, note)%s\n' % (TAG, suffix))
        for it in ITEMS:
            rel = it['rel']
            dp, hd = diffsha[rel]
            src = ('git apply %s (sha256 %s) to the S3d snap1 copy' % (rr(dp) if it['diff'] else
                   'build/agent2/s4a/pc-warmboot.diff', hd[:16].upper()))
            bnote = rr(os.path.join(BACKUP, *rel.split('/'))).replace('/', '\\')
            f.write('\t'.join([rel, it['before'].upper(), it['after'].upper(), src, now_s,
                               '%s %s: %s (%s); == staging record; backup %s' % (TAG, it['owner'], it['item'],
                                                                                it['switch'], bnote)]) + '\n')
    sp = os.path.join(S.SNAP_ROOT, 'STATE-%s-%s.tsv' % (TAG, time.strftime('%H%M')))
    if os.path.exists(sp):
        raise SystemExit('%s exists; stopping (snap1 copies and PATCHES-S4a.tsv are written)' % sp)
    rows = []
    for rel in order:
        c = base_rows[rel]
        if rel in patched:
            lst = os.stat(livef(rel))
            c = [rel, str(lst.st_size), str(lst.st_mtime_ns), sha(livef(rel)), str(patched[rel][0]),
                 str(patched[rel][1]), patched[rel][2], TAG]
        rows.append('\t'.join(c))
    with open(sp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# snap1 state after prep-s4a.py %s apply %s: %d files (rel, live size, live mtime_ns, live sha256, '
                'snap1 size, snap1 mtime_ns, snap1 sha256, origin); generated/ not listed; note: %s with the %d S4a '
                'rows replaced (their live columns re-read now; every other row keeps the S3d record)%s\n'
                % (TAG, now_s, len(rows), BASE, len(patched), suffix))
        f.write('\n'.join(rows) + '\n')
    with open(NOTES, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(NOTE_LINES) + '\n')
    os.makedirs(OUT, exist_ok=True)
    for name in ('HASHES.txt', 'pc-warmboot.diff'):
        src, dst = os.path.join(work, name), os.path.join(OUT, name)
        if os.path.exists(dst) and sha(dst) != sha(src):
            dst = os.path.join(OUT, name.replace('.', '-%s.' % stamp, 1))
        shutil.copyfile(src, dst)
        print('wrote %s (sha256 %s)' % (rr(dst), sha(dst)[:16].upper()))
    for p in (pt, sp, NOTES):
        print('wrote %s (sha256 %s)' % (rr(p), sha(p)[:16].upper()))
    vp = subprocess.run([sys.executable, os.path.join(A, 'snap-patch.py'), 'verify', TAG], capture_output=True,
                        text=True)
    print((vp.stdout + vp.stderr).strip())
    print('apply done, wall %.1fs; verify S4a exit %d' % (time.time() - t0, vp.returncode))
    sys.exit(vp.returncode)


if __name__ == '__main__':
    main()
