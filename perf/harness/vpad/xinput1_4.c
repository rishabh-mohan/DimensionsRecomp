/* harness/vpad/xinput1_4.c - Agent 3's virtual XInput pad. Harness-only test tooling, user mode only
 * (perf-notes/agent3-run-harness.md section 7): a stand-in for xinput1_4.dll that harness/run-game.ps1 -InputScript
 * copies into its own run dir, next to the exe. The game's XInput driver (--input_backend=xinput) loads
 * "xinput1_4.dll" by name and it is not a KnownDLL, so it gets this copy. Never put it in a staged
 * agent2 bin dir (build/agent2/NAME-bin); nothing is installed anywhere.
 *
 * Env AGENT3_VPAD = path of the 4 KiB state file the harness keeps mapped (harness/vpad/vpadhost.cs writes it).
 * Without it, or before the file has the magic, every slot is ERROR_DEVICE_NOT_CONNECTED. The DLL counts its calls
 * in the same file, so the harness can show that the game polls the pad and saw the presses. XInputGetKeystroke
 * hands out VK_PAD_* key-down/key-up events made from the button changes. XInputEnable is recorded, not applied.
 * No CRT and no headers: kernel32 only (harness/vpad/build-vpad.ps1).
 */
#if !defined(_M_X64)
#error x64 only
#endif

typedef unsigned char BYTE;
typedef unsigned short WORD;
typedef unsigned long DWORD;
typedef long LONG;
typedef short SHORT;
typedef int BOOL;
typedef __WCHAR_TYPE__ WCHAR;
typedef unsigned long long ULONGLONG;
typedef unsigned long long SIZE_T;
typedef void *HANDLE;
#define WINAPI __stdcall
#define IMPORT __declspec(dllimport)

IMPORT DWORD WINAPI GetEnvironmentVariableW(const WCHAR *name, WCHAR *buf, DWORD size);
IMPORT HANDLE WINAPI CreateFileW(const WCHAR *name, DWORD access, DWORD share, void *sa, DWORD disposition, DWORD flags,
                                 HANDLE tmpl);
IMPORT HANDLE WINAPI CreateFileMappingW(HANDLE file, void *sa, DWORD protect, DWORD size_high, DWORD size_low,
                                        const WCHAR *name);
IMPORT void *WINAPI MapViewOfFile(HANDLE mapping, DWORD access, DWORD off_high, DWORD off_low, SIZE_T bytes);
IMPORT BOOL WINAPI UnmapViewOfFile(const void *view);
IMPORT BOOL WINAPI CloseHandle(HANDLE h);
IMPORT ULONGLONG WINAPI GetTickCount64(void);
IMPORT DWORD WINAPI GetCurrentProcessId(void);
IMPORT DWORD WINAPI GetModuleFileNameW(HANDLE module, WCHAR *buf, DWORD size);
IMPORT BOOL WINAPI DisableThreadLibraryCalls(HANDLE module);

#define ERROR_SUCCESS 0u
#define ERROR_BAD_ARGUMENTS 160u
#define ERROR_DEVICE_NOT_CONNECTED 1167u
#define ERROR_EMPTY 4306u

/* XInput structures, same layout as xinput.h. */
typedef struct { WORD wButtons; BYTE bLeftTrigger, bRightTrigger; SHORT sThumbLX, sThumbLY, sThumbRX, sThumbRY; } VP_GAMEPAD;
typedef struct { DWORD dwPacketNumber; VP_GAMEPAD Gamepad; } VP_STATE;
typedef struct { WORD wLeftMotorSpeed, wRightMotorSpeed; } VP_VIBRATION;
typedef struct { BYTE Type, SubType; WORD Flags; VP_GAMEPAD Gamepad; VP_VIBRATION Vibration; } VP_CAPABILITIES;
typedef struct { WORD VirtualKey; WCHAR Unicode; WORD Flags; BYTE UserIndex, HidCode; } VP_KEYSTROKE;
typedef struct { BYTE BatteryType, BatteryLevel; } VP_BATTERY;

