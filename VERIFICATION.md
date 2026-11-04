# Verification: Windows 11 x64, 4 November 2026

19 automated bridge tests passed: input decode/calibration/remapping, all signed
motion axes, SDL coordinate composition, USB HID descriptors and ACKs, stale gyro,
DSU framing/CRC, ordinary rumble and detailed haptic bands/sides/timing/lease.

A physical official Switch 2 Pro Controller was connected over an RZ616 Bluetooth
adapter. Buttons, sticks, gyro, acceleration, reconnect and independent left/right
actuator tests were observed. Native SDL2/SDL3 opened the virtual Switch Pro and
its sensors. USB/IP 0.9.8.1's signed driver enumerated a healthy virtual HID device.
The user confirmed corrected up/down and left/right aiming in their native TOTK
installation. Ryujinx/Eglantine gameplay was not tested in this session.

With PowerMoon-Switch2Pro, game logs recorded motion reads and live vibration
requests. The user confirmed Odyssey gameplay motion, correctly timed rumble,
a sustained 2-second test and a modest subjective improvement with direct haptics.
No measured or blind comparison to console HD Rumble 2 was performed. Frequency
and perceptual amplitude calibration remain experimental. Other adapters/Windows
versions and USB cable transport have not been validated.

Raw hardware captures, device addresses, machine paths, calibration and logs are
excluded from publication. This document summarizes observations, not universal
compatibility or lossless HD Rumble certification.
