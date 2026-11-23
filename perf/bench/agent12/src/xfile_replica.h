// Agent 12 replica benches: XFile read paths, OLD vs NEW.
//
// OLD = pristine HEAD of DimensionsRecomp/rexglue-sdk src/system/xfile.cpp
//       (XFile::Read, ReadInternal, ReadScatter).
// NEW = working tree after sections A and B (synced 2026-11-21 18:40 from
//       `git diff`): Read fast path, ReadInternal = ReadData + CompleteRead,
//       ReadScatter dispatch + ReadScatterPositional, IsSingleHostBuffer,
//       AllowsUnlockedReads, cvars io_lockless_watch_check,
//       io_coalesce_scatter_reads, io_unlocked_file_reads (all default true).
// File I/O is real: HostPathFile::ReadSync + Win32FileHandle::Read
// (src/filesystem/devices/host_path_file.cpp, src/core/filesystem_win.cpp).
#pragma once
#include "mock_memory.h"

#include <functional>
#include <shared_mutex>
#include <span>
#include <string>

namespace b12 {

namespace FileAccess {
constexpr uint32_t kGenericRead = 0x80000000;
constexpr uint32_t kGenericWrite = 0x40000000;
constexpr uint32_t kGenericExecute = 0x20000000;
constexpr uint32_t kGenericAll = 0x10000000;
constexpr uint32_t kFileReadData = 0x00000001;
constexpr uint32_t kFileWriteData = 0x00000002;
constexpr uint32_t kFileAppendData = 0x00000004;
}  // namespace FileAccess

// ---- file read fixups (xfile.cpp, unchanged by the edits) ----
using FileReadFixup =
    std::function<void(const std::string& name, uint64_t offset, uint8_t* data, size_t length)>;
inline std::vector<FileReadFixup>& FileReadFixups() {
  static std::vector<FileReadFixup> fixups;
  return fixups;
}
inline void RegisterFileReadFixup(FileReadFixup fixup) {
  FileReadFixups().push_back(std::move(fixup));
}
inline void ClearFileReadFixups() { FileReadFixups().clear(); }
B12_NOINLINE inline bool HasFileReadFixups() { return !FileReadFixups().empty(); }
B12_NOINLINE inline void ApplyFileReadFixups(const std::string& name, uint64_t offset,
                                             uint8_t* data, size_t length) {
  B12_COUNT(fixup_calls);
  for (const auto& fixup : FileReadFixups()) {
    fixup(name, offset, data, length);
  }
}

// What kind of rex::filesystem::File the replica stands for (only matters for
// AllowsUnlockedReads; the I/O is always a host file).
enum class FileKind { kHostPath, kDiscImage, kStfs };

// HostPathFile over a Win32FileHandle. overlapped=true is the rejected option
// (FILE_FLAG_OVERLAPPED handle + per-thread event), for B4 only.
class HostFile {
 public:
  static std::unique_ptr<HostFile> OpenExisting(const std::wstring& path, uint32_t desired_access,
                                                bool allow_share_delete = false,
                                                bool overlapped = false) {
    DWORD open_access = 0;
    if (desired_access & FileAccess::kGenericRead) open_access |= GENERIC_READ;
    if (desired_access & FileAccess::kGenericWrite) open_access |= GENERIC_WRITE;
    if (desired_access & FileAccess::kGenericExecute) open_access |= GENERIC_EXECUTE;
    if (desired_access & FileAccess::kGenericAll) open_access |= GENERIC_READ | GENERIC_WRITE;
    if (desired_access & FileAccess::kFileReadData) open_access |= FILE_READ_DATA;
    if (desired_access & FileAccess::kFileWriteData) open_access |= FILE_WRITE_DATA;
    if (desired_access & FileAccess::kFileAppendData) open_access |= FILE_APPEND_DATA;
    DWORD share_mode = FILE_SHARE_READ | FILE_SHARE_WRITE;
    if (allow_share_delete) share_mode |= FILE_SHARE_DELETE;
    DWORD flags = FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS;
    if (overlapped) flags |= FILE_FLAG_OVERLAPPED;
    HANDLE handle = CreateFileW(path.c_str(), open_access, share_mode, nullptr, OPEN_EXISTING,
                                flags, nullptr);
    if (handle == INVALID_HANDLE_VALUE) {
      return nullptr;
    }
    auto f = std::unique_ptr<HostFile>(new HostFile());
    f->handle_ = handle;
    f->file_access_ = desired_access;
    f->overlapped_ = overlapped;
    return f;
  }
  virtual ~HostFile() {
    if (handle_) CloseHandle(handle_);
  }

