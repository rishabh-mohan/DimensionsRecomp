#!/usr/bin/env python3
"""S4 #19 (R1 stage 2, d3d12_async_submit, OFF, kInitOnly): staging generator.

Reads the S4b base copies in orig/sdk (byte copies of
build/agent2/snap1/DimensionsRecomp/rexglue-sdk, checked here), applies exact-once
edits, writes new/sdk, s4-r1s2.diff (paths relative to rexglue-sdk), SHA256SUMS.txt
and PROOFS.txt. Stdlib only. Read-only on build/agent2. No compile, no git writes.

    python -B build/agent7/s4-r1s2/make_s4r1s2.py
"""
import difflib
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SNAP_SDK = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'DimensionsRecomp', 'rexglue-sdk')
PATCHES_S4B = os.path.join(ROOT, 'build', 'agent2', 'snap1', 'PATCHES-S4b.tsv')
ORIG = os.path.join(HERE, 'orig', 'sdk')
NEW = os.path.join(HERE, 'new', 'sdk')

CP_H = 'include/rex/graphics/d3d12/command_processor.h'
DCL_H = 'include/rex/graphics/d3d12/deferred_command_list.h'
CP_CPP = 'src/graphics/d3d12/command_processor.cpp'
DCL_CPP = 'src/graphics/d3d12/deferred_command_list.cpp'  # unchanged, base check only
SM_CPP = 'src/graphics/d3d12/shared_memory.cpp'
TC_CPP = 'src/graphics/d3d12/texture_cache.cpp'
FILES = [CP_H, DCL_H, CP_CPP, SM_CPP, TC_CPP]
BASE_ONLY = [DCL_CPP]

# S4b after-hashes (prefixes) from PATCHES-S4b.tsv / build/agent2/s4b; texture_cache.cpp
# is not patched in S4b, so it is checked against the snap1 bytes only.
S4B_PREFIX = {
    CP_H: '67F4E8380C879377',
    DCL_H: '9F6CC70A6922232D',
    CP_CPP: '027204B53A271D69',
    DCL_CPP: '30FF57446EFB5D76',
    SM_CPP: '2A5ADF13B5E433F1',
}

EDITS = []  # (id, file, kind, anchor, replacement)


def edit(eid, rel, kind, anchor, replacement):
    EDITS.append((eid, rel, kind, anchor, replacement))


# ---------------------------------------------------------------- command_processor.h
edit('E1', CP_H, 'include', '#include <chrono>\n#include <deque>\n',
     '#include <chrono>\n#include <condition_variable>\n#include <deque>\n')

edit('E2', CP_H, 'include', '#include <rex/system/kernel_state.h>\n',
     '#include <rex/system/kernel_state.h>\n#include <rex/thread.h>\n')

edit('E3', CP_H, 'public-inline-guarded',
     '''  void NotifyQueueOperationsDoneDirectly() {
    queue_operations_done_since_submission_signal_ = true;
  }
''',
     '''  void NotifyQueueOperationsDoneDirectly() {
    queue_operations_done_since_submission_signal_ = true;
  }

  // S4 #19 (R1 stage 2): call before doing a queue operation like
  // UpdateTileMappings directly. With d3d12_async_submit on, it waits until the
  // submit thread has submitted the splits queued before it, so the queue sees
  // them first, as without the thread. Otherwise it does nothing.
  void FlushAsyncSubmissions() {
    if (submit_async_) {
      DrainAsyncSubmissions();
    }
  }
''')

edit('E4', CP_H, 'declarations',
     '''  void MaybeSplitSubmission();
  bool AwaitAllQueueOperationsCompletion() {
''',
     '''  void MaybeSplitSubmission();
  // S4 #19 (R1 stage 2), with d3d12_async_submit on: EndSubmissionAsync is
  // EndSubmission(false) for a split, with the Reset, Execute, Close,
  // ExecuteCommandLists and Signal handed to the submit thread
  // (AsyncSubmitThread). DrainAsyncSubmissions waits until that thread has
  // submitted everything queued. ShutdownAsyncSubmit stops the thread.
  bool EndSubmissionAsync();
  void DrainAsyncSubmissions();
  void AsyncSubmitThread();
  void ShutdownAsyncSubmit();
  bool AwaitAllQueueOperationsCompletion() {
''')

