import json
import base64
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, GLib, WebKit2

from markdown_renderer import (
    render_html, split_into_blocks, render_block, render_html_inline_edit
)


class NoteEditor(Gtk.Box):
    def __init__(self, on_changed, on_key_press, on_save_and_refresh=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self._content = ""
        self._blocks = []
        self._editable = True
        self._editing_index = -1
        self._external_changed = on_changed
        self._external_key_press = on_key_press
        self._on_save_and_refresh = on_save_and_refresh

        content_manager = WebKit2.UserContentManager()
        content_manager.register_script_message_handler("blockEdit")
        content_manager.connect("script-message-received::blockEdit", self._on_block_edit)

        self._webview = WebKit2.WebView.new_with_user_content_manager(content_manager)
        self._webview.set_name("webview")
        bg = Gdk.RGBA()
        bg.parse("rgba(0,0,0,0)")
        self._webview.set_background_color(bg)

        settings = self._webview.get_settings()
        settings.set_enable_javascript(True)
        settings.set_enable_developer_extras(False)

        self._webview.connect("context-menu", lambda *a: True)
        self._webview.connect("decide-policy", self._on_decide_policy)
        self._webview.connect("key-press-event", self._on_key_press_event)

        scroll = Gtk.ScrolledWindow()
        scroll.set_name("webview-scroll")
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_shadow_type(Gtk.ShadowType.NONE)
        scroll.add(self._webview)

        self.pack_start(scroll, True, True, 0)

    @property
    def mode(self):
        return "read"

    @property
    def is_editing(self):
        return self._editing_index >= 0

    def load(self, content):
        self._content = content
        self._blocks = split_into_blocks(content)
        self._editing_index = -1
        html = render_html_inline_edit(self._blocks)
        self._webview.load_html(html, None)

    def get_content(self):
        return self._content

    def set_editable(self, enabled):
        self._editable = enabled

    def switch_to_edit(self):
        pass

    def switch_to_read(self):
        pass

    def _rebuild_content(self):
        parts = []
        for i, block in enumerate(self._blocks):
            if i == 0 and block.startswith('---'):
                parts.append(block)
            else:
                parts.append(block)
        self._content = '\n\n'.join(parts)

    def _on_block_edit(self, manager, js_result):
        try:
            msg = json.loads(js_result.get_js_value().to_string())
        except (ValueError, AttributeError):
            return

        msg_type = msg.get('type')
        index = msg.get('index', -1)

        if msg_type == 'autosave':
            self._editing_index = index
            if 0 <= index < len(self._blocks):
                self._blocks[index] = msg['content']
                self._rebuild_content()
                if self._on_save_and_refresh:
                    self._on_save_and_refresh()

        elif msg_type == 'done':
            if 0 <= index < len(self._blocks):
                self._blocks[index] = msg['content']
                self._rebuild_content()
                # Re-render just that block in the webview
                html_fragment = render_block(msg['content'])
                encoded = base64.b64encode(html_fragment.encode('utf-8')).decode('ascii')
                js = (
                    f'(function() {{'
                    f'  var div = document.querySelector(\'.md-block[data-index="{index}"]\');'
                    f'  if (div) {{'
                    f'    div.innerHTML = atob("{encoded}");'
                    f'    div.classList.remove("editing");'
                    f'  }}'
                    f'  window._blocks[{index}] = {json.dumps(msg["content"])};'
                    f'  window._blockHtml[{index}] = atob("{encoded}");'
                    f'}})()'
                )
                self._webview.run_javascript(js, None, None, None)
                if self._on_save_and_refresh:
                    self._on_save_and_refresh()
            self._editing_index = -1

        elif msg_type == 'shortcut':
            key = msg.get('key')
            if key == 'save':
                self._rebuild_content()
                if self._on_save_and_refresh:
                    self._on_save_and_refresh()
            elif key == 'next':
                self._fake_key_press(Gdk.KEY_Tab, Gdk.ModifierType.CONTROL_MASK)
            elif key == 'prev':
                self._fake_key_press(Gdk.KEY_ISO_Left_Tab,
                                     Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)

    def _fake_key_press(self, keyval, state):
        event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
        event.keyval = keyval
        event.state = state
        event.window = self._webview.get_window()
        self._external_key_press(self._webview, event)

    def _on_key_press_event(self, widget, event):
        return self._external_key_press(widget, event)

    def _on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            nav = decision.get_navigation_action()
            req = nav.get_request()
            uri = req.get_uri()
            if uri and not uri.startswith("about:"):
                decision.ignore()
                return True
        return False
