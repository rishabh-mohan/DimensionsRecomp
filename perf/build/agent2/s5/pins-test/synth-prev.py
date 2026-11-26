# Synthetic test of nops_smoke_post.py's S1 parser and N2/N3 gates on a fake run dir (no game).
import os, sys, json, shutil, time, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('post', os.path.join(HERE, '..', '..', 'nops_smoke_post.py'))
post = importlib.util.module_from_spec(spec); spec.loader.exec_module(post)
rd = os.path.join(HERE, 'fake-run')
shutil.rmtree(rd, ignore_errors=True)
os.makedirs(os.path.join(rd, 'user', 'cache', 'shaders', 'shareable'))
os.makedirs(os.path.join(rd, 'kit-shots'))
t0 = time.time() - 10
open(os.path.join(rd, 'user', 'cache', 'shaders', 'shareable', 'x.xsh'), 'wb').write(b'x')
J = dict(seed_xenos=None, user_data_root=os.path.join(rd, 'user'), started_epoch_s=t0)
with open(os.path.join(rd, 'kit-shots', 'shots.txt'), 'w') as f:
    for s in post.SHOT_TIMES:
        f.write('shot %d s (at %d.1 s) pid 1: printwindow -> %s\\shot.png\n' % (s, s, rd))
L = ("[gpu] d3d12_occlusion_queries (first): frame=5000 zpd=1 zpd_no_host=0 begun=1 resolved=0 fallback=0 disabled=0 "
     "reason='' ended_by_submission=0 draws_in_query=0 dropped_in_query_ps=0 dropped_in_query_no_ps=0")
L2 = ("[gpu] d3d12_occlusion_queries (disabled): frame=5001 zpd=2 zpd_no_host=0 begun=1 resolved=0 fallback=1 disabled=1 "
      "reason='end without an active query' ended_by_submission=1 draws_in_query=7 dropped_in_query_ps=1 dropped_in_query_no_ps=3")
L3 = L2.replace('(disabled)', '(shutdown)').replace('zpd=2', 'zpd=9').replace('zpd_no_host=0', 'zpd_no_host=7')
post.n2_n3_gates('T2', rd, J, True)
r = post.zpd_report('T2', [L, 'noise', L2, L3], True)
assert r['zpd'] == 9 and r['zpd_no_host'] == 7 and r['dropped_in_query_no_ps'] == 3 and r['reason'] == 'end without an active query', r
assert r['s1'].startswith('S1 CONFIRMED') and 'HEAD behaviour' in r['s1'], r['s1']
print('fails', post.fails)
assert not post.fails
# Z5: valid 0 (late disable, mostly host queries), invalid 0 (early disable), no ZPD, Z4 missing shutdown line
Z = ("[gpu] d3d12_occlusion_queries ({w}): frame=1 zpd={z} zpd_no_host={nh} begun={b} resolved={r} fallback=0 "
     "disabled={d} reason='' ended_by_submission=0 draws_in_query=5 dropped_in_query_ps=0 dropped_in_query_no_ps=0")
z = lambda w, zz, nh, b, rr, d: Z.format(w=w, z=zz, nh=nh, b=b, r=rr, d=d)
r = post.zpd_report('T2', [z('first', 1, 0, 1, 0, 0), z('disabled', 80, 0, 40, 39, 1), z('shutdown', 100, 20, 40, 39, 1)], True)
assert r['s1'].startswith('valid 0'), r['s1']
r = post.zpd_report('T2', [z('first', 1, 0, 1, 0, 0), z('disabled', 4, 0, 2, 1, 1), z('shutdown', 100, 96, 2, 1, 1)], True)
assert r['s1'].startswith('0 NOT valid'), r['s1']
r = post.zpd_report('T2', [z('shutdown', 0, 0, 0, 0, 0)], True)
assert r['s1'].startswith('no ZPD'), r['s1']
assert not post.fails, post.fails
post.zpd_report('T2', [z('first', 1, 0, 1, 0, 0)], True)
assert len(post.fails) == 1 and 'Z4' in post.fails[0], post.fails
del post.fails[:]
# negative: old storage file, a black shot
os.utime(os.path.join(rd, 'user', 'cache', 'shaders', 'shareable', 'x.xsh'), (t0 - 100, t0 - 100))
with open(os.path.join(rd, 'kit-shots', 'shots.txt'), 'a') as f:
    f.write('shot 200 s (at 200.1 s) pid 1: screen copy (black) -> y\n')
post.n2_n3_gates('N2', rd, J, True)
print('fails', post.fails)
assert len(post.fails) == 2 and 'N2 cold' in post.fails[0] and 'N3' in post.fails[1], post.fails
shutil.rmtree(rd, ignore_errors=True)
print('SYNTH OK')
