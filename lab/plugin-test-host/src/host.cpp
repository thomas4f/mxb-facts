// Test host posing as mxbikes.exe (or gpbikes.exe, built with -DGPB): GL window, plugin-API calls, fake telemetry.
#include <windows.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <vector>
#include <string>
#ifdef GPB
#include "gpb_api.h"  // GP Bikes struct layouts, taken by setup.sh from PiBoSo's GP Bikes plugin example
#define GAME_NAME "GP Bikes"
#else
#include "mxb_api.h"
#define GAME_NAME "MX Bikes"
#endif

#define LOG(...) do { printf(__VA_ARGS__); fflush(stdout); } while (0)

typedef char* (*PFN_GetModID)();
typedef int (*PFN_Int)();
typedef int (*PFN_Startup)(char*);
typedef void (*PFN_Void)();
typedef void (*PFN_Data)(void*, int);
typedef void (*PFN_Tele)(void*, int, float, float);
typedef void (*PFN_TrackPos)(int, void*, int);
typedef int (*PFN_DrawInit)(int*, char**, int*, char**);
typedef void (*PFN_Draw)(int, int*, void**, int*, void**);

// The draw API's structs are the same in every PiBoSo game.
struct Quad { float pos[4][2]; int sprite; unsigned long color; };
struct Str { char text[100]; float pos[2]; int font; float size; int justify; unsigned long color; };

struct Plugin {
    std::string path;
    HMODULE mod = nullptr;
    PFN_GetModID GetModID = nullptr;
    PFN_Startup Startup = nullptr;
    PFN_Void Shutdown = nullptr, RunStart = nullptr, RunStop = nullptr, RunDeinit = nullptr, EventDeinit = nullptr;
    PFN_Data EventInit = nullptr, RunInit = nullptr, RaceVehicleData = nullptr;
    PFN_Tele RunTelemetry = nullptr;
    PFN_TrackPos RaceTrackPosition = nullptr;
    PFN_Void VictimReport = nullptr;
    PFN_DrawInit DrawInit = nullptr;
    PFN_Draw Draw = nullptr;
    int lastQuads = -1, lastStrings = -1;  // what Draw returned last, to log only changes
    Str* strings = nullptr;
};

// GL functions the "game" stores in globals via wglGetProcAddress (writable .data/.bss, like the real game).
typedef void (APIENTRY* PFN_DRE)(GLenum, GLuint, GLuint, GLsizei, GLenum, const void*);
static PFN_DRE g_glDrawRangeElements = nullptr;
static void* g_realDre = nullptr;

extern "C" {
extern void* __imp_glOrtho; extern void* __imp_glFrustum; extern void* __imp_glDrawElements;
extern void* __imp_glLoadMatrixf; extern void* __imp_glLoadIdentity; extern void* __imp_glMatrixMode;
extern void* __imp_glViewport; extern void* __imp_glClear; extern void* __imp_glBegin;
extern void* __imp_glReadPixels; extern void* __imp_SwapBuffers; extern void* __imp_wglGetProcAddress;
extern void* __imp_glScissor; extern void* __imp_glBlendFunc; extern void* __imp_glGetFloatv;
}
struct Slot { const char* name; void** imp; const char* dll; };
static Slot g_slots[] = {
    {"glOrtho", &__imp_glOrtho, "opengl32"}, {"glFrustum", &__imp_glFrustum, "opengl32"},
    {"glDrawElements", &__imp_glDrawElements, "opengl32"}, {"glLoadMatrixf", &__imp_glLoadMatrixf, "opengl32"},
    {"glLoadIdentity", &__imp_glLoadIdentity, "opengl32"}, {"glMatrixMode", &__imp_glMatrixMode, "opengl32"},
    {"glViewport", &__imp_glViewport, "opengl32"}, {"glClear", &__imp_glClear, "opengl32"},
    {"glBegin", &__imp_glBegin, "opengl32"}, {"glReadPixels", &__imp_glReadPixels, "opengl32"},
    {"glScissor", &__imp_glScissor, "opengl32"}, {"glBlendFunc", &__imp_glBlendFunc, "opengl32"},
    {"glGetFloatv", &__imp_glGetFloatv, "opengl32"},
    {"wglGetProcAddress", &__imp_wglGetProcAddress, "opengl32"}, {"SwapBuffers", &__imp_SwapBuffers, "gdi32"},
};

