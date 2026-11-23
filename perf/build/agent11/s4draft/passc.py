# passc.py - pass C of FINDINGS-AND-CHANGES.md and S4-DRAFT.md (Agent 11, task #25), after the 07:42 pass B2:
# Agent 7's rev 1 read-outs (~07:45), the SCRNSAVE post-install tests and Agent 10's 07:56 check, #19's rate
# request (08:12), Agent 2's PENDING-DIFFS refresh (07:49), the handoffs; and the W9 sub-bullet's breakdown of
# Agent 8's 32 disagreements corrected to 21 / 9 / 2 (W9-W5b-check.md L27).
# Dry run by default (writes passc-FN-diff.txt and passc-S4-diff.txt only); --apply --t=HH:MM writes both docs
# after hashed backups. Gates: both shas, LF counts, no CR, no BOM. Every op is keyed to a line number and needs
# its old text exactly once in that line. FINDINGS keeps its line count; S4-DRAFT gets one new line at the end only,
# so every external line cite stays valid (RESUME -> FINDINGS L141/142/146/147; RATE-REQUEST -> S4-DRAFT L236/L416;
# facts-perfopt -> S4-DRAFT L248, L252, L385-390, L393, L401-409).
import datetime
import difflib
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
OUTDIR = 'build/agent11/s4draft'
APPLY = '--apply' in sys.argv
T = None
for a in sys.argv[1:]:
    if a.startswith('--t='):
        T = a[4:]
if APPLY and not T:
    print('ABORT: --apply needs --t=HH:MM')
    sys.exit(1)
if not T:
    T = datetime.datetime.now().strftime('%H:%M')
if not re.fullmatch(r'\d\d:\d\d', T):
    print('ABORT: bad --t')
    sys.exit(1)
HHMM = T.replace(':', '')

DOCS = {
    'FN': {'path': 'perf-notes/FINDINGS-AND-CHANGES.md',
           'exp': '7D46CC9150CC0A6A0885F850DEA38B8312B1DF5091C8C71DDF40087B1411119C', 'nlf': 410, 'add': 0,
           'keep': [141, 142, 146, 147],
           'stale': ["(as of Nov 23, 07:42:"]},
    'S4': {'path': 'perf-notes/S4-DRAFT.md',
           'exp': 'A8EA669795AA9B650990158F996B8B864A063E3B354D30EA7263F87EA2E9EA37', 'nlf': 566, 'add': 1,
           'keep': [248, 252, 385, 386, 387, 388, 389, 390, 393, 401, 402, 403, 404, 405, 406, 407, 408, 409],
           'stale': ['26 differ by at most 2', '4 are light-share F values', 'the post-install tests and Agent 1']},
}
for k, d in DOCS.items():
    d['bk'] = os.path.join(OUTDIR, '%s.%s-%s.md' % (os.path.basename(d['path'])[:-3], HHMM, d['exp'][:8]))
BK_S4 = os.path.basename(DOCS['S4']['bk'])

fails = []
for k, d in DOCS.items():
    raw = open(d['path'], 'rb').read()
    sha = hashlib.sha256(raw).hexdigest().upper()
    if sha != d['exp']:
        fails.append('GATE %s sha %s' % (k, sha))
    if raw.count(b'\r'):
        fails.append('GATE %s CR' % k)
    if raw.startswith(b'\xef\xbb\xbf'):
        fails.append('GATE %s BOM' % k)
    if raw.count(b'\n') != d['nlf']:
        fails.append('GATE %s LF %d' % (k, raw.count(b'\n')))
    d['raw'] = raw
if fails:
    print('ABORT', fails)
    sys.exit(1)
for k, d in DOCS.items():
    d['lines'] = d['raw'].decode('utf-8').split('\n')
    assert d['lines'][-1] == '' and len(d['lines']) == d['nlf'] + 1
    print('GATE OK', k, d['exp'][:8], len(d['raw']), 'B,', d['nlf'], 'LF')

OPS = {'FN': [], 'S4': []}
APPEND = {'FN': [], 'S4': []}


def sub(doc, n, old, new):
    OPS[doc].append((n, old, new))


FL = '<workspace>/'

# ---------------- FINDINGS-AND-CHANGES.md (within lines only)
sub('FN', 1, "(as of Nov 23, 07:42: the night's windows are done",
    "(as of Nov 23, {T}: the night's windows are done")
sub('FN', 6, "they agree apart from rounding and a few small slips, none of which changes a verdict.",
    "they agree apart from rounding and a few small slips, none of which changes a verdict, and Agent 7 fixed its slips in a revision at about 07:45.")
sub('FN', 23, "and Agent 5 installed the fix at 07:33, before the launcher is used again.",
    "and Agent 5 installed the fix at 07:33, before the launcher is used again. After the install, all its tests passed again (45 of 45, plus 16 of 16 for the night launcher and 27 of 27 for the day launcher), and Agent 10 checked them at 07:56. Nothing needs re-pinning by hand: the launcher records the new files' fingerprints by itself the next time it starts.")
