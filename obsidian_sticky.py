#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ui.window import StickyWindow

widget = StickyWindow()
widget.connect("destroy", Gtk.main_quit)
widget.show_all()
Gtk.main()