static const char* module_of(void* p) {
    static char buf[MAX_PATH];
    HMODULE m = nullptr;
    if (!GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)p, &m)) return "?";
    GetModuleFileNameA(m, buf, sizeof(buf));
    const char* s = strrchr(buf, '\\');
    return s ? s + 1 : buf;
}

static void report_slots(const char* when) {
    LOG("== host import table check (%s)\n", when);
    for (auto& s : g_slots) {
        void* real = (void*)GetProcAddress(GetModuleHandleA(s.dll), s.name);
        void* cur = *s.imp;
        LOG("  %-18s %s%s\n", s.name, cur == real ? "untouched" : "REDIRECTED to ", cur == real ? "" : module_of(cur));
    }
    void* realDre = (void*)((uintptr_t)g_realDre ^ 0x5A5A5A5A5A5A5A5AULL);
    LOG("  %-18s %s%s  (global from wglGetProcAddress)\n", "glDrawRangeElements",
        (void*)g_glDrawRangeElements == realDre ? "untouched" : "REDIRECTED to ",
        (void*)g_glDrawRangeElements == realDre ? "" : module_of((void*)g_glDrawRangeElements));
}

static LRESULT CALLBACK wndproc(HWND h, UINT m, WPARAM w, LPARAM l) { return DefWindowProcA(h, m, w, l); }

static void save_bmp(const char* path, int w, int h) {
    std::vector<unsigned char> px(w * h * 3);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadBuffer(GL_BACK);
    glReadPixels(0, 0, w, h, GL_BGR_EXT, GL_UNSIGNED_BYTE, px.data());
    int row = (w * 3 + 3) & ~3;
    BITMAPFILEHEADER fh = {}; BITMAPINFOHEADER ih = {};
    fh.bfType = 0x4D42; fh.bfOffBits = sizeof(fh) + sizeof(ih); fh.bfSize = fh.bfOffBits + row * h;
    ih.biSize = sizeof(ih); ih.biWidth = w; ih.biHeight = h; ih.biPlanes = 1; ih.biBitCount = 24;
    FILE* f = fopen(path, "wb"); if (!f) return;
    fwrite(&fh, sizeof(fh), 1, f); fwrite(&ih, sizeof(ih), 1, f);
    std::vector<unsigned char> pad(row - w * 3);
    for (int y = 0; y < h; ++y) { fwrite(&px[y * w * 3], w * 3, 1, f); if (!pad.empty()) fwrite(pad.data(), pad.size(), 1, f); }
    fclose(f);
}

// --- a tiny "track": a bumpy grid, plus a box for the bike
static std::vector<float> g_v, g_c; static std::vector<unsigned short> g_i;
static void build_scene() {
    const int N = 64; const float S = 4.0f;
    for (int z = 0; z <= N; ++z) for (int x = 0; x <= N; ++x) {
        float wx = (x - N / 2) * S, wz = (z - N / 2) * S;
        float y = 0.6f * sinf(wx * 0.15f) * cosf(wz * 0.11f);
        g_v.insert(g_v.end(), {wx, y, wz});
        float k = ((x + z) & 1) ? 0.45f : 0.38f;
        g_c.insert(g_c.end(), {k + 0.1f, k, k * 0.6f, 1.0f});
    }
    for (int z = 0; z < N; ++z) for (int x = 0; x < N; ++x) {
        unsigned short a = z * (N + 1) + x, b = a + 1, c = a + N + 1, d = c + 1;
        g_i.insert(g_i.end(), {a, c, b, b, c, d});
    }
}

