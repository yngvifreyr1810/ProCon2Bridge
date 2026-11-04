# Experimental detailed haptics (0.2.0)

The ordinary path receives the virtual Switch 1 controller's rumble bytes. Their
translation is approximate. SDL_RumbleGamepad itself exposes two motor strengths;
it does not preserve the original game's four independently controlled bands.

PowerMoon-Switch2Pro instead sends eight float values over loopback UDP: LF amplitude,
LF frequency in Hz, HF amplitude, HF frequency, separately for left and right.
Guest-thread updates are sent immediately rather than reduced to a 60 Hz render
frame. Three different 5 ms subframes are retained per BLE packet, using a 15 ms
lookbehind buffer. BLE scheduling and radio jitter can still lose temporal precision.

The **experimental** profile is `code = 274 + 117 * log2(Hz / 160)` and linear
amplitude `450 * game_amplitude * strength`, capped at 800. Its anchors and slope
are informed by switch2-pico's unmeasured model and Linux's observed idle carriers.
They are **not** Nintendo factory calibration or a measured actuator transfer
function. BLE's donor codec has 9-bit frequency and separate tone flags; unknown
tone flags remain clear and frequency clips to 1..511. The USB codec's bit layout
must not be substituted for the LF-first BLE layout. Amplitude response is also
not physically linear in perceived intensity. No raw waveform, audio haptics or
HD Rumble 2 enhancement beyond these parameters is claimed.

## Public protocol v1

Bind/listen only on **127.0.0.1:26761**, UDP. Little-endian, IEEE binary32 floats.

* Query: 8 bytes `<4sI`: `PC2Q`, version 1.
* Reply: 16 bytes `<4sIII`: `PC2A`, version 1, capabilities, nominal 200 Hz.
  Capability bit 0 = physical BLE connected; bit 1 = detailed parameter endpoint.
* Effect: exactly 56 bytes `<4sHHIHHQ8f`: `PC2H`, version 1, flags 0,
  sequence uint32, TTL milliseconds 1..200, reserved 0, source timestamp uint64
  nanoseconds, then the eight floats above. Source timestamp is diagnostic only;
  receiver arrival time governs sampling and lease. Amplitude 0..2; Hz 1..1250.
* A source owns output until its TTL expires, with increasing sequence numbers
  modulo 2^32. Other local sources and stale/replayed frames are rejected.
  Ordinary virtual-HID rumble is ignored during this lease. Zero amplitude stops
  effects. Lost source, stale packet stream or crashed game stops within 200 ms
  plus the next BLE tick. This endpoint trusts local applications, not a network.

Power Moon enables this only for the bridge's specific virtual identity and when
the endpoint reports a connected controller. Otherwise it falls back to ordinary
SDL vibration. Toggle the experimental option in F1 > Controls to compare modes.

References and original authors are listed in [THIRD_PARTY.md](THIRD_PARTY.md). User testing found
correct gameplay event timing, a working 2-second test, and a modest subjective
improvement. There has been no instrumented or blind console comparison.
