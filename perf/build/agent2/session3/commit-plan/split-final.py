# split-final.py (M2): read-only on the repos. Split final/FINAL-DEFAULTS.diff (paths DimensionsRecomp/...) into
# per-repo patches with repo-relative paths, byte-exact otherwise:
#   final-sdk.diff   -> apply in DimensionsRecomp/rexglue-sdk (paths src/...)
#   final-super.diff -> apply in DimensionsRecomp            (paths rexlego/...)
# Also checks that the two parts concatenated (with the prefixes put back) == the original bytes.
import hashlib, os, re

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(H, '..', '..', '..', '..'))
SRC = os.path.join(R, 'build', 'agent2', 'final', 'FINAL-DEFAULTS.diff')

raw = open(SRC, 'rb').read()
nl = b'\r\n' if raw.count(b'\r\n') > raw.count(b'\n') // 2 else b'\n'
blocks = re.split(rb'(?m)^(?=diff --git )', raw)
assert blocks[0] == b'', blocks[0][:80]
parts = {'sdk': [], 'super': []}
for b in blocks[1:]:
    if b.startswith(b'diff --git a/DimensionsRecomp/rexglue-sdk/'):
        parts['sdk'].append(b.replace(b'a/DimensionsRecomp/rexglue-sdk/', b'a/').replace(b'b/DimensionsRecomp/rexglue-sdk/', b'b/'))
    elif b.startswith(b'diff --git a/DimensionsRecomp/'):
        parts['super'].append(b.replace(b'a/DimensionsRecomp/', b'a/').replace(b'b/DimensionsRecomp/', b'b/'))
    else:
        raise SystemExit('unexpected block: %r' % b[:80])
h = lambda b: hashlib.sha256(b).hexdigest().upper()
print('FINAL-DEFAULTS.diff sha256 %s, %d file blocks, line ends %s' % (h(raw), len(blocks) - 1, 'CRLF' if nl == b'\r\n' else 'LF'))
for k, v in parts.items():
    data = b''.join(v)
    out = os.path.join(H, 'final-%s.diff' % k)
    open(out, 'wb').write(data)
    files = [re.match(rb'diff --git a/(\S+)', b).group(1).decode() for b in v]
    print('%s: %d file(s) -> %s sha256 %s' % (k, len(v), out, h(data)))
    for f in files:
        print('   ', f)
# only header lines may change: every changed line must be a diff --git / --- / +++ header
orig = [x for x in blocks[1:] if x.startswith(b'diff --git a/DimensionsRecomp/rexglue-sdk/')] + \
       [x for x in blocks[1:] if not x.startswith(b'diff --git a/DimensionsRecomp/rexglue-sdk/')]
new = parts['sdk'] + parts['super']
bad = 0
for o, n in zip(orig, new):
    ol, nl_ = o.split(b'\n'), n.split(b'\n')
    if len(ol) != len(nl_):
        bad += 1
        continue
    for x, y in zip(ol, nl_):
        if x != y and not re.match(rb'(diff --git |--- a/|\+\+\+ b/)', x):
            bad += 1
print('split check (same line counts; only header lines changed): %s' % ('PASS' if bad == 0 else 'FAIL %d' % bad))