static void direct_hud();
static void draw_frame(int w, int h, float t, float bx, float bz, float yaw, bool helmet) {
    glViewport(0, 0, w, h);
    glClearColor(0.45f, 0.62f, 0.85f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glEnable(GL_DEPTH_TEST);
    // 3D pass, the way an old fixed-function engine does it
    glMatrixMode(GL_PROJECTION); glLoadIdentity();
    float n = 0.1f, f = 1000.0f, ar = (float)w / h, top = n * tanf(35.0f * 3.14159f / 180.0f);
    glFrustum(-top * ar, top * ar, -top, top, n, f);
    glMatrixMode(GL_MODELVIEW);
    float ey = helmet ? 1.5f : 3.0f;
    float cx = bx - (helmet ? 0 : 6) * sinf(yaw), cz = bz - (helmet ? 0 : 6) * cosf(yaw);
    float fx = sinf(yaw), fz = cosf(yaw);
    // look-at view matrix (column-major)
    float rx = fz, rz = -fx; // right = up x forward
    float m[16] = { rx, 0, -fx, 0,  0, 1, 0, 0,  rz, 0, -fz, 0,  0, 0, 0, 1 };
    m[12] = -(rx * cx + rz * cz); m[13] = -ey; m[14] = (fx * cx + fz * cz);
    glLoadMatrixf(m);
    glEnableClientState(GL_VERTEX_ARRAY); glEnableClientState(GL_COLOR_ARRAY);
    glVertexPointer(3, GL_FLOAT, 0, g_v.data()); glColorPointer(4, GL_FLOAT, 0, g_c.data());
    glDrawElements(GL_TRIANGLES, (GLsizei)g_i.size() / 2, GL_UNSIGNED_SHORT, g_i.data());
    if (g_glDrawRangeElements)
        g_glDrawRangeElements(GL_TRIANGLES, 0, (GLuint)(g_v.size() / 3 - 1), (GLsizei)(g_i.size() - g_i.size() / 2), GL_UNSIGNED_SHORT, g_i.data() + g_i.size() / 2);
    glDisableClientState(GL_COLOR_ARRAY); glDisableClientState(GL_VERTEX_ARRAY);
    // the bike: a red box
    glPushMatrix(); glTranslatef(bx, 0.8f, bz); glRotatef(yaw * 57.2958f, 0, 1, 0);
    glBegin(GL_QUADS); glColor3f(0.8f, 0.1f, 0.1f);
    float X = 0.3f, Y = 0.5f, Z = 1.0f;
    float q[6][4][3] = {{{-X,-Y,Z},{X,-Y,Z},{X,Y,Z},{-X,Y,Z}},{{-X,-Y,-Z},{-X,Y,-Z},{X,Y,-Z},{X,-Y,-Z}},
        {{-X,Y,-Z},{-X,Y,Z},{X,Y,Z},{X,Y,-Z}},{{-X,-Y,-Z},{X,-Y,-Z},{X,-Y,Z},{-X,-Y,Z}},
        {{X,-Y,-Z},{X,Y,-Z},{X,Y,Z},{X,-Y,Z}},{{-X,-Y,-Z},{-X,-Y,Z},{-X,Y,Z},{-X,Y,-Z}}};
    for (auto& face : q) for (auto& v : face) glVertex3fv(v);
    glEnd(); glPopMatrix();
    // 2D pass (HUD), like the game's HUD and the Draw-API plugins
    glDisable(GL_DEPTH_TEST);
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0, 1, 1, 0, -1, 1);
    glMatrixMode(GL_MODELVIEW); glLoadIdentity();
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glBegin(GL_QUADS); glColor4f(0, 0, 0, 0.6f);
    glVertex2f(0.02f, 0.02f); glVertex2f(0.30f, 0.02f); glVertex2f(0.30f, 0.12f); glVertex2f(0.02f, 0.12f);
    glColor4f(1, 1, 1, 1);
    for (int i = 0; i < 8; ++i) { float x0 = 0.04f + i * 0.032f; glVertex2f(x0, 0.05f); glVertex2f(x0 + 0.02f, 0.05f); glVertex2f(x0 + 0.02f, 0.09f); glVertex2f(x0, 0.09f); }
    glEnd(); glDisable(GL_BLEND);
    direct_hud();
    (void)t;
}

