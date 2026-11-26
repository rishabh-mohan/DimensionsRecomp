#!/usr/bin/env python3
"""rt_smoke_post.py - post checks for RUN-RT-SMOKE.cmd (M2, S5 Phase 3: T2 + F3) on devs5toml-bin / natives5fsr1p-bin.

FUNCTIONAL only (M10 P1/P2): no timing or perf verdicts. Arms (run dirs from harness\\run-game.ps1), any subset:
  --T2  <dir>  devs5toml-bin, harness toml (present_effect='fsr'), framerate_limit=60
  --F3A <dir>  natives5fsr1p-bin, harness toml (present_effect='fsr'), native_fps_limit=60       FSR 1 arm
  --F3B <dir>  natives5fsr1p-bin, perf-bilinear.toml (present_effect='bilinear'), native_fps_limit=60
Gates (every arm): run.json clean exit (exit 0, not early, wm_close), no dumps/crash events/WER, bin_dir = the arm's
bin, cvars exactly as the arm, run-dir toml = the arm's source toml (sha256-pinned) except user_data_root and the
-Cvar keys, toml not rewritten by the game, check-defaults PASS (T2 --mode xenos, F3 --mode native); against the
sha256-pinned reference logs of the same build family (T2: devfinal2 cold-ship60 + ship60-r1; F3: native4bp
cold-n4bp60 + n4bp60-r1, window 20261125-1804, attract-long): every runstats.py marker the refs have is there,
0 error/critical lines whose normalised text the refs lack, 0 new 'Config: unknown cvar' names; 0 'Native FSR 1:' lines.
  T2   exactly one warning-level "Config: present_effect = 'fsr' in <toml> rejected (allowed: bilinear); keeping
       'bilinear' ... (reported before logging started)" line (P1); 0 FFX-fallback INFO lines (not in this bin).
  F3A  frames.csv (native metrics) >= 2000 rows, spatial_fsr_presented=1 on >= 90% of them, fsr_enabled=0 on all
       (P4); run-dir toml present_effect='fsr'; 4 usable kit-shots (60 120 146 200 s): per time the PrintWindow PNG or
       the kit's screen copy, client >= 2% non-black by pixels (MIN_NONBLACK; the shots.txt label is not trusted).
  F3B  frames.csv >= 2000 rows, spatial_fsr_presented=0 and fsr_enabled=0 on all rows (P4); present_effect='bilinear';
       0 FFX-fallback INFO lines; 4 usable kit-shots (as F3A).
Report only: other Config: lines, new warning kinds, the FFX-fallback INFO line count on F3A, the hard-exit line, the
rows with spatial_fsr_presented=0 on F3A by source/output size, and the side-by-side PNGs (F3A FSR 1 left | F3B
bilinear right, full frame + 2x centre crop, with a detail number that is info only: the frames differ).
Exit 0 = every gate PASS. --selftest ARM=<dir> ... [SBS=<dirA>,<dirB>]: parse only (no gates), for the dry run.
"""
import argparse, csv, hashlib, json, os, re, subprocess, sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(ROOT, 'harness'))
import runstats as rs  # noqa: E402  (LOG_LINE, MARKERS, UNKNOWN_CVAR, BAD_LEVELS; pinned by the kit)

CD = os.path.join(ROOT, 'build', 'agent2', 'final', 'check-defaults.py')
MX = r'build\agent8\s5\matrix\20261125-1804\runs'
REFS = {  # game.log sha256 pins
    'devfinal2': [(MX + r'\1805-cold-ship60', '0FB3DC8AF9140841D5B28E38681865C693E956C7321FA4F2B513C708AA449FF0'),
                  (MX + r'\1815-ship60-r1', '850B9BE0FD6053B658C3209EF994BCD2C6585AFC253534A7469EE48734159683')],
    'native4bp': [(MX + r'\1812-cold-n4bp60', '93E1754B876684F286C13EF6923ACFEA46B89C994B4269D36D13EC2795533502'),
                  (MX + r'\1825-n4bp60-r1', '5AD5426AE17EAB2F9C22E22E688C4A75C0B5407DE92860D48D5D236EB892D1E9')],
}
TOML_H = (r'harness\legodimensions.toml', 'B763DABBE2C5FE7AFA300B3013EFDEE1FB9BF33E7A0A96738BEAC4BAF474FF54')
TOML_B = (r'build\agent2\s5\native-fsr1\perf-bilinear.toml',
          'FA47B1E31787B24D04B59E15F26D8B2ADFFC456B38E7DE24A2B5F80F24375B16')
