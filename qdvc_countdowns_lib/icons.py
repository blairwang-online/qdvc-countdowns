"""The set of selectable icons for a countdown.

These are standard freedesktop / theme icon names. The list is kept sorted
alphabetically (as required by the icon-picker dropdown). This module has no
GTK dependency so the list can be reused by any front-end.
"""
from __future__ import annotations

# 4 required + 12 additional, all standard icon-theme names, sorted A-Z.
ICON_NAMES: list[str] = sorted([
    # required four
    "dialog-warning",
    "emblem-generic",
    "emblem-important",
    "face-cool",
    # twelve more
    "appointment-soon",
    "emblem-default",
    "emblem-favorite",
    "emblem-urgent",
    "face-smile",
    "flag-red",
    "mail-mark-important",
    "media-playback-start",
    "office-calendar",
    "starred",
    "task-due",
    "user-away",
])

# Sentinel for "no icon".
NO_ICON = ""