// In-context renderer as some HUD plugins do it: GL pointers resolved at runtime and kept on the heap,
// so a module-section pointer scan can't see (or redirect) them.
struct DirectGL {
    void (APIENTRY* MatrixMode)(GLenum); void (APIENTRY* LoadIdentity)(); void (APIENTRY* Ortho)(GLdouble, GLdouble, GLdouble, GLdouble, GLdouble, GLdouble);
    void (APIENTRY* Begin)(GLenum); void (APIENTRY* End)(); void (APIENTRY* Color4f)(GLfloat, GLfloat, GLfloat, GLfloat); void (APIENTRY* Vertex2f)(GLfloat, GLfloat);
    void (APIENTRY* GetIntegerv)(GLenum, GLint*);
};
static DirectGL* g_direct = nullptr;
static void direct_init() {
    HMODULE gl = GetModuleHandleA("opengl32.dll"); g_direct = new DirectGL;
    g_direct->MatrixMode = (decltype(g_direct->MatrixMode))GetProcAddress(gl, "glMatrixMode");
    g_direct->LoadIdentity = (decltype(g_direct->LoadIdentity))GetProcAddress(gl, "glLoadIdentity");
    g_direct->Ortho = (decltype(g_direct->Ortho))GetProcAddress(gl, "glOrtho");
    g_direct->Begin = (decltype(g_direct->Begin))GetProcAddress(gl, "glBegin");
    g_direct->End = (decltype(g_direct->End))GetProcAddress(gl, "glEnd");
    g_direct->Color4f = (decltype(g_direct->Color4f))GetProcAddress(gl, "glColor4f");
    g_direct->Vertex2f = (decltype(g_direct->Vertex2f))GetProcAddress(gl, "glVertex2f");
    g_direct->GetIntegerv = (decltype(g_direct->GetIntegerv))GetProcAddress(gl, "glGetIntegerv");
}
static int g_lastVp[4], g_lastFbo;
static void direct_hud() {
    auto& d = *g_direct;
    d.GetIntegerv(GL_VIEWPORT, g_lastVp); d.GetIntegerv(0x8CA6 /*GL_DRAW_FRAMEBUFFER_BINDING*/, &g_lastFbo);
    d.MatrixMode(GL_PROJECTION); d.LoadIdentity(); d.Ortho(0, 1, 1, 0, -1, 1);
    d.MatrixMode(GL_MODELVIEW); d.LoadIdentity();
    d.Begin(GL_QUADS); d.Color4f(0.1f, 0.8f, 0.2f, 1);
    d.Vertex2f(0.80f, 0.02f); d.Vertex2f(0.98f, 0.02f); d.Vertex2f(0.98f, 0.10f); d.Vertex2f(0.80f, 0.10f);
    d.End();
}

static void tap_key(WORD vk, bool down) {
    INPUT in = {}; in.type = INPUT_KEYBOARD; in.ki.wVk = vk; in.ki.dwFlags = down ? 0 : KEYEVENTF_KEYUP;
    SendInput(1, &in, sizeof(in));
}

static void tap_mouse(bool down) {
    INPUT in = {}; in.type = INPUT_MOUSE; in.mi.dwFlags = down ? MOUSEEVENTF_LEFTDOWN : MOUSEEVENTF_LEFTUP;
    SendInput(1, &in, sizeof(in));
}

// Draw API: ask each plugin what it draws, and log it when the number of quads or strings changes.
static void draw_api(std::vector<Plugin>& pl) {
    for (auto& x : pl) {
        if (!x.Draw) continue;
        int nq = 0, ns = 0; void* q = nullptr; void* st = nullptr;
        x.Draw(0, &nq, &q, &ns, &st);
        x.strings = (Str*)st;
        if (nq == x.lastQuads && ns == x.lastStrings) continue;
        x.lastQuads = nq; x.lastStrings = ns;
        LOG("Draw(%s): %d quads, %d strings\n", x.path.c_str(), nq, ns);
        for (int i = 0; i < ns && st; ++i) LOG("  string \"%.100s\" at %.3f,%.3f\n", x.strings[i].text, x.strings[i].pos[0], x.strings[i].pos[1]);
    }
}

