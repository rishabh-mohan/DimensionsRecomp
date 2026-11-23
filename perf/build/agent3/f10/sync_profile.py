# sync_profile.py - memexport syncs per frame vs route position (f10 caveat check)
# usage: python -B sync_profile.py label=<run dir> [label=<run dir> ...]
# For each run: joins game*.log slow-frame lines, maps wall time to route t_s via
# run.json started (input t_s ~ run start), prints syncs per 10 s bucket relative
# to story-load, top-10 sync frames, and totals per route segment.
import json, os, re, sys, glob, datetime

RX = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\].*?slow frame #(\d+): ([\d.]+) ms \| gpu-thread idle ([\d.]+) \| host-gpu wait ([\d.]+) \((\d+)x\).*?memexport syncs (\d+)')

def marks(run):
    out = {}
    p = os.path.join(run, 'input.csv')
    if not os.path.exists(p):
        return out
    with open(p, encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            c = line.rstrip('\n').split(',')
            if len(c) > 3 and c[2] == 'mark':
                out[c[3]] = float(c[0])
    return out

def started(run):
    with open(os.path.join(run, 'run.json'), encoding='utf-8-sig') as f:
        j = json.load(f)
    return float(j['started_epoch_s'])

def logs(run):
    fs = glob.glob(os.path.join(run, '**', 'game*.log'), recursive=True)
    def key(p):
        m = re.search(r'game\.(\d+)\.log$', p)
        return -int(m.group(1)) if m else 0
    return sorted(fs, key=key)  # oldest rotation first, game.log last

def frames(run):
    seen = {}
    for p in logs(run):
        with open(p, encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'slow frame #' not in line:
                    continue
                m = RX.search(line)
                if not m:
                    continue
                ts = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f').timestamp()
                n = int(m.group(2))
                seen[n] = (ts, n, float(m.group(3)), float(m.group(4)), float(m.group(5)), int(m.group(6)), int(m.group(7)))
    return [seen[k] for k in sorted(seen)]

def main():
    for arg in sys.argv[1:]:
        label, run = arg.split('=', 1)
        mk = marks(run)
        t0 = started(run)
        fr = frames(run)
        sl = mk.get('story-load')
        print('=== %s  frames %d  story-load t_s %s  vortex %s  end %s' % (label, len(fr), sl, mk.get('vortex'), mk.get('end')))
        if not fr or sl is None:
            continue
        # segments
        segs = [('pre-story', -1e9, sl), ('story..+60', sl, sl + 60), ('+60..vortex', sl + 60, mk.get('vortex', 1e9)), ('vortex..end', mk.get('vortex', 1e9), 1e9)]
        for name, a, b in segs:
            sel = [x for x in fr if a <= x[0] - t0 < b]
            if not sel:
                print('  %-12s frames 0' % name); continue
            syn = sum(x[6] for x in sel); w = sum(x[4] for x in sel); nw = sum(x[5] for x in sel)
            print('  %-12s frames %6d  syncs %7d  max/frame %5d  host-gpu wait %8.1f ms over %6d waits  frames>=100ms %4d  >=1s %2d  max %.1f' % (
                name, len(sel), syn, max(x[6] for x in sel), w, nw, sum(1 for x in sel if x[2] >= 100), sum(1 for x in sel if x[2] >= 1000), max(x[2] for x in sel)))
        # 10 s buckets from story-load -20 to +80
        print('  buckets rel story-load (s): syncs / frames / max syncs per frame / max frame ms')
        row = []
        for k in range(-2, 9):
            a = sl + 10 * k; b = a + 10
            sel = [x for x in fr if a <= x[0] - t0 < b]
            if sel:
                row.append('%+4d:%d/%d/%d/%.0f' % (10 * k, sum(x[6] for x in sel), len(sel), max(x[6] for x in sel), max(x[2] for x in sel)))
            else:
                row.append('%+4d:-' % (10 * k))
        print('   ' + '  '.join(row))
        top = sorted(fr, key=lambda x: -x[6])[:8]
        print('  top sync frames: ' + '; '.join('#%d %+.1fs %d syncs %.1fms wait %.1f/%dx' % (x[1], x[0] - t0 - sl, x[6], x[2], x[4], x[5]) for x in top))
        topf = sorted(fr, key=lambda x: -x[2])[:5]
        print('  top long frames: ' + '; '.join('#%d %+.1fs %.1fms syncs %d wait %.1f/%dx idle %.1f' % (x[1], x[0] - t0 - sl, x[2], x[6], x[4], x[5], x[3]) for x in topf))

if __name__ == '__main__':
    main()
