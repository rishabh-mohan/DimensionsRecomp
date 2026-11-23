#!/usr/bin/env python3
"""Stage S4-T1 (#21, LEGO_NATIVE_CHAIN_PRIORITY) against the S4b sources that native4b is built from.

Agent 7, task #17 (2026-11-22). Stdlib only. Read-only on the source tree; writes only under
build/agent7/s4-t1/. No compile, no git. Run from anywhere (Below Normal):

    python -B build/agent7/s4-t1/make_s4t1.py

Source dir = CMAKE_HOME_DIRECTORY of build/agent2/snap1-on/CMakeCache.txt
           = build/agent2/snap1/DimensionsRecomp/rexlego
Writes: before/ and after/ copies (src/gpu_native/...), s4-t1.diff (paths relative to the source dir,
a/src/gpu_native/..., CRLF content lines exactly as the files), SHA256SUMS.txt, make_s4t1.out.txt.
Exit 0 only if every anchor matched once at its expected line and every proof below passed.

Revision 2 (22:50, review S1 in check/DIFF-REVIEW.md): native_preparation.h no longer declares an external
function. It holds an inline hook pointer (null) and an inline wrapper; native_worker.cpp defines the static
ApplyNativeChainPriorityImpl and installs the hook during static initialization. Builds that compile
native_recording.cpp / native_preparation.h without native_worker.cpp (gpu-aot fixtures) link as before.
"""
import difflib
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SRC = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexlego')
REL = 'src/gpu_native'
FILES = ['native_worker.cpp', 'native_recording.cpp', 'native_preparation.h']
BEFORE_SHA = {
    'native_worker.cpp': '7157E8F2EDC3D5C438E3F2F21B50051693A3046B36A4BD8EE096901DF8FE0E2F',
    'native_recording.cpp': '48F0C429DDB89E452794365788C8B34EA9510A4B10B86F93771F418F3E53AA9B',
    'native_preparation.h': '889F3FA6F207011B03D044E745C2952C68200A44C99BE6E13EB810357D3D41A5',
}
CALL = 'ApplyNativeChainPriority('

HELPER = [
    '// S4-T1 (#21) test bed, default off. LEGO_NATIVE_CHAIN_PRIORITY: 1 = THREAD_PRIORITY_ABOVE_NORMAL,',
    '// 2 = EcoQoS opt-out (power throttling control on, execution-speed throttling off), 3 = both.',
    '// Unset: no log line and no Win32 call. Any other value: off, with one log line. Each chain thread',
    '// reaches this through ApplyNativeChainPriority (native_preparation.h) right after naming itself.',
    'static void ApplyNativeChainPriorityImpl(const char* role) {',
    '  static const unsigned mode = [] {',
    '    const char* value = std::getenv("LEGO_NATIVE_CHAIN_PRIORITY");',
    '    if (!value) return 0u;',
    "    const unsigned parsed = value[0] >= '1' && value[0] <= '3' && value[1] == '\\0' ? unsigned(value[0] - '0') : 0u;",
    '    static const char* const kModes[] = {"off", "priority", "EcoQoS opt-out", "priority + EcoQoS opt-out"};',
    '    REXLOG_INFO("Native GPU: chain priority mode {}: {} (LEGO_NATIVE_CHAIN_PRIORITY={})", parsed, kModes[parsed], value);',
    '    return parsed;',
    '  }();',
    '  if (mode == 0) return;',
    '  const HANDLE self = GetCurrentThread();',
    '  const bool priority_ok = (mode & 1u) == 0 || SetThreadPriority(self, THREAD_PRIORITY_ABOVE_NORMAL) != 0;',
    '  const char* ecoqos = "unchanged";',
    '  if (mode & 2u) {',
    '    THREAD_POWER_THROTTLING_STATE state{};',
    '    state.Version = THREAD_POWER_THROTTLING_CURRENT_VERSION;',
    '    state.ControlMask = THREAD_POWER_THROTTLING_EXECUTION_SPEED;',
    '    state.StateMask = 0;',
    '    ecoqos = SetThreadInformation(self, ThreadPowerThrottling, &state, sizeof(state)) ? "opt-out" : "opt-out failed";',
    '  }',
    '  static std::atomic<unsigned> logged{0};',
    '  if (logged.fetch_add(1, std::memory_order_relaxed) < 16)',
    '    REXLOG_INFO("Native GPU: chain priority {} tid={} priority={}{} ecoqos={}", role, GetCurrentThreadId(),',
    '                GetThreadPriority(self), priority_ok ? "" : " (set failed)", ecoqos);',
    '}',
    '',
    '// Installs the native_preparation.h hook during static initialization, before main and so before any',
    '// chain thread exists. The settings are per thread and end with the thread.',
    '[[maybe_unused]] const bool g_native_chain_priority_installed = [] {',
    '  g_native_chain_priority = &ApplyNativeChainPriorityImpl;',
    '  return true;',
    '}();',
    '',
]
INSTALLER_START = '[[maybe_unused]] const bool g_native_chain_priority_installed = [] {'