// Moves the mouse onto a string a plugin draws (by its text), for --click.
static bool point_at(std::vector<Plugin>& pl, const std::string& text, HWND hwnd, int w, int h) {
    for (auto& x : pl) for (int i = 0; i < x.lastStrings && x.strings; ++i) {
        if (text != x.strings[i].text) continue;
        POINT p = {(LONG)(x.strings[i].pos[0] * w), (LONG)(x.strings[i].pos[1] * h + x.strings[i].size * h / 2)};
        ClientToScreen(hwnd, &p); SetCursorPos(p.x, p.y);
        LOG("mouse on \"%s\" at %ld,%ld\n", text.c_str(), p.x, p.y);
        return true;
    }
    LOG("--click: no string \"%s\" drawn\n", text.c_str());
    return false;
}

int main(int argc, char** argv) {
    int frames = 600; const char* shotPrefix = "shot";
    std::vector<std::string> paths; std::vector<std::pair<int, WORD>> keys; // frame -> key toggle
    std::vector<std::pair<int, std::string>> clicks; // frame -> text of a drawn string to click
    bool helmet = false, crash = false;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--frames")) frames = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--shot")) shotPrefix = argv[++i];
        else if (!strcmp(argv[i], "--helmet")) helmet = true;
        else if (!strcmp(argv[i], "--crash")) crash = true;
        else if (!strcmp(argv[i], "--key")) { int fr = atoi(argv[++i]); WORD vk = (WORD)strtol(argv[++i], nullptr, 0); keys.push_back({fr, vk}); }
        else if (!strcmp(argv[i], "--click")) { int fr = atoi(argv[++i]); clicks.push_back({fr, argv[++i]}); }
        else paths.push_back(argv[i]);
    }
    char exe[MAX_PATH]; GetModuleFileNameA(nullptr, exe, MAX_PATH);
    LOG("host: %s\n", exe);

    WNDCLASSA wc = {}; wc.lpfnWndProc = wndproc; wc.hInstance = GetModuleHandleA(nullptr); wc.lpszClassName = "MXB_TEST"; wc.style = CS_OWNDC;
    RegisterClassA(&wc);
    const int W = 1280, H = 720;
    HWND hwnd = CreateWindowA("MXB_TEST", GAME_NAME " (test host)", WS_POPUP | WS_VISIBLE, 0, 0, W, H, nullptr, nullptr, wc.hInstance, nullptr);
    HDC dc = GetDC(hwnd);
    PIXELFORMATDESCRIPTOR pfd = {}; pfd.nSize = sizeof(pfd); pfd.nVersion = 1;
    pfd.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER; pfd.iPixelType = PFD_TYPE_RGBA;
    pfd.cColorBits = 32; pfd.cDepthBits = 24; pfd.cStencilBits = 8;
    SetPixelFormat(dc, ChoosePixelFormat(dc, &pfd), &pfd);
    HGLRC rc = wglCreateContext(dc); wglMakeCurrent(dc, rc);
    SetForegroundWindow(hwnd); SetFocus(hwnd);
    LOG("GL: %s | %s | %s\n", glGetString(GL_VENDOR), glGetString(GL_RENDERER), glGetString(GL_VERSION));
    g_glDrawRangeElements = (PFN_DRE)wglGetProcAddress("glDrawRangeElements"); g_realDre = (void*)((uintptr_t)g_glDrawRangeElements ^ 0x5A5A5A5A5A5A5A5AULL);
    build_scene(); direct_init();
    report_slots("before plugins");

    std::vector<Plugin> pl;
    for (auto& p : paths) {
        Plugin x; x.path = p;
        x.mod = LoadLibraryA(p.c_str());
        if (!x.mod) { LOG("LoadLibrary(%s) failed: %lu\n", p.c_str(), GetLastError()); continue; }
#define GP(n) x.n = (decltype(x.n))GetProcAddress(x.mod, #n)
        GP(GetModID); GP(Startup); GP(Shutdown); GP(RunStart); GP(RunStop); GP(RunDeinit); GP(EventDeinit);
        GP(EventInit); GP(RunInit); GP(RaceVehicleData); GP(RunTelemetry); GP(RaceTrackPosition); GP(VictimReport);
        GP(DrawInit); GP(Draw);
        LOG("loaded %s (mod id '%s')\n", p.c_str(), x.GetModID ? x.GetModID() : "?");
        pl.push_back(x);
    }
    char save[MAX_PATH]; strcpy(save, exe); *strrchr(save, '\\') = 0; strcat(save, "\\save\\"); CreateDirectoryA(save, nullptr);
    for (auto& x : pl) if (x.Startup) LOG("Startup(%s) -> %d\n", x.path.c_str(), x.Startup(save));
    report_slots("after Startup");
    for (auto& x : pl) {
        if (!x.DrawInit) continue;
        int ns = 0, nf = 0; char* sp = nullptr; char* fn = nullptr;
        int r = x.DrawInit(&ns, &sp, &nf, &fn);
        LOG("DrawInit(%s) -> %d, %d sprites, %d fonts\n", x.path.c_str(), r, ns, nf);
        for (int i = 0; r == 0 && sp && i < ns; ++i) { LOG("  sprite %s\n", sp); sp += strlen(sp) + 1; }
        for (int i = 0; r == 0 && fn && i < nf; ++i) { LOG("  font %s\n", fn); fn += strlen(fn) + 1; }
        if (r != 0) x.Draw = nullptr;
    }

    SPluginsBikeEvent_t ev = {};
    strcpy(ev.m_szRiderName, "Test Rider"); strcpy(ev.m_szBikeID, "ktm_450sxf_2024"); strcpy(ev.m_szBikeName, "KTM 450 SX-F");
    ev.m_iNumberOfGears = 5; ev.m_iMaxRPM = 13000; ev.m_iLimiter = 12500; ev.m_iShiftRPM = 11500; ev.m_fMaxFuel = 6.3f;
    ev.m_afSuspMaxTravel[0] = 0.31f; ev.m_afSuspMaxTravel[1] = 0.31f; ev.m_fSteerLock = 38;
    strcpy(ev.m_szCategory, "MX1"); strcpy(ev.m_szTrackID, "test_track"); strcpy(ev.m_szTrackName, "Test Track");
    ev.m_fTrackLength = 1500; ev.m_iType = 1;
    for (auto& x : pl) if (x.EventInit) x.EventInit(&ev, sizeof(ev));
    SPluginsBikeSession_t ss = {}; ss.m_iSession = 1; ss.m_fAirTemperature = 22;
    for (auto& x : pl) if (x.RunInit) x.RunInit(&ss, sizeof(ss));
    for (auto& x : pl) if (x.RunStart) x.RunStart();

    LARGE_INTEGER fq, t0, tn; QueryPerformanceFrequency(&fq); QueryPerformanceCounter(&t0);
    double worst = 0, total = 0;
    for (int fr = 0; fr < frames; ++fr) {
        MSG msg; while (PeekMessageA(&msg, nullptr, 0, 0, PM_REMOVE)) { TranslateMessage(&msg); DispatchMessageA(&msg); }
        for (auto& k : keys) { if (k.first == fr) tap_key(k.second, true); if (k.first + 3 == fr) tap_key(k.second, false); }
        for (auto& c : clicks) { if (c.first == fr && point_at(pl, c.second, hwnd, W, H)) tap_mouse(true); if (c.first + 3 == fr) tap_mouse(false); }
        LARGE_INTEGER a; QueryPerformanceCounter(&a);
        float t = fr / 60.0f;
        float R = 40, w = 15.0f / R, ang = w * t;
        float bx = R * sinf(ang), bz = R * cosf(ang) - R, yaw = ang + 1.5708f;
        SPluginsBikeData_t d = {};
        d.m_iRPM = 8000 + (int)(2000 * sinf(t * 3)); d.m_iGear = 3; d.m_fFuel = 5; d.m_fSpeedometer = 15;
        d.m_fEngineTemperature = 80; d.m_fWaterTemperature = 75;
        d.m_fPosX = bx; d.m_fPosY = 0.6f * sinf(bx * 0.15f) * cosf(bz * 0.11f); d.m_fPosZ = bz;
        d.m_fVelocityX = 15 * cosf(ang); d.m_fVelocityZ = -15 * sinf(ang);
        d.m_fAccelerationX = 15 * w / 9.81f; d.m_fAccelerationY = 1.0f + 0.3f * sinf(t * 9); d.m_fAccelerationZ = 0.1f * sinf(t);
        float cy = cosf(yaw), sy = sinf(yaw);
        float rot[3][3] = {{cy, 0, -sy}, {0, 1, 0}, {sy, 0, cy}}; memcpy(d.m_aafRot, rot, sizeof(rot));
        d.m_fYaw = fmodf(yaw * 57.2958f + 180, 360) - 180; d.m_fRoll = -20; d.m_fYawVelocity = w * 57.2958f;
        d.m_afSuspLength[0] = d.m_afSuspLength[1] = 0.2f + 0.02f * sinf(t * 11);
        d.m_iCrashed = (crash && fr > frames / 2) ? 1 : 0;
        d.m_fThrottle = 0.7f; d.m_afWheelSpeed[0] = 15; d.m_afWheelSpeed[1] = 15.5f;
        d.m_aiWheelMaterial[0] = d.m_aiWheelMaterial[1] = 1;
#ifdef GPB
        // GP Bikes: hard braking with the front wheel slowing for a moment, so brake and slip code runs too.
        if (fr > frames * 6 / 10 && fr < frames * 7 / 10) { d.m_fThrottle = 0; d.m_fFrontBrake = 1; d.m_afWheelSpeed[0] = 10; }
#endif
        for (auto& x : pl) if (x.RunTelemetry) x.RunTelemetry(&d, sizeof(d), t, fmodf(t / 100, 1));
        SPluginsRaceTrackPosition_t tp[3] = {};
        for (int i = 0; i < 3; ++i) { float a2 = ang - 0.3f * i; tp[i].m_iRaceNum = i + 1; tp[i].m_fPosX = R * sinf(a2); tp[i].m_fPosZ = R * cosf(a2) - R; tp[i].m_fYaw = (a2 + 1.5708f) * 57.2958f; }
        for (auto& x : pl) if (x.RaceTrackPosition) x.RaceTrackPosition(3, tp, sizeof(SPluginsRaceTrackPosition_t));
        for (int i = 0; i < 3; ++i) {
            SPluginsRaceVehicleData_t vd = {}; vd.m_iRaceNum = i + 1; vd.m_iActive = 1; vd.m_iRPM = 9000; vd.m_iGear = 3; vd.m_fSpeedometer = 15; vd.m_fThrottle = 0.7f; vd.m_fLean = -20;
            for (auto& x : pl) if (x.RaceVehicleData) x.RaceVehicleData(&vd, sizeof(vd));
        }
        draw_frame(W, H, t, bx, bz, yaw, helmet);
        draw_api(pl);
        bool shoot = (fr == frames / 4) || (fr == frames / 2 + 30) || (fr == frames - 2);
        for (auto& k : keys) if (fr == k.first + 20) shoot = true;
        if (shoot) { char sp[MAX_PATH]; snprintf(sp, sizeof(sp), "%s_%04d.bmp", shotPrefix, fr); save_bmp(sp, W, H); }
        SwapBuffers(dc);
        QueryPerformanceCounter(&tn);
        double ms = (tn.QuadPart - a.QuadPart) * 1000.0 / fq.QuadPart; total += ms; if (ms > worst) worst = ms;
    }
    LOG("direct HUD draw saw viewport %d,%d %dx%d, draw FBO %d\n", g_lastVp[0], g_lastVp[1], g_lastVp[2], g_lastVp[3], g_lastFbo);
    LOG("frames %d, avg %.2f ms, worst %.2f ms\n", frames, total / frames, worst);
    report_slots("after frames");
    for (auto& x : pl) if (x.VictimReport) x.VictimReport();
    for (auto& x : pl) if (x.RunStop) x.RunStop();
    for (auto& x : pl) if (x.RunDeinit) x.RunDeinit();
    for (auto& x : pl) if (x.EventDeinit) x.EventDeinit();
    for (auto& x : pl) if (x.Shutdown) x.Shutdown();
    for (auto it = pl.rbegin(); it != pl.rend(); ++it) { LOG("FreeLibrary %s\n", it->path.c_str()); FreeLibrary(it->mod); }
    report_slots("after unload");
    wglMakeCurrent(nullptr, nullptr); wglDeleteContext(rc); ReleaseDC(hwnd, dc); DestroyWindow(hwnd);
    LOG("host: clean exit\n");
    return 0;
}
