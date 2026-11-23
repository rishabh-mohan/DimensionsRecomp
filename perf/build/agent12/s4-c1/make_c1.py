# make_c1.py (Agent 12, task #31): S4 C1, physical_protect_keep_watch (default off), staged on
# top of diag -> P2 -> fix (i). Reads build/agent12/s4-c1/orig (bases), writes
# build/agent12/s4-c1/new. Every anchor must occur exactly once. SDK files are LF; the rexlego
# file is CRLF and keeps CRLF. Added lines are checked against the 100-column limit.
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, 'orig')
NEW = os.path.join(HERE, 'new')

FILES = {
    'xmemory.cpp': ('sdk/src/system/xmemory.cpp',
                    '141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A'),
    'shared_memory.cpp': ('sdk/src/graphics/shared_memory.cpp',
                          '0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4'),
    'xmemory.h': ('sdk/include/rex/system/xmemory.h', '80100865A654AF04'),
    'shared_memory.h': ('sdk/include/rex/graphics/shared_memory.h', '4D861738A94B556B'),
    'primitive_processor.cpp': ('sdk/src/graphics/primitive_processor.cpp', 'E07F690223B564AE'),
    'memory_watch.cpp': ('game/rexlego/src/gpu_native/memory_watch.cpp',
                         '19AE1606C6DB727369A5F119EF3371A8D307F4B42088D5C064F0D2DF8D62D47A'),
}

added_lines = []  # (file, line) for the column check


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def once(text, anchor, name):
    n = text.count(anchor)
    if n != 1:
        sys.exit('FAIL %s: anchor found %d times: %r' % (name, n, anchor[:80]))


def ins_after(text, anchor, add, name):
    once(text, anchor, name)
    added_lines.extend((name, l) for l in add.split('\n'))
    return text.replace(anchor, anchor + add)


def ins_before(text, anchor, add, name):
    once(text, anchor, name)
    added_lines.extend((name, l) for l in add.split('\n'))
    return text.replace(anchor, add + anchor)


def repl(text, old, new, name):
    once(text, old, name)
    added_lines.extend((name, l) for l in new.split('\n'))
    return text.replace(old, new)


# ----------------------------------------------------------------------------- xmemory.h
def edit_xmemory_h(t):
    n = 'xmemory.h'
    t = ins_after(t, '''  // Modifies the protection mode of pages within the given range.
  virtual bool Protect(uint32_t address, uint32_t size, uint32_t protect,
                       uint32_t* old_protect = nullptr);
''', '''
  // S4 C1 (physical_protect_keep_watch): true if Protect(address, size, protect)
  // would leave the access of every page unchanged (Protect's rounding; committed
  // pages of one region). With apply, it also stores protect in those page table
  // entries, as Protect does. Takes heap_mutex_ only.
  bool ProtectAccessUnchanged(uint32_t address, uint32_t size, uint32_t protect, bool apply);
''', n)
    t = ins_after(t, '''  void SetDataProviders(uint32_t physical_address, uint32_t length, bool enable);
''', '''  // S4 C1: PhysicalHeap::Protect's keep-watch path (see the definition). The caller
  // holds the global critical region.
  bool ProtectKeepWatch(uint32_t address, uint32_t size, uint32_t protect);
''', n)
    t = ins_after(t, '''  void UnregisterPhysicalMemoryInvalidationCallback(void* callback_handle);
''', '''
  // S4 C1 (physical_protect_keep_watch): a keep-watch guard returns true if a write
  // protect may leave this callback's write watches armed over the physical range
  // instead of firing them. It is called with the global critical region held and
  // before any heap mutex, so it must take no lock and must not call into a heap.
  typedef bool (*PhysicalMemoryKeepWatchGuard)(void* context_ptr, uint32_t physical_address_start,
                                               uint32_t length);
  // As above, plus a keep-watch guard (nullptr: none). While a callback without a
  // guard is registered, every write protect takes the normal path.
  void* RegisterPhysicalMemoryInvalidationCallback(PhysicalMemoryInvalidationCallback callback,
                                                   void* callback_context,
                                                   PhysicalMemoryKeepWatchGuard keep_watch_guard);
  // Turns physical_protect_keep_watch off for the rest of the process. Lock-free, so
  // a static initializer may call it (rexlego's native renderer does).
  static void BlockPhysicalProtectKeepWatch();
  static bool IsPhysicalProtectKeepWatchBlocked();
''', n)
    t = ins_after(t, '''      physical_memory_invalidation_callbacks_;
''', '''  // S4 C1: keep-watch guards by callback handle, guarded like the callbacks above.
  std::vector<std::pair<std::pair<PhysicalMemoryInvalidationCallback, void*>*,
                        PhysicalMemoryKeepWatchGuard>>
      physical_memory_keep_watch_guards_;
''', n)
    return t


