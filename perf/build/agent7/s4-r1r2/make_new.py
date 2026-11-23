"""make_new.py (Agent 7, task #9): rebuild new/sdk from orig/sdk with the S4 #18 (R1 stage 1) and
#20 step 1 (R2 counters) edits. Every target must occur exactly once, or nothing is written.
Run: python -B build\\agent7\\s4-r1r2\\make_new.py   (LF files in, LF files out)."""
import difflib
import pathlib
import sys

STAGE = pathlib.Path(__file__).resolve().parent
ORIG = STAGE / "orig" / "sdk"
NEW = STAGE / "new" / "sdk"

CP_CPP = "src/graphics/d3d12/command_processor.cpp"
CP_H = "include/rex/graphics/d3d12/command_processor.h"
DCL_H = "include/rex/graphics/d3d12/deferred_command_list.h"
DCL_CPP = "src/graphics/d3d12/deferred_command_list.cpp"

EDITS = {}

# ---------------------------------------------------------------- #18: command_processor.cpp
EDITS[CP_CPP] = [
    # the cvar, next to d3d12_submit_on_primary_buffer_end
    (r'''REXCVAR_DEFINE_BOOL(d3d12_submit_on_primary_buffer_end, true, "GPU/D3D12",
                    "Submit command list when PM4 primary buffer ends")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);
''', r'''REXCVAR_DEFINE_BOOL(d3d12_submit_on_primary_buffer_end, true, "GPU/D3D12",
                    "Submit command list when PM4 primary buffer ends")
    .lifecycle(rex::cvar::Lifecycle::kHotReload);

// S4 #18 (R1 stage 1): end the open submission (not the frame) at the tail of
// a draw or resolve once its deferred command list has reached this many KB.
// It reuses the existing mid-frame EndSubmission(false) path, and holds the
// split while ending the submission would change behaviour (see
// MaybeSplitSubmission). A test bed for the split rules: each split adds a
// Close plus ExecuteCommandLists, so expect a small cost, not a win. Read once
// in SetupContext. Leave it at 0 on native builds unless tested there.
REXCVAR_DEFINE_UINT32(d3d12_submit_split_kb, 0, "GPU/D3D12",
                      "Split a submission mid-frame once its deferred command list reaches "
                      "this many KB (0 = off)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
'''),
    # cache it once in SetupContext
    (r'''  bindless_resources_used_ = REXCVAR_GET(d3d12_bindless) &&
                             provider.GetResourceBindingTier() >= D3D12_RESOURCE_BINDING_TIER_2;
''', r'''  bindless_resources_used_ = REXCVAR_GET(d3d12_bindless) &&
                             provider.GetResourceBindingTier() >= D3D12_RESOURCE_BINDING_TIER_2;

  // S4 #18: cached once (the cvar is kInitOnly), so with it at 0 a draw or
  // resolve pays one compare.
  submit_split_bytes_ = size_t(REXCVAR_GET(d3d12_submit_split_kb)) * 1024;
  submit_split_stats_ = {};
  submit_split_last_log_ = {};
  if (submit_split_bytes_) {
    REXGPU_INFO("d3d12_submit_split_kb: splitting submissions at {} KB of deferred commands",
                REXCVAR_GET(d3d12_submit_split_kb));
  }
'''),
    # the tail of IssueDraw
    (r'''          IssueDraw_MemexportReadbackFullPath(memexport_total_size);
        }
      }
    }
  }

  return true;
}
''', r'''          IssueDraw_MemexportReadbackFullPath(memexport_total_size);
        }
      }
    }
  }

  if (submit_split_bytes_) {
    // S4 #18: the draw, its barriers and any memexport readback are fully
    // recorded here.
    MaybeSplitSubmission();
  }

  return true;
}
'''),
    # the tail of IssueCopy
    (r'''  ReadbackResolveMode readback_mode = GetReadbackResolveMode(REXCVAR_GET(d3d12_readback_resolve));
  if (readback_mode == ReadbackResolveMode::kDisabled) {
    uint32_t written_address, written_length;
    return render_target_cache_->Resolve(*memory_, *shared_memory_, *texture_cache_,
                                         written_address, written_length);
  }
  return IssueCopy_ReadbackResolvePath();
}
''', r'''  ReadbackResolveMode readback_mode = GetReadbackResolveMode(REXCVAR_GET(d3d12_readback_resolve));
  bool resolved;
  if (readback_mode == ReadbackResolveMode::kDisabled) {
    uint32_t written_address, written_length;
    resolved = render_target_cache_->Resolve(*memory_, *shared_memory_, *texture_cache_,
                                             written_address, written_length);
  } else {
    resolved = IssueCopy_ReadbackResolvePath();
  }
  if (submit_split_bytes_ && resolved) {
    // S4 #18: the resolve, its barriers and any readback are fully recorded
    // here.
    MaybeSplitSubmission();
  }
  return resolved;
}
'''),
    # the split itself
    (r'''bool D3D12CommandProcessor::CanEndSubmissionImmediately() const {
  return !submission_open_ || !pipeline_cache_->IsCreatingPipelines();
}
''', r'''bool D3D12CommandProcessor::CanEndSubmissionImmediately() const {
  return !submission_open_ || !pipeline_cache_->IsCreatingPipelines();
}

void D3D12CommandProcessor::MaybeSplitSubmission() {
  // S4 #18 (R1 stage 1). Called only with d3d12_submit_split_kb on, on the GPU
  // Commands thread, from the tails of IssueDraw and IssueCopy once the
  // command and its barriers are fully recorded: never mid-packet, and never
  // from IssueSwap or RefreshGuestOutput (cond 1).
  if (!submission_open_ || !frame_open_ ||
      deferred_command_list_.GetSizeBytes() < submit_split_bytes_) {
    return;
  }
  // A split is due (cond 2). Hold it, and try again after the next draw or
  // resolve, while ending the submission now would change behaviour:
  // - EndSubmission would end the active occlusion query early;
  // - EndSubmission asserts that the scratch buffer is free;
  // - EndSubmission would wait for pending pipeline creation.
  if (active_occlusion_query_.valid) {
    ++submit_split_stats_.held_query;
  } else if (scratch_buffer_used_) {
    ++submit_split_stats_.held_scratch;
  } else if (!CanEndSubmissionImmediately()) {
    ++submit_split_stats_.held_pipelines;
  } else if (EndSubmission(false)) {
    // The frame stays open (is_swap is false). The next draw or resolve calls
    // BeginSubmission, which reopens the submission, resets the deferred
    // command list and re-binds every cached state. DeferredCommandList::Execute
    // keeps no state across submissions, so a split also resets R2's counter
    // state (S4 #20, cond (d)).
    ++submit_split_stats_.splits;
  } else {
    // No command allocator: EndSubmission left the submission open. Carry on
    // recording into it; BeginSubmission is not called here (cond 3).
    ++submit_split_stats_.failed;
  }
  // The counter line, about every 10 s while splits are due and only with the
  // cvar on. submission is the next fence value, so its change over frame's
  // change is the submissions per frame.
  auto now = std::chrono::steady_clock::now();
  if (now - submit_split_last_log_ >= std::chrono::seconds(10)) {
    submit_split_last_log_ = now;
    REXGPU_INFO(
        "d3d12_submit_split: frame={} submission={} splits={} failed={} held_query={} "
        "held_scratch={} held_pipelines={}",
        frame_current_, submission_current_, submit_split_stats_.splits,
        submit_split_stats_.failed, submit_split_stats_.held_query,
        submit_split_stats_.held_scratch, submit_split_stats_.held_pipelines);
  }
}
'''),
]

