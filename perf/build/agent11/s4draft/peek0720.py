# Agent 11, task #25 pass B: third read-only peek (07:20).
import re, sys, os, glob, hashlib, time
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

def lines_of(path):
    b = open(path, 'rb').read()
    t = b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', errors='replace')
    return re.split(r'\r\n|\n|\r', t)

def grep(path, pats, maxhits=20, width=700, rng=None):
    print('=' * 8, path)
    if not os.path.exists(path):
        print('MISSING'); return
    L = lines_of(path)
    n = 0
    for i, s in enumerate(L):
        if rng and not (rng[0] <= i + 1 <= rng[1]):
            continue
        if any(re.search(p, s) for p in pats):
            print('M%d: %s' % (i + 1, s[:width])); n += 1
            if n >= maxhits:
                print('...more'); break

def ls(pat):
    print('=' * 8, 'ls', pat)
    for p in sorted(glob.glob(pat)):
        st = os.stat(p)
        print('  %-70s %9d %s' % (p.replace('\\', '/'), st.st_size, time.strftime('%H:%M:%S', time.localtime(st.st_mtime))))

L = lines_of('perf-notes/S4-DRAFT.md')
print('S4 lines', len(L))
for i in range(4, 27):
    s = L[i]
    print('S4 L%d [%d]: %s' % (i + 1, len(s), s[:1200]))
grep('build/agent7/readout/pool-W5b.md', [r'.'], 20, 400, (84, 100))
ls('build/agent3/runs/*rpb0*'); ls('build/agent3/runs/*rpm4*'); ls('build/agent3/runs/*f10*')
ls('build/agent7/s4-t1/*')
grep('build/agent7/s4-t1/README.md', [r'ABOVE_NORMAL|EcoQoS|=3|= 3|value 3'], 10)
grep('build/agent7/s4-r1s2/README.md', [r'320|P10|P1-P10|files|kInitOnly|rate'], 12)
grep('build/agent6/s33-popin/DESIGN.md', [r'kRequiresRestart|\+105|4 files|counter|#34|apply --check'], 12, 500)
grep('build/agent6/s33-popin/CHECK.txt', [r'apply|5350b1d|files changed|insertion'], 10, 400)
grep('build/agent4/HANDOFF.md', [r'[Ss]tep 5|step 4|announce|native4b'], 12, 500)
