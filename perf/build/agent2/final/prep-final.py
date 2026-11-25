#!/usr/bin/env python3
# prep-final.py (M2, 2026-11-25): step 0 of BUILD-STEPS.md. Prepares the FINAL-DEFAULTS build WITHOUT touching
# snap1 / snap1-sdk / snap1-off / snap1-on (read-only there). Starts no compiler or linker.
#
#   python build/agent2/final/prep-final.py [--dry-run] [--no-gen]
#
# Writes only build/agent2/final/b/ (refuses an existing one):
#   DimensionsRecomp/  overlay = fresh byte copies of snap1's rexglue-sdk/src/{core,kernel/xboxkrnl,system,graphics} and
#                      rexlego/src, then FINAL-DEFAULTS.diff applied with `git -c core.autocrlf=false apply` (no-repo
#                      mode: GIT_CEILING_DIRECTORIES), before- and after-hashes checked (after == final/work/new).
#   rt/ gpu/ xe/ xeoff/ nat/ natoff/  list-ctl.tsv, list-on.tsv (recompile.py), replace-ctl.txt, replace-on.txt
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
FIN = os.path.join(A2, 'final')
B = os.path.join(FIN, 'b')
OV = os.path.join(B, 'DimensionsRecomp')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
NEW = os.path.join(FIN, 'work', 'new', 'DimensionsRecomp')
DIFF = os.path.join(FIN, 'FINAL-DEFAULTS.diff')
DIFF_SHA8 = '955543F5'
OFF, ON, SDKB = (os.path.join(A2, d) for d in ('snap1-off', 'snap1-on', 'snap1-sdk'))
NINJA = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
CMAKE = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
SHARED = os.path.join(SDKB, 'install', 'bin', 'rexgpu-xenos.dll')
SHARED_SHA = 'E3CB99CFDEA95E66EF093BF1B2A500076757FB727E60B046D70EBA01E05C9939'
FP_OLD, FP_NEW = '9b40acbbef4c57b3', '1616ce65e973c583'
COPY_DIRS = ['rexglue-sdk/src/core', 'rexglue-sdk/src/kernel/xboxkrnl', 'rexglue-sdk/src/system',
             'rexglue-sdk/src/graphics', 'rexlego/src']
