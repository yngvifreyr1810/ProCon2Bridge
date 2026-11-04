# Sources and licenses

This package is experimental GPL-3.0-or-later software. It is a user-mode BLE
bridge, not an independently developed or Microsoft-signed controller driver.
The separate USB/IP kernel driver is third-party software.

* Switch2Connect, copyright 2026 TommyWabg, GPL-3.0-or-later:
  https://github.com/TommyWabg/Switch2Connect
  pinned commit e5dd90bb54106b35a1110f96ec9d060390e5d096.
  `vendor/usbip_server.py` is copied unmodified from `src/usbip_server.py`.
  BLE initialization, pairing, memory/calibration layout, haptic packet layout,
  and Switch 1 rumble conversion in `src/protocol.py`/`src/bridge.py` are adapted from
  that project. The conversion does not guarantee identical HD Rumble 2 effects.
  `native_pro.py` subclasses the upstream server with a HID-only descriptor,
  64-byte USB reports, priority ACK handling, neutral virtual sensor calibration,
  and stale-motion suppression. The original vendor file remains unchanged.
  Version 0.3.0 additionally adapts the GATT discovery fallback and throughput
  request lifecycle from src/controller.py / src/windows_ble_parameters.py.
  Bounded haptic I/O and fixed-cadence scheduling were informed by
  src/system_bt_pair_rumble.py; the multi-Joy-Con coordinator is not copied.
  The same pinned commit was rechecked against origin/main on 4 November 2026.
  See UPSTREAM-REVIEW.md for the comparison and implementation boundaries.
* pad2go, GPL-3.0:
  https://github.com/patrickdeangelis/pad2go
  pinned commit 6fa74a5603e2ca7fc4f0185615c39ba2ccb68a19.
  Protocol layout and CemuHook framing were cross-checked against
  `internal/protocol`, `internal/controller` and `internal/dsu`.
* switch2-pico, copyright 2026 switch2-pico contributors, MIT:
  https://github.com/joshbirnholz/switch2-pico/tree/69b6475141952a931a07731be9bd0455ba90ab9c
  `core/src/hd_rumble.c` informed the experimental logarithmic frequency profile
  (anchor 274 at 160 Hz, slope 117 codes/octave). That upstream model is itself
  unmeasured and its repository identifies hardware testing as incomplete.
  The MIT notice is included in ../dependency-licenses/switch2-pico-MIT.txt.
* Linux input / hid-nintendo2, Vicki Pfau and contributors, GPL-2.0:
  https://marc.info/?l=linux-input&m=178280949199923&w=2
  Published idle carrier observations and 450 reference amplitude were consulted.
  No Linux driver source is incorporated. USB and BLE packet layouts differ.
* SDL, zlib: https://github.com/libsdl-org/SDL — Switch 1 coordinate conventions;
  hifihedgehog's Switch 2 SDL implementation at
  https://github.com/hifihedgehog/SDL/blob/d98c5804a9d20b0d96e993741797878c86b8f1e1/src/joystick/hidapi/SDL_hidapi_switch2.c
  was used to cross-check the native sensor basis. No SDL source is bundled.
* dekuNukem's public Nintendo Switch reverse-engineering documentation:
  https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering
  Classic rumble field conventions were consulted; this does not establish the
  Switch 2 physical frequency mapping. No firmware or game material is included.
* USB/IP for Windows, Vadym Hrynchyshyn and contributors:
  https://github.com/vadimgrn/usbip-win2/releases/tag/v.0.9.8.1
  The unmodified upstream installer is included under `../drivers/` and retains
  its BSD-2-Clause license and digital signature. The full notice is included in
  ../drivers/LICENSE-usbip-win2.txt. It is not part of this project's source.
  SHA256: 38cad6d4432b52d5bb9409d9ad03b72fdffc4ada4cd3a48fbeca1a2752a8518a.
* Bleak and PyWinRT provide Windows Bluetooth access; Python and PyInstaller
  provide the runtime and executable packaging; the settings window uses Python
  Tkinter with Tcl/Tk. Corresponding dependency licenses, including Tcl/Tk license
  terms, are included in `../dependency-licenses/`.

All ProCon2Bridge Python source is included next to the executable. Build with
Python 3.14 on Windows, install `requirements.txt` in a virtual environment,
then run `../scripts/ProCon2Bridge-Build.ps1`. Changes to the upstream USB/IP source are not needed.

No controller firmware is modified. Pairing stores the PC adapter address on
the controller; returning to a Switch console may require pairing it again.

* pystray 0.19.5 (LGPL-3.0), https://github.com/moses-palmer/pystray: Windows notification-area icon and menu. Pillow 13.0.0 (MIT-CMU / HPND), https://github.com/python-pillow/Pillow: programmatically drawn controller icon. six 1.17.0 (MIT), https://github.com/benjaminp/six: pystray compatibility dependency. Corresponding notices are in `../dependency-licenses/`; these packages are unmodified. The tray image is drawn by this project and uses no third-party game artwork.