  uint32_t file_access() const { return file_access_; }
  void set_file_access_for_test(uint32_t a) { file_access_ = a; }
  HANDLE handle() const { return handle_; }
  FileKind kind = FileKind::kHostPath;

  // HostPathFile::ReadSync (virtual in the SDK).
  B12_NOINLINE virtual X_STATUS ReadSync(std::span<uint8_t> buffer, size_t byte_offset,
                                         size_t* out_bytes_read) {
    if (!(file_access_ & (FileAccess::kGenericRead | FileAccess::kFileReadData))) {
      return X_STATUS_ACCESS_DENIED;
    }
    if (Read(byte_offset, buffer.data(), buffer.size(), out_bytes_read)) {
      return X_STATUS_SUCCESS;
    } else {
      return X_STATUS_END_OF_FILE;
    }
  }

 private:
  HostFile() = default;

  // Win32FileHandle::Read.
  bool Read(size_t file_offset, void* buffer, size_t buffer_length, size_t* out_bytes_read) {
    B12_COUNT(readfile_calls);
    *out_bytes_read = 0;
    if (overlapped_) {
      return ReadOverlapped(file_offset, buffer, buffer_length, out_bytes_read);
    }
    OVERLAPPED overlapped;
    overlapped.Pointer = (PVOID)file_offset;
    overlapped.hEvent = NULL;
    DWORD bytes_read = 0;
    BOOL read = ReadFile(handle_, buffer, (DWORD)buffer_length, &bytes_read, &overlapped);
    if (read) {
      *out_bytes_read = bytes_read;
      return true;
    } else {
      last_error_ = GetLastError();
      return false;
    }
  }

  bool ReadOverlapped(size_t file_offset, void* buffer, size_t buffer_length,
                      size_t* out_bytes_read) {
    thread_local HANDLE event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    OVERLAPPED overlapped = {};
    overlapped.Pointer = (PVOID)file_offset;
    overlapped.hEvent = event;
    DWORD bytes_read = 0;
    if (!ReadFile(handle_, buffer, (DWORD)buffer_length, nullptr, &overlapped)) {
      DWORD err = GetLastError();
      if (err != ERROR_IO_PENDING) {
        last_error_ = err;
        return false;
      }
    }
    if (!GetOverlappedResult(handle_, &overlapped, &bytes_read, TRUE)) {
      last_error_ = GetLastError();
      return false;
    }
    *out_bytes_read = bytes_read;
    return true;
  }

 public:
  DWORD last_error_ = 0;  // test hook: GetLastError of the last failed ReadFile

