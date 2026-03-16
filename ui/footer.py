import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk


class FooterBar(Gtk.Box):
    def __init__(self, on_prev, on_next, on_remove):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_name("footer")
        self.set_margin_start(8)
        self.set_margin_end(0)
        self.set_margin_top(4)
        self.set_margin_bottom(0)

        self._btn_prev = self._make_btn("←", "Previous note", on_prev)
        self._btn_prev.set_name("btn-arrow")
        self.pack_start(self._btn_prev, False, False, 0)

        self._counter = Gtk.Label(label="")
        self._counter.set_name("counter")
        self._counter.set_hexpand(True)
        self._counter.set_halign(Gtk.Align.CENTER)
        self.pack_start(self._counter, True, True, 0)

        self._btn_next = self._make_btn("→", "Next note", on_next)
        self._btn_next.set_name("btn-arrow")
        self.pack_start(self._btn_next, False, False, 0)

        self._btn_remove = self._make_btn("🗑", "Remove note from list", on_remove)
        self._btn_remove.set_name("btn-remove")
        self.pack_start(self._btn_remove, False, False, 4)

        grip = self._make_grip()
        self.pack_start(grip, False, False, 0)

    def update(self, index, total):
        self._counter.set_text(f"{index + 1} / {total}")

    def set_navigable(self, enabled):
        self._btn_prev.set_sensitive(enabled)
        self._btn_next.set_sensitive(enabled)

    def _make_btn(self, label, tooltip, callback):
        btn = Gtk.Button(label=label)
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", callback)
        return btn

    def _make_grip(self):
        grip = Gtk.EventBox()
        grip.set_size_request(16, 16)
        grip.set_tooltip_text("Resize")

        display = Gdk.Display.get_default()
        cursor = Gdk.Cursor.new_from_name(display, "se-resize")
        grip.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        grip.connect("enter-notify-event", lambda w, e: w.get_window() and w.get_window().set_cursor(cursor))
        grip.connect("leave-notify-event", lambda w, e: w.get_window() and w.get_window().set_cursor(None))
        grip.connect("button-press-event", self._on_grip_press)

        drawing = Gtk.DrawingArea()
        drawing.set_size_request(16, 16)
        drawing.connect("draw", self._draw_grip)
        grip.add(drawing)
        return grip

    def _on_grip_press(self, widget, event):
        window = self.get_toplevel()
        if isinstance(window, Gtk.Window):
            window.begin_resize_drag(
                Gdk.WindowEdge.SOUTH_EAST,
                event.button,
                int(event.x_root),
                int(event.y_root),
                event.time,
            )

    def _draw_grip(self, widget, cr):
        cr.set_source_rgba(0.43, 0.43, 0.43, 0.6)
        for i in range(3):
            for j in range(3):
                if i + j >= 2:
                    cr.arc(13 - i * 4, 13 - j * 4, 1.2, 0, 6.28)
                    cr.fill()