ARMS = {
    'T2': dict(bin=r'build\agent2\s5\devs5toml-bin', cvars={'framerate_limit': '60'}, toml=TOML_H, effect='fsr',
               mode='xenos', ref='devfinal2', native=False),
    'F3A': dict(bin=r'build\agent2\s5\natives5fsr1p-bin', cvars={'native_fps_limit': '60'}, toml=TOML_H, effect='fsr',
                mode='native', ref='native4bp', native=True, fsr=1),
    'F3B': dict(bin=r'build\agent2\s5\natives5fsr1p-bin', cvars={'native_fps_limit': '60'}, toml=TOML_B,
                effect='bilinear', mode='native', ref='native4bp', native=True, fsr=0),
}
SHOT_ARMS, SHOT_TIMES = ('F3A', 'F3B'), (60, 120, 146, 200)
MIN_ROWS, FSR_SHARE = 2000, 0.90
MIN_NONBLACK = 0.02  # kit-shot client share with R+G+B > 24 (a black native PrintWindow + fps counter is 0.4%;
#                      a dark real Xenos frame, nops t2 60 s, is 6.6%)
REJ_RE = re.compile(r"Config: present_effect = 'fsr' in (\S.*?) rejected \(allowed: bilinear\); keeping 'bilinear'")
L_REJ_SUFFIX = '(reported before logging started)'
L_FSR1_WARN = 'Native FSR 1:'
L_FFX_INFO = 'present_effect=fsr: this build has no FidelityFX SDK'
L_HARD_EXIT = 'Title terminated; hard-exiting process'

out_lines, fails = [], []


def say(s=''):
    print(s)
    out_lines.append(s)


def check(name, ok, detail='', gate=True):
    say('%s  %s%s' % ('PASS' if ok else ('FAIL' if gate else 'note'), name, ('  [' + detail + ']') if detail else ''))
    if gate and not ok:
        fails.append(name)


