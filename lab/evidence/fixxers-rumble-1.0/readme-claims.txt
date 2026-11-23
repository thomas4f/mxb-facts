$ grep -nE 'Version|Ctrl|SAVE|Settings live|falls back|crash|XInput|Credits|SDK' 'READ ME.md'
3:A controller rumble plugin for GP Bikes that uses live bike telemetry to drive XInput-compatible controllers in real time. Fully configurable in-game, allowing each user to fine-tune feedback to their preference or share custom profiles with friends.
11:Version: V1.0
27:While on track, press **Ctrl + R** to open the settings panel.
34:Click **SAVE** to write the file to disk. Settings persist between sessions.
36:Press **Ctrl + R** again to close the panel.
54:When you crash, all rumble cuts immediately.
62:> Note: XInput's left motor is physically a heavy / low-frequency motor and the right is a buzzy / high-frequency motor. Inverting swaps which **grip** each rumble appears on, but the physical character of the motors doesn't move with it — that's a fixed XInput limitation, not a bug.
68:Settings live in:
91:If the file is missing or any value is malformed, the plugin silently falls back to defaults (everything enabled, intensity 1.0, no inversion). Friends who send you a corrupt file won't break your install.
97:- **Native support**: anything that speaks **XInput** — Xbox 360, Xbox One, Xbox Series, and most third-party gamepads marketed as "PC-compatible".
99:- **Wheels with Force Feedback**: not supported — XInput's two-motor model doesn't translate to FFB.
105:- If you don't feel any rumble: check that your controller is actually visible to XInput. Steam Input must be enabled for GP Bikes if you're on a PS pad. An exotic non-XInput pad won't be seen.
112:## Credits
114:Plugin by **FIXXER 1001**. Built on the GP Bikes plugin SDK.
(exit 0)
