// Agent 12 replica benches: mock guest memory.
//
// Heaps with guest page protection, physical heaps with per-system-page
// write-watch bits (64 pages per uint64 block), the global critical region,
// and these functions transcribed from DimensionsRecomp/rexglue-sdk
// src/system/xmemory.cpp:
//   BaseHeap::QueryRangeAccess          pristine HEAD (unchanged)
//   PhysicalHeap::EnableAccessCallbacks working tree (section A: atomic_ref
//                                       bit store + seq_cst fence at the end)
//   PhysicalHeap::TriggerCallbacks      working tree (section A: atomic_ref
//                                       store in the clear loop)
//   PhysicalHeap::MayHaveWriteWatches   working tree (section A, new)
//   Memory::TranslateVirtual/Physical   include/rex/system/xmemory.h
// Differences from the SDK (on purpose):
//   - LookupHeap walks a small table instead of the fixed 0x40000000.. chain
//     (same cost class: a few compares, out of line).
//   - GetPhysicalAddress adds a per-heap phys_offset so the mock physical
//     heaps don't alias each other; the 0xE0000000 +0x1000 rule is the e_like
//     flag.
//   - rex::memory::Protect (VirtualProtect) is a counter + optional log.
#pragma once
#include "common.h"

#include <atomic>
#include <bit>
#include <cstdlib>
#include <limits>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

#if defined(B12_NO_COUNTERS)
#define B12_COUNT(field) ((void)0)
#else
#define B12_COUNT(field) (++::b12::tl_counters.field)
#endif

#define B12_NOINLINE __declspec(noinline)

namespace b12 {

struct Counters {
  uint64_t readfile_calls = 0;
  uint64_t file_lock = 0;       // file_lock_ acquisitions
  uint64_t shared_lock = 0;     // unlocked_read_lock_ shared acquisitions
  uint64_t global_lock = 0;     // global critical region acquisitions
  uint64_t heap_lock = 0;       // heap_mutex_ acquisitions (QueryRangeAccess)
  uint64_t lookup_heap = 0;
  uint64_t fixup_calls = 0;     // ApplyFileReadFixups
  uint64_t trigger_calls = 0;   // TriggerCallbacks entered
  uint64_t trigger_fired = 0;   // ... that found a watched page
  uint64_t precheck_calls = 0;  // MayHaveWriteWatches
  uint64_t notify_calls = 0;    // NotifyIOCompletionPorts
  uint64_t event_sets = 0;      // async_event_->Set()
  uint64_t unprotect_calls = 0;
  uint64_t protect_calls = 0;
};
inline thread_local Counters tl_counters;

template <typename T>
constexpr T sat_sub(T a, T b) {
  return a > b ? T(a - b) : T(0);
}
template <typename T>
constexpr T sat_add(T a, T b) {
  T r = T(a + b);
  return r < a ? std::numeric_limits<T>::max() : r;
}

enum class HeapType { kGuestVirtual, kGuestXex, kGuestPhysical, kHostPhysical };
enum class PageAccess { kNoAccess = 0, kReadOnly = 1, kReadWrite = 3 };

constexpr uint32_t kMemoryProtectRead = 1u << 0;
constexpr uint32_t kMemoryProtectWrite = 1u << 1;
constexpr uint32_t kMemoryProtectNoCache = 1u << 2;
constexpr uint32_t kMemoryProtectWriteCombine = 1u << 3;

// xmemory.cpp ToPageAccess (pristine).
inline PageAccess ToPageAccess(uint32_t protect) {
  bool is_writable = (protect & kMemoryProtectWrite) || (protect & kMemoryProtectWriteCombine);
  if ((protect & kMemoryProtectRead) && !is_writable) {
    return PageAccess::kReadOnly;
  } else if ((protect & kMemoryProtectRead) && is_writable) {
    return PageAccess::kReadWrite;
  } else {
    return PageAccess::kNoAccess;
  }
}

// rex::thread::global_critical_region: one process-wide recursive mutex behind
// an out-of-line accessor; AcquireDirect() returns a unique_lock on it.
struct global_critical_region {
  B12_NOINLINE static std::recursive_mutex& mutex() {
    static std::recursive_mutex global_mutex;
    return global_mutex;
  }
  static std::unique_lock<std::recursive_mutex> AcquireDirect() {
    B12_COUNT(global_lock);
    return std::unique_lock<std::recursive_mutex>(mutex());
  }
  std::unique_lock<std::recursive_mutex> Acquire() { return AcquireDirect(); }
};

// Stand-in for rex::memory::Protect on a heap's system pages.
struct ProtectRecord {
  uint32_t heap_base;
  uint32_t system_page_first;
  uint32_t system_page_count;
  PageAccess access;
};
inline thread_local std::vector<ProtectRecord>* tl_protect_log = nullptr;
inline void MockProtect(uint32_t heap_base, uint32_t system_page_first, uint32_t system_page_count,
                        PageAccess access) {
  if (access == PageAccess::kReadWrite) {
    B12_COUNT(unprotect_calls);
  } else {
    B12_COUNT(protect_calls);
  }
  if (tl_protect_log) {
    tl_protect_log->push_back({heap_base, system_page_first, system_page_count, access});
  }
}

using PhysicalMemoryInvalidationCallback = std::pair<uint32_t, uint32_t> (*)(
    void* context_ptr, uint32_t physical_address_start, uint32_t length, bool exact_range);

class MockMemory;

struct PageEntry {
  uint32_t current_protect = 0;
};

class BaseHeap {
 public:
  virtual ~BaseHeap() = default;

