"""Rebuild perf-notes/agent2-baseline.md and build/agent2/notes-top.md (both truncated to 0 bytes at 19:59:40)
by replaying Agent 2's transcript. Writes only into build/agent2/recovered/. Read-only on everything else."""
import builtins, datetime, io, json, os, re, sys

R = r'<workspace>'
LOGS = r'C:\Users\<user>\.gemini\antigravity-cli\brain\8f8b148b-98c7-4cb4-810f-5bd712203d23\.system_generated'
TRANSCRIPT = LOGS + r'\logs\transcript_full.jsonl'
STEPS = LOGS + r'\steps'
OUT = R + r'\build\agent2\recovered'
P_BASE = R + r'\perf-notes\agent2-baseline.md'
P_TOP = R + r'\build\agent2\notes-top.md'
SCRIPTS = {'splice-notes.py': R + r'\build\agent2\splice-notes.py',
           'splice-notes2.py': R + r'\build\agent2\splice-notes2.py'}
WIPE = datetime.datetime(2026, 11, 21, 19, 59, 40)
EXPECT_CHARS, EXPECT_LINES = 40544, 511

rep = []
def say(*a):
    s = ' '.join(str(x) for x in a)
    rep.append(s)
    print(s)

def norm(p):
    return os.path.normcase(os.path.normpath(p))
KEY = {norm(P_BASE): 'BASE', norm(P_TOP): 'TOP'}
NAME = {'BASE': 'perf-notes/agent2-baseline.md', 'TOP': 'build/agent2/notes-top.md'}

def local(ts):
    return datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ') - datetime.timedelta(hours=6)

# ---------------------------------------------------------------- transcript parsing
rows = [json.loads(l) for l in open(TRANSCRIPT, encoding='utf-8')]
pairs = []          # dicts: step, time, name, args, res (row or None)
pending = []
for o in rows:
    if o['type'] == 'PLANNER_RESPONSE':
        pairs.extend(dict(p, res=None) for p in pending)
        pending = [dict(step=int(o['step_index']), time=local(o['created_at']), name=tc['name'],
                        args=tc.get('args', {})) for tc in (o.get('tool_calls') or [])]
    elif o['type'] == 'GENERIC' and pending:
        pairs.append(dict(pending.pop(0), res=o))
pairs.extend(dict(p, res=None) for p in pending)

def body(res):
    """Tool result text without the Created/Completed header lines; follows 'output truncated' links to steps/."""
    if res is None:
        return None
    def strip_head(c):
        ls = c.split('\n')
        k = 0
        while k < len(ls) and (ls[k].startswith('Created At:') or ls[k].startswith('Completed At:')):
            k += 1
        return '\n'.join(ls[k:])
    c = strip_head(res.get('content') or '')
    m = re.search(r'full output in a file at file:///(\S+?output\.txt)', c)
    if m and c.startswith("The tool's output was truncated"):
        c = strip_head(open(m.group(1).replace('/', '\\'), encoding='utf-8', newline='').read())
    return c

def res_time(res):
    m = re.search(r'Created At: (\S+)', (res or {}).get('content') or '')
    return datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=None) if m else None

def is_err(res):
    return res is not None and (bool(res.get('error')) or body(res).startswith('Encountered error'))

def touches(p):
    a = p['args']
    if 'Path' in a and norm(a['Path']) in KEY:
        return KEY[norm(a['Path'])]
    s = json.dumps(a)
    if p['name'] == 'run_command' and re.search(r'agent2-baseline|notes-top|splice-notes', s):
        return 'CMD'
    if 'Path' in a and os.path.basename(a['Path']) in SCRIPTS:
        return 'SCRIPT'
    return None