# ----------------------------------------------------------------------------- xmemory.cpp
def edit_xmemory_cpp(t):
    n = 'xmemory.cpp'
    # X1: the cvar
    t = ins_after(t, '''                    "Hold the global lock across both host protects in PhysicalHeap::Protect");
''', '''
// S4 C1 (default off): keep the write watches on physical write protects that change
// no page's access. Engages only with physical_protect_hold_global_lock on; see
// PhysicalHeap::ProtectKeepWatch.
REXCVAR_DEFINE_BOOL(physical_protect_keep_watch, false, "Memory",
                    "Keep the write watches on physical write protects that leave every "
                    "page's access unchanged (needs physical_protect_hold_global_lock)");
''', n)
    # X2a: registration with a guard
    t = ins_before(t, '''void Memory::UnregisterPhysicalMemoryInvalidationCallback(void* callback_handle) {
''', '''// S4 C1: as above, and the guard is kept by handle for PhysicalHeap::ProtectKeepWatch.
void* Memory::RegisterPhysicalMemoryInvalidationCallback(
    PhysicalMemoryInvalidationCallback callback, void* callback_context,
    PhysicalMemoryKeepWatchGuard keep_watch_guard) {
  auto entry = new std::pair<PhysicalMemoryInvalidationCallback, void*>(callback, callback_context);
  auto lock = global_critical_region_.Acquire();
  physical_memory_invalidation_callbacks_.push_back(entry);
  if (keep_watch_guard) {
    physical_memory_keep_watch_guards_.emplace_back(entry, keep_watch_guard);
  }
  return entry;
}

''', n)
    # X2b+c: unregister drops the guard; the latch
    t = repl(t, '''      physical_memory_invalidation_callbacks_.erase(it);
    }
  }
  delete entry;
}
''', '''      physical_memory_invalidation_callbacks_.erase(it);
    }
    // S4 C1: drop the callback's keep-watch guard, if any, with it.
    auto guard_it = std::find_if(physical_memory_keep_watch_guards_.begin(),
                                 physical_memory_keep_watch_guards_.end(),
                                 [entry](const auto& item) { return item.first == entry; });
    if (guard_it != physical_memory_keep_watch_guards_.end()) {
      physical_memory_keep_watch_guards_.erase(guard_it);
    }
  }
  delete entry;
}

// S4 C1: process-wide latch, read by PhysicalHeap::ProtectKeepWatch. Constant-
// initialized, so a static initializer in another translation unit can set it.
static constinit std::atomic<bool> physical_protect_keep_watch_blocked{false};

void Memory::BlockPhysicalProtectKeepWatch() {
  physical_protect_keep_watch_blocked.store(true, std::memory_order_relaxed);
}

bool Memory::IsPhysicalProtectKeepWatchBlocked() {
  return physical_protect_keep_watch_blocked.load(std::memory_order_relaxed);
}
''', n)
    # X3: BaseHeap::ProtectAccessUnchanged
    t = ins_before(t, '''bool BaseHeap::QueryRegionInfo(uint32_t base_address, HeapAllocationInfo* out_info) {
''', '''// S4 C1: see the declaration. Same rounding and bounds as Protect; a zero size, an
// out-of-range or wrapping request, or guest pages smaller than host pages (Protect
// reconciles those after the table change) return false. Only heap_mutex_ is
// taken, so a caller that needs the global critical region holds it already.
bool BaseHeap::ProtectAccessUnchanged(uint32_t address, uint32_t size, uint32_t protect,
                                      bool apply) {
  if (!size || page_size_ < memory_->system_page_size_) {
    return false;
  }
  uint32_t start_page_number = (address - heap_base_) >> page_size_shift_;
  if (start_page_number >= page_table_.size()) {
    return false;
  }
  uint32_t end_page_number =
      uint32_t((uint64_t(address) + size - 1 - heap_base_) >> page_size_shift_);
  if (end_page_number >= page_table_.size()) {
    return false;
  }
  const memory::PageAccess access = ToPageAccess(protect);
  std::lock_guard<std::recursive_mutex> heap_lock(heap_mutex_);
  const uint32_t base_address = page_table_[start_page_number].base_address;
  for (uint32_t page_number = start_page_number; page_number <= end_page_number; ++page_number) {
    const auto& page_entry = page_table_[page_number];
    if (page_entry.base_address != base_address ||
        !(page_entry.state & memory::kMemoryAllocationCommit) ||
        ToPageAccess(page_entry.current_protect) != access) {
      return false;
    }
  }
  if (apply) {
    for (uint32_t page_number = start_page_number; page_number <= end_page_number; ++page_number) {
      page_table_[page_number].current_protect = protect;
    }
  }
  return true;
}

''', n)
    # X4: the branch in PhysicalHeap::Protect, after fix (i)'s second acquire
    t = repl(t, '''    hold_global_lock = global_critical_region_.Acquire();
  }

  // Only invalidate if making writable again, for simplicity - not when simply
''', '''    hold_global_lock = global_critical_region_.Acquire();
  }

  // S4 C1, physical_protect_keep_watch (default off): with fix (i)'s hold, a write
  // protect that changes no page's access may keep the range's write watches armed
  // (see ProtectKeepWatch). Off, without the hold, or with old_protect: the
  // original path below.
  if (hold_global_lock.owns_lock() && !old_protect && REXCVAR_GET(physical_protect_keep_watch) &&
      ProtectKeepWatch(address, size, protect)) {
    return true;
  }

  // Only invalidate if making writable again, for simplicity - not when simply
''', n)
    # X5: PhysicalHeap::ProtectKeepWatch
    t = ins_before(t, '''// notify_on_invalidation is only written with the global critical region held,
''', '''// S4 C1, physical_protect_keep_watch (default off). Protect calls this only for a
// write protect without old_protect and with fix (i)'s hold, so the global critical
// region (G) is held, twice, until Protect returns. When every page keeps its
// access, the normal path's host protects change nothing on a page whose host
// protection matches its table entry, and its TriggerCallbacks fires and drops the
// write watches on the range. Here the watches stay armed instead: a later CPU
// write still faults and fires them, and a range that is never written keeps its
// GPU copy. Returns true if the protect is done; false sends Protect down the
// normal path, with nothing changed except at most page table entries set to the
// value that path writes too. Required, all checked under G:
//  1. every page (Protect's rounding) keeps its access in this heap and in the
//     parent heap, and they are committed pages of one region (as Protect needs);
//  2. every invalidation callback has a keep-watch guard and the guard allows the
//     range (TriggerCallbacks' physical range); a callback without one, such as
//     rexlego's, keeps the normal path;
//  3. SharedMemory's guard: no valid page in the range holds GPU-written data;
//  4. no host page of the guest pages Protect would change waits for its data
//     provider (the normal path makes those host-writable without providing data).
// The guards run first, under G and before any heap mutex, and take no lock. Then
// G -> this heap_mutex_, released, and G -> the parent's heap_mutex_: the two heap
// mutexes are never nested. Memory::BlockPhysicalProtectKeepWatch (rexlego's native
// renderer, from static init) turns this off for the process.
bool PhysicalHeap::ProtectKeepWatch(uint32_t address, uint32_t size, uint32_t protect) {
  if (Memory::IsPhysicalProtectKeepWatchBlocked()) {
    return false;
  }
  // Inside this heap, not empty and not wrapping; anything else keeps the normal path.
  if (!size || address < heap_base_ || address - heap_base_ >= heap_size_ ||
      size > heap_size_ - (address - heap_base_)) {
    return false;
  }
  uint32_t heap_relative_address = address - heap_base_;

  // 2 and 3: the guards, with the physical range TriggerCallbacks would pass to the
  // callbacks.
  uint32_t system_page_first = (heap_relative_address + host_address_offset()) / system_page_size_;
  uint32_t system_page_last =
      (heap_relative_address + size - 1 + host_address_offset()) / system_page_size_;
  if (system_page_last >= system_page_count_) {
    return false;
  }
  uint32_t physical_address_offset = GetPhysicalAddress(heap_base_);
  uint32_t physical_address_start =
      rex::sat_sub(system_page_first * system_page_size_, host_address_offset()) +
      physical_address_offset;
  uint32_t physical_length =
      std::min(rex::sat_sub(system_page_last * system_page_size_ + system_page_size_,
                            host_address_offset()) +
                   physical_address_offset - physical_address_start,
               heap_size_ - (physical_address_start - physical_address_offset));
  for (auto invalidation_callback : memory_->physical_memory_invalidation_callbacks_) {
    Memory::PhysicalMemoryKeepWatchGuard guard = nullptr;
    for (const auto& item : memory_->physical_memory_keep_watch_guards_) {
      if (item.first == invalidation_callback) {
        guard = item.second;
        break;
      }
    }
    if (!guard || !guard(invalidation_callback->second, physical_address_start, physical_length)) {
      return false;
    }
  }

  // 4: data providers, over the host pages of the guest pages Protect would change.
  uint32_t provide_page_first =
      ((heap_relative_address & ~(page_size_ - 1)) + host_address_offset()) / system_page_size_;
  uint32_t provide_page_last =
      (((heap_relative_address + (size - 1)) | (page_size_ - 1)) + host_address_offset()) /
      system_page_size_;
  provide_page_last = std::min(provide_page_last, system_page_count_ - 1);
  for (uint32_t i = provide_page_first >> 6; i <= (provide_page_last >> 6); ++i) {
    uint64_t block = system_page_flags_[i].provide_data;
    if (i == (provide_page_first >> 6)) {
      block &= ~((uint64_t(1) << (provide_page_first & 63)) - 1);
    }
    if (i == (provide_page_last >> 6) && (provide_page_last & 63) != 63) {
      block &= (uint64_t(1) << ((provide_page_last & 63) + 1)) - 1;
    }
    if (block) {
      return false;
    }
  }

  // 1: the access of every page in both page tables. Check both, then store both,
  // each under its own heap_mutex_ only.
  uint32_t parent_address = GetPhysicalAddress(address);
  if (!ProtectAccessUnchanged(address, size, protect, false) ||
      !parent_heap_->ProtectAccessUnchanged(parent_address, size, protect, false)) {
    return false;
  }
  return ProtectAccessUnchanged(address, size, protect, true) &&
         parent_heap_->ProtectAccessUnchanged(parent_address, size, protect, true);
}

''', n)
    return t


