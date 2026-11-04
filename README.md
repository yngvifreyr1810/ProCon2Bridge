# ProCon2Bridge

Windows Bluetooth support for the **official Nintendo Switch 2 Pro Controller**,
with buttons, sticks, gyro, accelerometer and vibration. GPL-3.0-or-later.

**Gameplay testing so far: TOTK Recomp and Super Mario Odyssey / Power Moon Recomp
only. Ryujinx, Eglantine and all other emulators have NOT been tested.**

## Download and run

Before running, see [what the scripts do, permissions, checksums and removal](SECURITY.md).
Project executables are currently unsigned; do not disable antivirus to run them.

Download **ProCon2Bridge-0.2.0-windows-x64.zip** from [Releases](https://github.com/yngvifreyr1810/ProCon2Bridge/releases).
Extract to a writable folder and double-click **START.cmd**. Python is not needed.
First launch installs the bundled, signed USB/IP driver; accept Windows' administrator
prompt and restart Windows if requested. Keep the bridge window open.

Hold the controller's **SYNC** button on first use, then leave it flat and still
for a few seconds for automatic gyro calibration. Afterwards, press a button to
reconnect. It appears in games as a **Nintendo Switch Pro Controller**. Use Nintendo
button labels. In Steam, enable the game's Nintendo/Switch Pro controller support
as needed. For games reading SDL directly, disabling Steam Input for that game
can preserve native motion access. No manual Bluetooth MAC configuration is needed.

**STOP.cmd** disconnects cleanly. **CALIBRATE.cmd** restarts calibration: leave the
controller flat and untouched for a few seconds. Keep `config.json` when upgrading;
it contains your local calibration and is created automatically on first launch.

## Supported paths and limits

| Use | Input and motion | Vibration |
| --- | --- | --- |
| Native SDL games / Steam with Switch Pro input | Virtual Switch Pro HID, gyro and accelerometer | Classic Switch rumble translated to Pro 2 BLE |
| Ryujinx / Eglantine | Select virtual Pro Controller; DSU motion at 127.0.0.1:26760 where supported | Depends on the emulator's output support; not hardware-tested here |
| [PowerMoon-Switch2Pro](https://github.com/yngvifreyr1810/PowerMoon-Switch2Pro) | Native motion adapter in that fork | Direct per-side, per-band frequency/amplitude transport; experimental physical calibration |

This is a **user-mode bridge using a third-party signed virtual USB driver**,
not a new signed Nintendo kernel driver. Windows 11 x64 was tested; other Windows
versions, Bluetooth adapters and third-party controllers remain unverified.
USB cable transport, NFC, audio/headphone support and native GameChat are not implemented.
GL/GR/C can be mapped to existing controls in `config.json`; they are not extra
native Switch 1 buttons. Pairing back to a console may require SYNC again.

**HD Rumble 2 fidelity is not guaranteed.** The direct path retains the game's
individual effect parameters; the frequency-to-physical-carrier profile is
experimental. See [HD-RUMBLE.md](HD-RUMBLE.md), [verification](VERIFICATION.md),
and [credits/licenses](THIRD_PARTY.md). Do not equate standard SDL rumble with
lossless HD Rumble or advertise console-identical output.

## Build and contribute

On Windows x64 with Python 3.14: `python -m venv .venv`, activate it,
`python -m pip install -r requirements.txt`, `python -m unittest discover -v`,
then `powershell -ExecutionPolicy Bypass -File BUILD.ps1`.
Obtain the unchanged driver installer linked in THIRD_PARTY.md for a source build;
the binary release bundles it. BUILD.ps1 does not install drivers.

All bridge source is included in binary downloads. Runtime logs, physical device
addresses and calibration are intentionally excluded from Git and release files.
No game, keys, firmware, Nintendo SDK or game assets are distributed.

Maintained by **Vĩnh An Project / yngvifreyr1810**, with implementation assistance
from OpenAI Codex. Built on the credited community protocol research below.
