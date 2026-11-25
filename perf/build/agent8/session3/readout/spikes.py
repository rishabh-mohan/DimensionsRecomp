import csv, json, os, sys
rd = sys.argv[1]
fj = json.load(open(os.path.join(rd, 'frames.json'), encoding='utf-8-sig'))
w = fj['window']; first, n = w['first_row'], w['rows']
sc = float(fj.get('scale_to_us') or 1) / 1000
t = 0.0; hits = []
with open(fj['file'], encoding='utf-8-sig', newline='') as f:
    r = csv.reader(f); h = next(r); ci = h.index(fj['column'])
    for i, row in enumerate(r):
        if i < first: continue
        if i >= first + n: break
        v = float(row[ci]) * sc; t += v / 1000
        if v > 8: hits.append((round(t, 2), round(v, 2)))
print(len(hits), hits[:40])
s = json.load(open(os.path.join(rd, 'sys.json'), encoding='utf-8-sig'))
print({k: s['window'].get(k) for k in ('cpu_util_mean', 'eff_mhz_mean', 'eff_mhz_min', 'input_events', 'fg_game_share')}, s.get('flags'))
