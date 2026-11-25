#!/usr/bin/env python3
"""#33 slow-frame field report (M6, session 3). Read-only, stdlib only.

  python -B s33_fields.py [--arm NAME=PATH ...] [--late-frames 120] [--out FILE] <run dir | game.log>...

Reads every slow_frame_log_ms line ('slow frame #N: X ms | ... | pipeline create T (Cx), new M | ...
| memexport full-buffer ... | dropped draws D | forced pipeline waits W.W (Kx)') from all game*.log
rotations of a run (oldest -> newest: game.<highest N>.log first, game.log last). Per run:
  - slow lines, frames >= 100 / >= 250 ms and their summed ms, misses (sum of 'new');
  - whether the #33 fields are present (an unpatched bin has none: 'n/a');
  - dropped draws: total, frames with drops, the last frame with drops, and LATE drops = frames with
    drops more than --late-frames frames after the most recent frame with misses (DESIGN.md row 2:
    'dropped draws long after a burst' = a failed pipeline);
  - forced pipeline waits: total ms, total calls, max ms in one frame (read the ms, not the calls:
    Agent 10 N2);
  - the #33 latch lines: 'd3d12_pipeline_creation_no_wait: not waiting' (INFO) and '... ignored' (WARN).
With slow_frame_log_ms=1 every frame is logged; with a higher threshold drops in faster frames are not
visible. Arm = --arm label, else the dir name (NNNN-<arm>-rN, or yyyyMMdd-HHmmss-[s33-]<arm>).
Exit: 0 ok, 1 a run has no game*.log or a slow line with '| dropped draws' that does not parse,
2 usage error.
"""
import glob
import os
import re
import sys

SLOW_RE = re.compile(r'slow frame #(\d+): ([\d.]+) ms \|')
NEW_RE = re.compile(r'\| pipeline create [\d.]+ \(\d+x\), new (\d+) \|')
S33_RE = re.compile(r'\| dropped draws (\d+) \| forced pipeline waits ([\d.]+) \((\d+)x\)\s*$')
ROT_RE = re.compile(r'^game(?:\.(\d+))?\.log$', re.I)
INFO_TXT = 'd3d12_pipeline_creation_no_wait: not waiting for pipeline creation'
WARN_TXT = 'd3d12_pipeline_creation_no_wait ignored'
MATRIX_RUN_RE = re.compile(r'^\d{4}-(?:cold-)?([A-Za-z0-9]+)(?:-|$)')
HARNESS_RUN_RE = re.compile(r'^\d{8}-\d{6}-(?:s33-)?([A-Za-z0-9]+)')


def log_files(path):
    if os.path.isfile(path):
        return [path]
    found = []
    for p in glob.glob(os.path.join(path, 'game*.log')):
        m = ROT_RE.match(os.path.basename(p))
        if m:
            found.append((int(m.group(1)) if m.group(1) else 0, p))
    found.sort(key=lambda t: -t[0])
    return [p for _, p in found]


def arm_of(path):
    d = os.path.dirname(os.path.abspath(path)) if os.path.isfile(path) else os.path.abspath(path)
    name = os.path.basename(d)
    for rx in (MATRIX_RUN_RE, HARNESS_RUN_RE):
        m = rx.match(name)
        if m:
            return m.group(1).lower()
    return name.lower()