  void Initialize(MockMemory* memory, uint8_t* membase, HeapType heap_type, uint32_t heap_base,
                  uint32_t heap_size, uint32_t page_size, uint32_t host_address_offset = 0) {
    memory_ = memory;
    membase_ = membase;
    heap_type_ = heap_type;
    heap_base_ = heap_base;
    heap_size_ = heap_size;
    page_size_ = page_size;
    page_size_shift_ = uint32_t(std::countr_zero(page_size));
    host_address_offset_ = host_address_offset;
    page_table_.assign(heap_size / page_size, PageEntry{kMemoryProtectRead | kMemoryProtectWrite});
  }

  HeapType heap_type() const { return heap_type_; }
  uint32_t heap_base() const { return heap_base_; }
  uint32_t heap_size() const { return heap_size_; }
  uint32_t page_size() const { return page_size_; }
  uint32_t host_address_offset() const { return host_address_offset_; }

  // Pristine BaseHeap::QueryRangeAccess (xmemory.cpp:1908).
  B12_NOINLINE PageAccess QueryRangeAccess(uint32_t low_address, uint32_t high_address) {
    if (low_address > high_address || low_address < heap_base_ ||
        (high_address - heap_base_) >= heap_size_) {
      return PageAccess::kNoAccess;
    }
    uint32_t low_page_number = (low_address - heap_base_) >> page_size_shift_;
    uint32_t high_page_number = (high_address - heap_base_) >> page_size_shift_;
    bool all_readable = true;
    bool all_writable = true;
    {
      std::lock_guard<std::recursive_mutex> heap_lock(heap_mutex_);
      B12_COUNT(heap_lock);
      for (uint32_t i = low_page_number; i <= high_page_number; ++i) {
        uint32_t page_protect = page_table_[i].current_protect;
        if (!(page_protect & kMemoryProtectRead)) {
          all_readable = false;
        }
        if (!(page_protect & kMemoryProtectWrite) && !(page_protect & kMemoryProtectWriteCombine)) {
          all_writable = false;
        }
      }
    }
    if (all_readable && all_writable) {
      return PageAccess::kReadWrite;
    } else if (all_readable) {
      return PageAccess::kReadOnly;
    } else {
      return PageAccess::kNoAccess;
    }
  }

