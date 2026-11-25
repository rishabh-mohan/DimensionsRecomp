"""Shared #33 row-3 log parsing (M3). Reads a harness run dir's game*.log (rotated: game.2.log oldest, game.log newest).

Slow-frame lines (slow_frame_log_ms=1 logs every frame):
  [2026-11-25 10:04:00.847] [info] [gpu] [t21676] slow frame #12222: 374.7 ms | ... | pipeline create 12.5 (3x), new 9 | ...
  ... | dropped draws 17 | forced pipeline waits 0.0 (0x)
'new N' = pipelines created in that frame (cold misses); 'dropped draws K' = draws skipped because their pipeline was not
ready (only > 0 with d3d12_pipeline_creation_no_wait=true). 'resolve after drop:' lines exist only with the (d) bin/cvar.
FF (first frame) = the timestamp of the first slow-frame line (same definition live and after the run).
"""
import datetime, glob, os, re

SLOW = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\][^\n]*?slow frame #(\d+): ([\d.]+) ms'
                  r'[^\n]*?, new (\d+)[^\n]*?dropped draws (\d+)')
RAD = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\][^\n]*resolve after drop:')
TS = '%Y-%m-%d %H:%M:%S.%f'


def log_files(run):
    def key(p):
        m = re.search(r'game\.(\d+)\.log$', p)
        return -int(m.group(1)) if m else 0
    return sorted(glob.glob(os.path.join(run, 'game*.log')), key=key)


def parse(run):
    """-> dict(frames=[(t, frame, ms, new, dropped)], rad=[t], ff=datetime|None, files=[names])."""
    frames, rad = [], []
    files = log_files(run)
    for p in files:
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                if 'slow frame #' in ln:
                    m = SLOW.match(ln)
                    if m:
                        frames.append((datetime.datetime.strptime(m.group(1), TS), int(m.group(2)), float(m.group(3)),
                                       int(m.group(4)), int(m.group(5))))
                elif 'resolve after drop:' in ln:
                    m = RAD.match(ln)
                    if m:
                        rad.append(datetime.datetime.strptime(m.group(1), TS))
    return {'frames': frames, 'rad': rad, 'ff': frames[0][0] if frames else None,
            'files': [os.path.basename(p) for p in files]}


def events(d):
    """Scene anchors relative to FF (s): first 3D frame (first frame with new >= 15 after FF+60 s), the load
    transition (the next frame with new >= 15, >= 1 s later), the 12.4k shot (the first frame with new >= 60)."""
    ff = d['ff']
    out = {}
    if ff is None:
        return out
    big = [(t, n) for (t, _, _, n, _) in d['frames'] if n >= 15 and (t - ff).total_seconds() > 60]
    if big:
        out['first-3d'] = (big[0][0] - ff).total_seconds()
        later = [t for (t, n) in big if (t - big[0][0]).total_seconds() >= 1.0]
        if later:
            out['load'] = (later[0] - ff).total_seconds()
    s67 = [t for (t, _, _, n, _) in d['frames'] if n >= 60]
    if s67:
        out['shot-12.4k'] = (s67[0] - ff).total_seconds()
    return out


def window(d, t0, t1):
    """Frames, sum of dropped draws, frames with drops, max dropped, new pipelines, resolve-after-drop lines in [t0, t1]."""
    fr = [x for x in d['frames'] if t0 <= x[0] <= t1]
    return {'frames': len(fr), 'dropped': sum(x[4] for x in fr), 'frames_dropping': sum(1 for x in fr if x[4] > 0),
            'max_dropped': max([x[4] for x in fr] or [0]), 'new': sum(x[3] for x in fr),
            'max_ms': max([x[2] for x in fr] or [0.0]), 'rad': sum(1 for t in d['rad'] if t0 <= t <= t1)}
