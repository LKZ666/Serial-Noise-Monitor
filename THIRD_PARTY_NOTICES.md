# Third-party dependencies and source scope

| Dependency | Version used for local verification | License evidence |
| --- | --- | --- |
| PyQt5 | 5.15.11 | Installed metadata identifies GPL v3. Riverbank distributes PyQt under GPL v3 or a commercial license. This source release uses the GPL option. |
| pyserial | 3.5 | Installed metadata identifies BSD; the upstream repository identifies BSD-3-Clause. |
| Qt and transitive packages installed with PyQt5 | Resolved by pip | Retain their package notices and licenses. Dependency source and binary packages are not bundled here. |

References:

- https://www.riverbankcomputing.com/software/pyqt
- https://pypi.org/project/PyQt5/5.15.11/
- https://github.com/pyserial/pyserial/blob/master/LICENSE.txt
- https://pypi.org/project/pyserial/3.5/

The application was adapted from a user-authorized local serial noise display program. The publishing preparation generalizes the title and removes product-specific branding while retaining the existing serial and display logic. This repository does not claim authorship of PyQt5, Qt, pyserial or Python.

The full GPL v3 license text is included in LICENSE, obtained from the SPDX license-list-data repository (text/GPL-3.0-only.txt, blob f6cdd22a6c1fbc887e08a215cb4beb3c47048041).

