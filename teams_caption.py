"""Teams caption snapshots: explicit attribution and identity across polls.

No model, network, or name guessing is used for the structured Teams protocol.
Unknown speakers remain unknown rather than inheriting the preceding person's name.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass

SCHEMA = "cue.teams.v1"
UNKNOWN = "未识别发言人"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join("".join(c if c.isalnum() or c.isspace() else " " for c in text).split())


@dataclass(frozen=True)
class Caption:
    id: str
    speaker: str | None
    text: str


def read_snapshot(raw: str) -> tuple[str, list[Caption]] | None:
    """Only consume our versioned protocol, never arbitrary JSON in speech."""
    if not raw.lstrip("\ufeff \r\n\t").startswith("{"):
        return None
    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        return None
    result = []
    for entry in data.get("entries", []):
        if not isinstance(entry, dict):
            continue
        words = str(entry.get("text") or "").strip()
        if not words:
            continue
        who = str(entry.get("speaker") or "").strip() or None
        result.append(Caption(str(entry.get("id") or ""), who, words))
    return str(data.get("window_key") or ""), result


class CaptionLedger:
    """An utterance is a row, not a globally unique piece of text.

    Two people saying 'Yes' must both survive. The same person saying it twice in
    two rows must also survive. Revisions only replace a row with a stable identity.
    """
    def __init__(self):
        self.entries: list[Caption] = []
        self._active: dict[tuple[str, str], int] = {}
        self._last_window = ""

    def accept(self, window: str, entries: list[Caption]) -> list[tuple[str, int, Caption]]:
        changes = []
        if self._last_window and window != self._last_window:
            # A new meeting must never revise an entry from the previous one.
            self._active.clear()
        self._last_window = window
        for item in entries:
            key = (window, item.id)
            index = self._active.get(key) if item.id else None
            if index is not None:
                previous = self.entries[index]
                if previous == item:
                    continue
                # Teams may recycle a visual row. A changed speaker or unrelated
                # sentence starts a new utterance; it must not overwrite history.
                old, new = normalize(previous.text), normalize(item.text)
                same_turn = (previous.speaker == item.speaker or (previous.speaker is None and item.speaker is not None)) and (
                    old == new or old.startswith(new) or new.startswith(old)
                    or _corrects(old, new)
                )
                if same_turn:
                    if old.startswith(new) and old != new:
                        continue
                    self.entries[index] = item
                    changes.append(("update", index, item))
                    continue
            index = len(self.entries)
            self.entries.append(item)
            if item.id:
                self._active[key] = index
            changes.append(("add", index, item))
        return changes


def _corrects(a: str, b: str) -> bool:
    import difflib
    # A one-word reply must never be fuzzy-merged with a different reply.
    return len(a) >= 16 and len(b) >= 16 and difflib.SequenceMatcher(None, a, b).ratio() >= .82
