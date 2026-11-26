#!/usr/bin/env python3
"""dump_post.py (M16, S5 phase 0.4): read-only read-out of one LEGO_DUMP_MISSING_SHADERS attract run.

usage:
  dump_post.py --run RUN_DIR --dumps DUMP_ROOT [--trace TRACE_DIR] [--stage PACK_INPUT_DIR] --out REPORT.txt
  dump_post.py --trace-only EVENTS_TSV --out REPORT.txt          (self-test on an old trace)

Reports (and never writes outside --out / --stage):
  1. run: run.json exit fields, input.csv presses, game.log identity lines (fingerprint, miss cache OFF in dump mode);
  2. game.log: AOT-miss warnings (unique hashes), 'dumped missing shader' lines;
  3. dumps: every file per category (root = create path, placement-containers, placement-raw) with bytes and sha256;
     the 4 containers already packed in build/agent4/s35 are marked KNOWN; the rest are NEW;
  4. trace events.tsv: per-frame draw_calls and draw_missing_vertex/pixel_shader counts (the missing-draw "before"
     number), the guest addresses, missing_placement_shader_identity events.
--stage copies NEW pack candidates (root + placement-containers, never placement-raw) into PACK_INPUT_DIR plus
SHA256SUMS.txt; it refuses to overwrite a file with different bytes.
Exit 0 = report written (the verdict line says whether the dump looks usable).
"""
import argparse, collections, hashlib, json, os, re, shutil, statistics, sys

