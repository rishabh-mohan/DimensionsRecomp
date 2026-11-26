#!/usr/bin/env python3
# make_patch.py (E13.1, S5 phase 3 F2): writes native3_boot_check.py (patched copy of
# DimensionsRecomp/perf/bench/agent7/native3_boot_check.py, LF like the repo file) and
# native3_boot_check-f2.diff (git diff --no-index, bytes captured via subprocess). Repo file untouched.
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
REPO = os.path.join(WS, 'DimensionsRecomp')
REL = 'perf/bench/agent7/native3_boot_check.py'
SRC = os.path.join(REPO, *REL.split('/'))

REPL = [
    # Docstring, group C.
    ("""     INFO: rexruntime.dll is a non-FFX SDK (it has present_effect but not
     present_fsr_sharpness_reduction), so the toml's present_effect='fsr' can't be selected.
     C assumes option (a). A FidelityFX-header DLL (option (b)) makes FSR 1 selectable, and is
     flagged WARN.
""",
     """     rexruntime.dll is classified by the cvar names it defines (the exe is no use: rexlego names
     the present_fsr_* cvars itself, settings_registry.cpp:41-42):
      - FidelityFX-header SDK (option (b)): present_fsr_quality_mode / present_cas_additional_sharpness,
        which presenter.cpp defines only under REX_HAS_FIDELITYFX_SDK. present_effect='fsr' can be
        selected; flagged WARN.
      - native FSR 1 cvars only (present_fsr_sharpness_reduction / present_fsr_max_upsampling_passes
        without the FFX-only ones: the native-fsr1 SDK patch): present_effect accepts 'fsr' and the
        native renderer runs its own FSR 1. WARN if the run-dir toml selects 'fsr', else INFO.
      - present_effect alone: a non-FFX SDK, bilinear-only, the toml's 'fsr' is rejected. INFO.
     An amd_fidelityfx_dx12 reference in rexruntime.dll (the FFX runtime) is INFO only: the native
     bins ship amd_fidelityfx_dx12.dll without loading it, and option (b) needs no runtime.
     C assumes option (a) or bilinear.
"""),
    # The run-dir toml line.
    ("""    eff = [x.strip() for x in toml_lines if re.match(r"^\\s*present_effect\\s*=", x)]
    if eff:
        rep.add("INFO", "run-dir toml has %s (accepted only by an SDK with the FidelityFX headers)" % eff[0])
""",
     """    eff = [x.strip() for x in toml_lines if re.match(r"^\\s*present_effect\\s*=", x)]
    toml_fsr = bool(eff) and re.sub(r"\\s*#.*$", "", eff[0].split("=", 1)[1]).strip().strip("'\\"").lower() == "fsr"
    if eff:
        rep.add("INFO", "run-dir toml has %s ('fsr' is accepted by an SDK with the FidelityFX headers or the "
                "native-fsr1 patch)" % eff[0])
"""),
    # The DLL classification.
    ("""    has_effect = b"present_effect" in data
    ffx = [n.decode() for n in (b"present_fsr_sharpness_reduction", b"present_fsr_max_upsampling_passes") if n in data]
    tag = "%s (sha256 %s)" % (os.path.relpath(dll), sha16(dll))
    if has_effect and not ffx:
        rep.add("INFO", "%s: a non-FFX SDK (present_effect is there, the FSR 1 cvars aren't), so present_effect "
                "is bilinear-only and the toml's 'fsr' is rejected" % tag)
    elif ffx:
        rep.add("WARN", "%s has %s: an SDK with the FidelityFX headers (option (b)?), so present_effect='fsr' "
                "can be selected and bilinear is not the expected present" % (tag, "/".join(ffx)))
    else:
        rep.add("WARN", "%s: no present_effect string" % tag)
""",
     """    has_effect, ffx, fsr1, ffx_rt = classify_present_sdk(data)
    tag = "%s (sha256 %s)" % (os.path.relpath(dll), sha16(dll))
    if ffx:
        rep.add("WARN", "%s has %s: an SDK with the FidelityFX headers (option (b)?), so present_effect='fsr' "
                "can be selected and bilinear is not the expected present" % (tag, "/".join(ffx)))
    elif fsr1 and has_effect:
        rep.add("WARN" if toml_fsr else "INFO",
                "%s: native FSR 1 cvars (%s) without the FFX-only ones (native-fsr1 SDK), so present_effect "
                "accepts 'fsr' and the native renderer runs its own FSR 1%s" % (
                    tag, "/".join(fsr1), "; the toml selects it, so bilinear is not the expected present"
                    if toml_fsr else ""))
    elif has_effect:
        rep.add("INFO", "%s: a non-FFX SDK (present_effect is there, the FSR cvars aren't), so present_effect "
                "is bilinear-only and the toml's 'fsr' is rejected" % tag)
    else:
        rep.add("WARN", "%s: no present_effect string" % tag)
    if ffx_rt:
        rep.add("INFO", "%s references amd_fidelityfx_dx12 (the FFX runtime)" % tag)
"""),
    # The helper, before check_bilinear.
    ("""def check_bilinear(rep, run_dir, bin_dir, log, rows, toml_lines):
""",
     """# presenter.cpp (rexglue-sdk) defines these two only under REX_HAS_FIDELITYFX_SDK.
FFX_ONLY_CVARS = (b"present_fsr_quality_mode", b"present_cas_additional_sharpness")
# Defined under REX_HAS_FIDELITYFX_SDK and, with the native-fsr1 patch, in non-FFX builds too.
FSR1_CVARS = (b"present_fsr_sharpness_reduction", b"present_fsr_max_upsampling_passes")


def classify_present_sdk(data):
    \"\"\"(has present_effect, FFX-only cvar names, FSR 1 cvar names, FFX runtime referenced) of a binary.\"\"\"
    names = lambda ns: [n.decode() for n in ns if n in data]
    return (b"present_effect" in data, names(FFX_ONLY_CVARS), names(FSR1_CVARS),
            b"amd_fidelityfx_dx12" in data.lower())


def check_bilinear(rep, run_dir, bin_dir, log, rows, toml_lines):
"""),
]


