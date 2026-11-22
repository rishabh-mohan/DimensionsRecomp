// Last index buffer and blend factor bound on one command recording. Std-only (bench/agent4 tests it).
#pragma once
#include <array>
#include <cstdint>
#include <cstring>

namespace legodimensions::gpu_native {

// D3D12 keeps IASetIndexBuffer and OMSetBlendFactor state until the list sets it again or is
// reset; PSO, root signature and descriptor heap changes leave it alone. The owner keys a recording
// by (list, serial, layout), routes every set of these two states on it through Same*(), and calls
// Invalidate() whenever another writer may have touched the list.
class DrawStateShadow {
 public:
  // The D3D12_INDEX_BUFFER_VIEW fields: GPU address, byte size, format.
  struct IndexBuffer {
    uint64_t address = 0;
    uint32_t size = 0, format = 0;
  };

  // Returns true, and forgets every bound value, when the key changed.
  bool Begin(const void* commands, uint64_t serial, const void* layout) {
    if (commands == commands_ && serial == serial_ && layout == layout_) return false;
    commands_ = commands;
    serial_ = serial;
    layout_ = layout;
    Invalidate();
    return true;
  }
  void Invalidate() { index_set_ = blend_set_ = false; }

  // True when `value` is already bound, so the call may be skipped; otherwise records it as bound.
  bool SameIndexBuffer(const IndexBuffer& value) {
    if (index_set_ && index_.address == value.address && index_.size == value.size &&
        index_.format == value.format) return true;
    index_ = value;
    index_set_ = true;
    return false;
  }
  // Bitwise, as the call takes the floats: -0 and +0 differ, identical NaN bits match.
  bool SameBlendFactor(const std::array<float, 4>& value) {
    if (blend_set_ && std::memcmp(blend_.data(), value.data(), sizeof(blend_)) == 0) return true;
    blend_ = value;
    blend_set_ = true;
    return false;
  }

 private:
  const void* commands_ = nullptr;
  const void* layout_ = nullptr;
  uint64_t serial_ = 0;
  IndexBuffer index_;
  std::array<float, 4> blend_{};
  bool index_set_ = false, blend_set_ = false;
};

}  // namespace legodimensions::gpu_native
