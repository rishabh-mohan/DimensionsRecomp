#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <limits>
#if defined(_M_X64) || defined(__x86_64__)
#include <immintrin.h>
#endif

namespace native_heap_diagnostics {
enum class Operation : uint32_t { kAllocated = 1, kFreeBegin = 2, kFreeComplete = 3 };
struct Event {
  uint64_t sequence = 0, key = 0;
  uint32_t pointer = 0, heap = 0, caller = 0, frame = 0, thread = 0, bytes = 0;
  Operation operation{};
};
struct History { std::array<Event,8> events{}; uint32_t count = 0; };

// Diagnostics only. This records observations without interpreting allocator
// flags, changing guest memory, bypassing a free, or allocating in a hot hook.
// A bounded bucket can evict old observations; absence proves nothing.
//
// Layout for the per-alloc/free Record: a bucket's lock bit and next slot
// share one word in a 32 KiB array, apart from its eight 32-byte slots, so a
// Record touches one small hot word and half a cache line. A slot keeps the
// operation in the top bits of its sequence and the key is recomputed from the
// pointer, so Read returns exactly the Events that storing them whole would.
class Journal {
  struct Slot {
    uint64_t sequence_operation = 0;  // sequence | operation << kOperationShift
    uint32_t pointer = 0, heap = 0, caller = 0, frame = 0, thread = 0, bytes = 0;
  };
  static_assert(sizeof(Slot) == 32);
  struct alignas(64) Ring { std::array<Slot,8> slots{}; };
  static constexpr uint32_t kBusy = 1u << 31;
  // Sequences stay below 2^62: that many records takes centuries.
  static constexpr int kOperationShift = 62;
  static constexpr uint64_t kSequenceMask = (1ull << kOperationShift) - 1;
  static_assert(uint32_t(Operation::kFreeComplete) < 4);
  std::array<std::atomic<uint32_t>,8192> state_{};  // kBusy | next slot (0-7)
  std::array<Ring,8192> rings_{};
  alignas(64) std::atomic<uint64_t> sequence_{0};
  static uint32_t Index(uint64_t key) {
    key ^= key >> 33; key *= 0xff51afd7ed558ccdull;
    key ^= key >> 33;
    return uint32_t(key) & 8191;
  }
  // Locks one bucket and returns its next slot.
  uint32_t Acquire(uint32_t index) {
    auto& state = state_[index];
    uint32_t value = state.load(std::memory_order_relaxed);
    for (;;) {
      if (!(value & kBusy) && state.compare_exchange_weak(value, value | kBusy,
                                  std::memory_order_acquire, std::memory_order_relaxed))
        return value;
#if defined(_M_X64) || defined(__x86_64__)
      _mm_pause();
#endif
      value = state.load(std::memory_order_relaxed);
    }
  }
  void Release(uint32_t index, uint32_t next) {
    state_[index].store(next, std::memory_order_release);
  }
 public:
  static uint64_t Key(uint32_t pointer) {
    if (pointer >= 0xA0000000u) {
      const uint32_t view = pointer < 0xC0000000u ? 0xA0000000u :
                            pointer < 0xE0000000u ? 0xC0000000u : 0xE0000000u;
      const uint64_t physical = uint64_t(pointer - view) + (view == 0xE0000000u ? 4096 : 0);
      if (physical < 0x20000000u) return (1ull << 32) | physical;
    }
    return pointer;
  }
  uint64_t Record(Operation operation, uint32_t pointer, uint32_t heap,
                  uint32_t caller, uint32_t frame, uint32_t thread, uint32_t bytes = 0) {
    if (!pointer) return 0;
    const uint32_t index = Index(Key(pointer));
    const uint32_t next = Acquire(index);
    const uint64_t sequence = sequence_.fetch_add(1,std::memory_order_relaxed) + 1;
    if (!sequence) { Release(index, next); return 0; }
    rings_[index].slots[next] = {sequence | uint64_t(operation) << kOperationShift,
                                 pointer,heap,caller,frame,thread,bytes};
    Release(index, (next+1) & 7);
    return sequence;
  }
  History Read(uint32_t pointer) {
    History result;
    if (!pointer) return result;
    const uint64_t key = Key(pointer);
    const uint32_t index = Index(key);
    const uint32_t next = Acquire(index);
    // Walk oldest-to-newest without sorting or allocating under the lock.
    for (uint32_t n=0; n<8; ++n) {
      const Slot& slot = rings_[index].slots[(next+n)&7];
      const uint64_t sequence = slot.sequence_operation & kSequenceMask;
      if (sequence && Key(slot.pointer) == key)
        result.events[result.count++] = {sequence,key,slot.pointer,slot.heap,slot.caller,
            slot.frame,slot.thread,slot.bytes,Operation(slot.sequence_operation >> kOperationShift)};
    }
    Release(index, next);
    return result;
  }
};
} // namespace native_heap_diagnostics
