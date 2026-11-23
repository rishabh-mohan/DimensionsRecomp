// Item 4 bench support: device.cpp's out-of-line CurrentDrawPreparation and the HostDevice calls the
// draw path makes when no preparation is active (separate TU, so calls stay calls).
#pragma once
#include <cstdint>

struct DrawPreparationContext {
  bool alias_decided = false;
  void* commands = nullptr;
  uint64_t view = 0;
};

DrawPreparationContext* CurrentDrawPreparation();          // device.cpp:752
void SetDrawPreparation(DrawPreparationContext* context);  // DrawPreparationScope
// The alternative that needs device.cpp/device.h (Agent 7): an inline accessor.
extern thread_local DrawPreparationContext* t_draw_preparation;
inline DrawPreparationContext* CurrentDrawPreparationInline() { return t_draw_preparation; }

void* BeginFrameCommands();         // HostDevice::BeginFrameCommands
uint64_t CurrentDrawDeviceView();   // HostDevice::CurrentDrawDeviceView