edit('E5', CP_H, 'members',
     '''  std::chrono::steady_clock::time_point submit_split_last_log_{};
};
''',
     '''  std::chrono::steady_clock::time_point submit_split_last_log_{};

  // S4 #19 (R1 stage 2): set in SetupContext from the kInitOnly cvar
  // d3d12_async_submit, only with the split on and the submit thread running.
  bool submit_async_ = false;
  // Queued splits, in submission order: a ring of kAsyncSubmitSlots, the
  // oldest at async_submit_first_. A slot stays counted until the submit
  // thread has signalled its fence value, so a full ring makes the GPU
  // Commands thread wait.
  static constexpr uint32_t kAsyncSubmitSlots = 3;
  struct AsyncSubmission {
    explicit AsyncSubmission(const D3D12CommandProcessor& command_processor)
        : deferred_command_list(command_processor) {}
    DeferredCommandList deferred_command_list;
    ID3D12CommandAllocator* command_allocator = nullptr;
    uint64_t submission = 0;
  };
  std::unique_ptr<AsyncSubmission> async_submit_slots_[kAsyncSubmitSlots];
  std::unique_ptr<rex::thread::Thread> async_submit_thread_;
  std::mutex async_submit_mutex_;
  // Notified when a split is queued or the thread is asked to stop.
  std::condition_variable async_submit_work_cond_;
  // Notified when the submit thread has finished a split.
  std::condition_variable async_submit_idle_cond_;
  // Protected with async_submit_mutex_ (the ring, the stop flag, the stats).
  uint32_t async_submit_first_ = 0;
  uint32_t async_submit_count_ = 0;
  bool async_submit_stop_ = false;
  struct AsyncSubmitStats {
    uint64_t chunks = 0;
    uint64_t queued_max = 0;
    uint64_t full_waits = 0;
    uint64_t full_wait_ns = 0;
    uint64_t drains_waited = 0;
    uint64_t drain_wait_ns = 0;
    uint64_t worker_ns = 0;
  } async_submit_stats_;
  // GPU Commands thread only.
  std::chrono::steady_clock::time_point async_submit_last_log_{};
};
''')

# ---------------------------------------------------------------- deferred_command_list.h
edit('E6', DCL_H, 'inline-unused-when-off',
     '''  size_t GetSizeBytes() const { return command_stream_.size() * sizeof(uintmax_t); }
''',
     '''  size_t GetSizeBytes() const { return command_stream_.size() * sizeof(uintmax_t); }

  // S4 #19 (R1 stage 2): exchanges the recorded commands with another list of
  // the same command processor (a split queued for the submit thread).
  void Swap(DeferredCommandList& other) {
    assert_true(&command_processor_ == &other.command_processor_);
    command_stream_.swap(other.command_stream_);
  }
''')

# ---------------------------------------------------------------- command_processor.cpp
edit('E7', CP_CPP, 'cvar',
     '''REXCVAR_DEFINE_UINT32(d3d12_submit_split_kb, 0, "GPU/D3D12",
                      "Split a submission mid-frame once its deferred command list reaches "
                      "this many KB (0 = off)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
''',
     '''REXCVAR_DEFINE_UINT32(d3d12_submit_split_kb, 0, "GPU/D3D12",
                      "Split a submission mid-frame once its deferred command list reaches "
                      "this many KB (0 = off)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

// S4 #19 (R1 stage 2): with d3d12_submit_split_kb on, hand the submit of each
// split (Reset, Execute, Close, ExecuteCommandLists, Signal) to a thread of
// its own, so the GPU Commands thread can record on. Fence values are still
// given out in order on the GPU Commands thread. Every other submit, and every
// other queue operation of the GPU Commands thread, first waits until the
// thread has submitted the splits queued before it, so the queue sees the same
// order as without it. Read once in SetupContext; nothing changes while
// d3d12_submit_split_kb is 0. Leave it off on native builds unless tested there.
REXCVAR_DEFINE_BOOL(d3d12_async_submit, false, "GPU/D3D12",
                    "Submit mid-frame splits (d3d12_submit_split_kb) on a separate thread")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
''')

