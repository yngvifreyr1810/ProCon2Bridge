# Switch2Connect review — 4 November 2026

Reviewed [TommyWabg/Switch2Connect](https://github.com/TommyWabg/Switch2Connect)
at `e5dd90bb54106b35a1110f96ec9d060390e5d096`, still origin/main when checked.
It was already a credited source for ProCon2Bridge 0.2.0, not newly discovered
independent protocol work. Credits and GPL notices remain in THIRD_PARTY.md.

## Already inherited

* Unmodified `src/usbip_server.py`, retained as vendor/usbip_server.py.
* Pro 2 BLE initialization/pairing/calibration and haptic framing/conversion.
* Our HID-only NativeProServer wrapper retains the known-working Switch Pro 1
  identity, full-size HID reports and sensor-axis correction used by games.

## Adopted / adapted for 0.3.0

| Upstream reference | Focused implementation here |
| --- | --- |
| [controller.py: connect_ble](https://github.com/TommyWabg/Switch2Connect/blob/e5dd90bb54106b35a1110f96ec9d060390e5d096/src/controller.py#L1979) | Cached filtered discovery only after a successful connection in this process; fresh filtered/full fallback; all four required GATT characteristics checked; explicit client cleanup |
| [windows_ble_parameters.py](https://github.com/TommyWabg/Switch2Connect/blob/e5dd90bb54106b35a1110f96ec9d060390e5d096/src/windows_ble_parameters.py) and controller.py request lifecycle | Windows 11 build gate, synchronous/asynchronous API support, retain successful throughput request, close it on disconnect; failure remains nonfatal |
| [system_bt_pair_rumble.py](https://github.com/TommyWabg/Switch2Connect/blob/e5dd90bb54106b35a1110f96ec9d060390e5d096/src/system_bt_pair_rumble.py) | Applied the bounded-write/fixed-cadence principle to our single Pro controller, not the Joy-Con pair coordinator; 250 ms write deadline and no concurrent queued write stream |
| Upstream remapping/UI approach | Small native GL/GR settings window; simultaneous gamepad chords; live reload, atomic config replacement and writer locking so calibration/settings do not overwrite each other |

We also separated the input-loss watchdog from haptics, immediately neutralize
virtual controls on physical disconnect, ignore old-session disconnect callbacks
and input notifications, clear queued haptics between sessions, and preserve the
existing virtual device during physical reconnection. These changes address
failure paths in our smaller implementation rather than importing the entire app.

## Outside this update

No ESP32 firmware, multiple Joy-Con pair coordinator, Xbox/DualSense emulation,
magnetometer fusion, audio haptics, NFC, virtual Switch Pro 2 identity, or global
keyboard/mouse injection is added. Those features have different drivers and
validation requirements. The current focus is Windows 11 system Bluetooth with
the verified Switch Pro 1 path for emulators and recomp games. There is no claim
of 133 Hz over every PC adapter or console-identical HD Rumble 2 calibration.

## Evidence

Automated checks cover discovery failure/missing characteristics, cancellation,
cleanup, request disposal, blocked writes, input-loss release, live mapping reload,
GL/GR chords and overlapping holds, concurrent calibration/settings saves and
the existing motion/rumble protocol tests. The native settings UI was exercised
on Windows with a temporary configuration. Physical results are recorded separately
in VERIFICATION.md; simulations do not establish radio latency or universal compatibility.