def sha(p):
    with open(p, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def norm(msg):
    return re.sub(r'0x[0-9A-Fa-f]+|\b[0-9A-Fa-f]{8,}\b|\d+(\.\d+)?', '#', msg).strip()


def joined_log(rd):
    rot = sorted([f for f in os.listdir(rd) if re.fullmatch(r'game\.\d+\.log', f)], key=lambda f: -int(f.split('.')[1]))
    files = rot + (['game.log'] if os.path.exists(os.path.join(rd, 'game.log')) else [])
    lines = []
    for f in files:
        with open(os.path.join(rd, f), 'r', encoding='utf-8', errors='replace') as fh:
            lines += fh.read().splitlines()
    if len(files) == 1:
        return lines, os.path.join(rd, files[0]), files
    jp = os.path.join(HERE, 'rt-smoke', 'post', 'joined-%s.log' % os.path.basename(rd))
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    with open(jp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    return lines, jp, files


def run_json(rd):
    p = os.path.join(rd, 'run.json')
    if not os.path.exists(p):
        return {}
    with open(p, 'r', encoding='utf-8-sig') as fh:
        return json.load(fh)


def log_facts(lines):
    """parsed lines -> markers, bad (error/critical) msgs, warning msgs, unknown cvar names, unparsed count."""
    f = dict(markers=Counter(), bad=[], warn=[], unknown=set(), unparsed=0, parsed=[])
    for l in lines:
        m = rs.LOG_LINE.match(l)
        if not m:
            f['unparsed'] += 1
            continue
        lv, msg = m.group('level'), m.group('msg')
        f['parsed'].append((lv, msg))
        for k, r in rs.MARKERS.items():
            if r.search(msg):
                f['markers'][k] += 1
        if lv in rs.BAD_LEVELS:
            f['bad'].append(msg)
        elif lv == 'warning':
            f['warn'].append(msg)
        u = rs.UNKNOWN_CVAR.search(msg)
        if u:
            f['unknown'].add(u.group('name'))
    return f


_ref_cache = {}


def ref_facts(group, gate):
    if group in _ref_cache:
        return _ref_cache[group]
    agg = dict(markers=set(), bad=set(), warn=set(), unknown=set())
    for rel, pin in REFS[group]:
        p = os.path.join(ROOT, rel, 'game.log')
        ok = os.path.exists(p) and sha(p) == pin
        check('ref %s %s game.log sha256 = pin %s' % (group, os.path.basename(rel), pin[:16]), ok, p, gate)
        if not os.path.exists(p):
            continue
        with open(p, 'r', encoding='utf-8', errors='replace') as fh:
            f = log_facts(fh.read().splitlines())
        agg['markers'] |= {k for k, v in f['markers'].items() if v}
        agg['bad'] |= {norm(m) for m in f['bad']}
        agg['warn'] |= {norm(m) for m in f['warn']}
        agg['unknown'] |= f['unknown']
    say('ref %s: markers %s; ref error/critical kinds: %d; warning kinds %d; unknown cvars %d' % (
        group, sorted(agg['markers']), len(agg['bad']), len(agg['warn']), len(agg['unknown'])))
    _ref_cache[group] = agg
    return agg


def toml_gates(arm, rd, J, spec, g):
    src_rel, pin = spec['toml']
    src = os.path.join(ROOT, src_rel)
    check('%s source toml %s sha256 = pin %s' % (arm, os.path.basename(src_rel), pin[:16]),
          os.path.exists(src) and sha(src) == pin, src, g)
    rt = os.path.join(rd, 'legodimensions.toml')
    if not (os.path.exists(src) and os.path.exists(rt)):
        check('%s run-dir toml present' % arm, False, rt, g)
        return
    keys = ['user_data_root'] + list(spec['cvars'])
    kre = re.compile(r'^\s*(%s)\s*=' % '|'.join(map(re.escape, keys)))
    rd_lines = open(rt, encoding='utf-8-sig', errors='replace').read().splitlines()
    s_lines = open(src, encoding='utf-8-sig', errors='replace').read().splitlines()
    same = [l for l in rd_lines if not kre.match(l)] == [l for l in s_lines if not kre.match(l)]
    want = {'user_data_root': "'%s'" % os.path.join(os.path.abspath(rd), 'user')}
    want.update(spec['cvars'])
    got = {}
    for l in rd_lines:
        m = re.match(r'^\s*(\w+)\s*=\s*(.*?)\s*$', l)
        if m and m.group(1) in want:
            got[m.group(1)] = m.group(2)
    vals = all(os.path.normcase(got.get(k, '')) == os.path.normcase(v) for k, v in want.items())
    check('%s run-dir toml = %s except user_data_root/-Cvar keys, which hold the run values' % (
        arm, os.path.basename(src_rel)), same and vals, 'other lines equal %s; %s' % (same, got), g)
    eff = [re.sub(r'\s*#.*$', '', l.split('=', 1)[1]).strip().strip('\'"') for l in rd_lines
           if re.match(r'^\s*present_effect\s*=', l)]
    check("%s run-dir toml present_effect = '%s'" % (arm, spec['effect']), eff == [spec['effect']], str(eff), g)
    check('%s toml not rewritten by the game' % arm, J.get('toml_rewritten') in (False, None),
          'toml_rewritten %s' % J.get('toml_rewritten'), g)


def frames_report(arm, rd, spec, g):
    name = next((n for n in ('frames.csv', 'native-frames.csv') if os.path.exists(os.path.join(rd, n))), None)
    if not name:
        check('%s frames.csv present (native metrics)' % arm, False, rd, g)
        return None
    with open(os.path.join(rd, name), 'r', encoding='utf-8', errors='replace') as fh:
        rows = list(csv.DictReader(fh))
    iv = lambda r, k: int(float(r.get(k) or 0))
    n1 = sum(iv(r, 'spatial_fsr_presented') == 1 for r in rows)
    fe = sum(iv(r, 'fsr_enabled') != 0 for r in rows)
    first1 = next((r.get('frame') for r in rows if iv(r, 'spatial_fsr_presented') == 1), None)
    size = lambda r: '%sx%s->%sx%s' % (r.get('present_source_width'), r.get('present_source_height'),
                                       r.get('output_width'), r.get('output_height'))
    share = n1 / len(rows) if rows else 0.0
    say('%s frames: %d rows (%s), spatial_fsr_presented=1 on %d (%.1f%%), first at frame %s; fsr_enabled!=0 on %d; '
        'sizes %s' % (arm, len(rows), name, n1, 100 * share, first1, fe, dict(Counter(size(r) for r in rows).most_common(4))))
    zero = Counter(size(r) for r in rows if iv(r, 'spatial_fsr_presented') != 1)
    if spec.get('fsr') == 1 and zero:
        say('  rows with spatial_fsr_presented=0 by source->output size: %s' % dict(zero.most_common(5)))
    check('%s frames.csv >= %d rows' % (arm, MIN_ROWS), len(rows) >= MIN_ROWS, '%d' % len(rows), g)
    if spec.get('fsr') == 1:
        check('%s spatial_fsr_presented=1 on >= %d%% of rows (P4, FSR 1 on)' % (arm, 100 * FSR_SHARE),
              share >= FSR_SHARE, '%.1f%%' % (100 * share), g)
    else:
        check('%s spatial_fsr_presented=0 on every row (P4, bilinear)' % arm, n1 == 0, '%d rows with 1' % n1, g)
    check('%s fsr_enabled=0 on every row (no native FSR 3)' % arm, fe == 0, '%d' % fe, g)
    return dict(rows=len(rows), n1=n1, share=share)


def client_nonblack(p):
    """Share of client pixels (below the title bar) with R+G+B > 24; None if the PNG is missing or unreadable."""
    try:
        from PIL import Image
        import numpy as np
        a = np.asarray(Image.open(p).convert('RGB'), dtype=np.int32)
    except Exception:
        return None
    c = a[min(40, a.shape[0] // 4):]
    return float((c.sum(axis=2) > 24).mean()) if c.size else None


def pick_shot(rd, t):
    """The kit-shot used for time t: the PrintWindow PNG if its client is >= MIN_NONBLACK non-black, else the kit's
    screen copy (shot-NNNs-screen.png, taken when PrintWindow came back near-black and the game was in front).
    Returns (path or None, 'NNNs printwindow x% screen y%')."""
    info, best = [], None
    for kind, name in (('printwindow', 'shot-%03ds.png'), ('screen', 'shot-%03ds-screen.png')):
        p = os.path.join(rd, 'kit-shots', name % t)
        s = client_nonblack(p) if os.path.exists(p) else None
        info.append('%s %s' % (kind, '-' if s is None else '%.1f%%' % (100 * s)))
        if best is None and s is not None and s >= MIN_NONBLACK:
            best = p
    return best, '%03ds %s' % (t, ' '.join(info))


def shots_gate(arm, rd, g):
    # Pixel gate (M10 delta): the label in shots.txt is not trusted; a native flip/tearing swap chain gives a black
    # PrintWindow whose title bar and fps counter fool winhelper's IsBlack.
    picks = [pick_shot(rd, t) for t in SHOT_TIMES]
    sp = os.path.join(rd, 'kit-shots', 'shots.txt')
    sl = open(sp, encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(sp) else []
    say('%s shots.txt %d lines%s' % (arm, len(sl), ''.join('\n    ' + l for l in sl)))
    check('%s screenshots (%d times, client >= %d%% non-black, PrintWindow or screen copy)' % (
        arm, len(SHOT_TIMES), round(100 * MIN_NONBLACK)), all(p for p, _ in picks),
        '; '.join('%s -> %s' % (i, os.path.basename(p) if p else 'NONE') for p, i in picks), g)


def arm_gates(arm, rd, gates=True):
    spec = ARMS[arm]
    g = gates
    say('')
    say('--- %s %s' % (arm, rd))
    J = run_json(rd)
    cv = {k: str(v).lower() for k, v in (J.get('cvars') or {}).items()}
    say('bin %s exe %s cvars %s' % (J.get('bin_dir'), (J.get('exe_sha256') or '')[:16], J.get('cvars')))
    check('%s clean exit (exit 0, not early, wm_close)' % arm,
          J.get('exit_code') == 0 and not J.get('exited_early') and J.get('close_method') in ('wm_close', 'script_stop', None),
          'exit %s early %s close %s' % (J.get('exit_code_hex', J.get('exit_code')), J.get('exited_early'),
                                         J.get('close_method')), g)
    check('%s no dumps / crash events / WER' % arm, not J.get('dumps') and not J.get('crash_events') and not J.get('wer_seen'),
          'dumps %s crash %s wer %s' % (J.get('dumps'), J.get('crash_events'), J.get('wer_seen')), g)
    want_bin = os.path.normcase(os.path.join(ROOT, spec['bin']))
    check('%s bin_dir = %s' % (arm, spec['bin']), os.path.normcase(os.path.normpath(J.get('bin_dir') or '')) == want_bin,
          str(J.get('bin_dir')), g)
    check('%s cvars exactly %s' % (arm, spec['cvars']), cv == spec['cvars'], str(cv), g)
    toml_gates(arm, rd, J, spec, g)
    lines, logp, files = joined_log(rd)
    say('logs %s, %d lines' % (files, len(lines)))
    cp = subprocess.run([sys.executable, '-B', CD, logp, '--mode', spec['mode']], capture_output=True, text=True,
                        encoding='utf-8', errors='replace')
    check('%s check-defaults --mode %s PASS' % (arm, spec['mode']), cp.returncode == 0 and 'RESULT PASS' in cp.stdout,
          'exit %d; %s' % (cp.returncode, (cp.stdout.strip().splitlines() or ['?'])[-1]), g)
    ref = ref_facts(spec['ref'], g)
    f = log_facts(lines)
    say('%s levels %s, unparsed (continuation) lines %d' % (arm, dict(Counter(lv for lv, _ in f['parsed'])), f['unparsed']))
    miss = sorted(ref['markers'] - {k for k, v in f['markers'].items() if v})
    check('%s runstats markers of the %s refs all present (P1: log patterns still match)' % (arm, spec['ref']),
          not miss, 'missing %s; have %s' % (miss, dict(f['markers'])), g)
    new_bad = [m for m in f['bad'] if norm(m) not in ref['bad']]
    check('%s 0 new error/critical lines vs %s' % (arm, spec['ref']), not new_bad,
          '%d error/critical, %d new: %s' % (len(f['bad']), len(new_bad), ' | '.join(m[:100] for m in new_bad[:5])), g)
    new_unk = sorted(f['unknown'] - ref['unknown'])
    check("%s 0 new 'Config: unknown cvar' names" % arm, not new_unk, str(new_unk), g)
    new_warn = Counter(norm(m) for m in f['warn'] if norm(m) not in ref['warn'])
    say('  info: %d new warning kinds vs %s%s' % (len(new_warn), spec['ref'], ''.join(
        '\n    %dx %s' % (n, k[:150]) for k, n in new_warn.most_common(8))))
    n = lambda s: sum(s in m for _, m in f['parsed'])
    check("%s 0 '%s' lines" % (arm, L_FSR1_WARN), n(L_FSR1_WARN) == 0, '%d' % n(L_FSR1_WARN), g)
    cfg = [(lv, m) for lv, m in f['parsed'] if m.startswith('Config:')]
    if arm == 'T2':
        rej = [(lv, m) for lv, m in cfg if REJ_RE.search(m)]
        say('T2 present_effect reject lines: %d%s' % (len(rej), ''.join('\n    [%s] %s' % x for x in rej)))
        check("T2 exactly one warning-level present_effect 'fsr' reject line with the '%s' suffix (P1)" % L_REJ_SUFFIX,
              len(rej) == 1 and rej[0][0] == 'warning' and rej[0][1].rstrip().endswith(L_REJ_SUFFIX),
              '%d' % len(rej), g)
    other = [(lv, m) for lv, m in cfg if not REJ_RE.search(m)]
    say('  info: other Config: lines %d%s' % (len(other), ''.join('\n    [%s] %s' % (lv, m[:150]) for lv, m in other[:10])))
    if spec.get('fsr') == 1:
        say('  info: FFX-fallback INFO line (%s ...) %d' % (L_FFX_INFO, n(L_FFX_INFO)))
    else:
        check("%s 0 FFX-fallback INFO lines ('%s')" % (arm, L_FFX_INFO), n(L_FFX_INFO) == 0, '%d' % n(L_FFX_INFO), g)
    say('  info: hard-exit line %d' % n(L_HARD_EXIT))
    res = {'rd': rd}
    if spec['native']:
        res['frames'] = frames_report(arm, rd, spec, g)
    if arm in SHOT_ARMS:
        shots_gate(arm, rd, g)
    return res


def side_by_side(rd_a, rd_b, out_dir, la='F3A FSR 1 (harness toml)', lb='F3B bilinear (perf-bilinear.toml)'):
    """PNG pairs at matched shot times: A left, B right (full frame, then a 2x nearest centre crop). Report only."""
    try:
        from PIL import Image, ImageDraw
        import numpy as np
    except ImportError as e:
        say('side-by-side: skipped (%s)' % e)
        return []
    os.makedirs(out_dir, exist_ok=True)
    made = []
    detail = lambda im: float(np.abs(np.diff(np.asarray(im.convert('L'), dtype=np.float32), n=2, axis=1)).mean())
    for t in SHOT_TIMES:
        pa, pb = [pick_shot(d, t)[0] or os.path.join(d, 'kit-shots', 'shot-%03ds.png' % t) for d in (rd_a, rd_b)]
        if not (os.path.exists(pa) and os.path.exists(pb)):
            say('side-by-side %03ds: missing %s' % (t, ' '.join(p for p in (pa, pb) if not os.path.exists(p))))
            continue
        A, B = Image.open(pa).convert('RGB'), Image.open(pb).convert('RGB')
        outs = []
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
            dr.text((6, 5), '%s  t=%d s%s' % (la, t, '  (centre crop, 2x)' if kind == 'crop2x' else ''), fill=(255, 255, 255))
            dr.text((a.width + gap + 6, 5), '%s  t=%d s' % (lb, t), fill=(255, 255, 255))
            p = os.path.join(out_dir, 'sbs-%03ds%s.png' % (t, '' if kind == 'full' else '-crop2x'))
            c.save(p)
            outs.append(p)
        say('side-by-side %03ds: %s | %s  (A %s %dx%d, B %s %dx%d; detail A %.2f B %.2f, info only: different frames)' % (
            t, outs[0], outs[1], os.path.basename(pa), A.width, A.height, os.path.basename(pb), B.width, B.height,
            detail(A), detail(B)))
        made += outs
    return made


def verdicts(R, given, selftest=False):
    say('')
    say('=== PER-ARM VERDICTS (functional, untimed) ===')
    for arm in given:
        fa = [x for x in fails if x.startswith(arm + ' ')]
        v = 'n/a (selftest, no gates)' if selftest else 'PASS' if not fa else 'FAIL (%d)' % len(fa)
        say('%-4s %s%s' % (arm, v, ''.join('\n       - ' + x for x in fa)))
    rf = [x for x in fails if x.startswith('ref ')]
    if rf:
        say('refs FAIL: %s' % '; '.join(rf))


def main():
    ap = argparse.ArgumentParser()
    for a in ARMS:
        ap.add_argument('--' + a)
    ap.add_argument('--out')
    ap.add_argument('--sbs-dir', help='where the side-by-side PNGs go (default: next to --out)')
    ap.add_argument('--selftest', nargs='+', metavar='ARM=DIR', help='parse only, no gates; SBS=<dirA>,<dirB>')
    a = ap.parse_args()
    say('# rt_smoke_post %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    sbs_dir = a.sbs_dir or os.path.join(os.path.dirname(os.path.abspath(a.out or os.path.join(HERE, 'rt-smoke', 'post', 'x'))),
                                        'sbs-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    R, sbs_pair = {}, None
    if a.selftest:
        for kv in a.selftest:
            arm, rd = kv.split('=', 1)
            if arm == 'SBS':
                sbs_pair = rd.split(',', 1)
                continue
            R[arm] = arm_gates(arm, rd, gates=False)
        given = list(R)
    else:
        given = [k for k in ARMS if getattr(a, k)]
        if not given:
            ap.error('give at least one arm')
        for arm in given:
            R[arm] = arm_gates(arm, getattr(a, arm))
        if 'F3A' in R and 'F3B' in R:
            sbs_pair = (R['F3A']['rd'], R['F3B']['rd'])
    if sbs_pair:
        say('')
        say('=== SIDE-BY-SIDE (left %s | right %s) -> %s ===' % (sbs_pair[0], sbs_pair[1], sbs_dir))
        side_by_side(sbs_pair[0], sbs_pair[1], sbs_dir)
    verdicts(R, given, bool(a.selftest))
    say('')
    if a.selftest:
        say('RESULT: SELFTEST (no gates)')
    else:
        say('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d): %s' % (len(fails), '; '.join(fails))))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(out_lines) + '\n')
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()