def main():
    src = open(SRC, 'rb').read()
    assert b'\r' not in src
    text = src.decode('utf-8')
    for old, new in REPL:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new)
    dst = os.path.join(HERE, 'native3_boot_check.py')
    with open(dst, 'wb') as f:
        f.write(text.encode('utf-8'))
    # git diff --no-index from the repo dir with relative-ish labels; rewrite the header paths to a/<REL> b/<REL>.
    p = subprocess.run(['git', 'diff', '--no-index', '--no-color', '--', SRC, dst], capture_output=True)
    assert p.returncode == 1, p.stderr
    lines = p.stdout.split(b'\n')
    out = []
    for l in lines:
        if l.startswith(b'diff --git '):
            l = b'diff --git a/' + REL.encode() + b' b/' + REL.encode()
        elif l.startswith(b'--- '):
            l = b'--- a/' + REL.encode()
        elif l.startswith(b'+++ '):
            l = b'+++ b/' + REL.encode()
        elif l.startswith(b'index '):
            l = l.split(b' ')[0] + b' ' + l.split(b' ')[1] + b' 100644'
        out.append(l)
    diff = b'\n'.join(out)
    assert b'\r' not in diff
    dpath = os.path.join(HERE, 'native3_boot_check-f2.diff')
    with open(dpath, 'wb') as f:
        f.write(diff)
    c = subprocess.run(['git', '-C', REPO, 'apply', '--check', '-v', dpath], capture_output=True, text=True)
    for path in (dst, dpath):
        print(hashlib.sha256(open(path, 'rb').read()).hexdigest().upper(), os.path.relpath(path, WS))
    plus = sum(1 for l in out if l.startswith(b'+') and not l.startswith(b'+++'))
    minus = sum(1 for l in out if l.startswith(b'-') and not l.startswith(b'---'))
    print('diff +%d/-%d; git apply --check (working tree, not applied): rc=%d %s' % (
        plus, minus, c.returncode, (c.stdout + c.stderr).strip().replace('\n', ' | ')))
    return c.returncode


if __name__ == '__main__':
    sys.exit(main())
