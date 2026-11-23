# Rewrites the git diff --no-index header paths so the patch applies inside the
# DimensionsRecomp repo: git -C DimensionsRecomp apply ../bench/agent6/draw-async.patch
src = r'build/agent6/draw_async/raw-crlf.patch'
dst = r'bench/agent6/draw-async.patch'
d = open(src, 'rb').read()
old_a = b'a/build/agent6/draw_async/draw.orig.cpp'
old_b = b'b/build/agent6/draw_async/draw.cpp'
new_a = b'a/rexlego/src/gpu_native/draw.cpp'
new_b = b'b/rexlego/src/gpu_native/draw.cpp'
out = []
in_header = True
for ln in d.split(b'\n'):
    if in_header:
        if ln.startswith(b'@@'):
            in_header = False
        else:
            ln = ln.replace(old_a, new_a).replace(old_b, new_b)
    out.append(ln)
r = b'\n'.join(out)
assert r.count(new_a) == 2 and r.count(new_b) == 2, (r.count(new_a), r.count(new_b))
open(dst, 'wb').write(r)
print('patch bytes', len(r), 'lines', r.count(b'\n'), 'crlf', r.count(b'\r\n'),
      'hunks', r.count(b'\n@@ '), 'plus', sum(1 for l in r.split(b'\n') if l.startswith(b'+') and not l.startswith(b'+++')),
      'minus', sum(1 for l in r.split(b'\n') if l.startswith(b'-') and not l.startswith(b'---')))
