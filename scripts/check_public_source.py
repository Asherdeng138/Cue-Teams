"""Check release source for accidental local data, private paths and credentials.

This is a conservative release aid, not a guarantee that arbitrary meeting text
is safe to publish. Review any new examples and attachments before publishing.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
             '.pytest-tmp', 'build', 'dist', 'work', 'outputs'}
PRIVATE_DIRS = {'data', 'recordings', '字幕记录', '.meeting_workflow', 'CueData'}
PRIVATE_FILES = {'config.json', 'kb.jsonl', 'teams_extracted_raw.txt',
                 'teams_transcript_cleaned.txt'}
TEXT_SUFFIXES = {'.py', '.ps1', '.spec', '.md', '.txt', '.ini', '.json', '.yml', '.yaml'}
WINDOWS_HOME = re.compile(r'(?i)[a-z]:[\\/]+Users[\\/]+[^\\/\s<>]+')
UNIX_HOME = re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/')
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})')
SECRET = re.compile(r'(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{24,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')


def candidates():
    """Honor tracked files if this is the root of a Git checkout, else scan source."""
    if (ROOT / '.git').exists():
        result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--cached',
                                 '--others', '--exclude-standard'], capture_output=True)
        if result.returncode == 0:
            yield from (ROOT / p for p in result.stdout.decode('utf-8').split('\0') if p)
            return
    for path in ROOT.rglob('*'):
        if path.is_file() and not any(p in SKIP_DIRS for p in path.relative_to(ROOT).parts):
            yield path


def main():
    problems = []
    count = 0
    for path in sorted(set(candidates())):
        rel = path.relative_to(ROOT)
        count += 1
        if any(p in PRIVATE_DIRS for p in rel.parts) or path.name in PRIVATE_FILES:
            problems.append(f'{rel.as_posix()}: local app data must be excluded')
        if path.suffix.lower() in {'.exe', '.dll', '.lnk', '.pem', '.key', '.pfx', '.p12'}:
            problems.append(f'{rel.as_posix()}: unexpected binary, shortcut or key file')
        if path.name.startswith('.env') and path.name != '.env.example':
            problems.append(f'{rel.as_posix()}: local environment file')
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != '.gitignore':
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            labels = []
            if WINDOWS_HOME.search(line) or UNIX_HOME.search(line):
                labels.append('absolute personal home path')
            if SECRET.search(line):
                labels.append('possible credential')
            if any(m.group(1).lower() not in {'example.com', 'example.org', 'example.net'} for m in EMAIL.finditer(line)):
                labels.append('non-example email')
            if labels:
                # Do not echo potentially sensitive content.
                problems.append(f'{rel.as_posix()}:{number}: {", ".join(labels)}')
    if problems:
        print('\n'.join(problems))
        raise SystemExit(1)
    print(f'Public-source checks passed: {count} files inspected.')


if __name__ == '__main__':
    main()
