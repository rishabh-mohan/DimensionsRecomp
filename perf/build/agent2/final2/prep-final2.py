#!/usr/bin/env python3
# prep-final2.py (M2, 2026-11-25): final2 step 0, a copy of final/prep-final.py (83F732CA) for ONE bin pair built from
# the COMMITTED source (FINAL-DEFAULTS + #33 s33-popin-nohunk5 57CFA8AD). Same rules: snap1 / snap1-sdk / snap1-off /
# snap1-on read-only; the live repos read-only (git rev-parse / diff --name-only / ls-tree / cat-file only). Starts no
# compiler or linker.
#
#   python build/agent2/final2/prep-final2.py --sdk <sdk-commit> --super <superproject-commit> [--dry-run] [--no-gen]
#
# Differences from prep-final.py:
#   * source of truth = the committed blobs (`git cat-file blob <commit>:<path>`, raw bytes, no filters), not the patch
#     files. Gates: `git diff --name-only 5350b1d <sdk>` == exactly the 13 SDK files; `git diff --name-only c9e215f
#     <super>` == exactly the 2 rexlego files + rexglue-sdk; the gitlink in <super> == <sdk>; every committed blob's
#     sha256 == the after column (FINAL files also == final/work/new, #33 files also == s33/s33/sdk, the
#     devoff4b-s33-bin overlay). snap1 == 5350b1d/c9e215f was shown file by file (commit-plan/cmp-snap1.py), so
#     snap1 + these 15 blobs == the committed tree.
#   * the overlay also holds include/rex/graphics/d3d12/pipeline_cache.h (used with --include-first <overlay>/rexglue-sdk
#     /include, the devoff4b-s33 method); src/graphics is copied whole, so the relative "../frame_stats.h" includes
#     resolve to the overlay. The 15 files are overwritten with the committed blob bytes (before == snap1 checked).
#   * gpu leg = the 10 rexgpu-xenos objects whose ninja deps (snap1-sdk) include pipeline_cache.h / frame_stats.h /
#     graphics/shared_memory.cpp; ALL 10 compile the overlay source (the relative frame_stats.h include). No object
#     outside rexgpu-xenos.dir (SDK) and none in snap1-off/snap1-on depends on the #33 headers. The rexgpu-xenos PCH
#     (cmake_pch.hxx) does not include them (B2: PCH reuse stays valid).
#   * gpu objects: graphics/ and graphics/d3d12/ share basenames (shared_memory.cpp, command_processor.cpp), so the
#     d3d12 objects are named d3d12__<name>.obj (as prep-s33 / devoff4b-s33); all other objects keep their basename.
#   * no xeoff / natoff legs.
#
# Writes only build/agent2/final2/b/ (refuses an existing one):
#   DimensionsRecomp/  the overlay above.
#   rt/ gpu/ xe/ nat/  list-ctl.tsv, list-on.tsv (recompile.py), replace-ctl.txt, replace-on.txt
#                      (relink.py --replace-file) per build leg.
#   nat/gen-ctl, nat/gen-on  the native fingerprint header made by running snap1-on's own
#                      generate-native-gpu-fingerprint.cmake (copy with only the output paths, and for gen-on the
#                      shaders.cpp input path, swapped) with `cmake -P`. gen-ctl must equal snap1-on's header and
#                      native-gpu-build.txt byte for byte; gen-on must be 1616ce65e973c583 and differ only there.
#   prep.txt           this log.
# Also checks: base exes/maps in snap1-off/snap1-on == devoff4b-bin/native4b-bin; the native TU set from
# `ninja -t deps` of snap1-on (objects that include native_gpu_build_info.h, plus shaders.cpp.obj); the shared DLL.
import argparse, hashlib, os, re, shutil, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
FIN = os.path.join(A2, 'final2')
B = os.path.join(FIN, 'b')
OV = os.path.join(B, 'DimensionsRecomp')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
NEW = os.path.join(A2, 'final', 'work', 'new', 'DimensionsRecomp')  # FINAL-DEFAULTS after-files (devfinal's source)
S33 = os.path.join(A2, 's33', 's33', 'sdk')  # devoff4b-s33-bin's overlay (57CFA8AD applied)
LIVE_SUPER = os.path.join(R, 'DimensionsRecomp')
LIVE_SDK = os.path.join(LIVE_SUPER, 'rexglue-sdk')
BASE_SDK, BASE_SUPER = '5350b1d', 'c9e215f'
OFF, ON, SDKB = (os.path.join(A2, d) for d in ('snap1-off', 'snap1-on', 'snap1-sdk'))
NINJA = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
CMAKE = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
SHARED = os.path.join(SDKB, 'install', 'bin', 'rexgpu-xenos.dll')
SHARED_SHA = 'E3CB99CFDEA95E66EF093BF1B2A500076757FB727E60B046D70EBA01E05C9939'
FP_OLD, FP_NEW = '9b40acbbef4c57b3', '1616ce65e973c583'
COPY_DIRS = ['rexglue-sdk/src/core', 'rexglue-sdk/src/kernel/xboxkrnl', 'rexglue-sdk/src/system',
             'rexglue-sdk/src/graphics', 'rexlego/src']
