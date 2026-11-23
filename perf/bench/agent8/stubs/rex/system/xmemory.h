// Bench stub for rex/system/xmemory.h (agent8 runtime benches).
//
// cheat_engine.cpp only needs Memory::physical_membase(): the host address of
// guest physical address 0, covering 512 MiB. The bench hands it a
// VirtualAlloc'd 512 MiB reservation with only some chunks committed, so the
// engine's VirtualQuery-based region walk sees committed and reserved ranges
// just as it does over the real physical view.
#pragma once

#include <cstdint>

namespace rex::memory {

class Memory {
 public:
  explicit Memory(uint8_t* physical_membase) : physical_membase_(physical_membase) {}

  inline uint8_t* physical_membase() const { return physical_membase_; }

 private:
  uint8_t* physical_membase_ = nullptr;
};

}  // namespace rex::memory
