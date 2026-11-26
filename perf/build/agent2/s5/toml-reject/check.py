#!/usr/bin/env python3
# check.py (E13.1, S5 item 3): makes toml-reject.diff (rexglue-sdk-relative, vs a7e79c0) from the overlay
# files in ov/rexglue-sdk/, runs `git apply --check --cached` against the SDK index at a7e79c0 (no
# working-tree or index change), and compile-checks each changed TU with its snap1-sdk Release command
# from compile_commands.json (fsyntax + a real -c into obj/), at IDLE priority. Writes only this folder.
import difflib, hashlib, json, os, shlex, subprocess, sys, time

ITEM = 'toml-reject'
RELS = ['src/core/cvar.cpp', 'src/core/logging.cpp']
# (obj basename, needle) pairs that must be in the compiled objects.
NEEDLES = [
    ('cvar.cpp.obj', b'reported before logging started'),
    ('cvar.cpp.obj', b'FlushDeferredConfigWarnings'),
    ('cvar.cpp.obj', b'is outside the cvar\'s constraints'),
    ('cvar.cpp.obj', b'rejected ({}); keeping'),
    ('logging.cpp.obj', b'FlushDeferredConfigWarnings'),
]

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
S = os.path.join(A2, 's5', ITEM)
SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
SNAP_SDK = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
DB = os.path.join(A2, 'snap1-sdk', 'compile_commands.json')
out, fails = [], []


def say(s):
    out.append(s)
    print(s, flush=True)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def check(what, ok, detail=''):
    say('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
    if not ok:
        fails.append(what)


def blob(rel):
    return subprocess.run(['git', '-C', SDK, 'cat-file', 'blob', 'a7e79c0:' + rel], capture_output=True).stdout


head = subprocess.run(['git', '-C', SDK, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
check('SDK HEAD == a7e79c0', head.startswith('a7e79c0'), head)
parts, plus, minus = [], 0, 0
for rel in RELS:
    base, new = blob(rel), open(os.path.join(S, 'ov', 'rexglue-sdk', *rel.split('/')), 'rb').read()
    check('%s: overlay LF-only like the blob' % rel, b'\r' not in new and b'\r' not in base)
    snap = open(os.path.join(SNAP_SDK, *rel.split('/')), 'rb').read()
    check('%s: snap1 copy (compiled tree) == a7e79c0 blob' % rel, snap.replace(b'\r\n', b'\n') == base)
    say('  base %s  new %s' % (sha(base)[:16], sha(new)[:16]))
    d = ''.join(difflib.unified_diff(base.decode('utf-8').splitlines(True), new.decode('utf-8').splitlines(True),
                                     'a/' + rel, 'b/' + rel, n=3))
    parts.append('diff --git a/%s b/%s\n' % (rel, rel) + d)
    plus += sum(1 for l in d.splitlines() if l.startswith('+') and not l.startswith('+++'))
    minus += sum(1 for l in d.splitlines() if l.startswith('-') and not l.startswith('---'))
diff = os.path.join(S, ITEM + '.diff')
with open(diff, 'w', encoding='utf-8', newline='\n') as f:
    f.write(''.join(parts))
say('diff %s sha256 %s (+%d/-%d)' % (os.path.relpath(diff, R), sha(open(diff, 'rb').read()), plus, minus))
p = subprocess.run(['git', '-C', SDK, 'diff', '--cached', '--quiet'], capture_output=True)
check('SDK index clean (== HEAD a7e79c0)', p.returncode == 0)
p = subprocess.run(['git', '-C', SDK, 'apply', '--check', '--cached', '-v', diff], capture_output=True, text=True)
check('git apply --check --cached vs a7e79c0', p.returncode == 0, (p.stdout + p.stderr).strip().replace('\n', ' | '))

db = json.load(open(DB, encoding='utf-8'))
os.makedirs(os.path.join(S, 'obj'), exist_ok=True)
logs = {'fsyntax': [], 'compile': []}
for rel in RELS:
    ent = [e for e in db if e['file'].replace('\\', '/').endswith('/rexglue-sdk/' + rel)
           and 'Release' in e['command'] and '-DCMAKE_INTDIR=\\"Release\\"' in e['command']]
    check('%s: snap1-sdk Release command found' % rel, len(ent) == 1, '%d match(es)' % len(ent))
    if len(ent) != 1:
        continue
    new_src = os.path.join(S, 'ov', 'rexglue-sdk', *rel.split('/')).replace('\\', '/')
    args = shlex.split(ent[0]['command'], posix=False)
    args[-1] = new_src
    obj = os.path.join(S, 'obj', rel.split('/')[-1] + '.obj')
    args[args.index('-o') + 1] = obj
    args = [a.replace('\\"', '"') if a.startswith('-DREXGLUE_BUILD_CONFIG') or a.startswith('-DCMAKE_INTDIR')
            else a for a in args]
    for mode in ('fsyntax', 'compile'):
        a = list(args)
        if mode == 'fsyntax':
            a = [x for i, x in enumerate(a) if not (x == '-o' or (i > 0 and a[i - 1] == '-o')) and x != '-c']
            a.insert(1, '-fsyntax-only')
        t0 = time.time()
        p = subprocess.run(a, capture_output=True, text=True, cwd=ent[0]['directory'],
                           creationflags=0x00000040)  # IDLE_PRIORITY_CLASS
        log = p.stdout + p.stderr
        logs[mode].append(' '.join(a) + '\n\n' + log)
        name = rel.split('/')[-1]
        mine = [l for l in log.splitlines() if name in l and ('warning' in l or 'error' in l)]
        check('%s %s exit 0 (%.1f s)' % (rel, mode, time.time() - t0), p.returncode == 0,
              '%d errors, %d warnings in %s' % (log.count('error:'), len(mine), name))
        for l in mine:
            say('    ' + l)
    if os.path.isfile(obj):
        say('  obj %s %d B %s' % (os.path.relpath(obj, R), os.path.getsize(obj), sha(open(obj, 'rb').read())[:16]))
for mode, chunks in logs.items():
    open(os.path.join(S, mode + '.log'), 'w', encoding='utf-8').write('\n\n'.join(chunks))
for objname, needle in NEEDLES:
    path = os.path.join(S, 'obj', objname)
    check('needle in %s: %s' % (objname, needle.decode()), os.path.isfile(path) and needle in open(path, 'rb').read())
say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
open(os.path.join(S, 'check.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
sys.exit(1 if fails else 0)
