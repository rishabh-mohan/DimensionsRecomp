#!/usr/bin/env python3
# psobin.py - E16.1 (S5 phase 2.2+2.3 bin), build/agent16/psobin: native4bp + the PSO diffs 2.2 + 2.3 to
# rexlego/src/gpu_native/pipeline_library.cpp, built with the final2 / native4bp method (recompile.py + relink.py
# UNCHANGED on the build/agent2/snap1-on objects; the 7 native4bp TU objects and its runtime linked-bank.obj are
# copied in from build/agent16/pack/binwork-20261125-173830/on; outputs only under build/agent16/psobin).
# Launch through psobin.ps1 (Idle priority + affinity 0x3, devshell).
#
#   psobin.ps1 plan --src <E16.2 after-file> --sha <sha256 pinned by M16> [--diff D ...] [--fp-add-src]
#   psobin.ps1 bin  --src <E16.2 after-file> --sha <sha256 pinned by M16> [--diff D ...] [--fp-add-src]
#                   [--bin-out native4bp-pso-bin] [--no-ctl] [--jobs 2]
#
# Refuses unless: sha256(--src) == --sha; DimensionsRecomp HEAD == a8e8dc8 and HEAD:pipeline_library.cpp == blob
# 4484038 == the snap1 source the snap1-on objects were built from (EOL-normalized); --src != HEAD (EOL-normalized);
# every pin matches; the bin dir does not exist; perf-notes/WINDOW-HOLD.txt is absent.
# Fingerprint: pipeline_library.cpp is NOT in LEGO_NATIVE_GPU_FINGERPRINT_INPUTS (rexlego/CMakeLists.txt L604-786;
# only gpu_native/*.h are globbed), so the CMake recipe keeps 39129c4c059be5f0 and only the pipeline_library TU is
# recompiled (with --include-first <native4bp gen>, since it includes native_gpu_build_info.h via
# pipeline_recipes.h). --fp-add-src is an opt-in deviation from the CMake recipe: it appends the after-file to the
# fingerprint input list (fingerprint changes) and then recompiles all 4 fingerprint consumers (device,
# pipeline_library, shader_archive, final2 shaders.cpp overlay) with the new gen dir.
# Gates: CTL (HEAD file) relink == native4bp exe+map except TimeDateStamp; ON exe differs; ON exe contains
# LEGO_NATIVE_PSO_SAVE_UNLOCKED and LEGO_NATIVE_PSO_AUX_UNLOCKED; expected fingerprint present; no scratch/overlay
# path bytes; pe-check exports/imports == native4bp; stage-variant over pack/native4bp-bin; verify-bins PASS.
# Nothing here sets an env var or writes a config for the game: the bin is code only (B3).
import argparse, ctypes, datetime, hashlib, json, os, re, shutil, subprocess, sys, time

W = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
OUT = os.path.join(W, 'build', 'agent16', 'psobin')
PACK = os.path.join(W, 'build', 'agent16', 'pack')
HOLD = os.path.join(W, 'perf-notes', 'WINDOW-HOLD.txt')
REPO = os.path.join(W, 'DimensionsRecomp')
A2 = os.path.join(W, 'build', 'agent2')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
SNAPON = os.path.join(A2, 'snap1-on')
OV = os.path.join(A2, 'final2', 'b', 'DimensionsRecomp')
GPU = os.path.join(SNAP, 'rexlego', 'src', 'gpu_native')
BASEWORK = os.path.join(PACK, 'binwork-20261125-173830', 'on')
BASEBIN = os.path.join(PACK, 'native4bp-bin')
CMAKE = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
PY = sys.executable
IDLE = 0x00000040
NOWIN = 0x08000000
HEAD = 'a8e8dc8e34f453135794a0c82a142c01f720b1ac'
HEAD_BLOB = '44840383ad8fa798d63f869ac01c69b933f005f6'
REL_SRC = 'rexlego/src/gpu_native/pipeline_library.cpp'
# P-C2 (M10 pso-native-r2-rating): the after-file must be exactly the both-applied (2.2 + 2.3 r2) file
SRC_SHA = '4247ECB9F03976CF2C4805B7BA9E59D7E913440F9D72943826A7AD692138F5C9'
SRC_BLOB = '8583c5cc7badb652347b68992a2131c3240b64e0'  # git hash-object of the LF-normalised after-file
FP_BASE = '39129c4c059be5f0'
NEEDLES = [b'LEGO_NATIVE_PSO_SAVE_UNLOCKED', b'LEGO_NATIVE_PSO_AUX_UNLOCKED']
FP_TUS = ['device.cpp', 'pipeline_library.cpp', 'shader_archive.cpp', 'shaders.cpp']
# native4bp ON exe objects (replace key -> object basename); all 7 + linked-bank.obj are relink replacements
BASE_OBJS = {
    'lego-microcode-index.cpp.obj': ('CMakeFiles/legodimensions.dir/out/native-gpu/lego-microcode-index.cpp.obj',
                                     '985A3CD1D100346A36441E49F9C2E4CEA3BCF8897B9AA09FA03B6663E225970C'),
    'runtime_shader_cache.cpp.obj': ('CMakeFiles/legodimensions.dir/src/gpu_native/runtime_shader_cache.cpp.obj',
                                     'BA9709D7E13012E1AA7180ECCF8B50605E717DDC61D7AF3B2A3C9EB85BF74976'),
    'runtime_linked_shader_cache.cpp.obj': (
        'CMakeFiles/legodimensions.dir/src/gpu_native/runtime_linked_shader_cache.cpp.obj',
        'FCE81DC1E56CCDECE564FC1FDFE73C7699987ADC42651A543EC67C16BCC6050E'),
    'device.cpp.obj': ('CMakeFiles/legodimensions.dir/src/gpu_native/device.cpp.obj',
                       '7D3C84BB49EDB05CA6D8F081348D18C28E822C3266508627E8418F67ADB497BB'),
    'pipeline_library.cpp.obj': ('CMakeFiles/legodimensions.dir/src/gpu_native/pipeline_library.cpp.obj',
                                 '548AA7E39FC508FDCE9DC0B3CECAC6D336DF6920DEBFF9815308DB43EC5F6FF2'),
    'shader_archive.cpp.obj': ('CMakeFiles/legodimensions.dir/src/gpu_native/shader_archive.cpp.obj',
                               'EFD68BDE3D13892A128F561C04360B3E9C8B6998C007D4F98A405D03941E5F12'),
    'shaders.cpp.obj': ('CMakeFiles/legodimensions.dir/src/gpu_native/shaders.cpp.obj',
                        '9A72FC13B288F7E7762EB3333336D453AE6E878E60AA546AB0C9A60A24DA1567'),
}
LB_KEY = 'generated/gpu_native/runtime-linked-bank/linked-bank.obj'
P = lambda *a: os.path.join(W, *a)
PINS = [
    ('recompile', r'build\agent2\recompile.py', '855BCC79148E2DA87397E035A7E06DEFCB5B2AB6400131DFA34C5FC74B2BE1BB'),
    ('relink', r'build\agent2\relink.py', 'F3C6EEAF332AB213D8208400A9240F1D173FC5A6417D041E34F0CA046879FB62'),
    ('stage', r'build\agent2\stage-variant.py', 'D2BD1C6358FC19C1EBF160AA7EADF44F3FAE50EA64F5EC78320F463B77E40EB7'),
    ('verifybins', r'build\agent2\session3\verify-bins.py', '80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E'),
    ('pecheck', r'build\agent2\final\pe-check.py', 'F4368C32076AAA3EF4BD087E82A3FCA623F8D4FDCA363E2713825A52CD813E27'),
    ('mapcheck', r'build\agent2\s4b\mapcheck-s4c.py', 'F8CB7B495F74D97848125B57C731953206A1766C5B576958625570F44F8EECDE'),
    ('ccdb', r'build\agent2\snap1-on\compile_commands.json', 'A814629513BF60283CFE8E33B7F967FD595C3603D623300190B0EC71CF0469EF'),
    ('ninja', r'build\agent2\snap1-on\build.ninja', '5AB81775F2E4827ED1203F5CCE405698FCE17B32D0C3086CE0BE2981A887A812'),
    ('overlayshaders', r'build\agent2\final2\b\DimensionsRecomp\rexlego\src\gpu_native\shaders.cpp',
     '4B8250E976A384010915FA66C6E2279397C83A3DE05DCF2CFAC5FD452E85EEFD'),
    ('snapsrc', r'build\agent2\snap1\DimensionsRecomp\rexlego\src\gpu_native\pipeline_library.cpp',
     'EACB098E313E13ADEE777EEED920EFA9A0522A6B975AE3B7790F1D74F569F661'),
    ('basegenh', r'build\agent16\pack\binwork-20261125-173830\on\gen\native_gpu_build_info.h',
     '36319E632C8F768AEC3C82E79408E3222580E88B28B73D986A4F2A428A150472'),
    ('basegentxt', r'build\agent16\pack\binwork-20261125-173830\on\gen\native-gpu-build.txt',
     'E9B5A7B13D866AEEA8D92126A8D069EBA77410E2853AF21EAD33B78779781B84'),
    ('basefp', r'build\agent16\pack\binwork-20261125-173830\on\fp.cmake',
     '31F5DFD4631F7E6A5C8E60A9B070C6CBA716F00D155A72E761B1A1EB3A5CF9E4'),
    ('baselb', r'build\agent16\pack\binwork-20261125-173830\on\runtime-linked-bank\linked-bank.obj',
     '612932DEF92BC655C20B5D33146C7E03A6B42C6BC44587D0C6028FA421E43A40'),
    ('basemanifest', r'build\agent16\pack\native4bp-bin\MANIFEST.txt',
     'C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690'),
    ('baseexe', r'build\agent16\pack\native4bp-bin\legodimensions.exe',
     'FA761654D665BC928B9FC82AC5DCE58E25EE2E87BF60ED519CC5480A3012187C'),
    ('basemap', r'build\agent16\pack\native4bp-bin\legodimensions.map',
     '493DA6DA6660CC9F9C5C923E4E29F9336AEA82721C5BB88B7DD044FB2D73CE2D'),
    ('cmake', CMAKE, 'FC43B67BA03E1EDB63B2937D6311808A094B31B815435B39547AEF01CEFE8FB1'),
] + [('obj:' + k, os.path.join(BASEWORK, 'exe-obj', k), h) for k, (_, h) in BASE_OBJS.items()]
WATCH = [r'build\agent2', r'build\agent2\snap1-on', r'build\agent2\nativefinal2-bin', r'build\agent16\pack',
         r'build\agent16\pack\native4bp-bin', r'build\agent16\pack\binwork-20261125-173830\on',
         r'build\agent16\pack\binwork-20261125-173830\on\exe-obj', r'build\agent16\pso',
         r'build\agent2\snap1\DimensionsRecomp\rexlego\src\gpu_native', r'DimensionsRecomp\rexlego\src\gpu_native']


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


