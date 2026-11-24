#!/usr/bin/env bash
# MX Bikes Setup Duper 0.1.8674.29660 (no licence found; source public at 2e030e0873b043e5eab485ce9902761f999b9edf, tag
# 0.1.8674.29660).
# Usage: run.sh <release folder> <source checkout at 2e030e0>
# The release folder holds the one file of the GitHub release 0.1.8674.29660
# (https://github.com/dmkrtz/MXBikesSetupDuperWPF/releases/tag/0.1.8674.29660): MX_Bikes_Setup_Duper.exe, a .NET 6
# single-file program. This script lists and unpacks its bundle into app/ with ../netbundle.py, without running anything.
# nuget-libs, apphost and rebuild download from nuget.org and dot.net (pinned by SHA-256 where the file doesn't change),
# so they need the network, and so do release-page; rebuild installs the .NET SDK 7.0.302 into the scratch folder and
# builds the source there for Windows (EnableWindowsTargeting), which works on Linux.
. "$(dirname "$0")/../ev.sh"
: "${SRC:?give the source checkout as the second argument}"
E="$(cd "$OUT/.." && pwd)"; export E R
X=MX_Bikes_Setup_Duper.exe
C=MXBikesSetupDuperWPF/MainWindow.xaml.cs
ev files "sha256sum $X"
# The bundle: every file packed in the program, with its offset, size, type and SHA-256.
ev bundle "rm -rf app; python3 -I \"\$E/netbundle.py\" $X app"
ev file "file $X app/MX_Bikes_Setup_Duper.dll app/ModernWpf.dll app/ModernWpf.Controls.dll app/Newtonsoft.Json.dll app/de-DE/ModernWpf.resources.dll; file app/*/*.dll | grep -c 'Mono/.Net assembly'; cat app/MX_Bikes_Setup_Duper.runtimeconfig.json"
# Code signing: the Security (certificate) directory of the program.
ev signature "objdump -p $X | grep -E 'file format|Security Directory'"
# The libraries packed in the program are the files of the NuGet packages ModernWpfUI 0.9.6 and Newtonsoft.Json 13.0.3
# (lib/net5.0-windows7.0 and lib/net6.0), byte for byte, the 124 language files included.
ev nuget-libs "cd \"\$W\" && curl -sSL -o m.nupkg https://api.nuget.org/v3-flatcontainer/modernwpfui/0.9.6/modernwpfui.0.9.6.nupkg && curl -sSL -o n.nupkg https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg && printf '%s  m.nupkg\n%s  n.nupkg\n' 776b93df90c50547f82035fa7259b3b7162b9a9712b2485b30d16bf53686cb1d 872fc189e638ab1056555b03aaa38f68bcb54286e221aa646eb1129babf63c77 | sha256sum -c && mkdir m n && (cd m && unzip -q ../m.nupkg) && (cd n && unzip -q ../n.nupkg) && cd \"\$R/app\" && same=0; diff=0; for f in \$(find . -name 'ModernWpf*.dll' | sort); do if cmp -s \"\$f\" \"\$W/m/lib/net5.0-windows7.0/\$f\"; then same=\$((same+1)); else echo \"DIFFERENT: \$f\"; diff=\$((diff+1)); fi; done; cmp Newtonsoft.Json.dll \"\$W/n/lib/net6.0/Newtonsoft.Json.dll\" && same=\$((same+1)); echo \"\$same files the same as the packages, \$diff different\"; grep -E '<license|<projectUrl|<repository' \"\$W\"/m/*.nuspec \"\$W\"/n/*.nuspec | sed \"s#\$W#\\\$W#g\""
# The program's host code is .NET 6.0.16's apphost.exe (NuGet package Microsoft.NETCore.App.Host.win-x64 6.0.16): the same
# sections, but for the two fields the SDK fills in, and the resources it copies from the app's assembly.
ev apphost "cd \"\$W\" && curl -sSL -o h.nupkg https://api.nuget.org/v3-flatcontainer/microsoft.netcore.app.host.win-x64/6.0.16/microsoft.netcore.app.host.win-x64.6.0.16.nupkg && echo '330a4bf23d9c4aa8ab3dc5ae3af563d880461e00952ad153e679612decf6663b  h.nupkg' | sha256sum -c && unzip -q -o h.nupkg runtimes/win-x64/native/apphost.exe && cd \"\$R\" && python3 -I \"\$E/apphost_cmp.py\" \"\$W/runtimes/win-x64/native/apphost.exe\" $X"
# The program's resources (icon, version, manifest) are the app assembly's, and its icon is the source's mxbsd.ico.
ev rsrc "python3 -I \"\$E/rsrc.py\" $X \"\$SRC/MXBikesSetupDuperWPF/mxbsd.ico\"; echo '- the app assembly:'; python3 -I \"\$E/rsrc.py\" app/MX_Bikes_Setup_Duper.dll"
# The rebuild: the source at the commit, published as the release was (Release, win-x64, one file, framework-dependent)
# with the .NET SDK 7.0.302, whose WPF build tasks (7.0.5) the release names. Then the two bundles' files are compared:
# every library the same, the two JSON files the same but for Windows line ends (CRLF), and the app assembly the same
# byte for byte but for its per-build fields (../dotnet_cmp.py), given the release's version 0.1.8674.29660 (0.1.* in the
# project: the build's date and time); then the two programs section by section: the same host code (../apphost_cmp.py).
ev rebuild "cd \"\$W\" && curl -sSL -o dotnet-install.sh https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0.302 --install-dir \"\$W/dotnet\" >/dev/null 2>&1 && mkdir b && (cd \"\$SRC\" && git archive 2e030e0873b043e5eab485ce9902761f999b9edf) | tar -x -C b && cd b && DOTNET_ROOT=\"\$W/dotnet\" DOTNET_CLI_TELEMETRY_OPTOUT=1 NUGET_PACKAGES=\"\$W/nuget\" \"\$W/dotnet/dotnet\" publish MXBikesSetupDuperWPF/MXBikesSetupDuperWPF.csproj -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -p:EnableWindowsTargeting=true -o \"\$W/out\" 2>&1 | grep -E ' error |->' | sed \"s#\$W#\\\$W#g\"; cd \"\$R\" && python3 -I \"\$E/netbundle.py\" \"\$W/out/$X\" \"\$W/reb\" | awk 'NR>1{print \$5, \$6}' > \"\$W/reb.txt\"; python3 -I \"\$E/netbundle.py\" $X | awk 'NR>1{print \$5, \$6}' > \"\$W/rel.txt\"; echo '- packed files whose SHA-256 differs (release, then rebuild):'; diff \"\$W/rel.txt\" \"\$W/reb.txt\"; echo \"- \$(wc -l < \"\$W/rel.txt\") files in the release, \$(wc -l < \"\$W/reb.txt\") in the rebuild, \$(comm -12 <(sort \"\$W/rel.txt\") <(sort \"\$W/reb.txt\") | wc -l) the same\"; for j in deps runtimeconfig; do if [ \"\$(tr -d '\\r' < app/MX_Bikes_Setup_Duper.\$j.json | sha256sum)\" = \"\$(sha256sum < \"\$W/reb/MX_Bikes_Setup_Duper.\$j.json\")\" ]; then echo \"same but CRLF: MX_Bikes_Setup_Duper.\$j.json\"; else echo \"DIFFERENT: MX_Bikes_Setup_Duper.\$j.json\"; fi; done; echo '- MX_Bikes_Setup_Duper.dll:'; python3 -I \"\$E/dotnet_cmp.py\" app/MX_Bikes_Setup_Duper.dll \"\$W/reb/MX_Bikes_Setup_Duper.dll\" 0.1.8674.29660; echo '- the two programs, section by section (a build on Linux adds no .rsrc):'; python3 -I \"\$E/apphost_cmp.py\" \"\$W/out/$X\" $X"
# Every file in the repository at the commit, with its type: no prebuilt program file (code, XAML, images, an icon).
ev repo-files "cd \"\$SRC\" && git ls-tree -r --name-only 2e030e0873b043e5eab485ce9902761f999b9edf | while read f; do printf '%s: %s\n' \"\$f\" \"\$(git show 2e030e0873b043e5eab485ce9902761f999b9edf:\"\$f\" | file -b -)\"; done"
# The source's internet and browser code: one HttpClient request to GitHub's API for the latest release, and two
# Process.Start calls that open GitHub pages in your browser.
ev src-network "cd \"\$SRC\" && grep -nE 'Http|https?://|User-Agent|Process\\.Start|WebClient|Socket|Dns' $C MXBikesSetupDuperWPF/MainWindow.xaml MXBikesSetupDuperWPF/App.xaml.cs"
# Every place the source writes, copies, moves or deletes a file or folder.
ev src-files "cd \"\$SRC\" && grep -nE 'File\\.(Copy|Move|Delete|Write|Create|Replace|Open|AppendAll)|Directory\\.(CreateDirectory|Delete|Move)|WritePrivateProfileString|StreamWriter|FileStream|\\.Write\\(' $C"
# What it reads: global.ini (the mods folder), the folder names in the mods folder's tracks, the profiles, and the
# setups (.stp) of the profile you pick: names and dates, not their contents.
ev src-reads "cd \"\$SRC\" && grep -nE 'MyDocuments|global\\.ini|GetDirectories|GetFiles|EnumerateDirectories|GetCreationTime|GetLastWriteTime|ReadAll|GetPrivateProfileString|IniFile\\(' $C"
# What it would need to change the registry, start with Windows, open other processes, read or press keys outside its
# window, or change the game: none. Its only native calls are Windows' two .ini functions.
ev src-absent "cd \"\$SRC\" && grep -rnE 'Registry|HKEY|CurrentVersion|Startup|OpenProcess|GetProcesses|WriteProcessMemory|ReadProcessMemory|VirtualProtect|CreateRemoteThread|SetWindowsHookEx|GetAsyncKeyState|keybd_event|SendInput|mxbikes|DllImport|LoadLibrary|Assembly\\.Load|Environment\\.SetEnvironment' MXBikesSetupDuperWPF"
# The update check: when the window opens it compares its own version with the tag of the latest GitHub release; a newer
# one shows \"Update available!\" and a Get latest version button that opens the release page.
ev src-update "cd \"\$SRC\" && sed -n '27,63p;134,164p;231,234p' $C"
# Shop, payment and donation words in the source and the window.
ev strings-money "cd \"\$SRC\" && grep -rniIE 'donat|paypal|ko-?fi|patreon|premium|price|buy|licen[cs]e key|unlock|subscri|discord|shop' MXBikesSetupDuperWPF; echo '- in the app assembly:'; cd \"\$R\" && { strings -n 6 app/MX_Bikes_Setup_Duper.dll; strings -el -n 6 app/MX_Bikes_Setup_Duper.dll; } | grep -iE 'https?://|donat|paypal|ko-?fi|patreon|premium|shop|buy '"
# Credits and licence texts: none in the repository at the commit, none packed in the program.
ev thirdparty "cd \"\$SRC\" && echo '- repository at the commit:'; git ls-tree -r --name-only 2e030e0873b043e5eab485ce9902761f999b9edf | grep -iE 'licen|copying|notice|credit|third|readme'; echo '- packed in the program:'; cd \"\$R\" && find app -type f | grep -viE '\\.dll\$|\\.json\$'; grep -rniE 'ModernWpf|Newtonsoft|licen|credit' \"\$SRC/MXBikesSetupDuperWPF/MainWindow.xaml\""
# Dependencies: the project names two NuGet packages at one version each and no lock file; the SDK isn't named (no
# global.json); the release's assembly names the WPF build tasks it was built with (7.0.5, from the SDK 7.0.302).
ev deps "cd \"\$SRC\" && grep -nE 'PackageReference|TargetFramework' MXBikesSetupDuperWPF/MXBikesSetupDuperWPF.csproj; git ls-tree -r --name-only 2e030e0873b043e5eab485ce9902761f999b9edf | grep -iE 'global\\.json|packages\\.lock\\.json|Directory\\.Build|nuget\\.config|\\.github/'; cd \"\$R\" && strings -n 6 app/MX_Bikes_Setup_Duper.dll | grep -m1 -A1 -x 'PresentationBuildTasks'"
# The release page: who published it, when, from which branch, with its notes.
ev release-page "curl -sSL https://api.github.com/repos/dmkrtz/MXBikesSetupDuperWPF/releases/tags/0.1.8674.29660 | python3 -I -c 'import json,sys; r=json.load(sys.stdin); print(r[\"tag_name\"], r[\"published_at\"], \"by\", r[\"author\"][\"login\"], \"target\", r[\"target_commitish\"]); print([(a[\"name\"], a[\"size\"], a[\"uploader\"][\"login\"]) for a in r[\"assets\"]]); print(r[\"body\"])'; curl -sSL https://api.github.com/repos/dmkrtz/MXBikesSetupDuperWPF/git/refs/tags/0.1.8674.29660 | grep -E '\"sha\"|\"type\"'; curl -sSL https://api.github.com/repos/dmkrtz/MXBikesSetupDuperWPF | grep -E '\"license\"'"
# The public history up to the commit.
ev history "cd \"\$SRC\" && git log --format='%h %ad %s' --date=short 2e030e0873b043e5eab485ce9902761f999b9edf | cat; git log --format=%ad --date=short 2e030e0873b043e5eab485ce9902761f999b9edf | sort -u | wc -l"
