#!/usr/bin/env python3
"""s4b-compose-check.py (Agent 2; task #15 item 4, C1 variable 14:35; task #28 at ~17:00: #26 tool step + S4c as the
last step, live = S4a): read-only composition check of the staged S4b + S4c diffs.

C1 variable (Agent 1 sets it at build time; the S4b prep/build driver takes the same one):
  --c1 v2|v3|both   default: env S4B_C1 if set, else v2. Task #28: v3 (Agent 10, b2r row 36, S35: SAFE).
  v2 = build/agent12/s4-c1v2/keep-watch-v2.diff (418D3D39...)
  v3 = build/agent12/s4-c1v3/keep-watch-v3.diff (DECCFE33...)
  Both touch the same 5 SDK files with the same befores; only the after of src/system/xmemory.cpp differs
  (v2 DC23757A..., v3 BCA5E1CF...). The rexlego step (s4-c1/keep-watch-rexlego.diff 4D0C1079...,
  memory_watch.cpp -> 70829846..., CRLF kept) is the same for both.
S4c variable: --s4c 24-30|24-only|both   default 24-30 (Agent 9 R2.22: s4c-24-30.diff DC02104E... = #24 + #30's
  CMake option, both OFF; fallback s4c-24-only.diff A279DC71...; Agent 10 b2r row 38, S37: both SAFE OFF).

SDK part: copies the S4a-level files from the snap1 SDK into build/agent2/s4b-check/<order>/ (scratch, SDK-relative
paths) and git-applies the staged diffs there, outside any work tree (GIT_CEILING_DIRECTORIES=R,
-c core.autocrlf=false), in two orders per selected C1 variant X:
  o1-X: C1 X -> M1 -> P2c -> r1r2 -> #26      o2-X: C1 X -> M1 -> r1r2 -> P2c -> #26
(#26 = build/agent9/s4/spin/db16cyc-pause/db16cyc-pause.diff AC554DBB..., the codegen tool with the option
db16cyc_pause, default OFF; 3 SDK files no other step touches.)
Each step's input/output hashes are checked against the staging records; a file that an earlier step already
changed is "chained" (its before is the previous step's after). Then o1-X and o2-X must end byte-identical,
xmemory.cpp must end at that variant's C1 after, and with --c1 both the v2 and v3 finals may differ only in
src/system/xmemory.cpp.
Game part: [5] memory_watch.cpp (C1, CRLF) and the staged after-file; [6] S4c, the last step: rexlego/CMakeLists.txt
(CRLF, 3690D5D7...) + the new rexlego/src/gpu_wait_backoff.cpp, git-applied to a scratch copy of the snap1 file
(DimensionsRecomp-relative paths); CMakeLists must end at Agent 9's new/ copy and the TU at 01D9F8F3 (LF; the CRLF form
34D281E0 is also accepted, Agent 10 note 3).
S4a is live and committed (SDK 3bb65bb, game 1bd322e), so live must equal snap1 for every base file.
Writes only build/agent2/s4b-check/** and build/agent2/s4b-compose-<HHMM>-c1<sel>.txt. No builds, no repo writes.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
R = r'<workspace>'
SNAP_SDK = os.path.join(R, r'build\agent2\snap1\DimensionsRecomp\rexglue-sdk')
SNAP_GAME = os.path.join(R, r'build\agent2\snap1\DimensionsRecomp')
LIVE_SDK = os.path.join(R, r'DimensionsRecomp\rexglue-sdk')
LIVE_GAME = os.path.join(R, r'DimensionsRecomp')
OUT = os.path.join(R, r'build\agent2')
SCR = os.path.join(OUT, 's4b-check')

XM = 'src/system/xmemory.cpp'
CP = 'src/graphics/d3d12/command_processor.cpp'

# C1 variants: (diff, diff sha256, xmemory.cpp after). The other 4 C1 files are identical in v2 and v3.
C1_VARIANTS = {
    'v2': (r'build\agent12\s4-c1v2\keep-watch-v2.diff',
           '418D3D39947DB1461974851ABAEAE933BC6460D85448F52EA743CB1CDE39169D',
           'DC23757AC206FCC51F03B89C0A77F8EFCDB372B138C5D72600C230C295EC8CFD'),
    'v3': (r'build\agent12\s4-c1v3\keep-watch-v3.diff',
           'DECCFE3373C27C3C8442A26A3C4DDFDB01CE54E2C4912CDE6701484185D66F48',
           'BCA5E1CF63686E73FC5A12642B9B169E155FBBEC65D0A56CE1BE9B0B71022794'),
}
C1_COMMON = {
    'include/rex/graphics/shared_memory.h': (
        '4D861738A94B556B08A4604D2CAB07AD7AFE1B3AD56B295F7F1E31C57BAED847',
        '82A66445ED98B091B5CF8FAA75D0EF3E11DFA0344ABBC2184F3A23C46F0FF98C'),
    'include/rex/system/xmemory.h': (
        '80100865A654AF047D25EDA70CF1C746B182C81BCBDFC5B027EE56E0AE7132F9',
        '5A70782EF00F0FB6094A0F538690557E81B5EE21C7781E190A38ABD859541CB2'),
    'src/graphics/primitive_processor.cpp': (
        'E07F690223B564AE0D41D1192ACD9225BD35226A43A7ACA8F2798B1851291B35',
        '470BA4BED73B2ABFD32048F901C426BA24048C26A07694F9768F7AD35EC137F2'),
    'src/graphics/shared_memory.cpp': (
        '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4',
        'A4A31038ABDFF94A1B97D28A13EE2ACBB67F44DC596F7A964C8C7493050390C6'),
}
XM_BEFORE = '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A'

STEPS = {}
for _v, (_rel, _dsha, _xm_after) in C1_VARIANTS.items():
    _fmap = dict(C1_COMMON)
    _fmap[XM] = (XM_BEFORE, _xm_after)
    STEPS['c1' + _v] = ('C1 %s (A12)' % _v, _rel, _dsha, _fmap)
STEPS.update({
    'm1': ('M1 (A5)', r'build\agent5\s4-m1\m1-nontemporal-copy.diff',
           'EBECE86E68369C88464F5837ED4882680E712184273FE61F802CD939CEBF30CD', {
               'src/graphics/d3d12/shared_memory.cpp': (
                   'BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587',
                   '2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4'),
           }),
    'p2c': ('P2 counter (A12)', r'build\agent12\s4-p2c\memexport-full-buffer-counter.diff',
            '29E02E249EDDFEFD702CFBF6D7A36B6A3D060E9DFC9A8FD6F621BB0FE151BDE2', {
                'src/graphics/d3d12/command_processor.cpp': (
                    '3AB3AA5360D4E9875DCA8550346EE368EC9188BDC454C2EB93D9BB915BD1AD97',
                    '474C1CBAE6359D9EB9FD313FF541EEA2CF6A6987A5BCAE1821EFDF75A6B86EFF'),
            }),
    'r1r2': ('#18/#20 r1r2 (A7)', r'build\agent7\s4-r1r2\s4-r1r2.diff',
             'BD0C4A93446149BB111FA7659F70684579F3AA604A3DE0CEF0372FD71AF5B483', {
                 'src/graphics/d3d12/command_processor.cpp': (
                     '3AB3AA5360D4E9875DCA8550346EE368EC9188BDC454C2EB93D9BB915BD1AD97',
                     '760833A5D7D89ADCBE1FED1300D56829F05D4462AB7B2D62ADD38D95C9813481'),
                 'include/rex/graphics/d3d12/command_processor.h': (
                     '41F32B80BABA213CBC2821CD48661B51121D256E51054B8A46B83E5CBF8B2FA0',
                     '67F4E8380C879377F06B6E3DD879EE737A82BBBE9682F123247ED5D0671FF325'),
                 'include/rex/graphics/d3d12/deferred_command_list.h': (
                     'DA2F58B6CE3D7F6A72EDBF3D2A577EBE1E6FBC664FB9EA368C9CC65E874FE174',
                     '9F6CC70A6922232D4FF7A32303E8B785A01D1C7A3CF54373369EF6B23F8AF0F0'),
                 'src/graphics/d3d12/deferred_command_list.cpp': (
                     'FFDF7FB66EC8171557D1E4195147DE556BDDA342ACC7C3ED7EB81279494A3E30',
                     '30FF57446EFB5D7643EC71024CE1D04884C210831053DEE39EAAB611FD346872'),
             }),
    'n26': ('#26 db16cyc_pause (A9)', r'build\agent9\s4\spin\db16cyc-pause\db16cyc-pause.diff',
            'AC554DBBD965BF941BADE6391D0E0F483BE075B8A72434EEE8CB9D189ED61452', {
                'include/rex/codegen/config.h': (
                    'D07C575FF2904B8753FA4B4306847375EC2EB69156355947E874AFFFC19F46C2',
                    'CD39B0E110D3E0FD9E602446111183CB941478BF9057389BB815F125060D2087'),
                'src/codegen/config.cpp': (
                    '0ED529B7E5F0F4E7CC0A4551A1C5C3A3191F03D28D491D517850898D5062FCFD',
                    '4706A7F22C3859D6DBE8E7A3150B3403548856BAD626952818F7B96B3D5935DF'),
                'src/codegen/builders/system.cpp': (
                    'D1269273636B5A1A57BE6E467CE19326EAEA38F7E0E5A0C157D4B23998D10506',
                    'FAD4372074D32D69D5B2CB0B100F283E239A426C3E015DBD66C22BCB693998D2'),
            }),
})
AGENT10_CP_COMPOSITE = '027204B53A271D69'  # b2r S30/S31: P2c + r1r2, both orders (273,790 B)
MW_REL = 'rexlego/src/gpu_native/memory_watch.cpp'
MW_LIVE = '19AE1606C6DB727369A5F119EF3371A8D307F4B42088D5C064F0D2DF8D62D47A'
MW_AFTER = '70829846'  # Agent 10 (prefix)
MW_DIFF = r'build\agent12\s4-c1\keep-watch-rexlego.diff'
MW_DIFF_SHA = '4D0C10794188CF450046D42B249C9C46D009EE9F4F1B82116954857FA70838BD'
# S4c (Agent 9 R2.22, HASHES.txt 0489BC9F...): diff, diff sha256, CMakeLists after, Agent 9's new/ folder
S4C_DIR = r'build\agent9\s4\fence-wait\s4c'
S4C = {
    '24-30': (S4C_DIR + r'\s4c-24-30.diff', 'DC02104EA76E0BF6AE6CF28968079B8F18208480B884B536D22F700316EDD019',
              '1BF46D7878BA9A2535BD044A22EB50FC559067C72F0BAEFF6FDD742DFE5EF25E', S4C_DIR + r'\new'),
    '24-only': (S4C_DIR + r'\s4c-24-only.diff', 'A279DC71D6CD4FAA7FE6D5C8B7F968DC657E1E890703EF104AF713B092A36026',
                '9A4606A7031375F7F8286926C23AE48C2AAF681C77BF28D0483497451B5801A3', S4C_DIR + r'\new-24only'),
}
CML = 'rexlego/CMakeLists.txt'
CML_BEFORE = '3690D5D76AA9FBED39D3559163C9F87D380124D9657FE450896AAD1F21607429'
TU = 'rexlego/src/gpu_wait_backoff.cpp'
TU_LF = '01D9F8F3464C861401C3BE98F797938619C5DD85B1AEA166B6D9CED053FA19DD'
TU_CRLF = '34D281E006FB5FBEAFF3D4935ED9BFA3BE2F737FEE34C484BE225EAFAC44CF20'

lines = []
fails = []


def out(s=''):
    lines.append(s)
    print(s)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def sha_or(p):
    return sha(p) if os.path.isfile(p) else 'ABSENT'


def git_apply(cwd, diff, check=False):
    env = dict(os.environ)
    for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
        env.pop(k, None)
    env['GIT_CEILING_DIRECTORIES'] = R
    cmd = ['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', 'apply', '--verbose']
    if check:
        cmd.append('--check')
    cmd.append(diff)
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    msg = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, msg


def diff_pairs(path):
    # (old, new) path pairs of a unified diff: a '--- ' line directly followed by a '+++ ' line
    with open(path, 'rb') as f:
        ls = [x.rstrip(b'\r') for x in f.read().split(b'\n')]
    res = []
    for i in range(len(ls) - 1):
        if ls[i].startswith(b'--- ') and ls[i + 1].startswith(b'+++ '):
            res.append((ls[i][4:].split(b'\t')[0].decode(), ls[i + 1][4:].split(b'\t')[0].decode()))
    return res


def orders_for(variants):
    o = {}
    for v in variants:
        o['o1-' + v] = ['c1' + v, 'm1', 'p2c', 'r1r2', 'n26']
        o['o2-' + v] = ['c1' + v, 'm1', 'r1r2', 'p2c', 'n26']
    return o


def s4c_part(sels):
    out('[6] S4c, the last step (game repo; Agent 9 R2.22; rated SAFE OFF, b2r row 38): %s + new %s' % (CML, TU))
    sn = sha_or(os.path.join(SNAP_GAME, CML.replace('/', os.sep)))
    lv = sha_or(os.path.join(LIVE_GAME, CML.replace('/', os.sep)))
    out('  base %s: snap1 %s %s; live %s %s' % (CML, sn[:16], 'ok (= 3690D5D7)' if sn == CML_BEFORE else 'FAIL',
                                               lv[:16], 'ok (= snap1)' if lv == sn else 'DIFFERS'))
    if sn != CML_BEFORE:
        fails.append('s4c base snap1')
    if lv != sn:
        fails.append('s4c base live')
    for side, root in (('snap1', SNAP_GAME), ('live', LIVE_GAME)):
        p = os.path.join(root, TU.replace('/', os.sep))
        ex = os.path.exists(p)
        out('  %s %s: %s' % (side, TU, 'present (%s) FAIL: S4c adds it' % sha(p)[:16] if ex else 'absent (ok: S4c adds it)'))
        if ex:
            fails.append('s4c new file exists in ' + side)
    for key in ('24-30', '24-only'):
        rel, dsha, cml_after, newdir = S4C[key]
        selected = key in sels
        dp = os.path.join(R, rel)
        got = sha_or(dp)
        ok = got == dsha
        tag = '' if selected else ' (not selected; informational)'
        out('  [%s]%s diff %s: %s %s' % (key, tag, rel.replace('\\', '/'), got[:16], 'ok' if ok else 'FAIL (record %s)' % dsha[:16]))
        if selected and not ok:
            fails.append('s4c diff ' + key)
        if got == 'ABSENT':
            continue
        pairs = diff_pairs(dp)
        want = [('a/' + CML, 'b/' + CML), ('/dev/null', 'b/' + TU)]
        pok = sorted(pairs) == sorted(want)
        out('    patches %s: %s' % (pairs, 'ok' if pok else 'FAIL (want %s)' % want))
        if selected and not pok:
            fails.append('s4c pairs ' + key)
        d = os.path.join(SCR, 's4c-' + key)
        if os.path.isdir(d):
            shutil.rmtree(d)
        dst = os.path.join(d, CML.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(SNAP_GAME, CML.replace('/', os.sep)), dst)
        rc, msg = git_apply(d, dp)
        offs = [m for m in msg if 'offset' in m.lower() or 'fuzz' in m.lower()]
        out('    git -c core.autocrlf=false apply on a scratch copy of the snap1 file: exit %d%s' % (
            rc, (': ' + ' | '.join(msg[-4:])) if rc else ('; ' + '; '.join(offs) if offs else ', no offsets')))
        if rc:
            if selected:
                fails.append('s4c apply ' + key)
            continue
        hc = sha(dst)
        hn = sha_or(os.path.join(R, newdir, 'rexlego', 'CMakeLists.txt'))
        cok = hc == cml_after and hn == hc
        with open(dst, 'rb') as f:
            data = f.read()
        out('    %s after %s (%d B, %d CRLF, %d bare LF) %s; Agent 9 new/ copy %s' % (
            CML, hc[:16], len(data), data.count(b'\r\n'), data.count(b'\n') - data.count(b'\r\n'),
            '== record' if hc == cml_after else 'FAIL (record %s)' % cml_after[:16], hn[:16]))
        if selected and not cok:
            fails.append('s4c cmakelists after ' + key)
        text = data.decode('utf-8', 'replace')
        if key == '24-30':
            hit = [x.strip() for x in text.splitlines() if 'option(LEGODIMENSIONS_SCENE_WALK_PROBE' in x]
            ok30 = len(hit) == 1 and hit[0].rstrip(')').rstrip().endswith('OFF')
            out('    #30 option: %s %s' % (' | '.join(hit) or 'none', 'ok (default OFF)' if ok30 else 'FAIL'))
            if selected and not ok30:
                fails.append('s4c #30 option')
        blk = [x.strip() for x in text.splitlines() if 'gpu_wait_backoff.cpp' in x or 'LEGO_GPU_WAIT_HOOK_GETDATA' in x
               or x.strip().startswith('if(NOT LEGODIMENSIONS_NATIVE_GPU)')]
        ok24 = any('if(NOT LEGODIMENSIONS_NATIVE_GPU)' in x for x in blk) and any('LEGO_GPU_WAIT_HOOK_GETDATA=1' in x for x in blk)
        out('    #24 block: %s %s' % (' | '.join(blk)[:300], 'ok (OFF builds only, GETDATA hooks on)' if ok24 else 'FAIL'))
        if selected and not ok24:
            fails.append('s4c #24 block')
        tp = os.path.join(d, TU.replace('/', os.sep))
        ht = sha_or(tp)
        hn2 = sha_or(os.path.join(R, newdir, 'rexlego', 'src', 'gpu_wait_backoff.cpp')) if key == '24-30' else '(no TU copy in new-24only)'
        tok = ht in (TU_LF, TU_CRLF)
        out('    %s %s %s; Agent 9 new/ TU %s' % (TU, ht[:16], 'ok (= 01D9F8F3, LF)' if ht == TU_LF else (
            'ok (= 34D281E0, CRLF form)' if ht == TU_CRLF else 'FAIL (want 01D9F8F3 LF or 34D281E0 CRLF)'), hn2[:16]))
        if selected and not tok:
            fails.append('s4c TU ' + key)
        if ht != 'ABSENT':
            with open(tp, 'rb') as f:
                tt = f.read().decode('utf-8', 'replace')
            for needle in ('REX_HOOK_RAW', 'sub_83FBF7D0', 'sub_83FAF180', 'sub_83FB09E8', 'sub_83FC0C10',
                           'LEGO_GPU_WAIT_BACKOFF_US', 'LEGO_GPU_WAIT_SPIN_US', 'LEGO_GPU_WAIT_STATS'):
                out('      TU mentions %-26s %d time(s)' % (needle, tt.count(needle)))
    out()


def main():
    ap = argparse.ArgumentParser(description='Read-only S4b + S4c composition check (C1 variable: --c1 or env S4B_C1).')
    ap.add_argument('--c1', choices=['v2', 'v3', 'both'], default=None,
                    help='C1 variant(s) to compose; default: env S4B_C1, else v2')
    ap.add_argument('--s4c', choices=['24-30', '24-only', 'both'], default='24-30',
                    help='S4c diff(s) that must pass; default 24-30 (the other one is reported too)')
    args = ap.parse_args()
    envc1 = os.environ.get('S4B_C1', '').strip().lower()
    if args.c1:
        sel, src = args.c1, '--c1'
    elif envc1:
        if envc1 not in ('v2', 'v3', 'both'):
            print('S4B_C1=%r is not v2|v3|both; nothing done' % envc1)
            return 2
        sel, src = envc1, 'env S4B_C1'
    else:
        sel, src = 'v2', 'default: v2 unless Agent 10 rates v3 SAFE first'
    variants = ['v2', 'v3'] if sel == 'both' else [sel]
    s4c_sel = ['24-30', '24-only'] if args.s4c == 'both' else [args.s4c]
    orders = orders_for(variants)
    used = [k for k in STEPS if any(k in seq for seq in orders.values())]

    t0 = time.time()
    out('s4b-compose-check.py report, %s (read-only for every tree; scratch = build/agent2/s4b-check)'
        % time.strftime('%Y-%m-%d %H:%M:%S'))
    out('C1 selection: %s (%s); S4c selection: %s; orders: %s' % (sel, src, ', '.join(s4c_sel), ', '.join(orders)))
    out()
    out('[1] staged SDK diffs: sha256 vs the staging records')
    for k, (name, rel, dsha, _) in STEPS.items():
        p = os.path.join(R, rel)
        got = sha_or(p)
        ok = got == dsha
        if k in used:
            if not ok:
                fails.append('diff ' + k)
            verdict = 'ok' if ok else 'FAIL (record %s)' % dsha[:16]
        else:
            verdict = '(not selected; %s)' % ('matches record' if ok else 'record %s' % dsha[:16])
        out('  %-24s %-58s %s %s' % (name, rel.replace('\\', '/'), got[:16], verdict))
    out()
    files = []
    for k in used:
        for f in STEPS[k][3]:
            if f not in files:
                files.append(f)
    first_before = {}
    for o, seq in orders.items():
        fb = {}
        for k in seq:
            for f, (b, a) in STEPS[k][3].items():
                fb.setdefault(f, b)
        for f, b in fb.items():
            if first_before.setdefault(f, b) != b:
                fails.append('first-before conflict %s (%s)' % (f, o))
    out('[2] S4b SDK bases: snap1 (S4a level) must equal each file\'s first staged "before" (same for every C1 variant);'
        ' live too (S4a is live and committed: SDK 3bb65bb)')
    for f in files:
        s = sha(os.path.join(SNAP_SDK, f.replace('/', os.sep)))
        lv = sha(os.path.join(LIVE_SDK, f.replace('/', os.sep)))
        ok = s == first_before[f]
        if not ok:
            fails.append('base ' + f)
        if lv != s:
            fails.append('live ' + f)
        out('  %-52s snap1 %s %s; %s' % (f, s[:16], 'ok' if ok else 'FAIL (want %s)' % first_before[f][:16],
                                        'live == snap1' if lv == s else 'live %s DIFFERS' % lv[:16]))
    out()
    finals = {}
    for idx, (o, seq) in enumerate(orders.items()):
        d = os.path.join(SCR, o)
        if os.path.isdir(d):
            shutil.rmtree(d)
        for f in files:
            dst = os.path.join(d, f.replace('/', os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(SNAP_SDK, f.replace('/', os.sep)), dst)
        out('[3%s] order %s: %s' % (chr(ord('a') + idx), o, ' -> '.join(seq)))
        touched = set()
        for k in seq:
            name, rel, _, fmap = STEPS[k]
            for f, (b, a) in fmap.items():
                h = sha(os.path.join(d, f.replace('/', os.sep)))
                if f in touched:
                    out('    %-24s %-48s before %s (chained: an earlier step changed it; record %s)' % (name, f, h[:16], b[:16]))
                elif h != b:
                    fails.append('%s %s before' % (o, k))
                    out('    %-24s %-48s before %s FAIL (record %s)' % (name, f, h[:16], b[:16]))
            rc, msg = git_apply(d, os.path.join(R, rel))
            if rc != 0:
                fails.append('%s %s apply rc=%d' % (o, k, rc))
                out('    %-24s git apply exit %d: %s' % (name, rc, ' | '.join(msg[-6:])))
                continue
            offs = [m for m in msg if 'offset' in m.lower() or 'fuzz' in m.lower()]
            out('    %-24s git apply exit 0%s' % (name, ('; ' + '; '.join(offs)) if offs else ', no offsets'))
            for f, (b, a) in fmap.items():
                h = sha(os.path.join(d, f.replace('/', os.sep)))
                if f in touched:
                    out('    %-24s %-48s after  %s (chained; record for the lone apply %s)' % ('', f, h[:16], a[:16]))
                else:
                    ok = h == a
                    if not ok:
                        fails.append('%s %s after %s' % (o, k, f))
                    out('    %-24s %-48s after  %s %s' % ('', f, h[:16], '== record' if ok else 'FAIL (record %s)' % a[:16]))
                touched.add(f)
        finals[o] = {f: (sha(os.path.join(d, f.replace('/', os.sep))), os.path.getsize(os.path.join(d, f.replace('/', os.sep)))) for f in files}
        out()
    out('[4] final files per C1 variant, o1 vs o2 (the S4b SDK file set on top of S4a)')
    for v in variants:
        o1, o2 = 'o1-' + v, 'o2-' + v
        out('  C1 %s:' % v)
        same = True
        for f in files:
            h1, n1 = finals[o1][f]
            h2, n2 = finals[o2][f]
            eq = h1 == h2
            same = same and eq
            extra = ''
            if f == CP:
                cm = h1.startswith(AGENT10_CP_COMPOSITE)
                extra = '; Agent 10 composite %s...: %s' % (AGENT10_CP_COMPOSITE[:8], 'match' if cm else 'NO MATCH')
                if not cm:
                    fails.append('cp composite ' + v)
            elif f == XM:
                want = C1_VARIANTS[v][2]
                extra = '; = C1 %s after %s...: %s' % (v, want[:8], 'yes' if h1 == want else 'NO')
                if h1 != want:
                    fails.append('xmemory final ' + v)
            out('    %-52s %s %7d B %s%s' % (f, h1, n1, 'o1 == o2' if eq else 'o1 != o2 (o2 %s)' % h2[:16], extra))
        if not same:
            fails.append('o1 != o2 (%s)' % v)
    if len(variants) == 2:
        out()
        out('  v2 vs v3 finals (o1 of each): only src/system/xmemory.cpp may differ')
        dif = []
        for f in files:
            h2_, n2_ = finals['o1-v2'][f]
            h3_, n3_ = finals['o1-v3'][f]
            if h2_ != h3_:
                dif.append(f)
                out('    %-52s v2 %s %7d B | v3 %s %7d B  DIFFERS' % (f, h2_[:16], n2_, h3_[:16], n3_))
        out('    => %d of %d files identical; differing: %s %s' % (len(files) - len(dif), len(files), ', '.join(dif) or 'none',
                                                              'ok' if dif == [XM] else 'FAIL (want only %s)' % XM))
        if dif != [XM]:
            fails.append('v2/v3 finals differ beyond xmemory.cpp')
    out()
    out('[5] game repo file of C1 (keep-watch-rexlego.diff, v1, reused by C1 v2 and v3): %s' % MW_REL)
    lv = sha(os.path.join(LIVE_GAME, MW_REL.replace('/', os.sep)))
    sn = sha(os.path.join(SNAP_GAME, MW_REL.replace('/', os.sep)))
    out('  live  %s %s' % (lv[:16], 'ok (= 19AE1606)' if lv == MW_LIVE else 'DIFFERS from 19AE1606'))
    out('  snap1 %s %s' % (sn[:16], 'ok (= 19AE1606)' if sn == MW_LIVE else 'FAIL: DIFFERS from 19AE1606'))
    if sn != MW_LIVE:
        fails.append('memory_watch snap1 base')
    with open(os.path.join(SNAP_GAME, MW_REL.replace('/', os.sep)), 'rb') as f:
        data = f.read()
    out('  line ends (snap1): %d CRLF, %d bare LF' % (data.count(b'\r\n'), data.count(b'\n') - data.count(b'\r\n')))
    dp = os.path.join(R, MW_DIFF)
    dsha = sha_or(dp)
    out('  diff  %s %s' % (dsha[:16], 'ok (= record 4D0C1079)' if dsha == MW_DIFF_SHA else 'FAIL'))
    if dsha != MW_DIFF_SHA:
        fails.append('memory_watch diff')
    cands = []
    base = os.path.join(R, r'build\agent12\s4-c1')
    for root, _, fs in os.walk(base):
        for fn in fs:
            if fn == 'memory_watch.cpp':
                cands.append(os.path.join(root, fn))
    n_after = 0
    for c in sorted(cands):
        h = sha(c)
        tag = 'after (70829846...)' if h.startswith(MW_AFTER) else ('= live base' if h == MW_LIVE else 'other')
        n_after += h.startswith(MW_AFTER)
        out('  staged %-60s %s %s' % (os.path.relpath(c, R).replace('\\', '/'), h[:16], tag))
    if not n_after:
        fails.append('memory_watch staged after-file missing')
    d = os.path.join(SCR, 'mw')
    if os.path.isdir(d):
        shutil.rmtree(d)
    dst = os.path.join(d, MW_REL.replace('/', os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(SNAP_GAME, MW_REL.replace('/', os.sep)), dst)
    rc, msg = git_apply(d, dp, check=True)
    out('  git -c core.autocrlf=false apply --check on a scratch copy of the CRLF file: exit %d%s' % (rc, (': ' + ' | '.join(msg[-3:])) if rc else ''))
    out('  => landing rule (Agent 10): after the C1 apply memory_watch.cpp must hash 70829846...; if a plain apply gives anything else, copy the staged after-file (mtime = now)')
    out()
    s4c_part(s4c_sel)
    out('SUMMARY: C1=%s; S4c=%s; %s; %.1f s' % (sel, ','.join(s4c_sel), '0 FAIL' if not fails else '%d FAIL: %s' % (len(fails), ', '.join(fails)), time.time() - t0))
    rep = os.path.join(OUT, 's4b-compose-%s-c1%s.txt' % (time.strftime('%H%M'), sel))
    with open(rep, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('report:', rep)
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
