"""QDVC Countdowns library package.

Modules prefixed with ``gtk3_`` contain GTK 3 specific code and are the
only place that imports ``gi``/``Gtk``. Everything else is toolkit-agnostic
application logic, so that a future GTK 4 port can replace only the
``gtk3_*`` modules.
"""

APP_ID = "org.qdvc.Countdowns"
APP_NAME = "QDVC Countdowns"
APP_VERSION = "1.0.0"

# The program name used for the X11 WM_CLASS. This MUST match the
# ``StartupWMClass`` line in the .desktop launcher for the MATE panel to
# associate the running window with the launcher (and thus show the right
# icon rather than a generic one). See MAINTENANCE.md.
WM_CLASS = "qdvc-countdowns"

# A standard freedesktop themed icon, present on a typical GNOME/MATE
# install, so no icon file needs to be bundled or installed. Used as both
# the default icon and the per-window icon.
ICON_NAME = "appointment-soon"
