# Obsidian Sticky

A lightweight GTK3 desktop widget that displays Obsidian vault notes as floating sticky notes on your Linux desktop.

## Features

- **Dual-mode rendering**: WebKit2 HTML view for reading, plain TextView for editing
- **Full Markdown support**: headings, bold/italic, tables, code blocks, lists, horizontal rules
- **Obsidian-flavored Markdown**: callouts (`> [!tip]`), highlights (`==text==`), YAML frontmatter stripping
- **Desktop widget**: borderless, transparent, always-on-desktop window
- **Auto-save**: changes saved automatically after 1.5 seconds of inactivity
- **External file polling**: detects changes made in Obsidian and refreshes the widget
- **Multi-note navigation**: Ctrl+Tab / Ctrl+Shift+Tab to cycle through notes
- **Pin/unpin**: toggle between always-below (desktop widget) and normal window

## Requirements

- Python 3.10+
- GTK 3.0
- WebKit2 4.1 (`gir1.2-webkit2-4.1`)
- python-markdown (`pip install markdown`)

### Install dependencies (Ubuntu/Debian)

```bash
sudo apt install gir1.2-webkit2-4.1 python3-gi python3-gi-cairo gir1.2-gtk-3.0
pip install markdown
```

## Installation

```bash
bash install.sh
```

Creates a `.desktop` shortcut in the app menu and on the desktop.

### Uninstall

```bash
bash uninstall.sh
```

Removes the shortcuts from the app menu and desktop.

## Usage

```bash
bash start.sh
```

Or run directly:

```bash
python3 obsidian_sticky.py
```

Click the **+** button to add `.md` files from your Obsidian vault.

### Controls panel

| Action | Shortcut | 
|---|---|
| Save | Ctrl+S |
| Next note | Ctrl+Tab |
| Previous note | Ctrl+Shift+Tab |
| Enter edit mode | Double-click on note |
| Exit edit mode | Escape or click outside |

## Architecture

```
obsidian_sticky.py          # Entry point
config.py                   # Persistent config (~/.obsidian_sticky_v2.json)
note_manager.py             # Note loading, saving, navigation, file polling
markdown_renderer.py        # Markdown → HTML conversion with custom extensions
ui/
  window.py                 # Main StickyWindow (Gtk.Window)
  header.py                 # Header bar with title, pin, close buttons
  note_editor.py            # Dual-mode editor (WebView read / TextView edit)
  footer.py                 # Footer with navigation and resize grip
  styles.py                 # GTK CSS theming (dark palette)
```

## Testing

```bash
python3 -m pytest tests/ -v
```