HDR33 = 'rexglue-sdk/include/rex/graphics/d3d12/pipeline_cache.h'  # the one overlay header (--include-first)
# file (rel. to DimensionsRecomp) -> before sha256/16, after sha256/16 (COMMIT-PLAN.md section 1)
HASHES = {
    'rexglue-sdk/src/core/clock.cpp': ('A07EE16C9C5CC4BE', 'EAE926AC812F7EFD'),
    'rexglue-sdk/src/core/timer_queue.cpp': ('015C04A22DACC592', 'EF70211E5D248A94'),
    'rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp': ('8DF708B87A945F07', 'CEB5529AC853D5A8'),
    'rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp': ('6E20D417F0ED93A5', '7CA55716E7092199'),
    'rexglue-sdk/src/system/runtime.cpp': ('306B692BC091A56F', 'A997D0059A69FF99'),
    'rexglue-sdk/src/system/xmemory.cpp': ('BCA5E1CF63686E73', '3745C04AAC8AF75D'),
    'rexglue-sdk/src/system/xobject.cpp': ('189CA288893B1A36', '691A34BB64E11EA2'),
    'rexglue-sdk/src/system/xthread.cpp': ('FAEF9B99C893F684', '3B50A95E76B10377'),
    'rexglue-sdk/src/graphics/shared_memory.cpp': ('A4A31038ABDFF94A', 'E2465A155E22C20B'),
    'rexlego/src/gpu_wait_backoff.cpp': ('01D9F8F3464C8614', '74115EEA26C4AEB2'),
    'rexlego/src/gpu_native/shaders.cpp': ('9567FE3F3B63637D', '4B8250E976A38401'),
}
HASHES33 = {  # #33, s33-popin-nohunk5.patch 57CFA8AD (devoff4b-s33-bin MANIFEST after-hashes)
    HDR33: ('9322AD374BF4BBEC', '0BAF28BE633759CD'),
    'rexglue-sdk/src/graphics/d3d12/command_processor.cpp': ('027204B53A271D69', '00EA93D3E9115B01'),
    'rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp': ('DA77744302CFC149', 'C4CB51CC6D2A6429'),
    'rexglue-sdk/src/graphics/frame_stats.h': ('EFA82A7C20F6BF37', '9F3C4F9DC58DCA5D'),
}
ALL = dict(HASHES, **HASHES33)
DEFAULT_OFF = b'REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false,'
DEFAULT_Q500 = b'#define LEGO_GPU_WAIT_BACKOFF_DEFAULT_US 500'
# SDK legs: source (rel. to rexglue-sdk/src) -> object as written in snap1-sdk's Release ninja files
RT = {
    'core/clock.cpp': 'src/core/CMakeFiles/rexcore.dir/Release/clock.cpp.obj',
    'core/timer_queue.cpp': 'src/core/CMakeFiles/rexcore.dir/Release/timer_queue.cpp.obj',
    'kernel/xboxkrnl/xboxkrnl_rtl.cpp':
        'src/system/CMakeFiles/rexruntime.dir/Release/__/kernel/xboxkrnl/xboxkrnl_rtl.cpp.obj',
    'kernel/xboxkrnl/xboxkrnl_threading.cpp':
        'src/system/CMakeFiles/rexruntime.dir/Release/__/kernel/xboxkrnl/xboxkrnl_threading.cpp.obj',
    'system/runtime.cpp': 'src/system/CMakeFiles/rexruntime.dir/Release/runtime.cpp.obj',
    'system/xmemory.cpp': 'src/system/CMakeFiles/rexruntime.dir/Release/xmemory.cpp.obj',
    'system/xobject.cpp': 'src/system/CMakeFiles/rexruntime.dir/Release/xobject.cpp.obj',
    'system/xthread.cpp': 'src/system/CMakeFiles/rexruntime.dir/Release/xthread.cpp.obj',
}
GPU_PRE = 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/'
GPU_REL = ['shared_memory.cpp', 'command_processor.cpp'] + ['d3d12/%s.cpp' % n for n in (
    'command_processor', 'deferred_command_list', 'graphics_system', 'pipeline_cache', 'primitive_processor',
    'render_target_cache', 'shared_memory', 'texture_cache')]  # == prep-s33 tag s33 (devoff4b-s33), 10 objects