  // Test helpers (not SDK API).
  void SetGuestProtect(uint32_t address, uint32_t size, uint32_t protect) {
    if (!size) return;
    uint32_t first = (address - heap_base_) >> page_size_shift_;
    uint32_t last = (address + size - 1 - heap_base_) >> page_size_shift_;
    for (uint32_t i = first; i <= last && i < page_table_.size(); ++i) {
      page_table_[i].current_protect = protect;
    }
  }
  void ResetGuestProtect(uint32_t protect = kMemoryProtectRead | kMemoryProtectWrite) {
    for (auto& e : page_table_) e.current_protect = protect;
  }
  size_t guest_page_count() const { return page_table_.size(); }
  uint32_t guest_protect(size_t page) const { return page_table_[page].current_protect; }

 protected:
  MockMemory* memory_ = nullptr;
  uint8_t* membase_ = nullptr;
  HeapType heap_type_ = HeapType::kGuestVirtual;
  uint32_t heap_base_ = 0;
  uint32_t heap_size_ = 0;
  uint32_t page_size_ = 4096;
  uint32_t page_size_shift_ = 12;
  uint32_t host_address_offset_ = 0;
  std::vector<PageEntry> page_table_;
  mutable std::recursive_mutex heap_mutex_;
};

class PhysicalHeap : public BaseHeap {
 public:
  struct SystemPageFlagsBlock {
    uint64_t notify_on_invalidation = 0;
    uint64_t provide_data = 0;
  };

  // e_like: the 0xE0000000 heap on Windows (host_address_offset 0x1000 and
  // GetPhysicalAddress +0x1000).
  void InitializePhysical(MockMemory* memory, uint8_t* membase, uint32_t heap_base,
                          uint32_t heap_size, uint32_t page_size, bool e_like,
                          uint32_t phys_offset) {
    BaseHeap::Initialize(memory, membase, HeapType::kGuestPhysical, heap_base, heap_size,
                         page_size, e_like ? 0x1000u : 0u);
    e_like_ = e_like;
    phys_offset_ = phys_offset;
    system_page_size_ = 4096;
    system_page_count_ = uint32_t((size_t(heap_size_) + host_address_offset() +
                                   (system_page_size_ - 1)) /
                                  system_page_size_);
    system_page_flags_.assign((system_page_count_ + 63) / 64, SystemPageFlagsBlock{});
  }

  uint32_t GetPhysicalAddress(uint32_t address) const {
    address -= heap_base_;
    if (e_like_) {
      address += 0x1000;
    }
    return address + phys_offset_;
  }

  B12_NOINLINE void EnableAccessCallbacks(uint32_t physical_address, uint32_t length,
                                          bool enable_invalidation_notifications,
                                          bool enable_data_providers);
  B12_NOINLINE bool TriggerCallbacks(std::unique_lock<std::recursive_mutex> global_lock_locked_once,
                                     uint32_t virtual_address, uint32_t length, bool is_write,
                                     bool unwatch_exact_range, bool unprotect = true);
  B12_NOINLINE bool MayHaveWriteWatches(uint32_t virtual_address, uint32_t length) const;

  // Test helpers.
  std::vector<SystemPageFlagsBlock>& flags() { return system_page_flags_; }
  const std::vector<SystemPageFlagsBlock>& flags() const { return system_page_flags_; }
  uint32_t system_page_count() const { return system_page_count_; }
  uint32_t system_page_size() const { return system_page_size_; }