sub('FN', 34, "W7 (#19),",
    "W7 (#19; its rate request is written and waits for Agent 10's rating),")
sub('FN', 402, "W5b.md) (Agent 7), [Agent 8's check",
    "W5b.md) (Agent 7, revised at about 07:45), [Agent 8's check")
sub('FN', 402, ", and the [screensaver fix](" + FL + "build/agent5/scrnsave-fix/README.md) (Agent 5)",
    ", the [screensaver fix](" + FL + "build/agent5/scrnsave-fix/README.md) (Agent 5) with [Agent 10's post-install check](" + FL + "build/agent10/t27/scrnsave-delta.md), and the [rate request for #19](" + FL + "build/agent7/s4-r1s2/RATE-REQUEST.md) (Agent 7)")

# ---------------- S4-DRAFT.md (within lines, plus one new line at the end)
sub('S4', 3, "and on Nov 23 at 05:55, 06:55 and 07:42 under task #25",
    "and on Nov 23 at 05:55, 06:55, 07:42 and {T} under task #25")
sub('S4', 7, "(the 06:55 version is kept in `build/agent11/s4draft/S4-DRAFT.0742-017085DF.md`):",
    "(the 06:55 version is kept in `build/agent11/s4draft/S4-DRAFT.0742-017085DF.md`). At {T}, Agent 7's rev 1 of both read-outs (~07:45, no verdict changed), the SCRNSAVE post-install tests with Agent 10's 07:56 check, Agent 2's PENDING-DIFFS refresh, #19's rate request (08:12) and the agents' handoffs are in, and the W9 sub-bullet's breakdown of Agent 8's check is corrected (the 07:42 version is kept in `build/agent11/s4draft/{BK}`):")
sub('S4', 13, "(07:01, `build/agent7/readout/W9.md`;",
    "(07:01, rev 1 at ~07:45, `build/agent7/readout/W9.md`;")
sub('S4', 13, "Of the other 32, 26 differ by at most 2 in the last digit, 4 are light-share F values (results.csv's rounded light share can't reproduce them exactly), and 2 give",
    "Of the other 32, 21 are rounding ties (at most 1 in the last digit, no sign flip: Agent 7 works from unrounded per-run inputs, results.csv has 3 decimals), 9 come from the light-share definition (results.csv rounds each run's light share to 3 decimals, so the share differs by 0.001 in 5 runs and the F built on it moves), and 2 give")
sub('S4', 13, "still below the read-out's 2.8 cut for loaded runs, so its point stands).",
    "still below the read-out's 2.8 cut for loaded runs, so its point stands). Rev 1 of W9.md (~07:45, 8C58CAD1…) adds the ~23:16 Defender citation and softens one warm-up sentence; no number or verdict changed (W9.md §10).")
sub('S4', 15, "(07:21, `build/agent7/readout/W5b.md`;",
    "(07:21, rev 1 at ~07:45, `build/agent7/readout/W5b.md`;")
sub('S4', 15, "Agent 8's check covers this read-out too (the W9 bullet above).",
    "Agent 8's check covers this read-out too (the W9 bullet above). Rev 1 (~07:45, 6479A611…; W5b.md §10) applies the 11 findings of an independent check (`build/agent7/readout/check/CHECK-W5b.md`: ~830 claims, no copied number or CI wrong; mostly wording, sources and the Defender citation) and Agent 8's slip (0221's background load is 2.56, not 2.31; still unflagged, so no run set or number moves), and marks the loaded-run gap (−1.9 points) as post hoc and not significant (Welch p 0.083); no verdict changed.")
sub('S4', 22, "Agent 1 calls all four read-outs final (~07:38).",
    "Agent 1 calls all four read-outs final (~07:38). Agent 7's rev 1 of W9.md and W5b.md (~07:45) fixes the slips the checks found, with no verdict changed (the W9 and W5b sub-bullets).")
sub('S4', 24, "installed at 07:33:57, after the night launcher ended at 07:30:14 (all three files have the 'after' hashes; `build/agent5/scrnsave-fix/install-log.txt`).",
    "installed at 07:33:57, after the night launcher ended at 07:30:14 (all three files have the 'after' hashes; `build/agent5/scrnsave-fix/install-log.txt`). After the install: `test-scrnsave.ps1 -Set installed -E2E` 45/45 at 07:34:45 (`build/agent5/scrnsave-fix/results/summary-installed-073444.txt`), the day launcher's `test-day.ps1 -Name all` 27/27 at 07:47 (after a test-only fix; `build/agent5/day-draft/README-DAY.md` L130) and the night launcher's dry-run `go` group 16/16 at 07:52 on 565D30D4… (with a new test-only `-StopAt`; `build/agent5/launch-test/results/summary-go.txt`). Agent 10 checked them at 07:56 and closed the day draft's condition 1 (`build/agent10/t27/scrnsave-delta.md` §4-§5). No manual re-pin: the status file `pins.txt` is only a record, and the launcher pins the files it finds at each start (run-night.ps1 L967, L973; SESSION2 L3353).")
