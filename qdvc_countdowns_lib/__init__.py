"""QDVC Countdowns library package.

Modules prefixed with ``gtk3_`` contain GTK 3 specific code and are the
only place that imports ``gi``/``Gtk``. Everything else is toolkit-agnostic
application logic, so that a future GTK 4 port can replace only the
``gtk3_*`` modules.
"""

APP_ID = "org.qdvc.Countdowns"
APP_NAME = "QDVC Countdowns"
APP_VERSION = "1.0.0"
