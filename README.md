# ProCon2Bridge

ProCon2Bridge provides Windows 11 x64 support for official Nintendo Switch 2 Pro Controllers connected via Bluetooth. It translates controller inputs to a virtual Switch Pro 1 controller interface, enabling digital buttons, analog sticks, motion sensors (gyroscope and accelerometer), rumble feedback, and remappable GL/GR back buttons.

This repository contains no proprietary Nintendo software, firmware, SDKs, encryption keys, or extracted game assets.

## Installation & Setup

1. Download **ProCon2Bridge-0.4.0-windows-x64.zip** from [Releases](https://github.com/yngvifreyr1810/ProCon2Bridge/releases/tag/v0.4.0) and extract the complete ZIP.
2. Run `ProCon2Bridge.exe` from the extracted folder. The application installs itself locally into `%LOCALAPPDATA%\Programs\ProCon2Bridge`.
3. Approve the Windows administrator prompt if the signed third-party USB/IP driver needs installing. Restart Windows if its installer asks you to. Pair with **SYNC** for the first Bluetooth connection.

The third-party driver is signed; the project EXE is currently unsigned. The release provides a ZIP checksum. See [SECURITY.md](SECURITY.md) for verification, permissions and removal.

## Daily Usage & Windows Startup

ProCon2Bridge operates silently in the system tray without requiring an open command prompt (CMD) window.

- **Startup Integration:** The first launch registers ProCon2Bridge in Windows Startup apps. You can enable or disable automatic launch via Task Manager (**Startup apps** tab).
- **Daily Reconnection:** After Windows starts, turn on Bluetooth and press **A** to reconnect. Startup retries while Bluetooth or the virtual device is still becoming available.
- **Upgrades:** Run the newer package EXE to update the installed app. Existing configuration files, sensor calibrations, and GL/GR button mappings are preserved.

## Configuration & Calibration

Right-click the blue controller icon beside the clock for **Back buttons / Settings**, **Calibrate motion**, **Windows Startup settings**, logs or **Exit ProCon2Bridge**. Opening the EXE again brings up settings. Only the bridge starts with Windows; it does not launch a game.

Assign an existing Switch Pro button, a simultaneous chord such as `ZL + ZR`, or `NONE`, then choose **Save mappings**. These are Switch Pro 1 button aliases, not extra native game buttons; changes apply without reconnecting.

For motion calibration, place the controller still and choose **Calibrate motion** from the tray. Advanced settings remain in the installed `config.json`.

## Compatibility & Haptic Limitations

### Verified Applications
Input handling, motion controls, and rumble have been verified in games including [PowerfulMoon](https://github.com/yngvifreyr1810/PowerfulMoon) (Super Mario Odyssey Recomp), TOTK Recomp, and select Nintendo Switch emulators. The emulator names and versions were not recorded for those reports; compatibility depends on each game’s input settings.

### Vibration & Haptics
The virtual Switch Pro 1 path carries standard vibration and motion. The direct detailed haptics path is experimental. Console-identical HD Rumble / HD Rumble 2 feedback and exact physical amplitude reproduction are not claimed. Detailed vibration parameter routing and physical calibration boundaries are documented in [docs/HD-RUMBLE.md](docs/HD-RUMBLE.md).

Windows 11 x64 and the official controller are the tested target. USB cable transport, NFC, controller audio and native GameChat are not implemented. Pairing back to a console may require SYNC.

## Build and contribute

On Windows x64 with Python 3.14, create and activate a virtual environment, install `requirements.txt`, and run:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -t . -v
powershell -ExecutionPolicy Bypass -File scripts/ProCon2Bridge-Build.ps1
```

A source build needs the unchanged driver installer linked in [third-party credits](docs/THIRD_PARTY.md). The build script does not install drivers. Runtime logs, device addresses and calibration are excluded from Git and release files.

## Source and credits

ProCon2Bridge is licensed under the **GNU General Public License v3.0 or later (GPL-3.0-or-later)**.

The ZIP includes bridge source and dependency licenses. It contains no game files, keys, firmware, Nintendo SDK or game assets.

- **Third-party credits and licenses:** [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md)
- **Switch2Connect comparison:** [docs/UPSTREAM-REVIEW.md](docs/UPSTREAM-REVIEW.md)
- **Security & Integrity Policy:** [SECURITY.md](SECURITY.md)
- **Haptic technical details:** [docs/HD-RUMBLE.md](docs/HD-RUMBLE.md)

Maintained by Vĩnh An Project / yngvifreyr1810, with implementation assistance from OpenAI Codex.
