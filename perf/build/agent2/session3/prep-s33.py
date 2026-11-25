#!/usr/bin/env python3
# prep-s33.py (M2, session 3): prepare a #33 rexgpu-xenos.dll test build WITHOUT touching snap1 / snap1-sdk.
#
#   python build/agent2/session3/prep-s33.py --patch P --sha SHA256 --tag NAME [--dry-run]
#
# Overlay = build/agent2/s33/<tag>/sdk: a full copy of snap1's rexglue-sdk/src/graphics plus ONLY the patched headers
# under include/ (so every other header, and the PCH, still come from snap1). The patch is applied there in no-repo
# mode with `git -c core.autocrlf=false apply` (GIT_CEILING_DIRECTORIES set). The affected objects come from
# `ninja -t deps` of snap1-sdk (Release; read-only). Writes, in build/agent2/s33/<tag>/: list-on.tsv, list-ctl.tsv
# (recompile.py: ON compiles the overlay source with --include-first <overlay>/include; CTL compiles snap1's source),
# replace-on.txt, replace-ctl.txt (relink.py --replace-file) and prep.txt. Refuses an existing <tag> dir.
import argparse, hashlib, os, re, shutil, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
SDK = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
BDIR = os.path.join(R, 'build', 'agent2', 'snap1-sdk')
NINJA = r'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
IDLE = 0x40
OBJPRE = 'src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--patch', required=True)
    ap.add_argument('--sha', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    out = []
    say = lambda s: (out.append(s), print(s))
    fails = []

    def check(what, ok, detail=''):
        say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
        if not ok:
            fails.append(what)
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    patch = os.path.abspath(a.patch)
    top = os.path.join(R, 'build', 'agent2', 's33', a.tag)
    ov = os.path.join(top, 'sdk')
    say('# prep-s33 (M2 session 3) %s  tag %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), a.tag))
    ps = sha(patch)
    check('patch sha256 %s' % os.path.relpath(patch, R), ps == a.sha.upper(), ps)
    files = re.findall(r'^diff --git a/(\S+) b/\S+', open(patch, 'r', encoding='utf-8', newline='').read(), re.M)
    say('patch files (%d): %s' % (len(files), ', '.join(files)))
    for f in files:
        check('patch path allowed %s' % f, f.startswith('src/graphics/') or f.startswith('include/rex/graphics/'))
        check('before-file exists %s' % f, os.path.isfile(os.path.join(SDK, f)))
    if os.path.exists(top):
        check('out dir is new', False, os.path.relpath(top, R))
    if fails:
        return finish(out, None, fails)
    # Affected objects (Release) from ninja's deps log.
    p = subprocess.run([NINJA, '-C', BDIR, '-f', 'build-Release.ninja', '-t', 'deps'], capture_output=True, text=True,
                       creationflags=IDLE)
    deps, cur = {}, None
    for ln in p.stdout.splitlines():
        if ln and not ln.startswith(' '):
            cur = ln.split(':')[0].replace('\\', '/')
            deps[cur] = []
        elif ln.strip() and cur:
            deps[cur].append(ln.strip().replace('\\', '/').lower())
    want = ['rexglue-sdk/' + f.lower() for f in files]
    objs = sorted(o for o, ds in deps.items() if o.startswith(OBJPRE) and any(x.endswith(w) for x in ds for w in want))
    say('affected Release objects (%d):' % len(objs))
    for o in objs:
        say('    ' + o)
    check('affected objects found', len(objs) > 0)
    rels = [o[len(OBJPRE):-len('.obj')] for o in objs]  # e.g. d3d12/pipeline_cache.cpp
    for r in rels:
        check('source exists src/graphics/%s' % r, os.path.isfile(os.path.join(SDK, 'src', 'graphics', r)))
    if fails or a.dry_run:
        if a.dry_run:
            say('dry run: nothing copied')
        return finish(out, None, fails)
    # Overlay copy.
    os.makedirs(top)
    shutil.copytree(os.path.join(SDK, 'src', 'graphics'), os.path.join(ov, 'src', 'graphics'))
    for f in files:
        if f.startswith('include/'):
            os.makedirs(os.path.dirname(os.path.join(ov, f)), exist_ok=True)
            shutil.copy2(os.path.join(SDK, f), os.path.join(ov, f))
    n, bad = 0, []
    for d, _, fs in os.walk(os.path.join(SDK, 'src', 'graphics')):
        for fn in fs:
            s = os.path.join(d, fn)
            t = os.path.join(ov, os.path.relpath(s, SDK))
            n += 1
            if sha(s) != sha(t):
                bad.append(os.path.relpath(s, SDK))
    check('overlay copy of src/graphics equals snap1 (%d files)' % n, not bad, ', '.join(bad[:5]))
    before = {}
    for f in files:
        b = open(os.path.join(ov, f), 'rb').read()
        before[f] = (sha(os.path.join(ov, f)), b.count(b'\r\n'))
        say('before %s %s CRLF %d' % (f, before[f][0][:16], before[f][1]))
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=os.path.dirname(top))
    base = ['git', '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false', 'apply', '--verbose']
    for mode in (['--check'], []):
        q = subprocess.run(base + mode + [patch], cwd=ov, capture_output=True, text=True, env=env,
                           creationflags=IDLE)
        txt = q.stdout + q.stderr
        say('git apply %s exit %d:\n%s' % (' '.join(mode) or '(apply)', q.returncode, txt.strip()))
        chk = len(re.findall(r'^Checking patch ', txt, re.M))
        skp = len(re.findall(r'Skipped patch', txt))
        check('git apply %s: exit 0, %d Checking lines, 0 Skipped' % (' '.join(mode) or '(apply)', len(files)),
              q.returncode == 0 and chk == len(files) and skp == 0, 'exit %d, checking %d, skipped %d' % (
                  q.returncode, chk, skp))
        if fails:
            return finish(out, top, fails)
    for f in files:
        b = open(os.path.join(ov, f), 'rb').read()
        h = sha(os.path.join(ov, f))
        say('after  %s %s CRLF %d' % (f, h, b.count(b'\r\n')))
        check('changed %s' % f, h != before[f][0])
        check('no CRLF introduced %s' % f, before[f][1] > 0 or b.count(b'\r\n') == 0)
    # Lists.
    on_tsv, ctl_tsv, on_rep, ctl_rep = [], [], [], []
    for o, r in zip(objs, rels):
        uniq = r.replace('/', '__') + '.obj'
        src = os.path.join(SDK, 'src', 'graphics', r.replace('/', os.sep))
        osrc = os.path.join(ov, 'src', 'graphics', r.replace('/', os.sep))
        oon, octl = os.path.join(top, 'obj-on', uniq), os.path.join(top, 'obj-ctl', uniq)
        on_tsv.append('%s\t%s\t%s' % (src, osrc, oon))
        ctl_tsv.append('%s\t%s\t%s' % (src, src, octl))
        on_rep.append('%s=%s' % (o, oon))
        ctl_rep.append('%s=%s' % (o, octl))
    for nm, rows in (('list-on.tsv', on_tsv), ('list-ctl.tsv', ctl_tsv), ('replace-on.txt', on_rep),
                     ('replace-ctl.txt', ctl_rep)):
        with open(os.path.join(top, nm), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(rows) + '\n')
    say('wrote list-on.tsv, list-ctl.tsv, replace-on.txt, replace-ctl.txt (%d rows each)' % len(objs))
    return finish(out, top, fails)


def finish(out, top, fails):
    out.append('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
    print(out[-1])
    if top and os.path.isdir(top):
        with open(os.path.join(top, 'prep.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
