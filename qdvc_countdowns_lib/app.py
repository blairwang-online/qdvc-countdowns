"""Application bootstrap.

This module ties together the toolkit-agnostic pieces (config, store) and
the GTK 3 front-end. It is the only non-``gtk3_`` module that imports a
``gtk3_`` module, and it is intentionally small so that swapping in a GTK 4
front-end later means changing only this file plus the ``gtk3_*`` modules.
"""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .config import Config
from .storage import CountdownStore
from .gtk3_mainwindow import MainWindow


def main() -> int:
    config = Config()
    store = CountdownStore()

    # Optionally reopen the last used file.
    if config.reopen_last_file and config.last_file:
        if os.path.exists(config.last_file):
            try:
                store.open_file(config.last_file)
            except Exception:  # noqa: BLE001
                pass  # start with no file if it cannot be read

    window = MainWindow(store, config)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
    return 0
