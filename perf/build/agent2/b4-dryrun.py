#!/usr/bin/env python3
"""b4-dryrun.py (Agent 2, task #15): read-only readiness check for devoffB4 + nativeB4, i.e. the B line + S4a
(B's batch-nolr codegen plus the 6 S4a files; #2 native only).

Builds nothing, runs no ninja/cmake/git and writes nothing in any tree. It reads the S4a table in
apply-s4a-live.ps1, the stage backups snap1-backup-{S2,S3,S3d,S4a}, the B source trees (snapB, snapB3),
the B build dirs (snapB-off, snapB3-on: CMakeCache.txt, .ninja_log, .ninja_deps, stat only), the SDK
install, the batch-nolr pin and the bin folders' MANIFEST.txt files. One thread.
[10] (added 14:24) simulates stage-snap-bin.ps1's -GameSnap row check (snap1/PATCHES-S1..S4a.tsv vs the B source
trees, after the planned copies) and checks that the extra option-B copies are no snapB-off build input (.ninja_deps,
build.ninja).
The only file it writes is the report build/agent2/b4-dryrun-<HHMM>.txt.
  python build/agent2/b4-dryrun.py              # small files hashed; bins checked by size + link count
  python build/agent2/b4-dryrun.py --full-hash  # also sha256 every bin file against its MANIFEST row (~2.3 GB)
Exit 0 = no FAIL, 1 = at least one FAIL.
"""
import datetime
import hashlib
import importlib.util
import os
import re
import shutil
import sys

sys.dont_write_bytecode = True
A2 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(A2))
FULL = '--full-hash' in sys.argv
NOW = datetime.datetime.now()
OUT = os.path.join(A2, 'b4-dryrun-%s.txt' % NOW.strftime('%H%M'))
STAGES = ['S2', 'S3', 'S3d', 'S4a']
W4B_BINS = ['devoff2-bin', 'devoffB-bin', 'devoff3-bin', 'native3d-bin', 'nativeB-bin']
S4A_BINS = ['devoff4-bin', 'native4-bin']
MANIFEST_SHA = {'devoffB-bin': '8709476F', 'devoff3-bin': 'B9C5175D', 'native3d-bin': '368F9CE6',
                'nativeB-bin': 'E5CBF30A', 'devoff4-bin': '16DCC939', 'native4-bin': '00D33D4F'}
NEW_DIRS = ['devoffB4-bin', 'nativeB4-bin', 'snapB3-off', 'snapB-backup-B4', 'snapB3-backup-S4a']
FPRINT = '/native_gpu_build_info.h'   # regenerated when a fingerprint input (shaders.cpp) changes
lines, fails, warns = [], [], []


def w(s=''):
    print(s)
    lines.append(s)


def fail(s):
    fails.append(s)
    w('  FAIL ' + s)


def warn(s):
    warns.append(s)
    w('  WARN ' + s)


def sha(p):
    if not os.path.isfile(p):
        return 'MISSING'
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def nabs(p, base=None):
    if base and not os.path.isabs(p):
        p = os.path.join(base, p)
    return os.path.normcase(os.path.normpath(p))


def mtime_s(p):
    try:
        return datetime.datetime.fromtimestamp(os.stat(p).st_mtime).strftime('%m-%d %H:%M:%S')
    except OSError:
        return 'missing'