# ----------------------------------------------------------------------------- shared_memory.h
def edit_shared_memory_h(t):
    n = 'shared_memory.h'
    t = ins_after(t, '''  static std::pair<uint32_t, uint32_t> MemoryInvalidationCallbackThunk(
      void* context_ptr, uint32_t physical_address_start, uint32_t length, bool exact_range);
''', '''
  // S4 C1 (physical_protect_keep_watch): keep-watch guard, called with the global
  // critical region held and before any heap mutex; it takes no lock.
  static bool MemoryKeepWatchGuardThunk(void* context_ptr, uint32_t physical_address_start,
                                        uint32_t length);
  bool MemoryKeepWatchGuard(uint32_t physical_address_start, uint32_t length);
  // physical_protect_keep_watch_verify: per-page hashes of CPU uploads (0: none),
  // allocated by the first record. Protected by global_critical_region.
  void KeepWatchVerifyRecord(uint32_t page_first, uint32_t page_last, bool written_by_gpu);
  bool KeepWatchVerifyCheck(uint32_t page_first, uint32_t page_last, bool at_protect);
  std::unique_ptr<uint64_t[]> keep_watch_verify_hashes_;
  uint64_t keep_watch_verify_protect_mismatches_ = 0;
  uint64_t keep_watch_verify_fault_mismatches_ = 0;
''', n)
    return t