 private:
  HANDLE handle_ = nullptr;
  uint32_t file_access_ = 0;
  bool overlapped_ = false;
};

// NEW (xfile.cpp anonymous namespace).
inline bool AllowsUnlockedReads(const HostFile* file) {
  if (!file || (file->file_access() & (FileAccess::kGenericWrite | FileAccess::kGenericAll |
                                       FileAccess::kFileWriteData | FileAccess::kFileAppendData))) {
    return false;
  }
  return file->kind == FileKind::kHostPath || file->kind == FileKind::kDiscImage;
}

// NEW: the host byte that ReadData writes for guest_address.
inline const uint8_t* ReadDestination(const MockMemory* memory, const BaseHeap* heap,
                                      uint32_t guest_address) {
  return heap->heap_type() == HeapType::kGuestPhysical
             ? memory->TranslatePhysical(
                   static_cast<const PhysicalHeap*>(heap)->GetPhysicalAddress(guest_address))
             : memory->TranslateVirtual(guest_address);
}

// NEW: whether ReadData can take [guest_address, guest_address + length) as
// one buffer: a single heap, with contiguous host bytes behind it.
inline bool IsSingleHostBuffer(const MockMemory* memory, uint32_t guest_address,
                               uint32_t length) {
  const uint64_t last = uint64_t(guest_address) + length - 1;
  if (!length || last > UINT32_MAX) {
    return false;
  }
  const BaseHeap* heap = memory->LookupHeap(guest_address);
  if (!heap || memory->LookupHeap(uint32_t(last)) != heap) {
    return false;
  }
  return ReadDestination(memory, heap, uint32_t(last)) -
             ReadDestination(memory, heap, guest_address) ==
         ptrdiff_t(length - 1);
}

struct IONotification {
  uint32_t key_context = 0;
  uint32_t apc_context = 0;
  uint32_t num_bytes = 0;
  uint32_t status = 0;
};

// cvars (NEW) + a bench-only knob for "pristine code with the section A
// guard" (B1 variant OLD+A).
struct XFileKnobs {
  bool io_lockless_watch_check = true;
  bool io_coalesce_scatter_reads = true;
  bool io_unlocked_file_reads = true;
  bool old_with_precheck = false;
};

enum class ScatterPath { kNone, kOld, kPositional };

// rex::be<uint32_t> as stored in guest memory.
struct be32 {
  uint32_t raw;
  operator uint32_t() const { return _byteswap_ulong(raw); }
};

class XFileReplica {
 public:
  XFileReplica(MockMemory* memory, HostFile* file, std::string name)
      : memory_(memory), file_(file), name_(std::move(name)) {
    async_event_ = CreateEventW(nullptr, FALSE, FALSE, nullptr);  // auto-reset
    unlocked_reads_ok_ = AllowsUnlockedReads(file_);
  }
  ~XFileReplica() { CloseHandle(async_event_); }
  XFileReplica(const XFileReplica&) = delete;
  XFileReplica& operator=(const XFileReplica&) = delete;

  void RefreshUnlockedReadsOk() { unlocked_reads_ok_ = AllowsUnlockedReads(file_); }
  void set_file(HostFile* f) {
    file_ = f;
    RefreshUnlockedReadsOk();
  }

  // =================== OLD (pristine HEAD) ===================
  X_STATUS ReadOld(uint32_t buffer_guest_address, uint32_t buffer_length, uint64_t byte_offset,
                   uint32_t* out_bytes_read, uint32_t apc_context, bool notify_completion = true) {
    std::lock_guard<std::mutex> lock(file_lock_);
    B12_COUNT(file_lock);
    return ReadInternalOld(buffer_guest_address, buffer_length, byte_offset, out_bytes_read,
                           apc_context, notify_completion);
  }

  X_STATUS ReadScatterOld(uint32_t segments_guest_address, uint32_t length, uint64_t byte_offset,
                          uint32_t* out_bytes_read, uint32_t apc_context) {
    std::lock_guard<std::mutex> lock(file_lock_);
    B12_COUNT(file_lock);
    return ScatterLoop<false>(segments_guest_address, length, byte_offset, out_bytes_read,
                              apc_context);
  }

  // =================== NEW (working tree) ===================
  X_STATUS ReadNew(uint32_t buffer_guest_address, uint32_t buffer_length, uint64_t byte_offset,
                   uint32_t* out_bytes_read, uint32_t apc_context, bool notify_completion = true) {
    if (unlocked_reads_ok_ && byte_offset != uint64_t(-1) && byte_offset != uint64_t(-2) &&
        knobs.io_unlocked_file_reads) {
      size_t bytes_read = 0;
      X_STATUS result;
      {
        std::shared_lock<std::shared_mutex> read_lock(unlocked_read_lock_);
        B12_COUNT(shared_lock);
        result = ReadData(buffer_guest_address, buffer_length, byte_offset, &bytes_read);
      }
      std::lock_guard<std::mutex> lock(file_lock_);
      B12_COUNT(file_lock);
      return CompleteRead(result, buffer_length, byte_offset, bytes_read, out_bytes_read,
                          apc_context, notify_completion);
    }
    std::lock_guard<std::mutex> lock(file_lock_);
    B12_COUNT(file_lock);
    return ReadInternalNew(buffer_guest_address, buffer_length, byte_offset, out_bytes_read,
                           apc_context, notify_completion);
  }

