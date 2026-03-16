import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from markdown_renderer import (
    split_into_blocks, render_block, render_html_inline_edit
)


class TestSplitIntoBlocks:
    def test_single_paragraph(self):
        blocks = split_into_blocks("Hello world")
        assert blocks == ["Hello world"]

    def test_two_paragraphs(self):
        blocks = split_into_blocks("First\n\nSecond")
        assert blocks == ["First", "Second"]

    def test_frontmatter_is_first_block(self):
        md = "---\ntitle: Test\n---\n\n# Heading"
        blocks = split_into_blocks(md)
        assert blocks[0].startswith("---")
        assert "title: Test" in blocks[0]
        assert blocks[1] == "# Heading"

    def test_fenced_code_block_stays_together(self):
        md = "Before\n\n```python\nprint('hi')\nprint('bye')\n```\n\nAfter"
        blocks = split_into_blocks(md)
        assert any("```python" in b and "print('bye')" in b for b in blocks)

    def test_empty_input(self):
        blocks = split_into_blocks("")
        assert blocks == [""]

    def test_multiple_blank_lines(self):
        blocks = split_into_blocks("A\n\n\n\nB")
        assert "A" in blocks
        assert "B" in blocks


class TestRenderBlock:
    def test_renders_heading(self):
        html = render_block("# Title")
        assert "<h1>Title</h1>" in html

    def test_renders_paragraph(self):
        html = render_block("Some text")
        assert "<p>Some text</p>" in html

    def test_renders_bold(self):
        html = render_block("**bold**")
        assert "<strong>bold</strong>" in html

    def test_renders_list(self):
        html = render_block("- item1\n- item2")
        assert "<ul>" in html
        assert "item1" in html

    def test_renders_code_block(self):
        html = render_block("```\ncode\n```")
        assert "<pre>" in html
        assert "code" in html

    def test_consecutive_renders_independent(self):
        h1 = render_block("# First")
        h2 = render_block("# Second")
        assert "First" in h1
        assert "Second" in h2
        assert "First" not in h2


class TestRenderHtmlInlineEdit:
    def test_returns_full_html(self):
        blocks = ["# Hello", "World"]
        html = render_html_inline_edit(blocks)
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html

    def test_contains_md_block_divs(self):
        blocks = ["# Hello", "World"]
        html = render_html_inline_edit(blocks)
        assert 'class="md-block"' in html
        assert 'data-index="0"' in html
        assert 'data-index="1"' in html

    def test_frontmatter_block_has_frontmatter_class(self):
        blocks = ["---\ntitle: T\n---", "# Heading"]
        html = render_html_inline_edit(blocks)
        assert 'class="md-block frontmatter"' in html

    def test_blocks_json_in_script(self):
        blocks = ["# Hello", "World"]
        html = render_html_inline_edit(blocks)
        assert "window._blocks" in html
        assert json.dumps(blocks) in html

    def test_block_html_array_present(self):
        blocks = ["# Hello", "World"]
        html = render_html_inline_edit(blocks)
        assert "window._blockHtml" in html

    def test_block_html_array_contains_rendered_fragments(self):
        blocks = ["# Hello", "**bold**"]
        html = render_html_inline_edit(blocks)
        # Extract the _blockHtml JSON from the script
        marker = "window._blockHtml = "
        start = html.index(marker) + len(marker)
        end = html.index(";\n", start)
        block_html = json.loads(html[start:end])
        assert len(block_html) == 2
        assert "<h1>Hello</h1>" in block_html[0]
        assert "<strong>bold</strong>" in block_html[1]

    def test_block_html_array_empty_for_frontmatter(self):
        blocks = ["---\ntitle: T\n---", "Text"]
        html = render_html_inline_edit(blocks)
        marker = "window._blockHtml = "
        start = html.index(marker) + len(marker)
        end = html.index(";\n", start)
        block_html = json.loads(html[start:end])
        assert block_html[0] == ""
        assert "<p>Text</p>" in block_html[1]

    def test_block_html_matches_div_content(self):
        blocks = ["# Title"]
        html = render_html_inline_edit(blocks)
        # The rendered fragment should appear both in the div and in _blockHtml
        marker = "window._blockHtml = "
        start = html.index(marker) + len(marker)
        end = html.index(";\n", start)
        block_html = json.loads(html[start:end])
        assert block_html[0] in html  # fragment is in the page body too

    def test_inline_edit_css_present(self):
        blocks = ["Hello"]
        html = render_html_inline_edit(blocks)
        assert ".md-block" in html
        assert ".block-textarea" in html
        assert ".editing" in html

    def test_inline_edit_js_present(self):
        blocks = ["Hello"]
        html = render_html_inline_edit(blocks)
        assert "startEdit" in html
        assert "finishEdit" in html
        assert "blockEdit" in html


class TestFinishEditJsRestoresHtml:
    """Verify that finishEdit() restores rendered HTML client-side."""

    def _get_js(self):
        blocks = ["Hello"]
        html = render_html_inline_edit(blocks)
        script_start = html.index("<script>") + len("<script>")
        script_end = html.index("</script>")
        return html[script_start:script_end]

    def test_finish_edit_restores_block_html(self):
        js = self._get_js()
        assert "window._blockHtml" in js
        assert "_blockHtml[index]" in js

    def test_finish_edit_removes_editing_class(self):
        js = self._get_js()
        # finishEdit should remove .editing class client-side
        assert "classList.remove('editing')" in js

    def test_finish_edit_sends_done_message(self):
        js = self._get_js()
        assert "'done'" in js
        assert "blockEdit.postMessage" in js

    def test_dblclick_handler_present(self):
        js = self._get_js()
        assert "dblclick" in js
        assert "startEdit" in js

    def test_autosave_debounce_present(self):
        js = self._get_js()
        assert "debounceTimer" in js
        assert "'autosave'" in js

    def test_escape_triggers_finish(self):
        js = self._get_js()
        assert "'Escape'" in js
        assert "finishEdit" in js

    def test_blur_triggers_finish(self):
        js = self._get_js()
        assert "'blur'" in js
        assert "finishEdit" in js


class TestNoteEditorMessageParsing:
    """Test that _on_block_edit uses get_js_value().to_string() correctly."""

    def test_source_uses_get_js_value(self):
        import inspect
        from ui.note_editor import NoteEditor
        source = inspect.getsource(NoteEditor._on_block_edit)
        assert "get_js_value().to_string()" in source
        assert "js_result.to_string()" not in source.replace(
            "js_result.get_js_value().to_string()", ""
        )

    def test_done_handler_updates_block_html(self):
        import inspect
        from ui.note_editor import NoteEditor
        source = inspect.getsource(NoteEditor._on_block_edit)
        assert "window._blockHtml[" in source
