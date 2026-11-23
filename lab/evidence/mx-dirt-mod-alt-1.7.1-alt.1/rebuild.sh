#!/usr/bin/env bash
# The rebuild (T4), run by run.sh in the release folder: Zig 0.13.0 (pinned by SHA-256), the zig commands of build.ps1
# and build_render.ps1 on Linux, then pe_cmp.py, which names every byte range where a rebuilt file differs from the release's.
set -eu
D=$PWD
cd "$W"
curl -sSfL -o zig.tar.xz https://ziglang.org/download/0.13.0/zig-linux-x86_64-0.13.0.tar.xz
echo 'd45312e61ebcc48032b77bc4cf7fd6915c11fa16e4aad116b66c9468211230ea  zig.tar.xz' | sha256sum -c
tar xf zig.tar.xz; Z="$W/zig-linux-x86_64-0.13.0/zig"; echo "zig $($Z version)"
cp -r "$SRC" src; cd src
export ZIG_GLOBAL_CACHE_DIR="$W/gc" ZIG_LOCAL_CACHE_DIR="$W/lc"
F='-shared -target x86_64-windows-gnu -std=c11 -O2 -msse2 -Wall -Wextra -Werror -ffp-contract=off -fno-fast-math -fms-extensions'
C=src/core; Q=src/render
$Z cc $F -I $C -I src/shared $C/mx_dirt.c $C/mxdirt_session.c $C/mxdirt_contact.c $C/mxdirt_wheel_sample.c \
  $C/mxdirt_frame_snapshot.c $C/mxdirt_height_field.c $C/mxdirt_height_publication.c $C/mxdirt_publication_hooks.c \
  $C/mxdirt_transport.c $C/mxdirt_native_height.c $C/mxdirt_patches.c -luser32 -ladvapi32 -o "$W/mx_dirt.dll"
$Z cc $F -I src/shared -I $Q $Q/mxdirt_render_host.c $Q/mxdirt_render_content.c $Q/mxdirt_terrain_scope.c $Q/mxdirt_dirt.c \
  $Q/mxdirt_dirt_gl.c -lopengl32 -lgdi32 -luser32 -lbcrypt -o "$W/mx_dirt_render.dll"
cd "$D"
sha256sum plugins/mx_dirt.dlo "$W/mx_dirt.dll" plugins/mx_dirt_render.dlo "$W/mx_dirt_render.dll" | sed "s#$W#\$W#"
echo '-- plugins/mx_dirt.dlo vs the rebuild:'; pe_cmp.py plugins/mx_dirt.dlo "$W/mx_dirt.dll"
echo '-- plugins/mx_dirt_render.dlo vs the rebuild:'; pe_cmp.py plugins/mx_dirt_render.dlo "$W/mx_dirt_render.dll"