  X_STATUS ReadScatterNew(uint32_t segments_guest_address, uint32_t length, uint64_t byte_offset,
                          uint32_t* out_bytes_read, uint32_t apc_context) {
    if (byte_offset && byte_offset < uint64_t(-2) - length) {
      const bool coalesce = knobs.io_coalesce_scatter_reads;
      const bool unlocked = unlocked_reads_ok_ && knobs.io_unlocked_file_reads;
      if (coalesce || unlocked) {
        last_path = ScatterPath::kPositional;
        return ReadScatterPositional(segments_guest_address, length, byte_offset, out_bytes_read,
                                     apc_context, coalesce, unlocked);
      }
    }
    last_path = ScatterPath::kOld;
    std::lock_guard<std::mutex> lock(file_lock_);
    B12_COUNT(file_lock);
    return ScatterLoop<true>(segments_guest_address, length, byte_offset, out_bytes_read,
                             apc_context);
  }

  uint64_t position_ = 0;
  XFileKnobs knobs;
  bool unlocked_reads_ok_ = false;
  ScatterPath last_path = ScatterPath::kNone;  // test hook
  IONotification last_notification;           // test hook

 private:
  MockMemory* memory() const { return memory_; }
  const std::string& name() const { return name_; }

  void SetAsyncEvent() {
    B12_COUNT(event_sets);
    SetEvent(async_event_);
  }

  // XFile::NotifyIOCompletionPorts (no ports are ever bound in the game).
  void NotifyIOCompletionPorts(IONotification& notification) {
    std::lock_guard<std::mutex> lock(completion_port_lock_);
    B12_COUNT(notify_calls);
    last_notification = notification;
    for (uint32_t port_key : completion_ports_) {
      notification.key_context = port_key;
    }
  }

  // OLD ReadScatter body (pristine) with ReadInternal = OLD or NEW version
  // (the NEW ReadScatter falls back to this loop, calling the NEW
  // ReadInternal, for offsets 0/-1/-2 and when both cvars are off).
  template <bool kNewInternal>
  X_STATUS ScatterLoop(uint32_t segments_guest_address, uint32_t length, uint64_t byte_offset,
                       uint32_t* out_bytes_read, uint32_t apc_context) {
    X_STATUS result = X_STATUS_SUCCESS;
    const be32* segments =
        reinterpret_cast<const be32*>(memory()->TranslateVirtual(segments_guest_address));
    uint32_t page_size = 4096;
    uint32_t read_total = 0;
    uint32_t read_remain = length;
    while (read_remain) {
      uint32_t read_length = read_remain;
      uint32_t read_buffer = *segments;
      if (read_length > page_size) {
        read_length = page_size;
        segments++;
      }
      uint32_t bytes_read = 0;
      uint64_t seg_offset =
          byte_offset ? ((byte_offset != uint64_t(-1) && byte_offset != uint64_t(-2))
                             ? byte_offset + read_total
                             : byte_offset)
                      : uint64_t(-1);
      if constexpr (kNewInternal) {
        result = ReadInternalNew(read_buffer, read_length, seg_offset, &bytes_read, apc_context,
                                 false);
      } else {
        result = ReadInternalOld(read_buffer, read_length, seg_offset, &bytes_read, apc_context,
                                 false);
      }
      if (result != X_STATUS_SUCCESS) {
        break;
      }
      read_total += bytes_read;
      read_remain -= read_length;
    }
    if (out_bytes_read) {
      *out_bytes_read = uint32_t(read_total);
    }
    IONotification notify;
    notify.apc_context = apc_context;
    notify.num_bytes = uint32_t(read_total);
    notify.status = result;
    NotifyIOCompletionPorts(notify);
    SetAsyncEvent();
    return result;
  }

