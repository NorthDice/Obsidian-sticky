import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib, WebKit2

from markdown_renderer import render_html


class NoteEditor(Gtk.Box):
    def __init__(self, on_changed, on_key_press, on_save_and_refresh=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._content = ""
        self._editable = True
        self._suppress = False
        self._external_changed = on_changed
        self._external_key_press = on_key_press
        self._on_save_and_refresh = on_save_and_refresh

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(120)

        # --- Read mode: WebView ---
        self._web_scroll = Gtk.ScrolledWindow()
        self._web_scroll.set_name("webview-scroll")
        self._web_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._web_scroll.set_shadow_type(Gtk.ShadowType.NONE)

        self._webview = WebKit2.WebView()
        self._webview.set_name("webview")
        bg = Gdk.RGBA()
        bg.parse("rgba(0,0,0,0)")
        self._webview.set_background_color(bg)

        # Disable context menu and navigation
        settings = self._webview.get_settings()
        settings.set_enable_javascript(False)
        settings.set_enable_developer_extras(False)

        self._webview.connect("button-press-event", self._on_webview_click)
        self._webview.connect("key-press-event", self._on_read_key_press)
        self._web_scroll.add(self._webview)
        self._stack.add_named(self._web_scroll, "read")

        # --- Edit mode: TextView ---
        self._edit_scroll = Gtk.ScrolledWindow()
        self._edit_scroll.set_name("editor-scroll")
        self._edit_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._edit_scroll.set_shadow_type(Gtk.ShadowType.NONE)

        self._textview = Gtk.TextView()
        self._textview.set_name("textview")
        self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._textview.set_left_margin(14)
        self._textview.set_right_margin(14)
        self._textview.set_top_margin(10)
        self._textview.set_bottom_margin(10)

        self._buf = self._textview.get_buffer()
        self._buf.connect("changed", self._on_buffer_changed)
        self._textview.connect("key-press-event", self._on_edit_key_press)
        self._textview.connect("focus-out-event", self._on_focus_out)

        self._edit_scroll.add(self._textview)
        self._stack.add_named(self._edit_scroll, "edit")

        self.pack_start(self._stack, True, True, 0)

        # Start in read mode
        self._stack.set_visible_child_name("read")

    @property
    def mode(self):
        return self._stack.get_visible_child_name()

    def load(self, content):
        """Load content (raw markdown). Renders in current mode."""
        self._content = content
        if self.mode == "read":
            self._render_webview()
        else:
            self._suppress = True
            self._buf.set_text(content)
            self._suppress = False

    def get_content(self):
        """Return raw markdown content."""
        if self.mode == "edit":
            start = self._buf.get_start_iter()
            end = self._buf.get_end_iter()
            self._content = self._buf.get_text(start, end, True)
        return self._content

    def set_editable(self, enabled):
        self._editable = enabled
        self._textview.set_editable(enabled)

    def switch_to_edit(self):
        """Enter edit mode."""
        if not self._editable:
            return
        if self.mode == "edit":
            return
        self._suppress = True
        self._buf.set_text(self._content)
        self._suppress = False
        self._stack.set_visible_child_name("edit")
        self._textview.grab_focus()

    def switch_to_read(self):
        """Exit edit mode → save content and render HTML."""
        if self.mode == "read":
            return
        # Capture current text
        start = self._buf.get_start_iter()
        end = self._buf.get_end_iter()
        self._content = self._buf.get_text(start, end, True)
        self._stack.set_visible_child_name("read")
        self._render_webview()
        # Notify save callback
        if self._on_save_and_refresh:
            self._on_save_and_refresh()

    def _render_webview(self):
        html = render_html(self._content)
        self._webview.load_html(html, None)

    # --- Signals ---

    def _on_buffer_changed(self, buf):
        if self._suppress:
            return
        self._external_changed(buf)

    def _on_webview_click(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.switch_to_edit()
            return True
        return False

    def _on_edit_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.switch_to_read()
            return True
        return self._external_key_press(widget, event)

    def _on_read_key_press(self, widget, event):
        """Forward key presses in read mode (Ctrl+S, Ctrl+Tab, etc.)."""
        return self._external_key_press(widget, event)

    def _on_focus_out(self, widget, event):
        # Only switch if we're still in edit mode and the focus went
        # outside of this editor entirely
        GLib.idle_add(self._check_focus_out)
        return False

    def _check_focus_out(self):
        focused = self._textview.has_focus()
        if not focused and self.mode == "edit":
            self.switch_to_read()
        return False