def in_out(p):
    full = os.path.abspath(p)
    if not os.path.normcase(full).startswith(os.path.normcase(OUT) + os.sep):
        raise SystemExit('refusing to write outside build\\agent16\\psobin: %s' % full)
    return full


class Log:
    def __init__(self):
        self.path, self.buf = None, []

    def __call__(self, s=''):
        line = '[%s] %s' % (time.strftime('%H:%M:%S'), s)
        print(line, flush=True)
        if self.path:
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        else:
            self.buf.append(line)

    def open(self, path):
        self.path = in_out(path)
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


def pin(k):
    for kk, r, _ in PINS:
        if kk == k:
            return r if os.path.isabs(r) else P(r)
    raise KeyError(k)


def check_pins():
    bad = 0
    for k, r, want in PINS:
        p = r if os.path.isabs(r) else P(r)
        if not os.path.isfile(p):
            log('PIN  %-34s MISSING %s' % (k, rel(p)))
            bad += 1
            continue
        got = sha(p)
        ok = got == want
        bad += not ok
        log('PIN  %-34s %s %s %s' % (k, 'ok  ' if ok else 'FAIL', got, rel(p)))
    return bad


def listing(dirs):
    out = []
    for d in dirs:
        p = P(d)
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
    so = in_out(os.path.join(logdir, name + '.stdout.txt'))
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


def git(*args):
    r = subprocess.run(['git', '-C', REPO] + list(args), capture_output=True)
    if r.returncode:
        raise RuntimeError('git %s failed: %s' % (' '.join(args), r.stderr.decode(errors='replace').strip()))
    return r.stdout


def norm(b):
    return b.replace(b'\r\n', b'\n')