# ---------------------------------------------------------------- #18: command_processor.h
EDITS[CP_H] = [
    ("#include <atomic>\n#include <deque>\n", "#include <atomic>\n#include <chrono>\n#include <deque>\n"),
    (r'''  bool CanEndSubmissionImmediately() const;
''', r'''  bool CanEndSubmissionImmediately() const;
  // S4 #18 (R1 stage 1): with d3d12_submit_split_kb on, ends the open
  // submission (not the frame) once its deferred command list is large enough
  // and ending it now would not change behaviour. Call only at the tail of a
  // fully recorded draw or resolve.
  void MaybeSplitSubmission();
'''),
    (r'''  std::vector<draw_util::MemExportRange> memexport_ranges_;
};
''', r'''  std::vector<draw_util::MemExportRange> memexport_ranges_;

  // S4 #18 (R1 stage 1): the split size in bytes, cached in SetupContext from
  // the kInitOnly cvar d3d12_submit_split_kb (0 = off), and the counters for
  // its log line (written only when on).
  size_t submit_split_bytes_ = 0;
  struct SubmitSplitStats {
    uint64_t splits = 0;
    uint64_t failed = 0;
    uint64_t held_query = 0;
    uint64_t held_scratch = 0;
    uint64_t held_pipelines = 0;
  } submit_split_stats_;
  std::chrono::steady_clock::time_point submit_split_last_log_{};
};
'''),
]

