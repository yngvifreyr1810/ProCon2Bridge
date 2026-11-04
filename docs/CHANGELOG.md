## 0.4.0

* Run ProCon2Bridge.exe directly: per-user installation, Startup registration, notification-area menu, no console window.
* Store the installed app at a stable LocalAppData path; preserve configuration on upgrades.
* Replace the legacy Run value with a Task Manager-manageable Startup shortcut and respect disabled entries.
* Open settings on repeat launch; calibrate without stopping the bridge; exit cleanly from the tray.
* Retry startup when Bluetooth/USB services are not ready and release resources after failed initialization.

## 0.3.3

* Add a per-user Windows Run entry on first launch.
* Task Manager Startup apps can disable the ProCon2Bridge entry.

## 0.3.2

* Prefix Windows entry-point and maintenance script names with ProCon2Bridge.

## 0.3.1

* Organize source, tests, documentation and maintenance scripts into folders.
* Keep root launch commands and improve packaged source layout.

# Changes

## 0.3.0

* Native ProCon2Bridge-Settings.cmd window for GL/GR: one button or a simultaneous chord,
  immediate live reload, overlap-safe hold/release and preserved calibration.
* Windows 11 BLE recovery: GATT validation, fresh discovery fallback, explicit
  throughput-request cleanup, bounded haptic writes and fixed packet cadence.
* Input watchdog independent of haptics; neutralize controls on disconnect,
  reject stale-session callbacks/input and clear old effects across reconnects.
* Record owner-confirmed emulator input, motion and rumble via Switch Pro 1;
  document evidence limits and the review of Switch2Connect's existing source.

## 0.2.0

* Direct Power Moon haptics: independent side/band amplitudes and frequencies,
  three temporal subframes, lease arbitration and 200 ms source watchdog.
* Explicit experimental frequency profile; no claim of console HD Rumble 2 parity.
* First-launch signed-driver setup, automatic generic configuration, public source
  and privacy-filtered release contents with credits and dependency notices.
* Corrected motion axes and improved ordinary SDL rumble from earlier prototypes.
