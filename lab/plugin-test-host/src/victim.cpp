// A bystander plugin that keeps OpenGL function pointers in a global table, like many plugins do.
#include <windows.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstdint>
static const char* kNames[] = {"glOrtho", "glFrustum", "glLoadIdentity", "glDrawElements", "glViewport", "glScissor", "glReadPixels", "glBegin"};
static void* g_tbl[8];
static void* g_real[8];
// filled when the DLL loads (before any plugin Startup), like a static GL loader
static struct Init { Init() { HMODULE gl = LoadLibraryA("opengl32.dll"); for (int i = 0; i < 8; ++i) { g_tbl[i] = (void*)GetProcAddress(gl, kNames[i]); g_real[i] = (void*)((uintptr_t)g_tbl[i] ^ 0x5A5A5A5A5A5A5A5AULL); } } } s_init;
extern "C" {
__declspec(dllexport) char* GetModID() { static char id[] = "victim"; return id; }
__declspec(dllexport) int GetModDataVersion() { return 8; }
__declspec(dllexport) int GetInterfaceVersion() { return 9; }
__declspec(dllexport) int Startup(char*) { return -1; }
extern void* __imp_glOrtho; extern void* __imp_glBegin; extern void* __imp_glViewport; extern void* __imp_SwapBuffers;
__declspec(dllexport) void VictimDrawSomething() { glViewport(0, 0, 1, 1); glOrtho(0, 1, 1, 0, -1, 1); glBegin(GL_POINTS); glEnd(); }
static void imp(const char* n, void* cur, const char* dll) {
    void* real = (void*)GetProcAddress(GetModuleHandleA(dll), n);
    static char buf[MAX_PATH]; const char* who = "untouched";
    if (cur != real) { HMODULE m = nullptr; GetModuleHandleExA(6, (LPCSTR)cur, &m); GetModuleFileNameA(m, buf, sizeof(buf)); who = buf; }
    printf("  import %-10s %s%s\n", n, cur != real ? "REDIRECTED to " : "", who);
}
__declspec(dllexport) void VictimReport() {
    printf("== bystander plugin (victim.dlo) import table\n");
    imp("glOrtho", __imp_glOrtho, "opengl32"); imp("glBegin", __imp_glBegin, "opengl32"); imp("glViewport", __imp_glViewport, "opengl32");
    printf("== bystander plugin (victim.dlo) pointer table\n");
    for (int i = 0; i < 8; ++i) {
        const char* who = "untouched";
        static char buf[MAX_PATH];
        if (g_tbl[i] != (void*)((uintptr_t)g_real[i] ^ 0x5A5A5A5A5A5A5A5AULL)) {
            HMODULE m = nullptr;
            GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)g_tbl[i], &m);
            GetModuleFileNameA(m, buf, sizeof(buf)); who = buf;
        }
        printf("  %-16s %s%s\n", kNames[i], g_tbl[i] != (void*)((uintptr_t)g_real[i] ^ 0x5A5A5A5A5A5A5A5AULL) ? "REDIRECTED to " : "", who);
    }
    fflush(stdout);
}
}