# ----------------------------------------------------------------------------- shared_memory.cpp
def edit_shared_memory_cpp(t):
    n = 'shared_memory.cpp'
    t = repl(t, '''#include <rex/graphics/shared_memory.h>
#include <rex/math.h>
''', '''#include <rex/graphics/shared_memory.h>
#include <rex/hash.h>
#include <rex/logging.h>
#include <rex/math.h>
''', n)
    t = ins_after(t, '''                    "wakes on the GPU thread)");
''', '''
// S4 C1 verify (default off; set it at launch). Hashes every page of each CPU upload
// once its write watch is armed. A keep-watch protect (K) or a write fault (F) that
// finds a still-valid page changed logs it, and K sends that protect down the
// normal path. With physical_protect_keep_watch off, the F count is today's rate.
REXCVAR_DEFINE_BOOL(physical_protect_keep_watch_verify, false, "GPU",
                    "Verify physical_protect_keep_watch: hash CPU uploads and log pages that "
                    "changed without a write fault (slow; diagnostics only)")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
''', n)
    t = repl(t, '''  memory_invalidation_callback_handle_ =
      memory_.RegisterPhysicalMemoryInvalidationCallback(MemoryInvalidationCallbackThunk, this);
''', '''  // S4 C1: with SharedMemory's keep-watch guard (condition 3, verify mode's K check).
  memory_invalidation_callback_handle_ = memory_.RegisterPhysicalMemoryInvalidationCallback(
      MemoryInvalidationCallbackThunk, this, MemoryKeepWatchGuardThunk);
''', n)
    t = repl(t, '''        (valid_page_last - valid_page_first + 1) << page_size_log2_, true, false);
  }
}
''', '''        (valid_page_last - valid_page_first + 1) << page_size_log2_, true, false);
  }

  // S4 C1 verify: hash the pages once the watch is armed (a later write faults and
  // clears valid before it lands).
  if (REXCVAR_GET(physical_protect_keep_watch_verify) && memory_invalidation_callback_handle_) {
    KeepWatchVerifyRecord(valid_page_first, valid_page_last, written_by_gpu);
  }
}
''', n)
    t = repl(t, '''  auto global_lock = global_critical_region_.Acquire();

  if (!exact_range) {
''', '''  auto global_lock = global_critical_region_.Acquire();

  // S4 C1 verify (F): a write fault comes before its write lands, so a page that is
  // still valid must still match its upload hash.
  if (!exact_range && keep_watch_verify_hashes_) {
    KeepWatchVerifyCheck(page_first, page_last, false);
  }

  if (!exact_range) {
''', n)
    t = ins_after(t, '''  return std::make_pair(page_first << page_size_log2_, (page_last - page_first + 1)
                                                           << page_size_log2_);
}
''', '''
bool SharedMemory::MemoryKeepWatchGuardThunk(void* context_ptr, uint32_t physical_address_start,
                                             uint32_t length) {
  return reinterpret_cast<SharedMemory*>(context_ptr)
      ->MemoryKeepWatchGuard(physical_address_start, length);
}

// S4 C1 condition 3: a write protect may keep the watches on a range only if no
// valid page in it holds GPU-written data. Called by PhysicalHeap::ProtectKeepWatch
// with the global critical region held and before any heap mutex; takes no lock.
// In verify mode it also refuses a range whose CPU-uploaded pages changed (K).
bool SharedMemory::MemoryKeepWatchGuard(uint32_t physical_address_start, uint32_t length) {
  if (length == 0 || physical_address_start >= kBufferSize) {
    return true;
  }
  length = std::min(length, kBufferSize - physical_address_start);
  uint32_t page_first = physical_address_start >> page_size_log2_;
  uint32_t page_last = (physical_address_start + (length - 1)) >> page_size_log2_;
  uint32_t block_first = page_first >> 6;
  uint32_t block_last = page_last >> 6;
  for (uint32_t i = block_first; i <= block_last; ++i) {
    uint64_t gpu_written_bits = system_page_flags_valid_and_gpu_written_[i];
    if (i == block_first) {
      gpu_written_bits &= ~((uint64_t(1) << (page_first & 63)) - 1);
    }
    if (i == block_last && (page_last & 63) != 63) {
      gpu_written_bits &= (uint64_t(1) << ((page_last & 63) + 1)) - 1;
    }
    if (gpu_written_bits) {
      return false;
    }
  }
  return !keep_watch_verify_hashes_ || KeepWatchVerifyCheck(page_first, page_last, true);
}

// Verify mode only: whether the host page at host can be read, so hashing it can't
// fault (a valid page can be no-access in the physical view). readable_end caches
// the end of the last readable host region, for ascending pages.
static bool KeepWatchVerifyReadable(uint8_t* host, size_t page_size, uint8_t*& readable_end) {
  if (readable_end && host < readable_end) {
    return true;
  }
  size_t length = page_size;
  memory::PageAccess access;
  if (!memory::QueryProtect(host, length, access) || access == memory::PageAccess::kNoAccess) {
    return false;
  }
  readable_end = host + length;
  return true;
}

// Verify mode: hash each page of a CPU upload after its write watch is armed (any
// later write faults and clears valid first). GPU-written and unreadable pages get
// 0, which the checks skip.
void SharedMemory::KeepWatchVerifyRecord(uint32_t page_first, uint32_t page_last,
                                         bool written_by_gpu) {
  auto global_lock = global_critical_region_.Acquire();
  if (!keep_watch_verify_hashes_) {
    keep_watch_verify_hashes_ = std::make_unique<uint64_t[]>(kBufferSize >> page_size_log2_);
    REXGPU_INFO(
        "C1 verify: on. Hashing CPU uploads; K checks keep-watch protects, F checks write "
        "faults");
  }
  const size_t page_size = size_t(1) << page_size_log2_;
  uint8_t* readable_end = nullptr;
  for (uint32_t page = page_first; page <= page_last; ++page) {
    uint64_t hash = 0;
    if (!written_by_gpu) {
      uint8_t* host = memory_.TranslatePhysical(page << page_size_log2_);
      if (KeepWatchVerifyReadable(host, page_size, readable_end)) {
        hash = XXH3_64bits(host, page_size) | 1;
      }
    }
    keep_watch_verify_hashes_[page] = hash;
  }
}

// Verify mode: compare still-valid CPU-uploaded pages with their upload hashes.
// Called with the global critical region held: K from the keep-watch guard (no lock
// taken; the logger's lock is a leaf), F from a write fault before its write lands.
// Returns false if any page changed.
bool SharedMemory::KeepWatchVerifyCheck(uint32_t page_first, uint32_t page_last,
                                        bool at_protect) {
  const size_t page_size = size_t(1) << page_size_log2_;
  uint8_t* readable_end = nullptr;
  bool unchanged = true;
  for (uint32_t page = page_first; page <= page_last; ++page) {
    uint64_t hash = keep_watch_verify_hashes_[page];
    uint64_t page_bit = uint64_t(1) << (page & 63);
    if (!hash || !(system_page_flags_valid_[page >> 6] & page_bit) ||
        (system_page_flags_valid_and_gpu_written_[page >> 6] & page_bit)) {
      continue;
    }
    uint8_t* host = memory_.TranslatePhysical(page << page_size_log2_);
    if (!KeepWatchVerifyReadable(host, page_size, readable_end) ||
        (XXH3_64bits(host, page_size) | 1) == hash) {
      continue;
    }
    unchanged = false;
    uint64_t& mismatches =
        at_protect ? keep_watch_verify_protect_mismatches_ : keep_watch_verify_fault_mismatches_;
    ++mismatches;
    if (mismatches <= 256 || !(mismatches & 4095)) {
      REXGPU_WARN("C1 verify {}: page {:08X} changed since its upload ({} so far){}",
                  at_protect ? 'K' : 'F', page << page_size_log2_, mismatches,
                  at_protect ? "; protect keeps the normal path" : "");
    }
  }
  return unchanged;
}
''', n)
    return t