def load_s4est():
    spec = importlib.util.spec_from_file_location('s4est', os.path.join(A2, 's4-estimate.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def s4a_table():
    with open(os.path.join(A2, 'apply-s4a-live.ps1'), encoding='utf-8') as f:
        txt = f.read()
    rows = re.findall(r"@\('([^']*)',\s*'([^']*)',\s*'([0-9A-F]{64})',\s*(\d+),\s*'([0-9A-F]{64})',\s*(\d+)\)", txt)
    return [(it, rel, b, int(bs), a, int(asz)) for it, rel, b, bs, a, asz in rows]


def sec_s4a(tab):
    w('')
    w('[1] the 6 S4a files (table parsed from apply-s4a-live.ps1: %d rows); level = before / after / other' % len(tab))
    if len(tab) != 6:
        fail('expected 6 S4a rows, found %d' % len(tab))
    for it, rel, b, bs, a, asz in tab:
        def lv(h):
            return 'before' if h == b else ('after' if h == a else ('MISSING' if h == 'MISSING' else 'other ' + h[:12]))
        h1 = sha(os.path.join(A2, 'snap1', 'DimensionsRecomp', rel))
        hb3 = sha(os.path.join(A2, 'snapB3', 'DimensionsRecomp', rel))
        hb = sha(os.path.join(A2, 'snapB', 'DimensionsRecomp', rel))
        w('  %-25s %-50s snap1 %-6s snapB3 %-6s snapB %s' % (it, rel, lv(h1), lv(hb3), lv(hb)))
        if h1 != a:
            fail('snap1 %s is not the S4a after (the copy source)' % rel)
        if hb3 != b:
            fail('snapB3 %s is not the S4a before (nativeB4 base)' % rel)
        if hb != b:
            warn('snapB %s is %s' % (rel, lv(hb)))


def stage_files():
    files = {}
    for st in STAGES:
        base = os.path.join(A2, 'snap1-backup-' + st, 'DimensionsRecomp')
        lst = []
        for dp, dn, fn in os.walk(base):
            for f in fn:
                lst.append(os.path.relpath(os.path.join(dp, f), base).replace('\\', '/'))
        files[st] = sorted(lst)
    return files


LEVEL = {'snapB': 'S2', 'snapB3': 'S3d'}


def sec_levels(files, tab):
    cache = {}

    def hh(p):
        if p not in cache:
            cache[p] = sha(p)
        return cache[p]

    allrel = sorted(set(r for st in STAGES for r in files[st]))
    w('')
    w('[2] the %d files the S2/S3/S3d/S4a applies changed (%s): is each B tree exactly at its level? expected = the'
      ' backup of the first later stage that changed the file, else snap1 now (the S4a level)'
      % (len(allrel), ', '.join('%s %d' % (st, len(files[st])) for st in STAGES)))
    need = {}
    for tree, lvl in LEVEL.items():
        li = STAGES.index(lvl)
        ok, need[tree] = 0, []
        for rel in allrel:
            exp = None
            for st in STAGES[li + 1:]:
                if rel in files[st]:
                    exp = hh(os.path.join(A2, 'snap1-backup-' + st, 'DimensionsRecomp', rel))
                    break
            if exp is None:
                exp = hh(os.path.join(A2, 'snap1', 'DimensionsRecomp', rel))
            h = hh(os.path.join(A2, tree, 'DimensionsRecomp', rel))
            if h == exp:
                ok += 1
            else:
                (fail if rel.startswith('rexlego/') else warn)(
                    '%s %s is not at the %s level (%s, expected %s)' % (tree, rel, lvl, h[:12], exp[:12]))
            if h != hh(os.path.join(A2, 'snap1', 'DimensionsRecomp', rel)):
                need[tree].append(rel)
        nl = sum(1 for r in need[tree] if r.startswith('rexlego/'))
        ns = sum(1 for r in need[tree] if r.startswith('rexglue-sdk/'))
        w('  %-6s level %-3s: %d/%d files exact; %d differ from the S4a level: %d rexlego, %d rexglue-sdk, %d other'
          % (tree, lvl, ok, len(allrel), len(need[tree]), nl, ns, len(need[tree]) - nl - ns))
    s4rels = sorted(r[1] for r in tab)
    if sorted(need['snapB3']) == s4rels:
        w('  snapB3 -> S4a level needs exactly the 6 S4a files (nativeB4 apply list) ok')
    else:
        fail('snapB3 -> S4a level needs %s, not the 6 S4a files' % ', '.join(need['snapB3']))
    todo = sorted(r for r in need['snapB'] if r.startswith('rexlego/'))
    w('  devoffB4 option B apply list (rexlego files snapB lacks; source = snap1 now, the S4a level;'
      ' snapB\'s rexglue-sdk is not built, the B trees use snap1-sdk/install):')
    for rel in todo:
        w('   %-50s snapB %s -> snap1 %s' % (rel, hh(os.path.join(A2, 'snapB', 'DimensionsRecomp', rel))[:16],
                                            hh(os.path.join(A2, 'snap1', 'DimensionsRecomp', rel))[:16]))
    return todo


def walk_rel(base, skip_top):
    res = {}
    for dp, dn, fn in os.walk(base):
        if os.path.normcase(dp) == os.path.normcase(base):
            dn[:] = [d for d in dn if d not in skip_top]
        for f in fn:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            res[os.path.relpath(p, base).replace('\\', '/')] = (st.st_size, st.st_mtime_ns)
    return res


def sec_rexlego_diff(todo):
    w('')
    w('[3] rexlego sources, snapB vs snapB3 (outside generated/ and out/; stat, then sha256 where size or mtime differ)')
    ba = os.path.join(A2, 'snapB', 'DimensionsRecomp', 'rexlego')
    bb = os.path.join(A2, 'snapB3', 'DimensionsRecomp', 'rexlego')
    skip = {'generated', 'out', '.git'}
    a, b = walk_rel(ba, skip), walk_rel(bb, skip)
    diff = []
    for rel in sorted(set(a) | set(b)):
        if rel not in a:
            diff.append((rel, 'only in snapB3'))
        elif rel not in b:
            diff.append((rel, 'only in snapB'))
        elif a[rel] != b[rel]:
            if a[rel][0] != b[rel][0] or sha(os.path.join(ba, rel)) != sha(os.path.join(bb, rel)):
                diff.append((rel, 'differs'))
    w('  %d files in snapB, %d in snapB3; %d differ:' % (len(a), len(b), len(diff)))
    todo_rel = set(r[len('rexlego/'):] for r in todo)
    rest = []
    for rel, why in diff:
        cov = rel in todo_rel
        w('   %-55s %-15s %s' % (rel, why, 'covered by the option-B apply' if cov else 'NOT covered'))
        if not cov:
            rest.append(rel)
    if rest:
        warn('%d rexlego difference(s) not covered by the option-B apply: %s' % (len(rest), ', '.join(rest[:6])))
    else:
        w('  => after the option-B apply, snapB/rexlego == snapB3/rexlego outside generated/ and out/'
          ' (so devoffB4 from snapB-off == a fresh snapB3-off build, source-wise)')
    return diff


def cache_vals(tree):
    d = {}
    with open(os.path.join(A2, tree, 'CMakeCache.txt'), encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'^([A-Za-z0-9_]+):[A-Z]+=(.*)$', line.rstrip('\r\n'))
            if m:
                d[m.group(1)] = m.group(2)
    return d


def sec_cache():
    w('')
    w('[4] B build dirs: CMakeCache.txt')
    exp = {'snapB-off': ('snapB', 'OFF'), 'snapB3-on': ('snapB3', 'ON')}
    for tree, (src, nat) in exp.items():
        c = cache_vals(tree)
        checks = [
            ('CMAKE_HOME_DIRECTORY', nabs(c.get('CMAKE_HOME_DIRECTORY', '')) ==
             nabs(os.path.join(A2, src, 'DimensionsRecomp', 'rexlego')), c.get('CMAKE_HOME_DIRECTORY', '')),
            ('CMAKE_PREFIX_PATH', nabs(c.get('CMAKE_PREFIX_PATH', '')) == nabs(os.path.join(A2, 'snap1-sdk', 'install')),
             c.get('CMAKE_PREFIX_PATH', '')),
            ('LEGODIMENSIONS_NATIVE_GPU', c.get('LEGODIMENSIONS_NATIVE_GPU') == nat, c.get('LEGODIMENSIONS_NATIVE_GPU')),
            ('CMAKE_BUILD_TYPE', c.get('CMAKE_BUILD_TYPE') == 'Release', c.get('CMAKE_BUILD_TYPE')),
            ('REXGLUE_HOST_CODEGEN_EXECUTABLE',
             c.get('REXGLUE_HOST_CODEGEN_EXECUTABLE', '').lower().endswith('codegen-frozen2.exe'),
             os.path.basename(c.get('REXGLUE_HOST_CODEGEN_EXECUTABLE', ''))),
        ]
        w('  %-10s %s' % (tree, '; '.join('%s=%s %s' % (k, (v or '')[-60:], 'ok' if ok else 'BAD') for k, ok, v in checks)))
        for k, ok, v in checks:
            if not ok:
                fail('%s %s = %s' % (tree, k, v))


def manifest_rows(d):
    rows = {}
    p = os.path.join(d, 'MANIFEST.txt')
    if not os.path.isfile(p):
        return rows
    with open(p, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.rstrip('\r\n').split('\t')
            if (len(parts) >= 4 and parts[1].isdigit() and re.fullmatch(r'[0-9A-Fa-f]{64}', parts[3])
                    and '/' not in parts[0] and '\\' not in parts[0]):
                rows.setdefault(parts[0], (int(parts[1]), parts[2], parts[3].upper()))
    return rows


def gen_compare(tree_gen, ref_gen):
    a, b = walk_rel(tree_gen, set()), walk_rel(ref_gen, set())
    same = sum(1 for k in a if k in b and a[k][0] == b[k][0])
    sized = sorted(k for k in a if k in b and a[k][0] != b[k][0])
    return len(a), len(b), same, sized, sorted(set(a) - set(b)), sorted(set(b) - set(a))


def sec_sdk_pins():
    w('')
    w('[5] SDK install (snap1-sdk/install = the prefix of both B trees), relink/recompile triggers, batch-nolr pin')
    inst = os.path.join(A2, 'snap1-sdk', 'install')
    m4 = manifest_rows(os.path.join(A2, 'devoff4-bin'))
    mn4 = manifest_rows(os.path.join(A2, 'native4-bin'))
    for dll in ('rexruntime.dll', 'rexgpu-xenos.dll', 'TracyClient.dll'):
        h = sha(os.path.join(inst, 'bin', dll))
        refs = []
        for nm, rows in (('devoff4-bin', m4), ('native4-bin', mn4)):
            r = rows.get(dll)
            st = 'same' if (r and r[2] == h) else ('DIFFERS' if r else 'no row')
            refs.append('%s %s' % (nm, st))
            if r and r[2] != h:
                fail('install/bin/%s != %s row (the install is no longer the S4a SDK)' % (dll, nm))
        w('  install/bin/%-17s %s  %s' % (dll, h[:16], ', '.join(refs)))
    libs = []
    for dp, dn, fn in os.walk(os.path.join(inst, 'lib')):
        for f in fn:
            if f.lower().endswith('.lib'):
                p = os.path.join(dp, f)
                libs.append((os.stat(p).st_mtime, f))
    newest = max(libs) if libs else (0, '-')
    w('  newest install .lib: %s %s' % (newest[1], datetime.datetime.fromtimestamp(newest[0]).strftime('%m-%d %H:%M:%S')
                                         if newest[0] else '-'))
    hdrs = []
    for dp, dn, fn in os.walk(os.path.join(inst, 'include')):
        for f in fn:
            p = os.path.join(dp, f)
            hdrs.append((os.stat(p).st_mtime, os.path.relpath(p, inst).replace('\\', '/')))
    for tree in ('snapB-off', 'snapB3-on'):
        exe = os.path.join(A2, tree, 'legodimensions.exe')
        if not os.path.isfile(exe):
            warn('%s/legodimensions.exe missing' % tree)
            continue
        em = os.stat(exe).st_mtime
        newer = sorted((h for h in hdrs if h[0] > em), reverse=True)
        w('  %s exe %s: relink %s; %d installed header(s) newer than the exe%s' % (
            tree, mtime_s(exe), 'expected (newer SDK .lib)' if newest[0] > em else 'not forced by the SDK',
            len(newer), (': ' + ', '.join('%s (%s)' % (r, datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M'))
                                         for t, r in newer[:8])) if newer else ''))
    bn = os.path.join(ROOT, 'build', 'agent9', 'install', 'batch-nolr')
    hs = sha(os.path.join(bn, 'SHA256SUMS.txt'))
    ht = sha(os.path.join(bn, 'legodimensions_config.toml'))
    w('  batch-nolr SHA256SUMS.txt %s (pin 24CE1493) %s; legodimensions_config.toml %s (pin E60EAF1C) %s' % (
        hs[:16], 'ok' if hs.startswith('24CE1493') else 'BAD', ht[:16], 'ok' if ht.startswith('E60EAF1C') else 'BAD'))
    if not hs.startswith('24CE1493'):
        fail('batch-nolr SHA256SUMS.txt changed')
    if not ht.startswith('E60EAF1C'):
        fail('batch-nolr legodimensions_config.toml changed')
    for tree in ('snapB', 'snapB3'):
        rl = os.path.join(A2, tree, 'DimensionsRecomp', 'rexlego')
        h = sha(os.path.join(rl, 'legodimensions_config.toml'))
        na, nb, same, sized, only_t, only_r = gen_compare(os.path.join(rl, 'generated'), os.path.join(bn, 'generated'))
        w('  %-6s config.toml %s %s; generated/ %d files vs batch-nolr %d: %d same size, size differs: %s; only in tree: %d;'
          ' only in batch-nolr: %d' % (tree, h[:16], 'ok' if h == ht else 'BAD', na, nb, same,
                                        ', '.join(sized[:4]) or '-', len(only_t), len(only_r)))
        if h != ht:
            fail('%s legodimensions_config.toml != batch-nolr' % tree)
        if [s for s in sized if not s.endswith('codegen.d')] or only_r:
            fail('%s generated/ differs from batch-nolr beyond codegen.d (gen-check would stop the build)' % tree)


def sec_bins():
    w('')
    w('[6] bins that must stay byte-identical (W4b inputs + S4a bins): MANIFEST rows vs files (size, link count%s)'
      % (', sha256' if FULL else '; sha256 only with --full-hash'))
    for b in W4B_BINS + S4A_BINS:
        d = os.path.join(A2, b)
        if not os.path.isdir(d):
            fail('%s missing' % b)
            continue
        rows = manifest_rows(d)
        mh = sha(os.path.join(d, 'MANIFEST.txt'))
        exp = MANIFEST_SHA.get(b)
        okm = exp is None or mh.startswith(exp)
        files = sorted(f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and f != 'MANIFEST.txt')
        probs, nlinks = [], set()
        for f in files:
            p = os.path.join(d, f)
            st = os.stat(p)
            nlinks.add(st.st_nlink)
            r = rows.get(f)
            if r is None:
                probs.append('%s: no MANIFEST row' % f)
                continue
            if st.st_size != r[0]:
                probs.append('%s: size %d != %d' % (f, st.st_size, r[0]))
            if FULL and sha(p) != r[2]:
                probs.append('%s: sha256 differs' % f)
        for f in rows:
            if f not in files:
                probs.append('%s: row without file' % f)
        exe = rows.get('legodimensions.exe')
        w('  %-12s MANIFEST %s%s; exe %s; %d files = %d rows, sizes %s; hardlink counts %s' % (
            b, mh[:16], '' if exp is None else (' (== %s)' % exp if okm else ' (expected %s)' % exp),
            exe[2][:16] if exe else '-', len(files), len(rows), 'ok' if not probs else '; '.join(probs),
            ','.join(str(n) for n in sorted(nlinks))))
        if not okm:
            fail('%s MANIFEST.txt changed' % b)
        for p in probs:
            fail('%s %s' % (b, p))
    w('  (hardlink counts > 1 on bin files = other agents\' run-folder links to the staged copies; the B4 builds write'
      ' only the build dirs below and the new bin folders, so they cannot reach them)')
    for tree in ('snapB-off', 'snapB3-on'):
        p = os.path.join(A2, tree, 'legodimensions.exe')
        if os.path.isfile(p):
            st = os.stat(p)
            w('  %s/legodimensions.exe %d B, %s, %d link(s) (must be 1)' % (tree, st.st_size, mtime_s(p), st.st_nlink))
            if st.st_nlink != 1:
                fail('%s/legodimensions.exe has %d links (a rebuild would change a linked copy)' % (tree, st.st_nlink))


def sec_new_dirs():
    w('')
    w('[7] proposed new folders must not exist yet')
    for n in NEW_DIRS:
        p = os.path.join(A2, n)
        ex = os.path.exists(p)
        w('  build/agent2/%-18s %s' % (n, 'EXISTS' if ex else 'absent (ok)'))
        if ex:
            fail('build/agent2/%s already exists' % n)


def predict(tree, planned_abs, planned_suffix, s4, label):
    w('')
    w('[8] %s (%s): ninja-style dirty prediction from .ninja_deps + stat (compile edges; link/custom edges have no'
      ' deps rows)' % (tree, label))
    tdir = os.path.join(A2, tree)
    head, last, runs = s4.load_log(tree)
    ver, paths, deps, bad = s4.load_deps(tree)
    absn = [nabs(p, tdir) for p in paths]
    mt = {}

    def mtime(i):
        if i not in mt:
            try:
                mt[i] = os.stat(absn[i]).st_mtime_ns
            except OSError:
                mt[i] = None
        return mt[i]

    plan = set(nabs(p) for p in planned_abs)
    psuf = [s.lower() for s in planned_suffix]
    planned_ids = set(i for i, a in enumerate(absn)
                      if a in plan or any(a.replace('\\', '/').endswith(s) for s in psuf))
    reason = {}
    for o, ins in deps.items():
        om = mtime(o)
        if om is None:
            reason[o] = 'output missing'
            continue
        for i in ins:
            im = mtime(i)
            if im is None:
                reason[o] = 'input missing: ' + paths[i]
                break
            if im > om:
                reason[o] = 'newer input: ' + paths[i]
                break

    def close(seed_dirty, seed_paths):
        dirty = set(seed_dirty)
        changed = set(seed_paths) | dirty
        grew = True
        while grew:
            grew = False
            for o, ins in deps.items():
                if o not in dirty and not changed.isdisjoint(ins):
                    dirty.add(o)
                    changed.add(o)
                    grew = True
        return dirty

    def cost(ds):
        rows, unknown = [], 0
        for o in ds:
            e = last.get(s4.norm(paths[o]))
            if e is None:
                unknown += 1
                continue
            rows.append((e[0], paths[o]))
        rows.sort(key=lambda r: -r[0])
        work = sum(r[0] for r in rows) / 1000.0
        pch = sum(r[0] for r in rows if 'cmake_pch' in s4.norm(r[1])) / 1000.0
        longest = max([r[0] for r in rows if 'cmake_pch' not in s4.norm(r[1])] or [0]) / 1000.0
        return rows, unknown, work, pch + max((work - pch) / 10.0, longest)

    full = max(runs, key=lambda r: r['n']) if runs else None
    w('  log: %d outputs, %d runs; largest run %d edges, wall %.1f s (ended %s); deps v%d: %d paths, %d records, %d bad'
      % (len(last), len(runs), full['n'] if full else 0, (full['end'] - full['start']) / 1000.0 if full else 0,
         s4.ts_local(full['mt']) if full else '-', ver, len(paths), len(deps), bad))
    d0 = close(set(reason), set())
    r0, u0, wk0, es0 = cost(d0)
    w('  drift now (no change applied): %d edge(s) dirty (+%d no log entry), work %.0f s, est compile wall ~%.0f s'
      % (len(r0), u0, wk0, es0))
    top = {}
    for o in reason:
        top[reason[o]] = top.get(reason[o], 0) + 1
    for k, n in sorted(top.items(), key=lambda kv: -kv[1])[:6]:
        w('     %4d x %s' % (n, k))
    d1 = close(set(reason), planned_ids)
    r1, u1, wk1, es1 = cost(d1)
    w('  with the planned apply (%d file(s) + %s; %d dep path(s) matched): %d edge(s) (+%d no log entry), work %.0f s,'
      ' est compile wall at -j10 ~%.0f s' % (len(planned_abs), ', '.join(planned_suffix) or 'no suffix',
                                             len(planned_ids), len(r1), u1, wk1, es1))
    for d, p in r1[:8]:
        w('     %7.1f s  %s' % (d / 1000.0, p))
    if len(r1) > 8:
        w('     ... %d more' % (len(r1) - 8))
    links = [(v[0] / 1000.0, v[2]) for k, v in last.items() if k.endswith(('legodimensions.exe', 'prelink.obj'))
             or 'prelink' in k]
    for d, p in sorted(links, key=lambda x: -x[0])[:4]:
        w('  link-side edge (last run): %7.1f s  %s' % (d, p))
    return {'tree': tree, 'drift': len(r0), 'edges': len(r1), 'work': wk1, 'est': es1,
            'link': max([d for d, p in links if p.lower().endswith('legodimensions.exe')] or [0]),
            'full_wall': (full['end'] - full['start']) / 1000.0 if full else 0, 'full_n': full['n'] if full else 0}


PATCH_TAGS = ['S1', 'S2', 'S3', 'S3d', 'S4a']   # the -PatchTagList run-s4a.ps1 gives stage-snap-bin.ps1


def load_patch_rows():
    """snap1/PATCHES-<tag>.tsv rows in PATCH_TAGS order; the last row per file wins (stage-snap-bin L176-184)"""
    last, n = {}, 0
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
                if len(c) < 3:
                    continue
                n += 1
                last[c[0]] = (t, c[1].strip().upper(), c[2].strip().upper())
    return n, last


def ninja_text_refs(tree, rels):
    """rels named anywhere in <tree>/build.ninja (edges, implicit deps, the RERUN_CMAKE configure deps); ninja escapes
    ':' as '$:'; matched by the '/dimensionsrecomp/<rel>' tail, case-insensitive"""
    tails = {r: '/dimensionsrecomp/' + r.lower() for r in rels}
    hit = set()
    with open(os.path.join(A2, tree, 'build.ninja'), encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'imensions' not in line:
                continue
            ln = line.replace('$:', ':').replace('\\', '/').lower()
            for r, t in tails.items():
                if r not in hit and t in ln:
                    hit.add(r)
    return hit


def sec_stage_gate(tab, todo, s4):
    w('')
    w('[10] stage-snap-bin.ps1 -GameSnap row check (L188-195), simulated: with -PatchTagList %s every PATCHES row\'s'
      ' file in the game snapshot tree must hash == its last after (a planned copy counts as its snap1 hash)'
      % ','.join(PATCH_TAGS))
    n, last = load_patch_rows()
    rows = dict((r, v) for r, v in last.items() if v[2] != 'DELETED')
    s1 = dict((r, sha(os.path.join(A2, 'snap1', 'DimensionsRecomp', r))) for r in rows)
    bad1 = sorted(r for r in rows if s1[r] != rows[r][2])
    w('  %d rows, %d files (last row per file), %d with after DELETED; snap1 == last after %d/%d %s'
      % (n, len(last), len(last) - len(rows), len(rows) - len(bad1), len(rows), 'ok' if not bad1 else 'BAD'))
    for r in bad1:
        fail('snap1 %s is %s, not its last PATCHES after %s' % (r, s1[r][:12], rows[r][2][:12]))

    def sim(tree, applied):
        return sorted(r for r in rows if (s1[r] if r in applied else
                                          sha(os.path.join(A2, tree, 'DimensionsRecomp', r))) != rows[r][2])

    b3 = sim('snapB3', set(t[1] for t in tab))
    w('  nativeB4 and option A (-GameSnap snapB3, after the 6 S4a copies): %d row(s) fail%s'
      % (len(b3), ' (ok)' if not b3 else ': ' + ', '.join(b3[:8])))
    for r in b3:
        fail('snapB3 + the 6 S4a files: gate row %s fails' % r)
    bb = sim('snapB', set(todo))
    nl = sum(1 for r in bb if r.startswith('rexlego/'))
    ns = sum(1 for r in bb if r.startswith('rexglue-sdk/'))
    w('  devoffB4 option B with only the %d rexlego copies (-GameSnap snapB): %d row(s) would FAIL the gate: %d rexlego,'
      ' %d rexglue-sdk, %d other' % (len(todo), len(bb), nl, ns, len(bb) - nl - ns))
    if nl:
        fail('option B: %d rexlego gate row(s) fail even with the planned copies: %s' % (nl, ', '.join(
            r for r in bb if r.startswith('rexlego/'))))
    absent = [r for r in bb if not os.path.isfile(os.path.join(A2, 'snapB', 'DimensionsRecomp', r))]
    for r in bb:
        if not r.startswith('rexglue-sdk/'):
            w('     %-55s snapB %s -> snap1 %s (row %s)' % (r, sha(os.path.join(A2, 'snapB', 'DimensionsRecomp', r))[:12],
                                                        s1[r][:12], rows[r][0]))
    full = sim('snapB', set(todo) | set(bb))
    w('  => option B apply list = the %d rexlego files + these %d (%d absent in snapB, created by the copy): %d file(s);'
      ' gate rows failing after it: %d%s' % (len(todo), len(bb), len(absent), len(todo) + len(bb), len(full),
                                             ' (ok)' if not full else ''))
    for r in full:
        fail('option B with the full list: gate row %s still fails' % r)
    extra = [r for r in bb if not r.startswith('rexlego/')]
    tdir = os.path.join(A2, 'snapB-off')
    ver, paths, deps, nbad = s4.load_deps('snapB-off')
    tails = dict((r, '/dimensionsrecomp/' + r.lower()) for r in extra)
    dep_hits, outside = set(), set()
    for p in paths:
        q = nabs(p, tdir).replace('\\', '/').lower()
        if '/snapb/dimensionsrecomp/' in q and '/snapb/dimensionsrecomp/rexlego/' not in q:
            outside.add(q.split('/snapb/dimensionsrecomp/', 1)[1].split('/', 1)[0])
        for r, t in tails.items():
            if q.endswith(t):
                dep_hits.add(r)
    nin = ninja_text_refs('snapB-off', extra)
    w('  build neutrality of the %d non-rexlego copies in snapB-off: in .ninja_deps %d, named in build.ninja %d%s;'
      ' snapB-off deps outside snapB/rexlego: %s' % (len(extra), len(dep_hits), len(nin),
                                                     ' (ok: no compile, link or configure input)'
                                                     if not dep_hits and not nin else '',
                                                     ', '.join(sorted(outside)) or 'none'))
    for r in sorted(dep_hits | nin):
        fail('option B extra copy %s is a snapB-off build input (%s)' % (r, 'deps' if r in dep_hits else 'build.ninja'))
    return {'b3': len(b3), 'bb4': len(bb), 'full': len(todo) + len(bb), 'after': len(full),
            'neutral': not dep_hits and not nin}


def main():
    w('b4-dryrun.py report, %s (read-only%s); R = %s' % (NOW.strftime('%Y-%m-%d %H:%M:%S'),
                                                       ', --full-hash' if FULL else '', ROOT))
    s4 = load_s4est()
    tab = s4a_table()
    sec_s4a(tab)
    todo = sec_levels(stage_files(), tab)
    sec_rexlego_diff(todo)
    sec_cache()
    sec_sdk_pins()
    sec_bins()
    sec_new_dirs()
    pb3 = predict('snapB3-on', [os.path.join(A2, 'snapB3', 'DimensionsRecomp', r[1]) for r in tab], [FPRINT], s4,
                  'nativeB4: the 6 S4a files applied to snapB3')
    pb = predict('snapB-off', [os.path.join(A2, 'snapB', 'DimensionsRecomp', r) for r in todo], [], s4,
                 'devoffB4 option B: the rexlego apply list applied to snapB')
    free = shutil.disk_usage(ROOT).free / 2 ** 30
    w('')
    w('[9] free disk: %.1f GiB' % free)
    sg = sec_stage_gate(tab, todo, s4)
    w('')
    w('SUMMARY: %d FAIL, %d WARN' % (len(fails), len(warns)))
    for p in (pb3, pb):
        w('  %-9s predicted %d compile edge(s), est ~%.0f s at -j10, + exe link (last %.0f s); drift alone %d edge(s);'
          ' full build for reference: %d edges in %.0f s' % (p['tree'], p['edges'], p['est'], p['link'], p['drift'],
                                                             p['full_n'], p['full_wall']))
    w('  stage gate: nativeB4/option A %d failing row(s); option B needs %d copies (4-file list alone: %d failing rows),'
      ' then %d failing; extra copies build-neutral: %s' % (sg['b3'], sg['full'], sg['bb4'], sg['after'],
                                                            'yes' if sg['neutral'] else 'NO'))
    for s in fails:
        w('  FAIL ' + s)
    for s in warns:
        w('  WARN ' + s)
    tmp = OUT + '.new'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    os.replace(tmp, OUT)
    print('report: %s' % OUT)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
