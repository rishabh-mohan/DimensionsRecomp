"""Independent check: are all dropped-draw frames miss frames (new > 0)?
usage: s33_dropmiss.py <run_dir> [<run_dir> ...]"""
import re, sys, glob, os
RX = re.compile(r'^\[(\S+ \S+)\].*slow frame #(\d+): ([\d.]+) ms .*?pipeline create [\d.]+ \(\d+x\), new (\d+) .*dropped draws (\d+)')
for rd in sys.argv[1:]:
    fr = {}
    for p in sorted(glob.glob(os.path.join(rd, 'game*.log'))):
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                m = RX.match(ln)
                if m:
                    fr[int(m.group(2))] = (float(m.group(3)), int(m.group(4)), int(m.group(5)))
    drops = {k: v for k, v in fr.items() if v[2] > 0}
    nonmiss = [k for k, v in drops.items() if v[1] == 0]
    misses = sum(v[1] for v in fr.values())
    missfr = [k for k, v in fr.items() if v[1] > 0]
    print(f'{os.path.basename(rd)}: frames {len(fr)}; miss frames {len(missfr)} (new sum {misses}); '
          f'drop frames {len(drops)} draws {sum(v[2] for v in drops.values())}; last drop #{max(drops) if drops else "-"}; '
          f'last miss #{max(missfr) if missfr else "-"}; drop frames with new 0: {len(nonmiss)} {sorted(nonmiss)[:10]}')
    big = sorted(drops.items(), key=lambda kv: -kv[1][2])[:5]
    print('   top drop frames (frame: ms, new, dropped):', '; '.join(f'#{k}: {v[0]:.0f}, {v[1]}, {v[2]}' for k, v in big))
