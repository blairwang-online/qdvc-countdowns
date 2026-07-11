# QDVC Countdowns

A small GTK 3 desktop application for keeping track of different kinds of
countdowns — internal deadlines, external deadlines and events.

## Features

- Sortable table of countdowns (by **Name**, **Date**, **Countdown** or
  **Category**). The *Countdown* column sorts numerically, so `2 days`
  correctly sorts before `10 days`.
- Each countdown has a date, name, category and an optional 16×16 icon shown
  beside its name.
- Create and edit countdowns through the same form, with a calendar date
  picker and an icon-picker dropdown.
- Countdown collections are stored in plain **CSV** files that you can open
  and close from the **File** menu — keep separate files for separate
  collections.
- Menubar **and** toolbar with keyboard shortcuts.
- **Edit ▸ Preferences** for toolbar style (labels below vs. beside icons)
  and other options.
- Configuration is stored in an XDG config file
  (`$XDG_CONFIG_HOME/qdvc-countdowns/config.ini`).

## Requirements

- Python 3.10+
- GTK 3 and PyGObject

On Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

On Fedora:

```bash
sudo dnf install python3-gobject gtk3
```

## Running

```bash
python3 qdvc_countdowns.py
```

All actions are disabled until you open or create a CSV file via
**File ▸ New…** or **File ▸ Open…**.

## Installing a `.desktop` launcher

Create `~/.local/share/applications/qdvc-countdowns.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=QDVC Countdowns
Comment=Keep track of your countdowns
Exec=python3 /full/path/to/qdvc_countdowns.py
Icon=appointment-soon
Terminal=false
Categories=Utility;Office;
```

Replace `/full/path/to/` with the real location of the checkout. The chosen
icon, **`appointment-soon`**, is a standard freedesktop icon-theme name that
suits a countdown/deadline application and needs no bundled image file.

Then refresh the desktop database:

```bash
update-desktop-database ~/.local/share/applications
```

## CSV format

```csv
date,name,category,icon
2026-07-20,Quarterly report,Deadline (internal),task-due
2026-08-01,Product launch,Event,office-calendar
```

`date` is `YYYY-MM-DD`; `category` is one of `Deadline (internal)`,
`Deadline (external)` or `Event`; `icon` is a freedesktop icon name or empty.
