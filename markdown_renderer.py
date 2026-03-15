import re
import markdown
from markdown.preprocessors import Preprocessor
from markdown.inlinepatterns import InlineProcessor
from xml.etree.ElementTree import Element

from ui.styles import PALETTE


class _StripFrontmatter(Preprocessor):
    """Remove YAML frontmatter (---...---) from the beginning of the document."""
    RE = re.compile(r'\A---\s*\n.*?\n---\s*\n', re.DOTALL)

    def run(self, lines):
        text = '\n'.join(lines)
        text = self.RE.sub('', text, count=1)
        return text.split('\n')


class _HighlightInline(InlineProcessor):
    """Convert ==text== to <mark>text</mark>."""
    def handleMatch(self, m, data):
        el = Element('mark')
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class _CalloutPreprocessor(Preprocessor):
    """Convert Obsidian callouts to python-markdown admonition syntax.

    > [!tip] Title     -->  !!! tip "Title"
    > content                   content
    """
    RE_CALLOUT = re.compile(r'^>\s*\[!(\w+)\]\s*(.*)')

    def run(self, lines):
        out = []
        i = 0
        while i < len(lines):
            m = self.RE_CALLOUT.match(lines[i])
            if m:
                kind = m.group(1).lower()
                title = m.group(2).strip()
                title_str = f' "{title}"' if title else ''
                out.append(f'!!! {kind}{title_str}')
                i += 1
                # Gather continuation lines ("> ..." or blank)
                while i < len(lines):
                    line = lines[i]
                    if line.startswith('> '):
                        out.append('    ' + line[2:])
                        i += 1
                    elif line.strip() == '>':
                        out.append('')
                        i += 1
                    else:
                        break
                out.append('')
            else:
                out.append(lines[i])
                i += 1
        return out


def _build_css():
    p = PALETTE
    return f"""
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    html, body {{
        background-color: {p['BG']};
        color: {p['TEXT']};
        font-family: 'Ubuntu', 'Noto Sans', sans-serif;
        font-size: 10.5pt;
        line-height: 1.6;
        padding: 10px 14px;
        overflow-wrap: break-word;
        word-wrap: break-word;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {p['ACCENT_LIGHT']};
        margin: 0.6em 0 0.3em 0;
        line-height: 1.3;
    }}
    h1 {{ font-size: 1.5em; }}
    h2 {{ font-size: 1.3em; }}
    h3 {{ font-size: 1.1em; }}
    a {{
        color: {p['ACCENT_LIGHT']};
        text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}
    strong {{ color: #e0e0e0; }}
    mark {{
        background-color: rgba(167,139,250,0.25);
        color: {p['TEXT']};
        padding: 1px 3px;
        border-radius: 3px;
    }}
    code {{
        background-color: #252526;
        color: #e6db74;
        padding: 2px 5px;
        border-radius: 3px;
        font-family: 'Ubuntu Mono', 'Fira Code', monospace;
        font-size: 0.92em;
    }}
    pre {{
        background-color: #1a1a1a;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        margin: 0.6em 0;
    }}
    pre code {{
        background-color: transparent;
        padding: 0;
        color: {p['TEXT']};
    }}
    blockquote {{
        border-left: 3px solid {p['ACCENT']};
        margin: 0.5em 0;
        padding: 4px 12px;
        color: #999;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 0.6em 0;
    }}
    th, td {{
        border: 1px solid rgba(255,255,255,0.12);
        padding: 6px 10px;
        text-align: left;
    }}
    th {{
        background-color: rgba(255,255,255,0.05);
        color: {p['ACCENT_LIGHT']};
        font-weight: 600;
    }}
    tr:nth-child(even) {{
        background-color: rgba(255,255,255,0.02);
    }}
    ul, ol {{
        padding-left: 1.8em;
        margin: 0.3em 0;
    }}
    li {{ margin: 0.15em 0; }}
    hr {{
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 1em 0;
    }}
    img {{
        max-width: 100%;
        border-radius: 4px;
    }}
    .admonition {{
        border-left: 3px solid {p['ACCENT']};
        background-color: rgba(124,58,237,0.08);
        padding: 8px 12px;
        margin: 0.6em 0;
        border-radius: 0 6px 6px 0;
    }}
    .admonition-title {{
        font-weight: 600;
        color: {p['ACCENT_LIGHT']};
        margin-bottom: 4px;
    }}
    input[type="checkbox"] {{
        margin-right: 6px;
    }}
    """


_md = None


def _get_md():
    global _md
    if _md is None:
        _md = markdown.Markdown(
            extensions=['extra', 'sane_lists', 'admonition'],
            output_format='html5',
        )
        # Register custom preprocessors / inline patterns
        _md.preprocessors.register(_StripFrontmatter(_md), 'strip_frontmatter', 40)
        _md.preprocessors.register(_CalloutPreprocessor(_md), 'callout', 35)
        _md.inlinePatterns.register(
            _HighlightInline(r'==(.*?)==', _md), 'highlight', 175
        )
    return _md


def render_html(markdown_text):
    """Convert markdown text to a full HTML document string."""
    md = _get_md()
    md.reset()
    body = md.convert(markdown_text)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{_build_css()}</style></head>
<body>{body}</body>
</html>"""
