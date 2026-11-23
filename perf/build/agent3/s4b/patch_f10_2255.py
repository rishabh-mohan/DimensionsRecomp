"""patch_f10_2255.py - Agent 3, 11-22 22:55. Agent 1's 22:44 plan: Agent 6's direct test for finding 10 (f10a = s4b20's
set, C1 OFF; f10b = w6gB's set, p2fc; both untimed vpad L route + tags via the fixed sidecar + slow_frame_log_ms=1, on
the quiet host) runs first after the windows; host CPU logged at any hang. Changes:
  s4b_check.py  - hang_scan(): STUCK-LOCK events with sys.csv CPU [-10, +2] s and hostload.csv +-60 s, quiet-host rows,
                  Toy Pad LOAD count; f10a/f10b proofs (cvars, tags 3/3, level reached, STUCK count, quiet host, G8);
  postcheck.ps1 - f10a/f10b bases (s4bL0) and allowed families; P2c also on f10b;
  queue.jsonl   - rows f10a, f10b before rpb0, needing ready-s4b-off + ready-later + ready-quiet.
Each file is backed up to <file>.bak-2255; each target must occur exactly once (else nothing is written).
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def patch(path, reps):
    raw = open(path, 'rb').read().decode('utf-8')
    crlf = '\r\n' in raw
    s = raw.replace('\r\n', '\n')
    for old, new in reps:
        c = s.count(old)
        if c != 1:
            sys.exit('%s: target occurs %d times: %r' % (path, c, old[:90]))
        s = s.replace(old, new)
    shutil.copy2(path, path + '.bak-2255')
    with open(path, 'wb') as f:
        f.write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    print('patched %s: %d replacements (%s)' % (os.path.basename(path), len(reps), 'CRLF' if crlf else 'LF'))


HANG_SCAN = r'''STUCK_TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\]')
STUCK_LR = re.compile(r'\blr[=: ]+(?:0x)?([0-9A-Fa-f]{8})\b')
HOSTLOAD = os.path.join(HERE, 'logs', 'hostload.csv')


def _ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def hang_scan(cand, hostload=HOSTLOAD):
    """Agent 1 (22:44): host CPU at any hang. STUCK-LOCK lines in every game*.log (lines <= 3 s apart = one event),
    each with the run's sys.csv (about 1 Hz) cpu_util_pct / e_eff_mhz over [-10 s, +2 s], hostload.csv (compiler
    processes, about every 30 s, from hostload.ps1) over +-60 s, and the lr values in its lines (finding 10 = owner in
    sub_83FAF180, 83FAF180-83FAF25F). Also the hostload rows during the run (quiet host = no clang/cl/ninja/link)
    and the Toy Pad LOAD confirmations (game.log lines + the sidecar's result row)."""
    stamps, loads = [], 0
    for name in sorted(os.listdir(cand)):
        if not re.match(r'game(\.\d+)?\.log$', name):
            continue
        with open(os.path.join(cand, name), encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'STUCK-LOCK' in line:
                    m = STUCK_TS.match(line)
                    t = _ts(m.group(1)) if m else None
                    if t:
                        stamps.append((t, line.rstrip()))
                elif 'Toypad listener: LOAD ->' in line:
                    loads += 1
    stamps.sort(key=lambda x: x[0])
    events = []
    for t, line in stamps:
        if events and (t - events[-1][-1][0]).total_seconds() <= 3:
            events[-1].append((t, line))
        else:
            events.append([(t, line)])

    def rows(p):
        if not os.path.exists(p):
            return []
        with open(p, newline='', encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    def fnum(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    sysrows = [(fnum(r.get('epoch_s')), r) for r in rows(os.path.join(cand, 'sys.csv'))]
    sysrows = [(e, r) for e, r in sysrows if e is not None]
    if stamps:
        day = stamps[0][0].date()
    elif sysrows:
        day = datetime.datetime.fromtimestamp(sysrows[0][0]).date()
    else:
        day = datetime.date.today()
    hl = []
    for r in rows(hostload):
        try:
            t = datetime.datetime.combine(day, datetime.datetime.strptime(r.get('time') or '', '%H:%M:%S').time())
        except ValueError:
            continue
        busy = sum(int(fnum(r.get(k)) or 0) for k in ('clang', 'cl', 'ninja', 'link'))
        hl.append((t.timestamp(), busy, '%s clang %s cl %s ninja %s link %s cpu %s%%' % (
            r.get('time'), r.get('clang'), r.get('cl'), r.get('ninja'), r.get('link'), r.get('cpu_pct'))))
    out = []
    for ev in events:
        e0 = ev[0][0].timestamp()
        win = [r for e, r in sysrows if e0 - 10 <= e <= e0 + 2]
        cpu = [x for x in (fnum(r.get('cpu_util_pct')) for r in win) if x is not None]
        emhz = [x for x in (fnum(r.get('e_eff_mhz')) for r in win) if x is not None]
        lrs = sorted(set(m.group(1).upper() for _t, line in ev for m in STUCK_LR.finditer(line)))
        f10 = bool(lrs) and all(0x83FAF180 <= int(x, 16) <= 0x83FAF25F for x in lrs)
        out.append({'at': ev[0][0].strftime('%H:%M:%S.%f')[:-3], 'lines': len(ev), 'lr': lrs,
                    'finding10': f10 if lrs else None, 'first_line': ev[0][1][-220:], 'sys_rows': len(win),
                    'cpu_util_pct': [round(x) for x in cpu], 'cpu_util_max': round(max(cpu), 1) if cpu else None,
                    'e_eff_mhz_min': round(min(emhz)) if emhz else None,
                    'hostload': [s for t, _b, s in hl if abs(t - e0) <= 60]})
    quiet = {}
    if sysrows:
        a, b = sysrows[0][0], sysrows[-1][0]
        inrun = [busy for t, busy, _s in hl if a <= t <= b]
        quiet = {'rows': len(inrun), 'busy_rows': sum(1 for busy in inrun if busy)}
    res_row = ''
    for r in rows(os.path.join(cand, 'toypad-events.csv')):
        if r.get('kind') == 'result':
            res_row = r.get('detail') or ''
    return out, quiet, {'confirms': loads, 'result': res_row}


def row_proofs(row, rj, S, ld, res):
'''

F10_PROOFS = r'''            '"Unhandled guest physical write fault" %d' % (n['protect_failed'], n['recovered_stale'], n['unhandled_phys']))
    if r in F10_CVARS:
        want = F10_CVARS[r]
        bad = {k: cv.get(k) for k, v in want.items() if cv.get(k) != v}
        chk(not bad, 'f10 %s cvars in run.json (%d expected, %s): %s' % (
            r, len(want), "s4b20's set + slow_frame_log_ms=1" if r == 'f10a' else "w6gB's set",
            'all as planned' if not bad else 'DIFFER %s' % bad))
        if r == 'f10a':
            chk(n['c1_any'] == 0, 'C1 off: no C1 line (%d)' % n['c1_any'])
            chk(n['slow_frame'] > 0, 'slow-frame lines %d' % n['slow_frame'])
            ms = res.get('memexport') or {}
            chk(None, 'memexport full-buffer total with P2 off (not a gate): last %s, max %s' % (
                ms.get('last_total'), ms.get('max_total')))
        tp = res.get('toypad') or {}
        chk((tp.get('confirms') or 0) >= 3, 'tags placed: %s game.log LOAD lines (3 needed); sidecar: %s' % (
            tp.get('confirms'), tp.get('result') or 'no result row'))
        chk('vortex' in (COVER['marks'] or []), 'L route reached the level: ' + cover_txt())
        hc = res.get('hang_cpu') or []
        chk(None, 'FINDING 10 (Agent 6 direct test): STUCK-LOCK events %d%s' % (len(hc), ''.join(
            '; at %s lr %s (finding 10: %s) cpu_util max %s' % (h['at'], ','.join(h['lr']) or '?', h['finding10'],
                                                               h['cpu_util_max']) for h in hc)))
        hq = res.get('host_quiet') or {}
        chk((hq.get('busy_rows') == 0) if hq.get('rows') else None,
            'quiet host: hostload.csv rows with clang/cl/ninja/link during the run: %s of %s' % (
                hq.get('busy_rows'), hq.get('rows')))
        chk(n['protect_failed'] == 0 and n['recovered_stale'] == 0 and n['unhandled_phys'] == 0,
            'G8 bad lines: Protect failed %d, Recovered stale %d, Unhandled guest physical write fault %d' % (
                n['protect_failed'], n['recovered_stale'], n['unhandled_phys']))
    return P
'''

HANG_SAY = r'''    say('sys.csv slow state: %s' % (json.dumps(ss) if ss is not None else 'no sys.csv'))
    hc, hq, tp = hang_scan(cand)
    res['hang_cpu'], res['host_quiet'], res['toypad'] = hc, hq, tp
    for i, h in enumerate(hc, 1):
        say('hang %d: STUCK-LOCK at %s (%d lines, lr %s, finding 10: %s); sys.csv cpu_util_pct [-10, +2] s: %s (max %s), '
            'e_eff_mhz min %s; hostload +-60 s: %s' % (i, h['at'], h['lines'], ','.join(h['lr']) or '?', h['finding10'],
                                                      h['cpu_util_pct'], h['cpu_util_max'], h['e_eff_mhz_min'],
                                                      '; '.join(h['hostload']) or 'no rows'))
        say('  first line: %s' % h['first_line'])
    say('hangs: %d STUCK-LOCK event(s); hostload rows during the run: %s; toypad: %s' % (
        len(hc), json.dumps(hq), json.dumps(tp)))
'''

F10_CVARS = r'''# 22:44 (Agent 1): Agent 6's direct test for finding 10, first after the windows on the quiet host: untimed vpad L route,
# tags via the fixed sidecar, slow_frame_log_ms=1; f10a = s4b20's set (C1 OFF), f10b = w6gB's set (p2fc).
F10_CVARS = {
    'f10a': {'shared_memory_upload_nontemporal_copy': 'true', 'slow_frame_log_ms': '1'},
    'f10b': dict(W6_CVARS['w6gB']),
}
# rows that read P2's counter (memexport full-buffer total; must be 0)
P2_ROWS = ('s4b23', 'w6s1', 'w6s2', 'w6gA', 'w6s3', 'w6gB', 'f10b')
'''

S4B_REPS = [
    ('import argparse\nimport json\n', 'import argparse\nimport csv\nimport datetime\nimport json\n'),
    ("# rows that read P2's counter (memexport full-buffer total; must be 0)\n"
     "P2_ROWS = ('s4b23', 'w6s1', 'w6s2', 'w6gA', 'w6s3', 'w6gB')\n", F10_CVARS),
    ("    elif r in ('s4b04', 's4b24', 's4b07', 'w6s2', 'w6gA', 'w6s3', 'w6gB'):\n",
     "    elif r in ('s4b04', 's4b24', 's4b07', 'w6s2', 'w6gA', 'w6s3', 'w6gB', 'f10b'):\n"),
    ("        elif r in ('w6s2', 'w6s3', 'w6gB'):\n", "        elif r in ('w6s2', 'w6s3', 'w6gB', 'f10b'):\n"),
    ("            if r == 'w6gB':\n", "            if r in ('w6gB', 'f10b'):\n"),
    ("    elif r in ('s4b19', 's4b20'):\n", "    elif r in ('s4b19', 's4b20', 'f10a'):\n"),
    ('''            '"Unhandled guest physical write fault" %d' % (n['protect_failed'], n['recovered_stale'], n['unhandled_phys']))
    return P
''', F10_PROOFS),
    ('def row_proofs(row, rj, S, ld, res):\n', HANG_SCAN),
    ("    say('sys.csv slow state: %s' % (json.dumps(ss) if ss is not None else 'no sys.csv'))\n", HANG_SAY),
]

W6GB_LINE = ("                '^w6gB$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', "
             "'C1 keep-watch|slow frame|memexport full-buffer') }\n")
PC_REPS = [
    (W6GB_LINE, W6GB_LINE +
     "                # 22:55: Agent 6's direct test for finding 10 (Agent 1 22:44), L route + tags + slow_frame_log_ms=1\n"
     "                '^f10a$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', "
     "'slow frame|memexport full-buffer') }\n"
     "                '^f10b$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', "
     "'C1 keep-watch|slow frame|memexport full-buffer') }\n"),
    ("if ($id -match '^(s4b08|s4b23$|w6)') { P2c $id $c }", "if ($id -match '^(s4b08|s4b23$|w6|f10b$)') { P2c $id $c }"),
]

NEEDS = ['build\\agent3\\s4b\\ready-s4b-off', 'build\\agent3\\s4b\\ready-later', 'build\\agent3\\s4b\\ready-quiet']
NOTE = ("Agent 1 22:44: first after the windows, on the quiet host (create ready-quiet only with no clang/cl/ninja/link "
        "running; hostload.ps1 must run): Agent 6's direct test for finding 10, untimed vpad L route + tags via the fixed "
        "sidecar (22:50) + slow_frame_log_ms=1. PASS/WARN + STUCK-LOCK count to Agents 1, 6, 10, 12.")
F10_ROWS = [
    {"id": "f10a", "est": 560, "toypad": True, "needs": NEEDS,
     "args": ["-BinDir", "build\\agent2\\devoff4b-bin", "-Seconds", "600", "-Tag", "f10a-m1-sfl-level",
              "-InputScript", "build\\agent3\\toypad\\routes\\level-l.txt",
              "-Cvar", "shared_memory_upload_nontemporal_copy=true;slow_frame_log_ms=1"],
     "note": "s4b20's set (C1 OFF) + slow_frame_log_ms=1. " + NOTE},
    {"id": "f10b", "est": 560, "toypad": True, "needs": NEEDS,
     "args": ["-BinDir", "build\\agent2\\devoff4b-bin", "-Seconds", "600", "-Tag", "f10b-p2fc-level",
              "-InputScript", "build\\agent3\\toypad\\routes\\level-l.txt",
              "-Cvar", "framerate_limit=0;shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true;"
                       "physical_protect_keep_watch=true;physical_protect_keep_watch_verify=false;slow_frame_log_ms=1"],
     "note": "w6gB's set (p2fc). " + NOTE},
]


def patch_queue(path):
    raw = open(path, 'rb').read().decode('utf-8')
    crlf = '\r\n' in raw
    lines = raw.replace('\r\n', '\n').split('\n')
    ids = [json.loads(l).get('id') if l.strip().startswith('{') else None for l in lines]
    if 'f10a' in ids or 'f10b' in ids:
        sys.exit('queue already has f10 rows')
    if ids.count('rpb0') != 1:
        sys.exit('queue: rpb0 occurs %d times' % ids.count('rpb0'))
    i = ids.index('rpb0')
    lines[i:i] = [json.dumps(r) for r in F10_ROWS]
    shutil.copy2(path, path + '.bak-2255')
    s = '\n'.join(lines)
    with open(path, 'wb') as f:
        f.write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
    print('patched %s: f10a, f10b inserted before rpb0 (line %d)' % (os.path.basename(path), i + 1))


if __name__ == '__main__':
    # check every target first, so a miss writes nothing
    for path, reps in ((os.path.join(HERE, 's4b_check.py'), S4B_REPS), (os.path.join(HERE, 'postcheck.ps1'), PC_REPS)):
        s = open(path, 'rb').read().decode('utf-8').replace('\r\n', '\n')
        for old, _new in reps:
            if s.count(old) != 1:
                sys.exit('%s: target occurs %d times: %r' % (path, s.count(old), old[:90]))
    patch(os.path.join(HERE, 's4b_check.py'), S4B_REPS)
    patch(os.path.join(HERE, 'postcheck.ps1'), PC_REPS)
    patch_queue(os.path.join(HERE, 'queue.jsonl'))
