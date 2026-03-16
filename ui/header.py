import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Pango

OBSIDIAN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="18" height="18">
  <polygon points="50,5 90,25 90,75 50,95 10,75 10,25" fill="#7C3AED" opacity="0.9"/>
  <polygon points="50,5 75,30 60,55 35,30" fill="#A78BFA"/>
  <polygon points="10,25 35,30 60,55 10,75" fill="#6D28D9"/>
  <polygon points="90,25 75,30 60,55 90,75" fill="#5B21B6"/>
  <polygon points="35,30 60,55 50,95 10,75" fill="#7C3AED"/>
  <polygon points="75,30 90,75 50,95 60,55" fill="#6D28D9"/>
</svg>"""


class HeaderBar(Gtk.Box):
    def __init__(self, on_add, on_pin, on_close, on_toggle_ui):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("header")
        self.set_margin_start(10)
        self.set_margin_end(6)
        self.set_margin_top(7)
        self.set_margin_bottom(7)

        self._icon = self._make_svg_image(OBSIDIAN_SVG)
        if self._icon:
            self._icon.set_valign(Gtk.Align.CENTER)
            self.pack_start(self._icon, False, False, 0)

        self._title = Gtk.Label(label="No note")
        self._title.set_name("note-title")
        self._title.set_ellipsize(Pango.EllipsizeMode.END)
        self._title.set_halign(Gtk.Align.START)
        self._title.set_valign(Gtk.Align.CENTER)
        self._title.set_margin_start(7)
        self._title.set_hexpand(True)
        self.pack_start(self._title, True, True, 0)

        self._btn_add = self._make_btn("＋", "Add notes from Obsidian vault", on_add)
        self._btn_add.set_name("btn-add")
        self._btn_add.set_valign(Gtk.Align.CENTER)
        self.pack_start(self._btn_add, False, False, 0)

        self._btn_pin = self._make_btn("◉", "Unpin from desktop", on_pin)
        self._btn_pin.set_name("btn-pin")
        self._btn_pin.set_valign(Gtk.Align.CENTER)
        self.pack_start(self._btn_pin, False, False, 0)

        self._btn_toggle = self._make_btn("👁", "Hide interface", on_toggle_ui)
        self._btn_toggle.set_name("btn-toggle")
        self._btn_toggle.set_valign(Gtk.Align.CENTER)
        self.pack_start(self._btn_toggle, False, False, 0)

        self._btn_close = self._make_btn("✕", "Close widget", on_close)
        self._btn_close.set_name("btn-close")
        self._btn_close.set_valign(Gtk.Align.CENTER)
        self.pack_start(self._btn_close, False, False, 2)

        self._hideable = [self._icon, self._title, self._btn_add, self._btn_pin]

    def set_ui_visible(self, visible):
        for w in self._hideable:
            if w:
                w.set_visible(visible)
        if visible:
            self._btn_toggle.set_label("👁")
            self._btn_toggle.set_tooltip_text("Hide interface")
        else:
            self._btn_toggle.set_label("👁‍🗨")
            self._btn_toggle.set_tooltip_text("Show interface")

    def set_title(self, name):
        self._title.set_text(name)

    def set_pinned(self, pinned):
        self._drag_locked = pinned
        if pinned:
            self._btn_pin.set_label("◉")
            self._btn_pin.set_tooltip_text("Unpin — allow moving and floating")
        else:
            self._btn_pin.set_label("○")
            self._btn_pin.set_tooltip_text("Pin to desktop — lock position")

    def connect_drag(self, window):
        self._drag_window = window
        self._drag_active = False
        self._drag_locked = True
        self._drag_x = 0
        self._drag_y = 0

        self._drag_area = Gtk.EventBox()
        self._drag_area.set_visible_window(False)
        self._drag_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )
        self._drag_area.connect("button-press-event", self._on_drag_begin)
        self._drag_area.connect("button-release-event", self._on_drag_end)
        self._drag_area.connect("motion-notify-event", self._on_drag_motion)

        parent = self._title.get_parent()
        parent.remove(self._title)
        self._drag_area.add(self._title)
        parent.pack_start(self._drag_area, True, True, 0)
        parent.reorder_child(self._drag_area, 1)

    def _on_drag_begin(self, widget, event):
        if event.button == 1 and not self._drag_locked:
            self._drag_active = True
            self._drag_x = event.x_root
            self._drag_y = event.y_root

    def _on_drag_end(self, widget, event):
        if event.button == 1 and self._drag_active:
            self._drag_active = False
            self._drag_window._save_window_state()

    def _on_drag_motion(self, widget, event):
        if self._drag_active:
            dx = event.x_root - self._drag_x
            dy = event.y_root - self._drag_y
            self._drag_x = event.x_root
            self._drag_y = event.y_root
            wx, wy = self._drag_window.get_position()
            self._drag_window.move(wx + int(dx), wy + int(dy))

    def _make_btn(self, label, tooltip, callback):
        btn = Gtk.Button(label=label)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", callback)
        return btn

    def _make_svg_image(self, svg_data):
        try:
            import tempfile
            from gi.repository import GdkPixbuf
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w") as f:
                f.write(svg_data)
                tmp = f.name
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp, 20, 20, True)
            os.unlink(tmp)
            return Gtk.Image.new_from_pixbuf(pixbuf)
        except Exception:
            lbl = Gtk.Label(label="⬡")
            lbl.set_name("obs-icon")
            return lbl
