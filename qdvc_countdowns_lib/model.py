"""Core data model for a single countdown.

This module is deliberately free of any GTK dependency.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum


class Category(Enum):
    """The category of a countdown.

    The ``value`` is the human-readable label; it is also what is written
    to the CSV file, so changing these strings changes the on-disk format.
    """

    DEADLINE_INTERNAL = "Deadline (internal)"
    DEADLINE_EXTERNAL = "Deadline (external)"
    EVENT = "Event"

    @classmethod
    def from_label(cls, label: str) -> "Category":
        for member in cls:
            if member.value == label:
                return member
        raise ValueError(f"Unknown category label: {label!r}")

    @classmethod
    def labels(cls) -> list[str]:
        return [member.value for member in cls]


DATE_FORMAT = "%Y-%m-%d"


def parse_date(text: str) -> datetime.date:
    """Parse a YYYY-MM-DD string into a :class:`datetime.date`."""
    return datetime.datetime.strptime(text.strip(), DATE_FORMAT).date()


def format_date(value: datetime.date) -> str:
    """Format a :class:`datetime.date` as YYYY-MM-DD."""
    return value.strftime(DATE_FORMAT)


@dataclass
class Countdown:
    """A single countdown entry.

    Attributes:
        date: The target date.
        name: Human-readable name.
        category: One of the :class:`Category` members.
        icon: A freedesktop icon name, or "" if none is set.
    """

    date: datetime.date
    name: str
    category: Category
    icon: str = ""

    def days_remaining(self, today: datetime.date | None = None) -> int:
        """Whole days from ``today`` (default: real today) to the target.

        Negative values mean the date is in the past.
        """
        if today is None:
            today = datetime.date.today()
        return (self.date - today).days

    def countdown_label(self, today: datetime.date | None = None) -> str:
        """The countdown rendered as a string, e.g. ``"3 days"``."""
        return f"{self.days_remaining(today)} days"

    # ---- serialisation helpers (CSV row <-> object) --------------------
    def to_row(self) -> dict[str, str]:
        return {
            "date": format_date(self.date),
            "name": self.name,
            "category": self.category.value,
            "icon": self.icon,
        }

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Countdown":
        return cls(
            date=parse_date(row["date"]),
            name=row.get("name", "").strip(),
            category=Category.from_label(row["category"].strip()),
            icon=row.get("icon", "").strip(),
        )
