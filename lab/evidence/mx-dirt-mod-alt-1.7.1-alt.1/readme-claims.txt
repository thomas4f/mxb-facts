$ grep -nE 'SUPPORTED_EXE|se apaga solo|stays inactive|switch|memoria del juego|game.s memory|reverse engineering|Online|online|launcher|Install.cmd|backup|Nothing is ever deleted|Zig' README.txt SUPPORTED_EXE.txt | cut -c1-260
README.txt:32:| **Menú en el juego (F8)** | Reemplaza al launcher de PowerShell. 5 pestañas (Física, Visual, Pista, Presets, Overhaul), teclado **y mouse**, cambios en vivo, **español e inglés**. | Ajustar sin salir del juego. |
README.txt:40:| **Cubiertas reales por moto** | Ancho de cada cubierta leído de la **memoria del juego** (motos OEM cifradas) o de sus `.tyre` (motos descomprimidas); radio real de cada rueda. | Antes todo era 11/15 cm y 0,33/0,35 m fijos. |
README.txt:86:**Requisitos:** Windows 10/11 64 bits, **MX Bikes de Steam, build 23566986** (el hash exacto está en `SUPPORTED_EXE.txt`; con otra versión el mod se apaga solo y el juego anda normal), OpenGL 4.
README.txt:90:3. Doble clic en **`Install.cmd`**. Hace backup de todo lo que reemplaza en `Documents\PiBoSo\MX Bikes\mx_dirt_mod_backups`.
README.txt:185:- **Online** sigue siendo experimental, como en el original.
README.txt:189:Necesitás [Zig](https://ziglang.org/) 0.13 o más nuevo.
README.txt:227:| **In-game menu (F8)** | Replaces the PowerShell launcher. 5 tabs (Physics, Look, Track, Presets, Overhaul), keyboard **and mouse**, live changes, **Spanish and English**. | Tune without leaving the game. |
README.txt:235:| **Each bike's real tyres** | Each tyre's width read from the **game's memory** (encrypted OEM bikes) or from its `.tyre` (unpacked bikes); each wheel's real radius. | It was a fixed 11/15 cm and 0.33/0.35 m. |
README.txt:236:| **Official telemetry** | The rider's brakes widen the braking-bump rows; a crashed bike digs nothing. Self-verified before use. | Official API data, no reverse engineering. |
README.txt:238:| **Graphics Overhaul compatibility** | The renderer chains onto Overhaul's OpenGL hooks instead of switching off, and re-hooks on the next load. | With Overhaul installed the renderer drew nothing. |
README.txt:281:**Requirements:** Windows 10/11 64-bit, **MX Bikes from Steam, build 23566986** (exact hash in `SUPPORTED_EXE.txt`; with any other version the mod switches itself off and the game runs normally), OpenGL 4.
README.txt:285:3. Double-click **`Install.cmd`**. Everything it replaces is backed up to `Documents\PiBoSo\MX Bikes\mx_dirt_mod_backups`.
README.txt:305:| **Tab** / Shift+Tab, click a tab | switch tab |
README.txt:380:- **Online** is still experimental, as in the original.
README.txt:384:You need [Zig](https://ziglang.org/) 0.13 or newer.
SUPPORTED_EXE.txt:4:version it stays inactive and the game runs normally until a new release supports it.
(exit 0)
