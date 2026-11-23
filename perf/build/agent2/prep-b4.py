#!/usr/bin/env python3
"""prep-b4.py (Agent 2, board run 2): source inputs for devoffB4 + nativeB4 = the B line + S4a (Agent 9's batch-nolr
codegen + the S4a sources; #2 native only). Plan: perf-notes/agent2-baseline.md, "Task #15" section 2 (option B).
It copies files from build/agent2/snap1/DimensionsRecomp (at S4a: the tree behind devoff4-bin and native4-bin) into
the B source trees, byte for byte. Nothing is built; no git; live, snap1 and snap1-sdk are only read.
  native: snapB3 (snap1 at S3d + batch-nolr generated/, nativeB's tree) gets the 6 S4a files (5 rexglue-sdk files +
          rexlego/src/gpu_native/shaders.cpp; table parsed from apply-s4a-live.ps1).
  off   : snapB (snap1 at S2 + batch-nolr generated/, devoffB's tree) gets option B's 35 files: every file of the snap1
          PATCHES-S1..S4a rows whose snapB copy differs from snap1 (4 rexlego files + 31 files that are no snapB-off
          build input but that stage-snap-bin.ps1's -GameSnap row check needs; 3 of them are new).
  python build/agent2/prep-b4.py [--variant off|native|both]         dry run (default): read-only, writes only the
                                                                     report build/agent2/prep-b4-<HHMM>.txt
  python build/agent2/prep-b4.py --go [--variant off|native|both]    apply
Per file: the tree copy must equal its base (native: the S4a before; off: the before of the file's first S3/S3d/S4a
PATCHES row, i.e. the S2 level; ABSENT = the file must not exist) and the snap1 source must equal its last PATCHES
after (native: also the S4a after in apply-s4a-live.ps1). The file list must match the 14:24 plan (b4-dryrun [2] and
[10]: native 6 files; off 35 files, 3 absent, rexlego = draw.cpp, shaders.cpp, settings_preferences.cpp,
settings_registry.cpp); install/bin's rexruntime.dll, rexgpu-xenos.dll and TracyClient.dll must equal the S4a bin's
(B4 links the S4a SDK). Any mismatch, an existing backup folder, record or notes file, a staged out folder, or a
running game/ninja/clang/cmake process: --go refuses and writes nothing (no hand merges).
--go: backs up every existing file (shutil.copy2 to build/agent2/snapB3-backup-S4a or snapB-backup-B4, re-hashed ==
base) before any tree write; then per file chmod 0o666, copyfile, re-hash == after, then os.utime(now) (Agent 1's
mtime rule, 14:41: every copied file gets mtime = now after the copy and hash check, so ninja and the native
fingerprint see it). Then every PATCHES row's file in the tree must equal its last after (stage-snap-bin's -GameSnap
check). On any error it restores every touched file from its backup (re-hash == base, mtime = now) or removes a file
it created, and exits 4. Writes build/agent2/B4-copies-<variant>.tsv (the record run-b4.ps1 checks) and
B4-manifest-notes-<variant>.txt (stage-snap-bin.ps1 -ManifestNotesFile).
Exit: 0 = dry run ready / --go done; 1 = dry run not ready; 2 = --go refused; 3 = processes running; 4 = rolled back.
"""
import argparse
import datetime
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
A2 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(A2))
SNAP1 = os.path.join(A2, 'snap1', 'DimensionsRecomp')
PATCH_TAGS = ['S1', 'S2', 'S3', 'S3d', 'S4a']
VARIANTS = {
    'off': dict(tree='snapB', level='S2', backup='snapB-backup-B4', out='devoffB4-bin', compare='devoff4-bin',
                notes_src='snapB-manifest-notes.txt', n=35, absent=3, bin='devoffB4',
                rexlego=['rexlego/src/gpu_native/draw.cpp', 'rexlego/src/gpu_native/shaders.cpp',
                         'rexlego/src/settings_preferences.cpp', 'rexlego/src/settings_registry.cpp']),
    'native': dict(tree='snapB3', level='S3d', backup='snapB3-backup-S4a', out='nativeB4-bin', compare='native4-bin',
                   notes_src='snapB3-manifest-notes.txt', n=6, absent=0, bin='nativeB4',
                   rexlego=['rexlego/src/gpu_native/shaders.cpp']),
}
DLLS = ('rexruntime.dll', 'rexgpu-xenos.dll', 'TracyClient.dll')
PROC_RE = re.compile(r'^(legodimensions.*|ninja|clang.*|lld-link|ld\.lld|cmake)\.exe$', re.I)
NOW = datetime.datetime.now()
lines, fails = [], []
CACHE = {}