/* The state file (4096 bytes). harness/vpad/vpadhost.cs uses the same offsets. */
#define VPAD_MAGIC 0x31444150 /* "PAD1" */
#define VPAD_SIZE 4096u
typedef struct {
    volatile LONG seq; /* even = stable; the harness makes it odd while it writes the slot */
    volatile WORD buttons;
    volatile BYTE lt, rt;
    volatile SHORT lx, ly, rx, ry;
} VPAD_SLOT;
typedef struct {
    volatile LONG magic;           /*   0 harness, written last */
    volatile LONG version;         /*   4 harness: 1 */
    volatile LONG connected;       /*   8 harness: bit n = slot n connected */
    volatile LONG dll_pid;         /*  12 DLL: pid of the process that mapped the file */
    volatile LONG reads[4];        /*  16 DLL: XInputGetState(Ex) calls per slot */
    volatile LONG active_reads[4]; /*  32 DLL: ... that returned a pressed button, trigger or stick */
    volatile LONG caps_calls;      /*  48 DLL: XInputGetCapabilities calls on connected slots */
    volatile LONG key_calls;       /*  52 DLL: XInputGetKeystroke calls */
    volatile LONG key_events;      /*  56 DLL: keystrokes handed out */
    volatile LONG set_calls;       /*  60 DLL: XInputSetState calls on connected slots */
    volatile LONG enable_calls;    /*  64 DLL: XInputEnable calls */
    volatile LONG enable_last;     /*  68 DLL: last XInputEnable argument */
    volatile LONG vibration[4];    /*  72 DLL: last XInputSetState per slot, left << 16 | right */
    volatile LONG maps;            /*  88 DLL: times a process mapped the file */
    volatile LONG reserved[9];     /*  92 */
    VPAD_SLOT slot[4];             /* 128 harness */
    WCHAR dll_path[260];           /* 192 DLL: path of this DLL in the process that mapped the file */
} VPAD_SHM;
_Static_assert(sizeof(VPAD_SLOT) == 16, "slot layout");
_Static_assert(__builtin_offsetof(VPAD_SHM, maps) == 88, "layout");
_Static_assert(__builtin_offsetof(VPAD_SHM, slot) == 128, "layout");
_Static_assert(__builtin_offsetof(VPAD_SHM, dll_path) == 192, "layout");
_Static_assert(sizeof(VPAD_SHM) <= VPAD_SIZE, "layout");

static HANDLE g_module;
static VPAD_SHM *g_shm; /* published once, release/acquire */
static LONG g_busy;
static ULONGLONG g_next_try;
static WORD g_key_prev[4];

static VPAD_SHM *Shm(void) {
    VPAD_SHM *p = __atomic_load_n(&g_shm, __ATOMIC_ACQUIRE);
    if (p) return p;
    LONG expected = 0;
    if (!__atomic_compare_exchange_n(&g_busy, &expected, 1, 0, __ATOMIC_ACQUIRE, __ATOMIC_RELAXED)) return 0;
    ULONGLONG now = GetTickCount64();
    if (now >= g_next_try) {
        g_next_try = now + 1000; /* the harness makes the file before the launch; still, retry once a second */
        WCHAR path[520];
        DWORD n = GetEnvironmentVariableW(L"AGENT3_VPAD", path, 520);
        if (n > 0 && n < 520) {
            HANDLE f = CreateFileW(path, 0xC0000000u /* GENERIC_READ | GENERIC_WRITE */, 7u /* share r/w/delete */, 0,
                                   3u /* OPEN_EXISTING */, 0x80u /* FILE_ATTRIBUTE_NORMAL */, 0);
            if (f != (HANDLE)(long long)-1) {
                HANDLE m = CreateFileMappingW(f, 0, 0x04u /* PAGE_READWRITE */, 0, VPAD_SIZE, 0);
                if (m) {
                    VPAD_SHM *v = (VPAD_SHM *)MapViewOfFile(m, 0x0006u /* FILE_MAP_READ | FILE_MAP_WRITE */, 0, 0, VPAD_SIZE);
                    if (v && v->magic == VPAD_MAGIC) {
                        v->dll_pid = (LONG)GetCurrentProcessId();
                        GetModuleFileNameW(g_module, v->dll_path, 259);
                        __atomic_add_fetch(&v->maps, 1, __ATOMIC_SEQ_CST);
                        __atomic_store_n(&g_shm, v, __ATOMIC_RELEASE);
                        p = v;
                    } else if (v) {
                        UnmapViewOfFile(v);
                    }
                    CloseHandle(m); /* the view keeps the section alive */
                }
                CloseHandle(f);
            }
        }
    }
    __atomic_store_n(&g_busy, 0, __ATOMIC_RELEASE);
    return p;
}