edit('E8', CP_CPP, 'setup',
     '''  // Just not to expose uninitialized memory.
  std::memset(&system_constants_, 0, sizeof(system_constants_));

  return true;
}
''',
     '''  // Just not to expose uninitialized memory.
  std::memset(&system_constants_, 0, sizeof(system_constants_));

  // S4 #19: the submit thread, started last so that a failed setup leaves no
  // thread behind. Cached once (the cvar is kInitOnly); off unless the split
  // is on.
  submit_async_ = false;
  async_submit_stats_ = {};
  async_submit_last_log_ = {};
  if (REXCVAR_GET(d3d12_async_submit)) {
    if (!submit_split_bytes_) {
      REXGPU_WARN("d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off");
    } else {
      for (auto& slot : async_submit_slots_) {
        slot = std::make_unique<AsyncSubmission>(*this);
      }
      async_submit_first_ = 0;
      async_submit_count_ = 0;
      async_submit_stop_ = false;
      async_submit_thread_ = rex::thread::Thread::Create({}, [this]() { AsyncSubmitThread(); });
      if (async_submit_thread_) {
        async_submit_thread_->set_name("D3D12 Submit");
        submit_async_ = true;
        REXGPU_INFO("d3d12_async_submit: submitting splits on the submit thread ({} slots)",
                    uint32_t(kAsyncSubmitSlots));
      } else {
        REXGPU_ERROR("d3d12_async_submit: failed to create the submit thread, staying off");
        for (auto& slot : async_submit_slots_) {
          slot.reset();
        }
      }
    }
  }

  return true;
}
''')

edit('E9', CP_CPP, 'call-site',
     '''void D3D12CommandProcessor::ShutdownContext() {
  AwaitAllQueueOperationsCompletion();
''',
     '''void D3D12CommandProcessor::ShutdownContext() {
  AwaitAllQueueOperationsCompletion();
  // S4 #19: everything is submitted and complete; stop the submit thread
  // before the command list and the allocators go.
  ShutdownAsyncSubmit();
''')

edit('E10', CP_CPP, 'call-site',
     '''  // So a thread waiting for this data only ever waits for the GPU itself.
  if (submission_open_) {
    EndSubmission(false);
  }
''',
     '''  // So a thread waiting for this data only ever waits for the GPU itself.
  if (submission_open_) {
    EndSubmission(false);
  }
  // S4 #19: a split may have handed the batch's submission to the submit
  // thread; wait until it is submitted, so that still holds.
  if (submit_async_) {
    DrainAsyncSubmissions();
  }
''')

edit('E11', CP_CPP, 'call-site',
     '''void D3D12CommandProcessor::CheckSubmissionFence(uint64_t await_submission) {
  if (await_submission >= submission_current_) {
''',
     '''void D3D12CommandProcessor::CheckSubmissionFence(uint64_t await_submission) {
  if (await_submission >= submission_current_) {
    // S4 #19: the splits queued on the submit thread go to the queue before
    // the signal below.
    if (submit_async_) {
      DrainAsyncSubmissions();
    }
''')

edit('E12', CP_CPP, 'call-site',
     '''bool D3D12CommandProcessor::EndSubmission(bool is_swap) {
  const ui::d3d12::D3D12Provider& provider = GetD3D12Provider();
''',
     '''bool D3D12CommandProcessor::EndSubmission(bool is_swap) {
  const ui::d3d12::D3D12Provider& provider = GetD3D12Provider();

  // S4 #19: this submit, frame end or cache clear waits until the submit
  // thread has submitted the splits queued before it (d3d12_async_submit).
  if (submit_async_) {
    DrainAsyncSubmissions();
  }
''')

edit('E13', CP_CPP, 'ternary',
     '''  } else if (EndSubmission(false)) {
''',
     '''  } else if (submit_async_ ? EndSubmissionAsync() : EndSubmission(false)) {
''')

