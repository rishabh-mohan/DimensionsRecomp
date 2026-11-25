import os, hashlib
W = r'<workspace>\build\agent2\final\work\new\DimensionsRecomp\rexglue-sdk\src'
EDITS = {
 r'core\clock.cpp': [
  ('REXCVAR_DEFINE_BOOL(clock_lockfree, false, "Clock",', 'REXCVAR_DEFINE_BOOL(clock_lockfree, true, "Clock",')],
 r'core\timer_queue.cpp': [
  ('// Default off (behavior changes ship off until rated SAFE). perf-notes/agent11-kernel.md,',
   '// Default on (final build: WC win3 arm; false = the old phased spin). perf-notes/agent11-kernel.md,'),
  ('REXCVAR_DEFINE_BOOL(timer_queue_precise_wait, false, "Runtime",', 'REXCVAR_DEFINE_BOOL(timer_queue_precise_wait, true, "Runtime",')],
 r'graphics\shared_memory.cpp': [
  ('// S4 P2 (default off). When on, MakeRangeValid holds the global critical region',
   '// S4 P2 (default on, final build). When on, MakeRangeValid holds the global critical region'),
  ('REXCVAR_DEFINE_BOOL(shared_memory_single_hold_rearm, false, "GPU",', 'REXCVAR_DEFINE_BOOL(shared_memory_single_hold_rearm, true, "GPU",')],
 r'kernel\xboxkrnl\xboxkrnl_rtl.cpp': [
  ('    cs_spin, false, "Kernel",', '    cs_spin, true, "Kernel",')],
 r'kernel\xboxkrnl\xboxkrnl_threading.cpp': [
  ('    spinlock_pause_spin, false, "Kernel",', '    spinlock_pause_spin, true, "Kernel",')],
 r'system\runtime.cpp': [
  ('// Default off (session-2 batch rule); 1 / true is the recommended setting.',
   '// Default 1 / true (final build: WC win3 arm); 0 / false restore the old behaviour.'),
  ('REXCVAR_DEFINE_UINT32(host_timer_resolution_ms, 0, "Runtime",', 'REXCVAR_DEFINE_UINT32(host_timer_resolution_ms, 1, "Runtime",'),
  ('REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, false, "Runtime",', 'REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, true, "Runtime",')],
 r'system\xmemory.cpp': [
  ('// S4.7 fix (i), default off: see PhysicalHeap::Protect.', '// S4.7 fix (i), default on (final build): see PhysicalHeap::Protect.'),
  ('REXCVAR_DEFINE_BOOL(physical_protect_hold_global_lock, false, "Memory",', 'REXCVAR_DEFINE_BOOL(physical_protect_hold_global_lock, true, "Memory",'),
  ('// S4 C1 (default off): keep the write watches on physical write protects that change',
   '// S4 C1 (default on, final build): keep the write watches on physical write protects that change'),
  ('REXCVAR_DEFINE_BOOL(physical_protect_keep_watch, false, "Memory",', 'REXCVAR_DEFINE_BOOL(physical_protect_keep_watch, true, "Memory",')],
 r'system\xobject.cpp': [
  ('REXCVAR_DEFINE_BOOL(wait_timeout_round_up, false, "Kernel",', 'REXCVAR_DEFINE_BOOL(wait_timeout_round_up, true, "Kernel",')],
 r'system\xthread.cpp': [
  ('REXCVAR_DEFINE_BOOL(precise_guest_sleep, false, "Kernel",', 'REXCVAR_DEFINE_BOOL(precise_guest_sleep, true, "Kernel",'),
  ('REXCVAR_DEFINE_BOOL(tls_bounds_fix, false, "Kernel",', 'REXCVAR_DEFINE_BOOL(tls_bounds_fix, true, "Kernel",')],
}
for f, eds in EDITS.items():
    p = os.path.join(W, f)
    b = open(p, 'rb').read()
    assert b'\r\n' not in b, f
    s = b.decode('utf-8')
    for old, new in eds:
        n = s.count(old)
        assert n == 1, (f, old, n)
        s = s.replace(old, new)
    open(p, 'wb').write(s.encode('utf-8'))
    print(hashlib.sha256(s.encode()).hexdigest()[:16].upper(), f)