GPU = {'graphics/' + r: GPU_PRE + r + '.obj' for r in GPU_REL}
HDR_DEPS = ('rexglue-sdk/include/rex/graphics/d3d12/pipeline_cache.h', 'rexglue-sdk/src/graphics/frame_stats.h')
XE = {'gpu_wait_backoff.cpp': 'CMakeFiles/legodimensions.dir/src/gpu_wait_backoff.cpp.obj'}  # rel. to rexlego/src
NAT_MIN = {'gpu_native/shaders.cpp', 'gpu_native/device.cpp', 'gpu_native/shader_archive.cpp',
           'gpu_native/pipeline_library.cpp'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def manifest_sha(bin_dir, name):
    for ln in open(os.path.join(bin_dir, 'MANIFEST.txt'), encoding='utf-8', errors='replace'):
        c = ln.rstrip('\r\n').split('\t')
        if len(c) >= 4 and not ln.startswith('#') and c[0] == name:
            return c[3].upper()
    return None


def shab(b):
    return hashlib.sha256(b).hexdigest().upper()


def git(repo, *args):
    """Read-only git query in a live repo; returns (rc, stdout bytes, stderr text)."""
    p = subprocess.run(['git', '-C', repo, '-c', 'core.autocrlf=false'] + list(args), capture_output=True)
    return p.returncode, p.stdout, p.stderr.decode('utf-8', 'replace').strip()


def ninja_deps(build_dir, ninja_file=None):
    cmd = [NINJA, '-C', build_dir] + (['-f', ninja_file] if ninja_file else []) + ['-t', 'deps']
    p = subprocess.run(cmd, capture_output=True, text=True)
    deps, cur = {}, None
    for ln in p.stdout.splitlines():
        if ln and not ln.startswith(' '):
            cur = ln.split(':')[0].replace('\\', '/')
            deps[cur] = []
        elif ln.strip() and cur:
            deps[cur].append(ln.strip().replace('\\', '/').lower())
    return p.returncode, deps, (p.stderr or '').strip()[:300]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sdk', required=True, help='pushed rexglue-sdk commit (perf/opt)')
    ap.add_argument('--super', required=True, help='pushed DimensionsRecomp commit (perf/opt)')
    ap.add_argument('--dry-run', action='store_true', help='checks only; writes nothing')
    ap.add_argument('--no-gen', action='store_true', help='skip the cmake -P fingerprint step')
    a = ap.parse_args()
    out, fails = [], []

    def say(s):
        out.append(s)
        print(s, flush=True)

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)
        return ok

    def finish():
        say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d: %s)' % (len(fails), '; '.join(fails))))
        if os.path.isdir(B) and not a.dry_run:
            with open(os.path.join(B, 'prep.txt'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(out) + '\n')
        return 1 if fails else 0

    say('# prep-final2 (M2) %s%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), ' DRY RUN' if a.dry_run else ''))
    if os.path.exists(HOLD):
        check('no HOLD file', False)
        return finish()
    # The pushed commits (live repos, read-only queries).
    full = {}
    for nm, repo, c in (('sdk', LIVE_SDK, a.sdk), ('super', LIVE_SUPER, a.super), ('base sdk', LIVE_SDK, BASE_SDK),
                        ('base super', LIVE_SUPER, BASE_SUPER)):
        rc, o, e = git(repo, 'rev-parse', '--verify', '%s^{commit}' % c)
        full[nm] = o.decode().strip()
        check('%s commit %s resolves' % (nm, c), rc == 0, full[nm] or e)
    if fails:
        return finish()
    say('commits: sdk %s (base %s), super %s (base %s)' % (full['sdk'], full['base sdk'], full['super'],
                                                            full['base super']))
    want_sdk = sorted(f[len('rexglue-sdk/'):] for f in ALL if f.startswith('rexglue-sdk/'))
    want_sup = sorted([f for f in ALL if f.startswith('rexlego/')] + ['rexglue-sdk'])
    for nm, repo, base, want in (('sdk', LIVE_SDK, full['base sdk'], want_sdk),
                                 ('super', LIVE_SUPER, full['base super'], want_sup)):
        rc, o, e = git(repo, 'diff', '--name-only', '--no-renames', base, full[nm])
        got = sorted(o.decode().split())
        check('%s: git diff --name-only base..commit == exactly the %d planned paths' % (nm, len(want)),
              rc == 0 and got == want, 'extra %s, missing %s' % (sorted(set(got) - set(want)),
                                                                sorted(set(want) - set(got))))
        rc, o, e = git(repo, 'merge-base', '--is-ancestor', base, full[nm])
        check('%s: base %s is an ancestor of %s' % (nm, base[:7], full[nm][:7]), rc == 0, e)
    rc, o, e = git(LIVE_SUPER, 'ls-tree', full['super'], 'rexglue-sdk')
    gl = o.decode().split()
    check('super gitlink rexglue-sdk == sdk commit', rc == 0 and len(gl) >= 3 and gl[1] == 'commit' and
          gl[2] == full['sdk'], o.decode().strip() or e)
    blobs = {}
    for f, (bh, ah) in sorted(ALL.items()):
        repo, c, p = (LIVE_SDK, full['sdk'], f[len('rexglue-sdk/'):]) if f.startswith('rexglue-sdk/') else \
            (LIVE_SUPER, full['super'], f)
        rc, o, e = git(repo, 'cat-file', 'blob', '%s:%s' % (c, p))
        check('committed blob %s read (%d B, sha256 %s)' % (f, len(o), shab(o)[:16]), rc == 0 and o, e)
        check('committed blob %s: LF only (no CR)' % f, b'\r' not in o)
        # EOL form: the snap1 base file's (snap1 = the live working copy, mixed EOL). LF base -> the blob bytes;
        # CRLF base (only rexlego/src/gpu_native/shaders.cpp) -> the blob with LF -> CRLF, i.e. the autocrlf=true
        # checkout. Same rule as prep-final's "line endings kept"; keeps the fingerprint input == nativefinal's.
        sb = open(os.path.join(SNAP, f), 'rb').read()
        crlf = sb.count(b'\r\n') > 0
        check('snap1 base %s EOL is uniform (%s)' % (f, 'CRLF' if crlf else 'LF'),
              sb.count(b'\r\n') == sb.count(b'\n') if crlf else b'\r' not in sb)
        form = o.replace(b'\n', b'\r\n') if crlf else o
        blobs[f] = form
        h = shab(form)
        ref = os.path.join(NEW, f) if f in HASHES else os.path.join(S33, f[len('rexglue-sdk/'):])
        check('committed %s in the base EOL form (%s) %s == after column and == %s' % (
            f, 'CRLF' if crlf else 'LF = blob', h[:16], 'final/work/new' if f in HASHES else
            's33/s33/sdk (devoff4b-s33)'), h.startswith(ah) and h == sha(ref))
        say('blob %s %s %s B -> overlay %s %s' % (f, shab(o), len(o), 'CRLF' if crlf else 'LF', h))
        hb = shab(sb)
        check('snap1 before %s %s' % (f, hb[:16]), hb.startswith(bh))
    pc = blobs.get('rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp', b'')
    check('default OFF: committed pipeline_cache.cpp has %s' % DEFAULT_OFF.decode(), pc.count(DEFAULT_OFF) == 1)
    check('default q500: committed gpu_wait_backoff.cpp has %s' % DEFAULT_Q500.decode(),
          blobs.get('rexlego/src/gpu_wait_backoff.cpp', b'').count(DEFAULT_Q500) == 1)
    check('shared DLL %s == E3CB99CF' % os.path.relpath(SHARED, R), sha(SHARED) == SHARED_SHA)
    # Base binaries the CTL relinks are compared with == the staged reference bins.
    for tree, bin_, names in ((OFF, 'devoff4b-bin', ('legodimensions.exe', 'legodimensions.map')),
                              (ON, 'native4b-bin', ('legodimensions.exe', 'legodimensions.map'))):
        for n in names:
            h, m = sha(os.path.join(tree, n)), manifest_sha(os.path.join(A2, bin_), n)
            check('%s/%s == %s row (%s)' % (os.path.basename(tree), n, bin_, h[:16]), h == m)
    # The #33 headers: users only in rexgpu-xenos (== the planned gpu set), none in the game trees, not in the PCH.
    rc, sd, e = ninja_deps(SDKB, 'build-Release.ninja')
    check('ninja -t deps snap1-sdk (Release) exit 0', rc == 0 and sd, e)
    users = sorted(o for o, d in sd.items() if any(x.endswith(h.lower()) for x in d for h in HDR_DEPS))
    say('snap1-sdk objects depending on the #33 headers (%d): %s' % (len(users), ', '.join(users)))
    check('#33 header users are all rexgpu-xenos.dir/Release objects', all(o.startswith(GPU_PRE) for o in users),
          ', '.join(o for o in users if not o.startswith(GPU_PRE)))
    gset = set(users) | {GPU_PRE + 'shared_memory.cpp.obj'}
    check('gpu object set (#33 header users + shared_memory.cpp) == the 10 planned', gset == set(GPU.values()),
          'unexpected: %s' % ', '.join(sorted(gset ^ set(GPU.values()))))
    pch = [o for o in sd if o.startswith(GPU_PRE) and 'cmake_pch' in o]
    check('rexgpu-xenos Release PCH has a deps entry', bool(pch), ', '.join(pch))
    check('rexgpu-xenos PCH does not include the #33 headers (B2: PCH reuse valid)',
          pch and not any(x.endswith(h.lower()) for o in pch for x in sd[o] for h in HDR_DEPS))
    # Native TU set: objects whose ninja deps include native_gpu_build_info.h (+ shaders.cpp.obj, the changed TU).
    rc, deps, e = ninja_deps(ON)
    check('ninja -t deps snap1-on exit 0', rc == 0, e)
    rc2, deps_off, e2 = ninja_deps(OFF)
    check('ninja -t deps snap1-off exit 0', rc2 == 0, e2)
    for nm, dd in (('snap1-on', deps), ('snap1-off', deps_off)):
        bad = [o for o, d in dd.items() if any(x.endswith(h.lower()) for x in d for h in HDR_DEPS)]
        check('%s: no object depends on the #33 headers' % nm, not bad, ', '.join(bad[:5]))
    pre = 'CMakeFiles/legodimensions.dir/src/'
    hdr = [o for o, d in deps.items() if any(x.endswith('/native_gpu_build_info.h') for x in d)]
    say('objects including native_gpu_build_info.h (%d): %s' % (len(hdr), ', '.join(sorted(hdr))))
    nat = sorted(set(o[len(pre):-len('.obj')] for o in hdr if o.startswith(pre)) | {'gpu_native/shaders.cpp'})
    say('native TU set (%d): %s' % (len(nat), ', '.join(nat)))
    check('native TU set == the 4 planned (shaders, device, shader_archive, pipeline_library)', set(nat) == NAT_MIN,
          'unexpected: %s' % ', '.join(sorted(set(nat) ^ NAT_MIN)))
    if os.path.exists(B):
        check('final2/b is new', False)
    if fails or a.dry_run:
        if a.dry_run:
            say('dry run: nothing written')
        return finish()
    # Overlay: snap1 copies, the one #33 include header, then the committed blob bytes over the 15 files.
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(SNAP, d), os.path.join(OV, d))
    os.makedirs(os.path.dirname(os.path.join(OV, HDR33)))
    shutil.copy2(os.path.join(SNAP, HDR33), os.path.join(OV, HDR33))
    n, bad = 0, []
    for d in COPY_DIRS:
        for dp, _, fs in os.walk(os.path.join(SNAP, d)):
            for fn in fs:
                s = os.path.join(dp, fn)
                n += 1
                if sha(s) != sha(os.path.join(OV, os.path.relpath(s, SNAP))):
                    bad.append(os.path.relpath(s, SNAP))
    n += 1
    if sha(os.path.join(SNAP, HDR33)) != sha(os.path.join(OV, HDR33)):
        bad.append(HDR33)
    check('overlay copy equals snap1 (%d files in %d dirs + %s)' % (n, len(COPY_DIRS), HDR33), not bad,
          ', '.join(bad[:5]))
    for f, (bh, ah) in sorted(ALL.items()):
        p = os.path.join(OV, f)
        check('overlay before %s == snap1' % f, sha(p).startswith(bh))
        with open(p, 'wb') as fo:
            fo.write(blobs[f])
        h = sha(p)
        check('overlay after %s %s == committed blob (base EOL form)' % (f, h[:16]), h == shab(blobs[f]) and h.startswith(ah))
    if fails:
        return finish()
    # Leg lists.
    sdk_s, sdk_o = os.path.join(SNAP, 'rexglue-sdk', 'src'), os.path.join(OV, 'rexglue-sdk', 'src')
    lego_s, lego_o = os.path.join(SNAP, 'rexlego', 'src'), os.path.join(OV, 'rexlego', 'src')
    nat_map = {r: 'CMakeFiles/legodimensions.dir/src/%s.obj' % r for r in nat}
    legs = {'rt': (RT, sdk_s, sdk_o), 'gpu': (GPU, sdk_s, sdk_o), 'xe': (XE, lego_s, lego_o),
            'nat': (nat_map, lego_s, lego_o)}
    for leg, (m, s_root, o_root) in legs.items():
        top = os.path.join(B, leg)
        os.makedirs(top)
        rows = {'list-on.tsv': [], 'list-ctl.tsv': [], 'replace-on.txt': [], 'replace-ctl.txt': []}
        for rel, obj in sorted(m.items()):
            src = os.path.join(s_root, rel.replace('/', os.sep))
            osrc = os.path.join(o_root, rel.replace('/', os.sep))
            if sha(src) == sha(osrc) and leg != 'gpu':
                osrc = src  # unchanged TU (native header users): compile snap1's source in the ON leg too
            # gpu: always the overlay source, so the relative "frame_stats.h" / "../frame_stats.h" includes resolve
            # to the overlay's #33 frame_stats.h (as devoff4b-s33 did).
            # Keep the object's own basename (lld-link's /MAP names objects by basename). gpu: graphics/ and
            # graphics/d3d12/ share basenames, and recompile.py names its logs by object basename, so the d3d12 objects
            # are d3d12__<name>.obj, exactly as prep-s33 / devoff4b-s33 (whose gpu CTL == E3CB99CF except the TDS).
            uniq = obj[len(GPU_PRE):].replace('/', '__') if leg == 'gpu' else obj.split('/')[-1]
            if any(r.split('=', 1)[1].replace('\\', '/').endswith('/obj-on/' + uniq) for r in rows['replace-on.txt']):
                check('leg %s: object basenames unique' % leg, False, uniq)
                return finish()
            oon, octl = os.path.join(top, 'obj-on', uniq), os.path.join(top, 'obj-ctl', uniq)
            rows['list-on.tsv'].append('%s\t%s\t%s' % (src, osrc, oon))
            rows['list-ctl.tsv'].append('%s\t%s\t%s' % (src, src, octl))
            rows['replace-on.txt'].append('%s=%s' % (obj, oon))
            rows['replace-ctl.txt'].append('%s=%s' % (obj, octl))
        for nm, rr in rows.items():
            with open(os.path.join(top, nm), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(rr) + '\n')
        say('leg %s: %d TU(s): %s' % (leg, len(m), ', '.join(sorted(m))))
    # Native fingerprint headers (cmake -P on copies of snap1-on's own script).
    if not a.no_gen:
        scr = open(os.path.join(ON, 'generate-native-gpu-fingerprint.cmake'), encoding='utf-8', newline='').read()
        fs = lambda p: p.replace('\\', '/')
        o_hdr, o_txt = fs(os.path.join(ON, 'generated', 'native_gpu_build_info.h')), fs(os.path.join(ON,
                                                                                          'native-gpu-build.txt'))
        s_in, o_in = fs(os.path.join(lego_s, 'gpu_native', 'shaders.cpp')), fs(os.path.join(lego_o, 'gpu_native',
                                                                                          'shaders.cpp'))
        check('fingerprint script: header/txt outputs named once each', scr.count(o_hdr) == 1 and scr.count(o_txt) == 1)
        check('fingerprint script: shaders.cpp input named once', scr.count(s_in) == 1, str(scr.count(s_in)))
        for g in ('gen-ctl', 'gen-on'):
            gd = os.path.join(B, 'nat', g)
            os.makedirs(gd)
            t = scr.replace(o_hdr, fs(os.path.join(gd, 'native_gpu_build_info.h'))).replace(
                o_txt, fs(os.path.join(gd, 'native-gpu-build.txt')))
            if g == 'gen-on':
                t = t.replace(s_in, o_in)
            sp = os.path.join(B, 'nat', 'fp-%s.cmake' % g[4:])
            with open(sp, 'w', encoding='utf-8', newline='') as f:
                f.write(t)
            q = subprocess.run([CMAKE, '-P', sp], capture_output=True, text=True)
            check('cmake -P %s exit 0' % os.path.basename(sp), q.returncode == 0, (q.stdout + q.stderr).strip()[:300])
        if not fails:
            rd = lambda p: open(p, 'rb').read()
            gc, go = os.path.join(B, 'nat', 'gen-ctl'), os.path.join(B, 'nat', 'gen-on')
            check('gen-ctl header == snap1-on header (byte)', rd(os.path.join(gc, 'native_gpu_build_info.h')) ==
                  rd(os.path.join(ON, 'generated', 'native_gpu_build_info.h')))
            check('gen-ctl native-gpu-build.txt == snap1-on (byte)', rd(os.path.join(gc, 'native-gpu-build.txt')) ==
                  rd(os.path.join(ON, 'native-gpu-build.txt')))
            hn = rd(os.path.join(go, 'native_gpu_build_info.h'))
            check('gen-on header has %s, not %s' % (FP_NEW, FP_OLD), FP_NEW.encode() in hn and FP_OLD.encode() not in hn)
            check('gen-on header == snap1-on header with only the fingerprint swapped',
                  hn == rd(os.path.join(ON, 'generated', 'native_gpu_build_info.h')).replace(FP_OLD.encode(),
                                                                                           FP_NEW.encode()))
            say('gen-on native-gpu-build.txt: %s' % rd(os.path.join(go, 'native-gpu-build.txt')).decode().strip())
    return finish()


if __name__ == '__main__':
    sys.exit(main())
