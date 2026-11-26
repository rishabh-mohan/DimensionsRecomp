"""manual_sbs.py - offline FSR1|bilinear side-by-sides from the matched manual capture (M2; no game, local only, S3).
Each --pair LABEL A.png B.png (A = F3A FSR 1, B = F3B bilinear; same zoom region, ideally 1:1 1366 px wide crops)
gives sbs-LABEL.png (A left | B right, 1:1) and sbs-LABEL-crop2x.png (centre third, 2x nearest). Prints sizes, sha256 and
an info-only detail number (mean |2nd difference| of luma; FSR 1 RCAS should come out higher on the same content).
    python -B manual_sbs.py --out DIR --pair 060s A.png B.png [--pair 122s A.png B.png ...]
"""
import argparse, hashlib, os
from PIL import Image, ImageDraw
import numpy as np


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def detail(im):
    g = np.asarray(im.convert('L'), dtype=np.float32)
    return float((np.abs(np.diff(g, n=2, axis=1)).mean() + np.abs(np.diff(g, n=2, axis=0)).mean()) / 2)


def pair(label, pa, pb, out, la='F3A FSR 1', lb='F3B bilinear'):
    A, B = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')
    print('%s: A %s %dx%d sha %s detail %.2f | B %s %dx%d sha %s detail %.2f%s' % (
        label, pa, A.width, A.height, sha(pa)[:16], detail(A), pb, B.width, B.height, sha(pb)[:16], detail(B),
        '' if A.size == B.size else '  WARNING: sizes differ (not the same zoom region)'))
    made = []
    for kind in ('full', 'crop2x'):
        if kind == 'crop2x':
            w, h = min(A.width, B.width) // 3, min(A.height, B.height) // 3
            cut = lambda im: im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width + w) // 2,
                                      (im.height + h) // 2)).resize((2 * w, 2 * h), Image.NEAREST)
            a, b = cut(A), cut(B)
        else:
            a, b = A, B
        gap, top = 8, 22
        c = Image.new('RGB', (a.width + gap + b.width, top + max(a.height, b.height)), (24, 24, 24))
        c.paste(a, (0, top))
        c.paste(b, (a.width + gap, top))
        dr = ImageDraw.Draw(c)
        dr.text((6, 5), '%s  %s%s' % (la, label, '  (centre crop, 2x nearest)' if kind == 'crop2x' else '  (1:1)'), fill=(255, 255, 255))
        dr.text((a.width + gap + 6, 5), '%s  %s' % (lb, label), fill=(255, 255, 255))
        p = os.path.join(out, 'sbs-%s%s.png' % (label, '' if kind == 'full' else '-crop2x'))
        c.save(p, optimize=True)
        made.append(p)
        print('  -> %s (%.2f MB, sha %s)' % (p, os.path.getsize(p) / 1e6, sha(p)[:16]))
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--pair', nargs=3, action='append', metavar=('LABEL', 'A_PNG', 'B_PNG'), required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    made = []
    for label, pa, pb in a.pair:
        made += pair(label, pa, pb, a.out)
    print('total %d PNGs, %.2f MB' % (len(made), sum(os.path.getsize(p) for p in made) / 1e6))


if __name__ == '__main__':
    main()
