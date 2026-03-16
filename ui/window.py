import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
import cairo
from gi.repository import Gtk, Gdk, GLib

from config import ConfigManager
from note_manager import NoteManager
from ui.styles import apply_css
from ui.header import HeaderBar
from ui.footer import FooterBar
from ui.note_editor import NoteEditor

_RESIZE_BORDER = 8
_EDGE_CURSORS = {
    Gdk.WindowEdge.NORTH_WEST: "nw-resize",
    Gdk.WindowEdge.NORTH_EAST: "ne-resize",
    Gdk.WindowEdge.SOUTH_WEST: "sw-resize",
    Gdk.WindowEdge.SOUTH_EAST: "se-resize",
    Gdk.WindowEdge.WEST: "w-resize",
    Gdk.WindowEdge.EAST: "e-resize",
    Gdk.WindowEdge.NORTH: "n-resize",
    Gdk.WindowEdge.SOUTH: "s-resize",
}


class StickyWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._auto_save_id = None
        self._pinned = True

        self._setup_window()
        apply_css()
        self._build_ui()

        self._note_manager = NoteManager(
            self._config,
            self._on_note_loaded,
            self._on_no_notes,
        )
        self._note_manager.load_current()

        GLib.timeout_add_seconds(3, self._note_manager.poll_external_changes)
        self._setup_edge_resize()
        self.connect("draw", self._on_draw)

    def _on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False

    def _setup_edge_resize(self):
        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("motion-notify-event", self._on_edge_motion)
        self.connect("button-press-event", self._on_edge_press)
        self.connect("leave-notify-event", self._on_edge_leave)

    def _get_edge(self, x, y):
        w, h = self.get_size()
        b = _RESIZE_BORDER
        left = x < b
        right = x > w - b
        top = y < b
        bottom = y > h - b
        if top and left:    return Gdk.WindowEdge.NORTH_WEST
        if top and right:   return Gdk.WindowEdge.NORTH_EAST
        if bottom and left: return Gdk.WindowEdge.SOUTH_WEST
        if bottom and right:return Gdk.WindowEdge.SOUTH_EAST
        if left:            return Gdk.WindowEdge.WEST
        if right:           return Gdk.WindowEdge.EAST
        if top:             return Gdk.WindowEdge.NORTH
        if bottom:          return Gdk.WindowEdge.SOUTH
        return None

    def _on_edge_motion(self, widget, event):
        edge = self._get_edge(event.x, event.y)
        gdk_win = self.get_window()
        if not gdk_win:
            return
        if edge is not None:
            cursor = Gdk.Cursor.new_from_name(Gdk.Display.get_default(), _EDGE_CURSORS[edge])
        else:
            cursor = None
        gdk_win.set_cursor(cursor)

    def _on_edge_leave(self, widget, event):
        gdk_win = self.get_window()
        if gdk_win:
            gdk_win.set_cursor(None)

    def _on_edge_press(self, widget, event):
        if event.button != 1:
            return False
        edge = self._get_edge(event.x, event.y)
        if edge is not None:
            self.begin_resize_drag(edge, event.button, int(event.x_root), int(event.y_root), event.time)
            return True
        return False

    def _setup_window(self):
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_resizable(True)
        self.set_keep_below(True)
        self.set_app_paintable(True)
        self.stick()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.set_default_size(self._config.width, self._config.height)
        self.move(self._config.x, self._config.y)
        self.set_opacity(self._config.opacity)

    def _build_ui(self):
        self.set_name("sticky-window")
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_name("main-box")
        main_box.set_spacing(0)
        self.add(main_box)

        self._ui_visible = True
        self._header = HeaderBar(self._on_add_note, self._on_pin_toggle, self._on_close, self._on_toggle_ui)
        self._header.connect_drag(self)
        main_box.pack_start(self._header, False, False, 0)

        self._editor = NoteEditor(self._on_text_changed, self._on_key_press, self._save_and_refresh)
        main_box.pack_start(self._editor, True, True, 0)

        self._footer = FooterBar(self._on_prev, self._on_next, self._on_remove_note)
        main_box.pack_start(self._footer, False, False, 0)

    def _on_toggle_ui(self, btn):
        self._ui_visible = not self._ui_visible
        self._header.set_ui_visible(self._ui_visible)
        self._footer.set_visible(self._ui_visible)

    def _on_pin_toggle(self, btn):
        self._pinned = not self._pinned
        self.set_keep_below(self._pinned)
        if not self._pinned:
            self.set_keep_above(False)
        self._header.set_pinned(self._pinned)

    def _on_note_loaded(self, path, content, index, total):
        if self._editor.is_editing:
            return

        if self._auto_save_id:
            GLib.source_remove(self._auto_save_id)
            self._auto_save_id = None

        name = os.path.basename(path).replace(".md", "")
        self._header.set_title(name)
        self._footer.update(index, total)
        self._footer.set_navigable(total > 1)
        self._editor.set_editable(True)
        self._editor.load(content)

    def _on_no_notes(self):
        self._header.set_title("No notes")
        self._footer._counter.set_text("")
        self._footer.set_navigable(False)
        self._editor.set_editable(False)
        self._editor.load("Press ＋ to add notes from your Obsidian vault")

    def _on_text_changed(self, buf):
        if self._auto_save_id:
            GLib.source_remove(self._auto_save_id)
        self._auto_save_id = GLib.timeout_add(1500, self._auto_save)

    def _save_and_refresh(self):
        """Called when switching from edit → read mode."""
        self._note_manager.save_current(self._editor.get_content())

    def _auto_save(self):
        self._note_manager.save_current(self._editor.get_content())
        self._auto_save_id = None
        return False

    def _on_key_press(self, widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval == Gdk.KEY_s:
            self._note_manager.save_current(self._editor.get_content())
            return True
        if ctrl and event.keyval == Gdk.KEY_Tab:
            self._note_manager.navigate_to(1, self._editor.get_content())
            return True
        if ctrl and event.keyval == Gdk.KEY_ISO_Left_Tab:
            self._note_manager.navigate_to(-1, self._editor.get_content())
            return True
        return False

    def _on_add_note(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Add notes from Obsidian vault",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           "Add", Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        f = Gtk.FileFilter()
        f.set_name("Markdown (*.md)")
        f.add_pattern("*.md")
        dialog.add_filter(f)
        notes = self._config.notes
        if notes:
            dialog.set_filename(notes[0])

        if dialog.run() == Gtk.ResponseType.OK:
            self._note_manager.add_notes(dialog.get_filenames())
        dialog.destroy()

    def _on_remove_note(self, btn):
        self._note_manager.remove_current()

    def _on_prev(self, btn):
        self._note_manager.navigate_to(-1, self._editor.get_content())

    def _on_next(self, btn):
        self._note_manager.navigate_to(1, self._editor.get_content())

    def _on_close(self, btn):
        self._note_manager.save_current(self._editor.get_content())
        self._save_window_state()
        Gtk.main_quit()

    def _save_window_state(self):
        x, y = self.get_position()
        w, h = self.get_size()
        self._config.update_window_state(x, y, w, h)

    def do_configure_event(self, event):
        self._config._data["width"] = event.width
        self._config._data["height"] = event.height
        self._save_window_state()
        return Gtk.Window.do_configure_event(self, event)
