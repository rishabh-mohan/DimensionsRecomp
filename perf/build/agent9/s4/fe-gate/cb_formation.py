# #41 open item: who forms the callback pointers 0x82A9F718 / 0x82A9F5C8 (lis rS,-32086 ; addi rD,rS,-2280/-2616)?
# Input: findstr-cb.txt (A tree = baseline, same tree as 41-step1.txt). Read-only. Output: 41-cb-formation.txt
import re, os, collections
ROOT = r'<workspace>'
SRC = os.path.join(ROOT, r'build\agent9\s4\fe-gate\findstr-cb.txt')
OUT = os.path.join(ROOT, r'build\agent9\s4\fe-gate\41-cb-formation.txt')
TARGET = {-2280: 0x82A9F718, -2616: 0x82A9F5C8}
hit_re = re.compile(r'^(.*legodimensions_recomp\.(\d+)\.cpp):(\d+):\t// addi (r\d+),(r\d+),(-2280|-2616)\s*$')
ins_re = re.compile(r'^\t// ([a-z][a-z0-9.]*)\s*(.*?)\s*$')
lab_re = re.compile(r'^(loc_[0-9A-F]{8}):')
fn_re = re.compile(r'^(?!loc_)\S[^;]*(sub_[0-9A-F]{8})\b[^;]*$')
NONDEF = ('st', 'cmp', 'b', 'tw', 'td', 'dcb', 'mt', 'sync', 'isync', 'eieio', 'db16cyc', 'cct', 'nop', 'icbi')
hits = collections.defaultdict(list)
for ln in open(SRC, encoding='utf-8', errors='replace'):
    m = hit_re.match(ln.rstrip('\r\n'))
    if m:
        hits[m.group(1)].append((int(m.group(3)), m.group(4), m.group(5), int(m.group(6))))
out = ['# 41-cb-formation (A tree = baseline); lis rS,-32086 + addi rD,rS,-2280 -> 0x82A9F718, -2616 -> 0x82A9F5C8']
nmatch = collections.Counter()
installers = collections.defaultdict(list)
def tun(p):
    return int(re.search(r'\.(\d+)\.cpp$', p).group(1))
for path in sorted(hits, key=tun):
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    with open(full, encoding='utf-8', errors='replace') as f:
        lines = f.read().split('\n')
    tu = tun(path)
    for (lno, rd, rs, imm) in hits[path]:
        i = lno - 1
        fn = '?'
        for k in range(i, -1, -1):
            mm = fn_re.match(lines[k].rstrip('\r'))
            if mm:
                fn = '%s (L%d)' % (mm.group(1), k + 1)
                break
        definer = None
        crossed = False
        for k in range(i - 1, max(-1, i - 400), -1):
            s = lines[k].rstrip('\r')
            if lab_re.match(s):
                crossed = True
                continue
            mm = ins_re.match(s)
            if not mm:
                continue
            op, args = mm.group(1), mm.group(2)
            if op.startswith(NONDEF):
                continue
            if args.split(',')[0].strip() == rs:
                definer = (k + 1, op + ' ' + args)
                break
        ok = definer is not None and re.match(r'^lis %s,-32086$' % rs, definer[1]) is not None
        tgt = TARGET[imm]
        if ok:
            nmatch[tgt] += 1
            installers[tgt].append('TU%d:%d %s' % (tu, lno, fn))
        out.append('TU%d:%d addi %s,%s,%d in %s: definer %s%s -> %s' % (
            tu, lno, rd, rs, imm, fn, ('L%d %s' % definer) if definer else 'none within 400 lines',
            ' (crossed label)' if crossed else '', ('MATCH 0x%08X' % tgt) if ok else 'no'))
        if ok:
            n = 0
            for k in range(i + 1, min(len(lines), i + 600)):
                s = lines[k].rstrip('\r')
                mm = ins_re.match(s)
                if mm:
                    out.append('    L%d: %s %s' % (k + 1, mm.group(1), mm.group(2)))
                    n += 1
                    if n >= 12:
                        break
                elif lab_re.match(s):
                    out.append('    L%d: %s' % (k + 1, s))
out.append('SUMMARY hits examined=%d; matches: %s' % (sum(len(v) for v in hits.values()),
           ', '.join('0x%08X=%d' % (k, v) for k, v in sorted(nmatch.items())) or 'none'))
for tgt in sorted(installers):
    out.append('FORMS 0x%08X: %s' % (tgt, '; '.join(installers[tgt])))
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out) + '\n')
print('\n'.join(l for l in out if l.startswith(('SUMMARY', 'FORMS'))))