  // Pristine XFile::ReadInternal. knobs.old_with_precheck adds only the
  // section A guard in front of TriggerCallbacks (bench variant OLD+A).
  X_STATUS ReadInternalOld(uint32_t buffer_guest_address, uint32_t buffer_length,
                           uint64_t byte_offset, uint32_t* out_bytes_read, uint32_t apc_context,
                           bool notify_completion) {
    if (byte_offset == uint64_t(-1)) {
      byte_offset = position_;
    }
    size_t bytes_read = 0;
    X_STATUS result = X_STATUS_SUCCESS;
    if (buffer_length) {
      if (UINT32_MAX - buffer_guest_address < buffer_length) {
        result = X_STATUS_ACCESS_VIOLATION;
      } else {
        uint32_t buffer_guest_high_address = buffer_guest_address + buffer_length - 1;
        BaseHeap* buffer_start_heap = memory()->LookupHeap(buffer_guest_address);
        const BaseHeap* buffer_end_heap =
            static_cast<const MockMemory*>(memory())->LookupHeap(buffer_guest_high_address);
        if (!buffer_start_heap || !buffer_end_heap ||
            (buffer_start_heap->heap_type() == HeapType::kGuestPhysical) !=
                (buffer_end_heap->heap_type() == HeapType::kGuestPhysical) ||
            (buffer_start_heap->heap_type() == HeapType::kGuestPhysical &&
             buffer_start_heap != buffer_end_heap)) {
          result = X_STATUS_ACCESS_VIOLATION;
        } else {
          PhysicalHeap* buffer_physical_heap =
              buffer_start_heap->heap_type() == HeapType::kGuestPhysical
                  ? static_cast<PhysicalHeap*>(buffer_start_heap)
                  : nullptr;
          if (buffer_physical_heap &&
              buffer_physical_heap->QueryRangeAccess(buffer_guest_address,
                                                     buffer_guest_high_address) !=
                  PageAccess::kReadWrite) {
            result = X_STATUS_ACCESS_VIOLATION;
          } else {
            result = file_->ReadSync(
                std::span<uint8_t>(buffer_physical_heap
                                       ? memory()->TranslatePhysical(
                                             buffer_physical_heap->GetPhysicalAddress(
                                                 buffer_guest_address))
                                       : memory()->TranslateVirtual(buffer_guest_address),
                                   buffer_length),
                size_t(byte_offset), &bytes_read);
            if (XSUCCEEDED(result)) {
              if (HasFileReadFixups() && bytes_read) {
                ApplyFileReadFixups(name(), byte_offset,
                                    buffer_physical_heap
                                        ? memory()->TranslatePhysical(
                                              buffer_physical_heap->GetPhysicalAddress(
                                                  buffer_guest_address))
                                        : memory()->TranslateVirtual(buffer_guest_address),
                                    bytes_read);
              }
              if (buffer_physical_heap &&
                  (!knobs.old_with_precheck ||
                   buffer_physical_heap->MayHaveWriteWatches(buffer_guest_address,
                                                             buffer_length))) {
                buffer_physical_heap->TriggerCallbacks(
                    global_critical_region::AcquireDirect(), buffer_guest_address, buffer_length,
                    true, true);
              }
              if (byte_offset) {
                position_ = byte_offset;
              }
              position_ += bytes_read;
            }
          }
        }
      }
    }
    if (out_bytes_read) {
      *out_bytes_read = uint32_t(bytes_read);
    }
    if (notify_completion) {
      IONotification notify;
      notify.apc_context = apc_context;
      notify.num_bytes = uint32_t(bytes_read);
      notify.status = result;
      NotifyIOCompletionPorts(notify);
      SetAsyncEvent();
    }
    return result;
  }