 private:
  bool e_like_ = false;
  uint32_t phys_offset_ = 0;
  uint32_t system_page_size_ = 4096;
  uint32_t system_page_count_ = 0;
  std::vector<SystemPageFlagsBlock> system_page_flags_;
};

struct HeapDesc {
  HeapType type;
  uint32_t base;
  uint32_t size;
  uint32_t page_size;
  bool e_like = false;
  uint32_t phys_offset = 0;
};

struct Layout {
  std::vector<HeapDesc> heaps;
  uint32_t virtual_commit = 0;   // bytes of the virtual arena (guest 0..)
  uint32_t physical_commit = 0;  // bytes of the physical arena
};

class MockMemory {
 public:
  explicit MockMemory(const Layout& layout) {
    virtual_size_ = layout.virtual_commit;
    physical_size_ = layout.physical_commit;
    // 64 KB reserved but not committed after each arena: running off the end
    // faults instead of silently touching other data.
    virtual_membase_ = static_cast<uint8_t*>(
        VirtualAlloc(nullptr, size_t(virtual_size_) + 0x10000, MEM_RESERVE, PAGE_NOACCESS));
    physical_membase_ = static_cast<uint8_t*>(
        VirtualAlloc(nullptr, size_t(physical_size_) + 0x10000, MEM_RESERVE, PAGE_NOACCESS));
    if (!virtual_membase_ || !physical_membase_ ||
        !VirtualAlloc(virtual_membase_, virtual_size_, MEM_COMMIT, PAGE_READWRITE) ||
        !VirtualAlloc(physical_membase_, physical_size_, MEM_COMMIT, PAGE_READWRITE)) {
      std::fprintf(stderr, "MockMemory: VirtualAlloc failed (%lu)\n", GetLastError());
      std::exit(3);
    }
    for (const HeapDesc& d : layout.heaps) {
      BaseHeap* raw;
      if (d.type == HeapType::kGuestPhysical) {
        auto h = std::make_unique<PhysicalHeap>();
        h->InitializePhysical(this, virtual_membase_, d.base, d.size, d.page_size, d.e_like,
                              d.phys_offset);
        raw = h.get();
        heaps_.push_back(std::move(h));
      } else {
        auto h = std::make_unique<BaseHeap>();
        h->Initialize(this, virtual_membase_, d.type, d.base, d.size, d.page_size);
        raw = h.get();
        heaps_.push_back(std::move(h));
      }
      table_.push_back({d.base, d.size, raw});
    }
  }
  ~MockMemory() {
    VirtualFree(virtual_membase_, 0, MEM_RELEASE);
    VirtualFree(physical_membase_, 0, MEM_RELEASE);
  }
  MockMemory(const MockMemory&) = delete;
  MockMemory& operator=(const MockMemory&) = delete;

  B12_NOINLINE const BaseHeap* LookupHeap(uint32_t address) const {
    B12_COUNT(lookup_heap);
    for (const TableEntry& e : table_) {
      if (address - e.base < e.size) {
        return e.heap;
      }
    }
    return nullptr;
  }
  BaseHeap* LookupHeap(uint32_t address) {
    return const_cast<BaseHeap*>(static_cast<const MockMemory*>(this)->LookupHeap(address));
  }

  // include/rex/system/xmemory.h
  uint8_t* TranslateVirtual(uint32_t guest_address) const {
    uint8_t* host_address = virtual_membase_ + guest_address;
    const auto heap = LookupHeap(guest_address);
    if (heap) {
      host_address += heap->host_address_offset();
    }
    return host_address;
  }
  uint8_t* TranslatePhysical(uint32_t guest_address) const {
    return physical_membase_ + (guest_address & 0x1FFFFFFF);
  }

  uint8_t* virtual_membase() const { return virtual_membase_; }
  uint8_t* physical_membase() const { return physical_membase_; }
  uint32_t virtual_size() const { return virtual_size_; }
  uint32_t physical_size() const { return physical_size_; }
  BaseHeap* heap(size_t i) { return heaps_[i].get(); }
  PhysicalHeap* physical_heap(size_t i) { return static_cast<PhysicalHeap*>(heaps_[i].get()); }
  size_t heap_count() const { return heaps_.size(); }

  std::vector<std::pair<PhysicalMemoryInvalidationCallback, void*>*>
      physical_memory_invalidation_callbacks_;