DECL = [
    '',
    '// S4-T1 (#21): opt-in scheduling for the native GPU chain threads. Each chain thread calls',
    '// ApplyNativeChainPriority on itself right after naming itself. native_worker.cpp installs the hook before',
    '// main; builds without native_worker.cpp (the offline gpu-aot fixtures) keep it null, so the call is a no-op.',
    'inline void (*g_native_chain_priority)(const char* role) = nullptr;',
    'inline void ApplyNativeChainPriority(const char* role) {',
    '  if (auto* apply = g_native_chain_priority) apply(role);',
    '}',
]
HOOK_DECL = 'inline void (*g_native_chain_priority)(const char* role) = nullptr;'
WRAPPER_START = 'inline void ApplyNativeChainPriority(const char* role) {'

# (file, anchor text, expected 1-based line of the anchor, offset (insert after anchor+offset), new lines,
#  extra context checks {line: text}, label)
EDITS = [
    ('native_preparation.h', 'namespace legodimensions::gpu_native {', 13, 0, DECL,
     {14: '', 15: '// Jobs retain captured state and serialize mutable resource access.'}, 'declaration'),
    ('native_preparation.h', '    SetThreadDescription(GetCurrentThread(), name.c_str());', 26, 0,
     ['    ApplyNativeChainPriority("prepare");'],
     {24: '  void Run(unsigned index) {'}, 'prep pool thread "Native GPU prepare N"'),
    ('native_recording.cpp', '    SetThreadDescription(GetCurrentThread(), L"Native GPU recording");', 112, 0,
     ['    ApplyNativeChainPriority("recording queue");'],
     {111: '  void Run() {', 138: '  RecordingQueue() { worker_ = std::thread([this] { Run(); }); }'},
     'RecordingQueue thread "Native GPU recording" (th2-type)'),
    ('native_worker.cpp', '#include "gpu_native/fsr3_settings.h"', 5, 0,
     ['#include "gpu_native/native_preparation.h"'], {6: '', 7: '#include <windows.h>'}, 'include'),
    ('native_worker.cpp', '  SetThreadDescription(GetCurrentThread(), L"Native GPU recording");', 154, 0,
     ['  ApplyNativeChainPriority("recorder");'],
     {152: 'void RecorderMain() {', 153: '  t_on_recorder = true;'}, 'RecorderMain (th3)'),
    ('native_worker.cpp', '  SetThreadDescription(GetCurrentThread(), L"Native GPU preparation");', 199, 0,
     ['  ApplyNativeChainPriority("coordinator");'], {198: 'void CoordinatorMain() {'},
     'CoordinatorMain (th3 worker thread)'),
    ('native_worker.cpp',
     '  SetThreadDescription(GetCurrentThread(), NativePrepareEnabled() ? L"Native GPU preparation" : L"Native GPU recording");',
     261, 0, ['  ApplyNativeChainPriority("worker");'],
     {259: 'void WorkerMain() {', 260: '  if (NativeFullDrawPreparationEnabled()) { CoordinatorMain(); return; }'},
     'WorkerMain (th2 worker thread)'),
    ('native_worker.cpp',
     '    REXLOG_INFO("Native GPU: threaded recording {}", on ? "ON (LEGO_NATIVE_THREADED=1)" : "off");', 323, 5,
     HELPER, {319: 'bool NativeWorkerEnabled() {', 327: '}', 328: '', 329: 'bool NativeWorkerStarted() {',
              299: '}  // namespace'}, 'helper definition (named namespace, after NativeWorkerEnabled)'),
]

out_lines = []


def log(msg=''):
    print(msg)
    out_lines.append(msg)


def fail(msg):
    log('FAIL: ' + msg)
    write_out()
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def write_out():
    with open(os.path.join(HERE, 'make_s4t1.out.txt'), 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(out_lines) + '\n')


def split_crlf(data, name):
    if not data.endswith(b'\r\n'):
        fail(f'{name}: does not end with CRLF')
    body = data[:-2].split(b'\r\n')
    for i, line in enumerate(body, 1):
        if b'\n' in line or b'\r' in line:
            fail(f'{name}:{i}: lone CR/LF (mixed line endings)')
    return body