  // NEW XFile::ReadInternal.
  X_STATUS ReadInternalNew(uint32_t buffer_guest_address, uint32_t buffer_length,
                           uint64_t byte_offset, uint32_t* out_bytes_read, uint32_t apc_context,
                           bool notify_completion) {
    if (byte_offset == uint64_t(-1)) {
      byte_offset = position_;
    }
    size_t bytes_read = 0;
    X_STATUS result = ReadData(buffer_guest_address, buffer_length, byte_offset, &bytes_read);
    return CompleteRead(result, buffer_length, byte_offset, bytes_read, out_bytes_read,
                        apc_context, notify_completion);
  }

  // NEW XFile::ReadData.
  X_STATUS ReadData(uint32_t buffer_guest_address, uint32_t buffer_length, uint64_t byte_offset,
                    size_t* out_bytes_read) {
    size_t bytes_read = 0;
    X_STATUS result = X_STATUS_SUCCESS;
    if (buffer_length) {
      if (UINT32_MAX - buffer_guest_address < buffer_length) {
        result = X_STATUS_ACCESS_VIOLATION;
      } else {
        uint32_t buffer_guest_high_address = buffer_guest_address + buffer_length - 1;
        BaseHeap* buffer_start_heap = memory()->LookupHeap(buffer_guest_address);
        const BaseHeap* buffer_end_heap =
            static_cast<const MockMemory*>(memory())->LookupHeap(buffer_guest_high_address);
        if (!buffer_start_heap || !buffer_end_heap ||
            (buffer_start_heap->heap_type() == HeapType::kGuestPhysical) !=
                (buffer_end_heap->heap_type() == HeapType::kGuestPhysical) ||
            (buffer_start_heap->heap_type() == HeapType::kGuestPhysical &&
             buffer_start_heap != buffer_end_heap)) {
          result = X_STATUS_ACCESS_VIOLATION;
        } else {
          PhysicalHeap* buffer_physical_heap =
              buffer_start_heap->heap_type() == HeapType::kGuestPhysical
                  ? static_cast<PhysicalHeap*>(buffer_start_heap)
                  : nullptr;
          if (buffer_physical_heap &&
              buffer_physical_heap->QueryRangeAccess(buffer_guest_address,
                                                     buffer_guest_high_address) !=
                  PageAccess::kReadWrite) {
            result = X_STATUS_ACCESS_VIOLATION;
          } else {
            result = file_->ReadSync(
                std::span<uint8_t>(buffer_physical_heap
                                       ? memory()->TranslatePhysical(
                                             buffer_physical_heap->GetPhysicalAddress(
                                                 buffer_guest_address))
                                       : memory()->TranslateVirtual(buffer_guest_address),
                                   buffer_length),
                size_t(byte_offset), &bytes_read);
            if (XSUCCEEDED(result)) {
              if (HasFileReadFixups() && bytes_read) {
                ApplyFileReadFixups(name(), byte_offset,
                                    buffer_physical_heap
                                        ? memory()->TranslatePhysical(
                                              buffer_physical_heap->GetPhysicalAddress(
                                                  buffer_guest_address))
                                        : memory()->TranslateVirtual(buffer_guest_address),
                                    bytes_read);
              }
              if (buffer_physical_heap &&
                  (!knobs.io_lockless_watch_check ||
                   buffer_physical_heap->MayHaveWriteWatches(buffer_guest_address,
                                                             buffer_length))) {
                buffer_physical_heap->TriggerCallbacks(
                    global_critical_region::AcquireDirect(), buffer_guest_address, buffer_length,
                    true, true);
              }
            }
          }
        }
      }
    }
    *out_bytes_read = bytes_read;
    return result;
  }

  // NEW XFile::CompleteRead (caller holds file_lock_).
  X_STATUS CompleteRead(X_STATUS result, uint32_t buffer_length, uint64_t byte_offset,
                        size_t bytes_read, uint32_t* out_bytes_read, uint32_t apc_context,
                        bool notify_completion) {
    if (XSUCCEEDED(result) && buffer_length) {
      if (byte_offset) {
        position_ = byte_offset;
      }
      position_ += bytes_read;
    }
    if (out_bytes_read) {
      *out_bytes_read = uint32_t(bytes_read);
    }
    if (notify_completion) {
      IONotification notify;
      notify.apc_context = apc_context;
      notify.num_bytes = uint32_t(bytes_read);
      notify.status = result;
      NotifyIOCompletionPorts(notify);
      SetAsyncEvent();
    }
    return result;
  }