static int Connected(VPAD_SHM *s, DWORD i) { return (s->connected >> i) & 1; }

/* Seqlock read of one slot: retry while the harness is in the middle of a write. */
static DWORD ReadSlot(VPAD_SHM *s, DWORD i, VP_GAMEPAD *g) {
    VPAD_SLOT *sl = &s->slot[i];
    for (int tries = 0;; tries++) {
        LONG a = sl->seq;
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        g->wButtons = sl->buttons;
        g->bLeftTrigger = sl->lt;
        g->bRightTrigger = sl->rt;
        g->sThumbLX = sl->lx;
        g->sThumbLY = sl->ly;
        g->sThumbRX = sl->rx;
        g->sThumbRY = sl->ry;
        __atomic_thread_fence(__ATOMIC_ACQUIRE);
        if (((a & 1) == 0 && sl->seq == a) || tries >= 1000) return (DWORD)a >> 1;
        __builtin_ia32_pause();
    }
}

static DWORD GetStateImpl(DWORD i, VP_STATE *st) {
    if (i >= 4 || !st) return ERROR_BAD_ARGUMENTS;
    VPAD_SHM *s = Shm();
    if (!s) return ERROR_DEVICE_NOT_CONNECTED;
    __atomic_add_fetch(&s->reads[i], 1, __ATOMIC_RELAXED);
    if (!Connected(s, i)) return ERROR_DEVICE_NOT_CONNECTED;
    st->dwPacketNumber = ReadSlot(s, i, &st->Gamepad);
    const VP_GAMEPAD *g = &st->Gamepad;
    if (g->wButtons | g->bLeftTrigger | g->bRightTrigger | g->sThumbLX | g->sThumbLY | g->sThumbRX | g->sThumbRY)
        __atomic_add_fetch(&s->active_reads[i], 1, __ATOMIC_RELAXED);
    return ERROR_SUCCESS;
}

DWORD WINAPI XInputGetState(DWORD i, VP_STATE *st) { return GetStateImpl(i, st); }
DWORD WINAPI XInputGetStateEx(DWORD i, VP_STATE *st) { return GetStateImpl(i, st); } /* ordinal 100 */

DWORD WINAPI XInputGetCapabilities(DWORD i, DWORD flags, VP_CAPABILITIES *c) {
    (void)flags;
    if (i >= 4 || !c) return ERROR_BAD_ARGUMENTS;
    VPAD_SHM *s = Shm();
    if (!s || !Connected(s, i)) return ERROR_DEVICE_NOT_CONNECTED;
    __atomic_add_fetch(&s->caps_calls, 1, __ATOMIC_RELAXED);
    c->Type = 1;    /* XINPUT_DEVTYPE_GAMEPAD */
    c->SubType = 1; /* XINPUT_DEVSUBTYPE_GAMEPAD */
    c->Flags = 0;
    c->Gamepad.wButtons = 0xF3FF;
    c->Gamepad.bLeftTrigger = 0xFF;
    c->Gamepad.bRightTrigger = 0xFF;
    c->Gamepad.sThumbLX = (SHORT)0xFFC0;
    c->Gamepad.sThumbLY = (SHORT)0xFFC0;
    c->Gamepad.sThumbRX = (SHORT)0xFFC0;
    c->Gamepad.sThumbRY = (SHORT)0xFFC0;
    c->Vibration.wLeftMotorSpeed = 0xFF;
    c->Vibration.wRightMotorSpeed = 0xFF;
    return ERROR_SUCCESS;
}

