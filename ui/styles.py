import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

PALETTE = {
    "BG": "#1e1e1e",
    "HEADER": "#1e1e1e",
    "TEXT": "#dcddde",
    "ACCENT": "#7c3aed",
    "ACCENT_LIGHT": "#a78bfa",
    "BORDER": "rgba(255,255,255,0.06)",
    "SEP": "rgba(255,255,255,0.08)",
    "COUNTER": "#6e6e6e",
    "ARROW": "#888888",
    "CLOSE_HOVER": "#e53e3e",
    "REMOVE_HOVER": "#e53e3e",
    "REMOVE": "#555555",
}


def build_css():
    p = PALETTE
    return f"""
    #sticky-window,
    #sticky-window * {{
        border: none;
        box-shadow: none;
        outline: none;
        background-image: none;
        border-image: none;
    }}
    #sticky-window {{
        background-color: transparent;
    }}
    #main-box {{
        background-color: {p['BG']};
        border-radius: 10px;
        border: 1px solid {p['BORDER']};
    }}
    #header, #footer {{
        background-color: transparent;
    }}
    #note-title {{
        font-size: 9.5pt;
        font-weight: 600;
        color: {p['TEXT']};
    }}
    scrolledwindow, #editor-scroll,
    scrolledwindow overshoot, scrolledwindow undershoot,
    scrolledwindow junction {{
        background-color: transparent;
    }}
    #textview, #textview text {{
        background-color: transparent;
        color: {p['TEXT']};
        font-size: 10.5pt;
        font-family: 'Ubuntu', 'Noto Sans', sans-serif;
    }}
    #counter {{
        font-size: 9pt;
        color: {p['COUNTER']};
    }}
    #btn-arrow {{
        font-size: 15pt;
        padding: 0 8px;
        color: {p['ARROW']};
        min-width: 0;
        min-height: 0;
        background-color: transparent;
    }}
    #btn-arrow:hover {{ color: {p['ACCENT']}; }}
    #btn-close {{
        font-size: 10pt;
        padding: 1px 5px;
        color: #666;
        min-width: 0;
        min-height: 0;
        background-color: transparent;
    }}
    #btn-close:hover {{
        color: {p['CLOSE_HOVER']};
        background-color: rgba(229,62,62,0.13);
        border-radius: 5px;
    }}
    #btn-add {{
        font-size: 14pt;
        padding: 0 4px;
        color: {p['ACCENT']};
        min-width: 0;
        min-height: 0;
        background-color: transparent;
    }}
    #btn-add:hover {{
        background-color: rgba(124,58,237,0.15);
        border-radius: 5px;
    }}
    #btn-remove {{
        font-size: 10pt;
        padding: 0;
        color: {p['REMOVE']};
        min-width: 0;
        min-height: 0;
        background-color: transparent;
    }}
    #btn-remove:hover {{ color: {p['REMOVE_HOVER']}; }}
    #obs-icon {{ font-size: 14pt; color: {p['ACCENT']}; }}
    #btn-pin {{
        font-size: 11pt;
        padding: 0 4px;
        color: #555;
        min-width: 0;
        min-height: 0;
        background-color: transparent;
    }}
    #btn-pin:hover {{ color: {p['ACCENT_LIGHT']}; }}
    """.encode()


def apply_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(build_css())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