# file (rel. to DimensionsRecomp) -> before sha256/16, after sha256/16 (BUILD-PLAN.md table)
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
GPU = {'graphics/shared_memory.cpp': 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/shared_memory.cpp.obj'}
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


def main():
    ap = argparse.ArgumentParser()
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

    say('# prep-final (M2) %s%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), ' DRY RUN' if a.dry_run else ''))
    if os.path.exists(HOLD):
        check('no HOLD file', False)
        return finish()
    ds = sha(DIFF)
    check('FINAL-DEFAULTS.diff sha256 %s' % ds, ds.startswith(DIFF_SHA8))
    say('diff sha256 %s' % ds)
    files = re.findall(r'^diff --git a/DimensionsRecomp/(\S+) b/', open(DIFF, encoding='utf-8', newline='').read(),
                       re.M)
    check('diff names exactly the 11 planned files', sorted(files) == sorted(HASHES), ', '.join(files))
    check('shared DLL %s == E3CB99CF' % os.path.relpath(SHARED, R), sha(SHARED) == SHARED_SHA)
    for f, (bh, _) in sorted(HASHES.items()):
        h = sha(os.path.join(SNAP, f))
        check('snap1 before %s %s' % (f, h[:16]), h.startswith(bh))
    # Base binaries the CTL relinks are compared with == the staged reference bins.
    for tree, bin_, names in ((OFF, 'devoff4b-bin', ('legodimensions.exe', 'legodimensions.map')),
                              (ON, 'native4b-bin', ('legodimensions.exe', 'legodimensions.map'))):
        for n in names:
            h, m = sha(os.path.join(tree, n)), manifest_sha(os.path.join(A2, bin_), n)
            check('%s/%s == %s row (%s)' % (os.path.basename(tree), n, bin_, h[:16]), h == m)
    # Native TU set: objects whose ninja deps include native_gpu_build_info.h (+ shaders.cpp.obj, the changed TU).
    p = subprocess.run([NINJA, '-C', ON, '-t', 'deps'], capture_output=True, text=True)
    check('ninja -t deps snap1-on exit 0', p.returncode == 0, (p.stderr or '').strip()[:300])
    deps, cur = {}, None
    for ln in p.stdout.splitlines():
        if ln and not ln.startswith(' '):
            cur = ln.split(':')[0].replace('\\', '/')
            deps[cur] = []
        elif ln.strip() and cur:
            deps[cur].append(ln.strip().replace('\\', '/').lower())
    pre = 'CMakeFiles/legodimensions.dir/src/'
    hdr = [o for o, d in deps.items() if any(x.endswith('/native_gpu_build_info.h') for x in d)]
    say('objects including native_gpu_build_info.h (%d): %s' % (len(hdr), ', '.join(sorted(hdr))))
    nat = sorted(set(o[len(pre):-len('.obj')] for o in hdr if o.startswith(pre)) | {'gpu_native/shaders.cpp'})
    say('native TU set (%d): %s' % (len(nat), ', '.join(nat)))
    check('native TU set == the 4 planned (shaders, device, shader_archive, pipeline_library)', set(nat) == NAT_MIN,
          'unexpected: %s' % ', '.join(sorted(set(nat) ^ NAT_MIN)))
    if os.path.exists(B):
        check('final/b is new', False)
    if fails or a.dry_run:
        if a.dry_run:
            say('dry run: nothing written')
        return finish()
    # Overlay.
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(SNAP, d), os.path.join(OV, d))
    n, bad = 0, []
    for d in COPY_DIRS:
        for dp, _, fs in os.walk(os.path.join(SNAP, d)):
            for fn in fs:
                s = os.path.join(dp, fn)
                n += 1
                if sha(s) != sha(os.path.join(OV, os.path.relpath(s, SNAP))):
                    bad.append(os.path.relpath(s, SNAP))
    check('overlay copy equals snap1 (%d files in %d dirs)' % (n, len(COPY_DIRS)), not bad, ', '.join(bad[:5]))
    crlf0 = {f: open(os.path.join(OV, f), 'rb').read().count(b'\r\n') for f in HASHES}
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=FIN)
    base = ['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', 'apply', '--verbose']
    for mode in (['--check'], []):
        q = subprocess.run(base + mode + [DIFF], cwd=B, capture_output=True, text=True, env=env)
        txt = (q.stdout + q.stderr).strip()
        say('git apply %s exit %d:\n%s' % (' '.join(mode) or '(apply)', q.returncode, txt))
        chk, skp = len(re.findall(r'^Checking patch ', txt, re.M)), len(re.findall(r'Skipped patch', txt))
        if not check('git apply %s: exit 0, 11 Checking, 0 Skipped' % (' '.join(mode) or '(apply)'),
                     q.returncode == 0 and chk == 11 and skp == 0, 'exit %d, %d, %d' % (q.returncode, chk, skp)):
            return finish()
    for f, (_, ah) in sorted(HASHES.items()):
        h = sha(os.path.join(OV, f))
        c1 = open(os.path.join(OV, f), 'rb').read().count(b'\r\n')
        check('after %s %s == table and == final/work/new' % (f, h[:16]),
              h.startswith(ah) and h == sha(os.path.join(NEW, f)))
        check('line endings kept %s (CRLF %d -> %d)' % (f, crlf0[f], c1), (crlf0[f] > 0) == (c1 > 0))
    # Leg lists.
    sdk_s, sdk_o = os.path.join(SNAP, 'rexglue-sdk', 'src'), os.path.join(OV, 'rexglue-sdk', 'src')
    lego_s, lego_o = os.path.join(SNAP, 'rexlego', 'src'), os.path.join(OV, 'rexlego', 'src')
    nat_map = {r: 'CMakeFiles/legodimensions.dir/src/%s.obj' % r for r in nat}
    legs = {'rt': (RT, sdk_s, sdk_o), 'gpu': (GPU, sdk_s, sdk_o), 'xe': (XE, lego_s, lego_o),
            'xeoff': (XE, lego_s, lego_o), 'nat': (nat_map, lego_s, lego_o), 'natoff': (nat_map, lego_s, lego_o)}
    for leg, (m, s_root, o_root) in legs.items():
        top = os.path.join(B, leg)
        os.makedirs(top)
        rows = {'list-on.tsv': [], 'list-ctl.tsv': [], 'replace-on.txt': [], 'replace-ctl.txt': []}
        for rel, obj in sorted(m.items()):
            src = os.path.join(s_root, rel.replace('/', os.sep))
            osrc = os.path.join(o_root, rel.replace('/', os.sep))
            if sha(src) == sha(osrc):
                osrc = src  # unchanged TU (native header users): compile snap1's source in the ON leg too
            uniq = obj.split('/')[-1]  # keep the object's own basename: lld-link's /MAP names objects by basename
            if uniq in [r.split('=')[1].replace('\\', '/').split('/')[-1] for r in rows['replace-on.txt']]:
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
