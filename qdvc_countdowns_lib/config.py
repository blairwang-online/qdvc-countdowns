"""Application configuration, stored in an XDG config file.

Toolkit-agnostic. Config lives at::

    $XDG_CONFIG_HOME/qdvc-countdowns/config.ini
    (default $XDG_CONFIG_HOME = ~/.config)
"""
from __future__ import annotations

import configparser
import os

CONFIG_DIR_NAME = "qdvc-countdowns"
CONFIG_FILE_NAME = "config.ini"

# Toolbar style values.
TOOLBAR_STYLE_BELOW = "labels-below"   # labels below icons
TOOLBAR_STYLE_BESIDE = "labels-beside"  # labels beside icons

DEFAULTS = {
    "general": {
        "last_file": "",
        "reopen_last_file": "true",
    },
    "ui": {
        "toolbar_style": TOOLBAR_STYLE_BELOW,
        "confirm_delete": "true",
        "show_past_countdowns": "true",
    },
}


def config_dir() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, CONFIG_DIR_NAME)


def config_path() -> str:
    return os.path.join(config_dir(), CONFIG_FILE_NAME)


class Config:
    """Thin wrapper around :class:`configparser.ConfigParser`."""

    def __init__(self) -> None:
        self._parser = configparser.ConfigParser()
        # seed defaults
        for section, values in DEFAULTS.items():
            self._parser[section] = dict(values)
        self.load()

    def load(self) -> None:
        path = config_path()
        if os.path.exists(path):
            self._parser.read(path, encoding="utf-8")
        # Make sure any missing keys fall back to defaults.
        for section, values in DEFAULTS.items():
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            for key, value in values.items():
                if not self._parser.has_option(section, key):
                    self._parser.set(section, key, value)

    def save(self) -> None:
        os.makedirs(config_dir(), exist_ok=True)
        with open(config_path(), "w", encoding="utf-8") as fh:
            self._parser.write(fh)

    # ---- typed accessors ----------------------------------------------
    def get(self, section: str, key: str) -> str:
        return self._parser.get(section, key)

    def get_bool(self, section: str, key: str) -> bool:
        return self._parser.getboolean(section, key)

    def set(self, section: str, key: str, value) -> None:
        if isinstance(value, bool):
            value = "true" if value else "false"
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, str(value))

    # ---- convenience properties ---------------------------------------
    @property
    def toolbar_style(self) -> str:
        return self.get("ui", "toolbar_style")

    @toolbar_style.setter
    def toolbar_style(self, value: str) -> None:
        self.set("ui", "toolbar_style", value)

    @property
    def last_file(self) -> str:
        return self.get("general", "last_file")

    @last_file.setter
    def last_file(self, value: str) -> None:
        self.set("general", "last_file", value)

    @property
    def reopen_last_file(self) -> bool:
        return self.get_bool("general", "reopen_last_file")

    @property
    def confirm_delete(self) -> bool:
        return self.get_bool("ui", "confirm_delete")

    @property
    def show_past_countdowns(self) -> bool:
        return self.get_bool("ui", "show_past_countdowns")