NEW_FUNCTIONS = '''bool D3D12CommandProcessor::EndSubmissionAsync() {
  // S4 #19 (R1 stage 2). Called only from MaybeSplitSubmission, with the
  // submission and the frame open, no occlusion query active, the scratch
  // buffer free and no pipeline creation pending. It does what
  // EndSubmission(false) does there, but queues the recorded commands for the
  // submit thread instead of executing and submitting them here. The fence
  // value is given out here, in order, as in EndSubmission.
  if (!command_allocator_writable_first_) {
    ID3D12CommandAllocator* command_allocator;
    if (FAILED(GetD3D12Provider().GetDevice()->CreateCommandAllocator(
            D3D12_COMMAND_LIST_TYPE_DIRECT, IID_PPV_ARGS(&command_allocator)))) {
      REXGPU_ERROR("Failed to create a command allocator");
      // As in EndSubmission: the submission stays open (cond 3).
      return false;
    }
    command_allocator_writable_first_ = new CommandAllocator;
    command_allocator_writable_first_->command_allocator = command_allocator;
    command_allocator_writable_first_->last_usage_submission = 0;
    command_allocator_writable_first_->next = nullptr;
    command_allocator_writable_last_ = command_allocator_writable_first_;
  }

  assert_true(submission_open_);
  assert_false(scratch_buffer_used_);
  assert_false(active_occlusion_query_.valid);

  pipeline_cache_->EndSubmission();

  // Submit barriers now because resources with the queued barriers may be
  // destroyed between frames.
  SubmitBarriers();

  ID3D12CommandAllocator* command_allocator =
      command_allocator_writable_first_->command_allocator;
  {
    std::unique_lock<std::mutex> lock(async_submit_mutex_);
    if (async_submit_count_ >= kAsyncSubmitSlots) {
      // Every slot is queued or being submitted: wait for the oldest.
      auto wait_start = std::chrono::steady_clock::now();
      async_submit_idle_cond_.wait(lock,
                                   [this] { return async_submit_count_ < kAsyncSubmitSlots; });
      ++async_submit_stats_.full_waits;
      async_submit_stats_.full_wait_ns +=
          uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
                       std::chrono::steady_clock::now() - wait_start)
                       .count());
    }
    AsyncSubmission& chunk =
        *async_submit_slots_[(async_submit_first_ + async_submit_count_) % kAsyncSubmitSlots];
    // The slot's list is empty (the submit thread resets it): the open
    // submission's commands go to the slot, and recording goes on in the empty
    // list once BeginSubmission reopens the submission.
    chunk.deferred_command_list.Swap(deferred_command_list_);
    chunk.command_allocator = command_allocator;
    chunk.submission = submission_current_;
    ++async_submit_count_;
    ++async_submit_stats_.chunks;
    async_submit_stats_.queued_max =
        std::max(async_submit_stats_.queued_max, uint64_t(async_submit_count_));
  }
  async_submit_work_cond_.notify_one();

  // The rest is EndSubmission's: the allocator is in use until the GPU has
  // reached this submission's fence value, which the submit thread signals
  // after its ExecuteCommandLists.
  command_allocator_writable_first_->last_usage_submission = submission_current_;
  if (command_allocator_submitted_last_) {
    command_allocator_submitted_last_->next = command_allocator_writable_first_;
  } else {
    command_allocator_submitted_first_ = command_allocator_writable_first_;
  }
  command_allocator_submitted_last_ = command_allocator_writable_first_;
  command_allocator_writable_first_ = command_allocator_writable_first_->next;
  command_allocator_submitted_last_->next = nullptr;
  if (!command_allocator_writable_first_) {
    command_allocator_writable_last_ = nullptr;
  }

  ++submission_current_;

  submission_open_ = false;

  // Queue operations done directly before this point were issued before the
  // submit thread's ExecuteCommandLists and Signal of this submission, so
  // awaiting it awaits them too, as in EndSubmission.
  queue_operations_done_since_submission_signal_ = false;

  // The counter line, about every 10 s and only with the cvar on. Times are
  // totals in microseconds.
  auto now = std::chrono::steady_clock::now();
  if (now - async_submit_last_log_ >= std::chrono::seconds(10)) {
    async_submit_last_log_ = now;
    AsyncSubmitStats stats;
    {
      std::lock_guard<std::mutex> lock(async_submit_mutex_);
      stats = async_submit_stats_;
    }
    REXGPU_INFO(
        "d3d12_async_submit: frame={} submission={} chunks={} queued_max={} full_waits={} "
        "full_wait_us={} drains_waited={} drain_wait_us={} worker_us={}",
        frame_current_, submission_current_, stats.chunks, stats.queued_max, stats.full_waits,
        stats.full_wait_ns / 1000, stats.drains_waited, stats.drain_wait_ns / 1000,
        stats.worker_ns / 1000);
  }
  return true;
}

void D3D12CommandProcessor::DrainAsyncSubmissions() {
  // S4 #19: GPU Commands thread. Returns once the submit thread has submitted
  // and signalled every queued split. Splits are queued only by this thread,
  // so none can be added meanwhile.
  std::unique_lock<std::mutex> lock(async_submit_mutex_);
  if (!async_submit_count_) {
    return;
  }
  auto wait_start = std::chrono::steady_clock::now();
  async_submit_idle_cond_.wait(lock, [this] { return !async_submit_count_; });
  ++async_submit_stats_.drains_waited;
  async_submit_stats_.drain_wait_ns +=
      uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
                   std::chrono::steady_clock::now() - wait_start)
                   .count());
}

void D3D12CommandProcessor::AsyncSubmitThread() {
  // S4 #19: the submit thread. While a split is queued, the GPU Commands
  // thread does not touch command_list_ (its own submits drain first), and the
  // split's allocator came from the writable list, so the GPU is done with it.
  // This thread never waits for the GPU Commands thread, so it always empties
  // the queue.
  ID3D12CommandQueue* direct_queue = GetD3D12Provider().GetDirectQueue();
  std::unique_lock<std::mutex> lock(async_submit_mutex_);
  for (;;) {
    async_submit_work_cond_.wait(lock,
                                 [this] { return async_submit_count_ || async_submit_stop_; });
    if (!async_submit_count_) {
      // Asked to stop, and the queue is empty.
      break;
    }
    AsyncSubmission& chunk = *async_submit_slots_[async_submit_first_];
    lock.unlock();
    auto start = std::chrono::steady_clock::now();
    // EndSubmission's submit, in the same order.
    chunk.command_allocator->Reset();
    command_list_->Reset(chunk.command_allocator, nullptr);
    chunk.deferred_command_list.Execute(command_list_, command_list_1_);
    command_list_->Close();
    ID3D12CommandList* execute_command_lists[] = {command_list_};
    direct_queue->ExecuteCommandLists(1, execute_command_lists);
    direct_queue->Signal(submission_fence_, chunk.submission);
    chunk.deferred_command_list.Reset();
    chunk.command_allocator = nullptr;
    uint64_t worker_ns = uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
                                      std::chrono::steady_clock::now() - start)
                                      .count());
    lock.lock();
    async_submit_stats_.worker_ns += worker_ns;
    async_submit_first_ = (async_submit_first_ + 1) % kAsyncSubmitSlots;
    --async_submit_count_;
    async_submit_idle_cond_.notify_all();
  }
}

void D3D12CommandProcessor::ShutdownAsyncSubmit() {
  // S4 #19: GPU Commands thread. The submit thread submits whatever is still
  // queued, then exits.
  submit_async_ = false;
  if (!async_submit_thread_) {
    return;
  }
  {
    std::lock_guard<std::mutex> lock(async_submit_mutex_);
    async_submit_stop_ = true;
  }
  async_submit_work_cond_.notify_one();
  rex::thread::Wait(async_submit_thread_.get(), false);
  async_submit_thread_.reset();
  for (auto& slot : async_submit_slots_) {
    slot.reset();
  }
  async_submit_first_ = 0;
  async_submit_count_ = 0;
  async_submit_stop_ = false;
}

'''

