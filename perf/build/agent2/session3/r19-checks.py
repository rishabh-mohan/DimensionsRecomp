# r19-checks.py - M10 ACCEPT-IF C2/C3/C4 post-build checks for devoff4b-r19 (read-only).
import glob, hashlib, os, re, struct, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
T = os.path.join(A2, 's33', 'r19')
BASE = os.path.join(A2, 'devoff4b-bin')
NB = os.path.join(A2, 'devoff4b-r19-bin')
SHARED = os.path.join(A2, 'snap1-sdk', 'install', 'bin', 'rexgpu-xenos.dll')
fails = []


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()


def check(what, ok, detail=''):
    print('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''))
    if not ok:
        fails.append(what)


def exports(p):
    d = open(p, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    rva = struct.unpack_from('<I', d, opt + 112)[0]  # PE32+ export dir
    secs = []
    for i in range(nsec):
        s = pe + 24 + optsz + 40 * i
        vs, va, rs, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((va, max(vs, rs), ra))

    def off(r):
        for va, sz, ra in secs:
            if va <= r < va + sz:
                return r - va + ra
        raise ValueError(hex(r))
    e = off(rva)
    n = struct.unpack_from('<I', d, e + 24)[0]
    names = off(struct.unpack_from('<I', d, e + 32)[0])
    out = []
    for i in range(n):
        q = off(struct.unpack_from('<I', d, names + 4 * i)[0])
        out.append(d[q:d.index(b'\0', q)].decode())
    return out


print('# r19-checks %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
# C2: overlay -I ahead of the snap1 include on all 9 commands
ov = os.path.join(T, 'sdk', 'include').lower().replace('/', '\\')
sn = os.path.join(A2, 'snap1', 'DimensionsRecomp', 'rexglue-sdk', 'include').lower().replace('/', '\\')
txt = open(os.path.join(T, 'log-on', 'recompile-commands.txt'), encoding='utf-8', errors='replace').read()
cmds = [ln for ln in txt.splitlines() if 'clang' in ln.lower() and ' -c ' in ln]
print('C2: %d compile command lines in log-on/recompile-commands.txt' % len(cmds))
nok = 0
for c in cmds:
    lc = c.lower().replace('/', '\\')
    i, j = lc.find(ov), lc.find(sn)
    ok = i >= 0 and j >= 0 and i < j
    nok += ok
    print('  %s overlay@%d snap1@%d %s' % ('ok ' if ok else 'BAD', i, j, (re.findall(r'\S+\.obj', c) or ['?'])[-1][-60:]))
check('C2 overlay -I ahead of snap1 include on all 9 commands', len(cmds) == 9 and nok == 9, '%d/%d' % (nok, len(cmds)))
mdmf = sum(1 for c in cmds if ' -MD' in c or ' -MMD' in c)
print('C2 SHOULD -MD/-MF depfiles: %d/%d commands carry -MD (recompile.py strips/refuses depfile flags; not done)' % (mdmf, len(cmds)))
# C3: PCH reused unchanged, no PCH warning/error
pch_hits = []
for lg in sorted(glob.glob(os.path.join(T, 'log-on', '*.log')) + glob.glob(os.path.join(T, 'log-ctl', '*.log'))):
    for ln in open(lg, encoding='utf-8', errors='replace'):
        if re.search(r'pch|precompiled', ln, re.I) and re.search(r'warning|error|fatal', ln, re.I):
            pch_hits.append('%s: %s' % (os.path.basename(lg), ln.strip()[:200]))
for h in pch_hits[:10]:
    print('  ' + h)
check('C3 no PCH warning/error in log-on/log-ctl', not pch_hits, '%d hit(s)' % len(pch_hits))
pchs = glob.glob(os.path.join(A2, 'snap1-sdk', 'src', 'graphics', 'CMakeFiles', 'rexgpu-xenos.dir', 'Release',
                              'cmake_pch*.pch'))  # the -include-pch path in every command
check('C3 every ON command uses that PCH', bool(pchs) and all(
    pchs[0].replace('\\', '/').lower() in c.replace('\\', '/').lower() for c in cmds))
for p in pchs:
    st = os.stat(p)
    print('  PCH %s %d B mtime %s sha256 %s' % (os.path.relpath(p, R), st.st_size,
                                               time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)), sha(p)))
check('C3 PCH file found and older than tonight (not rebuilt)', bool(pchs) and all(
    os.stat(p).st_mtime < time.mktime(time.strptime('2026-11-25 02:30', '%Y-%m-%d %H:%M')) for p in pchs))
# C4
for fn in ('legodimensions.exe', 'rexruntime.dll', 'TracyClient.dll'):
    a, b = sha(os.path.join(NB, fn)), sha(os.path.join(BASE, fn))
    check('C4 %s == devoff4b-bin' % fn, a == b, a)
check('C4 shared DLL still E3CB99CF', sha(SHARED).startswith('E3CB99CF'), sha(SHARED))
eo, eb = exports(os.path.join(NB, 'rexgpu-xenos.dll')), exports(os.path.join(BASE, 'rexgpu-xenos.dll'))
print('  exports r19: %s' % eo)
print('  exports devoff4b: %s' % eb)
check('C4 ON DLL exports the same 4 names', eo == eb and len(eo) == 4)
print('RESULT: %s' % ('PASS' if not fails else 'FAIL (%s)' % '; '.join(fails)))
sys.exit(1 if fails else 0)