 private:
  struct TableEntry {
    uint32_t base;
    uint32_t size;
    BaseHeap* heap;
  };
  std::vector<TableEntry> table_;
  std::vector<std::unique_ptr<BaseHeap>> heaps_;
  uint8_t* virtual_membase_ = nullptr;
  uint8_t* physical_membase_ = nullptr;
  uint32_t virtual_size_ = 0;
  uint32_t physical_size_ = 0;
};

// ---------------------------------------------------------------------------
// xmemory.cpp section A helpers (working tree).
inline uint64_t LoadWatchBitsRelaxed(const uint64_t& bits) {
  return std::atomic_ref<uint64_t>(const_cast<uint64_t&>(bits)).load(std::memory_order_relaxed);
}
inline void StoreWatchBitsRelaxed(uint64_t& bits, uint64_t value) {
  std::atomic_ref<uint64_t>(bits).store(value, std::memory_order_relaxed);
}

// Working tree PhysicalHeap::EnableAccessCallbacks (data providers are not
// implemented in the SDK either).
inline void PhysicalHeap::EnableAccessCallbacks(uint32_t physical_address, uint32_t length,
                                                bool enable_invalidation_notifications,
                                                bool enable_data_providers) {
  if (!enable_invalidation_notifications && !enable_data_providers) {
    return;
  }
  uint32_t physical_address_offset = GetPhysicalAddress(heap_base_);
  if (physical_address < physical_address_offset) {
    if (physical_address_offset - physical_address >= length) {
      return;
    }
    length -= physical_address_offset - physical_address;
    physical_address = physical_address_offset;
  }
  uint32_t heap_relative_address = physical_address - physical_address_offset;
  if (heap_relative_address >= heap_size_) {
    return;
  }
  length = std::min(length, heap_size_ - heap_relative_address);
  if (length == 0) {
    return;
  }

  uint32_t system_page_first = (heap_relative_address + host_address_offset()) / system_page_size_;
  uint32_t system_page_last =
      (heap_relative_address + length - 1 + host_address_offset()) / system_page_size_;
  system_page_last = std::min(system_page_last, system_page_count_ - 1);

  PageAccess protect_access =
      enable_data_providers ? PageAccess::kNoAccess : PageAccess::kReadOnly;
  uint32_t protect_system_page_first = UINT32_MAX;
  auto global_lock = global_critical_region::AcquireDirect();
  for (uint32_t i = system_page_first; i <= system_page_last; ++i) {
    SystemPageFlagsBlock& page_flags_block = system_page_flags_[i >> 6];
    uint64_t page_flags_bit = uint64_t(1) << (i & 63);
    uint32_t guest_page_number =
        sat_sub(i * system_page_size_, host_address_offset()) >> page_size_shift_;
    if (guest_page_number >= page_table_.size()) {
      continue;
    }
    PageAccess current_page_access = ToPageAccess(page_table_[guest_page_number].current_protect);
    bool protect_system_page = false;
    if (current_page_access != PageAccess::kNoAccess) {
      if (enable_invalidation_notifications) {
        if (current_page_access != PageAccess::kReadOnly &&
            (page_flags_block.notify_on_invalidation & page_flags_bit) == 0) {
          protect_system_page = (page_flags_block.provide_data & page_flags_bit) == 0;
          StoreWatchBitsRelaxed(page_flags_block.notify_on_invalidation,
                                page_flags_block.notify_on_invalidation | page_flags_bit);
        }
      }
    }
    if (protect_system_page) {
      if (protect_system_page_first == UINT32_MAX) {
        protect_system_page_first = i;
      }
    } else {
      if (protect_system_page_first != UINT32_MAX) {
        MockProtect(heap_base_, protect_system_page_first, i - protect_system_page_first,
                    protect_access);
        protect_system_page_first = UINT32_MAX;
      }
    }
  }
  if (protect_system_page_first != UINT32_MAX) {
    MockProtect(heap_base_, protect_system_page_first,
                system_page_last + 1 - protect_system_page_first, protect_access);
  }
  // Pairs with the fence in MayHaveWriteWatches.
  std::atomic_thread_fence(std::memory_order_seq_cst);
}

// Working tree PhysicalHeap::TriggerCallbacks (= pristine + atomic_ref store
// in the clear loop).
inline bool PhysicalHeap::TriggerCallbacks(
    std::unique_lock<std::recursive_mutex> global_lock_locked_once, uint32_t virtual_address,
    uint32_t length, bool is_write, bool unwatch_exact_range, bool unprotect) {
  B12_COUNT(trigger_calls);
  if (!is_write) {
    return false;
  }

  if (virtual_address < heap_base_) {
    if (heap_base_ - virtual_address >= length) {
      return false;
    }
    length -= heap_base_ - virtual_address;
    virtual_address = heap_base_;
  }
  uint32_t heap_relative_address = virtual_address - heap_base_;
  if (heap_relative_address >= heap_size_) {
    return false;
  }
  length = std::min(length, heap_size_ - heap_relative_address);
  if (length == 0) {
    return false;
  }

  uint32_t system_page_first = (heap_relative_address + host_address_offset()) / system_page_size_;
  uint32_t system_page_last =
      (heap_relative_address + length - 1 + host_address_offset()) / system_page_size_;
  system_page_last = std::min(system_page_last, system_page_count_ - 1);
  uint32_t block_index_first = system_page_first >> 6;
  uint32_t block_index_last = system_page_last >> 6;

  // Check if watching any page, whether need to call the callback at all.
  bool any_watched = false;
  for (uint32_t i = block_index_first; i <= block_index_last; ++i) {
    uint64_t block = system_page_flags_[i].notify_on_invalidation;
    if (i == block_index_first) {
      block &= ~((uint64_t(1) << (system_page_first & 63)) - 1);
    }
    if (i == block_index_last && (system_page_last & 63) != 63) {
      block &= (uint64_t(1) << ((system_page_last & 63) + 1)) - 1;
    }
    if (block) {
      any_watched = true;
      break;
    }
  }
  if (!any_watched) {
    return false;
  }
  B12_COUNT(trigger_fired);

  // Trigger callbacks.
  if (!unprotect) {
    unwatch_exact_range = true;
  }
  uint32_t physical_address_offset = GetPhysicalAddress(heap_base_);
  uint32_t physical_address_start =
      sat_sub(system_page_first * system_page_size_, host_address_offset()) +
      physical_address_offset;
  uint32_t physical_length =
      std::min(sat_sub(system_page_last * system_page_size_ + system_page_size_,
                       host_address_offset()) +
                   physical_address_offset - physical_address_start,
               heap_size_ - (physical_address_start - physical_address_offset));
  uint32_t unwatch_first = 0;
  uint32_t unwatch_last = UINT32_MAX;
  for (auto invalidation_callback : memory_->physical_memory_invalidation_callbacks_) {
    std::pair<uint32_t, uint32_t> callback_unwatch_range = invalidation_callback->first(
        invalidation_callback->second, physical_address_start, physical_length,
        unwatch_exact_range);
    if (!unwatch_exact_range) {
      unwatch_first = std::max(unwatch_first, callback_unwatch_range.first);
      unwatch_last = std::min(
          unwatch_last, sat_add(callback_unwatch_range.first,
                                std::max(callback_unwatch_range.second, uint32_t(1)) - 1));
    }
  }
  if (!unwatch_exact_range) {
    unwatch_first = std::min(unwatch_first, physical_address_start);
    unwatch_last = std::max(unwatch_last, physical_address_start + physical_length - 1);
    const uint32_t kMaxUnwatchExcess = 4 * 1024 * 1024;
    unwatch_first = std::max(unwatch_first, physical_address_start & ~(kMaxUnwatchExcess - 1));
    unwatch_last = std::min(unwatch_last,
                            (physical_address_start + physical_length - 1) | (kMaxUnwatchExcess - 1));
    unwatch_first = sat_sub(unwatch_first, physical_address_offset);
    unwatch_last = sat_sub(unwatch_last, physical_address_offset);
    unwatch_first = std::min(unwatch_first, heap_size_ - 1);
    unwatch_last = std::min(unwatch_last, heap_size_ - 1);
    unwatch_first += host_address_offset();
    unwatch_last += host_address_offset();
    system_page_first = unwatch_first / system_page_size_;
    system_page_last = unwatch_last / system_page_size_;
    block_index_first = system_page_first >> 6;
    block_index_last = system_page_last >> 6;
  }

  // Unprotect ranges that need unprotection.
  if (unprotect) {
    uint32_t unprotect_system_page_first = UINT32_MAX;
    for (uint32_t i = system_page_first; i <= system_page_last; ++i) {
      bool unprotect_page =
          (system_page_flags_[i >> 6].notify_on_invalidation & (uint64_t(1) << (i & 63))) != 0 &&
          (system_page_flags_[i >> 6].provide_data & (uint64_t(1) << (i & 63))) == 0;
      if (unprotect_page) {
        uint32_t guest_page_number =
            sat_sub(i * system_page_size_, host_address_offset()) >> page_size_shift_;
        if (ToPageAccess(page_table_[guest_page_number].current_protect) !=
            PageAccess::kReadWrite) {
          unprotect_page = false;
        }
      }
      if (unprotect_page) {
        if (unprotect_system_page_first == UINT32_MAX) {
          unprotect_system_page_first = i;
        }
      } else {
        if (unprotect_system_page_first != UINT32_MAX) {
          MockProtect(heap_base_, unprotect_system_page_first, i - unprotect_system_page_first,
                      PageAccess::kReadWrite);
          unprotect_system_page_first = UINT32_MAX;
        }
      }
    }
    if (unprotect_system_page_first != UINT32_MAX) {
      MockProtect(heap_base_, unprotect_system_page_first,
                  system_page_last + 1 - unprotect_system_page_first, PageAccess::kReadWrite);
    }
  }

  // Mark pages as not write-watched.
  for (uint32_t i = block_index_first; i <= block_index_last; ++i) {
    uint64_t mask = 0;
    if (i == block_index_first) {
      mask |= (uint64_t(1) << (system_page_first & 63)) - 1;
    }
    if (i == block_index_last && (system_page_last & 63) != 63) {
      mask |= ~((uint64_t(1) << ((system_page_last & 63) + 1)) - 1);
    }
    StoreWatchBitsRelaxed(system_page_flags_[i].notify_on_invalidation,
                          system_page_flags_[i].notify_on_invalidation & mask);
  }

  return true;
}

// Working tree PhysicalHeap::MayHaveWriteWatches (section A).
inline bool PhysicalHeap::MayHaveWriteWatches(uint32_t virtual_address, uint32_t length) const {
  B12_COUNT(precheck_calls);
  std::atomic_thread_fence(std::memory_order_seq_cst);

  if (virtual_address < heap_base_) {
    if (heap_base_ - virtual_address >= length) {
      return false;
    }
    length -= heap_base_ - virtual_address;
    virtual_address = heap_base_;
  }
  uint32_t heap_relative_address = virtual_address - heap_base_;
  if (heap_relative_address >= heap_size_) {
    return false;
  }
  length = std::min(length, heap_size_ - heap_relative_address);
  if (length == 0) {
    return false;
  }

  uint32_t system_page_first = (heap_relative_address + host_address_offset()) / system_page_size_;
  uint32_t system_page_last =
      (heap_relative_address + length - 1 + host_address_offset()) / system_page_size_;
  system_page_last = std::min(system_page_last, system_page_count_ - 1);
  if (system_page_first > system_page_last) {
    return true;
  }
  uint32_t block_index_first = system_page_first >> 6;
  uint32_t block_index_last = system_page_last >> 6;
  for (uint32_t i = block_index_first; i <= block_index_last; ++i) {
    uint64_t block = LoadWatchBitsRelaxed(system_page_flags_[i].notify_on_invalidation);
    if (i == block_index_first) {
      block &= ~((uint64_t(1) << (system_page_first & 63)) - 1);
    }
    if (i == block_index_last && (system_page_last & 63) != 63) {
      block &= (uint64_t(1) << ((system_page_last & 63) + 1)) - 1;
    }
    if (block) {
      return true;
    }
  }
  return false;
}

}  // namespace b12
