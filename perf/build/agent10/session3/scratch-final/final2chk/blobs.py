import hashlib, os, subprocess, sys, re
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
SUP = os.path.join(R, 'DimensionsRecomp'); SDK = os.path.join(SUP, 'rexglue-sdk')
SNAP = os.path.join(R, 'build', 'agent2', 'snap1', 'DimensionsRecomp')
src = open(os.path.join(R, 'build', 'agent2', 'final2', 'prep-final2.py'), encoding='utf-8').read()
pairs = re.findall(r"'([^']+)': \('([0-9A-F]{16})', '([0-9A-F]{16})'\)", src)
pairs += [('rexglue-sdk/include/rex/graphics/d3d12/pipeline_cache.h',) + re.search(r"HDR33: \('([0-9A-F]{16})', '([0-9A-F]{16})'\)", src).groups()]
def g(repo, *a):
    return subprocess.run(['git', '-C', repo] + list(a), capture_output=True)
sdk_c, sup_c = sys.argv[1], sys.argv[2]
print('sdk', g(SDK, 'rev-parse', sdk_c).stdout.decode().strip(), 'super', g(SUP, 'rev-parse', sup_c).stdout.decode().strip())
print('gitlink', g(SUP, 'ls-tree', sup_c, 'rexglue-sdk').stdout.decode().strip())
print('sdk names', sorted(g(SDK, 'diff', '--name-only', '--no-renames', '5350b1d', sdk_c).stdout.decode().split()))
print('super names', sorted(g(SUP, 'diff', '--name-only', '--no-renames', 'c9e215f', sup_c).stdout.decode().split()))
print('n pairs', len(pairs))
for f, bh, ah in sorted(pairs):
    repo, c, p = (SDK, sdk_c, f[len('rexglue-sdk/'):]) if f.startswith('rexglue-sdk/') else (SUP, sup_c, f)
    o = g(repo, 'cat-file', 'blob', '%s:%s' % (c, p)).stdout
    sb = open(os.path.join(SNAP, f), 'rb').read()
    crlf = b'\r\n' in sb
    form = o.replace(b'\n', b'\r\n') if crlf else o
    h = hashlib.sha256(form).hexdigest().upper(); hb = hashlib.sha256(sb).hexdigest().upper()
    print('%-62s blobCR=%d base=%s blob %s form %s after_ok=%s before_ok=%s' % (
        f, o.count(b'\r'), 'CRLF' if crlf else 'LF', hashlib.sha256(o).hexdigest().upper()[:8], h[:8], h.startswith(ah), hb.startswith(bh)))
for f in ('rexglue-sdk/src/graphics/frame_stats.h', 'rexglue-sdk/src/graphics/d3d12/command_processor.cpp', 'rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp'):
    o = g(SDK, 'cat-file', 'blob', '%s:%s' % (sdk_c, f[len('rexglue-sdk/'):])).stdout
    for nd in (b'dropped draws {} | forced pipeline waits {:.1f} ({}x)', b'd3d12_pipeline_creation_no_wait', b'REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false,'):
        if nd in o:
            print('needle in', f, nd.decode(), o.count(nd))