sub('S4', 26, "(Agent 10's condition 1, met in staged form)",
    "(Agent 10's condition 1, met in staged form, and closed at 07:56 after the install)")
sub('S4', 29, "§5 (finding 10: n = 2); §6 (the new sources).",
    "§5 (finding 10: n = 2); §6 (the new sources). Updated at {T} (Agent 7's rev 1 read-outs, the post-install tests, #19's rate request, the handoffs): the header; this block (the intro, the W9 sub-bullet, whose breakdown of the check's 32 disagreements is corrected to 21 / 9 / 2, the W5b sub-bullet, the read-outs bullet, the SCRNSAVE sub-bullet and the wrap-up bullet); row 19; W7 in §2c; §4b (the 06:17-07:38 entry, Ratings still missing and Possible changes); §6 (the new sources).")
sub('S4', 236, "not built, not rated; risk medium-high (F) |",
    "not built, not rated; risk medium-high (F). Rate request written (`build/agent7/s4-r1s2/RATE-REQUEST.md`, Nov 23, 08:12, task #32): it asks Agent 10, after the break, (a) SAFE to build into devoff4b default-off, (b) SAFE to test ON (`d3d12_submit_split_kb=<N>` with `d3d12_async_submit=true`) in the rows, the soak and W7, (c) the threading and ownership rules accepted; `<N>` waits for Agent 3's ready-N gate, and the `clang -fsyntax-only` check waits until compiles are allowed (its §10) |")
sub('S4', 416, "GPU Cmds and fps. #18 alone should tie (§17 cond 6) |",
    "GPU Cmds and fps. #18 alone should tie (§17 cond 6). Agent 7's draft (`build/agent7/s4-r1s2/matrix-w7-draft.json`, RATE-REQUEST §14; Agent 8 owns the final) drops the 4th arm, because #20's step 2 isn't staged: s0 / s18 / s19 on one bin, 1 + 3 × 4 = 13 runs, ~30-34 min, or 17 runs, ~39-45 min with the optional s19h (`<N/2>`); W7 runs only after #19's ON test is rated SAFE and the rows and the soak pass |")
sub('S4', 493, "W8a's matrix is staged (Agent 8).",
    "W8a's matrix is staged (Agent 8). Since then (07:42-08:13; Changed since 23:29): Agent 7's rev 1 of W9.md and W5b.md (~07:45; no verdict changed); Agent 2's PENDING-DIFFS refresh (07:49, task #31); the post-install tests (45/45 at 07:34:45, the day launcher's 27/27 at 07:47, the night launcher's go group 16/16 at 07:52) and Agent 10's check of them (07:56: the day draft's condition 1 closed); #19's rate request (08:12, task #32); the handoffs of Agents 1-10 and 12.")
sub('S4', 496, "#19 (staged),",
    "#19 (staged; its rate request is written, `build/agent7/s4-r1s2/RATE-REQUEST.md`, 08:12 on Nov 23, for Agent 10 after the break),")
sub('S4', 500, "Next, before the break: the post-install tests and Agent 1's re-pin announcement.",
    "Since 07:42: Agent 7's rev 1 read-outs, the post-install tests with Agent 10's 07:56 check, Agent 2's PENDING-DIFFS refresh, #19's rate request and the agents' handoffs (Changed since 23:29). Next, before the break: Agent 1's re-pin announcement.")
APPEND['S4'].append(
    "- **Added at {T}:** Agent 7's rev 1 read-outs `build/agent7/readout/W9.md` (8C58CAD1…) and `build/agent7/readout/W5b.md` (6479A611…), with the independent check `build/agent7/readout/check/CHECK-W5b.md` and the pre-fix copies `build/agent7/readout/check/W9-rev0.md` and `build/agent7/readout/check/W5b-rev0.md`; the post-install test summaries `build/agent5/scrnsave-fix/results/summary-installed-073444.txt` and `build/agent5/launch-test/results/summary-go.txt`, and the day launcher's 07:47 run (`build/agent5/day-draft/README-DAY.md` L130); Agent 10's post-install check `build/agent10/t27/scrnsave-delta.md` §4-§5; Agent 2's `build/agent2/PENDING-DIFFS.md` (07:49); #19's rate request `build/agent7/s4-r1s2/RATE-REQUEST.md` (08:12) with `build/agent7/s4-r1s2/matrix-w7-draft.json`; Agent 6's `build/agent6/s33-popin/DESIGN.md` (updated 07:40); the installed launcher `bench/agent5/launch/run-night.ps1` (565D30D4…; L967, L973); the handoffs `build/agent<N>/HANDOFF.md` of Agents 1-10 and 12 (06:06-08:13); SESSION2 to L3355.")

