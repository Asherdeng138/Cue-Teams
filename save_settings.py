"""Validate user-selected transcript destinations without overwriting other meetings."""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)


def clean_filename(value: str) -> str:
    name = value.strip()
    for suffix in (".txt", ".json"):
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]
            break
    if not name or name in (".", ".."):
        raise ValueError("请填写会议或文件名称。")
    if _INVALID.search(name) or name.endswith((".", " ")):
        raise ValueError('文件名不能包含 < > : " / \\ | ? *，也不能以句点或空格结尾。')
    if _RESERVED.match(name):
        raise ValueError("这个名称是 Windows 的保留名称，请换一个文件名。")
    if len(name) > 140:
        raise ValueError("文件名过长，请缩短到 140 个字符以内。")
    return name


def recording_file(stem: Path, suffix: str) -> Path:
    # with_suffix would truncate meaningful dots, such as 'SDK v1.2'.
    return stem.parent / (stem.name + suffix)


def destination(folder: str, filename: str, *, active: Path | None = None) -> Path:
    name = clean_filename(filename)
    if not folder.strip():
        raise ValueError("请选择保存文件夹。")
    path = Path(os.path.expandvars(folder.strip())).expanduser()
    if not path.is_absolute():
        raise ValueError("请使用完整的保存路径，或点击「选择文件夹」。")
    path = path.resolve()
    candidate = path / name
    if active is not None and candidate == active.resolve():
        return candidate
    number = 2
    while any(recording_file(candidate, ext).exists() for ext in (".txt", ".json")):
        candidate = path / f"{name}_{number:02d}"
        number += 1
    return candidate


def check_writable(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    # The probe is our own temporary file; existing documents are never touched.
    with tempfile.NamedTemporaryFile(prefix=".cue-write-check-", dir=folder, delete=True) as probe:
        probe.write(b"Cue Teams")
        probe.flush()
