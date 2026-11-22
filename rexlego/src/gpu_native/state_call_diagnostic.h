// Counts guest draw binding requests; equal requests are not a D3D skip proof.
#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <utility>

namespace legodimensions::gpu_native {

struct StateCallCounts {
  uint64_t draws = 0, dropped_draws = 0, recordings = 0;
  uint64_t layouts = 0, equal_layouts = 0;
  uint64_t pipelines = 0, equal_pipelines = 0;
  std::array<uint64_t, 4> descriptors{}, equal_descriptors{};
  // skipped_* count calls LEGO_NATIVE_ELIDE_STATE_CALLS actually left out.
  uint64_t framebuffers = 0, equal_framebuffers = 0;
  uint64_t index_buffers = 0, equal_index_buffers = 0, skipped_index_buffers = 0;
  uint64_t blend_factors = 0, equal_blend_factors = 0, skipped_blend_factors = 0;
  uint64_t viewports = 0, equal_viewports = 0;
  uint64_t scissors = 0, equal_scissors = 0;
};

// The last value requested in this recording, compared bytewise as the API receives it.
template <class T>
struct LastRequest {
  T value{};
  bool set = false;
  bool Same(const T& next) {
    const bool same = set && std::memcmp(&value, &next, sizeof(T)) == 0;
    value = next;
    set = true;
    return same;
  }
};

class StateCallLedger {
 public:
  static constexpr uint32_t kMaxDraws = 4096;
  bool BeginDraw(const void* commands, uint64_t serial) {
    if (counts_.draws >= kMaxDraws) {
      ++counts_.dropped_draws;
      return false;
    }
    ++counts_.draws;
    if (commands != commands_ || serial != serial_) {
      ++counts_.recordings;
      commands_ = commands;
      serial_ = serial;
      layout_ = pipeline_ = nullptr;
      descriptors_.fill(nullptr);
      framebuffer_ = {};
      index_ = {};
      blend_ = {};
      viewport_ = {};
      scissor_ = {};
    }
    return true;
  }
  void Layout(const void* layout) {
    ++counts_.layouts;
    if (layout_ && layout_ == layout) ++counts_.equal_layouts;
    // A changed root signature invalidates its table comparisons.
    if (layout_ != layout) descriptors_.fill(nullptr);
    layout_ = layout;
  }
  void Descriptor(const void* descriptor, uint32_t slot) {
    if (slot >= descriptors_.size()) return;
    ++counts_.descriptors[slot];
    if (descriptors_[slot] && descriptors_[slot] == descriptor)
      ++counts_.equal_descriptors[slot];
    descriptors_[slot] = descriptor;
  }
  void Pipeline(const void* pipeline) {
    ++counts_.pipelines;
    if (pipeline_ && pipeline_ == pipeline) ++counts_.equal_pipelines;
    pipeline_ = pipeline;
  }
  void Framebuffer(const void* framebuffer) {
    ++counts_.framebuffers;
    if (framebuffer_.Same(framebuffer)) ++counts_.equal_framebuffers;
  }
  void IndexBuffer(uint64_t address, uint32_t size, uint32_t format) {
    ++counts_.index_buffers;
    if (index_.Same({address, size, format})) ++counts_.equal_index_buffers;
  }
  void SkippedIndexBuffer() { ++counts_.skipped_index_buffers; }
  void BlendFactor(const std::array<float, 4>& value) {
    ++counts_.blend_factors;
    if (blend_.Same(value)) ++counts_.equal_blend_factors;
  }
  void SkippedBlendFactor() { ++counts_.skipped_blend_factors; }
  void Viewport(const std::array<float, 6>& value) {
    ++counts_.viewports;
    if (viewport_.Same(value)) ++counts_.equal_viewports;
  }
  void Scissor(const std::array<int32_t, 4>& value) {
    ++counts_.scissors;
    if (scissor_.Same(value)) ++counts_.equal_scissors;
  }
  const StateCallCounts& Counts() const { return counts_; }
  void Reset() { *this = {}; }

