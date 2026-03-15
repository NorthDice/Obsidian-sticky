# CLAUDE.md

## Project Overview

Obsidian Sticky is a GTK3 desktop widget for displaying Obsidian vault markdown notes as floating sticky notes on Linux. It uses WebKit2 for rendered HTML reading view and Gtk.TextView for raw markdown editing.

## Build & Run

```bash
python3 obsidian_sticky.py
```

No build step. Pure Python + GTK3 bindings.

## Dependencies

- Python 3.10+, GTK 3.0, WebKit2 4.1 (gi bindings)
- `markdown` (pip package, v3.5.2) with extensions: `extra`, `sane_lists`, `admonition`

## Tests

```bash
python3 -m pytest tests/ -v          # all tests
python3 -m pytest tests/ -v -k test_markdown  # just markdown renderer tests
```

Tests use `pytest`. No GTK display required for non-UI tests — markdown renderer and config/note_manager are tested without a display server.

## Code Structure

- `obsidian_sticky.py` — entry point, creates StickyWindow and runs Gtk.main()
- `config.py` — `ConfigManager`: JSON config at `~/.obsidian_sticky_v2.json`
- `note_manager.py` — `NoteManager`: file I/O, navigation, external change polling
- `markdown_renderer.py` — `render_html(md_text) -> str`: markdown → full HTML document
- `ui/window.py` — `StickyWindow`: main window, wires up all components
- `ui/note_editor.py` — `NoteEditor`: Gtk.Stack with WebView (read) + TextView (edit)
- `ui/header.py` — `HeaderBar`: title, add/pin/close buttons, drag-to-move
- `ui/footer.py` — `FooterBar`: navigation arrows, counter, remove button, resize grip
- `ui/styles.py` — `PALETTE` dict + `apply_css()`: dark theme CSS for all GTK widgets

## Key Patterns

- `NoteEditor` has a `_content` field as single source of truth for raw markdown
- Mode switching: double-click WebView → edit; Escape or focus-out → read
- Auto-save triggers 1.5s after last edit via `GLib.timeout_add`
- External file changes detected by mtime polling every 3s
- Markdown renderer uses singleton `markdown.Markdown` instance (call `.reset()` before each render)
- PALETTE in `ui/styles.py` is imported by `markdown_renderer.py` for consistent theming

## Style Notes

- No type annotations in existing code — don't add them
- Minimal comments — code is self-explanatory
- Private methods/attributes prefixed with `_`
- GTK widget names set via `set_name()` for CSS targeting
