#!/usr/bin/env python3
# run-ffx-a.py (M2, S5 item 2 = FFX option A trial, fsyntax only, NO bin):
#   configure a NEW build dir build/agent2/s5/ffx-a/b from snap1's rexglue-sdk source with the same preset/options
#   as snap1-sdk (build-snap.ps1:78-80) plus -DREXGLUE_FIDELITYFX_SOURCE_DIR=<snap1>/thirdparty/FidelityFX-SDK
#   (REXGLUE_ENABLE_FIDELITYFX stays OFF), check the cache vs snap1-sdk, check that -DREX_HAS_FIDELITYFX_SDK=1 is
#   on exactly the rexui compile entries, then -fsyntax-only every Release rexui entry (PCH replaced by a textual
#   -include of cmake_pch.hxx) at IDLE priority, -j4.
# Writes only build/agent2/s5/ffx-a/. snap1/ and snap1-sdk/ are read only. Never builds, never installs.
import concurrent.futures as cf, hashlib, json, os, re, shlex, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
D = os.path.join(A2, 's5', 'ffx-a')
B = os.path.join(D, 'b')
SRC = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
FFX = os.path.join(SRC, 'thirdparty', 'FidelityFX-SDK')
REF = os.path.join(A2, 'snap1-sdk')
TC = os.path.join(R, 'toolchain', 'llvm-23.1.6', 'bin')
VSC = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake'
CMAKE = os.path.join(VSC, 'CMake', 'bin', 'cmake.exe')
IDLE = 0x00000040
fw = lambda p: p.replace('\\', '/')
out, fails = [], []


def say(s):
    out.append(s)
    print(s, flush=True)


def check(what, ok, detail=''):
    say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
    if not ok:
        fails.append(what)