# ---------------------------------------------------------------- #18: deferred_command_list.h
EDITS[DCL_H] = [
    (r'''  void Execute(ID3D12GraphicsCommandList* command_list, ID3D12GraphicsCommandList1* command_list_1);
''', r'''  void Execute(ID3D12GraphicsCommandList* command_list, ID3D12GraphicsCommandList1* command_list_1);

  // Bytes recorded since the last Reset (S4 #18's split check).
  size_t GetSizeBytes() const { return command_stream_.size() * sizeof(uintmax_t); }
'''),
]

# ---------------------------------------------------------------- #20 step 1: deferred_command_list.cpp
EDITS[DCL_CPP] = [
    (r'''#include <rex/math.h>

namespace rex::graphics::d3d12 {
''', r'''#include <rex/math.h>

// S4 #20 step 1 (R2): per-command-type counters for Execute. They only count:
// every command still reaches the real command list, unchanged and in order.
// Compiled out by default. Build this file with -DREX_D3D12_DEFERRED_COUNTERS=1
// to log, about every 10 s, how many commands of each type Execute replayed and
// how many pure state setters set exactly the state already set earlier in the
// same native command list (what a step 2 filter would drop). The macro changes
// no header, class layout or other file.
#ifndef REX_D3D12_DEFERRED_COUNTERS
#define REX_D3D12_DEFERRED_COUNTERS 0
#endif

#if REX_D3D12_DEFERRED_COUNTERS
#include <chrono>
#include <cstring>

#include <rex/logging.h>
#endif  // REX_D3D12_DEFERRED_COUNTERS

namespace rex::graphics::d3d12 {

#if REX_D3D12_DEFERRED_COUNTERS
namespace {

// DeferredCommandList::Command names, in enum order (Execute checks the count).
constexpr const char* kDeferredCommandNames[] = {
    "ClearDepthStencilView",
    "ClearRenderTargetView",
    "ClearUnorderedAccessViewUint",
    "CopyBufferRegion",
    "CopyResource",
    "CopyTexture",
    "CopyTextureRegion",
    "Dispatch",
    "DrawIndexedInstanced",
    "DrawInstanced",
    "BeginQuery",
    "EndQuery",
    "ResolveQueryData",
    "IASetIndexBuffer",
    "IASetPrimitiveTopology",
    "IASetVertexBuffers",
    "OMSetBlendFactor",
    "OMSetRenderTargets",
    "OMSetStencilRef",
    "ResourceBarrier",
    "RSSetScissorRect",
    "RSSetViewport",
    "SetComputeRoot32BitConstants",
    "SetGraphicsRoot32BitConstants",
    "SetComputeRootConstantBufferView",
    "SetGraphicsRootConstantBufferView",
    "SetComputeRootDescriptorTable",
    "SetGraphicsRootDescriptorTable",
    "SetComputeRootShaderResourceView",
    "SetGraphicsRootShaderResourceView",
    "SetComputeRootSignature",
    "SetGraphicsRootSignature",
    "SetComputeRootUnorderedAccessView",
    "SetGraphicsRootUnorderedAccessView",
    "SetDescriptorHeaps",
    "SetPipelineState",
    "SetPipelineStateHandle",
    "SetSamplePositions",
    "BeginDebugMarker",
    "EndDebugMarker",
    "InsertDebugMarker",
};
constexpr size_t kDeferredCommandCount =
    sizeof(kDeferredCommandNames) / sizeof(kDeferredCommandNames[0]);

// Counts since the last log line. Touched only by Execute, which runs only
// inside D3D12CommandProcessor::EndSubmission on the GPU Commands thread.
struct DeferredCommandCounters {
  uint64_t total[kDeferredCommandCount] = {};
  // Pure state setters that set exactly the state already set earlier in the
  // same native command list: what a step 2 filter could drop.
  uint64_t repeat[kDeferredCommandCount] = {};
  // Barriers inside ResourceBarrier commands. Counted only; never filter targets.
  uint64_t barriers = 0;
  // Execute calls (native command lists) and their stream bytes.
  uint64_t lists = 0;
  uint64_t bytes = 0;
  std::chrono::steady_clock::time_point last_log = {};
};
DeferredCommandCounters deferred_command_counters;

// The state that the commands replayed so far have set on the native command
// list; a pure state setter that sets exactly this counts as a repeat. Execute
// constructs one, empty, for each call. Each call replays one submission into
// a native command list that EndSubmission has just reset, and nothing else
// records into that list before its Close. So the state starts empty at every
// Execute. An R1 split (S4 #18) is an EndSubmission(false): it ends one
// Execute, and the next EndSubmission resets the native list and starts the
// next from empty. These are R2 conds (b) and (d).
struct DeferredCommandShadow {
  static constexpr UINT kMaxRootParameters = 16;
  static constexpr UINT kMaxRootConstants = 64;
  enum class RootKind : uint8_t { kUnknown, kConstants, kCBV, kSRV, kUAV, kTable };
  struct RootParameter {
    RootKind kind = RootKind::kUnknown;
    // GPU virtual address (CBV, SRV, UAV) or GPU descriptor handle (table).
    uint64_t value = 0;
    // Bit i: constants[i] holds the value set in this list.
    uint64_t constants_valid = 0;
    uint32_t constants[kMaxRootConstants];
  };
  // Graphics and compute keep separate root state. Root parameters past
  // kMaxRootParameters, or constants past kMaxRootConstants, are not tracked
  // and never count as repeats.
  struct Root {
    bool signature_valid = false;
    ID3D12RootSignature* signature = nullptr;
    RootParameter parameters[kMaxRootParameters];

    // Every root signature set resets all root arguments, a redundant one too.
    bool SetSignature(ID3D12RootSignature* new_signature) {
      bool repeat = signature_valid && signature == new_signature;
      signature_valid = true;
      signature = new_signature;
      for (RootParameter& parameter : parameters) {
        parameter.kind = RootKind::kUnknown;
        parameter.constants_valid = 0;
      }
      return repeat;
    }
    bool SetValue(UINT index, RootKind kind, uint64_t value) {
      if (index >= kMaxRootParameters) {
        return false;
      }
      RootParameter& parameter = parameters[index];
      bool repeat = parameter.kind == kind && parameter.value == value;
      parameter.kind = kind;
      parameter.value = value;
      parameter.constants_valid = 0;
      return repeat;
    }
    // Compares every value at its offset.
    bool SetConstants(UINT index, UINT count, UINT offset, const uint32_t* values) {
      if (index >= kMaxRootParameters) {
        return false;
      }
      RootParameter& parameter = parameters[index];
      if (parameter.kind != RootKind::kConstants) {
        parameter.kind = RootKind::kConstants;
        parameter.value = 0;
        parameter.constants_valid = 0;
      }
      if (offset >= kMaxRootConstants || count > kMaxRootConstants - offset) {
        parameter.constants_valid = 0;
        return false;
      }
      uint64_t mask = (count >= 64 ? ~uint64_t(0) : (uint64_t(1) << count) - 1) << offset;
      bool repeat = (parameter.constants_valid & mask) == mask &&
                    !std::memcmp(parameter.constants + offset, values, sizeof(uint32_t) * count);
      std::memcpy(parameter.constants + offset, values, sizeof(uint32_t) * count);
      parameter.constants_valid |= mask;
      return repeat;
    }
    // Every descriptor heap set resets the descriptor tables.
    void ResetTables() {
      for (RootParameter& parameter : parameters) {
        if (parameter.kind == RootKind::kTable) {
          parameter.kind = RootKind::kUnknown;
        }
      }
    }
  };

  Root graphics;
  Root compute;
  bool heaps_valid = false;
  ID3D12DescriptorHeap* heaps[2] = {};
  bool topology_valid = false;
  D3D12_PRIMITIVE_TOPOLOGY topology = D3D_PRIMITIVE_TOPOLOGY_UNDEFINED;
  bool index_buffer_valid = false;
  D3D12_INDEX_BUFFER_VIEW index_buffer = {};
  // The last IASetVertexBuffers call; vertex_buffer_count 0 means none yet.
  UINT vertex_buffer_start = 0;
  UINT vertex_buffer_count = 0;
  D3D12_VERTEX_BUFFER_VIEW vertex_buffers[D3D12_IA_VERTEX_INPUT_RESOURCE_SLOT_COUNT];
  bool render_targets_valid = false;
  UINT render_target_count = 0;
  bool render_target_range = false;
  D3D12_CPU_DESCRIPTOR_HANDLE render_targets[D3D12_SIMULTANEOUS_RENDER_TARGET_COUNT] = {};
  bool depth_stencil = false;
  D3D12_CPU_DESCRIPTOR_HANDLE depth_stencil_descriptor = {};
  bool viewport_valid = false;
  D3D12_VIEWPORT viewport = {};
  bool scissor_valid = false;
  D3D12_RECT scissor = {};
  bool blend_factor_valid = false;
  FLOAT blend_factor[4] = {};
  bool stencil_ref_valid = false;
  UINT stencil_ref = 0;
};

}  // namespace
#endif  // REX_D3D12_DEFERRED_COUNTERS
'''),
    (r'''  ID3D12PipelineState* current_pipeline_state = nullptr;
  while (stream_remaining != 0) {
    const CommandHeader& header = *reinterpret_cast<const CommandHeader*>(stream);
    stream += kCommandHeaderSizeElements;
    stream_remaining -= kCommandHeaderSizeElements;
    switch (header.command) {
''', r'''  ID3D12PipelineState* current_pipeline_state = nullptr;
#if REX_D3D12_DEFERRED_COUNTERS
  static_assert(size_t(Command::kInsertDebugMarker) + 1 == kDeferredCommandCount,
                "kDeferredCommandNames must name every DeferredCommandList::Command");
  // Empty at the start of every Execute (see DeferredCommandShadow).
  DeferredCommandShadow shadow;
  // Counts one command before it is replayed, so current_pipeline_state is
  // still the pipeline from before it. Only pure state setters can repeat
  // (R2 cond (a)); the whole payload is compared (cond (c)).
  auto count_command = [&](Command command, const uintmax_t* args) {
    using Shadow = DeferredCommandShadow;
    auto set_root_value = [args](Shadow::Root& root, Shadow::RootKind kind) {
      auto& view = *reinterpret_cast<const SetRootConstantBufferViewArguments*>(args);
      return root.SetValue(view.root_parameter_index, kind, view.buffer_location);
    };
    bool repeat = false;
    switch (command) {
      case Command::kD3DIASetIndexBuffer: {
        auto& view = *reinterpret_cast<const D3D12_INDEX_BUFFER_VIEW*>(args);
        // A null index buffer (DXGI_FORMAT_UNKNOWN) repeats a null one.
        repeat = shadow.index_buffer_valid && shadow.index_buffer.Format == view.Format &&
                 (view.Format == DXGI_FORMAT_UNKNOWN ||
                  (shadow.index_buffer.BufferLocation == view.BufferLocation &&
                   shadow.index_buffer.SizeInBytes == view.SizeInBytes));
        shadow.index_buffer_valid = true;
        shadow.index_buffer = view;
      } break;
      case Command::kD3DIASetPrimitiveTopology: {
        auto topology = *reinterpret_cast<const D3D12_PRIMITIVE_TOPOLOGY*>(args);
        repeat = shadow.topology_valid && shadow.topology == topology;
        shadow.topology_valid = true;
        shadow.topology = topology;
      } break;
      case Command::kD3DIASetVertexBuffers: {
        // The whole call, with its start slot and count.
        auto& vb = *reinterpret_cast<const D3DIASetVertexBuffersHeader*>(args);
        auto views = reinterpret_cast<const D3D12_VERTEX_BUFFER_VIEW*>(
            reinterpret_cast<const uint8_t*>(args) +
            rex::align(sizeof(D3DIASetVertexBuffersHeader), alignof(D3D12_VERTEX_BUFFER_VIEW)));
        if (vb.num_views > D3D12_IA_VERTEX_INPUT_RESOURCE_SLOT_COUNT) {
          shadow.vertex_buffer_count = 0;
          break;
        }
        size_t views_size = sizeof(D3D12_VERTEX_BUFFER_VIEW) * vb.num_views;
        repeat = shadow.vertex_buffer_count != 0 && shadow.vertex_buffer_count == vb.num_views &&
                 shadow.vertex_buffer_start == vb.start_slot &&
                 !std::memcmp(shadow.vertex_buffers, views, views_size);
        shadow.vertex_buffer_start = vb.start_slot;
        shadow.vertex_buffer_count = vb.num_views;
        std::memcpy(shadow.vertex_buffers, views, views_size);
      } break;
      case Command::kD3DOMSetBlendFactor:
        repeat = shadow.blend_factor_valid &&
                 !std::memcmp(shadow.blend_factor, args, sizeof(shadow.blend_factor));
        shadow.blend_factor_valid = true;
        std::memcpy(shadow.blend_factor, args, sizeof(shadow.blend_factor));
        break;
      case Command::kD3DOMSetRenderTargets: {
        // The whole array with its count, the range flag and the DSV handle.
        auto& rts = *reinterpret_cast<const D3DOMSetRenderTargetsArguments*>(args);
        UINT rt_count = rts.num_render_target_descriptors;
        bool rt_range = rts.rts_single_handle_to_descriptor_range;
        UINT rt_handles = rt_range ? std::min(rt_count, UINT(1)) : rt_count;
        repeat = shadow.render_targets_valid && shadow.render_target_count == rt_count &&
                 shadow.render_target_range == rt_range &&
                 shadow.depth_stencil == rts.depth_stencil &&
                 (!rts.depth_stencil ||
                  shadow.depth_stencil_descriptor.ptr == rts.depth_stencil_descriptor.ptr);
        for (UINT i = 0; repeat && i < rt_handles; ++i) {
          repeat = shadow.render_targets[i].ptr == rts.render_target_descriptors[i].ptr;
        }
        shadow.render_targets_valid = true;
        shadow.render_target_count = rt_count;
        shadow.render_target_range = rt_range;
        for (UINT i = 0; i < rt_handles; ++i) {
          shadow.render_targets[i] = rts.render_target_descriptors[i];
        }
        shadow.depth_stencil = rts.depth_stencil;
        shadow.depth_stencil_descriptor = rts.depth_stencil_descriptor;
      } break;
      case Command::kD3DOMSetStencilRef: {
        UINT stencil_ref = *reinterpret_cast<const UINT*>(args);
        repeat = shadow.stencil_ref_valid && shadow.stencil_ref == stencil_ref;
        shadow.stencil_ref_valid = true;
        shadow.stencil_ref = stencil_ref;
      } break;
      case Command::kD3DResourceBarrier:
        // Counted, never compared: a barrier is not a state.
        deferred_command_counters.barriers += *reinterpret_cast<const UINT*>(args);
        break;
      case Command::kRSSetScissorRect:
        repeat = shadow.scissor_valid && !std::memcmp(&shadow.scissor, args, sizeof(D3D12_RECT));
        shadow.scissor_valid = true;
        std::memcpy(&shadow.scissor, args, sizeof(D3D12_RECT));
        break;
      case Command::kRSSetViewport:
        repeat =
            shadow.viewport_valid && !std::memcmp(&shadow.viewport, args, sizeof(D3D12_VIEWPORT));
        shadow.viewport_valid = true;
        std::memcpy(&shadow.viewport, args, sizeof(D3D12_VIEWPORT));
        break;
      case Command::kD3DSetComputeRoot32BitConstants:
      case Command::kD3DSetGraphicsRoot32BitConstants: {
        auto constants = reinterpret_cast<const SetRoot32BitConstantsHeader*>(args);
        Shadow::Root& root = command == Command::kD3DSetComputeRoot32BitConstants
                                 ? shadow.compute
                                 : shadow.graphics;
        repeat = root.SetConstants(constants->root_parameter_index,
                                   constants->num_32bit_values_to_set,
                                   constants->dest_offset_in_32bit_values,
                                   reinterpret_cast<const uint32_t*>(constants + 1));
      } break;
      case Command::kD3DSetComputeRootConstantBufferView:
        repeat = set_root_value(shadow.compute, Shadow::RootKind::kCBV);
        break;
      case Command::kD3DSetGraphicsRootConstantBufferView:
        repeat = set_root_value(shadow.graphics, Shadow::RootKind::kCBV);
        break;
      case Command::kD3DSetComputeRootShaderResourceView:
        repeat = set_root_value(shadow.compute, Shadow::RootKind::kSRV);
        break;
      case Command::kD3DSetGraphicsRootShaderResourceView:
        repeat = set_root_value(shadow.graphics, Shadow::RootKind::kSRV);
        break;
      case Command::kD3DSetComputeRootUnorderedAccessView:
        repeat = set_root_value(shadow.compute, Shadow::RootKind::kUAV);
        break;
      case Command::kD3DSetGraphicsRootUnorderedAccessView:
        repeat = set_root_value(shadow.graphics, Shadow::RootKind::kUAV);
        break;
      case Command::kD3DSetComputeRootDescriptorTable:
      case Command::kD3DSetGraphicsRootDescriptorTable: {
        auto& table = *reinterpret_cast<const SetRootDescriptorTableArguments*>(args);
        Shadow::Root& root = command == Command::kD3DSetComputeRootDescriptorTable
                                 ? shadow.compute
                                 : shadow.graphics;
        repeat = root.SetValue(table.root_parameter_index, Shadow::RootKind::kTable,
                               table.base_descriptor.ptr);
      } break;
      case Command::kD3DSetComputeRootSignature:
        repeat = shadow.compute.SetSignature(*reinterpret_cast<ID3D12RootSignature* const*>(args));
        break;
      case Command::kD3DSetGraphicsRootSignature:
        repeat =
            shadow.graphics.SetSignature(*reinterpret_cast<ID3D12RootSignature* const*>(args));
        break;
      case Command::kSetDescriptorHeaps: {
        auto& heaps = *reinterpret_cast<const SetDescriptorHeapsArguments*>(args);
        repeat = shadow.heaps_valid && shadow.heaps[0] == heaps.cbv_srv_uav_descriptor_heap &&
                 shadow.heaps[1] == heaps.sampler_descriptor_heap;
        shadow.heaps_valid = true;
        shadow.heaps[0] = heaps.cbv_srv_uav_descriptor_heap;
        shadow.heaps[1] = heaps.sampler_descriptor_heap;
        // Every heap set resets the descriptor tables, a redundant one too.
        shadow.graphics.ResetTables();
        shadow.compute.ResetTables();
      } break;
      case Command::kD3DSetPipelineState: {
        // Only the pipeline Execute would still draw with repeats. A pipeline
        // change does not reset the root arguments.
        ID3D12PipelineState* pipeline = *reinterpret_cast<ID3D12PipelineState* const*>(args);
        repeat = pipeline != nullptr && pipeline == current_pipeline_state;
      } break;
      case Command::kSetPipelineStateHandle: {
        ID3D12PipelineState* pipeline =
            command_processor_.GetD3D12PipelineByHandle(*reinterpret_cast<void* const*>(args));
        repeat = pipeline != nullptr && pipeline == current_pipeline_state;
      } break;
      default:
        // Draws, dispatches, clears, copies, queries, sample positions and
        // debug markers: counted only.
        break;
    }
    size_t index = size_t(command);
    if (index < kDeferredCommandCount) {
      ++deferred_command_counters.total[index];
      if (repeat) {
        ++deferred_command_counters.repeat[index];
      }
    }
  };
#endif  // REX_D3D12_DEFERRED_COUNTERS
  while (stream_remaining != 0) {
    const CommandHeader& header = *reinterpret_cast<const CommandHeader*>(stream);
    stream += kCommandHeaderSizeElements;
    stream_remaining -= kCommandHeaderSizeElements;
#if REX_D3D12_DEFERRED_COUNTERS
    count_command(header.command, stream);
#endif  // REX_D3D12_DEFERRED_COUNTERS
    switch (header.command) {
'''),
    (r'''    stream += header.arguments_size_elements;
    stream_remaining -= header.arguments_size_elements;
  }
}
''', r'''    stream += header.arguments_size_elements;
    stream_remaining -= header.arguments_size_elements;
  }
#if REX_D3D12_DEFERRED_COUNTERS
  // About every 10 s, log the counts since the last line and start over.
  DeferredCommandCounters& counters = deferred_command_counters;
  ++counters.lists;
  counters.bytes += command_stream_.size() * sizeof(uintmax_t);
  auto now = std::chrono::steady_clock::now();
  if (counters.last_log == std::chrono::steady_clock::time_point()) {
    counters.last_log = now;
  } else if (now - counters.last_log >= std::chrono::seconds(10)) {
    REXGPU_INFO("deferred_counters: {:.1f} s, {} lists, {} KB, {} barriers",
                std::chrono::duration<double>(now - counters.last_log).count(), counters.lists,
                counters.bytes >> 10, counters.barriers);
    for (size_t i = 0; i < kDeferredCommandCount; ++i) {
      if (counters.total[i]) {
        REXGPU_INFO("deferred_counters:   {:<33} total={:<8} repeat={:<8} ({:.1f}%)",
                    kDeferredCommandNames[i], counters.total[i], counters.repeat[i],
                    100.0 * double(counters.repeat[i]) / double(counters.total[i]));
      }
    }
    counters = DeferredCommandCounters();
    counters.last_log = now;
  }
#endif  // REX_D3D12_DEFERRED_COUNTERS
}
'''),
]


