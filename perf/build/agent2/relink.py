#!/usr/bin/env python3
# relink.py (Agent 2, board run 2 task #1: the S4b CTR and CG26 bins). Re-runs ONE ninja link edge in a scratch dir.
#
#   python build/agent2/relink.py --ninja <build dir>/build.ninja (or build-Release.ninja) --target <output>
#          --out-dir <scratch dir> [--replace OLD=NEW ...] [--compare REF] [--compare-map REF.map] [--dry-run]
#
# Reads the edge that makes --target (path as written in the ninja files, unescaped; matched case-insensitively
# after normpath) and its rule from the ninja file and every file it includes. --replace swaps an explicit object
# input (OLD as written in the ninja file, NEW an existing file). TARGET_FILE, TARGET_IMPLIB, TARGET_PDB, RSP_FILE and
# every -Xlinker /MAP: go into --out-dir; PRE_LINK and POST_BUILD become "cd ."; the expanded command runs from the
# build dir at Below Normal priority. The command and rsp are checked to name no output outside --out-dir, so
# nothing is written outside it. --compare REF: the new binary must equal REF except 4-byte fields that hold the
# two links' COFF TimeDateStamps (lld writes the link time into the PE header and the resource directory tables).
# --compare-map REF.map: the maps must be equal except the "Timestamp is" line.
# The HOLD rule: refuses to start while perf-notes/WINDOW-HOLD.txt exists, and kills the link if it appears.
import argparse, hashlib, os, re, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HOLD = os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')
BELOW_NORMAL = 0x00004000
PRIO = {'idle': 0x00000040, 'belownormal': BELOW_NORMAL, 'normal': 0x00000020}  # normal: 11-25 night (cap lifted)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def read_lines(path):
    with open(path, 'r', encoding='utf-8', errors='surrogateescape') as f:
        raw = f.read().split('\n')
    out, cur = [], None
    for line in raw:
        line = line.rstrip('\r')
        if cur is not None:
            line = cur + line.lstrip(' ')
            cur = None
        m = re.search(r'(\$+)$', line)
        if m and len(m.group(1)) % 2 == 1:
            cur = line[:-1]
            continue
        out.append(line)
    if cur is not None:
        out.append(cur)
    return out


class Scope:
    def __init__(self):
        self.globals, self.rules, self.edges, self.files = {}, {}, [], []
        self.unresolved = set()


def evaluate(s, lookup):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == '$' and i + 1 < len(s):
            n = s[i + 1]
            if n in ' :$':
                out.append(n)
                i += 2
                continue
            if n == '{':
                j = s.index('}', i)
                out.append(lookup(s[i + 2:j]))
                i = j + 1
                continue
            m = re.match(r'[A-Za-z0-9_-]+', s[i + 1:])
            if m:
                out.append(lookup(m.group(0)))
                i += 1 + len(m.group(0))
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def split_unescaped(s, ch):
    i = 0
    while i < len(s):
        if s[i] == '$':
            i += 2
            continue
        if s[i] == ch:
            return s[:i], s[i + 1:]
        i += 1
    return s, None


def lex_paths(s, lookup):
    toks, cur, have, i = [], [], False, 0
    while i < len(s):
        c = s[i]
        if c == '$' and i + 1 < len(s):
            n = s[i + 1]
            if n in ' :$':
                cur.append(n)
                have = True
                i += 2
                continue
            if n == '{':
                j = s.index('}', i)
                cur.append(lookup(s[i + 2:j]))
                have = True
                i = j + 1
                continue
            m = re.match(r'[A-Za-z0-9_-]+', s[i + 1:])
            if m:
                cur.append(lookup(m.group(0)))
                have = True
                i += 1 + len(m.group(0))
                continue
        if c == ' ':
            if have:
                toks.append(''.join(cur))
            cur, have = [], False
            i += 1
            continue
        cur.append(c)
        have = True
        i += 1
    if have:
        toks.append(''.join(cur))
    return toks


