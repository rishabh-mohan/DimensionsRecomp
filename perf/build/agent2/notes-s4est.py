"""Agent 2 - task #30: insert the "S4 estimate (task #30)" section and a RESUME paragraph into
perf-notes/agent2-baseline.md. Anchored, counted replacements; refuses unless the notes are the expected
version (sha256 prefix 75425D29E26B67C5, LF only). Backup: build/agent2/notes-backup/agent2-baseline.md.HHMMSS.
Estimates only (no builds); sources: build/agent2/s4-estimate.py -> s4-estimate.txt."""
import hashlib, os, sys, textwrap, time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
BKDIR = os.path.join(R, 'build', 'agent2', 'notes-backup')
EXPECT = '75425D29E26B67C5'
HM = time.strftime('%H:%M')


def wrap_md(s, w=118):
    out = []
    for line in s.split('\n'):
        if line.startswith('|') or line.startswith('#') or line.strip() == '' or len(line) <= w:
            out.append(line)
        elif line.startswith('- '):
            out.append(textwrap.fill(line, w, subsequent_indent='  ', break_long_words=False,
                                     break_on_hyphens=False))
        else:
            out.append(textwrap.fill(line, w, break_long_words=False, break_on_hyphens=False))
    return '\n'.join(out)


H_OLD = ('# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 done, inventory done, standby; '
         'updated 06:20)\n')
H_NEW = ('# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 done, inventory done, task #30 estimates '
         'sent, standby; updated @HM@)\n')

P_ANCHOR = 'Delete nothing until Agent 1 or the user says so.**\n\n<!-- inventory:begin -->'
PARA = (
    '**Task #30 (Agent 11, 06:49): build-time and disk estimates for the first S4 batch, for '
    '`perf-notes/S4-DRAFT.md` (Agent 11\'s `@@done 30` is due 08:15). Estimates only, nothing built: section '
    '"S4 estimate (task #30)" below, done @HM@, from `build/agent2/s4-estimate.py` -> `s4-estimate.txt` '
    '(read-only ninja log/deps analysis); the summary line went to Agent 11. Agent 1 (~06:56): no builds and no '
    'new bin dirs tonight (S4 is not built tonight; Agent 4\'s s35 pack stays on scratch, no bin); reads and '
    'estimates are OK at <= 2 threads; tell Agent 1 before starting anything else; from 08:30 notes only. '
    'Agent 8: its last run ended 07:00:02 and its slot is over. Standby: nothing of mine is running, no timers; '
    'window 4 waits for the user (~10:00).**'
)