def main():
    log('make_s4t1.py: S4-T1 (#21) staging against ' + os.path.relpath(SRC, ROOT).replace('\\', '/'))
    originals, results, inserted_idx = {}, {}, {}
    for name in FILES:
        path = os.path.join(SRC, *REL.split('/'), name)
        with open(path, 'rb') as f:
            data = f.read()
        if sha(data) != BEFORE_SHA[name]:
            fail(f'{name}: before sha256 {sha(data)} != expected {BEFORE_SHA[name]}')
        originals[name] = data
    for name in FILES:
        lines = [l.decode('ascii') for l in split_crlf(originals[name], name)]
        edits = [e for e in EDITS if e[0] == name]
        plan = []
        for (_, anchor, exp, off, new, ctx, label) in edits:
            hits = [i + 1 for i, l in enumerate(lines) if l == anchor]
            if hits != [exp]:
                fail(f'{name}: anchor for {label!r} found at {hits}, expected exactly [{exp}]')
            for ln, text in ctx.items():
                if lines[ln - 1] != text:
                    fail(f'{name}:{ln}: context mismatch for {label!r}: {lines[ln - 1]!r} != {text!r}')
            for t in new:
                t.encode('ascii')
            plan.append((exp + off, new, label))
        plan.sort(key=lambda p: p[0])
        after, idx, prev = [], [], 0
        for at, new, label in plan:
            after.extend(lines[prev:at])
            start = len(after)
            after.extend(new)
            idx.extend(range(start, start + len(new)))
            log(f'  {name}: +{len(new):2d} lines after before-L{at} (after-L{start + 1}-L{start + len(new)}): {label}')
            prev = at
        after.extend(lines[prev:])
        results[name] = after
        inserted_idx[name] = set(idx)

    # Write before/after copies and the diff.
    diff_chunks = []
    sums = []
    for name in FILES:
        before_b = originals[name]
        after_b = ('\r\n'.join(results[name]) + '\r\n').encode('ascii')
        for side, data in (('before', before_b), ('after', after_b)):
            d = os.path.join(HERE, side, *REL.split('/'))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, name), 'wb') as f:
                f.write(data)
        sums.append((sha(before_b), f'before/{REL}/{name}', len(before_b), before_b.count(b'\r\n')))
        sums.append((sha(after_b), f'after/{REL}/{name}', len(after_b), after_b.count(b'\r\n')))
        a = [l + '\r\n' for l in before_b.decode('ascii')[:-2].split('\r\n')]
        b = [l + '\r\n' for l in results[name]]
        ud = list(difflib.unified_diff(a, b, f'a/{REL}/{name}', f'b/{REL}/{name}', n=3, lineterm='\n'))
        diff_chunks.append(f'diff --git a/{REL}/{name} b/{REL}/{name}\n')
        diff_chunks.extend(ud)
    diff_b = ''.join(diff_chunks).encode('ascii')
    with open(os.path.join(HERE, 's4-t1.diff'), 'wb') as f:
        f.write(diff_b)

    # ---- Proofs ----
    log('')
    log('PROOF 1 (additive only): difflib opcodes are equal/insert only; 0 deleted or changed lines')
    total_plus = 0
    for name in FILES:
        a = originals[name][:-2].split(b'\r\n')
        b = [l.encode('ascii') for l in results[name]]
        ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
        bad = [o for o in ops if o[0] not in ('equal', 'insert')]
        if bad:
            fail(f'{name}: non-insert opcodes {bad}')
        plus = sum(j2 - j1 for (t, i1, i2, j1, j2) in ops if t == 'insert')
        if plus != len(inserted_idx[name]):
            fail(f'{name}: difflib inserts {plus} != planned {len(inserted_idx[name])}')
        total_plus += plus
        log(f'  {name}: +{plus} -0')
    dl = diff_b.split(b'\n')
    n_plus = sum(1 for l in dl if l.startswith(b'+') and not l.startswith(b'+++'))
    n_minus = sum(1 for l in dl if l.startswith(b'-') and not l.startswith(b'---'))
    if n_plus != total_plus or n_minus != 0:
        fail(f's4-t1.diff: +{n_plus} -{n_minus}, expected +{total_plus} -0')
    log(f'  s4-t1.diff: +{n_plus} -{n_minus}')

    log('PROOF 2 (reversible): removing the inserted lines from after/ gives the before bytes (sha256 equal)')
    for name in FILES:
        kept = [l for i, l in enumerate(results[name]) if i not in inserted_idx[name]]
        rebuilt = ('\r\n'.join(kept) + '\r\n').encode('ascii')
        if rebuilt != originals[name]:
            fail(f'{name}: stripped after != before')
        log(f'  {name}: {sha(rebuilt)} == before')

    log('PROOF 3 (call sites): inside pre-existing code the only inserted statements are')
    log('  ApplyNativeChainPriority("<literal>"); each directly after the thread\'s SetThreadDescription line')
    calls = 0
    blocks = {}
    for name, block in (('native_worker.cpp', HELPER), ('native_preparation.h', DECL)):
        after = results[name]
        first = next(k for k, l in enumerate(block) if l.strip())
        hits = [i for i, l in enumerate(after) if l == block[first]]
        if len(hits) != 1:
            fail(f'{name}: block start {block[first]!r} found {len(hits)} times')
        start = hits[0] - first
        span = set(range(start, start + len(block)))
        if after[start:start + len(block)] != block or not span <= inserted_idx[name]:
            fail(f'{name}: new block is not contiguous, identical and fully inserted')
        blocks[name] = span
        log(f'  {name} after-L{start + 1}-L{start + len(block)}: new block ({len(block)} lines, all inserted)')
    for name in FILES:
        after = results[name]
        for i in sorted(inserted_idx[name]):
            line = after[i]
            if i in blocks.get(name, set()):
                continue
            s = line.strip()
            if s.startswith(CALL):
                if not (s.endswith('");') and s.count('"') == 2):
                    fail(f'{name}: call is not a single string literal: {line!r}')
                if 'SetThreadDescription(GetCurrentThread(), ' not in after[i - 1]:
                    fail(f'{name}: call not directly after SetThreadDescription: {after[i - 1]!r}')
                calls += 1
                log(f'  {name} after-L{i + 1}: {s}   <- after-L{i}: {after[i - 1].strip()[:70]}')
            elif s == '' or s.startswith('//') or s == '#include "gpu_native/native_preparation.h"':
                continue
            else:
                fail(f'{name}: unexpected inserted statement {line!r}')
    if calls != 5:
        fail(f'expected 5 call sites, got {calls}')
    log(f'  call sites: {calls} (prepare, recording queue, recorder, coordinator, worker)')

    log('PROOF 4 (unset path): in the helper, the unset return precedes the first log, and')
    log('  "if (mode == 0) return;" precedes every Win32 call and the per-thread log')
    h = HELPER
    i_unset = h.index('    if (!value) return 0u;')
    i_log1 = next(i for i, l in enumerate(h) if 'REXLOG_INFO' in l)
    i_ret = h.index('  if (mode == 0) return;')
    win32 = [i for i, l in enumerate(h) if any(k in l for k in (
        'GetCurrentThread', 'SetThreadPriority', 'SetThreadInformation', 'GetThreadPriority', 'GetCurrentThreadId'))]
    logs2 = [i for i, l in enumerate(h) if 'REXLOG_INFO' in l][1:]
    if not (i_unset < i_log1 < i_ret and all(i > i_ret for i in win32 + logs2)):
        fail('helper statement order')
    first_stmt = [l for l in h[5:] if l.strip()][0]
    if first_stmt.strip() != 'static const unsigned mode = [] {':
        fail('helper does not start with the mode guard')
    log(f'  unset return at helper L{i_unset + 1} < first log L{i_log1 + 1} < "mode == 0" return L{i_ret + 1}'
        f' < Win32 calls L{min(win32) + 1}-L{max(win32) + 1} and per-thread log L{logs2[0] + 1}')
    if h[4] != 'static void ApplyNativeChainPriorityImpl(const char* role) {':
        fail('helper function line')
    wrap = [l.strip() for l in DECL[DECL.index(WRAPPER_START) + 1:] if l.strip()]
    if HOOK_DECL not in DECL or wrap != ['if (auto* apply = g_native_chain_priority) apply(role);', '}']:
        fail('header wrapper is not a single null-checked forward to the hook')
    inst = [l.strip() for l in h[h.index(INSTALLER_START) + 1:] if l.strip()]
    if inst != ['g_native_chain_priority = &ApplyNativeChainPriorityImpl;', 'return true;', '}();']:
        fail('installer does more than store the hook')
    if h.index(INSTALLER_START) < max(win32 + logs2):
        fail('installer is not after the helper body')
    log('  header wrapper ApplyNativeChainPriority: one statement, calls the hook only when it is set; the hook')
    log('  starts null (constant init); native_worker.cpp\'s installer only stores &ApplyNativeChainPriorityImpl')
    log('  (no Win32 call, no log, before main). So with the variable unset, legodimensions reaches only the')
    log('  getenv-then-return above, and builds without native_worker.cpp make no call at all')

    log('PROOF 5 (untouched): existing lines still present exactly once')
    w = results['native_worker.cpp']
    for text in ('    SetThreadPriority(g_thread.native_handle(), THREAD_PRIORITY_ABOVE_NORMAL);',
                 '    if (NativeFullDrawPreparationEnabled()) g_recorder_thread = std::thread(RecorderMain);',
                 '    g_thread = std::thread(WorkerMain);',
                 '  if (g_thread.joinable()) g_thread.join();',
                 '  if (g_recorder_thread.joinable()) g_recorder_thread.join();'):
        if w.count(text) != 1:
            fail(f'native_worker.cpp: {text.strip()!r} count {w.count(text)}')
        log(f'  native_worker.cpp after-L{w.index(text) + 1}: {text.strip()}')
    for name in FILES:
        n = sum(l.count('SetThreadPriority(') for l in results[name]) - \
            sum(l.count('SetThreadPriority(') for l in originals[name].decode('ascii').split('\r\n'))
        log(f'  {name}: SetThreadPriority( occurrences added = {n} (only inside the helper)')
    # no process-wide calls anywhere in the inserted text
    added_text = '\n'.join(results[n][i] for n in FILES for i in inserted_idx[n])
    for k in ('SetPriorityClass', 'SetProcessInformation', 'timeBeginPeriod', 'SetThreadAffinityMask',
              'SetProcessAffinityMask', 'SetThreadSelectedCpuSets', 'PowerSetRequest', 'Reg'):
        if k in added_text:
            fail(f'inserted text contains {k}')
    log('  inserted text has no process-wide/system calls (SetPriorityClass, SetProcessInformation, timeBeginPeriod,')
    log('  affinity/CPU-set calls, power requests, registry)')

    log('PROOF 6 (link closure, review S1): the header and native_recording.cpp add only inline entities and calls,')
    log('  so a build that compiles them without native_worker.cpp (the gpu-aot fixtures) needs no new symbol')
    added = {n: [results[n][i].strip() for i in sorted(inserted_idx[n])] for n in FILES}
    hdr_code = [s for s in added['native_preparation.h'] if s and not s.startswith('//')]
    if hdr_code != [HOOK_DECL, WRAPPER_START, 'if (auto* apply = g_native_chain_priority) apply(role);', '}',
                    'ApplyNativeChainPriority("prepare");']:
        fail(f'native_preparation.h inserted code {hdr_code}')
    if added['native_recording.cpp'] != ['ApplyNativeChainPriority("recording queue");']:
        fail(f'native_recording.cpp inserted {added["native_recording.cpp"]}')
    impl_refs = [(n, i + 1) for n in FILES for i, l in enumerate(results[n]) if 'ApplyNativeChainPriorityImpl' in l]
    if len(impl_refs) != 2 or any(n != 'native_worker.cpp' for n, _ in impl_refs):
        fail(f'ApplyNativeChainPriorityImpl references {impl_refs}')
    for n in FILES:
        before_text = originals[n].decode('ascii')
        for k in ('g_native_chain_priority', 'ApplyNativeChainPriority'):
            if k in before_text:
                fail(f'{n}: {k} already present before the change')
    log('  native_preparation.h adds: inline hook pointer (= nullptr), inline wrapper, 1 call (prepare)')
    log('  native_recording.cpp adds: 1 call (recording queue); no new include, no extern declaration anywhere')
    log(f'  ApplyNativeChainPriorityImpl (static) appears only in native_worker.cpp at after-L'
        f'{impl_refs[0][1]} (definition) and after-L{impl_refs[1][1]} (installer); no name existed before')

    with open(os.path.join(HERE, 'SHA256SUMS.txt'), 'w', encoding='ascii', newline='\n') as f:
        f.write('# S4-T1 (#21) staging, Agent 7 task #17. sha256 (upper hex), path, bytes, CRLF lines.\n')
        f.write('# before/ = byte copies of build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_native/*\n')
        for s, p, size, nl in sums:
            f.write(f'{s}  {p}  {size}  {nl}\n')
        f.write(f'{sha(diff_b)}  s4-t1.diff  {len(diff_b)}\n')
    log('')
    log('SHA256 (before -> after):')
    for k in range(0, len(sums), 2):
        log(f'  {FILES[k // 2]}: {sums[k][0]} ({sums[k][2]} B, {sums[k][3]} lines) -> '
            f'{sums[k + 1][0]} ({sums[k + 1][2]} B, {sums[k + 1][3]} lines)')
    log(f'  s4-t1.diff: {sha(diff_b)} ({len(diff_b)} B)')
    log('ALL PROOFS PASS')
    write_out()


if __name__ == '__main__':
    main()