def preflight(a):
    """Source checks; returns a list of failures (each also logged)."""
    fails = []

    def f(msg):
        fails.append(msg)
        log('FAIL %s' % msg)

    if not os.path.isfile(a.src):
        f('--src missing: %s' % a.src)
        return fails
    got = sha(a.src)
    log('src %s sha256 %s (pinned --sha %s)' % (rel(a.src), got, a.sha))
    if got != a.sha:
        f('--src sha256 %s != pinned %s: refusing' % (got, a.sha))
    if not fwd(a.src).lower().endswith('/' + REL_SRC):
        f('--src must end with %s (needed for the macro prefix map)' % REL_SRC)
    try:
        head = git('rev-parse', 'HEAD').decode().strip()
        blob = git('rev-parse', 'HEAD:' + REL_SRC).decode().strip()
        hb = git('cat-file', '-p', HEAD_BLOB)
    except RuntimeError as ex:
        f(str(ex))
        return fails
    log('DimensionsRecomp HEAD %s; HEAD:%s = %s' % (head, REL_SRC, blob))
    if head != HEAD:
        f('DimensionsRecomp HEAD %s != %s' % (head, HEAD))
    if blob != HEAD_BLOB:
        f('HEAD blob %s != %s' % (blob, HEAD_BLOB))
    snap = open(pin('snapsrc'), 'rb').read()
    if norm(snap) != norm(hb):
        f('snap1 pipeline_library.cpp != HEAD blob %s (EOL-normalized): the diffs do not apply to the snap1-on '
          'objects; STOP' % HEAD_BLOB[:7])
    else:
        log('PASS snap1 pipeline_library.cpp == HEAD blob %s (EOL-normalized, %d bytes LF)' % (HEAD_BLOB[:7],
                                                                                             len(norm(hb))))
    src = open(a.src, 'rb').read()
    lf = norm(src)
    bid = hashlib.sha1(b'blob %d\0' % len(lf) + lf).hexdigest()
    a.src_blob = bid
    ok = bid == SRC_BLOB and got == SRC_SHA and a.sha.upper() == SRC_SHA
    log('%s P-C2 gate: --src LF blob %s (want %s), sha256 %s (want %s)' % (
        'PASS' if ok else 'FAIL', bid, SRC_BLOB, got, SRC_SHA))
    if not ok:
        f('P-C2: --src is not the both-applied file (blob %s / sha256 %s): refusing' % (bid, got))
    if norm(src) == norm(hb):
        f('--src is identical to HEAD (EOL-normalized): nothing to build')
    for n in NEEDLES:
        k = src.count(n)
        log('%s source string %s: %d occurrence(s)' % ('PASS' if k else 'FAIL', n.decode(), k))
        if not k:
            f('--src lacks %s (the ON exe gate would fail)' % n.decode())
    for d in a.diff:
        log('diff %s sha256 %s' % (rel(d), sha(d) if os.path.isfile(d) else 'MISSING'))
        if not os.path.isfile(d):
            f('diff missing: %s' % d)
    return fails


def fp_python(script):
    items = re.search(r'set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "([^"]*)"\)', open(script, encoding='utf-8').read())
    lst = items.group(1).split(';')
    mat = ''.join(sha(p).lower() for p in lst)
    return hashlib.sha256(mat.encode()).hexdigest()[:16], len(lst)


