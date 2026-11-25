# combo-check.py (M2): read-only on the repos and bins. In a scratch dir (commit-plan/work, outside any repo via
# GIT_CEILING_DIRECTORIES) copy the live files each patch touches, apply the patches with
# `git -c core.autocrlf=false apply`, and compare the results with what the bins were built from:
#   - FINAL (sdk + super) alone           vs final/work/new (the devfinal/nativefinal overlay sources, prep after-hashes)
#   - each s33 candidate alone            vs devoff4b-s33-bin MANIFEST "after" hashes (the bin the #33 rows ran on)
#   - FINAL + s33 combined (one tree)     per-file: which bin's source each file equals
import hashlib, os, re, shutil, subprocess, sys

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.abspath(os.path.join(H, '..', '..', '..', '..'))
A2 = os.path.join(R, 'build', 'agent2')
LIVE_SDK = os.path.join(R, 'DimensionsRecomp', 'rexglue-sdk')
LIVE_SUP = os.path.join(R, 'DimensionsRecomp')
W = os.path.join(H, 'work')
PATCHES = {
    'final-sdk': os.path.join(H, 'final-sdk.diff'),
    'final-super': os.path.join(H, 'final-super.diff'),
    's33-no5 (M2, 4061ED2D)': os.path.join(A2, 'session3', 's33-popin-no5.patch'),
    's33-nohunk5 (M6, 57CFA8AD)': os.path.join(R, 'build', 'agent6', 's33-popin', 's33-popin-nohunk5.patch'),
}
sha = lambda b: hashlib.sha256(b).hexdigest().upper()


def touched(p):
    return [m.decode() for m in re.findall(rb'(?m)^\+\+\+ b/(\S+)', open(p, 'rb').read())]


def tree(name, live, patches):
    d = os.path.join(W, name)
    if os.path.exists(d):
        shutil.rmtree(d)
    for p in patches:
        for rel in touched(p):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(live, rel), os.path.join(d, rel))
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=W)
    r = subprocess.run(['git', '-c', 'core.autocrlf=false', 'apply', '-v'] + patches, cwd=d, env=env,
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print('[%s] apply %s: exit %d %s' % (name, ' + '.join(os.path.basename(p) for p in patches), r.returncode,
                                        '' if ok else r.stderr.strip()))
    return d, ok


for k, p in PATCHES.items():
    print('patch %-28s sha256 %s  files %s' % (k, sha(open(p, 'rb').read())[:16], touched(p)))

# expected sources
final_new = os.path.join(A2, 'final', 'work', 'new')  # prep-final's after copies, by repo-ish path
man = open(os.path.join(A2, 'devoff4b-s33-bin', 'MANIFEST.txt'), encoding='utf-8', errors='replace').read()
s33_after = {m.group(1): m.group(2) for m in re.finditer(r'# prep: after\s+(\S+) ([0-9A-F]{64})', man)}
print('devoff4b-s33-bin MANIFEST after-hashes:', {k: v[:16] for k, v in s33_after.items()})


def find_new(rel_sdk_or_sup):
    # final/work/new layout: look for a file whose path ends with the repo-relative path
    for root, _, fs in os.walk(final_new):
        for f in fs:
            full = os.path.join(root, f)
            if full.replace('\\', '/').endswith('/' + rel_sdk_or_sup):
                return full
    return None


rows = []
# 1. FINAL alone
d1, ok1 = tree('final-sdk', LIVE_SDK, [PATCHES['final-sdk']])
d2, ok2 = tree('final-super', LIVE_SUP, [PATCHES['final-super']])
for d, p in ((d1, PATCHES['final-sdk']), (d2, PATCHES['final-super'])):
    for rel in touched(p):
        got = sha(open(os.path.join(d, rel), 'rb').read())
        ref = find_new(rel)
        exp = sha(open(ref, 'rb').read()) if ref else None
        print('  FINAL %-46s %s %s devfinal/nativefinal source (%s)' % (rel, got[:16], '==' if got == exp else '!=',
                                                                       exp[:16] if exp else 'not found'))
# 2. each s33 candidate alone
for k in ('s33-no5 (M2, 4061ED2D)', 's33-nohunk5 (M6, 57CFA8AD)'):
    tag = 's33-' + k.split()[0].split('-')[1]
    d, ok = tree(tag, LIVE_SDK, [PATCHES[k]])
    for rel in touched(PATCHES[k]):
        got = sha(open(os.path.join(d, rel), 'rb').read())
        exp = s33_after.get(rel)
        print('  %s %-46s %s %s devoff4b-s33 source (%s)' % (k.split()[0], rel, got[:16], '==' if got == exp else '!=',
                                                            exp[:16] if exp else 'n/a'))
# 3. FINAL + s33 combined, SDK tree (super part is unaffected by s33)
for k in ('s33-no5 (M2, 4061ED2D)', 's33-nohunk5 (M6, 57CFA8AD)'):
    tag = 'combo-' + k.split()[0].split('-')[1]
    d, ok = tree(tag, LIVE_SDK, [PATCHES['final-sdk'], PATCHES[k]])
    n_f = n_s = bad = 0
    for rel in touched(PATCHES['final-sdk']):
        got = sha(open(os.path.join(d, rel), 'rb').read())
        ref = find_new(rel)
        if ref and got == sha(open(ref, 'rb').read()):
            n_f += 1
        else:
            bad += 1
            print('  combo MISMATCH final file', rel)
    for rel in touched(PATCHES[k]):
        got = sha(open(os.path.join(d, rel), 'rb').read())
        if got == s33_after.get(rel):
            n_s += 1
        else:
            bad += 1
            print('  combo %s file %s %s != devoff4b-s33 source' % (k.split()[0], rel, got[:16]))
    print('  combo %s: %d final files == devfinal source, %d s33 files == devoff4b-s33 source, %d mismatch'
          % (k.split()[0], n_f, n_s, bad))
