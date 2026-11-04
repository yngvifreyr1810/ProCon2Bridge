# ProCon2Bridge

[Tiếng Việt](docs/README-VI.md)

Windows Bluetooth support for the **official Nintendo Switch 2 Pro Controller**,
with buttons, sticks, gyro, accelerometer and vibration. GPL-3.0-or-later.

**Compatibility evidence:** TOTK Recomp and Super Mario Odyssey / Power Moon Recomp
were tested during development. The project owner has additionally confirmed
working input, motion and rumble in Switch emulators through the virtual **Switch
Pro 1** protocol. Emulator names/versions and a complete game matrix were not
recorded for that report; it is not a guarantee for every emulator or game.

## Repository layout

The root keeps the quick-start commands, project overview and default configuration.
Implementation lives in `src/`, automated checks in `tests/`, long-form guides and
credits in `docs/`, and build / driver maintenance tools in `scripts/`.

## Download and run

Before running, see [what the scripts do, permissions, checksums and removal](SECURITY.md).
Project executables are currently unsigned; do not disable antivirus to run them.

Download **ProCon2Bridge-0.4.0-windows-x64.zip** from [Releases](https://github.com/yngvifreyr1810/ProCon2Bridge/releases).
Extract the complete ZIP, then double-click **ProCon2Bridge.exe**. Python is not needed.
The EXE installs the app for your Windows account in
`%LOCALAPPDATA%/Programs/ProCon2Bridge`, registers startup, and runs in the
notification area beside the clock. First-time driver setup may ask for Windows
administrator approval. Restart Windows if the driver installer requests it.

After setup, press a controller button to reconnect; hold SYNC for initial pairing.
The bridge keeps running without a CMD window. Right-click its blue controller
icon for **Settings**, **Calibrate motion**, **Windows Startup settings**, logs,
or **Exit ProCon2Bridge**. Launching the EXE again opens settings instead of
starting another bridge. Legacy Start/Settings/Stop scripts remain available.

The installed app has a fixed location, so moving or deleting the downloaded ZIP
or extracted package does not break startup. Your configuration and logs are in
the installed app folder. An existing `config.json` beside the downloaded EXE is
migrated only when no installed configuration exists; upgrades preserve the
installed calibration and GL/GR mappings.

## Start automatically with Windows

First EXE launch creates **ProCon2Bridge.lnk** in the current user's Windows
Startup folder, targeting the installed EXE. It appears as **ProCon2Bridge** in
**Task Manager > Startup apps** and **Settings > Apps > Startup**.
Disable it there whenever you prefer manual launch. The app does not overwrite
Windows' enabled/disabled choice. No scheduled task or bridge service is used.
Startup waits and retries when Bluetooth or the virtual controller is not ready
immediately after sign-in. Exit from the tray stops the bridge for this session.

## Map the GL / GR back buttons

Double-click **ProCon2Bridge-Settings.cmd** (or run `ProCon2Bridge.exe --settings`). Choose an
action for **GL (left)** and **GR (right)**, then **Save mappings**. You can select
one existing Switch Pro button from the list or type a simultaneous chord such
as `ZL + ZR` (up to four buttons). `NONE` disables that back button.

Changes apply to the running bridge within one second, without reconnecting.
The window also shows held back buttons and virtual output; hold a button for
one second to see it in the status display. Physical face buttons keep working
when their target is also assigned to GL/GR. Mapping is held/released with the
physical back button; there is no turbo, timed macro or keyboard injection.

Example: GL = `B`, GR = `A`. Button names follow **Nintendo** labeling. These are
aliases/chords of Switch Pro 1 buttons, not two additional native game buttons.
Existing configuration and gyro calibration survive updates. Manual mappings can
still use legacy strings or lists, e.g. `"GL": ["ZL", "ZR"]`.

## Supported paths and limits

| Use | Input and motion | Vibration |
| --- | --- | --- |
| Native SDL games / Steam with Switch Pro input | Virtual Switch Pro HID, gyro and accelerometer | Classic Switch rumble translated to Pro 2 BLE |
| Switch emulators (owner-confirmed; versions not recorded) | Virtual Switch Pro 1 input and motion; optional DSU at 127.0.0.1:26760 where supported | Owner confirmed working output through Switch Pro 1; emulator-specific settings still apply |
| [PowerMoon-Switch2Pro](https://github.com/yngvifreyr1810/PowerMoon-Switch2Pro) | Native motion adapter in that fork | Direct per-side, per-band frequency/amplitude transport; experimental physical calibration |

This is a **user-mode bridge using a third-party signed virtual USB driver**,
not a new signed Nintendo kernel driver. Windows 11 x64 was tested; other Windows
versions, Bluetooth adapters and third-party controllers remain unverified.
USB cable transport, NFC, audio/headphone support and native GameChat are not implemented.
GL/GR can be configured in the settings window; C and other advanced mappings
remain in `config.json`. Pairing back to a console may require SYNC again.

**HD Rumble 2 fidelity is not guaranteed.** The direct path retains the game's
individual effect parameters; the frequency-to-physical-carrier profile is
experimental. See [HD-RUMBLE.md](docs/HD-RUMBLE.md), [verification](docs/VERIFICATION.md),
and [credits/licenses](docs/THIRD_PARTY.md). Do not equate standard SDL rumble with
lossless HD Rumble or advertise console-identical output.

## Windows 11 Bluetooth improvements

Version 0.3.2 adds fresh GATT discovery fallback after a stale reconnect cache,
checks all required characteristics before initialization, explicitly releases
the Windows throughput-preference request, bounds BLE haptic writes and keeps
input-loss recovery independent of rumble. The virtual controller remains present
while the physical controller reconnects; held controls are released on loss.
No Bluetooth adapter power settings, registry tweaks or priority hacks are applied.

See [the Switch2Connect comparison](docs/UPSTREAM-REVIEW.md) for inherited code,
new adaptations and features deliberately outside this focused bridge's scope.

## Build and contribute

On Windows x64 with Python 3.14: `python -m venv .venv`, activate it,
`python -m pip install -r requirements.txt`, then run these PowerShell commands:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -t . -v
powershell -ExecutionPolicy Bypass -File scripts/ProCon2Bridge-Build.ps1
```
Obtain the unchanged driver installer linked in docs/THIRD_PARTY.md for a source build;
the binary release bundles it. scripts/ProCon2Bridge-Build.ps1 does not install drivers.

All bridge source is included in binary downloads. Runtime logs, physical device
addresses and calibration are intentionally excluded from Git and release files.
No game, keys, firmware, Nintendo SDK or game assets are distributed.

Maintained by **Vĩnh An Project / yngvifreyr1810**, with implementation assistance
from OpenAI Codex. Built on the credited community protocol research below.
