#!/usr/bin/env python3
# recompile.py (Agent 2, board run 2 task #1: the S4b CTR and CG26 bins). Recompiles TUs from a CMake
# compile_commands.json into scratch objects, with the build's own command lines.
#
#   python build/agent2/recompile.py --ccdb <build dir>/compile_commands.json --list <tsv> [--define NAME=VAL ...]
#          [--jobs N] [--log-dir D] [--dry-run]
#
# <tsv> rows: <source as in the ccdb 'file' field> TAB <source to compile> TAB <output object>. For each row the ccdb
# command is reused unchanged except: the '-c' source and the '-o' object are swapped for the row's paths, and each
# --define is added after the compiler. The command runs from the ccdb 'directory' (the build dir) at Below Normal
# priority, at most --jobs (max 8) at a time. Refuses commands with other output flags (-MF, -MD, -MMD, -ftime-trace,
# /Fo, /Fd), so the only file written is the object. HOLD rule: refuses to start while perf-notes/WINDOW-HOLD.txt
# exists, and kills the compiles if it appears.
import argparse, hashlib, json, os, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
BELOW_NORMAL = 0x00004000
BAD = ('-MF', '-MD', '-MMD', '-MT', '-MQ', '/Fo', '/Fd')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ccdb', required=True)
    ap.add_argument('--list', required=True)
    ap.add_argument('--define', action='append', default=[])
    ap.add_argument('--obj-filter', help='keep only ccdb entries whose -o path contains this (use / separators), '
                                         'e.g. /Release/ for a multi-config ccdb')
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--log-dir')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.jobs > 8:
        print('FAIL: --jobs above the -j8 cap')
        return 2
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    with open(a.ccdb, 'r', encoding='utf-8') as f:
        db = json.load(f)
    by = {}
    for ent in db:
        fp = ent['file'] if os.path.isabs(ent['file']) else os.path.join(ent['directory'], ent['file'])
        by.setdefault(norm(fp), []).append(ent)
    rows = []
    with open(a.list, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if not line or line.startswith('#'):
                continue
            src, new, obj = line.split('\t')
            rows.append((src, os.path.abspath(new), os.path.abspath(obj)))
    log_dir = os.path.abspath(a.log_dir or os.path.dirname(os.path.abspath(a.list)))
    os.makedirs(log_dir, exist_ok=True)
    jobs = []
    for src, new, obj in rows:
        ents = by.get(norm(src), [])
        if a.obj_filter:
            def out_of(ent):
                if ent.get('output'):
                    return ent['output']
                t = ent.get('command', '').split(' ')
                return t[t.index('-o') + 1] if '-o' in t[:-1] else ''
            ents = [ent for ent in ents if a.obj_filter in out_of(ent).replace('\\', '/')]
        if len(ents) != 1:
            print('FAIL: %s has %d ccdb entries (need 1)' % (src, len(ents)))
            return 2
        ent = ents[0]
        if 'command' not in ent:
            print('FAIL: entry without a command string: %s' % src)
            return 2
        toks = ent['command'].split(' ')
        bad = [t for t in toks if t.startswith(BAD) or t.startswith('-ftime-trace')]
        if bad:
            print('FAIL: %s: output flag(s) %s in the command' % (src, bad))
            return 2
        io = [k for k, t in enumerate(toks) if t == '-o']
        ic = [k for k, t in enumerate(toks) if t == '-c']
        if len(io) != 1 or len(ic) != 1:
            print('FAIL: %s: need exactly one -o and one -c (found %d, %d)' % (src, len(io), len(ic)))
            return 2
        if norm(toks[ic[0] + 1] if os.path.isabs(toks[ic[0] + 1]) else os.path.join(ent['directory'],
                                                                                  toks[ic[0] + 1])) != norm(src):
            print('FAIL: %s: the -c argument is %s' % (src, toks[ic[0] + 1]))
            return 2
        if not os.path.isfile(new):
            print('FAIL: source to compile does not exist: %s' % new)
            return 2
        old_obj = toks[io[0] + 1]
        toks[io[0] + 1] = obj
        toks[ic[0] + 1] = new
        for d in reversed(a.define):
            toks.insert(1, '-D' + d)
        os.makedirs(os.path.dirname(obj), exist_ok=True)
        cmd = ' '.join(toks)
        tag = os.path.basename(obj)
        jobs.append({'src': src, 'new': new, 'obj': obj, 'old_obj': old_obj, 'cmd': cmd, 'cwd': ent['directory'],
                     'log': os.path.join(log_dir, tag + '.log'), 'tag': tag})
    with open(os.path.join(log_dir, 'recompile-commands.txt'), 'w', encoding='utf-8') as f:
        for j in jobs:
            f.write('cwd: %s\nwas -o %s\ncmd: %s\n\n' % (j['cwd'], j['old_obj'], j['cmd']))
    print('%d TU(s); defines: %s; commands in %s' % (len(jobs), ', '.join(a.define) or '-',
                                                   os.path.relpath(os.path.join(log_dir, 'recompile-commands.txt'),
                                                                   R)))
    for j in jobs:
        print('  %s: %s (%s) -> %s' % (os.path.basename(j['src']), os.path.relpath(j['new'], R),
                                       sha(j['new'])[:16], os.path.relpath(j['obj'], R)))
    if a.dry_run:
        print('dry run: nothing compiled')
        return 0
    t0 = time.time()
    pending, running, done = list(jobs), [], []
    while pending or running:
        if os.path.exists(HOLD):
            for j in running:
                subprocess.run('taskkill /T /F /PID %d' % j['p'].pid, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            print('HOLD file appeared: compiles killed')
            return 30
        while pending and len(running) < a.jobs:
            j = pending.pop(0)
            if os.path.exists(j['obj']):
                os.remove(j['obj'])
            j['lf'] = open(j['log'], 'wb')
            j['t'] = time.time()
            j['p'] = subprocess.Popen(j['cmd'], cwd=j['cwd'], stdout=j['lf'], stderr=subprocess.STDOUT,
                                      creationflags=BELOW_NORMAL)
            running.append(j)
        for j in list(running):
            if j['p'].poll() is not None:
                j['lf'].close()
                j['dt'] = time.time() - j['t']
                running.remove(j)
                done.append(j)
        time.sleep(0.5)
    fails = 0
    for j in jobs:
        rc = j['p'].returncode
        ok = rc == 0 and os.path.isfile(j['obj'])
        fails += 0 if ok else 1
        warn = os.path.getsize(j['log'])
        print('%s %s exit %d %.1f s%s%s' % ('PASS' if ok else 'FAIL', j['tag'], rc, j['dt'],
                                            (' obj %d B %s' % (os.path.getsize(j['obj']), sha(j['obj'])[:16]))
                                            if ok else '', (' (log %d B)' % warn) if warn else ''))
        if not ok:
            with open(j['log'], 'r', encoding='utf-8', errors='replace') as f:
                print(f.read()[-2000:])
    print('wall %.1f s, %d failure(s)' % (time.time() - t0, fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
