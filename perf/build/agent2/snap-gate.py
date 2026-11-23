"""Agent 2 - gate for a snapshot game tree (dev OFF / ON builds from snap1; build B from snapB). Exit 0 = pass.
Checks, before anything compiles:
  1. every -I/-isystem/-iquote/-idirafter/-imsvc dir under the workspace is inside the snapshot (build/agent2/snap1;
     with --snap-dir only that DimensionsRecomp copy), snap1-sdk (the SDK build and install) or the game tree; none is
     under build/sdk, baseline/ or the live DimensionsRecomp tree;
  2. rexglue_DIR in the game cache is snap1-sdk/install/lib/cmake/rexglue;
  3. installed SDK headers hash-equal the snap1 sources the SDK was built from (include/rex/** and the fmt/spdlog/simde
     copies); configure_file outputs (include/rex/version.h) hash-equal snap1-sdk's own configure output instead;
  4. the DB's generated TUs are exactly the sources listed in <snapshot>/rexlego/generated/default/sources.cmake
     (snap1: 440 = 438 TUs + init + register; Agent 9's batch-nolr: 432), and their include dirs contain
     snap1-sdk/install/include. (Until 23:40 this was a fixed count of 440.)
Usage: python build\\agent2\\snap-gate.py [game_tree] [--snap-dir DIR]
  defaults: game tree build/agent2/snap1-off; snapshot build/agent2/snap1/DimensionsRecomp (allowed root build/agent2/snap1)
  build B:  python build\\agent2\\snap-gate.py build\\agent2\\snapB-off --snap-dir build\\agent2\\snapB\\DimensionsRecomp
"""
import argparse, hashlib, json, os, re, sys

R = r'<workspace>'
ap = argparse.ArgumentParser()
ap.add_argument('game', nargs='?', default=os.path.join(R, r'build\agent2\snap1-off'))
ap.add_argument('--snap-dir', default='', help='the DimensionsRecomp copy the game tree builds (default: snap1)')
args = ap.parse_args()
GAME = args.game
SNAP_DIR = os.path.abspath(args.snap_dir) if args.snap_dir else os.path.join(R, r'build\agent2\snap1\DimensionsRecomp')
SNAP_ROOT = SNAP_DIR if args.snap_dir else os.path.join(R, r'build\agent2\snap1')
GEN_DEFAULT = os.path.join(SNAP_DIR, r'rexlego\generated\default')
SNAP_SDK = os.path.join(R, r'build\agent2\snap1\DimensionsRecomp\rexglue-sdk')
INST = os.path.join(R, r'build\agent2\snap1-sdk\install')
ALLOWED = [SNAP_ROOT, os.path.join(R, r'build\agent2\snap1-sdk'), GAME]


def norm(p):
    return os.path.normcase(os.path.normpath(p.strip('"')))


def under(p, roots):
    return any(p == norm(r) or p.startswith(norm(r) + os.sep) for r in roots)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


