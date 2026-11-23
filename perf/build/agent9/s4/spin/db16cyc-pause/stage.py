# stage.py (Agent 9, run-2 task #17): stage #26 (codegen db16cyc -> spin-wait pause) as a diff.
# Reads only: the live SDK (DimensionsRecomp/rexglue-sdk, c5fe668), the S4a snap1 SDK copy and the codegen tomls.
# Writes only under build/agent9/s4/spin/db16cyc-pause/. Run from the workspace root:
#   cmd /c start "" /belownormal /wait /b python build\agent9\s4\spin\db16cyc-pause\stage.py
import difflib, hashlib, os, shutil, subprocess, sys

ROOT = os.getcwd()
HERE = os.path.join(ROOT, 'build', 'agent9', 's4', 'spin', 'db16cyc-pause')
LIVE = os.path.join(ROOT, 'DimensionsRecomp', 'rexglue-sdk')
SNAP = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
PATCH = r'C:\Program Files\Git\usr\bin\patch.exe'


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def rd(path):
    with open(path, 'rb') as f:
        return f.read()


def wr(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def edit(data, anchor, repl, what):
    n = data.count(anchor)
    if n != 1:
        sys.exit('%s: anchor found %d times' % (what, n))
    return data.replace(anchor, repl)


# --- SDK edits (all three files are LF-only, no BOM) ---
SDK_EDITS = {
    'include/rex/codegen/config.h': [(
        b'  bool vmxVectorFallbacks = false;  ///< SSE forms for VMX ops emitted as scalar lane loops\n',
        b'  bool vmxVectorFallbacks = false;  ///< SSE forms for VMX ops emitted as scalar lane loops\n'
        b'  bool db16cycPause = false;        ///< db16cyc emits simde_mm_pause() (a spin-wait hint)\n')],
    'src/codegen/config.cpp': [(
        b'  MergeBool(cfg.vmxVectorFallbacks, toml["vmx_vector_fallbacks"].value_or(false),\n'
        b'            hasBool("vmx_vector_fallbacks"), "vmx_vector_fallbacks");\n',
        b'  MergeBool(cfg.vmxVectorFallbacks, toml["vmx_vector_fallbacks"].value_or(false),\n'
        b'            hasBool("vmx_vector_fallbacks"), "vmx_vector_fallbacks");\n'
        b'  MergeBool(cfg.db16cycPause, toml["db16cyc_pause"].value_or(false), hasBool("db16cyc_pause"),\n'
        b'            "db16cyc_pause");\n')],
    'src/codegen/builders/system.cpp': [(
        b'bool build_db16cyc(BuilderContext& ctx) {\n'
        b'  // Xenon-specific 16-cycle delay hint, no effect in recompiled code\n'
        b'  (void)ctx;\n'
        b'  return true;\n'
        b'}\n',
        b'bool build_db16cyc(BuilderContext& ctx) {\n'
        b'  // Xenon-specific 16-cycle delay hint. By default it emits nothing (no effect in\n'
        b'  // recompiled code). With db16cyc_pause each one emits a spin-wait hint, so a\n'
        b'  // guest delay loop yields to the sibling hyperthread instead of running empty.\n'
        b'  // simde_mm_pause() is x86 PAUSE here and is already in the generated pch.\n'
        b'  if (ctx.config().db16cycPause)\n'
        b'    ctx.println("\\tsimde_mm_pause();");\n'
        b'  return true;\n'
        b'}\n')],
}

# --- codegen-config toml edits (CRLF files). Root keys must come before [functions]. ---
TOML_EDITS = {
    # B arm: batch-nolr config == snapB rexlego/legodimensions_config.toml (E60EAF1C)
    'B': (os.path.join(ROOT, 'build', 'agent9', 'install', 'batch-nolr', 'legodimensions_config.toml'),
          [os.path.join(ROOT, 'build', 'agent2', 'snapB', 'DimensionsRecomp', 'rexlego', 'legodimensions_config.toml')],
          'E60EAF1CEB575572BA0274AA5F52E97F25A35C01690B41E6A637739408E6A090',
          b'musttail_calls = true\r\n', b'musttail_calls = true\r\ndb16cyc_pause = true\r\n'),
    # A arm: live == snap1 (S3d/S4a) rexlego/legodimensions_config.toml (7F775847); no root keys yet
    'A': (os.path.join(ROOT, 'DimensionsRecomp', 'rexlego', 'legodimensions_config.toml'),
          [os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego', 'legodimensions_config.toml')],
          None,
          b'\r\n[functions]\r\n', b'\r\ndb16cyc_pause = true\r\n[functions]\r\n'),
}


def udiff(rel, a, b):
    al = a.decode('utf-8').splitlines(keepends=True)
    bl = b.decode('utf-8').splitlines(keepends=True)
    out = ['diff --git a/%s b/%s\n' % (rel, rel)]
    out += list(difflib.unified_diff(al, bl, 'a/' + rel, 'b/' + rel, n=3))
    return ''.join(out).encode('utf-8')


def patch_check(diff_path, base_dir, verify_dir, rels, new_dir):
    if os.path.isdir(verify_dir):
        shutil.rmtree(verify_dir)
    shutil.copytree(base_dir, verify_dir)
    r = subprocess.run([PATCH, '--binary', '-p1', '-d', verify_dir, '-i', diff_path],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    for rel in rels:
        same = sha(os.path.join(verify_dir, rel)) == sha(os.path.join(new_dir, rel))
        ok = ok and same
    shutil.rmtree(verify_dir)
    return ok, r.returncode, (r.stdout + r.stderr).strip().replace('\n', ' | ')


lines = ['# HASHES.txt (Agent 9, run-2 task #17): #26 codegen db16cyc -> simde_mm_pause(), option db16cyc_pause (default OFF)',
         '# SHA-256. SDK paths are relative to the SDK root; toml paths to DimensionsRecomp/. Made by stage.py.',
         '']
head = subprocess.run(['git', '-C', LIVE, 'log', '-1', '--format=%H %cd'], capture_output=True, text=True).stdout.strip()
lines.append('live SDK  DimensionsRecomp/rexglue-sdk HEAD %s' % head)
lines.append('snap1 SDK build/agent2/snap1/DimensionsRecomp/rexglue-sdk (S4a snap; codegen untouched)')
lines.append('')
lines.append('## SDK files: base (live == snap1), new')
diff_all = b''
for rel, eds in SDK_EDITS.items():
    lp, sp = os.path.join(LIVE, rel), os.path.join(SNAP, rel)
    hl, hs = sha(lp), sha(sp)
    if hl != hs:
        sys.exit('%s: live %s != snap1 %s' % (rel, hl, hs))
    data = rd(lp)
    if b'\r' in data:
        sys.exit('%s: has CR' % rel)
    wr(os.path.join(HERE, 'base', rel), data)
    new = data
    for anchor, repl in eds:
        new = edit(new, anchor, repl, rel)
    wr(os.path.join(HERE, 'new', rel), new)
    diff_all += udiff(rel, data, new)
    lines.append('base %s  %s  %d B  (live = snap1)' % (hl, rel, len(data)))
    lines.append('new  %s  %s  %d B  (+%d lines)' % (sha(os.path.join(HERE, 'new', rel)), rel, len(new),
                                                     new.count(b'\n') - data.count(b'\n')))
dpath = os.path.join(HERE, 'db16cyc-pause.diff')
wr(dpath, diff_all)
ok, rc, msg = patch_check(dpath, os.path.join(HERE, 'base'), os.path.join(HERE, 'verify'), list(SDK_EDITS), os.path.join(HERE, 'new'))
lines.append('diff %s  db16cyc-pause.diff  %d B  (apply from the SDK root: git apply -p1, or patch -p1)' % (sha(dpath), len(diff_all)))
lines.append('     patch --binary -p1 onto base/: exit %d, result == new/: %s  [%s]' % (rc, 'yes' if ok else 'NO', msg))
lines.append('')
lines.append('## codegen config toml (one line each; root key, before [functions])')
for arm, (src, others, want, anchor, repl) in TOML_EDITS.items():
    h = sha(src)
    if want and h != want:
        sys.exit('toml %s: %s != %s' % (arm, h, want))
    for o in others:
        if sha(o) != h:
            sys.exit('toml %s: %s differs from %s' % (arm, o, src))
    data = rd(src)
    new = edit(data, anchor, repl, 'toml ' + arm)
    rel = 'rexlego/legodimensions_config.toml'
    wr(os.path.join(HERE, 'toml', 'base-' + arm, rel), data)
    wr(os.path.join(HERE, 'toml', 'new-' + arm, rel), new)
    tpath = os.path.join(HERE, 'toml-db16cyc-pause-%s.diff' % arm)
    wr(tpath, udiff(rel, data, new))
    ok, rc, msg = patch_check(tpath, os.path.join(HERE, 'toml', 'base-' + arm), os.path.join(HERE, 'verify'), [rel],
                              os.path.join(HERE, 'toml', 'new-' + arm))
    line_no = data[:data.index(anchor)].count(b'\n') + 1
    lines.append('%s base %s  %s  %d B  (= %s)' % (arm, h, os.path.relpath(src, ROOT).replace('\\', '/'), len(data),
                                                  ', '.join(os.path.relpath(o, ROOT).replace('\\', '/') for o in others)))
    lines.append('%s new  %s  +1 line after line %d: db16cyc_pause = true (CRLF)' % (arm, sha(os.path.join(HERE, 'toml', 'new-' + arm, rel)), line_no))
    lines.append('%s diff %s  toml-db16cyc-pause-%s.diff  (apply from DimensionsRecomp/: patch --binary -p1)' % (arm, sha(tpath), arm))
    lines.append('       patch onto base: exit %d, result == new: %s  [%s]' % (rc, 'yes' if ok else 'NO', msg))
hh = sha(os.path.join(ROOT, 'harness', 'legodimensions.toml'))
lines.append('')
lines.append('## not changed')
lines.append('harness/legodimensions.toml %s: the runtime config the EXE reads (rex_app.cpp SetupEnvironment);' % hh)
lines.append('  codegen never reads it, so no diff is staged against it.')
for rel in ('src/codegen/codegen_writer.cpp', 'src/codegen/project_recompiler.cpp', 'src/codegen/output_stamp.cpp',
            'src/codegen/output_partition.cpp'):
    lines.append('%s  %s  (read, unchanged)' % (sha(os.path.join(LIVE, rel)), rel))
wr(os.path.join(HERE, 'HASHES.txt'), ('\n'.join(lines) + '\n').encode('ascii'))
print('\n'.join(lines))
