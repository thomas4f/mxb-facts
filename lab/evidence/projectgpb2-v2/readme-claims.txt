$ grep -nE 'Copy the|plugins\\|F6|F9|Ctrl\+F9|default F8|Settings are saved|off by default|read from the game|gfx.cfg|exhaustsmoke|ReShade|VR|UNINSTALL|Delete the three|ProjGPB2.log|free|link to the download|CC BY|Wikimedia' README.txt; echo '== CREDITS.txt'; cat CREDITS.txt
10:2. Copy the "plugins" folder inside "gpbikes" from this zip into your GP Bikes
14:     plugins\ProjectGPB2_core64.dlo   graphics + the menu
15:     plugins\ProjectGPB2_cam64.dlo    rider POV camera
16:     plugins\ProjectGPB2_fx64.dlo     backfires, smoke, heat haze, dust, weather
17:     plugins\ProjGPB2\                shaders, sounds, settings, log
18:     plugins\presets\                 graphics presets
21:ReShade: if you use ReShade (an opengl32.dll next to core.exe), turn it off
25:F6          the ProjectGPB2 menu (open / close + save) - change it in MENU AND PRESETS
26:F9          graphics on / off (compare with the normal game)
27:Ctrl+F9     reload settings
41:Settings are saved to plugins\ProjGPB2\ProjGPB2.ini.
51:  read from the game's own exhaust data.
53:  the bike's gfx.cfg (its pipes and smoke top_rpm / max_rpm) and from
54:  effects\particles\exhaustsmoke.cfg. Strongest around top_rpm, gone by max_rpm,
63:- Pipe position: by default the pipes come from the bike's own gfx.cfg. For
64:  bikes packed in a .pkz (no gfx.cfg to read) use the Height / Forward / Side
101:v4.0 - Release check. Exhaust effects, headlight and brake light are now off by default
136:v2.3 - Screenshots: a key of your choice (default F8) saves exactly what you see - every effect,
144:v1.8 - Paused replay: flames, sparks and smoke freeze in place.
153:       riders and the dash alone. Head motion only in first person, 30 % gentler. VR (-vrs):
170:       alone, helmet-view blur fixed at full lean, brake light off by default.
189:- F9 compares with the normal game.
190:- plugins\ProjGPB2\ProjGPB2.log and gamefx.log say what happened.
192:UNINSTALL
193:Delete the three ProjectGPB2_*.dlo files (and the ProjGPB2 folder).
196:ProjectGPB2 is free. Please link to the download page instead of re-uploading it.
197:Heavy rain sound: "Calm rain.wav" by Zuvji, Wikimedia Commons (CC BY-SA 4.0)
198:Light rain sound: "Falling Rain SFX 1" by valvalion, Wikimedia Commons (CC BY 3.0)
== CREDITS.txt
Rain sounds (Graphics Overhaul)

rain_heavy.wav - from "Calm rain.wav" by Zuvji (Wikimedia Commons)
https://commons.wikimedia.org/wiki/File:Calm_rain.wav
License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
Changes: a 30 s stretch cut into a seamless loop, level matched, loud drop hits limited,
32 kHz. This loop is shared under the same license.

rain_light.wav - from "Falling Rain SFX 1 2016-11-19" by valvalion (Wikimedia Commons)
https://commons.wikimedia.org/wiki/File:Falling_Rain_SFX_1_2016-11-19.oga
License: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/)
Changes: a 30 s stretch cut into a seamless loop, level matched, 32 kHz.
(exit 0)
