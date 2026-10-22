# Validation record

Date: 2026-10-22.

The generalized release was checked with Python 3.13, PyQt5 5.15.11 and pyserial 3.5 on Windows. The Qt platform was set to offscreen for the GUI checks.

| Check actually executed | Result |
| --- | --- |
| Parse the release Python source and import its dependencies | Passed |
| Construct the application window without opening a physical serial port | Passed |
| Check generalized window/brand labels | Passed |
| Parse UP:72.5,DOWN:48.2 and let the display animations complete | Passed; labels show 72 dB, 48 dB and 24 dB |
| Ignore a malformed line | Passed |
| Clamp a channel value above 130 | Passed |
| Reassemble a line split across two simulated serial reads | Passed |
| Handle multiple newline-delimited frames in one simulated read | Passed |
| Close the serial fixture when the window closes | Passed |
| Scan the release's text for common credential patterns | No matches |

Not performed: a real CH340/device transfer, an acoustic calibration or accuracy study, validation against an acoustic standard, binary packaging, or validation on other operating systems.

The release retains the existing parser and serial behavior. These checks do not establish production robustness or measurement accuracy.