def fp_script(dst, gen_dir, add):
    t = open(pin('basefp'), encoding='utf-8').read()
    old_gen = fwd(os.path.join(BASEWORK, 'gen'))
    if t.count(old_gen) != 2:
        raise RuntimeError('base fp.cmake: gen path occurs %d times (need 2)' % t.count(old_gen))
    t = t.replace(old_gen, fwd(gen_dir))
    m = re.search(r'set\(LEGO_NATIVE_GPU_FINGERPRINT_INPUTS "([^"]*)"\)', t)
    if fwd(add).lower() in m.group(1).lower():
        raise RuntimeError('fingerprint list already contains %s' % add)
    t = t[:m.end(1)] + ';' + fwd(add) + t[m.end(1):]
    with open(in_out(dst), 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def derive_ccdb(out_path, tus):
    db = json.load(open(pin('ccdb'), encoding='utf-8'))
    keep = []
    for t in tus:
        hits = [e for e in db if 'legodimensions.dir' in e['output'] and
                e['file'].lower() == os.path.join(GPU, t).lower()]
        if len(hits) != 1:
            raise RuntimeError('ccdb: %s has %d entries' % (t, len(hits)))
        keep.append(hits[0])
    with open(in_out(out_path), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(keep, f, indent=1)


def do(a, stamp):
    t_all = time.time()
    dry = a.mode == 'plan'
    wk = in_out(os.path.join(OUT, 'work-' + stamp))
    out_bin = in_out(os.path.join(OUT, a.bin_out))
    tus = FP_TUS if a.fp_add_src else ['pipeline_library.cpp']
    log('psobin: src %s; work %s; staged bin %s; CTL %s; jobs %d; fingerprint mode %s; recompiled TUs %s' % (
        rel(a.src), rel(wk), rel(out_bin), a.ctl, a.jobs,
        'CHANGE (--fp-add-src: after-file appended to the input list, deviation from CMake)' if a.fp_add_src
        else 'CMake recipe (pipeline_library.cpp is not an input: stays %s)' % FP_BASE, ', '.join(tus)))
    fails = preflight(a)
    bad = check_pins()
    if bad:
        fails.append('%d pin(s) bad' % bad)
        log('FAIL %d pin(s) bad' % bad)
    if os.path.exists(out_bin):
        fails.append('%s exists' % rel(out_bin))
        log('FAIL %s exists (never overwritten)' % rel(out_bin))
    if fails and not dry:
        log('VERDICT FAIL (preflight: %d failure(s)); nothing built' % len(fails))
        return 1
    before = listing(WATCH)
    base = os.path.join(wk, 'base')
    if not dry:
        os.makedirs(wk)
        log.open(os.path.join(wk, 'psobin-log.txt'))
        os.makedirs(in_out(os.path.join(base, 'exe-obj')))
        os.makedirs(in_out(os.path.join(base, 'gen')))
        for k in BASE_OBJS:
            shutil.copyfile(pin('obj:' + k), in_out(os.path.join(base, 'exe-obj', k)))
        for k, fn in (('basegenh', 'native_gpu_build_info.h'), ('basegentxt', 'native-gpu-build.txt')):
            shutil.copyfile(pin(k), in_out(os.path.join(base, 'gen', fn)))
        shutil.copyfile(pin('baselb'), in_out(os.path.join(base, 'linked-bank.obj')))
        shutil.copyfile(a.src, in_out(os.path.join(base, 'pipeline_library.after.cpp')))
        for k, (_, h) in BASE_OBJS.items():
            if sha(os.path.join(base, 'exe-obj', k)) != h:
                log('FAIL base copy differs: %s' % k)
                return 1
        log('base: 7 native4bp ON objects + linked-bank.obj + gen (%s) copied to %s and re-verified' % (
            FP_BASE, rel(base)))
    src_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.src)))))
    gates = []

    def gate(name, ok):
        gates.append((name, bool(ok)))
        log('%s %s' % ('PASS' if ok else 'FAIL', name))
        return ok

    variants = (['ctl', 'on'] if a.ctl else ['on'])
    otmp = (os.environ.get('TMP'), os.environ.get('TEMP'))
    res = {}
    try:
        for v in variants:
            ctl = v == 'ctl'
            o = os.path.join(wk, v)
            x = dict(o=o, ccdb=os.path.join(o, 'ccdb.json'), elist=os.path.join(o, 'exe-list.tsv'),
                     eobj=os.path.join(o, 'exe-obj'), rep=os.path.join(o, 'replace.txt'), link=os.path.join(o, 'link'),
                     logs=os.path.join(o, 'logs'), tmp=os.path.join(o, 'tmp'), fp=os.path.join(o, 'fp.cmake'),
                     gen=os.path.join(base, 'gen') if (ctl or not a.fp_add_src) else os.path.join(o, 'gen'))
            res[v] = x
            plsrc = pin('snapsrc') if ctl else os.path.abspath(a.src)
            log('=== %s: pipeline_library.cpp source %s; gen %s' % (v.upper(), rel(plsrc), rel(x['gen'])))
            if not dry:
                for k in ('o', 'eobj', 'link', 'logs', 'tmp'):
                    os.makedirs(in_out(x[k]), exist_ok=True)
                os.environ['TMP'] = os.environ['TEMP'] = x['tmp']
                derive_ccdb(x['ccdb'], tus)
                with open(in_out(x['elist']), 'w', encoding='utf-8', newline='\n') as f:
                    for t in tus:
                        s_ = plsrc if t == 'pipeline_library.cpp' else (
                            pin('overlayshaders') if t == 'shaders.cpp' else os.path.join(GPU, t))
                        f.write('%s\t%s\t%s\n' % (os.path.join(GPU, t), s_, os.path.join(x['eobj'], t + '.obj')))
                with open(in_out(x['rep']), 'w', encoding='utf-8', newline='\n') as f:
                    for k, (key, _) in BASE_OBJS.items():
                        src_obj = os.path.join(x['eobj'], k) if k[:-4] in tus else os.path.join(base, 'exe-obj', k)
                        f.write('%s=%s\n' % (key, src_obj))
                    f.write('%s=%s\n' % (LB_KEY, os.path.join(base, 'linked-bank.obj')))
            if not ctl and a.fp_add_src:
                if not dry:
                    os.makedirs(in_out(x['gen']), exist_ok=True)
                    fp_script(x['fp'], x['gen'], plsrc)
                rc, txt = run(v + '-fingerprint', [CMAKE, '-P', x['fp']], o, x['logs'], dry=dry)
                if not dry:
                    if rc:
                        raise RuntimeError('fingerprint failed (exit %d)' % rc)
                    fp_txt = open(os.path.join(x['gen'], 'native-gpu-build.txt'), encoding='utf-8').read().split()[-1]
                    fpp, nin = fp_python(x['fp'])
                    log('fingerprint ON %s (python cross-check %s over %d inputs)' % (fp_txt, fpp, nin))
                    gate('ON fingerprint cmake == python recompute', fp_txt == fpp)
                    gate('ON fingerprint %s != %s' % (fp_txt, FP_BASE), fp_txt != FP_BASE)
                    x['fp_new'] = fp_txt
            else:
                x['fp_new'] = FP_BASE
            flags = ['--flag=-fmacro-prefix-map=%s=%s' % (fwd(os.path.join(OV, 'rexlego')),
                                                          fwd(os.path.join(SNAP, 'rexlego')))]
            if not ctl:
                flags.append('--flag=-fmacro-prefix-map=%s=%s' % (fwd(os.path.join(src_root, 'rexlego')),
                                                                  fwd(os.path.join(SNAP, 'rexlego'))))
            cmds = [
                ('exe-recompile', [PY, pin('recompile'), '--ccdb', x['ccdb'], '--list', x['elist'], '--jobs',
                                   str(a.jobs), '--priority', 'idle', '--fwd-src'] + flags +
                 ['--include-first', x['gen'], '--log-dir', x['logs']], SNAPON),
                ('exe-relink', [PY, pin('relink'), '--ninja', pin('ninja'), '--target', 'legodimensions.exe',
                                '--out-dir', x['link'], '--priority', 'idle', '--link-flag', '-Xlinker /threads:2',
                                '--replace-file', x['rep']]
                 + (['--compare', pin('baseexe'), '--compare-map', pin('basemap')] if ctl else []), SNAPON),
            ]
            for name, cmd, cwd in cmds:
                rc, txt = run(v + '-' + name, cmd, cwd, x['logs'], dry=dry)
                if dry:
                    continue
                tail = [l for l in txt.splitlines() if re.match(r'(PASS|FAIL|DIFF|wall|link exit|replace input|edge:)', l)]
                for l in tail[-14:]:
                    log('     ' + l)
                if rc:
                    raise RuntimeError('%s %s failed (exit %d)' % (v, name, rc))
                if name == 'exe-recompile':
                    cmdf = open(os.path.join(x['logs'], 'recompile-commands.txt'), encoding='utf-8').read()
                    gi = fwd(x['gen'])
                    okinc = all(('-I' + gi) in c and c.index('-I' + gi) < c.find('snap1-on/generated')
                                for c in cmdf.split('cmd: ')[1:])
                    gate('%s include-first gen dir ahead of snap1-on/generated in all commands' % v, okinc)
                    if not ctl:
                        gate('ON recompile compiled the after-file', fwd(plsrc) in cmdf)
                    bads = [f for f in os.listdir(x['logs']) if f.endswith('.obj.log') and
                            re.search(r'(?i)\berror\b|pch', open(os.path.join(x['logs'], f), errors='replace').read())]
                    gate('%s no error/pch text in compile logs' % v, not bads)
                if name == 'exe-relink' and ctl:
                    if not gate('CTL (HEAD file) relink exe+map = native4bp except TimeDateStamp',
                                re.search(r'^PASS compare', txt, re.M) and re.search(r'^PASS map', txt, re.M)):
                        raise RuntimeError('CTL relink differs from native4bp')
        if dry:
            log('then: ON gates (exe differs from native4bp, env strings %s, fingerprint %s present, no scratch/overlay '
                'path bytes, pe-check vs native4bp exe, mapcheck --mode same INFO), stage-variant.py --base %s --out %s, '
                'verify-bins.py, listing diff of watched dirs' % (
                    '/'.join(n.decode() for n in NEEDLES), 'NEW' if a.fp_add_src else FP_BASE, rel(BASEBIN),
                    rel(out_bin)))
            return 0 if not fails else 1
        x = res['on']
        exe, mp = os.path.join(x['link'], 'legodimensions.exe'), os.path.join(x['link'], 'legodimensions.map')
        b = open(exe, 'rb').read()
        mb = open(mp, 'rb').read()
        gate('ON exe differs from native4bp', sha(exe) != sha(pin('baseexe')))
        for n in NEEDLES:
            gate('ON exe contains %s' % n.decode(), n in b)
        gate('ON exe contains fingerprint %s' % x['fp_new'], x['fp_new'].encode() in b)
        if x['fp_new'] != FP_BASE:
            gate('ON exe lacks the native4bp fingerprint %s' % FP_BASE, FP_BASE.encode() not in b)
        scr = re.compile(re.escape(os.path.basename(os.path.dirname(src_root))).encode() + rb'[/\\]+' +
                         re.escape(os.path.basename(src_root)).encode() + rb'[/\\]+rexlego', re.I)
        gate('no after-file path bytes (%s) in exe/map' % scr.pattern.decode(errors='replace'),
             not scr.search(b) and not scr.search(mb))
        ovre = re.compile(rb'agent2[/\\]+final2[/\\]+b[/\\]', re.I)
        gate('no overlay path bytes (agent2/final2/b/) in exe/map', not ovre.search(b) and not ovre.search(mb))
        rc, txt = run('on-pe-check', [PY, pin('pecheck'), '--new', exe, '--ref', pin('baseexe')], x['o'], x['logs'])
        gate('pe-check ON exe vs native4bp (exports/imports equal)', rc == 0)
        rc, txt = run('on-mapcheck', [PY, pin('mapcheck'), '--map', mp, '--ref', pin('basemap'), '--mode', 'same',
                                      '--out', in_out(os.path.join(x['o'], 'mapcheck.txt'))], x['o'], x['logs'])
        log('INFO mapcheck --mode same vs native4bp map: exit %d (informational; new code may move symbols)' % rc)
        if not all(ok for _, ok in gates):
            raise RuntimeError('gate(s) failed: %s' % ', '.join(n for n, ok in gates if not ok))
        notes = [
            'native4bp-bin (MANIFEST C518152026695279993085A8497E7B14D318C1DFF54B57F2767670B90A7AA690) + PSO diffs to '
            '%s: after-file %s sha256 %s (HEAD %s blob %s; snap1 source == HEAD EOL-normalized)' % (
                REL_SRC, rel(a.src), sha(a.src), HEAD[:7], HEAD_BLOB[:7]),
            'P-C2: after-file LF git blob %s, sha256 %s (both-applied 2.2 + 2.3 r2)' % (a.src_blob, sha(a.src)),
            'diffs: %s' % '; '.join('%s %s' % (rel(d), sha(d)) for d in a.diff),
            'native GPU fingerprint %s (native4bp: %s)%s' % (
                x['fp_new'], FP_BASE, ': changed by --fp-add-src (after-file appended to the input list; deviation '
                'from the CMake recipe); first boot is cold' if x['fp_new'] != FP_BASE else
                ': unchanged, pipeline_library.cpp is not a CMake fingerprint input; native-pso-recipes.bin / seed of '
                'native4bp stay valid for this bin'),
            'code only (B3): no defaults changed by the build; PREPARE_THREADS=1, SAVE_UNLOCKED and AUX_UNLOCKED stay '
            'off unless the env vars are set at run time; recompiled TUs: %s' % ', '.join(tus),
            'built by build/agent16/psobin/psobin.py (sha256 %s): final2/native4bp recipe, recompile.py/relink.py '
            'unchanged on build/agent2/snap1-on objects + native4bp ON objects; work dir %s' % (
                sha(os.path.abspath(__file__)), rel(wk)),
            'gates: %s' % '; '.join('%s %s' % ('PASS' if ok else 'FAIL', n) for n, ok in gates),
        ]
        cmd = [PY, pin('stage'), '--base', BASEBIN, '--out', out_bin, '--replace', 'legodimensions.exe=' + exe,
               '--replace', 'legodimensions.map=' + mp, '--title',
               'native4bp-pso: native4bp + PSO diffs 2.2+2.3 (pipeline_library.cpp), native GPU fingerprint %s' %
               x['fp_new']]
        for n_ in notes:
            cmd += ['--note', n_]
        rc, txt = run('stage', cmd, wk, wk, timeout=900)
        if rc:
            raise RuntimeError('stage-variant failed (exit %d)' % rc)
        rc, txt = run('verify-bins', [PY, pin('verifybins'), out_bin, '--out',
                                      in_out(os.path.join(wk, 'verify-bins.txt'))], wk, wk)
        gate('verify-bins %s' % rel(out_bin), rc == 0)
        if rc:
            raise RuntimeError('verify-bins failed')
        after = listing(WATCH)
        diff = sorted(set(before) ^ set(after))
        diff = [d for d in diff if not d.startswith('build\\agent16\\psobin')]
        with open(in_out(os.path.join(wk, 'side-effects.txt')), 'w', encoding='utf-8', newline='\n') as f:
            f.write(''.join(d + '\n' for d in diff) or 'none\n')
        gate('no side effects in watched dirs', not diff)
        mf = os.path.join(out_bin, 'MANIFEST.txt')
        log('STAGED %s MANIFEST sha256 %s; exe %s; map %s; fingerprint %s' % (
            rel(out_bin), sha(mf), sha(os.path.join(out_bin, 'legodimensions.exe')),
            sha(os.path.join(out_bin, 'legodimensions.map')), x['fp_new']))
        with open(in_out(os.path.join(OUT, 'LATEST-bin.txt')), 'w', encoding='utf-8', newline='\n') as f:
            f.write('%s %s %s MANIFEST=%s fingerprint=%s src=%s\n' % (
                a.bin_out, 'PASS' if not diff else 'PASS-with-side-effects', time.strftime('%H:%M:%S'), sha(mf),
                x['fp_new'], sha(a.src)))
        log('VERDICT %s (wall %.1f s)' % ('PASS' if not diff else 'FAIL (side effects)', time.time() - t_all))
        return 0 if not diff else 1
    except Exception as ex:  # noqa: BLE001
        log('FAIL %s' % ex)
        log('VERDICT FAIL (wall %.1f s)' % (time.time() - t_all))
        return 1
    finally:
        os.environ['TMP'], os.environ['TEMP'] = otmp[0] or '', otmp[1] or ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('plan', 'bin'))
    ap.add_argument('--src', required=True, help="E16.2's after-file .../rexlego/src/gpu_native/pipeline_library.cpp")
    ap.add_argument('--sha', required=True, help='sha256 of --src pinned by M16 (refuses on mismatch)')
    ap.add_argument('--diff', action='append', default=None, help='diff file(s) recorded in the MANIFEST '
                    '(default: build/agent16/pso/pso-prepare-merged.diff + pso-unlocked-aux-save.diff)')
    ap.add_argument('--fp-add-src', action='store_true', help='deviation: append the after-file to the fingerprint '
                    'inputs so the fingerprint changes (recompiles the 4 fingerprint consumers)')
    ap.add_argument('--bin-out', default='native4bp-pso-bin')
    ap.add_argument('--no-ctl', dest='ctl', action='store_false')
    ap.add_argument('--jobs', type=int, default=2)
    a = ap.parse_args()
    if a.jobs > 2 or a.jobs < 1:
        print('FAIL: --jobs must be 1 or 2 (2-CPU limit)')
        return 2
    a.src = os.path.abspath(a.src)
    a.sha = a.sha.upper()
    a.diff = [os.path.abspath(d) for d in (a.diff or [P(r'build\agent16\pso\pso-prepare-merged.diff'),
                                                      P(r'build\agent16\pso\pso-unlocked-aux-save.diff')])]
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    pc, aff = self_limit()
    if a.mode == 'plan':
        os.makedirs(OUT, exist_ok=True)
        log.open(os.path.join(OUT, 'plan-%s.txt' % stamp))
    log('psobin.py %s pid=%d priority=0x%X affinity=0x%X python=%s sha256=%s' % (
        a.mode, os.getpid(), pc, aff, sys.version.split()[0], sha(os.path.abspath(__file__))))
    if pc != IDLE or aff & ~0x3 or not aff:
        log('FAIL: not at Idle priority / affinity within 0x3')
        return 2
    if a.mode == 'plan':
        log('clang++ = %s' % shutil.which('clang++'))
    rc = do(a, stamp if a.mode == 'bin' else '<stamp>')
    if a.mode == 'plan':
        log('PLAN %s' % ('OK' if rc == 0 else 'NOT OK (see FAIL lines)'))
    return rc


if __name__ == '__main__':
    sys.exit(main())
