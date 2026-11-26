#!/usr/bin/env python3
# test_f2.py (E13.1, S5 phase 3 F2): runs check_bilinear() of the ORIGINAL (repo) and the PATCHED (f2/)
# native3_boot_check.py against real binaries and prints group C's verdict lines. Writes test.txt here.
# Static: reads binaries, copies small stand-ins into f2/inputs/, never launches anything.
import contextlib, hashlib, importlib.util, io, os, re, shutil, subprocess, sys

sys.dont_write_bytecode = True  # no __pycache__ in the repo's agent7 dir

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
AGENT7 = os.path.join(WS, 'DimensionsRecomp', 'perf', 'bench', 'agent7')
SDK = os.path.join(WS, 'DimensionsRecomp', 'rexglue-sdk')
sys.path.insert(0, AGENT7)  # native_frames_summary
out = []


def say(s=''):
    out.append(s)
    print(s, flush=True)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16].upper()


orig_py = os.path.join(HERE, 'inputs', 'native3_boot_check-HEAD.py')  # ORIG = the HEAD blob (the repo file may be patched)
os.makedirs(os.path.dirname(orig_py), exist_ok=True)
open(orig_py, 'wb').write(subprocess.run(['git', '-C', os.path.join(WS, 'DimensionsRecomp'), 'show',
                                          'HEAD:perf/bench/agent7/native3_boot_check.py'], capture_output=True).stdout)
orig = load('n3_orig', orig_py)
new = load('n3_f2', os.path.join(HERE, 'native3_boot_check.py'))

# Inputs. (label, dir holding rexruntime.dll, what it is)
inp = os.path.join(HERE, 'inputs')
os.makedirs(inp, exist_ok=True)
cases = []
nf2 = os.path.join(WS, 'build', 'agent2', 'nativefinal2-bin')
cases.append(('nativefinal2', nf2, 'real rexruntime.dll (non-FFX a7e79c0-era SDK)'))
d = os.path.join(inp, 'native-fsr1-obj')
os.makedirs(d, exist_ok=True)
obj = os.path.join(WS, 'build', 'agent2', 's5', 'native-fsr1', 'obj', 'presenter.cpp.obj')
shutil.copyfile(obj, os.path.join(d, 'rexruntime.dll'))
cases.append(('native-fsr1 obj', d, 'stand-in: native-fsr1 presenter.cpp.obj (%s) copied as rexruntime.dll' % sha16(obj)))
# FFX: no FFX-built binary exists (s5/ffx-a is fsyntax-only; no rexruntime.dll under build/ has
# present_fsr_quality_mode). Synthetic stand-in: the cvar names the a7e79c0 presenter.cpp defines in its
# REX_HAS_FIDELITYFX_SDK branch, NUL-separated, plus every other cvar name of the TU.
src = subprocess.run(['git', '-C', SDK, 'show', 'a7e79c0:src/ui/presenter.cpp'], capture_output=True, text=True,
                     encoding='utf-8').stdout
ffx_branch = src[src.index('#if defined(REX_HAS_FIDELITYFX_SDK)'):src.index('#else')]
rest = src[src.index('#endif', src.index('#else')):]
names = re.findall(r'REXCVAR_DEFINE_\w+\(\s*(\w+)', ffx_branch) + re.findall(r'REXCVAR_DEFINE_\w+\(\s*(\w+)', rest)
d = os.path.join(inp, 'ffx-synthetic')
os.makedirs(d, exist_ok=True)
open(os.path.join(d, 'rexruntime.dll'), 'wb').write(b'\0'.join(n.encode() for n in names) + b'\0')
cases.append(('FFX (synthetic)', d, 'SYNTHETIC: cvar names of the a7e79c0 FFX branch: %s' % ', '.join(
    re.findall(r'REXCVAR_DEFINE_\w+\(\s*(\w+)', ffx_branch))))

tomls = [('harness toml (fsr)', os.path.join(WS, 'harness', 'legodimensions.toml')),
         ('perf-bilinear.toml', os.path.join(WS, 'build', 'agent2', 's5', 'native-fsr1', 'perf-bilinear.toml'))]
