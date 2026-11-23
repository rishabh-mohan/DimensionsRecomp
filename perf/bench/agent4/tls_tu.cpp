#include "tls_tu.h"

thread_local DrawPreparationContext* t_draw_preparation = nullptr;
DrawPreparationContext* CurrentDrawPreparation() { return t_draw_preparation; }
void SetDrawPreparation(DrawPreparationContext* context) { t_draw_preparation = context; }

namespace {
int g_frame_commands = 0;
}
void* BeginFrameCommands() { return &g_frame_commands; }
uint64_t CurrentDrawDeviceView() { return 42; }