def parse(path, sc, build_dir):
    sc.files.append(path)
    lines = read_lines(path)
    glook = lambda k: sc.globals.get(k, '')
    i = 0
    while i < len(lines):
        l = lines[i]
        if not l.strip() or l.lstrip().startswith('#'):
            i += 1
            continue
        if l.startswith('rule '):
            name, binds = l[5:].strip(), {}
            i += 1
            while i < len(lines) and lines[i][:1] in (' ', '\t') and lines[i].strip():
                k, _, v = lines[i].strip().partition('=')
                binds[k.strip()] = v.strip()
                i += 1
            sc.rules[name] = binds
            continue
        if l.startswith('build '):
            outs_s, rest = split_unescaped(l[6:], ':')
            otoks = lex_paths(outs_s, glook)
            rtoks = lex_paths(rest or '', glook)
            outs = otoks[:otoks.index('|')] if '|' in otoks else otoks
            rule, ins, mode = rtoks[0], [], 'explicit'
            implicit, order = [], []
            for t in rtoks[1:]:
                if t in ('|', '||', '|@'):
                    mode = {'|': 'implicit', '||': 'order', '|@': 'validation'}[t]
                    continue
                if mode == 'explicit':
                    ins.append(t)
                elif mode == 'implicit':
                    implicit.append(t)
                elif mode == 'order':
                    order.append(t)
            binds = {}
            i += 1
            while i < len(lines) and lines[i][:1] in (' ', '\t') and lines[i].strip():
                k, _, v = lines[i].strip().partition('=')
                binds[k.strip()] = v.lstrip()
                i += 1
            sc.edges.append({'outs': outs, 'rule': rule, 'ins': ins, 'implicit': implicit, 'order': order,
                             'binds': binds, 'file': path})
            continue
        if l.startswith('include ') or l.startswith('subninja '):
            p = evaluate(l.split(' ', 1)[1].strip(), glook)
            full = p if os.path.isabs(p) else os.path.join(build_dir, p)
            parse(full, sc, build_dir)
            i += 1
            continue
        if l.startswith('pool ') or l.startswith('default '):
            i += 1
            while i < len(lines) and lines[i][:1] in (' ', '\t') and lines[i].strip():
                i += 1
            continue
        m = re.match(r'^([A-Za-z0-9_.-]+)\s*=\s?(.*)$', l)
        if m:
            sc.globals[m.group(1)] = evaluate(m.group(2), glook)
        i += 1


def ts_value(buf):
    e = int.from_bytes(buf[0x3C:0x40], 'little')
    if buf[e:e + 4] != b'PE\0\0':
        raise SystemExit('not a PE file')
    return bytes(buf[e + 8:e + 12]), e + 8


def pe_compare(new, ref):
    a, b = open(new, 'rb').read(), open(ref, 'rb').read()
    if len(a) != len(b):
        return False, 'size %d vs %d B' % (len(a), len(b))
    tn, off = ts_value(a)
    tr, _ = ts_value(b)
    ma, mb = memoryview(a), memoryview(b)
    runs, CH = [], 1 << 16
    for c0 in range(0, len(a), CH):
        if ma[c0:c0 + CH] == mb[c0:c0 + CH]:
            continue
        j = c0
        end = min(c0 + CH, len(a))
        while j < end:
            if a[j] != b[j]:
                k = j
                while k < len(a) and a[k] != b[k]:
                    k += 1
                runs.append((j, k))
                j = k
            else:
                j += 1
    if not runs:
        return True, 'byte-identical'
    bad, fields = [], set()
    for s, e in runs:
        ok = False
        for k in range(max(0, e - 4), s + 1):
            if k <= s and e <= k + 4 and a[k:k + 4] == tn and b[k:k + 4] == tr:
                ok = True
                fields.add(k)
                break
        if not ok:
            bad.append((s, e))
    if bad:
        return False, '%d differing run(s) outside timestamp fields, first at 0x%X-0x%X' % (len(bad), bad[0][0],
                                                                                           bad[0][1])
    return True, 'identical except %d TimeDateStamp field(s) (%s vs %s; COFF header at 0x%X%s)' % (
        len(fields), tn[::-1].hex(), tr[::-1].hex(), off, ', included' if off in fields else ', NOT among them')