S_ANCHOR = '## Batches 1 and 2: run details (moved out of the RESUME block at 00:45)\n'
SECTION = r'''## S4 estimate (task #30, for Agent 11's `perf-notes/S4-DRAFT.md`; @HM@; estimates only, nothing built)

Method: `build/agent2/s4-estimate.py` (read-only) parses `.ninja_log` + `.ninja_deps` of my 5 trees (snap1-sdk, snap1-off, snap1-on, snapB-off, snapB3-on), finds every edge whose recorded deps contain a changed file (PCH users included) and takes compile wall at -j10 = PCH + max(work/10, longest TU). Full report: `build/agent2/s4-estimate.txt`. Calibration: for the S3d draw.cpp rebuild it predicts 58 s of compile; the measured build took 102.7 s, so fingerprint + link + ninja/custom overhead is ~45 s per native build. The logged TU times come from builds on a busy machine: +-30%. Ranges span the S3d line (snap1 trees) and the B line (snapB-off/snapB3-on), whichever S4 builds on.

**Cost driver: `rex/system/xmemory.h` is in the generated-code closure.** Through the PCH it reaches all 440 generated TUs (432 with codegen B), main.cpp and 18-22 rexlego TUs, plus 199 SDK TUs, so changing it is in effect a full rebuild of both game trees. `rex/thread/timer_queue.h` behaves the same (keep S4 to `timer_queue.cpp`). The other listed SDK headers (graphics/command_processor.h, shared_memory.h, d3d12/command_processor.h, deferred_command_list.h, pipeline_cache.h) are in no game TU's deps.

### (1) First S4 batch: SDK runtime files + gpu_native files + 1 new hook, every new switch OFF, no regen

| Step | xmemory.h changed (as listed) | xmemory.h unchanged (only the .cpp files + SDK-internal headers) |
|---|---|---|
| SDK (snap1-sdk, shared) | 200 edges, ~1,710 s work: ~4 min compile + ~25 s relinks (rexruntime.dll 18 s) + install 50-65 s = **~5-6 min** (cf. S1 SDK 269.6 s + install 50.9 s) | 18 edges (the 9 .cpp files alone: 127 s; longest d3d12/command_processor.cpp 36.5 s): ~36 s compile + relinks + install = **~2 min** |
| devoff | 460 edges on the S3d line (452 on B), 7,680 s work (10,020 on B): ~13 min compile (~17 min on B) + link 6 s + gen-check 61 s + gate 3 s + stage 16-25 s = **~15-19 min** (cf. full OFF builds: S1 789 s, B 1,039 s) | 0 game compile edges: re-run CMake + relink + gen-check + gate + stage = **~1.5-2 min** (cf. devoff3: 113.6 s incl. SDK, + stage 16.1 s) |
| native | 485 edges on the S3d line (477 on B3), 9,410-11,140 s work: ~16-19 min compile + fingerprint 8-14 s + link 4-8 s + re-run CMake 7-25 s + stage 30-75 s = **~17-21 min** (cf. full nativeB 1,151 s) | 7 TUs + the new hook TU: ~31-39 s compile (longest device.cpp, rebuilt through the fingerprint header) + ~45 s overhead + re-run CMake + stage = **~2-3 min** (cf. S3d 102.7 s + stage 74.5 s) |
| **Total at -j10, one after the other** | **~37-46 min** | **~6-10 min** (incl. apply, MANIFESTs, gates) |

- New hook .cpp: the 6 existing hooks_*.cpp TUs take 15-24 s each, so it runs beside the other TUs (+0-5 s wall). It is native-only if it goes into the gpu_native source list (OFF builds compile no gpu_native code); the CMakeLists.txt edit makes both trees re-run CMake (7-25 s each). If the hook also needs a recomp config change (a TOML hook/override), that is a regen: see (3).
- Every listed gpu_native file (and native_preparation.h) is a fingerprint input: `native_gpu_build_info.h` is regenerated, which also recompiles device.cpp, pipeline_library.cpp and shader_archive.cpp (part of the 7 edges).
- Disk: built in place (my S2/S3/S3d procedure on the snap1 trees, with apply backups): only the 2 new bin dirs, devoff ~214 MiB + native ~364 MiB = **~0.56 GiB**, plus a few MB of backups and logs. If the S3d trees must stay intact, clone them first: snap1 2.19 GiB + snap1-sdk 0.45 + snap1-off 0.62 + snap1-on 0.96 = **+4.2 GiB** (2-4 min of copying).

### (2) Native AOT shader pack (`LEGO_NATIVE_RUNTIME_SHADER_CACHE` -> a real pack)

- The pack is Agent 4's `build/agent4/s35` output (its `-Go` run was still pending at 07:06): `runtime-cache.cpp` with 4 entries (the placement VS/PS containers) plus a merged `lego-microcode-index.cpp` (19,116 old + 6 new rows).
- Swap-in: `-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=<copy of runtime-cache.cpp>` (a cache variable, now the 869 B stub), and the index replaces the fixed-path `rexlego/out/native-gpu/lego-microcode-index.cpp` in the snapshot (1,652,630 B in snap1). Both are fingerprint inputs. `snap-native-inputs.py` copies only from live DimensionsRecomp/, so S4 needs a hashed copy from build/agent4 (a small option or a separate step, ~10-15 min of prep, not build time).
- Extra edges: re-run CMake; runtime-cache.cpp in the prelink tool (2-4 s with the stub) and runtime_shader_cache.cpp (2-3 s); lego_gpu_prelink_runtime.exe relink 1-2 s; runtime prelink + embed (0.6-2.9 s with the stub; ~28 ms per shader, so seconds for 4); the index TU 3-4 s; the fingerprint, which recompiles device/pipeline_library/shader_archive (~31-39 s); exe link 4-8 s.
- **Bundled into the (1) native build: under +1 min and under 1 MB of extra disk.** On its own (own native bin): ~2-3 min incl. stage, +~364 MiB for the bin. devoff is unaffected (OFF has no gpu_native).
- For comparison only: changing the MAIN cache (`LEGO_NATIVE_SHADER_CACHE`, 9,532 shaders) would cost ~4-8 min (prelink-tool compile of the 35 MB TU 40-60 s, main prelink 64-115 s, embed 62-199 s, then fingerprint + relink) and rewrite the 502 MB linked C++.

### (3) Agent 9's codegen change (db16cyc -> `_mm_pause`, `src/codegen/builders/system.cpp`)

- Codegen tool: system.cpp 8 s + rexglue.exe relink: under 1 min. Regen: ~130 s (887 files, 467.3 MB) + gen-check ~61 s; or Agent 9 supplies the regenerated tree, as with batch-nolr for build B.
- Rebuild: codegen only rewrites files whose content changed, so only TUs with a db16cyc site recompile, as long as `_mm_pause` needs no change to the PCH or a shared header (if the PCH changes, everything rebuilds). The site count is unknown; I have not scanned the 467 MB (Agent 9 can count). db16cyc is a spin-wait hint, so few TUs is plausible (then ~2-4 min per bin), unverified. If the generator splits TUs by size, added lines could also move functions between files.
- Worst case (most TUs, or the PCH): full game rebuilds, devoff ~13-17 min (S1 789 s, B 1,039 s) + native ~16-19 min (nativeB 1,151 s) + gates and stage ~3 min: **~35-45 min for both bins.** Bundled with (1) when xmemory.h changes: **+3-4 min only** (both game trees rebuild fully anyway).
- Disk: own snapshot like build B: snapshot ~2.1 GiB + OFF tree ~0.6 + native tree ~0.95 + 2 bins ~0.56 = **~4.2 GiB** (measured for nativeB alone: 3.36 GB). In place: bins only (+0.47 GiB if the regen output is kept for a diff).

### (4) Disk now

- Free C: **241.45 GiB** (259,261,992,960 B) at 07:02. All of the above together stays under ~10 GiB.
- One bin dir: devoff ~214 MiB (8 files incl. MANIFEST), native ~364 MiB (9 files; nativeB 347.7 MiB). All staged bins now: 2.79 GiB (inventory, 05:39).
'''