  // NEW XFile::ReadScatterPositional.
  X_STATUS ReadScatterPositional(uint32_t segments_guest_address, uint32_t length,
                                 uint64_t byte_offset, uint32_t* out_bytes_read,
                                 uint32_t apc_context, bool coalesce, bool unlocked) {
    std::unique_lock<std::mutex> lock(file_lock_, std::defer_lock);
    std::shared_lock<std::shared_mutex> read_lock(unlocked_read_lock_, std::defer_lock);
    if (unlocked) {
      read_lock.lock();
      B12_COUNT(shared_lock);
    } else {
      lock.lock();
      B12_COUNT(file_lock);
    }
    X_STATUS result = X_STATUS_SUCCESS;

    const be32* segments =
        reinterpret_cast<const be32*>(memory()->TranslateVirtual(segments_guest_address));
    const uint32_t page_size = 4096;

    uint32_t read_total = 0;
    uint32_t read_remain = length;
    bool position_set = false;
    uint64_t new_position = 0;
    uint32_t single_pages = 0;
    while (read_remain) {
      if (coalesce && !single_pages && read_remain > page_size) {
        const uint64_t run_start = uint32_t(segments[0]);
        uint32_t run_pages = 1;
        while (uint64_t(run_pages) * page_size < read_remain &&
               uint32_t(segments[run_pages]) == run_start + uint64_t(run_pages) * page_size) {
          ++run_pages;
        }
        if (run_pages > 1) {
          const uint32_t run_length =
              uint32_t(std::min<uint64_t>(uint64_t(run_pages) * page_size, read_remain));
          const uint64_t run_offset = byte_offset + read_total;
          size_t run_bytes = 0;
          if (IsSingleHostBuffer(memory(), uint32_t(run_start), run_length) &&
              ReadData(uint32_t(run_start), run_length, run_offset, &run_bytes) ==
                  X_STATUS_SUCCESS &&
              run_bytes == run_length) {
            position_set = true;
            new_position = run_offset + run_length;
            read_total += run_length;
            read_remain -= run_length;
            segments += run_pages;
            continue;
          }
          single_pages = run_pages;
        }
      }
      if (single_pages) {
        --single_pages;
      }

      uint32_t read_length = read_remain;
      uint32_t read_buffer = *segments;
      if (read_length > page_size) {
        read_length = page_size;
        segments++;
      }

      const uint64_t read_offset = byte_offset + read_total;
      size_t bytes_read = 0;
      result = ReadData(read_buffer, read_length, read_offset, &bytes_read);
      if (XSUCCEEDED(result)) {
        position_set = true;
        new_position = read_offset + bytes_read;
      }

      if (result != X_STATUS_SUCCESS) {
        break;
      }

      read_total += uint32_t(bytes_read);
      read_remain -= read_length;
    }

    if (unlocked) {
      read_lock.unlock();
      lock.lock();
      B12_COUNT(file_lock);
    }
    if (position_set) {
      position_ = new_position;
    }

    if (out_bytes_read) {
      *out_bytes_read = uint32_t(read_total);
    }

    IONotification notify;
    notify.apc_context = apc_context;
    notify.num_bytes = uint32_t(read_total);
    notify.status = result;
    NotifyIOCompletionPorts(notify);
    SetAsyncEvent();
    return result;
  }

  MockMemory* memory_;
  HostFile* file_;
  std::string name_;
  HANDLE async_event_ = nullptr;
  std::mutex file_lock_;
  std::shared_mutex unlocked_read_lock_;
  std::mutex completion_port_lock_;
  std::vector<uint32_t> completion_ports_;
};

}  // namespace b12