fails = []
listed, src_err = [], None
try:
    with open(os.path.join(GEN_DEFAULT, 'sources.cmake'), encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            m = re.search(r'\$\{CMAKE_CURRENT_LIST_DIR\}/(\S+?\.cpp)', line)
            if m:
                listed.append(norm(os.path.join(GEN_DEFAULT, m.group(1))))
except OSError as ex:
    src_err = str(ex)
db = json.load(open(os.path.join(GAME, 'compile_commands.json'), encoding='utf-8'))
inc_re = re.compile(r'(?:^|\s)(?:-I|-isystem|-iquote|-idirafter|-imsvc|/I)\s*("[^"]+"|\S+)')
dirs, gen_dirs, n_gen, gen_files = {}, None, 0, set()
for e in db:
    cmd = e.get('command') or ' '.join(e.get('arguments', []))
    ds = [norm(os.path.join(e['directory'], m.group(1).strip('"'))) for m in inc_re.finditer(cmd)]
    for d in ds:
        dirs[d] = dirs.get(d, 0) + 1
    f = e['file'].replace('\\', '/')
    if '/generated/' in f and '/legodimensions_' in f and f.endswith('.cpp'):
        n_gen += 1
        gen_files.add(norm(os.path.join(e['directory'], e['file'])))
        if gen_dirs is None:
            gen_dirs = ds
ws = norm(R)
print('# snap-gate %s: %d DB entries, %d generated TUs (sources.cmake lists %d), %d distinct include dirs; snapshot %s'
      % (GAME, len(db), n_gen, len(listed), len(dirs), SNAP_DIR))
for d, n in sorted(dirs.items()):
    if d.startswith(ws + os.sep):
        ok = under(d, ALLOWED)
        print('%-4s %5d  %s' % ('ok' if ok else 'BAD', n, d))
        if not ok:
            fails.append('include dir outside the snapshot trees: ' + d)
    else:
        print('ext  %5d  %s' % (n, d))
want_gen = set(listed)
if src_err:
    fails.append('cannot read %s: %s' % (os.path.join(GEN_DEFAULT, 'sources.cmake'), src_err))
elif not listed:
    fails.append('sources.cmake lists no sources')
elif n_gen != len(listed) or gen_files != want_gen:
    miss, extra = sorted(want_gen - gen_files), sorted(gen_files - want_gen)
    fails.append('expected the %d generated TUs listed in sources.cmake, found %d (%d missing, %d extra; e.g. %s)'
                 % (len(listed), n_gen, len(miss), len(extra), (miss + extra)[:2]))
if not gen_dirs or norm(os.path.join(INST, 'include')) not in gen_dirs:
    fails.append('generated TUs do not use snap1-sdk/install/include')

cache = open(os.path.join(GAME, 'CMakeCache.txt'), encoding='utf-8', errors='replace').read()
m = re.search(r'^rexglue_DIR:PATH=(.*)$', cache, re.M)
want = norm(os.path.join(INST, r'lib\cmake\rexglue'))
got = norm(m.group(1)) if m else '(not set)'
print('rexglue_DIR: %s (%s)' % (got, 'ok' if got == want else 'BAD'))
if got != want:
    fails.append('rexglue_DIR is %s' % got)

groups = [('rex', os.path.join(INST, r'include\rex'), os.path.join(SNAP_SDK, r'include\rex')),
          ('fmt', os.path.join(INST, r'include\fmt'), os.path.join(SNAP_SDK, r'thirdparty\fmt\include\fmt')),
          ('spdlog', os.path.join(INST, r'include\spdlog'), os.path.join(SNAP_SDK, r'thirdparty\spdlog\include\spdlog')),
          ('simde', os.path.join(INST, r'include\simde'), os.path.join(SNAP_SDK, r'thirdparty\simde\simde'))]
# 20:53 fix: configure_file outputs (rexglue-sdk/CMakeLists.txt: include/rex/version.h.in -> <SDK build>/include/rex/
# version.h) are installed from the SDK build dir, not the source tree. They pass when the snapshot has <rel>.in and the
# installed copy hash-equals snap1-sdk's own configure output. (The S0d gate failed on version.h at 20:11; the
# `start /affinity` wrapper hid its exit code.)
SDK_BIN = os.path.join(R, r'build\agent2\snap1-sdk')
for name, inst, src in groups:
    if not os.path.isdir(inst):
        print('headers %-6s: no installed copy at %s' % (name, inst))
        continue
    n = same = gen = 0
    bad = []
    for dp, dn, fn in os.walk(inst):
        for f in fn:
            ip = os.path.join(dp, f)
            rel = os.path.relpath(ip, inst)
            sp = os.path.join(src, rel)
            bp = os.path.join(SDK_BIN, 'include', name, rel)
            n += 1
            if os.path.isfile(sp) and sha(sp) == sha(ip):
                same += 1
            elif (not os.path.exists(sp) and os.path.isfile(sp + '.in') and os.path.isfile(bp)
                  and sha(bp) == sha(ip)):
                gen += 1
                print('   configure-generated: %s == snap1-sdk\\include\\%s\\%s (from the snapshot\'s %s.in)'
                      % (rel, name, rel, rel))
            else:
                bad.append(rel)
    print('headers %-6s: %d installed, %d hash-equal to the snapshot, %d configure-generated, %d differ/missing'
          % (name, n, same, gen, len(bad)))
    for b in bad[:20]:
        print('   differs/missing: ' + b)
    if bad:
        fails.append('%d installed %s headers differ from the snapshot' % (len(bad), name))

print('RESULT: ' + ('PASS' if not fails else 'FAIL'))
for f in fails:
    print('  - ' + f)
sys.exit(0 if not fails else 1)