def refuse(msg):
    print('REFUSED:', msg)
    sys.exit(2)


data = open(NOTES, 'rb').read()
h0 = hashlib.sha256(data).hexdigest().upper()
if not h0.startswith(EXPECT):
    refuse('notes sha %s != expected %s' % (h0[:16], EXPECT))
if b'\r' in data:
    refuse('CR present in notes')
text = data.decode('utf-8')

ins_para = wrap_md(PARA.replace('@HM@', HM))
ins_sec = wrap_md(SECTION.replace('@HM@', HM)).rstrip('\n') + '\n'
h_new = H_NEW.replace('@HM@', HM)
for name, s in (('para', ins_para), ('section', ins_sec), ('header', h_new)):
    try:
        s.encode('ascii')
    except UnicodeEncodeError as e:
        refuse('non-ASCII in %s: %s' % (name, e))
for name, a in (('header', H_OLD), ('para anchor', P_ANCHOR), ('section anchor', S_ANCHOR)):
    c = text.count(a)
    if c != 1:
        refuse('%s count %d != 1' % (name, c))
if text.count('## S4 estimate (task #30') != 0:
    refuse('section already present')
if not text.startswith(H_OLD):
    refuse('header is not line 1')

new = text.replace(H_OLD, h_new, 1)
new = new.replace(P_ANCHOR, 'Delete nothing until Agent 1 or the user says so.**\n\n' + ins_para +
                  '\n\n<!-- inventory:begin -->', 1)
i = new.index(S_ANCHOR)
pre = new[:i]
if not pre.endswith('\n\n'):
    pre += '\n' if pre.endswith('\n') else '\n\n'
new = pre + ins_sec + '\n' + new[i:]

# checks on the result
for name, a, n in (('inventory:begin', '<!-- inventory:begin -->', 1), ('inventory:end', '<!-- inventory:end -->', 1),
                   ('new section', '## S4 estimate (task #30', 1), ('batches', S_ANCHOR, 1), ('para', ins_para, 1)):
    c = new.count(a)
    if c != n:
        refuse('result: %s count %d != %d' % (name, c, n))
if new.index('<!-- inventory:end -->') > new.index('## S4 estimate (task #30'):
    refuse('section landed inside/above the inventory block')
if new.index(ins_para) > new.index('<!-- inventory:begin -->'):
    refuse('para landed inside the inventory block')
if new.replace(h_new, H_OLD, 1).replace(ins_para + '\n\n', '', 1).replace(ins_sec + '\n', '', 1) != text and \
        new.replace(h_new, H_OLD, 1).replace(ins_para + '\n\n', '', 1).replace(ins_sec, '', 1) != text:
    print('NOTE: the round-trip check differs (blank-line handling); see the diff counts below')

os.makedirs(BKDIR, exist_ok=True)
bk = os.path.join(BKDIR, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
if os.path.exists(bk):
    refuse('backup exists: ' + bk)
with open(bk, 'wb') as f:
    f.write(data)
out = new.encode('utf-8')
with open(NOTES, 'wb') as f:
    f.write(out)
back = open(NOTES, 'rb').read()
if back != out:
    refuse('read-back mismatch')
h1 = hashlib.sha256(back).hexdigest().upper()
lines = new.split('\n')
ln_sec = next(k + 1 for k, l in enumerate(lines) if l.startswith('## S4 estimate (task #30'))
ln_para = next(k + 1 for k, l in enumerate(lines) if l.startswith('**Task #30 (Agent 11'))
print('backup', os.path.basename(bk), len(data), h0[:16])
print('notes ', len(back), h1[:16], 'lines', len(lines), 'CR' if b'\r' in back else 'LF-only')
print('para at line', ln_para, '; section at line', ln_sec, '..', ln_sec + ins_sec.count('\n') - 1)
print('added bytes', len(back) - len(data))
