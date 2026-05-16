# Security policy

## Supported versions

EQ Travel Map is a single-user desktop tool that only reads local
EverQuest log files and writes a PNG to disk. It does not handle
credentials, network traffic, or untrusted remote input.

Security fixes will be applied to the latest released version. Older
versions are not maintained.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security-sensitive
reports.

Instead, use GitHub's private vulnerability reporting:

1. Go to https://github.com/ajbtech/EQ-Travel-Map/security
2. Click **Report a vulnerability**
3. Fill in the form with a description of the issue, steps to
   reproduce, and (if possible) a suggested fix or mitigation.

You can expect an initial acknowledgement within a few days. If the
report is confirmed, we'll work with you on a fix and coordinate
disclosure timing.

## Scope

In scope:

- Code execution, file overwrite, or path traversal triggered by a
  crafted EverQuest log file
- Vulnerabilities in the PyInstaller bundle that ship to end users
  (`EQTravelMap.exe` and its bundled libraries)
- Issues in the build / release workflow that could allow tampering
  with published release artifacts

Out of scope:

- Bugs that only crash the application without further impact
- Theoretical issues in third-party dependencies that don't actually
  affect this app's usage of them
- Anything requiring an attacker to already have write access to the
  user's machine