PATHRE = re.compile(r'`((?:build|bench|perf-notes|harness)/[^`\s]*)`')


def missing(text):
    out = set()
    for m in PATHRE.finditer(text):
        p = m.group(1)
        if '<' in p or '*' in p:
            continue
        if not os.path.exists(p.rstrip('/')):
            out.add(p)
    return out


for k, d in DOCS.items():
    lines = d['lines']
    out = lines[:]
    for n, old, nw in OPS[k]:
        l = out[n - 1]
        c = l.count(old)
        if c != 1:
            fails.append('OP %s L%d count %d: %r' % (k, n, c, old[:70]))
            continue
        out[n - 1] = l.replace(old, nw)
    body = out[:-1] + APPEND[k]
    new = '\n'.join(body) + '\n'
    new = new.replace('{T}', T).replace('{BK}', BK_S4)
    oldtext = '\n'.join(lines)
    nb = new.encode('utf-8')
    if '{T}' in new or '{BK}' in new:
        fails.append('PLACEHOLDER left in ' + k)
    if '\r' in new or new.startswith('\ufeff'):
        fails.append('CR/BOM in output ' + k)
    for s in d['stale']:
        if s in new:
            fails.append('STALE %s %r' % (k, s))
    newlines = new.split('\n')[:-1]
    if len(newlines) != d['nlf'] + d['add']:
        fails.append('LINES %s %d' % (k, len(newlines)))
    for n in d['keep']:
        if newlines[n - 1] != lines[n - 1]:
            fails.append('KEPT LINE CHANGED %s L%d' % (k, n))
    changed = [i + 1 for i in range(d['nlf']) if newlines[i] != lines[i]]
    pers_o = len(re.findall(r'<user>|rishabh', oldtext, re.I))
    pers_n = len(re.findall(r'<user>|rishabh', new, re.I))
    url_o = len(re.findall(r'https?://|file:///', oldtext))
    url_n = len(re.findall(r'https?://|file:///', new))
    print('%s: OPS %d, changed lines %s, appended %d; lines %d -> %d; personal %d -> %d; links %d -> %d'
          % (k, len(OPS[k]), changed, len(APPEND[k]), d['nlf'], len(newlines), pers_o, pers_n, url_o, url_n))
    if k == 'S4' and (pers_n != pers_o or url_n != url_o):
        fails.append('S4 personal/link count changed')
    if k == 'FN' and (pers_n - pers_o != 2 or url_n - url_o != 2):
        fails.append('FN personal/link delta not +2')
    newmiss = missing(new) - missing(oldtext)
    newmiss.discard('build/agent11/s4draft/' + BK_S4)
    for p in sorted(newmiss):
        print('  PATH missing (new in this pass): ' + p)
    if newmiss:
        fails.append('%s new missing paths %d' % (k, len(newmiss)))
    diff = difflib.unified_diff(lines[:-1], newlines, '%s 07:42' % k, '%s passc' % k, lineterm='', n=0)
    with open(os.path.join(OUTDIR, 'passc-%s-diff.txt' % k), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(diff) + '\n')
    d['nb'] = nb
    d['nsha'] = hashlib.sha256(nb).hexdigest().upper()
    print('NEW %s %s %d B %d LF' % (k, d['nsha'], len(nb), nb.count(b'\n')))

if fails:
    for x in fails:
        print('FAIL', x)
    print('ABORT (nothing written)')
    sys.exit(2)
if not APPLY:
    print('DRY OK (diffs in %s/passc-FN-diff.txt and passc-S4-diff.txt; S4 backup would be %s)' % (OUTDIR, BK_S4))
    sys.exit(0)
for k, d in DOCS.items():
    if os.path.exists(d['bk']):
        print('ABORT backup exists', d['bk'])
        sys.exit(3)
for k, d in DOCS.items():
    with open(d['bk'], 'wb') as f:
        f.write(d['raw'])
    if hashlib.sha256(open(d['bk'], 'rb').read()).hexdigest().upper() != d['exp']:
        print('ABORT backup mismatch', d['bk'])
        sys.exit(3)
for k, d in DOCS.items():
    with open(d['path'], 'wb') as f:
        f.write(d['nb'])
    chk = open(d['path'], 'rb').read()
    if hashlib.sha256(chk).hexdigest().upper() != d['nsha']:
        print('ABORT write mismatch', d['path'])
        sys.exit(4)
    print('WROTE', d['path'], d['nsha'], len(chk), 'B', chk.count(b'\n'), 'LF; backup', d['bk'])