def main():
    out = {}
    for rel, pairs in EDITS.items():
        data = (ORIG / rel).read_bytes().decode("utf-8")
        if "\r" in data:
            sys.exit(f"{rel}: base has CR bytes")
        for i, (old, new) in enumerate(pairs):
            n = data.count(old)
            if n != 1:
                sys.exit(f"{rel}: edit {i}: target found {n} times; nothing written")
            data = data.replace(old, new)
        out[rel] = data
    for rel, data in out.items():
        raw = data.encode("utf-8")
        (NEW / rel).write_bytes(raw)
        print(f"{rel}: {len(EDITS[rel])} edits, {len(raw)} bytes, {data.count(chr(10))} lines")
    # unified diffs with a/ b/ paths relative to the SDK root (git apply -p1)
    diffs = {
        "r1-split.diff": [CP_H, CP_CPP, DCL_H],
        "r2-counters.diff": [DCL_CPP],
        "s4-r1r2.diff": [CP_H, DCL_H, CP_CPP, DCL_CPP],
    }
    for name, rels in diffs.items():
        text = []
        for rel in rels:
            a = (ORIG / rel).read_bytes().decode("utf-8").splitlines(keepends=True)
            b = (NEW / rel).read_bytes().decode("utf-8").splitlines(keepends=True)
            text.append(f"diff --git a/{rel} b/{rel}\n")
            text.extend(difflib.unified_diff(a, b, f"a/{rel}", f"b/{rel}", n=3))
        (STAGE / name).write_bytes("".join(text).encode("utf-8"))
        print(f"{name}: {', '.join(rels)}")


if __name__ == "__main__":
    main()
