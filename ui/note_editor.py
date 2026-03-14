import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from markdown_renderer import MarkdownRenderer


class NoteEditor(Gtk.ScrolledWindow):
    def __init__(self, on_changed, on_key_press):
        super().__init__()
        self.set_name("editor-scroll")
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_shadow_type(Gtk.ShadowType.NONE)

        self._suppress = False

        self._textview = Gtk.TextView()
        self._textview.set_name("textview")
        self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._textview.set_left_margin(14)
        self._textview.set_right_margin(14)
        self._textview.set_top_margin(10)
        self._textview.set_bottom_margin(10)

        self._buf = self._textview.get_buffer()
        self._renderer = MarkdownRenderer(self._buf)

        self._buf.connect("changed", self._changed_proxy(on_changed))
        self._textview.connect("key-press-event", on_key_press)

        self.add(self._textview)

    def _changed_proxy(self, on_changed):
        def handler(buf):
            if not self._suppress:
                on_changed(buf)
        return handler

    def load(self, content):
        self._suppress = True
        self._renderer.render(content)
        self._suppress = False

    def get_content(self):
        start = self._buf.get_start_iter()
        end = self._buf.get_end_iter()
        return self._buf.get_text(start, end, False)

    def set_editable(self, enabled):
        self._textview.set_editable(enabled)
