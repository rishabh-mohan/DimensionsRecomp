#!/usr/bin/env python3
# native6pack.py - M16 (S5), copy of native5pack.py 7DDFB8B9 (frozen, N6) with 5 changes: names native6pack in the
# log / MANIFEST title / MANIFEST note; default --bin-out native6pack-bin; S1: bin re-checks PINS_BIN and diffs the
# top-level listing of the watched dirs after stage + verify-bins (binwork side-effects.txt, gated); ON fingerprint
# gates also against native5pack a349d5292f67b127; N1 header fix (no LATEST-pack.txt in the pack outputs).
# native5pack.py itself: native4bp.py 37FD3989 with no LATEST-pack.txt / LATEST-bin.txt writes and --pack-run
# required for bin (no LATEST fallback); everything else is native4bp.py unchanged.
# native4bp.py - E16.1 (S5 phase 0.4b), build/agent16/pack: dumped placement containers -> tools/gpu-aot ->
# native4bp AOT pack -> native4bp bin. Launch through native4bp.ps1 (dot-sources env\devshell.ps1 so clang++
# and the MSVC env are on PATH; sets Idle priority + affinity 0x3 first so every child inherits them).
#
#   native4bp.ps1 plan [--input <pack-input dir>] [--exclude NAME ...]
#   native4bp.ps1 pack [--input <pack-input dir>] [--exclude NAME ...]          -> pack\run-<stamp>\
#   native4bp.ps1 bin  [--pack-run <pack\run-<stamp>>] [--bin-out native4bp-bin] [--no-ctl] -> pack\binwork-<stamp>\
#                                                                               + pack\<bin-out>\ (staged)
# plan: writes only pack\plan-<stamp>.txt. Re-checks every tool/input pin, prechecks the input containers in
#       place (read-only) and prints every command of pack and bin.
# pack: the s35 run_pack.ps1 flow, generalized: stage (4 pinned s35 containers + every container of --input,
#       verified against its SHA256SUMS.txt, de-duplicated by sha256, placement-raw refused, default exclusions
#       logged) -> gradient_compiler (DXIL only) -> microcode indexer -> merge over the snap1 index 2DB85917 ->
#       check_pack.py prelookup -> production lookup (runtime cache, then + main cache) -> check_pack.py post ->
#       pin re-check, watched-dir listing diff, SHA256SUMS.txt (no pack\LATEST-pack.txt write).
# bin:  the build-final2 nat-leg recipe (recompile.py + relink.py UNCHANGED, objects of build/agent2/snap1-on,
#       outputs only under binwork): prelink runtime exe relink with the new runtime cache -> run it ->
#       embed_linked_bank.py --runtime -> fingerprint (fp-on.cmake with the 3 AOT inputs swapped) -> recompile
#       7 TUs (index, runtime_shader_cache, runtime_linked_shader_cache, device, pipeline_library, shader_archive,
#       final2 shaders.cpp overlay) with --include-first <gen> -> relink legodimensions.exe (+ runtime linked-bank.obj)
#       -> gates -> stage-variant.py on nativefinal2-bin -> verify-bins.py -> PINS_BIN re-check + watched-dir listing
#       diff (S1). With CTL (default) every step is first
#       run with the shipped inputs and must reproduce nativefinal2 (exe+map equal except TimeDateStamp).
# HARD RULES baked in: every write is asserted inside build/agent16/pack; HOLD file (perf-notes/WINDOW-HOLD.txt)
# refuses a start; TMP/TEMP point inside the run dir; PYTHONDONTWRITEBYTECODE=1; jobs <= 2; Idle priority.
import argparse, ctypes, datetime, hashlib, json, os, re, shutil, subprocess, sys, time

W = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
PACK = os.path.join(W, 'build', 'agent16', 'pack')
HOLD = os.path.join(W, 'perf-notes', 'WINDOW-HOLD.txt')
A2 = os.path.join(W, 'build', 'agent2')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
SNAPON = os.path.join(A2, 'snap1-on')
OV = os.path.join(A2, 'final2', 'b', 'DimensionsRecomp')
NF2 = os.path.join(A2, 'nativefinal2-bin')
CMAKE = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
PY = sys.executable
IDLE = 0x00000040
NOWIN = 0x08000000
FP_OLD = '1616ce65e973c583'
FP_N5 = 'a349d5292f67b127'  # native5pack-bin (MANIFEST 787CD694); the ON fp must differ from it too
S35_DIR = os.path.join(W, r'build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps\placement-containers')
S35 = {
    'vs-ACAF01F01E1C03D2.bin': '6C4F65C3161DF6BEE23F9C551F34971D60275BB49C3DB6327CFF9084F4317A66',
    'ps-75A4D1ABA62F7594.bin': '09D05274AFBC26A2605D0B91E5C2A0E0C95303C4C0C84F4D463105EB678D66EE',
    'vs-CCD7655302B54D80.bin': 'F4EE30B28DEE9E4AB5AE2E9204D54195A0AC9D8D5497B7F2C8FAC11D90EEC65E',
    'ps-E81FD692C3AB35E1.bin': '58B4FA21E35500529895AA400F4B307F0DD09BBBBDB71F5C7C8E8748B31170F1',
}
# create-path ("root") dumps that cannot go through the placement flow
DEFAULT_EXCLUDE = {
    'vs-A58EBA123EFB541C.bin': 'memexport VS (create path): gradient_compiler rejects memexport; not a placement '
                               'container flow',
    'ps-93B9F93B535E7CCA.bin': '156 B create-path dump, not a placement container (no virtual/physical layout)',
}
P = lambda *a: os.path.join(W, *a)
PINS_PACK = [
    ('gradient', r'build\agent6\aot\gradient-build\gradient_compiler.exe', '705980C4F6071E9B675DFBB57A33ED64C0C74BA6F8172FD7094850A76371A653'),
    ('dxcompiler', r'build\agent6\aot\gradient-build\dxcompiler.dll', '0689E2FEE0A1C9DF8662A59680469F24E2A3AD7CE6BBBCC9284F7A83172BFC59'),
    ('dxil', r'build\agent6\aot\gradient-build\dxil.dll', '64BE2368211D257A038A7D4EA6BB3E24C878EB8D588C7B8414FCCF759B69C2AC'),
    ('fmt', r'build\agent6\aot\gradient-build\fmt.dll', 'BB89FF51186F9E8F8F7CAE69E5A229C9D1D322562B033C0D8DD35071434A1FE5'),
    ('common', r'DimensionsRecomp\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h', '362E9EDBA0B9E4AC156982E7D75A70AF1341C6E1F1F52139BE03978DB3AA1E8F'),
    ('indexer', r'build\agent6\aot\microcode-index\lego_gpu_microcode_index.exe', '3B5A68FE447DF23D46BCFF7913E590A8AF4A14A2FBBE28453B17EB23144BB9A1'),
    ('oldindex', r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\lego-microcode-index.cpp', '2DB859177B4656477D2858B87F37E7F068CABA420362FA21AFA1B3C8C6DD13A2'),
    ('maincache', r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\aot\lego-dxil-cache.cpp', 'FF9386C1CD435E7EE12781F43A6F42F97AED7062A4147D4E649AF2450157A819'),
    ('merge', r'DimensionsRecomp\tools\gpu-aot\merge_microcode_index.py', '20986E998AB8B6F83FC0390A15A45DABB86F37E81206A9ED06D06E205DDB1BE2'),
    ('lookup', r'DimensionsRecomp\tools\gpu-aot\test_placement_capture_lookup.py', '856D0A8E0E827D6AECF99FC0D34DDCCB0FE0F182D9EE372A20048FDC3350058B'),
    ('archive', r'DimensionsRecomp\rexlego\src\gpu_native\shader_archive.cpp', '1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC'),
    ('archiveh', r'DimensionsRecomp\rexlego\src\gpu_native\shader_archive.h', '83B030F92C504D1FF5AD554371745A8DA38C52310B290DA9246A212CC3F743D5'),
    ('snaparch', r'build\agent2\snap1\DimensionsRecomp\rexlego\src\gpu_native\shader_archive.cpp', '1C5B1767B8F6871D7E11DAAE59733E0CE8FA86362E95BECF7E03BC3EB67092EC'),
    ('checker', r'build\agent16\pack\check_pack.py', ''),
    ('wrapper', r'build\agent16\pack\run_lookup.py', ''),
]
PINS_BIN = [
    ('recompile', r'build\agent2\recompile.py', '855BCC79148E2DA87397E035A7E06DEFCB5B2AB6400131DFA34C5FC74B2BE1BB'),
    ('relink', r'build\agent2\relink.py', 'F3C6EEAF332AB213D8208400A9240F1D173FC5A6417D041E34F0CA046879FB62'),
    ('stage', r'build\agent2\stage-variant.py', 'D2BD1C6358FC19C1EBF160AA7EADF44F3FAE50EA64F5EC78320F463B77E40EB7'),
    ('verifybins', r'build\agent2\session3\verify-bins.py', '80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E'),
    ('pecheck', r'build\agent2\final\pe-check.py', 'F4368C32076AAA3EF4BD087E82A3FCA623F8D4FDCA363E2713825A52CD813E27'),
    ('mapcheck', r'build\agent2\s4b\mapcheck-s4c.py', 'F8CB7B495F74D97848125B57C731953206A1766C5B576958625570F44F8EECDE'),
    ('mapcmp', r'build\agent9\mapcmp.py', '5BDDAE2104A113E5FD7AB5F5A493C54DDA058A3CEA5ABFEDBA61B1975C964C6D'),
    ('ccdb', r'build\agent2\snap1-on\compile_commands.json', 'A814629513BF60283CFE8E33B7F967FD595C3603D623300190B0EC71CF0469EF'),
    ('ninja', r'build\agent2\snap1-on\build.ninja', '5AB81775F2E4827ED1203F5CCE405698FCE17B32D0C3086CE0BE2981A887A812'),
    ('fpon', r'build\agent2\final2\b\nat\fp-on.cmake', 'EF78BF00CD0821F3FB3CEC95292BE9B5160AA42BE7AEBFA8D3CE9E378CA1D435'),
    ('buildinfoin', r'build\agent2\snap1\DimensionsRecomp\rexlego\src\gpu_native\build_info.h.in', '36F069DF6C109A6CE1632D83566B1B979D75D8C70047C6F04270E96137036960'),
    ('genonh', r'build\agent2\final2\b\nat\gen-on\native_gpu_build_info.h', '8511FF42ECA408CED98AD5A10B350136075D216D758B0F7E47574BD2FA9708FB'),
    ('genontxt', r'build\agent2\final2\b\nat\gen-on\native-gpu-build.txt', 'BC37A606A3F28CAB7092BD130A71506ED358D5F1007A0AC6F743C717194A6214'),
    ('overlayshaders', r'build\agent2\final2\b\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp', '4B8250E976A384010915FA66C6E2279397C83A3DE05DCF2CFAC5FD452E85EEFD'),
    ('stubcache', r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\stubs\runtime-cache.cpp', 'E66C9AA34C301C60003F18AE62B6496041F59123DC1372DAC5C393C7BE88053D'),
    ('rlcache', r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\runtime-linked-dxil-cache.cpp', 'A479268EB611CDC52FD52AD1F76A5857587CD67E776F431E9B1BE320FFD4896D'),
    ('rlmeta', r'build\agent2\snap1-on\generated\gpu_native\runtime-linked-bank\linked-bank-metadata.cpp', 'E4D91F96049C4F9E6EB267EC444EB69E2F9D0C70A390471E8932AF696D15C865'),
    ('rlobj', r'build\agent2\snap1-on\generated\gpu_native\runtime-linked-bank\linked-bank.obj', '7B952900EB35F2342F0FB577018C6085323339F399989AD501D9D72DD34876B9'),
    ('embed', r'build\agent2\snap1\DimensionsRecomp\tools\gpu-aot\embed_linked_bank.py', 'C678C3644616E0F2B831601AB42B4950941F6F8C79B3FD7BD3EA9E2C348EE6BD'),
    ('llvmmc', r'toolchain\llvm-23.1.6\bin\llvm-mc.exe', '559F2932481EEEAA5DDD0B89910D5FFAFAB8CF2DD0A97AD1815F4AE09ABE50FD'),
    ('prelinkexe', r'build\agent2\snap1-on\lego_gpu_prelink_runtime.exe', '4BB316E898757F192899E52EE06D2C3B67E4E261983B48BA015419488A7283A8'),
    ('pdxcompiler', r'build\agent2\snap1-on\dxcompiler.dll', '0689E2FEE0A1C9DF8662A59680469F24E2A3AD7CE6BBBCC9284F7A83172BFC59'),
    ('pdxil', r'build\agent2\snap1-on\dxil.dll', '64BE2368211D257A038A7D4EA6BB3E24C878EB8D588C7B8414FCCF759B69C2AC'),
    ('nf2exe', r'build\agent2\nativefinal2-bin\legodimensions.exe', '090A420BA16797A1A94FFAA0D07730734BEF906435A11081B5638C90C4856C25'),
    ('nf2map', r'build\agent2\nativefinal2-bin\legodimensions.map', 'B669786E17B3B09E53840139A9B372FD66D15019C8B9AD4A59797134A1139D92'),
    ('nf2manifest', r'build\agent2\nativefinal2-bin\MANIFEST.txt', '4E5E2620F38F7D09E064FB191BA396D7149B27A593C5158EF317CB2D9A31A163'),
    ('cmake', CMAKE, 'FC43B67BA03E1EDB63B2937D6311808A094B31B815435B39547AEF01CEFE8FB1'),
]
WATCH = [
    r'build\agent6\aot\gradient-build', r'build\agent6\aot\microcode-index',
    r'build\agent8\matrix\20261122-0509\runs\0509-sd-r1\shader-dumps\placement-containers',
    r'DimensionsRecomp\rexlego\out\native-gpu', r'DimensionsRecomp\rexlego\src\gpu_native', r'DimensionsRecomp\tools\gpu-aot',
    r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu', r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\aot',
    r'build\agent2\snap1\DimensionsRecomp\rexlego\out\native-gpu\stubs', r'build\agent2\snap1\DimensionsRecomp\tools\gpu-aot',
    r'build\agent2\snap1-on', r'build\agent2\snap1-on\generated\gpu_native\runtime-linked-bank',
    r'build\agent2\snap1-on\CMakeFiles\legodimensions.dir\src\gpu_native', r'build\agent2\snap1-on\CMakeFiles\lego_gpu_prelink_runtime.dir',
    r'build\agent2\final2\b\nat', r'build\agent2\final2\b\nat\gen-on', r'build\agent2\nativefinal2-bin', r'build\agent2',
    r'build\agent9', r'build\agent16\dump',
]
# legodimensions TUs recompiled by bin: (ccdb file, ON source, object basename, replace key)
GPU = os.path.join(SNAP, 'rexlego', 'src', 'gpu_native')
FP_TUS = ['device.cpp', 'pipeline_library.cpp', 'shader_archive.cpp', 'shaders.cpp']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def fwd(p):
    return os.path.abspath(p).replace('\\', '/')


def rel(p):
    try:
        return os.path.relpath(os.path.abspath(p), W)
    except ValueError:
        return p


def in_pack(p):
    full = os.path.abspath(p)
    if not os.path.normcase(full).startswith(os.path.normcase(PACK) + os.sep):
        raise SystemExit('refusing to write outside build\\agent16\\pack: %s' % full)
    return full


class Log:
    def __init__(self):
        self.path = None
        self.buf = []

    def __call__(self, s=''):
        line = '[%s] %s' % (time.strftime('%H:%M:%S'), s)
        print(line, flush=True)
        if self.path:
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        else:
            self.buf.append(line)

    def open(self, path):
        self.path = in_pack(path)
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(''.join(x + '\n' for x in self.buf))
        self.buf = []


log = Log()


def self_limit():
    from ctypes import wintypes
    k = ctypes.windll.kernel32
    k.GetCurrentProcess.restype = wintypes.HANDLE
    k.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.GetPriorityClass.argtypes = [wintypes.HANDLE]
    k.GetPriorityClass.restype = wintypes.DWORD
    k.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    k.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t),
                                         ctypes.POINTER(ctypes.c_size_t)]
    h = k.GetCurrentProcess()
    k.SetPriorityClass(h, IDLE)
    k.SetProcessAffinityMask(h, ctypes.c_size_t(0x3))
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    k.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm))
    return k.GetPriorityClass(h), pm.value


