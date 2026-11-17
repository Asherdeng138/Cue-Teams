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

The portable release produced by `scripts/build_portable.py` additionally includes
the `licenses/` directory and `BUILD-DEPENDENCIES.json`: CPython, Tcl/Tk and license
files collected conservatively for installed build-environment packages. Some
listed packages are build tools or are pruned from the final binary. Preserve these
notices when redistributing the portable ZIP. Tcl and Tk license texts are also
retained at `docs/licenses/` in this source repository.

`CueTeams.spec` excludes audio engines including PyAV / FFmpeg, faster-whisper,
ctranslate2, onnxruntime, soundcard, torch and numpy. Retained upstream modules
still import AI clients and document-processing libraries. A binary publisher must
inspect the actual build output and preserve the notices and licenses for all
bundled components, including CPython, Tcl/Tk, sv-ttk and Python dependencies.

The original upstream notices are preserved as historical reference at
`docs/upstream/THIRD-PARTY-NOTICES.md`. They describe the original Cue binary,
including audio components and restricted original assets, rather than certifying
the dependency inventory or legal status of a new build of this derivative.
