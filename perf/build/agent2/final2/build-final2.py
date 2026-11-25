#!/usr/bin/env python3
# build-final2.py (M2, 2026-11-25): the final2 build driver, a copy of final/build-final.py (5BE1F221, rated CONFORM
# 94CC9FA7) for ONE bin pair from the COMMITTED source (rexglue-sdk a7e79c0 = FINAL + #33 nohunk5; DimensionsRecomp
# 2de88ce). recompile.py (855BCC79) and relink.py (F3C6EEAF) are used UNCHANGED.
#
#   python build/agent2/final2/build-final2.py --leg rt|gpu|xe|nat [--dry-run] [--jobs 8]
#   python build/agent2/final2/build-final2.py --stage devfinal2|nativefinal2 [--dry-run]
#
# Differences from build-final.py: final2/b paths; no xeoff/natoff legs or OFF stages; gpu leg = the 10 rexgpu-xenos
# TUs of prep-final2 (overlay sources, --include-first b/DimensionsRecomp/rexglue-sdk/include for the #33
# pipeline_cache.h, gate: that -I is ahead of snap1's rexglue-sdk/include in every command), extra gpu needles
# (the #33 cvar name and slow-frame fields); nativefinal2 stages the NEW rexruntime.dll + rexgpu-xenos.dll too (not
# N-A); pe-check.py / mapcheck-s4c.py / verify-bins.py / stage-variant.py used by path, unchanged.
#
# Needs prep-final2.py (b/prep.txt RESULT: PASS) and, for the ON legs, fsyntax2.py (b/fsyntax/fsyntax.txt PASS).
# Per leg (writes only build/agent2/final2/b/<leg>/):
#   CTL  (rt, gpu, xe, nat): recompile the leg's UNPATCHED snap1 TUs (list-ctl.tsv) with the build's own flags and relink
#        the target from its own ninja edge with only those objects swapped; relink.py --compare must say PASS (equal to
#        the reference except TimeDateStamp fields) and, for exes, --compare-map PASS. Anything else = STOP (D1).
#   ON   recompile the overlay sources (list-on.tsv) with --fwd-src, -fmacro-prefix-map overlay=snap1 (so __FILE__
#        strings equal the CTL's), nat: --include-first b/nat/gen-on (fingerprint 1616ce65e973c583 header),
#        gpu: --include-first b/DimensionsRecomp/rexglue-sdk/include; relink.
#   GATES: needles (want in ON and absent in the reference; absent in ON); no overlay path bytes in the outputs;
#        no pch/error text in any compile log; gpu/nat: the include-first -I is ahead of the snap1 one in every command;
#        pe-check.py (D5) vs the reference; xe: mapcheck-s4c (31 hooked aliases); shared DLL E3CB99CF before/after.
# Targets / ccdbs (from snap1-sdk CMakeFiles/impl-Release.ninja and the game trees' build.ninja):
#   rt  : snap1-sdk ccdb (/Release/), edge .../rexglue-sdk/out/win-amd64/Release/rexruntime.dll (8 TUs incl. the 2
#         rexcore.dir objects), ref devoff4b-bin/rexruntime.dll A33801D1
#   gpu : same ccdb, edge .../Release/rexgpu-xenos.dll, ref devoff4b-bin/rexgpu-xenos.dll E3CB99CF
#   xe  : snap1-off ccdb, edge legodimensions.exe, ref devoff4b-bin exe DFBE1D43 + map
#   nat : snap1-on ccdb, edge legodimensions.exe, ref native4b-bin exe + map
# Stage (atomic, stage-variant.py; then verify-bins.py on the new bin + devoff4b, devoff4b-cg26, native4b = 0 FAIL):
#   devfinal2    = devoff4b-bin + rexruntime.dll (rt) + rexgpu-xenos.dll (gpu) + legodimensions.exe/.map (xe)
#   nativefinal2 = native4b-bin + rexruntime.dll (rt) + rexgpu-xenos.dll (gpu) + legodimensions.exe/.map (nat)
import argparse, glob, hashlib, os, re, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
FIN = os.path.join(A2, 'final2')
B = os.path.join(FIN, 'b')
OV = os.path.join(B, 'DimensionsRecomp')
SNAP = os.path.join(A2, 'snap1', 'DimensionsRecomp')
SDKB = os.path.join(A2, 'snap1-sdk')
OFF, ON = os.path.join(A2, 'snap1-off'), os.path.join(A2, 'snap1-on')
DEV, NAT = os.path.join(A2, 'devoff4b-bin'), os.path.join(A2, 'native4b-bin')
SDK_OUT = os.path.join(SNAP, 'rexglue-sdk', 'out', 'win-amd64', 'Release')
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
SHARED = os.path.join(SDKB, 'install', 'bin', 'rexgpu-xenos.dll')
SHARED_SHA = 'E3CB99CFDEA95E66EF093BF1B2A500076757FB727E60B046D70EBA01E05C9939'
SHARED_BINS = ['devoff4b-bin', 'devoff4b-cg26-bin', 'native4b-bin']
FP_OLD, FP_NEW = '9b40acbbef4c57b3', '1616ce65e973c583'
MARK = 'GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US='
MC = 'Native GPU: shader miss cache {} ({}{})'
PY = sys.executable
PECHECK = os.path.join(A2, 'final', 'pe-check.py')
TOOLS = [os.path.abspath(__file__), os.path.join(A2, 'recompile.py'), os.path.join(A2, 'relink.py'),
         os.path.join(A2, 'stage-variant.py'), os.path.join(A2, 'session3', 'verify-bins.py'),
         os.path.join(FIN, 'prep-final2.py'), os.path.join(FIN, 'fsyntax2.py'), PECHECK,
         os.path.join(A2, 's4b', 'mapcheck-s4c.py')]
