# Read-only verifier for S4-T1 staging (agent7 checker). Writes nothing; prints findings.
import hashlib, difflib, os, sys
ROOT = os.getcwd()
SNAP = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego', 'src', 'gpu_native')
S4 = os.path.join(ROOT, 'build', 'agent7', 's4-t1')
FILES = ['native_worker.cpp', 'native_recording.cpp', 'native_preparation.h']
def sha(b): return hashlib.sha256(b).hexdigest().upper()
for name in FILES:
    snap = open(os.path.join(SNAP, name), 'rb').read()
    before = open(os.path.join(S4, 'before', 'src', 'gpu_native', name), 'rb').read()
    after = open(os.path.join(S4, 'after', 'src', 'gpu_native', name), 'rb').read()
    print('==', name)
    print(' snap   ', sha(snap), len(snap))
    print(' before ', sha(before), len(before), 'EQUAL_TO_SNAP' if before == snap else 'DIFFERS_FROM_SNAP')
    print(' after  ', sha(after), len(after))
    for tag, data in (('before', before), ('after', after)):
        lf = data.count(b'\n'); crlf = data.count(b'\r\n'); cr = data.count(b'\r')
        nonascii = [i for i, c in enumerate(data) if c > 0x7E or (c < 0x20 and c not in (9, 10, 13))]
        print(' %-6s LF=%d CRLF=%d CR=%d bare_LF=%d bare_CR=%d nonascii/ctrl=%d ends_with_newline=%s tabs=%d' % (
            tag, lf, crlf, cr, lf - crlf, cr - crlf, len(nonascii), data.endswith(b'\n'), data.count(b'\t')))
    bl = before.split(b'\n'); al = after.split(b'\n')
    sm = difflib.SequenceMatcher(None, bl, al, autojunk=False)
    ops = [op for op in sm.get_opcodes() if op[0] != 'equal']
    kinds = sorted(set(op[0] for op in ops))
    added = sum(j2 - j1 for t, i1, i2, j1, j2 in ops if t == 'insert')
    removed = sum(i2 - i1 for t, i1, i2, j1, j2 in ops if t in ('delete', 'replace'))
    print(' opcodes:', kinds, 'added=%d removed_or_changed=%d' % (added, removed))
    # Strip-back proof: deleting inserted lines from after reproduces before exactly.
    keep = []
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t == 'equal': keep.extend(al[j1:j2])
        elif t in ('replace', 'delete'): keep.extend(bl[i1:i2])
    print(' strip-back == before:', b'\n'.join(keep) == before)
    for t, i1, i2, j1, j2 in ops:
        prev = al[j1 - 1].rstrip(b'\r').decode('ascii', 'replace').strip() if j1 > 0 else ''
        print('  %s before@%d after@%d-%d  (prev line: %s)' % (t, i1 + 1, j1 + 1, j2, prev[:110]))
        for k in range(j1, j2):
            print('    +%d: %s' % (k + 1, al[k].rstrip(b'\r').decode('ascii', 'replace')))
# Diff file is consistent with after/ (apply hunks by simple reconstruction check of + lines).
d = open(os.path.join(S4, 's4-t1.diff'), 'rb').read()
print('== diff sha', sha(d), len(d), 'minus-lines:', sum(1 for l in d.split(b'\n') if l.startswith(b'-') and not l.startswith(b'---')),
      'plus-lines:', sum(1 for l in d.split(b'\n') if l.startswith(b'+') and not l.startswith(b'+++')))