def map_compare(new, ref):
    def lines(p):
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            return [x for x in f.read().splitlines() if 'Timestamp is' not in x]
    a, b = lines(new), lines(ref)
    if a == b:
        return True, 'equal except the Timestamp line (%d lines)' % len(a)
    n = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
    return False, '%d line(s) differ (%d vs %d lines)' % (n, len(a), len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ninja', required=True)
    ap.add_argument('--target', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--replace', action='append', default=[])
    ap.add_argument('--replace-file', help='a file with one OLD=NEW --replace per line')
    ap.add_argument('--compare')
    ap.add_argument('--compare-map')
    ap.add_argument('--priority', choices=sorted(PRIO), default='idle')  # session 3: Idle by default
    ap.add_argument('--link-flag', action='append', default=[],
                    help='session 3: append to LINK_FLAGS, e.g. "-Xlinker /threads:2"')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.replace_file:
        with open(a.replace_file, 'r', encoding='utf-8') as f:
            a.replace += [x.strip() for x in f if x.strip() and not x.startswith('#')]
    if os.path.exists(HOLD):
        print('HOLD file exists: not starting')
        return 9
    ninja = os.path.abspath(a.ninja)
    bdir = os.path.dirname(ninja)
    od = os.path.abspath(a.out_dir)
    os.makedirs(od, exist_ok=True)
    sc = Scope()
    parse(ninja, sc, bdir)
    tgt = norm(a.target if os.path.isabs(a.target) else os.path.join(bdir, a.target))
    hits = [e for e in sc.edges if any(norm(o if os.path.isabs(o) else os.path.join(bdir, o)) == tgt
                                       for o in e['outs'])]
    print('parsed %d file(s), %d edges, %d rules; edges making the target: %d' % (len(sc.files), len(sc.edges),
                                                                                len(sc.rules), len(hits)))
    if len(hits) != 1:
        print('FAIL: need exactly one edge for %s' % a.target)
        return 2
    e = hits[0]
    rule = sc.rules.get(e['rule'])
    if rule is None:
        print('FAIL: rule %s not found' % e['rule'])
        return 2
    print('edge: %s (rule %s, from %s), %d explicit inputs, %d implicit' % (
        e['outs'][0], e['rule'], os.path.relpath(e['file'], R), len(e['ins']), len(e['implicit'])))
    glook = lambda k: sc.globals.get(k, '')
    binds = {k: evaluate(v, glook) for k, v in e['binds'].items()}
    orig = dict(binds)
    ins = list(e['ins'])
    for rp in a.replace:
        old, _, new = rp.partition('=')
        new = os.path.abspath(new)
        if not os.path.isfile(new):
            print('FAIL: replacement %s does not exist' % new)
            return 2
        idx = [k for k, t in enumerate(ins) if norm(t) == norm(old)]
        if len(idx) != 1:
            print('FAIL: %s matches %d explicit inputs (need 1)' % (old, len(idx)))
            return 2
        print('replace input %d: %s -> %s (%d B, %s)' % (idx[0], ins[idx[0]], new, os.path.getsize(new),
                                                        sha(new)[:16]))
        ins[idx[0]] = new.replace('\\', '/')
    tf = binds.get('TARGET_FILE', e['outs'][0])
    newtf = os.path.join(od, os.path.basename(tf.replace('/', os.sep)))
    binds['TARGET_FILE'] = newtf
    for k in ('TARGET_IMPLIB', 'TARGET_PDB', 'RSP_FILE'):
        if k in binds:
            binds[k] = os.path.join(od, os.path.basename(binds[k].replace('/', os.sep)))
    for k in ('PRE_LINK', 'POST_BUILD'):
        if k in binds:
            binds[k] = 'cd .'
    for k in ('LINK_FLAGS', 'FLAGS', 'LANGUAGE_COMPILE_FLAGS', 'ARCH_FLAGS'):
        if k in binds:
            binds[k] = re.sub(r'(?i)/MAP:(\S+)', lambda m: '/MAP:' + os.path.join(
                od, os.path.basename(m.group(1).replace('/', os.sep))), binds[k])
    if a.link_flag:
        if 'LINK_FLAGS' not in binds and '$LINK_FLAGS' not in rule['command']:
            print('FAIL: --link-flag given but neither the edge nor the rule has LINK_FLAGS')
            return 2
        binds['LINK_FLAGS'] = (binds.get('LINK_FLAGS', '') + ' ' + ' '.join(a.link_flag)).strip()
    print('priority %s, link flags added: %s' % (a.priority, ' '.join(a.link_flag) or '-'))
    for k, v in orig.items():
        if v != binds[k]:
            print('  %s: %s\n    -> %s' % (k, v[:300], binds[k][:300]))
    special = {'in': ' '.join(ins), 'in_newline': '\n'.join(ins), 'out': newtf}

    def look(k):
        if k in special:
            return special[k]
        if k in binds:
            return binds[k]
        if k in sc.globals:
            return sc.globals[k]
        sc.unresolved.add(k)
        return ''
    cmd = evaluate(rule['command'], look)
    rsp = rule.get('rspfile')
    rspfile = evaluate(rsp, look) if rsp else None
    rspc = evaluate(rule.get('rspfile_content', ''), look) if rsp else ''
    if sc.unresolved:
        print('NOTE unresolved (empty) variables: %s' % ', '.join(sorted(sc.unresolved)))
    # Output check: every output-looking argument must be inside the out dir.
    probs = []
    for m in re.finditer(r'(?i)(?:/MAP:|/implib:|/pdb:|/OUT:|/DEF:|-o\s+)("?)([^\s"]+)\1', cmd + ' ' + rspc):
        p = m.group(2)
        full = norm(p if os.path.isabs(p) else os.path.join(bdir, p))
        if m.group(0).lower().startswith('/def:'):
            print('NOTE /DEF input: %s' % p)
            continue
        if not full.startswith(norm(od) + os.sep):
            probs.append(p)
    if rspfile and not norm(rspfile).startswith(norm(od) + os.sep):
        probs.append(rspfile)
    with open(os.path.join(od, 'relink-command.txt'), 'w', encoding='utf-8') as f:
        f.write('cwd: %s\ncommand: %s\nrspfile: %s\n' % (bdir, cmd, rspfile))
    if rsp:
        with open(os.path.join(od, 'relink-rsp-content.txt'), 'w', encoding='utf-8') as f:
            f.write(rspc)
    print('command (%d chars) and rsp (%d chars) written to %s' % (len(cmd), len(rspc), os.path.relpath(od, R)))
    if probs:
        print('FAIL: output path(s) outside the out dir: %s' % ', '.join(probs))
        return 2
    print('PASS outputs: every output path in the command is inside %s' % os.path.relpath(od, R))
    if a.dry_run:
        print('dry run: not linking')
        return 0
    if rsp:
        with open(rspfile, 'w', encoding='utf-8', newline='') as f:
            f.write(rspc)
    log = os.path.join(od, 'relink.log')
    t0 = time.time()
    with open(log, 'wb') as lf:
        p = subprocess.Popen(cmd, cwd=bdir, stdout=lf, stderr=subprocess.STDOUT, creationflags=PRIO[a.priority])
        while p.poll() is None:
            if os.path.exists(HOLD):
                subprocess.run('taskkill /T /F /PID %d' % p.pid, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print('HOLD file appeared: link killed')
                return 30
            time.sleep(1)
    dt = time.time() - t0
    print('link exit %d, %.1f s (log %s)' % (p.returncode, dt, os.path.relpath(log, R)))
    if p.returncode != 0:
        with open(log, 'r', encoding='utf-8', errors='replace') as f:
            print(f.read()[-3000:])
        return 3
    for fn in sorted(os.listdir(od)):
        fp = os.path.join(od, fn)
        if os.path.isfile(fp) and not fn.startswith('relink'):
            print('  %s %d B %s' % (fn, os.path.getsize(fp), sha(fp)))
    rc = 0
    if a.compare:
        ok, msg = pe_compare(newtf, a.compare)
        print('%s compare %s vs %s: %s' % ('PASS' if ok else 'DIFF', os.path.basename(newtf),
                                           os.path.relpath(a.compare, R), msg))
        rc = rc or (0 if ok else 4)
    if a.compare_map:
        mp = [os.path.join(od, f) for f in os.listdir(od) if f.lower().endswith('.map')]
        if len(mp) != 1:
            print('FAIL: expected one .map in the out dir, found %d' % len(mp))
            return 5
        ok, msg = map_compare(mp[0], a.compare_map)
        print('%s map %s vs %s: %s' % ('PASS' if ok else 'DIFF', os.path.basename(mp[0]),
                                       os.path.relpath(a.compare_map, R), msg))
        rc = rc or (0 if ok else 4)
    return rc


if __name__ == '__main__':
    sys.exit(main())