 private:
  StateCallCounts counts_;
  const void* commands_ = nullptr;
  uint64_t serial_ = 0;
  const void* layout_ = nullptr;
  const void* pipeline_ = nullptr;
  std::array<const void*, 4> descriptors_{};
  LastRequest<const void*> framebuffer_;
  LastRequest<std::array<uint64_t, 3>> index_;
  LastRequest<std::array<float, 4>> blend_;
  LastRequest<std::array<float, 6>> viewport_;
  LastRequest<std::array<int32_t, 4>> scissor_;
};

// One finite capture per process. Optional trigger arms the next present
// interval; polling and file output occur only at the guest present hook.
class StateCallCapture {
 public:
  static constexpr uint32_t kMaxFrames = 120;
  StateCallCapture(std::filesystem::path output, std::filesystem::path trigger)
      : output_(std::move(output)), trigger_(std::move(trigger)),
        armed_(!output_.empty() && trigger_.empty()) {}
  StateCallLedger* BeginDraw(const void* commands, uint64_t serial) {
    if (!armed_ || !commands || !serial || exhausted_) return nullptr;
    return ledger_.BeginDraw(commands, serial) ? &ledger_ : nullptr;
  }
  void Present(uint32_t frame) {
    if (output_.empty() || exhausted_) return;
    if (!armed_) {
      std::error_code error;
      if (!std::filesystem::is_regular_file(trigger_, error) || error) return;
      if (!std::filesystem::remove(trigger_, error) || error) return;
      armed_ = true;
      return;
    }
    if (!file_.is_open()) {
      // A diagnostic cannot overwrite existing evidence.
      std::error_code error;
      if (std::filesystem::exists(output_, error) || error) {
        exhausted_ = true;
        return;
      }
      file_.open(output_, std::ios::out);
      if (!file_) { exhausted_ = true; return; }
      file_ << "# scope=guest_draw_requests;equal=adjacent_guest_request;"
               "unobserved_helper_compute_ray_or_external_calls_not_measured;"
               "skipped=elided_by_LEGO_NATIVE_ELIDE_STATE_CALLS;"
               "max_frames=120;max_draws_per_frame=4096\n"
               "frame,draws,dropped_draws,recordings,layout_calls,layout_equal,"
               "pso_calls,pso_equal,table0_calls,table0_equal,table1_calls,table1_equal,"
               "table2_calls,table2_equal,table3_calls,table3_equal,"
               "framebuffer_calls,framebuffer_equal,index_calls,index_equal,index_skipped,"
               "blend_calls,blend_equal,blend_skipped,viewport_calls,viewport_equal,"
               "scissor_calls,scissor_equal\n";
    }
    const auto& count = ledger_.Counts();
    file_ << frame << ',' << count.draws << ',' << count.dropped_draws << ','
          << count.recordings << ',' << count.layouts << ',' << count.equal_layouts
          << ',' << count.pipelines << ',' << count.equal_pipelines;
    for (size_t i = 0; i < count.descriptors.size(); ++i)
      file_ << ',' << count.descriptors[i] << ',' << count.equal_descriptors[i];
    file_ << ',' << count.framebuffers << ',' << count.equal_framebuffers
          << ',' << count.index_buffers << ',' << count.equal_index_buffers
          << ',' << count.skipped_index_buffers << ',' << count.blend_factors
          << ',' << count.equal_blend_factors << ',' << count.skipped_blend_factors
          << ',' << count.viewports << ',' << count.equal_viewports
          << ',' << count.scissors << ',' << count.equal_scissors;
    file_ << '\n';
    file_.flush();
    ledger_.Reset();
    if (!file_ || ++frames_ >= kMaxFrames) {
      exhausted_ = true;
      file_.close();
    }
  }

 private:
  std::filesystem::path output_, trigger_;
  StateCallLedger ledger_;
  std::ofstream file_;
  uint32_t frames_ = 0;
  bool armed_ = false, exhausted_ = false;
};

}  // namespace legodimensions::gpu_native