/* Button bit -> VK_PAD_* (guide has none). */
static const WORD kKeyBits[14] = {0x1000, 0x2000, 0x4000, 0x8000, 0x0200, 0x0100, 0x0001,
                                  0x0002, 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080};
static const WORD kKeyVks[14] = {0x5800, 0x5801, 0x5802, 0x5803, 0x5804, 0x5805, 0x5810,
                                 0x5811, 0x5812, 0x5813, 0x5814, 0x5815, 0x5816, 0x5817};

DWORD WINAPI XInputGetKeystroke(DWORD i, DWORD reserved, VP_KEYSTROKE *k) {
    (void)reserved;
    if (!k || (i >= 4 && i != 0xFF)) return ERROR_BAD_ARGUMENTS;
    VPAD_SHM *s = Shm();
    if (!s) return ERROR_DEVICE_NOT_CONNECTED;
    __atomic_add_fetch(&s->key_calls, 1, __ATOMIC_RELAXED);
    DWORD first = i == 0xFF ? 0 : i, last = i == 0xFF ? 3 : i;
    int any = 0;
    for (DWORD u = first; u <= last; u++) {
        if (!Connected(s, u)) continue;
        any = 1;
        VP_GAMEPAD g;
        ReadSlot(s, u, &g);
        WORD diff = (WORD)(g.wButtons ^ g_key_prev[u]);
        for (int b = 0; diff && b < 14; b++) {
            if (!(diff & kKeyBits[b])) continue;
            g_key_prev[u] = (WORD)(g_key_prev[u] ^ kKeyBits[b]);
            k->VirtualKey = kKeyVks[b];
            k->Unicode = 0;
            k->Flags = (g.wButtons & kKeyBits[b]) ? 0x0001 /* KEYDOWN */ : 0x0002 /* KEYUP */;
            k->UserIndex = (BYTE)u;
            k->HidCode = 0;
            __atomic_add_fetch(&s->key_events, 1, __ATOMIC_RELAXED);
            return ERROR_SUCCESS;
        }
        g_key_prev[u] = g.wButtons; /* only bits without a VK were left */
    }
    return any ? ERROR_EMPTY : ERROR_DEVICE_NOT_CONNECTED;
}

DWORD WINAPI XInputSetState(DWORD i, VP_VIBRATION *v) {
    if (i >= 4 || !v) return ERROR_BAD_ARGUMENTS;
    VPAD_SHM *s = Shm();
    if (!s || !Connected(s, i)) return ERROR_DEVICE_NOT_CONNECTED;
    __atomic_add_fetch(&s->set_calls, 1, __ATOMIC_RELAXED);
    s->vibration[i] = (LONG)(((DWORD)v->wLeftMotorSpeed << 16) | v->wRightMotorSpeed);
    return ERROR_SUCCESS;
}

void WINAPI XInputEnable(BOOL enable) {
    VPAD_SHM *s = Shm();
    if (!s) return;
    __atomic_add_fetch(&s->enable_calls, 1, __ATOMIC_RELAXED);
    s->enable_last = enable;
}

DWORD WINAPI XInputGetBatteryInformation(DWORD i, BYTE dev_type, VP_BATTERY *b) {
    (void)dev_type;
    if (i >= 4 || !b) return ERROR_BAD_ARGUMENTS;
    VPAD_SHM *s = Shm();
    if (!s || !Connected(s, i)) return ERROR_DEVICE_NOT_CONNECTED;
    b->BatteryType = 1;  /* BATTERY_TYPE_WIRED */
    b->BatteryLevel = 3; /* BATTERY_LEVEL_FULL */
    return ERROR_SUCCESS;
}

BOOL WINAPI VpadDllMain(HANDLE module, DWORD reason, void *reserved) {
    (void)reserved;
    if (reason == 1 /* DLL_PROCESS_ATTACH */) {
        g_module = module;
        DisableThreadLibraryCalls(module);
    }
    return 1;
}