def w(s=''):
    print(s, flush=True)
    lines.append(s)


def fail(s):
    fails.append(s)
    w('  FAIL ' + s)


def sha(p):
    if not os.path.isfile(p):
        return 'MISSING'
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def hh(p):
    if p not in CACHE:
        CACHE[p] = sha(p)
    return CACHE[p]


def rr(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def tpath(tree, rel):
    return os.path.join(A2, tree, 'DimensionsRecomp', *rel.split('/'))


def s4a_table():
    with open(os.path.join(A2, 'apply-s4a-live.ps1'), encoding='utf-8') as f:
        txt = f.read()
    rows = re.findall(r"@\('([^']*)',\s*'([^']*)',\s*'([0-9A-F]{64})',\s*(\d+),\s*'([0-9A-F]{64})',\s*(\d+)\)", txt)
    return dict((rel, (it, b, a)) for it, rel, b, bs, a, asz in rows)


def patch_rows():
    rows = []
    for t in PATCH_TAGS:
        p = os.path.join(A2, 'snap1', 'PATCHES-%s.tsv' % t)
        if not os.path.isfile(p):
            fail('snap1/PATCHES-%s.tsv missing' % t)
            continue
        with open(p, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.rstrip('\r\n')
                if not line or line.startswith('#'):
                    continue
                c = line.split('\t')
                if len(c) >= 3:
                    rows.append((t, c[0], c[1].strip().upper(), c[2].strip().upper()))
    return rows


def procs():
    try:
        out = subprocess.run(['tasklist', '/fo', 'csv', '/nh'], capture_output=True, text=True).stdout
    except OSError as e:
        return ['tasklist failed: %s' % e]
    res = []
    for line in out.splitlines():
        m = re.match(r'^"([^"]+)","(\d+)"', line)
        if m and PROC_RE.match(m.group(1)):
            res.append('%s(%s)' % (m.group(1), m.group(2)))
    return res


def kind_of(it):
    if it['base'] == 'ABSENT':
        return 'new'
    rel = it['rel']
    return 'rexlego' if rel.startswith('rexlego/') else ('rexglue-sdk' if rel.startswith('rexglue-sdk/') else 'other')


def plan(v, cfg, rows, s4a):
    tree, li = cfg['tree'], PATCH_TAGS.index(cfg['level'])
    last, first_later = {}, {}
    for t, rel, b, a in rows:
        last[rel] = a
        if PATCH_TAGS.index(t) > li and rel not in first_later:
            first_later[rel] = b
    w('')
    w('[%s] %s: build/agent2/%s/DimensionsRecomp (level %s) -> the S4a level, source build/agent2/snap1/DimensionsRecomp'
      % (v, cfg['bin'], tree, cfg['level']))
    for rel in sorted(r for r, a in last.items() if a == 'DELETED'):
        fail('%s: its last PATCHES after is DELETED (not handled here)' % rel)
    items, same = [], 0
    for rel in sorted(r for r in last if last[r] != 'DELETED'):
        hs = hh(os.path.join(SNAP1, *rel.split('/')))
        ht = hh(tpath(tree, rel))
        if hs != last[rel]:
            fail('snap1 %s is %s, not its last PATCHES after %s' % (rel, hs[:16], last[rel][:16]))
            continue
        if ht == hs:
            same += 1
            continue
        items.append(dict(rel=rel, base=first_later.get(rel), after=last[rel], cur=ht))
    for it in items:
        rel, base, cur = it['rel'], it['base'], it['cur']
        if base is None:
            ok, exp = False, 'no S3/S3d/S4a row after the %s level, so it should already equal snap1' % cfg['level']
        elif base == 'ABSENT':
            ok, exp = cur == 'MISSING', 'ABSENT (a new file)'
        else:
            ok, exp = cur == base, base[:16]
        it['kind'] = kind_of(it)
        w('  %-4s %-62s %-11s %s -> %s' % ('ok' if ok else 'BAD', rel, it['kind'],
                                           'ABSENT' if base == 'ABSENT' else (base or '-')[:16], it['after'][:16]))
        if not ok:
            fail('%s %s is %s, expected %s' % (tree, rel, 'missing' if cur == 'MISSING' else cur[:16], exp))
        if v == 'native':
            t = s4a.get(rel)
            if t is None:
                fail('%s is not one of the 6 S4a files' % rel)
            elif t[1] != base or t[2] != it['after']:
                fail('%s: PATCHES before/after %s/%s != the S4a table %s/%s' % (rel, (base or '-')[:16], it['after'][:16],
                                                                               t[1][:16], t[2][:16]))
    n_abs = sum(1 for it in items if it['base'] == 'ABSENT')
    rl = sorted(it['rel'] for it in items if it['rel'].startswith('rexlego/'))
    cnt = dict((k, sum(1 for it in items if it['kind'] == k)) for k in ('rexlego', 'rexglue-sdk', 'other', 'new'))
    w('  %d PATCHES files (last row each), %d already == snap1, %d to copy: %d rexlego, %d rexglue-sdk, %d other, %d new'
      % (len(last), same, len(items), cnt['rexlego'], cnt['rexglue-sdk'], cnt['other'], cnt['new']))
    if len(items) != cfg['n'] or n_abs != cfg['absent'] or rl != sorted(cfg['rexlego']):
        fail('%s: %d files (%d new), rexlego %s; the 14:24 plan is %d files (%d new), rexlego %s' % (
            v, len(items), n_abs, ', '.join(r.split('/')[-1] for r in rl), cfg['n'], cfg['absent'],
            ', '.join(r.split('/')[-1] for r in cfg['rexlego'])))
    if v == 'native' and sorted(it['rel'] for it in items) != sorted(s4a):
        fail('native: the copy list is not exactly the 6 S4a files')
    # folders, SDK install, compare bin
    for p in (os.path.join(A2, cfg['backup']), os.path.join(A2, 'B4-copies-%s.tsv' % v),
              os.path.join(A2, 'B4-manifest-notes-%s.txt' % v)):
        if os.path.exists(p):
            fail('%s already exists' % rr(p))
    if os.path.exists(os.path.join(A2, cfg['out'], 'MANIFEST.txt')):
        fail('build/agent2/%s is already staged' % cfg['out'])
    cmp_dir = os.path.join(A2, cfg['compare'])
    dl = []
    for d in DLLS:
        hi, hc = hh(os.path.join(A2, 'snap1-sdk', 'install', 'bin', d)), hh(os.path.join(cmp_dir, d))
        dl.append('%s %s %s' % (d, hi[:8], '==' if hi == hc else '!= %s' % hc[:8]))
        if hi != hc:
            fail('snap1-sdk/install/bin/%s != %s/%s: the install is no longer the S4a SDK' % (d, cfg['compare'], d))
    w('  install/bin vs %s: %s; %s MANIFEST %s' % (cfg['compare'], ', '.join(dl), cfg['compare'],
                                                hh(os.path.join(cmp_dir, 'MANIFEST.txt'))[:16]))
    return items, last


def notes_text(v, cfg, items, stamp):
    with open(os.path.join(A2, cfg['notes_src']), encoding='utf-8') as f:
        src = [ln.rstrip('\r\n') for ln in f]
    keep = [ln for ln in src if ln.strip() and not ln.startswith('A (')]
    inst = os.path.join(A2, 'snap1-sdk', 'install', 'bin')
    sdk = ('SDK: build/agent2/snap1-sdk/install = the S4a SDK (rexruntime.dll %s, rexgpu-xenos.dll %s, the files in %s): '
           'new switches, all OFF by default: #7 u diag (cvar shared_memory_upload_hash_log), #8 P2 '
           '(shared_memory_single_hold_rearm), #5 fix (i) (physical_protect_hold_global_lock), #38 precise wait '
           '(timer_queue_precise_wait, init only); always on: #32 warm-boot fix (pipeline_cache.cpp L564).'
           % (hh(os.path.join(inst, 'rexruntime.dll'))[:16], hh(os.path.join(inst, 'rexgpu-xenos.dll'))[:16],
              cfg['compare']))
    man = hh(os.path.join(A2, cfg['compare'], 'MANIFEST.txt'))[:16]
    if v == 'native':
        head = ('nativeB4 = the B line + S4a, NATIVE_GPU=ON with Agent 6 AOT inputs: nativeB\'s tree (snapB3: snap1 at S3d + '
                'Agent 9\'s batch-nolr generated/) + the 6 S4a files.')
        b4 = ('B4 (prep-b4.py --go, %s): the 6 S4a files copied from build/agent2/snap1 (at S4a, the tree behind '
              'native4-bin) into snapB3, each checked: the snapB3 copy == the S4a before, the copy == the S4a after '
              '(build/agent2/s4a/HASHES.txt); mtime set to now after the check (ninja and the native fingerprint see '
              'them); backups build/agent2/snapB3-backup-S4a; record build/agent2/B4-copies-native.tsv. Native only: '
              '#2 miss cache (rexlego/src/gpu_native/shaders.cpp, env LEGO_NATIVE_SHADER_MISS_CACHE, default off).'
              % stamp)
        tail = 'A (the same sources and SDK, pinned 0.0.23.3 codegen): build/agent2/native4-bin (MANIFEST %s).' % man
    else:
        cnt = dict((k, sum(1 for it in items if it['kind'] == k)) for k in ('rexlego', 'rexglue-sdk', 'other', 'new'))
        head = ('devoffB4 = the B line + S4a, NATIVE_GPU=OFF: devoffB\'s tree (snapB: snap1 at S2 + Agent 9\'s batch-nolr '
                'generated/) brought to the S4a level (option B), snapB-off rebuilt incrementally.')
        b4 = ('B4 (prep-b4.py --go, %s): %d files copied from build/agent2/snap1 (at S4a, the tree behind devoff4-bin) '
              'into snapB: every file of the snap1 PATCHES-S1..S4a rows whose snapB copy differed from snap1. Each '
              'checked: the snapB copy == its S2-level hash (the before of its first S3/S3d/S4a PATCHES row; %d new '
              'files were absent), the copy == its last PATCHES after; mtime set to now after the check; backups '
              'build/agent2/snapB-backup-B4; record build/agent2/B4-copies-off.tsv. %d rexlego files (%s; the OFF '
              'build compiles no gpu_native file); %d rexglue-sdk and %d other files are no snapB-off build input '
              '(the B trees link snap1-sdk/install) and are copied so the -GameSnap row check passes. Afterwards '
              'snapB/rexlego == snapB3/rexlego outside generated/ and out/.'
              % (stamp, len(items), cnt['new'], cnt['rexlego'],
                 ', '.join(it['rel'][len('rexlego/'):] for it in items if it['kind'] == 'rexlego'),
                 sum(1 for it in items if it['rel'].startswith('rexglue-sdk/')),
                 sum(1 for it in items if not it['rel'].startswith(('rexglue-sdk/', 'rexlego/')))))
        tail = 'A (the same sources and SDK, pinned 0.0.23.3 codegen): build/agent2/devoff4-bin (MANIFEST %s).' % man
    return [head] + keep + [b4, sdk, tail]


def apply(v, cfg, items, last, stamp):
    tree = cfg['tree']
    bk = os.path.join(A2, cfg['backup'], 'DimensionsRecomp')
    for it in items:
        if it['base'] == 'ABSENT':
            continue
        b = os.path.join(bk, *it['rel'].split('/'))
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.copy2(tpath(tree, it['rel']), b)
        if sha(b) != it['base']:
            w('REFUSED: the backup of %s does not hash to its base %s; nothing written to %s' % (it['rel'],
                                                                                              it['base'][:16], tree))
            return 2
    w('  backups: %s (%d files, each == base)' % (rr(bk), sum(1 for it in items if it['base'] != 'ABSENT')))
    touched = []
    try:
        for it in items:
            dst, src = tpath(tree, it['rel']), os.path.join(SNAP1, *it['rel'].split('/'))
            it['new_dirs'] = []
            if it['base'] == 'ABSENT':
                p = os.path.dirname(dst)
                while not os.path.isdir(p):
                    it['new_dirs'].append(p)
                    p = os.path.dirname(p)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
            else:
                os.chmod(dst, 0o666)
            touched.append(it)
            shutil.copyfile(src, dst)
            h = sha(dst)
            if h != it['after']:
                raise RuntimeError('%s: the copy hashes to %s, not the after %s' % (it['rel'], h[:16], it['after'][:16]))
            t = time.time()
            os.utime(dst, (t, t))
            st = os.stat(dst)
            it['size'], it['mtime_ns'] = st.st_size, st.st_mtime_ns
            w('  copied %-62s %s -> %s (%d B), mtime %s' % (
                it['rel'], 'ABSENT' if it['base'] == 'ABSENT' else it['base'][:16], h[:16], st.st_size,
                datetime.datetime.fromtimestamp(st.st_mtime).strftime('%H:%M:%S.%f')[:12]))
        bad = sorted(r for r in last if last[r] != 'DELETED' and sha(tpath(tree, r)) != last[r])
        if bad:
            raise RuntimeError('%d PATCHES row(s) fail in %s after the copies: %s' % (len(bad), tree, ', '.join(bad[:6])))
        w('  -GameSnap row check, simulated: all %d PATCHES files in %s == their last after' % (len(last), tree))
    except Exception as e:  # noqa: BLE001 (any error: roll back)
        w('ERROR: %s. Rolling back %d file(s)' % (e, len(touched)))
        for it in reversed(touched):
            dst = tpath(tree, it['rel'])
            try:
                if it['base'] == 'ABSENT':
                    if os.path.exists(dst):
                        os.chmod(dst, 0o666)
                        os.remove(dst)
                    for d in it['new_dirs']:
                        try:
                            os.rmdir(d)
                        except OSError:
                            pass
                    w('  removed %s (created by this run)' % it['rel'])
                else:
                    os.chmod(dst, 0o666)
                    shutil.copyfile(os.path.join(bk, *it['rel'].split('/')), dst)
                    t = time.time()
                    os.utime(dst, (t, t))
                    h = sha(dst)
                    w('  restored %s: %s %s' % (it['rel'], h[:16], '== base' if h == it['base'] else 'FAIL: != base'))
            except Exception as e2:  # noqa: BLE001
                w('  FAIL restoring %s: %s' % (it['rel'], e2))
        return 4
    rec = os.path.join(A2, 'B4-copies-%s.tsv' % v)
    out = ['# B4 copies (%s, %s), written %s by build/agent2/prep-b4.py --go: tree build/agent2/%s/DimensionsRecomp '
           '(level %s) <- build/agent2/snap1/DimensionsRecomp (S4a); columns: rel, base sha256 (ABSENT = new file), after '
           'sha256, size, kind, backup, mtime_ns (set to now after the hash check)' % (v, cfg['bin'], stamp, tree,
                                                                                     cfg['level'])]
    for it in items:
        out.append('\t'.join([it['rel'], it['base'], it['after'], str(it['size']), it['kind'],
                              'none (created)' if it['base'] == 'ABSENT' else
                              rr(os.path.join(bk, *it['rel'].split('/'))), str(it['mtime_ns'])]))
    with open(rec, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    notes = os.path.join(A2, 'B4-manifest-notes-%s.txt' % v)
    with open(notes, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(notes_text(v, cfg, items, stamp)) + '\n')
    for p in (rec, notes):
        w('  wrote %s (%d B, sha256 %s)' % (rr(p), os.path.getsize(p), sha(p)[:16]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--variant', choices=['off', 'native', 'both'], default='both')
    ap.add_argument('--go', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    vs = ['off', 'native'] if a.variant == 'both' else [a.variant]
    stamp = NOW.strftime('%Y-%m-%d %H:%M:%S')
    rep = os.path.join(A2, 'prep-b4-%s%s.txt' % ('go-' if a.go else '', NOW.strftime('%H%M')))
    w('prep-b4.py %s --variant %s at %s; R = %s' % ('--go' if a.go else 'dry run (read-only)', a.variant, stamp, ROOT))
    rows, s4a = patch_rows(), s4a_table()
    w('  snap1 PATCHES %s: %d rows; S4a table (apply-s4a-live.ps1): %d rows'
      % (','.join(PATCH_TAGS), len(rows), len(s4a)))
    if len(s4a) != 6:
        fail('the S4a table has %d rows, not 6' % len(s4a))
    plans = {}
    for v in vs:
        plans[v] = plan(v, VARIANTS[v], rows, s4a)
    pr = procs()
    w('')
    w('running game/ninja/clang/cmake processes: %s' % (', '.join(pr) if pr else 'none'))
    code = 0
    if not a.go:
        w('')
        w('DRY RUN: %d FAIL; %s' % (len(fails), 'READY for --go%s' % (' once the processes above end' if pr else '')
                                    if not fails else 'NOT READY'))
        code = 1 if fails else 0
    elif fails:
        w('')
        w('REFUSED (exit 2): %d check(s) failed; nothing written' % len(fails))
        code = 2
    elif pr:
        w('')
        w('REFUSED (exit 3): a game, ninja, clang or cmake process is running; nothing written')
        code = 3
    else:
        for v in vs:
            w('')
            w('[%s] --go' % v)
            code = apply(v, VARIANTS[v], plans[v][0], plans[v][1], stamp)
            if code:
                break
        w('')
        w('GO: %s' % ('done, %s' % ', '.join('%s %d files' % (v, len(plans[v][0])) for v in vs) if not code else
                      'stopped with exit %d' % code))
    for s in fails:
        w('  FAIL ' + s)
    w('wall %.1f s; report %s' % (time.time() - t0, rr(rep)))
    tmp = rep + '.new'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    os.replace(tmp, rep)
    return code


if __name__ == '__main__':
    sys.exit(main())
