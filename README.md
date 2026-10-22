# Serial Noise Monitor

A small Python desktop utility for viewing two sound-level values received from an embedded device over a serial port. This is a generalized release of an existing local application.

## Features

- Automatically prefers CH340/CH341 serial adapters.
- Displays upper and lower channel values and their absolute difference.
- Refreshes the serial input every 100 ms and animates displayed values.
- Reports connection and disconnection status.
- Clamps displayed values to 0–130 dB and rounds the labels to whole numbers.

The application displays measurements supplied by the device. It does not acquire microphone audio, perform acoustic calibration, or establish compliance with an acoustic testing standard. The difference is the absolute difference of the two displayed channel values.

## Run

The release was prepared with Python 3.13, PyQt5 5.15.11 and pyserial 3.5.

```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python src/noise_monitor.py
```

Connect the transmitting device before pressing the test button. Serial settings are **9600 baud, 8 data bits, no parity, 1 stop bit**.

## Serial data

Send ASCII lines terminated by a newline:

```text
UP:72.5,DOWN:48.2
UP:73.0,DOWN:49.1
```

The source's existing parser expects the fields in this order. Example values are illustrative. The UI labels are in Chinese.

If no CH340/CH341 adapter is recognized, the existing implementation falls back to the first available serial port. Check the connected device before starting. A manual port selector has not been implemented.

## Project scope

Only application source, dependency declarations, sample serial lines, documentation and licensing are included. Build caches, executables, screenshots and product-specific branding are excluded.

This is an early-stage standalone release. No public usage counts, external deployments or acoustic measurement accuracy are claimed. See VALIDATION.md for the checks actually run.

## License

The application source is released under **GPL-3.0-only**; see LICENSE. PyQt5 and pyserial are installed as dependencies and retain their own licenses. See THIRD_PARTY_NOTICES.md.

