# MAINTENANCE.md — QDVC Countdowns

A technical manual for anyone (human or AI) maintaining this codebase.

## 1. Design goals

1. **Toolkit isolation.** All GTK 3 code lives in modules prefixed `gtk3_`.
   No other module imports `gi`/`Gtk`. This makes a future GTK 4 port a
   matter of rewriting the `gtk3_*` modules (and the one import line in
   `app.py`) without touching the data model, storage or config logic.
2. **Thin entry point.** `qdvc_countdowns.py` only imports and calls
   `qdvc_countdowns_lib.app.main`.
3. **Plain, inspectable storage.** Countdown data is CSV; configuration is an
   INI file in the XDG config directory. Both are human-editable.

## 2. Directory layout

```
qdvc_countdowns.py              Thin entry point.
qdvc_countdowns_lib/
    __init__.py                 Package metadata (APP_ID, APP_NAME, APP_VERSION).
    model.py                    Countdown dataclass, Category enum, date helpers.
    storage.py                  CountdownStore: CSV load/save + dirty tracking.
    config.py                   Config: XDG INI read/write, typed accessors.
    icons.py                    ICON_NAMES: the sorted 16-icon picker list.
    app.py                      Bootstrap: wires config+store to the GTK window.
    gtk3_mainwindow.py          Main window: menubar, toolbar, sortable table.
    gtk3_dialog.py              Create/Edit countdown dialog.
    gtk3_preferences.py         Preferences dialog.
```

**Rule of thumb:** if a file imports `gi`, its name must start with `gtk3_`
(the sole deliberate exception is `app.py`, the bootstrap seam).

## 3. Module responsibilities

### 3.1 `model.py` (toolkit-agnostic)
- `Category` — `Enum` whose `value` is the human label written to CSV.
  Changing a value changes the on-disk format; add a migration if you do.
- `Countdown` — a `@dataclass` with `date` (`datetime.date`), `name`,
  `category`, `icon`. Key methods:
  - `days_remaining(today=None)` → signed `int` (negative = past).
  - `countdown_label(today=None)` → e.g. `"3 days"`.
  - `to_row()` / `from_row()` — CSV row dict serialisation.
- `parse_date` / `format_date` enforce the `YYYY-MM-DD` (`DATE_FORMAT`)
  representation used everywhere outside the calendar widget.

### 3.2 `storage.py` (toolkit-agnostic)
- `CountdownStore` holds the in-memory list, the current file path and a
  `dirty` flag. `open_file`, `new_file`, `close_file`, `save`, plus
  `add`/`replace`/`remove`/`get`. Saving is atomic (write to `*.tmp`, then
  `os.replace`). Mutations set `dirty = True`; `save` clears it.
- `FIELDNAMES` defines the CSV header order.

### 3.3 `config.py` (toolkit-agnostic)
- `Config` wraps `configparser`. Path:
  `$XDG_CONFIG_HOME/qdvc-countdowns/config.ini` (default `~/.config`).
- `DEFAULTS` seeds every key so a missing/partial file always yields a
  complete config. Add new settings by (a) adding to `DEFAULTS`, and
  (b) optionally exposing a typed property.
- Toolbar-style constants: `TOOLBAR_STYLE_BELOW`, `TOOLBAR_STYLE_BESIDE`.

### 3.4 `icons.py` (toolkit-agnostic)
- `ICON_NAMES` — 16 freedesktop icon-theme names, kept **sorted**
  (the list is wrapped in `sorted(...)` so it self-corrects). The 4 required
  icons (`dialog-warning`, `emblem-generic`, `emblem-important`, `face-cool`)
  plus 12 more. To add icons, just extend the list.

### 3.5 `gtk3_mainwindow.py` (GTK)
The heart of the UI. Notable points:

- **Tree model columns** (`Gtk.ListStore`) — indices are named constants:
  `COL_ICON, COL_NAME, COL_DATE, COL_COUNTDOWN, COL_CATEGORY, COL_DAYS,
  COL_INDEX`.
  - `COL_ICON` feeds a `CellRendererPixbuf` via its `icon-name` property, so
    the icon renders next to the name in a single "Name" column. Empty icon =
    `None` = blank space (16×16 via `Gtk.IconSize.MENU`).
  - **Numeric countdown sort:** the *Countdown* column *displays*
    `COL_COUNTDOWN` (the `"N days"` string) but its `set_sort_column_id` is
    `COL_DAYS` (the hidden signed `int`). This is why `2 days` sorts before
    `10 days`. Do **not** point the sort at `COL_COUNTDOWN`.
  - `COL_INDEX` maps a table row back to its position in
    `store.items`, used by edit/delete.