edit('E14', CP_CPP, 'new-functions',
     'void D3D12CommandProcessor::ClearCommandAllocatorCache() {\n',
     NEW_FUNCTIONS + 'void D3D12CommandProcessor::ClearCommandAllocatorCache() {\n')

# ---------------------------------------------------------------- shared_memory.cpp, texture_cache.cpp
edit('E15', SM_CPP, 'call-site',
     '''  UINT heap_range_start_offset = 0;
  direct_queue->UpdateTileMappings(buffer_, 1, &region_start_coordinates, &region_size, heap, 1,
''',
     '''  UINT heap_range_start_offset = 0;
  // S4 #19: with d3d12_async_submit on, the splits queued before this mapping
  // go to the queue first, as without the submit thread.
  command_processor_.FlushAsyncSubmissions();
  direct_queue->UpdateTileMappings(buffer_, 1, &region_start_coordinates, &region_size, heap, 1,
''')

edit('E16', TC_CPP, 'call-site',
     '''    std::array<size_t, 2> buffer_indices =
        GetPossibleScaledResolveBufferIndices(uint64_t(i) << kScaledResolveHeapSizeLog2);
    for (size_t j = 0; j < 2; ++j) {
''',
     '''    std::array<size_t, 2> buffer_indices =
        GetPossibleScaledResolveBufferIndices(uint64_t(i) << kScaledResolveHeapSizeLog2);
    // S4 #19: with d3d12_async_submit on, the splits queued before these
    // mappings go to the queue first, as without the submit thread.
    command_processor_.FlushAsyncSubmissions();
    for (size_t j = 0; j < 2; ++j) {
''')

