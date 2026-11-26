"""Static test of the rt_smoke_post.py pixel shot gate (pick_shot / client_nonblack) on scratch kit-shot dirs."""
import os, shutil, sys
sys.dont_write_bytecode = True
R = r'<workspace>\build\agent2\s5'
sys.path.insert(0, R)
import rt_smoke_post as P  # noqa: E402

BLACK = os.path.join(R, r'rt-smoke\runs\20261126-013637-s5rt-f3a\kit-shots\shot-060s.png')  # native PrintWindow, black
GOOD = os.path.join(R, r'nops-smoke\runs\20261125-201249-s5nops-t1\kit-shots\shot-120s.png')  # real frame
DARK = os.path.join(R, r'nops-smoke\runs\20261125-201719-s5nops-t2\kit-shots\shot-060s.png')  # dark real frame
TT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tt-shot')
if os.path.exists(TT):
    shutil.rmtree(TT)
res = []


def case(name, files, want_pick):
    rd = os.path.join(TT, name)
    os.makedirs(os.path.join(rd, 'kit-shots'))
    for dst, src in files.items():
        shutil.copy2(src, os.path.join(rd, 'kit-shots', dst))
    p, info = P.pick_shot(rd, 60)
    got = os.path.basename(p) if p else None
    ok = got == want_pick
    res.append(ok)
    print('%s %-28s pick %-22s want %-22s %s' % ('PASS' if ok else 'FAIL', name, got, want_pick, info))


case('black only', {'shot-060s.png': BLACK}, None)
case('black + screen copy', {'shot-060s.png': BLACK, 'shot-060s-screen.png': GOOD}, 'shot-060s-screen.png')
case('black + black screen', {'shot-060s.png': BLACK, 'shot-060s-screen.png': BLACK}, None)
case('good printwindow', {'shot-060s.png': GOOD, 'shot-060s-screen.png': BLACK}, 'shot-060s.png')
case('dark real printwindow', {'shot-060s.png': DARK}, 'shot-060s.png')
case('missing', {}, None)
print('black %.2f%% good %.2f%% dark %.2f%% (MIN_NONBLACK %.0f%%)' % tuple(
    [100 * P.client_nonblack(x) for x in (BLACK, GOOD, DARK)] + [100 * P.MIN_NONBLACK]))
shutil.rmtree(TT)
print('SHOT GATE TEST', 'ALL PASS' if all(res) else 'FAIL', '(%d cases)' % len(res))
sys.exit(0 if all(res) else 1)
