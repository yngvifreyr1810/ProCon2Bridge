# Verification: Windows 11 x64, 4 November 2026

32 automated bridge tests passed: input decode/calibration/remapping, all signed
motion axes, SDL coordinate composition, USB HID descriptors and ACKs, stale gyro,
DSU framing/CRC, ordinary rumble and detailed haptic bands/sides/timing/lease.

A physical official Switch 2 Pro Controller was connected over an RZ616 Bluetooth
adapter. Buttons, sticks, gyro, acceleration, reconnect and independent left/right
actuator tests were observed. Native SDL2/SDL3 opened the virtual Switch Pro and
its sensors. USB/IP 0.9.8.1's signed driver enumerated a healthy virtual HID device.
The user confirmed corrected up/down and left/right aiming in their native TOTK
installation. In a subsequent report, the owner confirmed emulator input, motion
and rumble through the virtual Switch Pro 1 protocol. Emulator names, versions
and a per-game matrix were not recorded; that report is not universal certification.

For 0.3.0, the rebuilt executable connected through fresh filtered GATT discovery
and retained the Windows throughput request. The native settings window opened
from the packaged executable. The owner saved GL = B / GR = A without restarting
the bridge, tested in gameplay/emulation and reported that both worked perfectly.
Local status also recorded the physical GL/GR inputs and remapped output; raw
captures and controller addresses remain private. Automated checks cover chords,
overlapping holds/releases, live reload, concurrent config/calibration updates,
stale/missing GATT characteristics, cancellation, cleanup, blocked writes and the
independent input-loss watchdog. GUI layout/save was tested with a temporary config.
Cached-discovery failure scenarios were simulated, not reproduced on every adapter.

With PowerfulMoon, game logs recorded motion reads and live vibration
requests. The user confirmed Odyssey gameplay motion, correctly timed rumble,
a sustained 2-second test and a modest subjective improvement with direct haptics.
No measured or blind comparison to console HD Rumble 2 was performed. Frequency
and perceptual amplitude calibration remain experimental. Other adapters/Windows
versions and USB cable transport have not been validated.

Raw hardware captures, device addresses, machine paths, calibration and logs are
excluded from publication. This document summarizes observations, not universal
compatibility or lossless HD Rumble certification.


## 0.4.0 background app

Local Windows 11 validation: the installed windowless EXE ran from LocalAppData
with no console window. Windows Settings > Apps > Startup visibly listed
ProCon2Bridge.exe as On. Its Startup-folder shortcut targets the installed EXE;
the legacy Run value was removed. After turning Bluetooth on, the running app
connected without restarting it. SDL3 opened the virtual Nintendo Switch Pro
Controller, enabled accelerometer and gyro and returned changing sensor and
stick values. The bridge observed A/B and GL/GR input with zero invalid reports.
SDL accepted both rumble calls and the user confirmed feeling two pulses.
Configuration migration preserved GL=B / GR=A. Automated lifecycle checks cover
cleanup after failed initialization, interruptible startup retry and upgrade
preservation without re-enabling disabled startup. Actual Windows restart is
pending the user's manual test; do not present it as verified.