# Lines an inserted call site may add (besides comments and blank lines).
CALL_SITE_ALLOWED = {
    'if (submit_async_) {', 'DrainAsyncSubmissions();', '}', 'ShutdownAsyncSubmit();',
    'command_processor_.FlushAsyncSubmissions();',
}
WORKER_ALLOWED_MEMBERS = {
    'async_submit_mutex_', 'async_submit_work_cond_', 'async_submit_idle_cond_',
    'async_submit_count_', 'async_submit_stop_', 'async_submit_first_', 'async_submit_slots_',
    'async_submit_stats_', 'command_list_', 'command_list_1_', 'submission_fence_',
}


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def rd(path):
    with open(path, 'rb') as f:
        return f.read()


def wr(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def main():
    proofs = []
    ok = True

    def check(cond, msg):
        nonlocal ok
        proofs.append(('PASS ' if cond else 'FAIL ') + msg)
        if not cond:
            ok = False

    # P1: base identity (orig == snap1 bytes == S4b after-hash).
    patches = open(PATCHES_S4B, encoding='utf-8', errors='replace').read()
    for rel in FILES + BASE_ONLY:
        o = rd(os.path.join(ORIG, rel))
        s = rd(os.path.join(SNAP_SDK, rel))
        check(o == s, 'P1 orig == snap1 bytes: %s (%s)' % (rel, sha(o)[:16]))
        if rel in S4B_PREFIX:
            check(sha(o).startswith(S4B_PREFIX[rel]) and S4B_PREFIX[rel] in patches.upper()
                  and ('rexglue-sdk/' + rel) in patches,
                  'P1 == S4b after-hash in PATCHES-S4b.tsv: %s %s' % (rel, S4B_PREFIX[rel]))
        else:
            check(('rexglue-sdk/' + rel) not in patches,
                  'P1 not patched in S4b (S4a/S1 bytes): %s' % rel)

    # Apply the edits.
    text = {rel: rd(os.path.join(ORIG, rel)).decode('utf-8') for rel in FILES}
    orig_text = dict(text)
    for eid, rel, kind, anchor, repl in EDITS:
        n = orig_text[rel].count(anchor)
        check(n == 1, 'P2 %s anchor exactly once in base %s (found %d)' % (eid, rel, n))
        added = repl.replace(anchor, '', 1) if anchor in repl else repl
        check(text[rel].count(anchor) == 1, 'P2 %s anchor once before applying' % eid)
        text[rel] = text[rel].replace(anchor, repl, 1)
    for rel in FILES:
        check('\r' not in text[rel] and text[rel].endswith('\n'),
              'P9 LF only, final newline: %s' % rel)

    # Write new/ and the diff.
    diff_parts = []
    stats = []
    for rel in FILES:
        new_bytes = text[rel].encode('utf-8')
        wr(os.path.join(NEW, rel), new_bytes)
        a = orig_text[rel].split('\n')[:-1]
        b = text[rel].split('\n')[:-1]
        ud = list(difflib.unified_diff(a, b, 'a/' + rel, 'b/' + rel, n=3, lineterm=''))
        plus = [l for l in ud if l.startswith('+') and not l.startswith('+++')]
        minus = [l for l in ud if l.startswith('-') and not l.startswith('---')]
        stats.append((rel, len(plus), len(minus)))
        diff_parts.append('diff --git a/%s b/%s\n' % (rel, rel) + '\n'.join(ud) + '\n')
    diff = ''.join(diff_parts)
    wr(os.path.join(HERE, 's4-r1s2.diff'), diff.encode('utf-8'))

    # P3: diff shape. The only removed line is MaybeSplitSubmission's; the ternary's
    # false arm is the removed expression.
    all_minus = []
    for rel in FILES:
        a = orig_text[rel].split('\n')
        b = text[rel].split('\n')
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag in ('replace', 'delete'):
                all_minus.extend((rel, x) for x in a[i1:i2])
    check(all_minus == [(CP_CPP, '  } else if (EndSubmission(false)) {')],
          'P3 only removed line: cp.cpp MaybeSplitSubmission "} else if (EndSubmission(false)) {" '
          '(got %d)' % len(all_minus))
    check('  } else if (submit_async_ ? EndSubmissionAsync() : EndSubmission(false)) {'
          in text[CP_CPP], 'P3 its replacement: submit_async_ ? EndSubmissionAsync() : '
          'EndSubmission(false) (false arm == the removed call)')

    # P4: call sites add only guarded statements.
    for eid, rel, kind, anchor, repl in EDITS:
        if kind not in ('call-site', 'public-inline-guarded'):
            continue
        added = [l.strip() for l in repl.split('\n')]
        base = [l.strip() for l in anchor.split('\n')]
        extra = list(added)
        for l in base:
            if l in extra:
                extra.remove(l)
        code = [l for l in extra if l and not l.startswith('//')]
        if kind == 'public-inline-guarded':
            code = [l for l in code if l != 'void FlushAsyncSubmissions() {']
        bad = [l for l in code if l not in CALL_SITE_ALLOWED]
        check(not bad, 'P4 %s (%s) adds only guarded lines %s%s' % (
            eid, rel, sorted(set(code)), (' BAD ' + repr(bad)) if bad else ''))

    # P5: every queue operation on the GPU Commands thread follows a drain in its
    # function (or is the submit thread itself).
    func_re = re.compile(r'^[A-Za-z].*?\b(\w+)::(~?\w+)\(')
    for rel in (CP_CPP, SM_CPP, TC_CPP):
        lines = text[rel].split('\n')
        for idx, line in enumerate(lines):
            if not re.search(r'(ExecuteCommandLists\(|->Signal\(|UpdateTileMappings\(|->Wait\()', line):
                continue
            if line.strip().startswith('//'):
                continue
            start = idx
            while start > 0 and not func_re.match(lines[start]):
                start -= 1
            m = func_re.match(lines[start])
            fname = m.group(2) if m else '?'
            body = '\n'.join(lines[start:idx])
            drained = ('DrainAsyncSubmissions();' in body) or ('FlushAsyncSubmissions();' in body)
            exempt = fname == 'AsyncSubmitThread'
            check(drained or exempt, 'P5 %s:%d %s: %s -> %s' % (
                rel.split('/')[-1], idx + 1, fname, line.strip()[:60],
                'submit thread' if exempt else ('drain before' if drained else 'NO DRAIN')))

    # P6: the submit thread touches only its own members, the command list and the fence.
    cpp = text[CP_CPP]
    s = cpp.index('void D3D12CommandProcessor::AsyncSubmitThread() {')
    e = cpp.index('\nvoid D3D12CommandProcessor::ShutdownAsyncSubmit() {', s)
    body = re.sub(r'//[^\n]*', '', cpp[s:e])
    members = set(re.findall(r'\b([a-z][a-z0-9_]*_)\b', body))
    check(members <= WORKER_ALLOWED_MEMBERS, 'P6 submit thread members %s%s' % (
        sorted(members), (' EXTRA ' + repr(sorted(members - WORKER_ALLOWED_MEMBERS)))
        if not members <= WORKER_ALLOWED_MEMBERS else ''))

    # P7: bracket balance of the added text.
    for rel in FILES:
        for o_, c_ in (('{', '}'), ('(', ')'), ('[', ']')):
            d_o = text[rel].count(o_) - orig_text[rel].count(o_)
            d_c = text[rel].count(c_) - orig_text[rel].count(c_)
            check(d_o == d_c, 'P7 %s balance %s%s: +%d/+%d' % (rel.split('/')[-1], o_, c_, d_o, d_c))

    # P8: with submit_async_ false, MaybeSplitSubmission is stage 1 (one line differs).
    def body_of(t, sig):
        i = t.index(sig)
        j = t.index('\n}\n', i)
        return t[i:j].split('\n')
    a = body_of(orig_text[CP_CPP], 'void D3D12CommandProcessor::MaybeSplitSubmission() {')
    b = body_of(text[CP_CPP], 'void D3D12CommandProcessor::MaybeSplitSubmission() {')
    diffl = [(x, y) for x, y in zip(a, b) if x != y]
    check(len(a) == len(b) and len(diffl) == 1, 'P8 MaybeSplitSubmission: %d lines, %d differ' % (
        len(b), len(diffl)))

    # P10: EndSubmission's own body is unchanged apart from the drain at its top.
    a = body_of(orig_text[CP_CPP], 'bool D3D12CommandProcessor::EndSubmission(bool is_swap) {')
    b = body_of(text[CP_CPP], 'bool D3D12CommandProcessor::EndSubmission(bool is_swap) {')
    b_wo = [l for l in b]
    ins = ['', '  // S4 #19: this submit, frame end or cache clear waits until the submit',
           '  // thread has submitted the splits queued before it (d3d12_async_submit).',
           '  if (submit_async_) {', '    DrainAsyncSubmissions();', '  }']
    k = b_wo.index(ins[1]) - 1
    check(b_wo[k:k + len(ins)] == ins and b_wo[:k] + b_wo[k + len(ins):] == a,
          'P10 EndSubmission == base + the guarded drain only (%d -> %d lines)' % (len(a), len(b)))

    # Hashes.
    sums = []
    for rel in FILES:
        sums.append('%s  orig/sdk/%s' % (sha(orig_text[rel].encode('utf-8')), rel))
        sums.append('%s  new/sdk/%s' % (sha(text[rel].encode('utf-8')), rel))
    for rel in BASE_ONLY:
        sums.append('%s  orig/sdk/%s (unchanged)' % (sha(rd(os.path.join(ORIG, rel))), rel))
    sums.append('%s  s4-r1s2.diff' % sha(diff.encode('utf-8')))
    wr(os.path.join(HERE, 'SHA256SUMS.txt'), ('\n'.join(sums) + '\n').encode('utf-8'))

    out = ['# make_s4r1s2.py proofs', '']
    out += ['diff: %s  +%d/-%d  %s' % (r, p, m, '') for r, p, m in stats]
    out.append('total: +%d/-%d' % (sum(p for _, p, _ in stats), sum(m for _, _, m in stats)))
    out.append('')
    out += proofs
    out.append('')
    out.append('RESULT: %s' % ('ALL PASS' if ok else 'FAILURES'))
    wr(os.path.join(HERE, 'PROOFS.txt'), ('\n'.join(out) + '\n').encode('utf-8'))
    print('\n'.join(out))
    print('\n'.join(sums))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
