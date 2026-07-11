"""CSV persistence for countdown collections.

Toolkit-agnostic. The on-disk format is a CSV file with a header row:

    date,name,category,icon

``date`` is YYYY-MM-DD and ``category`` is a human-readable label matching
:class:`qdvc_countdowns_lib.model.Category` values.
"""
from __future__ import annotations

import csv
import os

from .model import Countdown

FIELDNAMES = ["date", "name", "category", "icon"]


class CountdownStore:
    """An in-memory collection of countdowns backed by a CSV file.

    The store tracks a "dirty" flag so the UI can prompt before losing
    unsaved changes.
    """

    def __init__(self) -> None:
        self._path: str | None = None
        self._items: list[Countdown] = []
        self._dirty = False

    # ---- open/close/save ----------------------------------------------
    @property
    def path(self) -> str | None:
        return self._path

    @property
    def is_open(self) -> bool:
        return self._path is not None

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def items(self) -> list[Countdown]:
        return list(self._items)

    def new_file(self, path: str) -> None:
        """Create and open a brand new (empty) CSV file at ``path``."""
        self._path = path
        self._items = []
        self._dirty = False
        self.save()

    def open_file(self, path: str) -> None:
        """Load countdowns from ``path`` and make it the current file."""
        items: list[Countdown] = []
        with open(path, "r", newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if not row.get("date"):
                    continue
                items.append(Countdown.from_row(row))
        self._path = path
        self._items = items
        self._dirty = False

    def close_file(self) -> None:
        self._path = None
        self._items = []
        self._dirty = False

    def save(self) -> None:
        """Write the current collection back to disk."""
        if self._path is None:
            raise RuntimeError("No file is open")
        tmp = self._path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
            writer.writeheader()
            for item in self._items:
                writer.writerow(item.to_row())
        os.replace(tmp, self._path)
        self._dirty = False

    # ---- mutation ------------------------------------------------------
    def add(self, countdown: Countdown) -> None:
        self._items.append(countdown)
        self._dirty = True

    def replace(self, index: int, countdown: Countdown) -> None:
        self._items[index] = countdown
        self._dirty = True

    def remove(self, index: int) -> None:
        del self._items[index]
        self._dirty = True

    def get(self, index: int) -> Countdown:
        return self._items[index]