GPU_INC = os.path.join(OV, 'rexglue-sdk', 'include')
NO_WAIT = 'd3d12_pipeline_creation_no_wait'
SLOW33 = 'dropped draws {} | forced pipeline waits {:.1f} ({}x)'


def pmap(sub):
    return '--flag=-fmacro-prefix-map=%s=%s' % (os.path.join(OV, sub).replace('\\', '/'),
                                                os.path.join(SNAP, sub).replace('\\', '/'))


SDK_COMP = ['--ccdb', os.path.join(SDKB, 'compile_commands.json'), '--obj-filter', '/Release/']
LEGS = {
    'rt': dict(comp=SDK_COMP, pm='rexglue-sdk', ninja=os.path.join(SDKB, 'build-Release.ninja'),
               target=os.path.join(SDK_OUT, 'rexruntime.dll'), out='rexruntime.dll',
               ref=os.path.join(DEV, 'rexruntime.dll'), want=['Final defaults:{}'], absent=[],
               pe=[]),
    'gpu': dict(comp=SDK_COMP, pm='rexglue-sdk', ninja=os.path.join(SDKB, 'build-Release.ninja'),
                target=os.path.join(SDK_OUT, 'rexgpu-xenos.dll'), out='rexgpu-xenos.dll',
                ref=os.path.join(DEV, 'rexgpu-xenos.dll'), want=['Final defaults (GPU): {} {}', NO_WAIT, SLOW33],
                absent=[], inc=GPU_INC, inc_before='snap1/dimensionsrecomp/rexglue-sdk/include',
                pe=['--allow-add', 'rexruntime.dll!GetFlagByName', '--allow-add', 'rexruntime.dll!GetFlagSource',
                    '--ref-count', 'rexruntime.dll=115', '--added-exported-by',
                    'rexruntime.dll=' + os.path.join(DEV, 'rexruntime.dll')]),
    'xe': dict(comp=['--ccdb', os.path.join(OFF, 'compile_commands.json')], pm='rexlego',
               ninja=os.path.join(OFF, 'build.ninja'), target='legodimensions.exe', out='legodimensions.exe',
               ref=os.path.join(DEV, 'legodimensions.exe'), refmap=os.path.join(DEV, 'legodimensions.map'),
               want=[MARK], absent=[MC], pe=[]),
    'nat': dict(comp=['--ccdb', os.path.join(ON, 'compile_commands.json')], pm='rexlego',
                ninja=os.path.join(ON, 'build.ninja'), target='legodimensions.exe', out='legodimensions.exe',
                ref=os.path.join(NAT, 'legodimensions.exe'), refmap=os.path.join(NAT, 'legodimensions.map'),
                inc=os.path.join(B, 'nat', 'gen-on'), inc_before='snap1-on/generated', want=[MC, FP_NEW],
                absent=[FP_OLD, MARK], pe=[]),
}
STAGES = {
    'devfinal2': (DEV, [('rexruntime.dll', 'rt'), ('rexgpu-xenos.dll', 'gpu'), ('legodimensions.exe', 'xe'),
                        ('legodimensions.map', 'xe')]),
    'nativefinal2': (NAT, [('rexruntime.dll', 'rt'), ('rexgpu-xenos.dll', 'gpu'), ('legodimensions.exe', 'nat'),
                           ('legodimensions.map', 'nat')]),
}
TITLES = {
    'devfinal2': 'FINAL2 Xenos bin from the committed source (rexglue-sdk a7e79c0 = win3 defaults + #33 '
                 'd3d12_pipeline_creation_no_wait opt-in default OFF; DimensionsRecomp 2de88ce = q500 back-off default)',
    'nativefinal2': 'FINAL2 native bin from the committed source (native4b + shaders.cpp miss cache default ON, '
                    'fingerprint 1616ce65e973c583; NEW rexruntime.dll + rexgpu-xenos.dll from rexglue-sdk a7e79c0)',
}
OUT, NOTES, FAILS = [], [], []  # one build-final2 run per process
OVERLAY_RE = re.compile(rb'agent2[/\\]+final2[/\\]+b[/\\]', re.I)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def result_pass(p):
    return os.path.isfile(p) and re.search(r'^RESULT: PASS', open(p, encoding='utf-8', errors='replace').read(), re.M)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--leg', choices=sorted(LEGS))
    g.add_argument('--stage', choices=sorted(STAGES))
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--dry-run', action='store_true', help='recompile/relink --dry-run; stage --dry-run')
    a = ap.parse_args()
    name = a.leg or a.stage
    top = os.path.join(B, a.leg) if a.leg else os.path.join(B, 'stage-' + a.stage)
    out, notes, fails, times = OUT, NOTES, FAILS, {}
    t_all = time.time()

    def say(s):
        out.append(s)
        print(s, flush=True)

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)
        return ok

    def run(label, cmd, dry=True):
        if a.dry_run and dry:
            cmd = cmd + ['--dry-run']
        t0 = time.time()
        say('$ ' + ' '.join(cmd))
        p = subprocess.run(cmd, cwd=R, capture_output=True, text=True)
        txt = (p.stdout + p.stderr).rstrip()
        for ln in txt.splitlines():
            say('    ' + ln)
        dt = time.time() - t0
        say('%s: exit %d, %.1f s' % (label, p.returncode, dt))
        times[label] = dt
        return p.returncode, txt

    def finish():
        say('notes:')
        for n in notes:
            say('  ' + n)
        say('RESULT: %s (total %.1f s)%s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails),
                                            time.time() - t_all, ' DRY RUN' if a.dry_run else ''))
        fn = 'build-final%s.txt' % ('-dry' if a.dry_run else '')
        if not os.path.isdir(B):  # never create final2/b here: prep-final2.py must make it
            return 1 if fails else 0
        os.makedirs(top, exist_ok=True)
        with open(os.path.join(top, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
        if not a.dry_run:
            with open(os.path.join(top, 'notes.txt'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(notes) + '\n')
        return 1 if fails else 0

    say('# build-final2 (M2) %s %s%s' % (time.strftime('%Y-%m-%d %H:%M:%S'), name, ' DRY RUN' if a.dry_run else ''))
    notes.append('tools that ran (sha256/16): ' + ', '.join('%s %s' % (os.path.basename(p), sha(p)[:16])
                                                            for p in TOOLS))
    say(notes[-1])
    if os.path.exists(HOLD):
        check('no HOLD file', False)
        return finish()
    check('prep-final2 RESULT: PASS (b/prep.txt)', result_pass(os.path.join(B, 'prep.txt')))
    check('shared DLL before == E3CB99CF', sha(SHARED) == SHARED_SHA)
    if result_pass(os.path.join(B, 'prep.txt')):
        for ln in open(os.path.join(B, 'prep.txt'), encoding='utf-8'):
            if re.match(r'^(commits: |blob |PASS default |gen-on native-gpu-build)', ln):
                notes.append('prep: ' + ln.strip())
    if fails:
        return finish()
    return leg(a, LEGS[a.leg], top, say, check, run, notes, finish) if a.leg else \
        stage(a, top, say, check, run, notes, finish)


def leg(a, L, top, say, check, run, notes, finish):
    lg = a.leg
    if not a.dry_run:
        check('fsyntax2 RESULT: PASS (b/fsyntax/fsyntax.txt)', result_pass(os.path.join(B, 'fsyntax', 'fsyntax.txt')))
        # a --dry-run relink creates the out dirs (command/rsp text only); a real output file means "not new"
        check('leg output is new (b/%s/link-on/%s)' % (lg, L['out']),
              not os.path.exists(os.path.join(top, 'link-on', L['out'])))
        if a.leg in ('rt', 'gpu', 'xe', 'nat'):
            check('CTL output is new (b/%s/link-ctl/%s)' % (lg, L['out']),
                  not os.path.exists(os.path.join(top, 'link-ctl', L['out'])))
    if a.jobs > 8:
        check('--jobs <= 8', False)
    if FAILS:
        return finish()
    comp = [PY, os.path.join(A2, 'recompile.py')] + L['comp'] + ['--jobs', str(a.jobs), '--priority', 'normal',
                                                                '--fwd-src']
    link = [PY, os.path.join(A2, 'relink.py'), '--ninja', L['ninja'], '--target', L['target'], '--priority', 'normal']
    is_exe = L['out'].endswith('.exe')
    # CTL (D1)
    if 'ctl_of' in L:
        ok = result_pass(os.path.join(B, L['ctl_of'], 'build-final.txt'))
        check('CTL of %s passed earlier (b/%s/build-final.txt RESULT: PASS)' % (L['ctl_of'], L['ctl_of']),
              bool(ok) or a.dry_run)
        if ok:
            for ln in open(os.path.join(B, L['ctl_of'], 'notes.txt'), encoding='utf-8'):
                if ln.startswith('CTL'):
                    notes.append(ln.strip() + ' (leg %s)' % L['ctl_of'])
    else:
        rc, _ = run('CTL recompile', comp + ['--list', os.path.join(top, 'list-ctl.tsv'),
                                             '--log-dir', os.path.join(top, 'log-ctl')])
        if not check('CTL recompile', rc == 0):
            return finish()
        cmd = link + ['--replace-file', os.path.join(top, 'replace-ctl.txt'), '--out-dir',
                      os.path.join(top, 'link-ctl'), '--compare', L['ref']]
        if is_exe:
            cmd += ['--compare-map', L['refmap']]
        rc, txt = run('CTL relink', cmd)
        if a.dry_run:
            check('CTL relink dry run', rc == 0)
        else:
            m = re.search(r'^(PASS|DIFF) compare .*$', txt, re.M)
            mm = re.search(r'^(PASS|DIFF) map .*$', txt, re.M)
            ok = rc == 0 and m and m.group(1) == 'PASS' and (not is_exe or (mm and mm.group(1) == 'PASS'))
            if not check('D1 CTL %s == %s except TimeDateStamp%s (else STOP)' % (
                    L['out'], os.path.relpath(L['ref'], A2), ' + map' if is_exe else ''), ok,
                    '%s%s' % (m.group(0).strip() if m else 'no compare line',
                              ('; ' + mm.group(0).strip()) if mm else '')):
                say('STOP: D1 control leg failed; do not build ON, do not stage (rating C20B6FDB D1)')
                return finish()
            notes.append('CTL: ' + m.group(0).strip())
            if mm:
                notes.append('CTL: ' + mm.group(0).strip())
    # ON
    cmd = comp + ['--list', os.path.join(top, 'list-on.tsv'), '--log-dir', os.path.join(top, 'log-on'),
                  pmap(L['pm'])]
    for d in L.get('define', []):
        cmd += ['--define', d]
    if L.get('inc'):
        cmd += ['--include-first', L['inc']]
    rc, txt = run('ON recompile', cmd)
    if not check('ON recompile', rc == 0):
        return finish()
    for ln in txt.splitlines():
        if ln.startswith('PASS ') and ' obj ' in ln:
            notes.append('ON object ' + ln[5:].strip())
    if L.get('define'):
        notes.append('ON defines: ' + ', '.join('-D' + d for d in L['define']))
    rcmds = open(os.path.join(top, 'log-on', 'recompile-commands.txt'), encoding='utf-8').read()
    if L.get('inc'):
        gi = L['inc'].replace('\\', '/').lower()
        cm = re.findall(r'^cmd: (.*)$', rcmds, re.M)
        bad = [c for c in cm if not (0 <= c.replace('\\', '/').lower().find(gi) <
                                     c.replace('\\', '/').lower().find(L['inc_before']))]
        check('%s: -I %s ahead of %s in all %d commands' % (lg, os.path.relpath(L['inc'], FIN), L['inc_before'],
                                                           len(cm)), cm and not bad, '%d bad' % len(bad))
        notes.append('ON --include-first %s (ahead of %s)' % (os.path.relpath(L['inc'], A2), L['inc_before']))
    rc, txt = run('ON relink', link + ['--replace-file', os.path.join(top, 'replace-on.txt'), '--out-dir',
                                       os.path.join(top, 'link-on')])
    if a.dry_run:
        check('ON relink dry run', rc == 0)
        say('dry run: stopping before the gates')
        return finish()
    new = os.path.join(top, 'link-on', L['out'])
    if not check('ON relink', rc == 0 and os.path.isfile(new)):
        return finish()
    # Gates
    for d in ('log-ctl', 'log-on'):
        for lf in glob.glob(os.path.join(top, d, '*.log')):
            t = open(lf, encoding='utf-8', errors='replace').read()
            check('no pch/error text in %s/%s' % (d, os.path.basename(lf)),
                  not re.search(r'pch|error', t, re.I), t[:300].replace('\n', ' | '))
    data, refd = open(new, 'rb').read(), open(L['ref'], 'rb').read()
    nsha = sha(new)
    say('ON %s %d B %s' % (L['out'], len(data), nsha))
    notes.append('ON %s %s' % (L['out'], nsha))
    check('ON output differs from the reference', nsha != sha(L['ref']))
    for n in L['want']:
        check('needle in ON: %s' % n, n.encode() in data)
        check('needle NOT in reference: %s' % n, n.encode() not in refd)
    for n in L['absent']:
        check('needle NOT in ON: %s' % n, n.encode() not in data)
    if lg in ('nat', 'natoff'):
        check('reference has the old fingerprint %s' % FP_OLD, FP_OLD.encode() in refd)
    notes.append('needles: ON has %s; reference lacks them; ON lacks %s' % (L['want'], L['absent'] or '-'))
    files = [new] + glob.glob(os.path.join(top, 'link-on', '*.map'))
    for f in files:
        b = open(f, 'rb').read()
        check('no overlay path bytes (agent2/final2/b/) in %s' % os.path.basename(f), not OVERLAY_RE.search(b))
    rc, txt = run('pe-check', [PY, PECHECK, '--new', new, '--ref', L['ref']] + L['pe'],
                  dry=False)
    check('D5 pe-check %s vs %s' % (L['out'], os.path.relpath(L['ref'], A2)), rc == 0)
    notes.append('D5 pe-check vs %s: %s' % (os.path.relpath(L['ref'], A2), 'PASS' if rc == 0 else 'FAIL'))
    if lg in ('xe', 'xeoff', 'nat', 'natoff'):
        mp = glob.glob(os.path.join(top, 'link-on', '*.map'))
        if check('one map in link-on', len(mp) == 1):
            xe = lg in ('xe', 'xeoff')
            mref = os.path.join(A2, 'devoff4-bin', 'legodimensions.map') if xe else L['refmap']
            mode = 's4c' if xe else 'same'
            rc, txt = run('mapcheck', [PY, os.path.join(A2, 's4b', 'mapcheck-s4c.py'), '--map', mp[0], '--ref', mref,
                                       '--mode', mode, '--out', os.path.join(top, 'mapcheck.txt')], dry=False)
            check('mapcheck --mode %s vs %s (hooked aliases by name/object; s4c = 31)' % (
                mode, os.path.relpath(mref, A2)), rc == 0)
            notes.append('mapcheck --mode %s vs %s: %s' % (mode, os.path.relpath(mref, A2),
                                                         'PASS' if rc == 0 else 'FAIL'))
    if lg in ('xeoff', 'natoff'):
        sib = os.path.join(B, lg[:-3], 'link-on', L['out'])
        if os.path.isfile(sib):
            check('%s exe differs from the %s exe (the define took effect)' % (lg, lg[:-3]), sha(sib) != nsha)
    check('shared DLL after == E3CB99CF', sha(SHARED) == SHARED_SHA)
    notes.append('times: ' + ', '.join('%s %.1f s' % kv for kv in times_of(OUT)))
    return finish()


def times_of(out):
    return [(m.group(1), float(m.group(2))) for m in (re.match(r'^(.+): exit \d+, ([\d.]+) s$', l) for l in out) if m]


def stage(a, top, say, check, run, notes, finish):
    base, reps = STAGES[a.stage]
    dst = os.path.join(A2, a.stage + '-bin')
    check('bin dir is new (%s)' % os.path.relpath(dst, R), not os.path.exists(dst))
    args = []
    for fn, lg in reps:
        lt = os.path.join(B, lg)
        check('leg %s RESULT: PASS' % lg, bool(result_pass(os.path.join(lt, 'build-final.txt'))))
        src = os.path.join(lt, 'link-on', fn)
        if fn.endswith('.map'):
            mp = glob.glob(os.path.join(lt, 'link-on', '*.map'))
            src = mp[0] if len(mp) == 1 else src
        check('%s exists (%s)' % (fn, os.path.relpath(src, A2)), os.path.isfile(src))
        args += ['--replace', '%s=%s' % (fn, src)]
        if os.path.isfile(os.path.join(lt, 'notes.txt')) and fn != 'legodimensions.map':
            notes += ['%s: %s' % (lg, ln.strip()) for ln in open(os.path.join(lt, 'notes.txt'), encoding='utf-8')
                      if ln.strip() and not ln.startswith('tools') and not ln.startswith('prep:')]
    if a.stage.startswith('nativefinal'):
        t = os.path.join(B, 'nat', 'gen-on', 'native-gpu-build.txt')
        notes.append('native-gpu-build.txt (b/nat/gen-on, not staged: native4b-bin has none): %s' %
                     open(t, encoding='utf-8').read().strip())
        notes.append('NEW rexruntime.dll / rexgpu-xenos.dll from b/rt, b/gpu (rexglue-sdk a7e79c0); TracyClient.dll is '
                     'native4b-bin\'s')
    notes.append('overlay = committed blobs (rexglue-sdk a7e79c0, DimensionsRecomp 2de88ce) in the snap1 base EOL form: '
                 'shaders.cpp CRLF (autocrlf=true checkout form) 4B8250E9 = blob 88D8CC7F; all other files LF = blob')
    if FAILS:
        return finish()
    rc, txt = run('stage', [PY, os.path.join(A2, 'stage-variant.py'), '--base', base, '--out', dst, '--title',
                            TITLES[a.stage] + ' [M2, build/agent2/final2/build-final2.py]'] + args +
                  sum([['--note', n] for n in notes], []))
    if a.dry_run:
        check('stage dry run', rc == 0)
        return finish()
    if not check('stage %s (atomic)' % os.path.basename(dst), rc == 0):
        return finish()
    rc, txt = run('verify', [PY, os.path.join(A2, 'session3', 'verify-bins.py'), dst] +
                  [os.path.join(A2, b) for b in SHARED_BINS], dry=False)
    if not check('D6 verify-bins new + devoff4b, devoff4b-cg26, native4b: 0 FAIL', rc == 0):
        say('STOP: a shared bin failed its MANIFEST (rating D6)')
    check('D6 shared DLL after == E3CB99CF', sha(SHARED) == SHARED_SHA)
    for fn in sorted(os.listdir(dst)):
        if os.path.isfile(os.path.join(dst, fn)):
            say('  %s %s' % (fn, sha(os.path.join(dst, fn))))
    say('  MANIFEST.txt sha256 %s' % sha(os.path.join(dst, 'MANIFEST.txt')))
    fn = 'TracyClient.dll'
    check('%s == %s' % (fn, os.path.basename(base)), sha(os.path.join(dst, fn)) == sha(os.path.join(base, fn)))
    dev2 = os.path.join(A2, 'devfinal2-bin')
    for fn, lg, old in (('rexruntime.dll', 'rt', 'A33801D1'), ('rexgpu-xenos.dll', 'gpu', SHARED_SHA)):
        s = sha(os.path.join(dst, fn))
        check('%s == b/%s/link-on output' % (fn, lg), s == sha(os.path.join(B, lg, 'link-on', fn)))
        check('%s != old %s' % (fn, old[:8]), not s.startswith(old))
        if a.stage == 'nativefinal2':
            check('%s == devfinal2-bin copy' % fn, os.path.isdir(dev2) and s == sha(os.path.join(dev2, fn)))
    check('no cache/ in the bin', not os.path.exists(os.path.join(dst, 'cache')))
    return finish()


if __name__ == '__main__':
    sys.exit(main())