# M10 NIT N1: a trailing '# comment' on the present_effect line must still read as 'fsr'.
cmt = os.path.join(inp, 'harness-comment.toml')
open(cmt, 'w', encoding='utf-8', newline='\n').write(re.sub(
    r"(?m)^present_effect = 'fsr'$", "present_effect = 'fsr'  # FSR 1 on (N1 test)",
    open(tomls[0][1], encoding='utf-8').read()))
tomls.append(("harness toml + '# comment' (N1)", cmt))
rows = [{'frame': '1', 'spatial_fsr_presented': '0', 'fsr_enabled': '0'}]


def run(mod, bin_dir, toml_path):
    lines = open(toml_path, encoding='utf-8').read().splitlines()
    buf = io.StringIO()
    rep = mod.Report()
    with contextlib.redirect_stdout(buf):
        mod.check_bilinear(rep, None, bin_dir, None, rows, lines)
    keep = [l for l in buf.getvalue().splitlines() if 'rexruntime.dll' in l or 'run-dir toml' in l]
    return rep.verdict('C'), keep


for label, bdir, what in cases:
    dll = os.path.join(bdir, 'rexruntime.dll')
    data = open(dll, 'rb').read()
    say('== %s: %s' % (label, what))
    say('   %s sha16 %s, %d B; classify_present_sdk = %r' % (os.path.relpath(dll, WS), sha16(dll), len(data),
                                                           new.classify_present_sdk(data)))
    for tl, tp in tomls:
        for mname, mod in (('ORIG', orig), ('F2  ', new)):
            v, keep = run(mod, bdir, tp)
            say('   [%s | %s] group C %s' % (mname, tl, v))
            for l in keep:
                if 'run-dir toml' in l:
                    continue
                say('     ' + re.sub(r'\S*rexruntime\.dll \(sha256 \w+\)', 'rexruntime.dll', l.strip()))
    say()

# Exe vs DLL: the game exe names the present_fsr_* cvars itself (rexlego), so it can't be the probe.
exe = os.path.join(nf2, 'legodimensions.exe')
data = open(exe, 'rb').read()
say('== exe, not a check input: %s classify_present_sdk = %r' % (os.path.relpath(exe, WS), new.classify_present_sdk(data)))
say('   (the exe always has the FSR 1 names (rexlego settings_registry.cpp:41-42, device.cpp:2064/2066), whatever the SDK:'
    ' probing it would call every non-FFX SDK native-fsr1. The check reads rexruntime.dll, which is right.)')
ok = (new.classify_present_sdk(open(os.path.join(cases[0][1], 'rexruntime.dll'), 'rb').read())[1:3] == ([], [])
      and new.classify_present_sdk(open(os.path.join(cases[1][1], 'rexruntime.dll'), 'rb').read())[1:3]
      == ([], ['present_fsr_sharpness_reduction', 'present_fsr_max_upsampling_passes'])
      and new.classify_present_sdk(open(os.path.join(cases[2][1], 'rexruntime.dll'), 'rb').read())[1]
      == ['present_fsr_quality_mode', 'present_cas_additional_sharpness'])
assert '# FSR 1 on (N1 test)' in open(cmt, encoding='utf-8').read()
n1 = run(new, cases[1][1], cmt)[0] == run(new, cases[1][1], tomls[0][1])[0] != run(new, cases[1][1], tomls[1][1])[0]
say("N1: native-fsr1 obj, F2, toml with a trailing '# comment' gives the same verdict as the plain fsr toml "
    "(and not the bilinear one): %s" % ('PASS' if n1 else 'FAIL'))
ok = ok and n1
say('RESULT: %s (nativefinal2 = non-FFX, native-fsr1 = FSR 1 cvars only, FFX synthetic = FFX, N1)' % ('PASS' if ok else 'FAIL'))
open(os.path.join(HERE, 'test.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
sys.exit(0 if ok else 1)