def analyse(path, late_frames):
    r = {'path': path, 'logs': log_files(path), 'slow': 0, 'ge100': 0, 'ge100_ms': 0.0, 'ge250': 0,
         'ge250_ms': 0.0, 'misses': 0, 's33': 0, 'dropped': 0, 'drop_frames': 0, 'last_drop': None,
         'late': 0, 'late_max': 0, 'fw_ms': 0.0, 'fw_n': 0, 'fw_max': 0.0, 'info': 0, 'warn': 0,
         'bad': []}
    last_miss = None
    for lf in r['logs']:
        with open(lf, encoding='utf-8', errors='replace') as f:
            for ln, line in enumerate(f, 1):
                if INFO_TXT in line:
                    r['info'] += 1
                if WARN_TXT in line:
                    r['warn'] += 1
                m = SLOW_RE.search(line)
                if not m:
                    continue
                frame, ms = int(m.group(1)), float(m.group(2))
                r['slow'] += 1
                if ms >= 100:
                    r['ge100'] += 1
                    r['ge100_ms'] += ms
                if ms >= 250:
                    r['ge250'] += 1
                    r['ge250_ms'] += ms
                nm = NEW_RE.search(line)
                if nm and int(nm.group(1)) > 0:
                    r['misses'] += int(nm.group(1))
                    last_miss = frame
                if '| dropped draws' not in line:
                    continue
                sm = S33_RE.search(line)
                if not sm:
                    r['bad'].append('%s:%d' % (os.path.basename(lf), ln))
                    continue
                r['s33'] += 1
                dd, fw, fn = int(sm.group(1)), float(sm.group(2)), int(sm.group(3))
                if dd:
                    r['dropped'] += dd
                    r['drop_frames'] += 1
                    r['last_drop'] = frame
                    gap = frame - last_miss if last_miss is not None else None
                    if gap is None or gap > late_frames:
                        r['late'] += 1
                        r['late_max'] = max(r['late_max'], gap if gap is not None else frame)
                r['fw_ms'] += fw
                r['fw_n'] += fn
                r['fw_max'] = max(r['fw_max'], fw)
    return r


def fmt(r, arm):
    out = ['== %s  (arm %s)  logs %d' % (r['path'].replace('\\', '/'), arm, len(r['logs']))]
    if not r['logs']:
        out.append('   WARN no game*.log')
        return out
    out.append('   latch: INFO not-waiting %d, WARN ignored %d' % (r['info'], r['warn']))
    out.append('   slow lines %d; frames >=100 ms %d (%.1f ms), >=250 ms %d (%.1f ms); misses %d' % (
        r['slow'], r['ge100'], r['ge100_ms'], r['ge250'], r['ge250_ms'], r['misses']))
    if not r['s33']:
        out.append('   #33 fields: n/a (no line with dropped draws / forced pipeline waits)')
    else:
        out.append('   #33 fields in %d lines: dropped draws %d in %d frames, last at frame %s; '
                   'late drops %d (max gap %d frames)' % (
                       r['s33'], r['dropped'], r['drop_frames'], r['last_drop'], r['late'], r['late_max']))
        out.append('   forced pipeline waits %.1f ms total (%d calls), max %.1f ms in one frame' % (
            r['fw_ms'], r['fw_n'], r['fw_max']))
    for b in r['bad'][:12]:
        out.append('   WARN unparsed #33 fields at %s' % b)
    return out


def main(argv):
    late, out_path, items = 120, None, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('--late-frames', '--out', '--arm'):
            if i + 1 >= len(argv):
                print(__doc__)
                return 2
            v = argv[i + 1]
            if a == '--late-frames':
                if not v.isdigit():
                    print(__doc__)
                    return 2
                late = int(v)
            elif a == '--out':
                out_path = v
            else:
                if '=' not in v or not re.match(r'^[A-Za-z0-9]+$', v.split('=', 1)[0]):
                    print('error: --arm needs NAME=PATH with an alphanumeric NAME')
                    return 2
                n, p = v.split('=', 1)
                items.append((n.lower(), p))
            i += 2
            continue
        if a.startswith('-'):
            print(__doc__)
            return 2
        items.append((None, a))
        i += 1
    if not items:
        print(__doc__)
        return 2
    for _, p in items:
        if not os.path.exists(p):
            print('error: no such file or dir: %s' % p)
            return 2
    lines, rc = ['#33 slow-frame fields (build/agent6/s33-popin/s33_fields.py), late = > %d frames '
                 'after the last miss' % late], 0
    for arm, p in items:
        r = analyse(p, late)
        lines += fmt(r, arm or arm_of(p))
        if not r['logs'] or r['bad']:
            rc = 1
    print('\n'.join(lines))
    if out_path:
        with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
