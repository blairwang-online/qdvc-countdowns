"""GTK 3 Preferences dialog.

GTK-specific. Reads from and writes to a
:class:`qdvc_countdowns_lib.config.Config` instance.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .config import Config, TOOLBAR_STYLE_BELOW, TOOLBAR_STYLE_BESIDE  # noqa: E402


class PreferencesDialog(Gtk.Dialog):
    """Edit application preferences.

    On :data:`Gtk.ResponseType.OK` the values are written back into the
    supplied config object and saved to disk.
    """

    def __init__(self, parent: Gtk.Window, config: Config):
        super().__init__(title="Preferences", transient_for=parent, modal=True)
        self._config = config
        self.set_default_size(380, -1)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_OK", Gtk.ResponseType.OK)

        grid = Gtk.Grid(row_spacing=10, column_spacing=10, margin=12)
        self.get_content_area().add(grid)
        row = 0

        # --- Toolbar style ---------------------------------------------
        grid.attach(Gtk.Label(label="Toolbar style:", xalign=0.0), 0, row, 1, 1)
        self.toolbar_combo = Gtk.ComboBoxText()
        # Keep parallel arrays of value <-> label.
        self._toolbar_values = [TOOLBAR_STYLE_BELOW, TOOLBAR_STYLE_BESIDE]
        self.toolbar_combo.append_text("Labels below icons")
        self.toolbar_combo.append_text("Labels beside icons")
        self.toolbar_combo.set_active(
            self._toolbar_values.index(config.toolbar_style)
            if config.toolbar_style in self._toolbar_values else 0
        )
        grid.attach(self.toolbar_combo, 1, row, 1, 1)
        row += 1

        # --- Confirm delete --------------------------------------------
        self.confirm_delete_check = Gtk.CheckButton(
            label="Confirm before deleting a countdown")
        self.confirm_delete_check.set_active(config.confirm_delete)
        grid.attach(self.confirm_delete_check, 0, row, 2, 1)
        row += 1

        # --- Show past countdowns --------------------------------------
        self.show_past_check = Gtk.CheckButton(
            label="Show countdowns whose date has passed")
        self.show_past_check.set_active(config.show_past_countdowns)
        grid.attach(self.show_past_check, 0, row, 2, 1)
        row += 1

        # --- Reopen last file ------------------------------------------
        self.reopen_check = Gtk.CheckButton(
            label="Reopen last file on startup")
        self.reopen_check.set_active(config.reopen_last_file)
        grid.attach(self.reopen_check, 0, row, 2, 1)
        row += 1

        self.show_all()

    def apply(self) -> None:
        """Persist the chosen values into the config object."""
        idx = self.toolbar_combo.get_active()
        if idx >= 0:
            self._config.toolbar_style = self._toolbar_values[idx]
        self._config.set("ui", "confirm_delete",
                         self.confirm_delete_check.get_active())
        self._config.set("ui", "show_past_countdowns",
                         self.show_past_check.get_active())
        self._config.set("general", "reopen_last_file",
                         self.reopen_check.get_active())
        self._config.save()
