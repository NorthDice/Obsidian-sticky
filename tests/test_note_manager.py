import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from note_manager import NoteManager
from config import ConfigManager


class FakeConfig:
    def __init__(self, notes=None, index=0):
        self._data = {
            "notes": notes or [],
            "current_index": index,
        }

    @property
    def notes(self):
        return self._data["notes"]

    @property
    def current_index(self):
        return self._data["current_index"]

    @current_index.setter
    def current_index(self, value):
        self._data["current_index"] = value

    def add_note(self, path):
        if path not in self._data["notes"]:
            self._data["notes"].append(path)

    def remove_note(self, index):
        self._data["notes"].pop(index)
        self._data["current_index"] = max(0, index - 1)

    def save(self):
        pass


class TestNoteManagerLoad:
    def test_load_existing_file(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("# Hello", encoding="utf-8")
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["path"] = path
            loaded["content"] = content
            loaded["idx"] = idx
            loaded["total"] = total

        cfg = FakeConfig(notes=[str(note)], index=0)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.load_current()
        assert loaded["content"] == "# Hello"
        assert loaded["idx"] == 0
        assert loaded["total"] == 1

    def test_load_no_notes(self):
        called = {"no_notes": False}

        def on_no():
            called["no_notes"] = True

        cfg = FakeConfig()
        nm = NoteManager(cfg, lambda *a: None, on_no)
        nm.load_current()
        assert called["no_notes"]

    def test_load_nonexistent_file(self):
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["content"] = content

        cfg = FakeConfig(notes=["/nonexistent/path.md"], index=0)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.load_current()
        assert "Read error" in loaded["content"]

    def test_clamps_index(self, tmp_path):
        note = tmp_path / "only.md"
        note.write_text("content", encoding="utf-8")
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["idx"] = idx

        cfg = FakeConfig(notes=[str(note)], index=999)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.load_current()
        assert loaded["idx"] == 0
        assert cfg.current_index == 0


class TestNoteManagerSave:
    def test_save_writes_file(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("old", encoding="utf-8")
        cfg = FakeConfig(notes=[str(note)])
        nm = NoteManager(cfg, lambda *a: None, lambda: None)
        nm.save_current("new content")
        assert note.read_text(encoding="utf-8") == "new content"

    def test_save_no_notes(self):
        cfg = FakeConfig()
        nm = NoteManager(cfg, lambda *a: None, lambda: None)
        nm.save_current("data")  # should not raise


class TestNoteManagerNavigation:
    def test_navigate_forward(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("aaa", encoding="utf-8")
        b.write_text("bbb", encoding="utf-8")
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["content"] = content
            loaded["idx"] = idx

        cfg = FakeConfig(notes=[str(a), str(b)], index=0)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.navigate_to(1, "aaa")
        assert loaded["idx"] == 1
        assert loaded["content"] == "bbb"

    def test_navigate_wraps(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("aaa", encoding="utf-8")
        b.write_text("bbb", encoding="utf-8")
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["idx"] = idx

        cfg = FakeConfig(notes=[str(a), str(b)], index=1)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.navigate_to(1, "bbb")
        assert loaded["idx"] == 0

    def test_navigate_saves_current(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("old", encoding="utf-8")
        b.write_text("bbb", encoding="utf-8")
        cfg = FakeConfig(notes=[str(a), str(b)], index=0)
        nm = NoteManager(cfg, lambda *a: None, lambda: None)
        nm.navigate_to(1, "modified content")
        assert a.read_text(encoding="utf-8") == "modified content"


class TestNoteManagerAddRemove:
    def test_add_notes(self, tmp_path):
        note = tmp_path / "new.md"
        note.write_text("new", encoding="utf-8")
        cfg = FakeConfig()
        nm = NoteManager(cfg, lambda *a: None, lambda: None)
        nm.add_notes([str(note)])
        assert str(note) in cfg.notes

    def test_remove_current(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("aaa", encoding="utf-8")
        b.write_text("bbb", encoding="utf-8")
        loaded = {}

        def on_loaded(path, content, idx, total):
            loaded["content"] = content

        cfg = FakeConfig(notes=[str(a), str(b)], index=0)
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.remove_current()
        assert str(a) not in cfg.notes
        assert loaded["content"] == "bbb"


class TestExternalPolling:
    def test_detects_mtime_change(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("v1", encoding="utf-8")
        loaded = {"count": 0}

        def on_loaded(path, content, idx, total):
            loaded["count"] += 1
            loaded["content"] = content

        cfg = FakeConfig(notes=[str(note)])
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.load_current()
        assert loaded["count"] == 1

        # Modify external file
        import time
        time.sleep(0.05)
        note.write_text("v2", encoding="utf-8")
        nm.poll_external_changes()
        assert loaded["count"] == 2
        assert loaded["content"] == "v2"

    def test_no_reload_when_unchanged(self, tmp_path):
        note = tmp_path / "note.md"
        note.write_text("v1", encoding="utf-8")
        loaded = {"count": 0}

        def on_loaded(path, content, idx, total):
            loaded["count"] += 1

        cfg = FakeConfig(notes=[str(note)])
        nm = NoteManager(cfg, on_loaded, lambda: None)
        nm.load_current()
        nm.poll_external_changes()
        assert loaded["count"] == 1  # not reloaded

    def test_poll_no_notes(self):
        cfg = FakeConfig()
        nm = NoteManager(cfg, lambda *a: None, lambda: None)
        result = nm.poll_external_changes()
        assert result is True  # keeps polling
