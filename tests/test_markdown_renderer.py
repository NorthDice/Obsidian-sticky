import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from markdown_renderer import render_html


class TestBasicStructure:
    def test_returns_full_html_document(self):
        html = render_html("hello")
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_includes_css(self):
        html = render_html("hello")
        assert "<style>" in html
        assert "#1e1e1e" in html

    def test_empty_input(self):
        html = render_html("")
        assert "<body>" in html


class TestHeadings:
    def test_h1(self):
        html = render_html("# Title")
        assert "<h1>Title</h1>" in html

    def test_h2(self):
        html = render_html("## Subtitle")
        assert "<h2>Subtitle</h2>" in html

    def test_h3(self):
        html = render_html("### Section")
        assert "<h3>Section</h3>" in html


class TestInlineFormatting:
    def test_bold(self):
        html = render_html("**bold text**")
        assert "<strong>bold text</strong>" in html

    def test_italic(self):
        html = render_html("*italic text*")
        assert "<em>italic text</em>" in html

    def test_inline_code(self):
        html = render_html("`some code`")
        assert "<code>some code</code>" in html

    def test_highlight(self):
        html = render_html("==highlighted==")
        assert "<mark>highlighted</mark>" in html

    def test_highlight_in_sentence(self):
        html = render_html("This is ==important== text")
        assert "<mark>important</mark>" in html

    def test_link(self):
        html = render_html("[click](https://example.com)")
        assert 'href="https://example.com"' in html
        assert ">click</a>" in html


class TestCodeBlocks:
    def test_fenced_code_block(self):
        md = "```python\nprint('hello')\n```"
        html = render_html(md)
        assert "<pre>" in html
        assert "<code" in html
        assert "print" in html

    def test_fenced_code_no_language(self):
        md = "```\nsome code\n```"
        html = render_html(md)
        assert "<pre>" in html
        assert "some code" in html


class TestBlockquotes:
    def test_simple_blockquote(self):
        html = render_html("> quoted text")
        assert "<blockquote>" in html
        assert "quoted text" in html


class TestLists:
    def test_unordered_list(self):
        md = "- item one\n- item two\n- item three"
        html = render_html(md)
        assert "<ul>" in html
        assert "<li>" in html
        assert "item one" in html

    def test_ordered_list(self):
        md = "1. first\n2. second\n3. third"
        html = render_html(md)
        assert "<ol>" in html
        assert "first" in html


class TestTables:
    def test_simple_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = render_html(md)
        assert "<table>" in html
        assert "<th>" in html or "<th" in html
        assert "<td>" in html or "<td" in html
        assert ">A<" in html
        assert ">1<" in html

    def test_table_alignment(self):
        md = "| Left | Center | Right |\n|:---|:---:|---:|\n| a | b | c |"
        html = render_html(md)
        assert "<table>" in html


class TestHorizontalRule:
    def test_hr(self):
        html = render_html("---")
        assert "<hr" in html


class TestFrontmatter:
    def test_strips_yaml_frontmatter(self):
        md = "---\ntitle: My Note\ntags: [a, b]\n---\n\n# Content"
        html = render_html(md)
        assert "title:" not in html
        assert "tags:" not in html
        assert "<h1>Content</h1>" in html

    def test_frontmatter_only_at_start(self):
        md = "Some text\n\n---\ntitle: Not frontmatter\n---"
        html = render_html(md)
        # This should NOT be stripped — it's not at the start
        assert "<hr" in html

    def test_no_frontmatter(self):
        md = "# Just a heading"
        html = render_html(md)
        assert "<h1>Just a heading</h1>" in html


class TestCallouts:
    def test_tip_callout(self):
        md = "> [!tip] My Tip\n> Some content here"
        html = render_html(md)
        assert "admonition" in html
        assert "tip" in html
        assert "My Tip" in html
        assert "Some content here" in html

    def test_callout_without_title(self):
        md = "> [!warning]\n> Be careful"
        html = render_html(md)
        assert "admonition" in html
        assert "warning" in html

    def test_callout_multiline(self):
        md = "> [!note] Title\n> Line 1\n> Line 2"
        html = render_html(md)
        assert "Line 1" in html
        assert "Line 2" in html

    def test_callout_followed_by_text(self):
        md = "> [!info] Info\n> Details\n\nNormal paragraph"
        html = render_html(md)
        assert "admonition" in html
        assert "Normal paragraph" in html


class TestConsecutiveRenders:
    """Ensure the singleton md instance resets properly between renders."""

    def test_two_renders_independent(self):
        html1 = render_html("# First")
        html2 = render_html("# Second")
        assert "First" in html1
        assert "Second" in html2
        assert "First" not in html2

    def test_frontmatter_reset(self):
        render_html("---\nkey: val\n---\n\nBody1")
        html2 = render_html("# No frontmatter")
        assert "key:" not in html2


class TestComplexDocument:
    def test_mixed_content(self):
        md = """---
title: Test
---

# Heading

Some **bold** and *italic* and ==highlight== text.

> [!tip] Tip Title
> Tip content

| Col A | Col B |
|-------|-------|
| 1     | 2     |

```python
def hello():
    pass
```

- list item 1
- list item 2

> A blockquote

---
"""
        html = render_html(md)
        assert "title:" not in html
        assert "<h1>Heading</h1>" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "<mark>highlight</mark>" in html
        assert "admonition" in html
        assert "<table>" in html
        assert "<pre>" in html
        assert "<ul>" in html
        assert "<blockquote>" in html
        assert "<hr" in html
