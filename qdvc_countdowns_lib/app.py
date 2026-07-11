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
from gi.repository import GLib, Gtk  # noqa: E402

from . import ICON_NAME, WM_CLASS
from .config import Config
from .storage import CountdownStore
from .gtk3_mainwindow import MainWindow

# Set the program name at import time, before any window is created or
# realized. This fixes the X11 WM_CLASS to WM_CLASS so the MATE panel can
# associate the running window with the .desktop launcher (whose
# StartupWMClass must match). Doing this later has no effect once the
# display connection/window class is established.
GLib.set_prgname(WM_CLASS)


def main() -> int:
    config = Config()
    store = CountdownStore()

    # Ensure the themed icon is used for the window, taskbar and, together
    # with the matching .desktop StartupWMClass, the MATE panel.
    Gtk.Window.set_default_icon_name(ICON_NAME)

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
