"""Pick N vertex shaders from character packs (likely skinned) out of the 32 shards into <out>/shard00
for a 1-CPU end-to-end test of gradient_compiler -> make_float_blend_inputs -> build_float_blend_indices_bank.
Usage: pick_vs_test.py <shards-dir> <corpus.tsv> <out-shards-dir> [--count 24]"""
import argparse, csv, os, shutil
ap = argparse.ArgumentParser()
ap.add_argument('shards'); ap.add_argument('corpus'); ap.add_argument('out'); ap.add_argument('--count', type=int, default=24)
a = ap.parse_args()
flags = {}
with open(a.corpus, newline='') as fh:
    for r in csv.DictReader(fh, delimiter='\t'):
        flags[r['digest']] = int(r['flags'], 16)
rows = []
with open(os.path.join(a.shards, 'manifest.tsv'), newline='') as fh:
    for r in csv.DictReader(fh, delimiter='\t'):
        if (flags.get(r['digest'], 0) & 0xFF) == 1 and '\\chars\\' in r['path'].lower():
            rows.append(r)
rows.sort(key=lambda r: r['digest'])
pick = rows[:a.count]
d = os.path.join(a.out, 'shard00'); os.makedirs(d, exist_ok=False)
for r in pick:
    shutil.copyfile(os.path.join(a.shards, r['shard'], r['file']), os.path.join(d, r['file']))
print(f'candidates={len(rows)} picked={len(pick)} -> {d}')