def finish():
    say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
    open(os.path.join(D, 'ffx-a-check.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    sys.exit(1 if fails else 0)


env = dict(os.environ)
env['PATH'] = os.pathsep.join([TC, os.path.join(VSC, 'CMake', 'bin'), os.path.join(VSC, 'Ninja'), env['PATH']])
say('start %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
check('FFX sdk/include + ffx-api/include exist in snap1',
      os.path.isdir(os.path.join(FFX, 'sdk', 'include')) and os.path.isdir(os.path.join(FFX, 'ffx-api', 'include')))

# 1. configure (skipped when b/ already has a generated build.ninja and --reuse is given)
if not ('--reuse' in sys.argv and os.path.isfile(os.path.join(B, 'build.ninja'))):
    os.makedirs(B, exist_ok=True)
    cmd = [CMAKE, '--preset', 'win-amd64', '-B', fw(B), '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
           '-DREXGLUE_BUILD_TESTS=OFF', '-DCMAKE_INSTALL_PREFIX=' + fw(os.path.join(D, 'install-never')),
           '-DREXGLUE_FIDELITYFX_SOURCE_DIR=' + fw(FFX)]
    say('configure: ' + ' '.join(cmd))
    t0 = time.time()
    with open(os.path.join(D, 'configure.log'), 'w', encoding='utf-8') as lf:
        p = subprocess.run(cmd, cwd=SRC, env=env, stdout=lf, stderr=subprocess.STDOUT, creationflags=IDLE)
    check('configure exit 0 (%.1f s)' % (time.time() - t0), p.returncode == 0)
    if fails:
        finish()


# 2. cache vs snap1-sdk (non-path entries)
def cache(p):
    d = {}
    for ln in open(os.path.join(p, 'CMakeCache.txt'), encoding='utf-8', errors='replace'):
        m = re.match(r'^([A-Za-z0-9_.+-]+):([A-Z]+)=(.*)$', ln.rstrip('\n'))
        if m and m.group(2) != 'INTERNAL' and not m.group(1).endswith('-ADVANCED'):
            d[m.group(1)] = m.group(3)
    return d


a, b = cache(REF), cache(B)
skip = lambda v: ('snap1-sdk' in v or 's5/ffx-a' in v or 'CMAKE_INSTALL_PREFIX' == v)
dif = []
for k in sorted(set(a) | set(b)):
    va, vb = a.get(k), b.get(k)
    if va != vb and not (va and vb and fw(va).replace(fw(REF), '@') == fw(vb).replace(fw(B), '@')):
        dif.append('%s: snap1-sdk=%r new=%r' % (k, va, vb))
for l in dif:
    say('    cache diff ' + l)
# CMAKE_C/CXX_COMPILER: snap1-sdk stored the bare names, the new cache the resolved paths; the ccdb check below proves
# the same compiler binary. CMAKE_RC_COMPILER (llvm-rc vs rc.exe: PATH order) only compiles .rc files, none in rexui.
expected = {'CMAKE_INSTALL_PREFIX', 'REXGLUE_FIDELITYFX_SOURCE_DIR', 'CMAKE_C_COMPILER', 'CMAKE_CXX_COMPILER',
            'CMAKE_RC_COMPILER'}
unexp = [l for l in dif if l.split(':')[0] not in expected]
check('cache == snap1-sdk except install prefix, FFX source dir, compiler spelling, RC compiler (not used by rexui)',
      not unexp, '%d unexpected' % len(unexp))

# 3. ccdb: define on exactly the rexui entries
cc = json.load(open(os.path.join(B, 'compile_commands.json'), encoding='utf-8'))
ref = json.load(open(os.path.join(REF, 'compile_commands.json'), encoding='utf-8'))
check('ccdb entry count == snap1-sdk (%d)' % len(ref), len(cc) == len(ref), str(len(cc)))
is_ui = lambda e: '/src/ui/CMakeFiles/rexui.dir/' in fw(e.get('output', '')) or \
    'src/ui/CMakeFiles/rexui.dir/' in fw(e['command'])
withdef = [e for e in cc if '-DREX_HAS_FIDELITYFX_SDK=1' in e['command']]
ui = [e for e in cc if is_ui(e)]
check('define only on rexui entries', all(is_ui(e) for e in withdef),
      '%d with define, %d rexui' % (len(withdef), len(ui)))
check('every rexui entry has the define', len(withdef) == len(ui))
rel = [e for e in ui if 'CMAKE_INTDIR=\\"Release\\"' in e['command']]
say('rexui entries: %d total, %d Release' % (len(ui), len(rel)))
check('36 Release rexui entries (35 TUs + PCH .cxx)', len(rel) == 36, str(len(rel)))
# non-rexui commands must be identical to snap1-sdk's apart from the build dir (both slash forms, any case: the PCH
# entries carry the build dir in 'file' and in the command with backslashes)
norm = lambda s, d: fw(s).lower().replace(fw(d).lower(), '@')
rk = lambda e, d: norm(e['file'], d) + '|' + e['command'].split('CMAKE_INTDIR=')[1][:12]
rmap = {rk(e, REF): norm(e['command'], REF) for e in ref}
nd = 0
for e in cc:
    if is_ui(e):
        continue
    k = rk(e, B)
    if rmap.get(k) != norm(e['command'], B):
        nd += 1
        if nd <= 3:
            say('    differs: %s' % k)
check('non-rexui compile commands identical to snap1-sdk (modulo build dir)', nd == 0, '%d differ' % nd)


# 4. fsyntax every Release rexui entry
def fsyn(e):
    args = shlex.split(e['command'], posix=False)
    args = [x.replace('\\"', '"') if x.startswith('-DREXGLUE_BUILD_CONFIG') or x.startswith('-DCMAKE_INTDIR')
            else x for x in args]
    o = []
    i = 0
    while i < len(args):
        x = args[i]
        if x in ('-o', '-MF', '-MT'):
            i += 2
            continue
        if x in ('-c', '-MD'):
            i += 1
            continue
        if x == '-Xclang' and i + 3 < len(args) and args[i + 1] == '-include-pch':
            i += 4  # drop "-Xclang -include-pch -Xclang <pch>", keep the textual -include of cmake_pch.hxx
            continue
        o.append(x)
        i += 1
    o.insert(1, '-fsyntax-only')
    t0 = time.time()
    p = subprocess.run(o, cwd=e['directory'], capture_output=True, creationflags=IDLE)
    log = (p.stdout + p.stderr).decode('utf-8', errors='replace')
    return e['file'], p.returncode, time.time() - t0, log, ' '.join(o)


t0 = time.time()
logs = []
with cf.ThreadPoolExecutor(4) as ex:
    res = list(ex.map(fsyn, rel))
nerr = 0
for f, rc, dt, log, cmdl in sorted(res):
    w = log.count('warning:')
    e = log.count('error:')
    nerr += (rc != 0)
    say('    %s rc=%d %.1fs errors=%d warnings=%d %s' % ('ok  ' if rc == 0 else 'FAIL', rc, dt, e, w,
                                                        os.path.relpath(f, SRC)))
    logs.append('==== %s rc=%d\n%s\n%s\n' % (f, rc, cmdl, log))
open(os.path.join(D, 'fsyntax.log'), 'w', encoding='utf-8').write('\n'.join(logs))
check('fsyntax all %d Release rexui entries (%.1f s wall, -j4 idle)' % (len(rel), time.time() - t0), nerr == 0,
      '%d failed' % nerr)
for n in ('compile_commands.json', 'CMakeCache.txt'):
    say('%s sha256 %s' % (n, hashlib.sha256(open(os.path.join(B, n), 'rb').read()).hexdigest().upper()[:16]))
finish()