# ----------------------------------------------------------------------------- primitive_processor.cpp
def edit_primitive_processor_cpp(t):
    n = 'primitive_processor.cpp'
    t = repl(t, '''namespace rex::graphics {

// SIMD processing here assumes''', '''namespace rex::graphics {

// S4 C1: the converted index cache lets a keep-watch protect keep its write watches;
// a later CPU write still faults and invalidates the cached conversions.
static bool MemoryKeepWatchGuardAlwaysAllow(void*, uint32_t, uint32_t) { return true; }

// SIMD processing here assumes''', n)
    t = repl(t, '''              MemoryInvalidationCallbackThunk, &processor_);
''', '''              MemoryInvalidationCallbackThunk, &processor_, MemoryKeepWatchGuardAlwaysAllow);
''', n)
    return t


# ----------------------------------------------------------------------------- memory_watch.cpp (CRLF)
def edit_memory_watch_cpp(t):
    n = 'memory_watch.cpp'
    crlf = lambda s: s.replace('\n', '\r\n')
    t = ins_after(t, crlf('''void* g_callback = nullptr;
'''), crlf('''// S4 C1: MemoryWritten has no keep-watch guard on purpose: it unwatches its exact
// range, so a kept watch would fault once per written page. The native renderer
// also turns physical_protect_keep_watch off for the process from static init,
// before any guest code runs, not only from the lazy registration below.
[[maybe_unused]] const bool g_keep_watch_blocked =
    (rex::memory::Memory::BlockPhysicalProtectKeepWatch(), true);
'''), n)
    return t