KNOWN = {  # build/agent4/s35/README.md inputs (already in the s35 scratch pack)
    '6C4F65C3161DF6BEE23F9C551F34971D60275BB49C3DB6327CFF9084F4317A66': 'vs-ACAF01F01E1C03D2 (s35 placement VS 0xAC449538)',
    '09D05274AFBC26A2605D0B91E5C2A0E0C95303C4C0C84F4D463105EB678D66EE': 'ps-75A4D1ABA62F7594 (s35 placement PS 0xAC448F28)',
    'F4EE30B28DEE9E4AB5AE2E9204D54195A0AC9D8D5497B7F2C8FAC11D90EEC65E': 'vs-CCD7655302B54D80 (s35 second placement VS)',
    '58B4FA21E35500529895AA400F4B307F0DD09BBBBDB71F5C7C8E8748B31170F1': 'ps-E81FD692C3AB35E1 (s35 second placement PS)',
}
FINGERPRINT = '1616ce65e973c583'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def trace_stats(path, out):
    frames = {}          # frame -> draw_calls
    miss = collections.Counter()   # frame -> missing draws (vs+ps events)
    miss_vs = collections.Counter(); miss_ps = collections.Counter()
    first_ms = {}
    frame_ms = {}
    ident = []
    with open(path, encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            p = line.rstrip('\r\n').split('\t')
            if len(p) < 5:
                continue
            ev = p[2]
            if ev not in ('frame', 'draw_missing_vertex_shader', 'draw_missing_pixel_shader',
                          'missing_placement_shader_identity'):
                continue
            try:
                fr = int(p[1]); ms = float(p[0])
            except ValueError:
                continue
            det = p[4].split()
            if ev == 'frame':
                frame_ms[fr] = ms
                if 'draw_calls=' in det:
                    i = det.index('draw_calls=')
                    try:
                        frames[fr] = float(det[i + 1])
                    except (IndexError, ValueError):
                        pass
            elif ev == 'missing_placement_shader_identity':
                ident.append(p[4].strip())
            else:
                miss[fr] += 1
                key = det[1] if len(det) > 1 else '?'
                stage = 'VS' if ev.endswith('vertex_shader') else 'PS'
                (miss_vs if stage == 'VS' else miss_ps)[key] += 1
                first_ms.setdefault((stage, key), ms)
    out.append(f'trace {path}')
    out.append(f'  frames with draw_calls: {len(frames)}; frames with >=1 missing draw: {len(miss)}')
    out.append(f'  draw_missing_vertex_shader events {sum(miss_vs.values())} ({len(miss_vs)} guest VS); '
               f'draw_missing_pixel_shader events {sum(miss_ps.values())} ({len(miss_ps)} guest PS)')
    m3 = [fr for fr in miss if fr in frames]
    res = {'frames': len(frames), 'frames_missing': len(miss), 'vs_events': sum(miss_vs.values()),
           'ps_events': sum(miss_ps.values()), 'vs_objects': len(miss_vs), 'ps_objects': len(miss_ps)}
    if m3:
        md = statistics.median(miss[fr] for fr in m3)
        dc = statistics.median(frames[fr] for fr in m3)
        res.update(median_missing_per_frame=md, median_draw_calls_same_frames=dc)
        # draw_calls counts recorded draws; missing ones return before recording (draw.cpp failed-bind test)
        out.append(f'  on frames with misses: median missing/frame {md:g}, median recorded draw_calls {dc:g} '
                   f'(=> ~{md:g} of ~{md + dc:g} submitted draws skipped, if draw_calls excludes skipped draws)')
    # 3D attract start: the first burst of >= 5 newly missing shader objects within 5 s (the attract load binds
    # dozens of never-seen VS at once; the front end only has the placement pair and a stray one)
    late = sorted(ms for (st, k), ms in first_ms.items())
    t3d = next((t for i, t in enumerate(late) if sum(1 for u in late[i:] if u - t <= 5000) >= 5), None)
    if t3d is not None:
        a3 = [fr for fr in frames if frame_ms.get(fr, -1) >= t3d]
        if a3:
            mm = [miss.get(fr, 0) for fr in a3]; dd = [frames[fr] for fr in a3]
            q = lambda v, p: sorted(v)[min(len(v) - 1, int(p * len(v)))]
            res.update(attract_from_ms=t3d, attract_frames=len(a3), attract_median_missing=statistics.median(mm),
                       attract_p90_missing=q(mm, 0.9), attract_median_draw_calls=statistics.median(dd),
                       attract_missing_total=sum(mm))
            out.append(f'  3D phase (frames from {t3d / 1000:.1f} s trace time, first burst of new misses): {len(a3)} frames, '
                       f'missing/frame median {statistics.median(mm):g} p90 {q(mm, 0.9):g}, recorded draw_calls median '
                       f'{statistics.median(dd):g}, missing total {sum(mm)}')
    for name, c in (('VS', miss_vs), ('PS', miss_ps)):
        for k, n in c.most_common(60):
            try:
                addr = f'0x{int(k):08X}'
            except ValueError:
                addr = k
            out.append(f'    missing {name} guest {addr}: {n} draws, first at {first_ms.get((name, k), 0) / 1000:.1f} s (trace time)')
    out.append(f'  missing_placement_shader_identity events: {len(ident)}')
    for s in ident[:40]:
        out.append(f'    {s}')
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run'); ap.add_argument('--dumps'); ap.add_argument('--trace'); ap.add_argument('--stage')
    ap.add_argument('--trace-only'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = []
    if a.trace_only:
        r = trace_stats(a.trace_only, out)
        out.append(f'RESULT: trace-only self-test {json.dumps(r)}')
        open(a.out, 'w', encoding='utf-8').write('\n'.join(out) + '\n'); print('\n'.join(out))
        return 0
    bad = []
    # 1. run
    rj = os.path.join(a.run, 'run.json')
    if os.path.exists(rj):
        try:
            j = json.load(open(rj, encoding='utf-8-sig'))
            keys = {k: j.get(k) for k in ('exit_code', 'exited_early', 'crashed', 'closed_by', 'desktop', 'seconds', 'status') if k in j}
            out.append(f'run.json {keys}')
            if j.get('crashed') or j.get('exited_early'):
                bad.append('run crashed or exited early')
        except Exception as e:  # noqa
            out.append(f'run.json unreadable: {e}'); bad.append('run.json unreadable')
    else:
        out.append('run.json missing'); bad.append('no run.json')
    ic = os.path.join(a.run, 'input.csv')
    if os.path.exists(ic):
        txt = open(ic, encoding='utf-8', errors='replace').read()
        presses = re.findall(r'press,?\s*(START|A)\b', txt)
        out.append(f'input.csv presses seen: {presses}')
        if len(presses) < 3:
            bad.append('START, A, A not all in input.csv')
    else:
        out.append('input.csv missing'); bad.append('no input.csv')
    gl = os.path.join(a.run, 'game.log')
    miss_hashes = collections.Counter(); dumped = 0; fp = mc_off = False
    if os.path.exists(gl):
        for line in open(gl, encoding='utf-8', errors='replace'):
            m = re.search(r'shader not present in AOT cache, hash=0x([0-9A-Fa-f]+)', line)
            if m:
                miss_hashes[m.group(1).upper()] += 1
            if 'dumped missing shader' in line:
                dumped += 1
            if FINGERPRINT in line:
                fp = True
            if 'shader miss cache OFF' in line and 'LEGO_DUMP_MISSING_SHADERS' in line:
                mc_off = True
        out.append(f'game.log: fingerprint {FINGERPRINT} {"seen" if fp else "NOT seen"}; dump mode line (miss cache OFF) {"seen" if mc_off else "NOT seen"}')
        out.append(f'game.log: AOT-miss warnings {sum(miss_hashes.values())} lines, {len(miss_hashes)} unique hashes; "dumped missing shader" {dumped} lines')
        for h, n in miss_hashes.most_common():
            out.append(f'    miss hash {h} x{n}')
        if not mc_off:
            bad.append('dump mode line missing (env not applied?)')
    else:
        out.append('game.log missing'); bad.append('no game.log')
    # 3. dumps
    new = []
    if a.dumps and os.path.isdir(a.dumps):
        for root, _, files in os.walk(a.dumps):
            cat = os.path.relpath(root, a.dumps)
            cat = 'root' if cat == '.' else cat.replace('\\', '/')
            for fn in sorted(files):
                p = os.path.join(root, fn); h = sha(p); n = os.path.getsize(p)
                tag = KNOWN.get(h, 'NEW')
                out.append(f'dump {cat}/{fn} {n} B {h} {tag}')
                if tag == 'NEW' and cat in ('root', 'placement-containers'):
                    new.append((cat, fn, p, h))
        out.append(f'pack candidates (NEW, root + placement-containers): {len(new)}')
    else:
        out.append(f'dump root {a.dumps} missing: no shader was dumped'); bad.append('no dump dir')
    if a.stage and new:
        os.makedirs(a.stage, exist_ok=True)
        sums = []
        for cat, fn, p, h in new:
            dst = os.path.join(a.stage, fn)
            if os.path.exists(dst):
                if sha(dst) != h:
                    out.append(f'STAGE REFUSED {dst}: exists with different bytes'); bad.append('stage clash'); continue
            else:
                shutil.copyfile(p, dst)
            sums.append(f'{h}  {fn}  ({cat})')
        open(os.path.join(a.stage, 'SHA256SUMS.txt'), 'w', encoding='utf-8').write('\n'.join(sums) + '\n')
        out.append(f'staged {len(sums)} pack candidates into {a.stage}')
    # 4. trace
    if a.trace:
        ev = os.path.join(a.trace, 'events.tsv')
        if os.path.exists(ev):
            trace_stats(ev, out)
        else:
            out.append(f'trace {ev} missing'); bad.append('no trace events.tsv')
    out.append('RESULT: ' + ('USABLE' if not bad else 'CHECK: ' + '; '.join(bad)) + f' ({len(new)} new pack candidates)')
    open(a.out, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