def classify_cmd(cl):
    if re.search(r"open\([^)]*'wb'\)", cl):
        return 'WRITER (inline python)'
    m = re.search(r'python\s+\S*(splice-notes\d?\.py)', cl)
    if m:
        return 'WRITER (runs %s)' % m.group(1)
    if re.search(r'Set-Content|Out-File|Add-Content|Copy-Item|Move-Item|Remove-Item|WriteAll|\.write\(', cl):
        return 'POSSIBLE WRITER - review'
    return 'reader'

# ---------------------------------------------------------------- read_file output parsing
def parse_read(text):
    m = re.match(r'Showing lines (\d+)-(\d+) of (\d+)\n', text)
    if not m:
        return None
    a, b, n = map(int, m.groups())
    ls = text[m.end():].split('\n')
    out = []
    for k in range(a, b + 1):
        l = ls[k - a]
        if l.startswith('%d: ' % k):
            out.append(l[len('%d: ' % k):])
        elif l == '%d:' % k:
            out.append('')
        else:
            raise ValueError('bad read line %d: %r' % (k, l[:60]))
    return a, b, n, out

def file_lines(s):
    """Lines as the read tool counts them (a final newline does not add an empty line)."""
    ls = s.split('\n')
    if s.endswith('\n'):
        ls = ls[:-1]
    return ls

# ---------------------------------------------------------------- fake file system for the splice scripts
class FakeFS:
    def __init__(self, files):
        self.files = dict(files)    # KEY -> bytes
        self.log = []
    def open(self, path, mode='r', encoding=None, newline=None, **kw):
        k = KEY.get(norm(path))
        if k is None:
            raise RuntimeError('splice script opened an unexpected path: %s' % path)
        self.log.append((k, mode))
        return FakeFile(self, k, mode, encoding, newline)

class FakeFile:
    def __init__(self, fs, k, mode, encoding, newline):
        self.fs, self.k, self.mode, self.enc, self.nl = fs, k, mode, encoding, newline
        if 'w' in mode:
            fs.files[k] = b''
        elif k not in fs.files:
            raise FileNotFoundError(k)
    def read(self):
        d = self.fs.files[self.k]
        if 'b' in self.mode:
            return d
        s = d.decode(self.enc or 'cp1252')
        return s.replace('\r\n', '\n').replace('\r', '\n') if self.nl is None else s
    def write(self, x):
        if 'b' not in self.mode:
            if self.nl is None:
                x = x.replace('\n', '\r\n')
            elif self.nl in ('\r', '\r\n'):
                x = x.replace('\n', self.nl)
            x = x.encode(self.enc or 'cp1252')
        self.fs.files[self.k] += x
        return len(x)
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False

def run_script(code, fname, state):
    fs = FakeFS({k: v.encode('utf-8') for k, v in state.items() if v is not None})
    printed = []
    g = {'__name__': '__main__', '__builtins__': builtins, 'open': fs.open,
         'print': lambda *a, **kw: printed.append(' '.join(str(x) for x in a))}
    exec(compile(code, fname, 'exec'), g)
    new = {}
    for k, b in fs.files.items():
        new[k] = b.decode('utf-8')
    return new, printed, fs.log