- **Sensitivity gating:** every widget that requires an open file is
  appended to `self._action_widgets` at construction and toggled in
  `_update_sensitivity()`. Edit/Delete additionally require a selection.
  This implements "all functionality disabled unless a CSV file is open".
- **Menubar** built in `_build_menubar` via the `_menu_item` helper, which
  attaches an icon, a callback and an accelerator in one call. Shortcuts:
  New `Ctrl+N`, Open `Ctrl+O`, Close `Ctrl+W`, Save `Ctrl+S`, Quit `Ctrl+Q`,
  Add `Ctrl+A`, Edit `Ctrl+E`, Delete `Delete`, Preferences `Ctrl+,`,
  About `F1`.
- **Toolbar** is a subset of the menu actions (New, Open, Save | Add, Edit,
  Delete). `apply_toolbar_style()` maps the config value to
  `Gtk.ToolbarStyle.BOTH` (labels below) or `BOTH_HORIZ` (labels beside).
- **Unsaved-changes guard:** `_confirm_discard()` is called before New, Open,
  Close and Quit, and from the window `delete-event`.
- Window is centred via `Gtk.WindowPosition.CENTER`.

### 3.6 `gtk3_dialog.py` (GTK)
- `CountdownDialog` serves both create (pass `countdown=None`) and edit.
- Date is chosen with a `Gtk.Calendar` inside a `Gtk.Popover` behind a
  `Gtk.MenuButton`; the button label always shows the `YYYY-MM-DD` string.
  **Gotcha:** `Gtk.Calendar` months are **0-based**; conversions live in
  `_get_date`/`_set_date`.
- Icon picker is a `Gtk.ComboBox` over a 2-column `ListStore`
  (icon-name, display-name) with a pixbuf + text renderer; row 0 is
  `("", "(none)")`.
- `get_countdown()` reads the widgets back into a `Countdown`.

### 3.7 `gtk3_preferences.py` (GTK)
- `PreferencesDialog` edits: toolbar style, confirm-before-delete,
  show-past-countdowns, reopen-last-file. `apply()` writes to the `Config`
  and saves. The caller re-applies toolbar style and refreshes.

### 3.8 `app.py` (bootstrap seam)
- Creates `Config` and `CountdownStore`, optionally reopens the last file,
  constructs `MainWindow`, runs `Gtk.main()`.

## 4. Data flow

```
CSV file  ─open→  CountdownStore.items (list[Countdown])
                        │ refresh()
                        ▼
             Gtk.ListStore rows  ─→  Gtk.TreeView
                        ▲                    │ select
             add/edit/delete via CountdownDialog
                        │
                   store.save()  ─→  CSV file (atomic)
```

Every mutating action calls `store.save()` then `self.refresh()`, so the
table, window title (shows `*` when dirty), and statusbar stay in sync.

## 5. Testing

There is no GTK in headless CI, so test the toolkit-agnostic layer directly:

```bash
python3 -m py_compile qdvc_countdowns.py qdvc_countdowns_lib/*.py
python3 - <<'PY'
from qdvc_countdowns_lib.model import Countdown, Category, parse_date
import datetime
cd = Countdown(parse_date('2026-07-20'),'x',Category.EVENT,'')
assert cd.days_remaining(datetime.date(2026,7,11)) == 9
PY
```

`CountdownStore` and `Config` can be exercised against a `tempfile`
directory (set `XDG_CONFIG_HOME` to isolate config tests). GTK modules are
best smoke-tested manually.

## 6. How to make common changes

- **Add a category:** add a member to `Category`. It flows automatically into
  the dialog combo and the CSV. Old files lacking it are unaffected.
- **Add a preference:** add to `config.DEFAULTS`, add a widget +
  read/write line in `gtk3_preferences.py`, consume it where relevant.
- **Add a toolbar/menu action:** add via `_menu_item` and/or the toolbar
  `add()` helper; append to `_action_widgets` if it needs an open file.
- **Add an icon:** append to `icons.ICON_NAMES` (stays auto-sorted).
- **GTK 4 port:** rewrite the three `gtk3_*` modules and the two `gi` import
  lines in `app.py`. `model`, `storage`, `config`, `icons` should not change.

## 7. Known constraints / gotchas

- `Gtk.Calendar` months are 0-based (see `gtk3_dialog.py`).
- `Gtk.ImageMenuItem` and `Gtk.Toolbar` are deprecated in GTK 3 but are the
  idiomatic GTK-3 choices; they disappear in GTK 4 (that is the porting work).
- Save is atomic per file; there is no locking, so do not point two running
  instances at the same CSV.
- Icons rely on the active icon theme; unknown names simply render blank.
