# Third-party notices

## Upstream application code

This source derivative is based on Digitalgrub's Cue / meeting-copilot v1.2.3,
commit `3665cdc51e55bcf4cdb0ff0e4188c1600bdeca0e`.
Copyright (c) 2026 Digitalgrub. The full original MIT license is in `LICENSE`.
See `ATTRIBUTION.md` for the changes in this derivative.

## Assets

The original Cue icon, Digitalgrub logo and promotional assets are not included.
The `cue.ico` in this repository is independently drawn for this derivative,
and is supplied under the repository's MIT license. See `assets/README.md`.

## Dependencies and binary distribution

This package distributes application source, tests and an original replacement
icon, not Python packages, a Python runtime, or compiled application binaries.
`requirements-teams-lock.txt` records the tested dependency versions. Each external
package remains subject to its own license; the application MIT license does not
replace dependency licenses.

`CueTeams.spec` excludes audio engines including PyAV / FFmpeg, faster-whisper,
ctranslate2, onnxruntime, soundcard, torch and numpy. Retained upstream modules
still import AI clients and document-processing libraries. A binary publisher must
inspect the actual build output and preserve the notices and licenses for all
bundled components, including CPython, Tcl/Tk, sv-ttk and Python dependencies.

The original upstream notices are preserved as historical reference at
`docs/upstream/THIRD-PARTY-NOTICES.md`. They describe the original Cue binary,
including audio components and restricted original assets, rather than certifying
the dependency inventory or legal status of a new build of this derivative.
