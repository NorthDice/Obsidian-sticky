import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango


class MarkdownRenderer:
    def __init__(self, buf):
        self._buf = buf
        self._tags = {}
        self._setup_tags()

    def _setup_tags(self):
        b = self._buf

        def tag(name, **props):
            t = b.create_tag(name)
            for k, v in props.items():
                t.set_property(k.replace("_", "-"), v)
            self._tags[name] = t

        tag("h1", size_points=18, weight=Pango.Weight.BOLD, foreground="#a78bfa")
        tag("h2", size_points=15, weight=Pango.Weight.BOLD, foreground="#a78bfa")
        tag("h3", size_points=12.5, weight=Pango.Weight.BOLD, foreground="#a78bfa")
        tag("bold", weight=Pango.Weight.BOLD)
        tag("italic", style=Pango.Style.ITALIC)
        tag("code_inline", family="monospace", background="#252526", foreground="#e6db74")
        tag("blockquote", foreground="#6a737d", style=Pango.Style.ITALIC, left_margin=18)
        tag("bullet", left_margin=18)
        tag("hr", foreground="#6e6e6e", strikethrough=True)

    def render(self, markdown_text):
        handler_id = self._buf.connect("changed", lambda *a: None)
        self._buf.disconnect(handler_id)

        changed_id = [None]

        def noop(*a):
            pass

        changed_id[0] = self._buf.connect("changed", noop)
        self._buf.set_text("")
        self._buf.disconnect(changed_id[0])

        lines = markdown_text.split("\n")
        for i, line in enumerate(lines):
            is_last = i == len(lines) - 1
            self._render_line(line, not is_last)

    def _render_line(self, line, add_newline):
        b = self._buf
        start_offset = b.get_end_iter().get_offset()

        block_tag = None
        text = line

        if line.startswith("### "):
            block_tag = "h3"
        elif line.startswith("## "):
            block_tag = "h2"
        elif line.startswith("# "):
            block_tag = "h1"
        elif line.startswith("> "):
            block_tag = "blockquote"
        elif line.strip() == "---":
            block_tag = "hr"
        elif re.match(r"^(\s*[-*+]|\s*\d+\.)\s", line):
            block_tag = "bullet"

        suffix = "\n" if add_newline else ""
        b.insert(b.get_end_iter(), text + suffix)

        end_offset = b.get_end_iter().get_offset()

        if block_tag:
            s = b.get_iter_at_offset(start_offset)
            e = b.get_iter_at_offset(end_offset)
            b.apply_tag(self._tags[block_tag], s, e)

        self._apply_inline(start_offset, text)

    def _apply_inline(self, line_start, text):
        b = self._buf

        def apply_spans(pattern, tag_name):
            for m in re.finditer(pattern, text):
                s = b.get_iter_at_offset(line_start + m.start())
                e = b.get_iter_at_offset(line_start + m.end())
                b.apply_tag(self._tags[tag_name], s, e)

        apply_spans(r"`[^`]+`", "code_inline")
        apply_spans(r"\*\*[^*]+\*\*|__[^_]+__", "bold")
        apply_spans(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)|(?<!_)_(?!_)([^_]+)(?<!_)_(?!_)", "italic")