def check_pins(pins):
    bad = 0
    for k, r, want in pins:
        p = r if os.path.isabs(r) else P(r)
        if not os.path.isfile(p):
            log('PIN  %-14s MISSING %s' % (k, r))
            bad += 1
            continue
        got = sha(p)
        tag = 'logd' if not want else ('ok  ' if got == want else 'FAIL')
        bad += tag == 'FAIL'
        log('PIN  %-14s %s %s %s' % (k, tag, got, r))
    return bad


def pin(k):
    for kk, r, _ in PINS_PACK + PINS_BIN:
        if kk == k:
            return r if os.path.isabs(r) else P(r)
    raise KeyError(k)


def listing(dirs):
    out = []
    for d in dirs:
        p = d if os.path.isabs(d) else P(d)
        if not os.path.isdir(p):
            out.append('%s|MISSING' % d)
            continue
        for fn in sorted(os.listdir(p)):
            fp = os.path.join(p, fn)
            st = os.stat(fp)
            out.append('%s\\%s|%s|%d' % (d, fn, '<dir>' if os.path.isdir(fp) else st.st_size, st.st_mtime_ns))
    return out


def run(name, cmd, cwd, logdir, env=None, timeout=1800, dry=False):
    shown = ' '.join('"%s"' % c if ' ' in c else c for c in cmd)
    log('RUN  %s : %s   (cwd %s)' % (name, shown, rel(cwd)))
    if dry:
        return 0, ''
    t0 = time.time()
    e = dict(os.environ)
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    if env:
        e.update(env)
    so = in_pack(os.path.join(logdir, name + '.stdout.txt'))
    with open(so, 'wb') as f:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, env=e, creationflags=IDLE | NOWIN)
        try:
            p.wait(timeout)
        except subprocess.TimeoutExpired:
            subprocess.run('taskkill /T /F /PID %d' % p.pid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait()
            log('FAIL %s timed out after %d s (process tree killed)' % (name, timeout))
    txt = open(so, 'r', encoding='utf-8', errors='replace').read()
    log('DONE %s exit=%d wall_s=%.1f' % (name, p.returncode, time.time() - t0))
    return p.returncode, txt


# ------------------------------------------------------------------------------------------------- inputs
def select_inputs(input_dir, excludes, check):
    """Returns (rows [(name, sha, src, source-desc)], excluded [(name, reason)], fails [str])."""
    rows, excl, fails = {}, [], []
    for n, h in S35.items():
        p = os.path.join(S35_DIR, n)
        if not os.path.isfile(p) or sha(p) != h:
            fails.append('s35 pinned container %s missing or changed' % n)
            continue
        rows[n] = (n, h, p, 's35 pinned (build/agent8 0509-sd-r1)')
    if input_dir:
        sums = os.path.join(input_dir, 'SHA256SUMS.txt')
        if not os.path.isfile(sums):
            fails.append('no SHA256SUMS.txt in %s' % input_dir)
            return list(rows.values()), excl, fails
        listed = {}
        for line in open(sums, encoding='utf-8', errors='replace'):
            m = re.match(r'^([0-9A-Fa-f]{64})\s+(\S+)\s*(?:\((.*)\))?\s*$', line.strip())
            if not m:
                if line.strip():
                    fails.append('unparsed SHA256SUMS line: %s' % line.strip())
                continue
            listed[m.group(2)] = (m.group(1).upper(), m.group(3) or '')
        present = sorted(f for f in os.listdir(input_dir) if f != 'SHA256SUMS.txt')
        for f in present:
            if f not in listed:
                fails.append('%s is in the input dir but not in SHA256SUMS.txt' % f)
        for n, (h, cat) in sorted(listed.items()):
            p = os.path.join(input_dir, n)
            if 'raw' in cat.lower():
                fails.append('%s is category %s: placement-raw is never compiler input' % (n, cat))
                continue
            if not os.path.isfile(p):
                fails.append('%s listed but missing' % n)
                continue
            if sha(p) != h:
                fails.append('%s sha256 differs from SHA256SUMS.txt' % n)
                continue
            if n in excludes:
                excl.append((n, '%s [%s]' % (excludes[n], cat)))
                continue
            if n in rows:
                if rows[n][1] != h:
                    fails.append('%s: same name, different sha256 than an already selected input' % n)
                continue
            if any(r[1] == h for r in rows.values()):
                excl.append((n, 'duplicate content of an already selected input'))
                continue
            info = check.parse_container(p)
            if info['problems']:
                fails.append('%s [%s]: %s (add --exclude %s if it cannot go through the placement flow)' % (
                    n, cat, '; '.join(info['problems']), n))
                continue
            rows[n] = (n, h, p, 'input %s (%s)' % (os.path.basename(input_dir), cat))
    for n, r in rows.items():
        if r[3].startswith('s35'):
            info = check.parse_container(r[2])
            if info['problems']:
                fails.append('%s: %s' % (n, '; '.join(info['problems'])))
    return [rows[k] for k in sorted(rows)], excl, fails


def import_checker():
    sys.dont_write_bytecode = True
    sys.path.insert(0, PACK)
    import check_pack
    return check_pack


# ------------------------------------------------------------------------------------------------- pack
def pack_commands(r):
    g = r.get
    return [
        ('gradient', [pin('gradient'), g('in'), g('cache'), pin('common')], {'XENOS_RECOMP_DXIL_ONLY': '1',
                                                                             'XENOS_RECOMP_HLSL_DUMP': g('hlsl')}, 1800),
        ('indexer', [pin('indexer'), g('add'), g('in')], None, 600),
        ('merge', [PY, pin('merge'), pin('oldindex'), g('add'), g('index'), '--report', g('mrep')], None, 600),
        ('prelookup', [PY, pin('checker'), 'prelookup', g('run'), '--old-index', pin('oldindex'), '--main-cache',
                       pin('maincache')], None, 600),
        ('lookup', [PY, pin('wrapper'), pin('lookup'), g('in'), g('index'), g('cache'), g('lk')], None, 1800),
        ('lookup-main', [PY, pin('wrapper'), pin('lookup'), g('in'), g('index'), g('cache'), g('lkm'),
                         '--main-cache', pin('maincache')], None, 1800),
    ]


def run_dirs(run_):
    return {'run': run_, 'in': os.path.join(run_, 'runtime-input'), 'logs': os.path.join(run_, 'logs'),
            'hlsl': os.path.join(run_, 'hlsl'), 'work': os.path.join(run_, 'work'), 'tmp': os.path.join(run_, 'tmp'),
            'cache': os.path.join(run_, 'runtime-cache.cpp'), 'add': os.path.join(run_, 'index-addition.cpp'),
            'index': os.path.join(run_, 'lego-microcode-index.cpp'), 'mrep': os.path.join(run_, 'merge-report.json'),
            'lk': os.path.join(run_, 'lookup'), 'lkm': os.path.join(run_, 'lookup-main'),
            'check': os.path.join(run_, 'pack-check.json')}


def do_pack(a, check, stamp):
    run_ = in_pack(os.path.join(PACK, 'run-' + stamp))
    if os.path.exists(run_):
        log('FAIL %s exists' % run_)
        return 2
    d = run_dirs(run_)
    for k in ('run', 'in', 'logs', 'hlsl', 'work', 'tmp'):
        os.makedirs(in_pack(d[k]))
    log.open(os.path.join(run_, 'pack-log.txt'))
    bad = check_pins(PINS_PACK)
    rows, excl, fails = select_inputs(a.input, a.excl, check)
    for n, why in excl:
        log('EXCL %s: %s' % (n, why))
    if bad or fails:
        for f in fails:
            log('FAIL input: %s' % f)
        log('VERDICT FAIL (bad pins %d, input failures %d): nothing compiled' % (bad, len(fails)))
        return 1
    before = listing(WATCH + ([a.input] if a.input else []))
    otmp = (os.environ.get('TMP'), os.environ.get('TEMP'))
    os.environ['TMP'] = os.environ['TEMP'] = d['tmp']
    failed, rc_check = None, None
    t_all = time.time()
    try:
        with open(in_pack(os.path.join(d['in'], 'STAGED.tsv')), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# name\tsha256\tsource\n')
            for n, h, src, desc in rows:
                dst = in_pack(os.path.join(d['in'], n))
                shutil.copyfile(src, dst)
                if sha(dst) != h:
                    raise RuntimeError('staged %s differs from its pinned sha256' % n)
                f.write('%s\t%s\t%s\n' % (n, h, desc))
        os.replace(os.path.join(d['in'], 'STAGED.tsv'), in_pack(os.path.join(run_, 'STAGED.tsv')))
        # the input dir must hold only *.bin for the tools; keep STAGED.tsv next to it and a copy for the checker
        shutil.copyfile(os.path.join(run_, 'STAGED.tsv'), in_pack(os.path.join(d['in'], 'STAGED.tsv')))
        log('staged %d containers (%d s35 + %d from --input), %d excluded' % (
            len(rows), sum(r[3].startswith('s35') for r in rows), sum(not r[3].startswith('s35') for r in rows),
            len(excl)))
        rc, txt = run('precheck', [PY, pin('checker'), 'precheck', d['in'], '--staged',
                                   os.path.join(d['in'], 'STAGED.tsv')], d['work'], d['logs'], timeout=300)
        if rc:
            raise RuntimeError('precheck failed (exit %d)' % rc)
        for name, cmd, env, to in pack_commands(d):
            rc, txt = run(name, cmd, d['work'], d['logs'], env=env, timeout=to)
            if rc:
                raise RuntimeError('%s failed (exit %d)' % (name, rc))
            if name == 'gradient' and not os.path.isfile(d['cache']):
                raise RuntimeError('gradient_compiler wrote no runtime-cache.cpp')
            if name == 'prelookup':
                for l in txt.splitlines()[-6:]:
                    log('     ' + l)
    except Exception as ex:  # noqa: BLE001
        failed = str(ex)
        log('FAIL %s' % failed)
    finally:
        os.environ['TMP'], os.environ['TEMP'] = otmp[0] or '', otmp[1] or ''
    after = listing(WATCH + ([a.input] if a.input else []))
    diff = sorted(set(before) ^ set(after))
    with open(in_pack(os.path.join(run_, 'side-effects.txt')), 'w', encoding='utf-8') as f:
        f.write('\n'.join(('< ' if x in before else '> ') + x for x in diff) + '\n' if diff else
                'none: the top level of all %d watched dirs is unchanged\n' % len(WATCH))
    log('side effects: %s' % ('%d listing change(s), see side-effects.txt' % len(diff) if diff else 'none'))
    bad_after = check_pins(PINS_PACK)
    if os.path.isfile(d['add']) and os.path.isfile(d['index']):
        rc_check, txt = run('check', [PY, pin('checker'), 'post', run_, '--old-index', pin('oldindex'),
                                      '--main-cache', pin('maincache'), '--out', d['check']], d['work'], d['logs'],
                            timeout=600)
        for l in txt.splitlines():
            if not l.startswith('  [ok]'):
                log('     ' + l)
    verdict = 'PASS' if (not failed and rc_check == 0 and not diff and not bad_after) else 'FAIL'
    sums = []
    for dp, _, fns in os.walk(run_):
        if os.path.normcase(dp).startswith(os.path.normcase(d['tmp'])):
            continue
        for fn in fns:
            if fn in ('SHA256SUMS.txt', 'pack-log.txt'):
                continue
            fp = os.path.join(dp, fn)
            sums.append('%s  %s' % (sha(fp), os.path.relpath(fp, run_)))
    with open(in_pack(os.path.join(run_, 'SHA256SUMS.txt')), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(sorted(sums, key=lambda s: s[66:])) + '\n')
    log('LATEST-pack.txt not written (native6pack): run-%s %s containers=%d input=%s' % (
        stamp, verdict, len(rows), a.input or '-'))
    log('VERDICT %s (tools: %s; check exit: %s; side effects: %d; pins changed after: %d; wall %.1f s)' % (
        verdict, failed or 'ok', rc_check, len(diff), bad_after, time.time() - t_all))
    if verdict == 'PASS':
        log('runtime-cache.cpp %s' % sha(d['cache']))
        log('lego-microcode-index.cpp %s' % sha(d['index']))
    return 0 if verdict == 'PASS' else 1


# ------------------------------------------------------------------------------------------------- bin
def latest_pack_run():
    lp = os.path.join(PACK, 'LATEST-pack.txt')
    if not os.path.isfile(lp):
        return None
    return os.path.join(PACK, open(lp, encoding='utf-8').read().split()[0])


def derive_ccdb(out_path, subs):
    """Writes a ccdb with only the needed entries; subs: {ccdb file basename-key: (old path, new path)}."""
    db = json.load(open(pin('ccdb'), encoding='utf-8'))
    keep, notes = [], []
    want = {
        'runtime-cache.cpp': lambda e: 'lego_gpu_prelink_runtime.dir' in e['output'] and e['file'].endswith(
            'stubs\\runtime-cache.cpp'),
        'lego-microcode-index.cpp': lambda e: 'legodimensions.dir' in e['output'] and e['file'].endswith(
            'lego-microcode-index.cpp'),
    }
    for t in ['runtime_shader_cache.cpp', 'runtime_linked_shader_cache.cpp'] + FP_TUS:
        want[t] = (lambda t: lambda e: 'legodimensions.dir' in e['output'] and
                   e['file'].lower() == os.path.join(GPU, t).lower())(t)
    for key, f in want.items():
        hits = [e for e in db if f(e)]
        if len(hits) != 1:
            raise RuntimeError('ccdb: %s has %d entries' % (key, len(hits)))
        e = dict(hits[0])
        if key in subs:
            old, new = subs[key]
            if e['command'].count(old) != 1:
                raise RuntimeError('ccdb: %s: %s occurs %d times' % (key, old, e['command'].count(old)))
            e['command'] = e['command'].replace(old, new)
            notes.append('%s: %s -> %s' % (key, old, new))
        keep.append(e)
    with open(in_pack(out_path), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(keep, f, indent=1)
    return notes


def fp_script(dst, gen_dir, swaps):
    t = open(pin('fpon'), encoding='utf-8').read()
    old_gen = fwd(os.path.join(A2, 'final2', 'b', 'nat', 'gen-on'))
    if t.count(old_gen) != 2:
        raise RuntimeError('fp-on.cmake: gen-on path occurs %d times (need 2)' % t.count(old_gen))
    t = t.replace(old_gen, fwd(gen_dir))
    for old, new in swaps:
        k = t.count(old + ';') + t.count(old + '"')
        if k != 1:
            raise RuntimeError('fp-on.cmake: %s occurs %d times as a list item' % (old, k))
        t = t.replace(old + ';', new + ';').replace(old + '"', new + '"')
    with open(in_pack(dst), 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def fp_python(script):
    items = re.match(r'set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "([^"]*)"\)', open(script, encoding='utf-8').read())
    mat = ''.join(sha(p).lower() for p in items.group(1).split(';'))
    return hashlib.sha256(mat.encode()).hexdigest()[:16], len(items.group(1).split(';'))


def bin_plan(a, bw, pr):
    """All bin steps as (name, cmd, cwd, env, timeout, kind). kind: ctl|on."""
    s = {}
    for v in (['ctl', 'on'] if a.ctl else ['on']):
        o = os.path.join(bw, v)
        s[v] = dict(o=o, ccdb=os.path.join(o, 'ccdb.json'), plist=os.path.join(o, 'prelink-list.tsv'),
                    pobj=os.path.join(o, 'prelink-obj'), plink=os.path.join(o, 'prelink-link'),
                    rlc=os.path.join(o, 'runtime-linked-dxil-cache.cpp'), emb=os.path.join(o, 'runtime-linked-bank'),
                    fp=os.path.join(o, 'fp.cmake'), gen=os.path.join(o, 'gen'), elist=os.path.join(o, 'exe-list.tsv'),
                    eobj=os.path.join(o, 'exe-obj'), rep=os.path.join(o, 'replace.txt'),
                    link=os.path.join(o, 'link'), logs=os.path.join(o, 'logs'), tmp=os.path.join(o, 'tmp'))
    return s


def write_lists(v, x, cache_src, index_src):
    stub = pin('stubcache')
    with open(in_pack(x['plist']), 'w', encoding='utf-8', newline='\n') as f:
        f.write('%s\t%s\t%s\n' % (stub, cache_src, os.path.join(x['pobj'], 'runtime-cache.cpp.obj')))
    rows = [(pin('oldindex'), index_src, 'lego-microcode-index.cpp.obj',
             'CMakeFiles/legodimensions.dir/out/native-gpu/lego-microcode-index.cpp.obj')]
    for t in ['runtime_shader_cache.cpp', 'runtime_linked_shader_cache.cpp'] + FP_TUS:
        src = pin('overlayshaders') if t == 'shaders.cpp' else os.path.join(GPU, t)
        rows.append((os.path.join(GPU, t), src, t + '.obj', 'CMakeFiles/legodimensions.dir/src/gpu_native/%s.obj' % t))
    with open(in_pack(x['elist']), 'w', encoding='utf-8', newline='\n') as f:
        for c, s_, o, _ in rows:
            f.write('%s\t%s\t%s\n' % (c, s_, os.path.join(x['eobj'], o)))
    with open(in_pack(x['rep']), 'w', encoding='utf-8', newline='\n') as f:
        for _, _, o, k in rows:
            f.write('%s=%s\n' % (k, os.path.join(x['eobj'], o)))
        f.write('generated/gpu_native/runtime-linked-bank/linked-bank.obj=%s\n' % os.path.join(x['emb'],
                                                                                              'linked-bank.obj'))


def do_bin(a, stamp):
    t_all = time.time()
    pr = os.path.abspath(a.pack_run) if a.pack_run else None  # native6pack: --pack-run required
    bw = in_pack(os.path.join(PACK, 'binwork-' + stamp))
    out_bin = in_pack(os.path.join(PACK, a.bin_out))
    plan_only = a.mode == 'plan'
    if not plan_only:
        os.makedirs(bw)
        log.open(os.path.join(bw, 'bin-log.txt'))
    log('bin: pack run %s; work %s; staged bin %s; CTL %s; jobs %d' % (pr and rel(pr), rel(bw), rel(out_bin),
                                                                    a.ctl, a.jobs))
    fails = []
    if not plan_only:
        if os.path.exists(out_bin):
            fails.append('%s exists' % rel(out_bin))
        if not pr or not os.path.isfile(os.path.join(pr, 'pack-check.json')):
            fails.append('pack run has no pack-check.json')
        else:
            pc = json.load(open(os.path.join(pr, 'pack-check.json'), encoding='utf-8'))
            if pc.get('verdict') != 'PASS':
                fails.append('pack run verdict %s' % pc.get('verdict'))
        bad = check_pins(PINS_BIN)
        if bad:
            fails.append('%d bin pin(s) bad' % bad)
        if fails:
            for f in fails:
                log('FAIL %s' % f)
            return 1
        before = listing(WATCH)  # S1 (native6pack): watched-dir listing before the bin
    s = bin_plan(a, bw, pr)
    inp = os.path.join(bw, 'inputs')
    cache_on, index_on = os.path.join(inp, 'runtime-cache.cpp'), os.path.join(inp, 'lego-microcode-index.cpp')
    if not plan_only:
        os.makedirs(in_pack(inp))
        for fn in ('runtime-cache.cpp', 'lego-microcode-index.cpp', 'pack-check.json', 'STAGED.tsv'):
            shutil.copyfile(os.path.join(pr, fn), in_pack(os.path.join(inp, fn)))
        pc = json.load(open(os.path.join(inp, 'pack-check.json'), encoding='utf-8'))
        if sha(cache_on) != pc['runtime_cache']['sha256'] or sha(index_on) != pc['index']['new_sha256']:
            log('FAIL pack outputs differ from pack-check.json')
            return 1
        log('inputs: runtime-cache.cpp %s, lego-microcode-index.cpp %s (from %s)' % (sha(cache_on), sha(index_on),
                                                                                   rel(pr)))
    stub, rlc_snap, rlmeta = pin('stubcache'), pin('rlcache'), pin('rlmeta')
    gates = []

    def gate(name, ok):
        gates.append((name, bool(ok)))
        log('%s %s' % ('PASS' if ok else 'FAIL', name))
        return ok

    otmp = (os.environ.get('TMP'), os.environ.get('TEMP'))
    try:
        for v, x in s.items():
            ctl = v == 'ctl'
            cache_src = stub if ctl else cache_on
            index_src = pin('oldindex') if ctl else index_on
            log('=== %s: runtime cache %s, index %s' % (v.upper(), rel(cache_src), rel(index_src)))
            if not plan_only:
                for k in ('o', 'pobj', 'plink', 'emb', 'gen', 'eobj', 'link', 'logs', 'tmp'):
                    os.makedirs(in_pack(x[k]), exist_ok=True)
                os.environ['TMP'] = os.environ['TEMP'] = x['tmp']
                subs = {
                    'runtime_shader_cache.cpp': (fwd(stub), fwd(cache_src)),
                    'runtime_linked_shader_cache.cpp': (fwd(rlmeta), fwd(os.path.join(x['emb'],
                                                                                      'linked-bank-metadata.cpp'))),
                }
                for n_ in derive_ccdb(x['ccdb'], subs):
                    log('ccdb sub %s' % n_)
                write_lists(v, x, cache_src, index_src)
            # 1. prelink runtime exe with this runtime cache
            cmds = [
                ('prelink-recompile', [PY, pin('recompile'), '--ccdb', x['ccdb'], '--list', x['plist'], '--jobs', '1',
                                       '--priority', 'idle', '--fwd-src', '--log-dir', x['logs']], SNAPON, None),
                ('prelink-relink', [PY, pin('relink'), '--ninja', pin('ninja'), '--target', 'lego_gpu_prelink_runtime.exe',
                                    '--out-dir', x['plink'], '--priority', 'idle', '--link-flag', '-Xlinker /threads:2',
                                    '--replace', 'CMakeFiles/lego_gpu_prelink_runtime.dir/out/native-gpu/stubs/'
                                    'runtime-cache.cpp.obj=' + os.path.join(x['pobj'], 'runtime-cache.cpp.obj')]
                 + (['--compare', pin('prelinkexe')] if ctl else []), SNAPON, None),
                ('prelink-run', [os.path.join(x['plink'], 'lego_gpu_prelink_runtime.exe'), x['rlc']], x['plink'],
                 {'LEGO_GPU_PRELINK_JOBS': '2'}),
                ('embed', [PY, pin('embed'), x['rlc'], x['emb'], '--llvm-mc', fwd(pin('llvmmc')), '--arch', 'x86_64',
                           '--runtime'], x['o'], None),
                ('fingerprint', [CMAKE, '-P', x['fp']], x['o'], None),
                ('exe-recompile', [PY, pin('recompile'), '--ccdb', x['ccdb'], '--list', x['elist'], '--jobs', str(a.jobs),
                                   '--priority', 'idle', '--fwd-src',
                                   '--flag=-fmacro-prefix-map=%s=%s' % (fwd(os.path.join(OV, 'rexlego')),
                                                                        fwd(os.path.join(SNAP, 'rexlego'))),
                                   '--include-first', x['gen'], '--log-dir', x['logs']], SNAPON, None),
                ('exe-relink', [PY, pin('relink'), '--ninja', pin('ninja'), '--target', 'legodimensions.exe',
                                '--out-dir', x['link'], '--priority', 'idle', '--link-flag', '-Xlinker /threads:2',
                                '--replace-file', x['rep']]
                 + (['--compare', pin('nf2exe'), '--compare-map', pin('nf2map')] if ctl else []), SNAPON, None),
            ]
            for name, cmd, cwd, env in cmds:
                if name == 'prelink-run' and not plan_only:
                    for dll in ('pdxcompiler', 'pdxil'):
                        dst = in_pack(os.path.join(x['plink'], os.path.basename(pin(dll))))
                        shutil.copyfile(pin(dll), dst)
                        if sha(dst) != sha(pin(dll)):
                            raise RuntimeError('dll copy differs: %s' % dst)
                if name == 'fingerprint' and not plan_only:
                    swaps = [] if ctl else [(fwd(pin('oldindex')), fwd(index_on)), (fwd(stub), fwd(cache_on)),
                                            (fwd(rlc_snap), fwd(x['rlc']))]
                    fp_script(x['fp'], x['gen'], swaps)
                if plan_only:
                    run(v + '-' + name, cmd, cwd, None, dry=True)
                    continue
                rc, txt = run(v + '-' + name, cmd, cwd, x['logs'], env=env, timeout=1800)
                tail = [l for l in txt.splitlines() if re.match(r'(PASS|FAIL|DIFF|wall|link exit|replace input|edge:)', l)]
                for l in tail[-14:]:
                    log('     ' + l)
                if rc:
                    raise RuntimeError('%s %s failed (exit %d)' % (v, name, rc))
                if name == 'prelink-run' and ctl:
                    if not gate('CTL prelink output = snap1 runtime-linked-dxil-cache.cpp (A479268E)',
                                sha(x['rlc']) == sha(rlc_snap)):
                        raise RuntimeError('CTL prelink differs')
                if name == 'embed' and ctl:
                    ok = all(sha(os.path.join(x['emb'], f)) == sha(os.path.join(os.path.dirname(rlmeta), f))
                             for f in ('linked-bank-metadata.cpp', 'linked-bank.obj'))
                    if not gate('CTL embed metadata.cpp + linked-bank.obj = snap1-on generated runtime-linked-bank', ok):
                        raise RuntimeError('CTL embed differs')
                if name == 'fingerprint':
                    fp_txt = open(os.path.join(x['gen'], 'native-gpu-build.txt'), encoding='utf-8').read().split()[-1]
                    fpp, nin = fp_python(x['fp'])
                    log('fingerprint %s %s (python cross-check %s over %d inputs)' % (v, fp_txt, fpp, nin))
                    gate('%s fingerprint cmake == python recompute' % v, fp_txt == fpp)
                    if ctl:
                        ok = (fp_txt == FP_OLD and sha(os.path.join(x['gen'], 'native_gpu_build_info.h')) ==
                              sha(pin('genonh')) and sha(os.path.join(x['gen'], 'native-gpu-build.txt')) ==
                              sha(pin('genontxt')))
                        if not gate('CTL fingerprint = %s, header+txt identical to final2 gen-on' % FP_OLD, ok):
                            raise RuntimeError('CTL fingerprint differs')
                    else:
                        x['fp_new'] = fp_txt
                        gate('ON fingerprint %s != %s' % (fp_txt, FP_OLD), fp_txt != FP_OLD)
                        gate('ON fingerprint %s != native5pack %s' % (fp_txt, FP_N5), fp_txt != FP_N5)
                if name == 'exe-recompile':
                    cmdf = open(os.path.join(x['logs'], 'recompile-commands.txt'), encoding='utf-8').read()
                    gi = fwd(x['gen'])
                    okinc = all(('-I' + gi) in c and c.index('-I' + gi) < c.find('snap1-on/generated')
                                for c in cmdf.split('cmd: ')[1:])
                    gate('%s include-first gen dir ahead of snap1-on/generated in all commands' % v, okinc)
                    bads = [f for f in os.listdir(x['logs']) if f.endswith('.obj.log') and
                            re.search(r'(?i)error|pch', open(os.path.join(x['logs'], f), errors='replace').read())]
                    gate('%s no error/pch text in compile logs' % v, not bads)
                if name == 'exe-relink' and ctl:
                    if not gate('CTL relink exe+map = nativefinal2 except TimeDateStamp',
                                re.search(r'^PASS compare', txt, re.M) and re.search(r'^PASS map', txt, re.M)):
                        raise RuntimeError('CTL relink differs from nativefinal2')
        if plan_only:
            log('then: gates (fingerprint needles, overlay bytes, pe-check, mapcheck --mode same), stage-variant.py '
                '--base %s --out %s, verify-bins.py, PINS_BIN re-check + watched-dir listing diff (S1)' % (
                rel(NF2), rel(out_bin)))
            return 0
        # 2. gates on the ON exe
        x = s['on']
        exe, mp = os.path.join(x['link'], 'legodimensions.exe'), os.path.join(x['link'], 'legodimensions.map')
        b = open(exe, 'rb').read()
        gate('ON exe contains the new fingerprint %s' % x['fp_new'], x['fp_new'].encode() in b)
        gate('ON exe lacks the old fingerprint %s' % FP_OLD, FP_OLD.encode() not in b)
        gate('ON exe lacks the native5pack fingerprint %s' % FP_N5, FP_N5.encode() not in b)
        ovre = re.compile(rb'agent2[/\\]+final2[/\\]+b[/\\]', re.I)
        gate('no overlay path bytes (agent2/final2/b/) in exe/map', not ovre.search(b) and
             not ovre.search(open(mp, 'rb').read()))
        npk = len(re.findall(rb'(?i)agent16[/\\]+pack', b))
        log('INFO agent16/pack path bytes in the exe: %d' % npk)
        gate('ON exe differs from nativefinal2', sha(exe) != sha(pin('nf2exe')))
        rc, txt = run('on-pe-check', [PY, pin('pecheck'), '--new', exe, '--ref', pin('nf2exe')], x['o'], x['logs'])
        gate('pe-check ON exe vs nativefinal2 (exports/imports equal)', rc == 0)
        rc, txt = run('on-mapcheck', [PY, pin('mapcheck'), '--map', mp, '--ref', pin('nf2map'), '--mode', 'same',
                                      '--out', in_pack(os.path.join(x['o'], 'mapcheck.txt'))], x['o'], x['logs'])
        gate('mapcheck --mode same vs nativefinal2 map', rc == 0)
        if not all(ok for _, ok in gates):
            raise RuntimeError('gate(s) failed: %s' % ', '.join(n for n, ok in gates if not ok))
        # 3. stage + verify
        pc = json.load(open(os.path.join(inp, 'pack-check.json'), encoding='utf-8'))
        ncont = len(pc.get('containers', []))
        notes = [
            'native GPU fingerprint %s (nativefinal2: %s): native-pso-recipes.bin / seed are keyed by it, first boot '
            'is cold' % (x['fp_new'], FP_OLD),
            'pack run %s: %d placement containers; runtime-cache.cpp %s; lego-microcode-index.cpp %s (merge base '
            'snap1 2DB85917, %d -> %d rows)' % (rel(pr), ncont, sha(cache_on), sha(index_on),
                                               pc['index']['old_rows'], pc['index']['new_rows']),
            'runtime-linked-dxil-cache.cpp %s; runtime linked-bank.obj %s' % (
                sha(x['rlc']), sha(os.path.join(x['emb'], 'linked-bank.obj'))),
            'built by build/agent16/pack/native6pack.py bin (sha256 %s): build-final2 nat recipe, recompile.py/relink.py '
            'unchanged on build/agent2/snap1-on objects; work dir %s' % (sha(os.path.abspath(__file__)), rel(bw)),
            'gates: %s' % '; '.join('%s %s' % ('PASS' if ok else 'FAIL', n) for n, ok in gates),
        ]
        cmd = [PY, pin('stage'), '--base', NF2, '--out', out_bin, '--replace', 'legodimensions.exe=' + exe,
               '--replace', 'legodimensions.map=' + mp, '--title',
               'native6pack: nativefinal2 + AOT placement pack (%d containers), native GPU fingerprint %s' % (
                   ncont, x['fp_new'])]
        for n_ in notes:
            cmd += ['--note', n_]
        rc, txt = run('stage', cmd, bw, os.path.join(bw), timeout=900)
        if rc:
            raise RuntimeError('stage-variant failed (exit %d)' % rc)
        rc, txt = run('verify-bins', [PY, pin('verifybins'), out_bin, '--out',
                                      in_pack(os.path.join(bw, 'verify-bins.txt'))], bw, bw)
        gate('verify-bins %s' % rel(out_bin), rc == 0)
        if rc:
            raise RuntimeError('verify-bins failed')
        # 4. S1 (native6pack): watched-dir listing diff + PINS_BIN re-check after stage + verify-bins
        after = listing(WATCH)
        diff = sorted(set(before) ^ set(after))
        with open(in_pack(os.path.join(bw, 'side-effects.txt')), 'w', encoding='utf-8') as f:
            f.write('\n'.join(('< ' if y in before else '> ') + y for y in diff) + '\n' if diff else
                    'none: the top level of all %d watched dirs is unchanged\n' % len(WATCH))
        log('side effects: %s' % ('%d listing change(s), see side-effects.txt' % len(diff) if diff else 'none'))
        gate('bin side effects: top level of all %d watched dirs unchanged' % len(WATCH), not diff)
        bad_after = check_pins(PINS_BIN)
        gate('bin pins unchanged after stage + verify-bins (%d bad)' % bad_after, not bad_after)
        if diff or bad_after:
            raise RuntimeError('bin side effects: %d listing change(s), %d pin(s) changed' % (len(diff), bad_after))
        mf = os.path.join(out_bin, 'MANIFEST.txt')
        log('STAGED %s MANIFEST sha256 %s; exe %s; map %s; fingerprint %s' % (
            rel(out_bin), sha(mf), sha(os.path.join(out_bin, 'legodimensions.exe')),
            sha(os.path.join(out_bin, 'legodimensions.map')), x['fp_new']))
        log('LATEST-bin.txt not written (native6pack): %s PASS MANIFEST=%s fingerprint=%s pack=%s' % (
            a.bin_out, sha(mf), x['fp_new'], rel(pr)))
        log('VERDICT PASS (wall %.1f s)' % (time.time() - t_all))
        return 0
    except Exception as ex:  # noqa: BLE001
        log('FAIL %s' % ex)
        log('VERDICT FAIL (wall %.1f s)' % (time.time() - t_all))
        return 1
    finally:
        os.environ['TMP'], os.environ['TEMP'] = otmp[0] or '', otmp[1] or ''


# ------------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('plan', 'pack', 'bin'))
    ap.add_argument('--input', help='pack-input dir (dump_post.py --stage output with SHA256SUMS.txt); '
                                    'omitted = the 4 s35 containers alone (stand-in)')
    ap.add_argument('--exclude', action='append', default=[], help='extra NAME to leave out (logged)')
    ap.add_argument('--no-default-exclude', action='store_true')
    ap.add_argument('--pack-run', help='bin: a PASS pack run dir (required; no LATEST-pack.txt fallback)')
    ap.add_argument('--bin-out', default='native6pack-bin')
    ap.add_argument('--no-ctl', dest='ctl', action='store_false')
    ap.add_argument('--jobs', type=int, default=2)
    a = ap.parse_args()
    if a.jobs > 2 or a.jobs < 1:
        print('FAIL: --jobs must be 1 or 2 (2-CPU limit)')
        return 2
    if a.input:
        a.input = os.path.abspath(a.input)
    a.excl = {} if a.no_default_exclude else dict(DEFAULT_EXCLUDE)
    for n in a.exclude:
        a.excl[n] = 'excluded by --exclude'
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    pc, aff = self_limit()
    if a.mode == 'plan':
        log.open(os.path.join(PACK, 'plan-%s.txt' % stamp))
    log('native6pack.py %s pid=%d priority=0x%X affinity=0x%X python=%s sha256=%s' % (
        a.mode, os.getpid(), pc, aff, sys.version.split()[0], sha(os.path.abspath(__file__))))
    if pc != IDLE or aff & ~0x3 or not aff:
        log('FAIL: not at Idle priority / affinity within 0x3')
        return 2
    check = import_checker()
    if a.mode == 'pack':
        return do_pack(a, check, stamp)
    if a.mode == 'bin':
        return do_bin(a, stamp)
    # plan
    clang = shutil.which('clang++')
    log('clang++ = %s' % clang)
    bad = check_pins(PINS_PACK) + check_pins(PINS_BIN)
    rows, excl, fails = select_inputs(a.input, a.excl, check)
    log('inputs: %d selected (%d s35 pinned + %d from %s), %d excluded, %d failure(s)' % (
        len(rows), sum(r[3].startswith('s35') for r in rows), sum(not r[3].startswith('s35') for r in rows),
        a.input or '(no --input: s35 stand-in)', len(excl), len(fails)))
    for n, why in excl:
        log('EXCL %s: %s' % (n, why))
    for f in fails:
        log('FAIL input: %s' % f)
    log('--- pack (outputs under %s):' % rel(os.path.join(PACK, 'run-<stamp>')))
    log('stage %d containers -> runtime-input\\ (+STAGED.tsv), re-verify sha256; check_pack.py precheck' % len(rows))
    for name, cmd, env, _ in pack_commands(run_dirs(os.path.join(PACK, 'run-<stamp>'))):
        log('RUN  %s : %s%s' % (name, ' '.join(cmd), ('   env ' + str(env)) if env else ''))
    log('check_pack.py post; pins re-check; watched-dir listing diff; SHA256SUMS.txt (no LATEST-pack.txt)')
    log('--- bin (outputs under %s, staged %s):' % (rel(os.path.join(PACK, 'binwork-<stamp>')), a.bin_out))
    a.pack_run = a.pack_run or os.path.join(PACK, 'run-<stamp>')
    do_bin(a, '<stamp>')
    ok = not bad and not fails and clang
    log('PLAN %s (bad pins %d, input failures %d, clang++ %s)' % ('OK' if ok else 'NOT OK', bad, len(fails),
                                                                  'found' if clang else 'MISSING'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
