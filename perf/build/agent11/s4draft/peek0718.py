# Agent 11, task #25 pass B: second read-only peek (07:18).
import re, sys, os, glob, hashlib
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

def lines_of(path):
    with open(path, 'rb') as f:
        b = f.read()
    t = b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', errors='replace')
    return re.split(r'\r\n|\n|\r', t)

def grep(path, pats, maxhits=30, width=900, rng=None):
    print('=' * 8, path)
    if not os.path.exists(path):
        print('MISSING'); return
    L = lines_of(path)
    b = open(path, 'rb').read()
    print('size', len(b), 'lines', len(L), 'sha', hashlib.sha256(b).hexdigest()[:16].upper())
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
        import time
        print('  %-70s %9d %s' % (p.replace('\\', '/'), st.st_size, time.strftime('%H:%M:%S', time.localtime(st.st_mtime))))

grep('build/agent7/readout/pool-W5b.md', [r'^\| \*?\*?(B-block )?T-std\*?\*? \| (cores|p99|1 % low|game)', r'cores', r'^\*\*no-slow-d11t', r'^\| \*\*B-block T-std\*\* \| fps'], 40)
grep('build/agent10/t27/r21-s4t1.md', [r'SAFE', r'ACCEPTED', r'F-CA', r'=\s*3|= 3|value 3'], 25, 600)
ls('build/agent7/s4-r1s2/*')
ls('build/agent6/s33-popin/*')
ls('build/agent8/readout/w-followup/*')
ls('build/agent8/readout/w-followup/a7check/*')
ls('build/agent*/HANDOFF.md')
grep('build/agent8/w-followup/PROPOSAL.md', [r'W8a'], 15, 600)
ls('build/agent8/w-followup/matrix-window8a*.json')
ls('build/agent5/scrnsave-fix/install-log.txt')
ls('perf-notes/*.md')
