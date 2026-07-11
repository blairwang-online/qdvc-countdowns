"""GTK 3 create/edit dialog for a single countdown.

GTK-specific. Provides :class:`CountdownDialog`, used for both creating a
new countdown and editing an existing one (same form).
"""
from __future__ import annotations

import datetime

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .icons import ICON_NAMES  # noqa: E402
from .model import Category, Countdown, format_date  # noqa: E402

ICON_PIXEL_SIZE = 16


class CountdownDialog(Gtk.Dialog):
    """A modal dialog for creating or editing a :class:`Countdown`.

    Pass ``countdown=None`` to create; pass an existing one to edit.
    """

    def __init__(self, parent: Gtk.Window, countdown: Countdown | None = None):
        title = "Edit Countdown" if countdown else "New Countdown"
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_default_size(480, -1)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("_Save", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        # Two-column layout: form fields on the left, an always-visible
        # calendar on the right.
        columns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18,
                          margin=12)
        self.get_content_area().add(columns)

        # ---- LEFT column: Name / Category / Icon ----------------------
        left = Gtk.Grid(row_spacing=8, column_spacing=8)
        left.set_valign(Gtk.Align.START)
        columns.pack_start(left, True, True, 0)

        left.attach(self._label("Name:"), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry(hexpand=True)
        self.name_entry.set_activates_default(True)
        left.attach(self.name_entry, 1, 0, 1, 1)

        left.attach(self._label("Category:"), 0, 1, 1, 1)
        self.category_combo = Gtk.ComboBoxText(hexpand=True)
        for label in Category.labels():
            self.category_combo.append_text(label)
        self.category_combo.set_active(0)
        left.attach(self.category_combo, 1, 1, 1, 1)

        left.attach(self._label("Icon:"), 0, 2, 1, 1)
        self.icon_combo = self._build_icon_combo()
        self.icon_combo.set_hexpand(True)
        left.attach(self.icon_combo, 1, 2, 1, 1)

        # ---- RIGHT column: always-visible calendar --------------------
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_valign(Gtk.Align.START)
        columns.pack_start(right, False, False, 0)

        right.pack_start(self._label("Date:"), False, False, 0)
        self.calendar = Gtk.Calendar()
        self.calendar.connect("day-selected", self._on_day_selected)
        right.pack_start(self.calendar, False, False, 0)
        # Live YYYY-MM-DD readout beneath the calendar.
        self.date_label = Gtk.Label(xalign=0.0)
        right.pack_start(self.date_label, False, False, 0)

        # --- populate for edit, or defaults for create ------------------
        if countdown is not None:
            self._load(countdown)
        else:
            self._set_date(datetime.date.today())

        self.show_all()

    # ---- widget builders ----------------------------------------------
    @staticmethod
    def _label(text: str) -> Gtk.Label:
        lbl = Gtk.Label(label=text, xalign=0.0)
        return lbl

    def _build_icon_combo(self) -> Gtk.ComboBox:
        # ListStore columns: icon-name (str), display-name (str)
        store = Gtk.ListStore(str, str)
        store.append(["", "(none)"])
        for name in ICON_NAMES:
            store.append([name, name])
        combo = Gtk.ComboBox.new_with_model(store)

        renderer_icon = Gtk.CellRendererPixbuf()
        renderer_icon.set_property("stock-size", Gtk.IconSize.MENU)
        combo.pack_start(renderer_icon, False)
        combo.add_attribute(renderer_icon, "icon-name", 0)

        renderer_text = Gtk.CellRendererText()
        combo.pack_start(renderer_text, True)
        combo.add_attribute(renderer_text, "text", 1)

        combo.set_active(0)
        self._icon_store = store
        return combo

    # ---- date helpers --------------------------------------------------
    def _on_day_selected(self, _calendar: Gtk.Calendar) -> None:
        self.date_label.set_text(format_date(self._get_date()))

    def _get_date(self) -> datetime.date:
        year, month, day = self.calendar.get_date()
        # GtkCalendar months are 0-based.
        return datetime.date(year, month + 1, day)

    def _set_date(self, value: datetime.date) -> None:
        self.calendar.select_month(value.month - 1, value.year)
        self.calendar.select_day(value.day)
        self.date_label.set_text(format_date(value))

    # ---- load / read ---------------------------------------------------
    def _load(self, countdown: Countdown) -> None:
        self.name_entry.set_text(countdown.name)
        self._set_date(countdown.date)
        labels = Category.labels()
        self.category_combo.set_active(labels.index(countdown.category.value))
        self._select_icon(countdown.icon)

    def _select_icon(self, icon_name: str) -> None:
        for i, row in enumerate(self._icon_store):
            if row[0] == icon_name:
                self.icon_combo.set_active(i)
                return
        self.icon_combo.set_active(0)

    def get_countdown(self) -> Countdown:
        """Build a :class:`Countdown` from the current field values."""
        it = self.icon_combo.get_active_iter()
        icon = self._icon_store[it][0] if it is not None else ""
        return Countdown(
            date=self._get_date(),
            name=self.name_entry.get_text().strip(),
            category=Category.from_label(self.category_combo.get_active_text()),
            icon=icon,
        )
