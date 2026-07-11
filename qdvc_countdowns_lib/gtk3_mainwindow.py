"""GTK 3 main application window.

GTK-specific. Wires the toolkit-agnostic :class:`CountdownStore` and
:class:`Config` to a menubar, toolbar and a sortable table view.
"""
from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from . import APP_NAME, APP_VERSION, ICON_NAME
from .config import (Config, TOOLBAR_STYLE_BESIDE)  # noqa: E402
from .storage import CountdownStore  # noqa: E402
from .gtk3_dialog import CountdownDialog  # noqa: E402
from .gtk3_preferences import PreferencesDialog  # noqa: E402

# ListStore column indices for the tree model.
COL_ICON = 0        # icon name (str) for pixbuf renderer
COL_NAME = 1        # str
COL_DATE = 2        # str YYYY-MM-DD
COL_COUNTDOWN = 3   # display str, e.g. "3 days"
COL_CATEGORY = 4    # str
COL_DAYS = 5        # int, hidden, used for correct numeric sorting
COL_INDEX = 6       # int, index back into the store's item list


class MainWindow(Gtk.Window):
    def __init__(self, store: CountdownStore, config: Config):
        super().__init__(title=APP_NAME)
        self.store = store
        self.config = config

        # Set the window icon explicitly (in addition to the app-wide
        # default set in app.py) so the window/taskbar shows the themed
        # icon even before any .desktop launcher association. The MATE
        # panel association additionally relies on the WM_CLASS set via
        # GLib.set_prgname matching the launcher's StartupWMClass.
        self.set_icon_name(ICON_NAME)

        self.set_default_size(720, 480)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self.on_delete_event)

        self._action_widgets: list[Gtk.Widget] = []

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.menubar = self._build_menubar()
        vbox.pack_start(self.menubar, False, False, 0)

        self.toolbar = self._build_toolbar()
        vbox.pack_start(self.toolbar, False, False, 0)

        self.treeview = self._build_treeview()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.treeview)
        vbox.pack_start(scrolled, True, True, 0)

        self.statusbar = Gtk.Statusbar()
        self._status_ctx = self.statusbar.get_context_id("main")
        vbox.pack_start(self.statusbar, False, False, 0)

        self.apply_toolbar_style()
        self.refresh()

    # ==================================================================
    # Menubar
    # ==================================================================
    def _build_menubar(self) -> Gtk.MenuBar:
        menubar = Gtk.MenuBar()

        # ---- File ----
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="_File", use_underline=True)
        file_item.set_submenu(file_menu)

        self.mi_new = self._menu_item(
            file_menu, "New\u2026", "document-new",
            Gdk.KEY_n, Gdk.ModifierType.CONTROL_MASK, self.on_new)
        self.mi_open = self._menu_item(
            file_menu, "Open\u2026", "document-open",
            Gdk.KEY_o, Gdk.ModifierType.CONTROL_MASK, self.on_open)
        self.mi_close = self._menu_item(
            file_menu, "Close", "window-close",
            Gdk.KEY_w, Gdk.ModifierType.CONTROL_MASK, self.on_close_file,
            needs_file=True)
        file_menu.append(Gtk.SeparatorMenuItem())
        self.mi_save = self._menu_item(
            file_menu, "Save", "document-save",
            Gdk.KEY_s, Gdk.ModifierType.CONTROL_MASK, self.on_save,
            needs_file=True)
        file_menu.append(Gtk.SeparatorMenuItem())
        self._menu_item(
            file_menu, "Quit", "application-exit",
            Gdk.KEY_q, Gdk.ModifierType.CONTROL_MASK, self.on_quit)
        menubar.append(file_item)

        # ---- Edit ----
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="_Edit", use_underline=True)
        edit_item.set_submenu(edit_menu)

        self.mi_add = self._menu_item(
            edit_menu, "Add Countdown\u2026", "list-add",
            Gdk.KEY_a, Gdk.ModifierType.CONTROL_MASK, self.on_add,
            needs_file=True)
        self.mi_edit = self._menu_item(
            edit_menu, "Edit Countdown\u2026", "document-edit",
            Gdk.KEY_e, Gdk.ModifierType.CONTROL_MASK, self.on_edit,
            needs_file=True)
        self.mi_delete = self._menu_item(
            edit_menu, "Delete Countdown", "list-remove",
            Gdk.KEY_Delete, 0, self.on_delete, needs_file=True)
        edit_menu.append(Gtk.SeparatorMenuItem())
        self._menu_item(
            edit_menu, "Preferences\u2026", "preferences-system",
            Gdk.KEY_comma, Gdk.ModifierType.CONTROL_MASK, self.on_preferences)
        menubar.append(edit_item)

        # ---- Help ----
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="_Help", use_underline=True)
        help_item.set_submenu(help_menu)
        self._menu_item(help_menu, "About", "help-about",
                        Gdk.KEY_F1, 0, self.on_about)
        menubar.append(help_item)

        return menubar

    def _menu_item(self, menu, label, icon_name, key, mods, callback,
                   needs_file=False) -> Gtk.MenuItem:
        """Build an image menu item, wire accelerator + callback."""
        item = Gtk.ImageMenuItem(label=label, use_underline=True)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            item.set_image(img)
            item.set_always_show_image(True)
        item.connect("activate", callback)
        if key:
            item.add_accelerator("activate", self.accel_group, key, mods,
                                 Gtk.AccelFlags.VISIBLE)
        menu.append(item)
        if needs_file:
            self._action_widgets.append(item)
        return item

    # ==================================================================
    # Toolbar
    # ==================================================================
    def _build_toolbar(self) -> Gtk.Toolbar:
        tb = Gtk.Toolbar()

        def add(icon, text, callback, needs_file=False):
            btn = Gtk.ToolButton()
            btn.set_icon_name(icon)
            btn.set_label(text)
            btn.set_is_important(True)
            btn.connect("clicked", callback)
            tb.insert(btn, -1)
            if needs_file:
                self._action_widgets.append(btn)
            return btn

        add("document-new", "New", self.on_new)
        add("document-open", "Open", self.on_open)
        add("document-save", "Save", self.on_save, needs_file=True)
        tb.insert(Gtk.SeparatorToolItem(), -1)
        add("list-add", "Add", self.on_add, needs_file=True)
        add("document-edit", "Edit", self.on_edit, needs_file=True)
        add("list-remove", "Delete", self.on_delete, needs_file=True)
        return tb

    def apply_toolbar_style(self) -> None:
        if self.config.toolbar_style == TOOLBAR_STYLE_BESIDE:
            self.toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        else:
            self.toolbar.set_style(Gtk.ToolbarStyle.BOTH)

    # ==================================================================
    # Tree view
    # ==================================================================
    def _build_treeview(self) -> Gtk.TreeView:
        # icon, name, date, countdown, category, days(int), index(int)
        self.model = Gtk.ListStore(str, str, str, str, str, int, int)
        view = Gtk.TreeView(model=self.model)
        view.set_rules_hint(True)

        # Icon + Name in one column so the icon sits next to the name.
        col_name = Gtk.TreeViewColumn("Name")
        r_icon = Gtk.CellRendererPixbuf()
        r_icon.set_property("stock-size", Gtk.IconSize.MENU)
        col_name.pack_start(r_icon, False)
        col_name.add_attribute(r_icon, "icon-name", COL_ICON)
        r_name = Gtk.CellRendererText()
        col_name.pack_start(r_name, True)
        col_name.add_attribute(r_name, "text", COL_NAME)
        col_name.set_sort_column_id(COL_NAME)
        col_name.set_resizable(True)
        col_name.set_expand(True)
        view.append_column(col_name)

        self._text_column("Date", COL_DATE, COL_DATE, view)
        # Countdown displays COL_COUNTDOWN but sorts on COL_DAYS (numeric).
        self._text_column("Countdown", COL_COUNTDOWN, COL_DAYS, view)
        self._text_column("Category", COL_CATEGORY, COL_CATEGORY, view)

        view.connect("row-activated", self.on_row_activated)
        view.get_selection().connect("changed", self.on_selection_changed)
        return view

    def _text_column(self, title, display_col, sort_col, view):
        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(title, renderer, text=display_col)
        col.set_sort_column_id(sort_col)
        col.set_resizable(True)
        view.append_column(col)
        return col

    # ==================================================================
    # Data refresh
    # ==================================================================
    def refresh(self) -> None:
        self.model.clear()
        if self.store.is_open:
            show_past = self.config.show_past_countdowns
            for index, cd in enumerate(self.store.items):
                days = cd.days_remaining()
                if not show_past and days < 0:
                    continue
                self.model.append([
                    cd.icon or None,
                    cd.name,
                    cd.date.strftime("%Y-%m-%d"),
                    cd.countdown_label(),
                    cd.category.value,
                    days,
                    index,
                ])
        self._update_sensitivity()
        self._update_title()
        self._update_status()

    def _update_sensitivity(self) -> None:
        enabled = self.store.is_open
        for w in self._action_widgets:
            w.set_sensitive(enabled)
        # Edit/Delete additionally need a selection.
        has_sel = self._selected_index() is not None
        for w in (self.mi_edit, self.mi_delete):
            w.set_sensitive(enabled and has_sel)

    def _update_title(self) -> None:
        if self.store.is_open:
            name = os.path.basename(self.store.path)
            dirty = "*" if self.store.dirty else ""
            self.set_title(f"{dirty}{name} \u2014 {APP_NAME}")
        else:
            self.set_title(APP_NAME)

    def _update_status(self) -> None:
        self.statusbar.pop(self._status_ctx)
        if self.store.is_open:
            n = len(self.store.items)
            msg = f"{n} countdown(s) \u2014 {self.store.path}"
        else:
            msg = "No file open. Use File \u25b8 Open or File \u25b8 New."
        self.statusbar.push(self._status_ctx, msg)

    # ==================================================================
    # Selection helpers
    # ==================================================================
    def _selected_index(self) -> int | None:
        model, treeiter = self.treeview.get_selection().get_selected()
        if treeiter is None:
            return None
        return model[treeiter][COL_INDEX]

    def on_selection_changed(self, _selection) -> None:
        self._update_sensitivity()

    def on_row_activated(self, _view, _path, _column) -> None:
        self.on_edit(None)

    # ==================================================================
    # File actions
    # ==================================================================
    def on_new(self, _widget) -> None:
        if not self._confirm_discard():
            return
        dialog = Gtk.FileChooserDialog(
            title="New Countdown File", transient_for=self,
            action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL,
                           "_Create", Gtk.ResponseType.OK)
        dialog.set_current_name("countdowns.csv")
        dialog.set_do_overwrite_confirmation(True)
        self._add_csv_filter(dialog)
        if dialog.run() == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            if not path.lower().endswith(".csv"):
                path += ".csv"
            self.store.new_file(path)
            self.config.last_file = path
            self.config.save()
            self.refresh()
        dialog.destroy()

    def on_open(self, _widget) -> None:
        if not self._confirm_discard():
            return
        dialog = Gtk.FileChooserDialog(
            title="Open Countdown File", transient_for=self,
            action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL,
                           "_Open", Gtk.ResponseType.OK)
        self._add_csv_filter(dialog)
        if dialog.run() == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            try:
                self.store.open_file(path)
                self.config.last_file = path
                self.config.save()
            except Exception as exc:  # noqa: BLE001
                self._error(f"Could not open file:\n{exc}")
            self.refresh()
        dialog.destroy()

    def on_close_file(self, _widget) -> None:
        if not self._confirm_discard():
            return
        self.store.close_file()
        self.refresh()

    def on_save(self, _widget) -> None:
        if not self.store.is_open:
            return
        try:
            self.store.save()
        except Exception as exc:  # noqa: BLE001
            self._error(f"Could not save file:\n{exc}")
        self.refresh()

    def _add_csv_filter(self, dialog) -> None:
        f_csv = Gtk.FileFilter()
        f_csv.set_name("CSV files")
        f_csv.add_pattern("*.csv")
        dialog.add_filter(f_csv)
        f_all = Gtk.FileFilter()
        f_all.set_name("All files")
        f_all.add_pattern("*")
        dialog.add_filter(f_all)

    # ==================================================================
    # Edit actions
    # ==================================================================
    def on_add(self, _widget) -> None:
        if not self.store.is_open:
            return
        dialog = CountdownDialog(self, None)
        if dialog.run() == Gtk.ResponseType.OK:
            cd = dialog.get_countdown()
            if cd.name:
                self.store.add(cd)
                self.store.save()
                self.refresh()
        dialog.destroy()

    def on_edit(self, _widget) -> None:
        index = self._selected_index()
        if index is None:
            return
        current = self.store.get(index)
        dialog = CountdownDialog(self, current)
        if dialog.run() == Gtk.ResponseType.OK:
            cd = dialog.get_countdown()
            if cd.name:
                self.store.replace(index, cd)
                self.store.save()
                self.refresh()
        dialog.destroy()

    def on_delete(self, _widget) -> None:
        index = self._selected_index()
        if index is None:
            return
        if self.config.confirm_delete:
            cd = self.store.get(index)
            dialog = Gtk.MessageDialog(
                transient_for=self, modal=True,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Delete countdown \u201c{cd.name}\u201d?")
            resp = dialog.run()
            dialog.destroy()
            if resp != Gtk.ResponseType.YES:
                return
        self.store.remove(index)
        self.store.save()
        self.refresh()

    def on_preferences(self, _widget) -> None:
        dialog = PreferencesDialog(self, self.config)
        if dialog.run() == Gtk.ResponseType.OK:
            dialog.apply()
            self.apply_toolbar_style()
            self.refresh()
        dialog.destroy()

    # ==================================================================
    # Help / quit
    # ==================================================================
    def on_about(self, _widget) -> None:
        about = Gtk.AboutDialog(transient_for=self, modal=True)
        about.set_program_name(APP_NAME)
        about.set_version(APP_VERSION)
        about.set_comments("Keep track of your countdowns.")
        about.set_logo_icon_name("appointment-soon")
        about.run()
        about.destroy()

    def on_quit(self, _widget) -> None:
        if self._confirm_discard():
            Gtk.main_quit()

    def on_delete_event(self, _widget, _event) -> bool:
        if self._confirm_discard():
            Gtk.main_quit()
            return False
        return True  # stop the delete, stay open

    # ==================================================================
    # Utilities
    # ==================================================================
    def _confirm_discard(self) -> bool:
        """Return True if it is safe to proceed (no unsaved changes or user
        chose to discard/save)."""
        if not (self.store.is_open and self.store.dirty):
            return True
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.WARNING,
            text="Save changes before continuing?")
        dialog.add_buttons("Discard", Gtk.ResponseType.NO,
                           "_Cancel", Gtk.ResponseType.CANCEL,
                           "_Save", Gtk.ResponseType.YES)
        resp = dialog.run()
        dialog.destroy()
        if resp == Gtk.ResponseType.YES:
            self.on_save(None)
            return True
        if resp == Gtk.ResponseType.NO:
            return True
        return False

    def _error(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=message)
        dialog.run()
        dialog.destroy()
