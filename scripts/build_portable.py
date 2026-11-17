"""Build a clean, licensed Windows portable ZIP from this source tree."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DENY_DIRS = {'data', 'recordings', '字幕记录', '.meeting_workflow', '__pycache__', '.git'}
DENY_NAMES = {'config.json', 'teams_extracted_raw.txt', 'kb.jsonl'}


def add_notices(app: Path):
    for name in ('LICENSE', 'ATTRIBUTION.md', 'PRIVACY.md', 'THIRD-PARTY-NOTICES.md'):
        shutil.copy2(ROOT / name, app / name)
    licenses = app / 'licenses'
    licenses.mkdir(exist_ok=True)
    shutil.copy2(Path(sys.base_prefix) / 'LICENSE.txt', licenses / 'CPython-LICENSE.txt')
    for path in (ROOT / 'docs' / 'licenses').glob('*'):
        shutil.copy2(path, licenses / path.name)
    inventory = []
    # Include notices conservatively for the complete locked build environment,
    # rather than assuming every imported transitive dependency was pruned.
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
        name = dist.metadata['Name']
        copied = []
        for rel in dist.files or []:
            leaf = PurePosixPath(str(rel)).name.lower()
            if not any(token in leaf for token in ('license', 'copying', 'notice', 'copyright')):
                continue
            if '..' in PurePosixPath(str(rel)).parts:
                continue
            source = Path(dist.locate_file(rel))
            if not source.is_file():
                continue
            target = licenses / name / str(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target.relative_to(app).as_posix())
        inventory.append({'name': name, 'version': dist.version, 'notice_files': copied})
    (app / 'BUILD-DEPENDENCIES.json').write_text(json.dumps({
        'scope': 'Conservative inventory of installed build-environment packages; not all packages are bundled.',
        'python': sys.version.split()[0], 'packages': inventory,
    }, indent=2) + '\n', encoding='utf-8')
    (app / 'START-HERE.txt').write_text(
        'Cue Teams — Windows 10 / 11 x64\n\n'
        '1. Extract the entire ZIP to a writable local folder.\n'
        '2. Open Cue-Teams and double-click CueTeams.exe. No Python installation is needed.\n'
        '3. Enable live captions in your Teams desktop meeting. Keep the captions visible.\n'
        '4. Choose a file name and save folder, then click 开始保存字幕.\n'
        '5. Check that speaker names and captions appear and the saved count increases.\n'
        '6. Stop capture after the meeting. TXT and JSON are saved automatically.\n\n'
        'Keep _internal with the executable. New settings are created under data/.\n'
        'No personal settings, meetings, credentials or audio models are included.\n'
        'If names are not exposed by Teams they cannot be reconstructed. UI changes may require updates.\n'
        'This community build is unsigned; follow your organization’s software policy.\n\n'
        'Source and releases: https://github.com/Asherdeng138/Cue-Teams\n'
        'Based on Digitalgrub Cue v1.2.3 (MIT); see LICENSE and ATTRIBUTION.md.\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-dist', type=Path, help='Package a clean existing onedir build instead of rebuilding')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise SystemExit('Build on Windows with Python 3.12 and Tcl/Tk.')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.from_dist:
        app = args.from_dist.resolve()
    else:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm',
                        '--distpath', str(output), str(ROOT / 'CueTeams.spec')], cwd=ROOT, check=True)
        app = output / 'Cue-Teams'
    if not (app / 'CueTeams.exe').is_file() or not (app / '_internal').is_dir():
        raise SystemExit('Expected a complete Cue-Teams onedir build.')
    for path in app.rglob('*'):
        rel = path.relative_to(app)
        if any(p in DENY_DIRS for p in rel.parts) or path.name in DENY_NAMES:
            raise SystemExit(f'Refusing to package local data: {rel}')
    add_notices(app)
    # Build imports must never accidentally pull the original audio stack in.
    unexpected = [p.name for p in (app / '_internal').iterdir()
                  if p.name.lower().startswith(('torch', 'numpy', 'faster_whisper', 'ctranslate2', 'av.', 'libavcodec', 'onnxruntime'))]
    if unexpected:
        raise SystemExit(f'Unexpected audio dependencies: {unexpected}')
    files = sorted(p for p in app.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    manifest = app / 'SHA256SUMS.txt'
    manifest.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(app).as_posix()}\n' for p in files), encoding='utf-8')
    archive = output / 'Cue-Teams-Windows-x64.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in sorted(p for p in app.rglob('*') if p.is_file()):
            z.write(path, (Path('Cue-Teams') / path.relative_to(app)).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise SystemExit('Archive verification failed')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    print(json.dumps({'asset': archive.name, 'bytes': archive.stat().st_size,
                      'files': len(files) + 1, 'sha256': checksum}))


if __name__ == '__main__':
    main()
