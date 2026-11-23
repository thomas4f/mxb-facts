$ pdftotext -layout MaxHUD.pdf - | grep -nE 'credit|thanks|CAPS-LOCK|MaxHUD.ini|renamed|Documents|XInput|rumble_crashed|xinput_device|Logging|log was never|MX Bikes|vc_redist|MaxStopRumble|licen|Licen|donat|Donat'
3:MaXHUD has been inspired by the great AdvancedHUD by random: I credit random for his
9:                    Kart Racing Pro             MX Bikes beta18
19:   ●   MaxHUD_MXB64.dlo                : plugin for MX Bikes
28:    ● C:\Program Files\MX Bikes\plugins
30:The plugin creates a MaxHUD.ini file in the data directory corresponding to the game:
31:    ● C:\Users\<Your Windows Username>\Documents\PiBoSo\GP Bikes\
32:    ● C:\Users\<Your Windows Username>\Documents\PiBoSo\World Racing Series\
33:    ● C:\Users\<Your Windows Username>\Documents\PiBoSo\Kart Racing Pro\
34:    ● C:\Users\<Your Windows Username>\Documents\PiBoSo\MX Bikes\
38:     ● your existing MaxHUD.ini file MAY be replaced by a new one with default values. All the
40:        be kept, renamed to MaxHUD.ini.20130413_223000 (current date and time).
45:                   https://aka.ms/vs/16/release/vc_redist.x64.exe
63:When on the track, pressing CAPS-LOCK will show a menu that will allow to:
85:happens): your old MaxHUD.ini file will be renamed to MaxHUD.ini.YYYYMMDD-hhmmss.
115:helmet (thanks to TheFatController) GPB, KRP and WRS
116:use the same helmet (thanks to Juju).
358:         one you use: typically, the joypad you use in its XInput variant.
404:Enables rumble on rumble-capable XInput devices. Rumble can be driven by different
423:   ●   xinput_device: cycles through the possible XInput devices. You have to select the
425:   ●   rumble_crashed: 0/1 to avoid/allow rumble when vehicle is crashed.
586:     ●    Now working for MX Bikes too (no changes for other versions).
598:     ●    New helmet for MXB, thanks to TheFatController.
610:     ●    Added HUDRumble to enable rumble on XInput devices.
615:     ●    Improved handling of settings file (MaxHUD.ini): sorry, but it will overwrite your current one (will have to re-configure
616:          everything). In the future, it will happen less often thanks to the improvements in this release.
617:     ●    Logging to MaxHUD.log is always now on (tiny file, no impact).
621:     ●    Fix bug: MaxHUD.log was never erased (hence growing over time). Now it’s erased at startup.
622:     ●    Fix bug: starting the game and exiting right after (i.e. without going to track) was messing up the MaxHUD.ini file (possible
735:     ●    Files renamed to:
743:     ●    Files renamed to:
754:     ●    Try to prevent rumble staying on in some conditions (thanks to TFC for reporting).
819:         associate the right XInput device).
(exit 0)