# ---------------------------------------------------------------- event list
events = [p for p in pairs if touches(p)]
say('=' * 100)
say('RECOVERY REPORT  (generated %s by build/agent2/recover-notes.py)' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
say('Transcript: %s (%d rows, %d tool calls paired with results)' % (TRANSCRIPT, len(rows), len(pairs)))
say('Wipe cut-off: %s local. Writes at or after it are excluded.' % WIPE.strftime('%H:%M:%S'))
say('=' * 100)
say('')
say('1. EVENTS touching the two notes files or the splice scripts (in transcript order)')
say('   step  call time  result time  tool         target  description')
for p in events:
    a, t, res = p['args'], touches(p), p['res']
    rt = res_time(res)
    if p['name'] == 'write_file':
        d = 'write %s chars%s%s' % (len(a.get('Content', '')), ' Overwrite' if a.get('Overwrite') else '', ' Append' if a.get('Append') else '')
    elif p['name'] == 'edit_file':
        d = 'edit Target %d chars -> %d chars: %r' % (len(a.get('Target', '')), len(a.get('Replacement', '')), a.get('Target', '')[:60])
    elif p['name'] == 'read_file':
        d = 'read lines %s-%s' % (a.get('StartLine', 1), a.get('EndLine', 'end'))
    else:
        d = '%s: %s' % (classify_cmd(a.get('CommandLine', '')), a.get('CommandLine', '')[:110].replace('\n', ' '))
    if t == 'SCRIPT':
        t = os.path.basename(a['Path'])
    first = (body(res) or '').split('\n')[0][:90]
    flag = ' ERROR' if is_err(res) else ''
    say('   S%-4d %s   %s     %-12s %-6s  %s' % (p['step'], p['time'].strftime('%H:%M:%S'), rt.strftime('%H:%M:%S') if rt else '   -    ', p['name'], t, d))
    say('%s-> %s%s' % (' ' * 30, first, flag))
say('')

# ---------------------------------------------------------------- calibration of the read_file rendering
say('2. CALIBRATION: read_file output vs. exact write_file content of the same file (nothing changed in between)')
def find(step, name, path_end=None):
    for p in pairs:
        if p['step'] == step and p['name'] == name and (path_end is None or p['args'].get('Path', '').endswith(path_end)):
            return p
    raise KeyError((step, name, path_end))
calib_ok = True
for wstep, wend, rstep in ((333, 'splice-notes.py', 484), (319, 'notes-top.md', 323), (496, 'notes-top.md', 501)):
    w = find(wstep, 'write_file', wend)['args']['Content']
    r = find(rstep, 'read_file', wend)
    a, b, n, ls = parse_read(body(r['res']))
    same = (ls == file_lines(w)) and n == len(file_lines(w))
    calib_ok &= same
    say('   S%d write %s (%d chars, ends with LF=%s, %d LFs) vs S%d read (%d-%d of %d): %s' % (
        wstep, wend, len(w), w.endswith('\n'), w.count('\n'), rstep, a, b, n, 'IDENTICAL lines' if same else 'DIFFERENT'))
say('   => read_file shows each line verbatim after "N: ", and a final LF does not add a line.' if calib_ok else '   => CALIBRATION FAILED')
say('')

# ---------------------------------------------------------------- replay
say('3. REPLAY')
state = {'BASE': None, 'TOP': None}
scripts = {}            # name -> code as written in the transcript
issues = []
checks = []

def check(label, ok, detail=''):
    checks.append((label, ok))
    say('   [%s] %s%s' % ('OK' if ok else 'MISMATCH', label, (' - ' + detail) if detail else ''))

def check_read(p, k):
    a, b, n, ls = parse_read(body(p['res']))
    cur = file_lines(state[k])
    ok = n == len(cur) and cur[a - 1:b] == ls
    detail = 'lines %d-%d of %d; state has %d lines' % (a, b, n, len(cur))
    if not ok:
        for i, l in enumerate(ls, a):
            if i > len(cur) or cur[i - 1] != l:
                detail += '; first diff at line %d: read=%r state=%r' % (i, l[:70], cur[i - 1][:70] if i <= len(cur) else None)
                break
    check('S%d read_file %s %s' % (p['step'], NAME[k], 'checkpoint'), ok, detail)

def check_numbered(p, k, text, label):
    """Select-String style lines 'N: prefix' in a command output must prefix-match state line N."""
    cur = file_lines(state[k])
    n_ok = n_all = 0
    bad = []
    for l in text.split('\n'):
        l = l.rstrip('\r')
        m = re.match(r'^\s*(\d+): (.*)$', l)
        if not m:
            continue
        i, pre = int(m.group(1)), m.group(2)
        n_all += 1
        if 1 <= i <= len(cur) and cur[i - 1].startswith(pre):
            n_ok += 1
        else:
            bad.append((i, pre[:50]))
    check('S%d %s: %d/%d numbered lines match' % (p['step'], label, n_ok, n_all), n_ok == n_all and n_all > 0,
          ('bad: %r' % bad[:3]) if bad else '')

base_start = None
for p in events:
    k = touches(p)
    a, res = p['args'], p['res']
    rt = res_time(res) or p['time']
    tag = 'S%d %s' % (p['step'], p['time'].strftime('%H:%M:%S'))
    cl = a.get('CommandLine', '')
    if rt >= WIPE or (p['name'] == 'run_command' and classify_cmd(cl).startswith('WRITER (inline')):
        if classify_cmd(cl).startswith('WRITER') or p['name'] in ('write_file', 'edit_file'):
            say('   %s EXCLUDED (the wipe / after the cut-off): %s' % (tag, cl[:160] or p['name']))
            m = re.findall(r"replace\(b'([^']*)',b'([^']*)'\)", cl)
            if m:
                say('       intended byte replacements (NOT applied): %s' % '; '.join('%r -> %r' % x for x in m))
                intended = m
        continue
    if k == 'SCRIPT':
        if p['name'] == 'write_file':
            scripts[os.path.basename(a['Path'])] = a['Content']
            say('   %s %s written (%d chars) - kept for replay' % (tag, os.path.basename(a['Path']), len(a['Content'])))
        continue
    if p['name'] == 'read_file':
        pr = parse_read(body(res))
        if state[k] is None:
            ra, rb, rn, ls = pr
            if ra == 1 and rb == rn:
                state[k] = '\n'.join(ls) + '\n'
                base_start = base_start or (p['step'], rt)
                say('   %s START %s from full read_file (%d lines; final LF assumed, verified by later counts)' % (tag, NAME[k], rn))
            continue
        # duplicate full reads before any change are also checkpoints
        check_read(p, k)
        continue
    if p['name'] == 'write_file':
        if is_err(res):
            issues.append('%s write_file %s failed: %s' % (tag, NAME[k], body(res)[:120]))
            continue
        c = a.get('Content', '')
        state[k] = (state[k] or '') + c if a.get('Append') else c
        say('   %s write_file %s: %d chars, %d lines%s' % (tag, NAME[k], len(c), len(file_lines(c)), ' (Overwrite)' if a.get('Overwrite') else ''))
        continue
    if p['name'] == 'edit_file':
        T, Rp = a.get('Target', ''), a.get('Replacement', '')
        cnt = state[k].count(T) if state[k] is not None else -1
        if is_err(res):
            issues.append('%s edit_file %s FAILED in the original run (tool said: %s). Not applied; state has %d occurrence(s) of the Target.'
                          % (tag, NAME[k], body(res)[:100], cnt))
            say('   %s edit_file %s: tool reported an error in the original run -> skipped (Target occurs %d time(s) in state)' % (tag, NAME[k], cnt))
            continue
        m = re.search(r'Made (\d+) replacement', body(res))
        want = int(m.group(1)) if m else None
        if cnt <= 0:
            issues.append('%s edit_file %s: Target NOT FOUND in replayed state (tool said %s replacement(s))' % (tag, NAME[k], want))
            say('   %s edit_file %s: TARGET NOT FOUND' % (tag, NAME[k]))
            continue
        if want is not None and cnt != want:
            issues.append('%s edit_file %s: Target occurs %d times, tool reported %d' % (tag, NAME[k], cnt, want))
        state[k] = state[k].replace(T, Rp)
        say('   %s edit_file %s: %d occurrence(s) replaced (tool reported %s); now %d lines' % (tag, NAME[k], cnt, want, len(file_lines(state[k]))))
        continue
    if p['name'] == 'run_command':
        kind = classify_cmd(cl)
        out = body(res) or ''
        if kind.startswith('WRITER (runs'):
            sname = re.search(r'(splice-notes\d?\.py)', kind).group(1)
            code = scripts.get(sname)
            disk = open(SCRIPTS[sname], encoding='utf-8').read() if os.path.exists(SCRIPTS[sname]) else None
            say('   %s run %s (transcript copy %d chars; on-disk copy %s)' % (tag, sname, len(code),
                'identical' if disk == code else ('DIFFERENT' if disk is not None else 'missing')))
            new, printed, log = run_script(code, sname, state)
            changed = [kk for kk in new if new[kk] != state[kk]]
            for kk in new:
                state[kk] = new[kk]
            say('       script printed: %s' % ' | '.join(printed))
            say('       files written by the script: %s' % ', '.join(NAME[kk] for kk in changed))
            # the script's own print in the original run (from the command output or the task-finished message)
            orig = re.search(r'ok crlf=\S+ chars=\d+ lines=\d+ \S+', out)
            if not orig:
                for o in rows:
                    if o['type'] == 'SYSTEM_MESSAGE' and int(o['step_index']) > p['step'] and 'ok crlf=' in (o.get('content') or '') and sname in json.dumps(a) :
                        orig = re.search(r'ok crlf=\S+ chars=\d+ lines=\d+ \S+', o['content'])
                        out = o['content']
                        if orig:
                            break
            check('%s %s output equals the original run' % (tag, sname), bool(orig) and printed and printed[0] == orig.group(0),
                  'original: %s' % (orig.group(0) if orig else 'not found'))
            check_numbered(p, 'BASE', out.split('ok crlf=')[1] if 'ok crlf=' in out else out, 'post-run Select-String output')
            if sname == 'splice-notes2.py':
                cur = file_lines(state['BASE'])
                o_lines = [l.rstrip('\r') for l in out.split('\n')]
                def seq(lbl, start, n):
                    i = o_lines.index(lbl) + 1 if lbl else None
                    return i
                try:
                    i = o_lines.index('lines=%d' % len(cur))
                    check('%s Get-Content count lines=%d' % (tag, len(cur)), True)
                    check('%s first 3 lines printed by the command' % tag, o_lines[i + 1:i + 4] == cur[0:3])
                    mi = [l for l in o_lines if l.startswith('marker at line ')][0]
                    mk = int(mi.split()[-1]); j = o_lines.index(mi)
                    check('%s marker at line %d; lines %d-%d printed' % (tag, mk, mk - 2, mk + 1), cur[mk - 1] == 'Problems and fixes (session 3):' and o_lines[j + 1:j + 5] == cur[mk - 3:mk + 1])
                    ii = [l for l in o_lines if l.startswith('item15 at ')][0]
                    k15 = int(ii.split()[-1]); j = o_lines.index(ii)
                    check('%s item15 at line %d; lines %d-%d printed' % (tag, k15, k15 - 2, k15 + 2), o_lines[j + 1:j + 6] == cur[k15 - 3:k15 + 2])
                except (ValueError, IndexError) as e:
                    check('%s context lines of the splice-2 output' % tag, False, repr(e))
            continue
        if kind == 'reader' and state.get('BASE') is not None and 'agent2-baseline' in cl and res is not None:
            m = re.match(r'Command exited with code 0\.\n\nCommand output:\n(\d+)\r?\nlines=(\d+)', out)
            if m:
                check('S%d Get-Item Length=%s bytes, Get-Content lines=%s' % (p['step'], m.group(1), m.group(2)),
                      int(m.group(1)) == len(state['BASE'].encode('utf-8')) and int(m.group(2)) == len(file_lines(state['BASE'])),
                      'state: %d bytes, %d lines' % (len(state['BASE'].encode('utf-8')), len(file_lines(state['BASE']))))
            if re.search(r'^\s*\d+: ', out, re.M):
                check_numbered(p, 'BASE', out, 'read-only command output')
            else:
                say('   %s read-only command, no line-numbered output to check' % tag)
            continue
        if kind == 'reader':
            say('   %s read-only command (%s) - nothing to replay' % (tag, cl[:70]))
            continue
        issues.append('%s run_command classified %s - review: %s' % (tag, kind, cl[:150]))

say('')
# ---------------------------------------------------------------- other writers on disk
say('4. OTHER SCRIPTS in build/agent2 that name the notes files (possible writers outside the transcript)')
for fn in sorted(os.listdir(R + r'\build\agent2')):
    fp = os.path.join(R, 'build', 'agent2', fn)
    if os.path.isfile(fp) and fn.lower().endswith(('.py', '.ps1')) and fn != 'recover-notes.py':
        s = open(fp, encoding='utf-8', errors='replace').read()
        if 'agent2-baseline' in s or 'notes-top' in s:
            say('   %s names a notes file (%s, file mtime %s)' % (fn, 'replayed above' if fn in SCRIPTS else 'not replayed; matching lines below',
                datetime.datetime.fromtimestamp(os.path.getmtime(fp)).strftime('%H:%M:%S')))
            if fn not in SCRIPTS:
                for i, l in enumerate(s.split('\n'), 1):
                    if 'agent2-baseline' in l or 'notes-top' in l:
                        say('      %d: %s' % (i, l.strip()[:170]))
say('')

# ---------------------------------------------------------------- results
os.makedirs(OUT, exist_ok=True)
say('5. RESULT')
for k, fn in (('BASE', 'agent2-baseline.md'), ('TOP', 'notes-top.md')):
    s = state[k]
    open(os.path.join(OUT, fn), 'wb').write(s.encode('utf-8'))
    say('   %s -> %s' % (NAME[k], os.path.join(OUT, fn)))
    say('      chars=%d lines(LF count)=%d bytes=%d CRLF=%s ends-with-LF=%s' % (len(s), s.count('\n'), len(s.encode('utf-8')), '\r\n' in s, s.endswith('\n')))
b = state['BASE']
bl = file_lines(b)
say('   expected for agent2-baseline.md: chars=%d lines=%d -> %s' % (EXPECT_CHARS, EXPECT_LINES,
    'MATCH' if (len(b), b.count('\n')) == (EXPECT_CHARS, EXPECT_LINES) else 'DIFFERENT'))
say('   top line: %s' % bl[0])
say('   top block says "updated 19:57": %s' % ('updated 19:57)' in bl[0]))
nums = [int(m.group(1)) for m in (re.match(r'^(\d+)\. ', l) for l in bl[bl.index('Problems and fixes (session 3):'):]) if m]
run = []
for n in nums:
    if run and n != run[-1] + 1:
        break
    run.append(n)
say('   "Problems and fixes (session 3):" at line %d; numbered items there: %s' % (bl.index('Problems and fixes (session 3):') + 1, run))
say('   items 1-20 in order: %s' % (run == list(range(1, 21))))
say('   notes-top.md equals the top block of agent2-baseline.md: %s' % (b.startswith(state['TOP'].rstrip('\n') + '\n\nProblems and fixes (session 3):')))
for k in ('BASE', 'TOP'):
    for x, y in globals().get('intended', []):
        say('   %s: %r occurs %d time(s) (the wipe meant to change it to %r)' % (NAME[k], x, state[k].count(x), y))
say('')
say('6. CHECKS: %d run, %d OK, %d mismatched' % (len(checks), sum(1 for c in checks if c[1]), sum(1 for c in checks if not c[1])))
for c in checks:
    if not c[1]:
        say('   MISMATCH: %s' % c[0])
say('')
say('7. EDITS NOT APPLIED / AMBIGUOUS / REVIEW')
for i in issues or ['none']:
    say('   ' + i)
open(os.path.join(OUT, 'REPORT.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(rep) + '\n')
