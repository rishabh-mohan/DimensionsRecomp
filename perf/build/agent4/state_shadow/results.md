| build | case | expected exit | exit | ok |
|---|---|---:|---:|---|
| real | unit | 0 | 0 | yes |
| real | oracle elision | 0 | 0 | yes |
| real | oracle variable unset | 0 | 0 | yes |
| real | oracle full preparation | 0 | 0 | yes |
| real | negative: lookup after the layout bind | 3 | 3 | yes |
| real | negative: external write without notify | 3 | 3 | yes |
| real | negative: draw-layout rebind after external write | 3 | 3 | yes |
| mutant no_tripwire | --oracle | 3 | 3 | yes |
| mutant ignore_serial | --oracle | 3 | 3 | yes |
| mutant no_tripwire_ignore_serial | --oracle | 3 | 3 | yes |
| mutant no_heaps_check | --oracle | 3 | 3 | yes |
| mutant no_root_signature_check | --oracle | 3 | 3 | yes |
| mutant full_prep_gate_removed | --oracle | 3 | 3 | yes |
| mutant preparation_gate_removed | --unit | 1 | 1 | yes |
| mutant env_parse_loose | --unit | 1 | 1 | yes |
| mutant shadow_ignores_size | --oracle | 3 | 3 | yes |
| mutant shadow_ignores_format | --oracle | 3 | 3 | yes |
| mutant blend_float_compare | --oracle | 3 | 3 | yes |
| mutant invalidate_keeps_blend | --oracle | 3 | 3 | yes |
| mutant begin_ignores_layout | --unit | 1 | 1 | yes |

| audit | ok |
|---|---|
| draw.cpp: one shadow lookup, inside DispatchDraw | yes |
| DispatchDraw: the lookup precedes its first BindNativeDrawLayout (plume flags still unrevalidated) | yes |
| draw.cpp: the only SetNativeBlendFactor call is guarded by SameDrawBlendFactor | yes |
| draw.cpp: both setIndexBuffer calls are guarded by SameDrawIndexBuffer | yes |
| rexlego/src setIndexBuffer( = draw.cpp x2 + native_recording.cpp tape: {'draw.cpp': [3550, 3577], 'native_recording.cpp': [393, 399]} | yes |
| rexlego/src raw IASetIndexBuffer = native overlay only: {'native_overlay_gpu.cpp': [176]} | yes |
| rexlego/src OMSetBlendFactor = native_recording.cpp (tape replay, SetNativeBlendFactor): {'native_recording.cpp': [322, 542]} | yes |
| rexlego/src SetNativeBlendFactor( = draw.cpp call + native_recording declaration/definition: {'draw.cpp': [2948], 'native_recording.cpp': [534], 'native_recording.h': [44]} | yes |
| rexlego/src has no ClearState / ExecuteBundle / ExecuteIndirect: {} | yes |
| rexlego/src ->begin() = device.cpp frame list + native_recording.cpp tape: {'device.cpp': [744], 'native_recording.cpp': [334]} | yes |
| device.cpp: ++g_recording_serial follows the frame list begin() before it is returned | yes |
| device.cpp: the native overlay is followed by both notify calls, then end(), with no draw between | yes |
| plume begin() calls notifyCommandStateWasChangedExternally | yes |
| plume end() clears descriptorHeapsSet and calls notifyCommandStateWasChangedExternally | yes |
| plume notifyDescriptorHeapWasChangedExternally clears descriptorHeapsSet | yes |
| plume notifyCommandStateWasChangedExternally nulls the graphics root signature and validity | yes |
| plume setGraphicsPipelineLayout records the root signature and sets validity | yes |
| plume sets cachedGraphicsRootValid / descriptorHeapsSet true in one place each | yes |
| plume setIndexBuffer binds (gpuVA + offset or 0, toDXGI(format), size): the shadow key | yes |