EDITS = {
    'xmemory.h': edit_xmemory_h,
    'xmemory.cpp': edit_xmemory_cpp,
    'shared_memory.h': edit_shared_memory_h,
    'shared_memory.cpp': edit_shared_memory_cpp,
    'primitive_processor.cpp': edit_primitive_processor_cpp,
    'memory_watch.cpp': edit_memory_watch_cpp,
}


def main():
    bad = 0
    for name, (rel, want) in FILES.items():
        src = os.path.join(ORIG, rel)
        data = open(src, 'rb').read()
        h = sha(data)
        if not h.startswith(want):
            sys.exit('FAIL base %s: sha %s, want %s' % (name, h[:16], want[:16]))
        text = data.decode('utf-8')
        crlf = '\r\n' in text
        if name != 'memory_watch.cpp' and crlf:
            sys.exit('FAIL base %s: CRLF in an SDK file' % name)
        out = EDITS[name](text)
        if name == 'memory_watch.cpp':
            if out.replace('\r\n', '').count('\n'):
                sys.exit('FAIL memory_watch.cpp: bare LF after the edit')
        elif '\r' in out:
            sys.exit('FAIL %s: CR after the edit' % name)
        dst = os.path.join(NEW, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(out.encode('utf-8'))
        print('%-24s base %s (%6d B) -> new %s (%6d B)' % (name, h[:16], len(data),
                                                           sha(out.encode('utf-8'))[:16],
                                                           len(out.encode('utf-8'))))
    for name, line in added_lines:
        line = line.rstrip('\r')
        if len(line) > 100:
            bad += 1
            print('LONG %s (%d): %s' % (name, len(line), line))
        if line != line.rstrip():
            bad += 1
            print('TRAILING SPACE %s: %r' % (name, line))
    print('added lines checked: %d, problems: %d' % (len(added_lines), bad))
    print('RESULT ' + ('FAIL' if bad else 'PASS'))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
