import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as config_module


def _make_config(tmp_path, data=None):
    """Create a ConfigManager with a temporary config file."""
    cfg_file = os.path.join(tmp_path, "test_config.json")
    original = config_module.CONFIG_FILE
    config_module.CONFIG_FILE = cfg_file
    if data is not None:
        with open(cfg_file, "w") as f:
            json.dump(data, f)
    cm = config_module.ConfigManager()
    config_module.CONFIG_FILE = original
    # Patch save to use temp file
    cm._config_file = cfg_file
    original_save = cm.save

    def patched_save():
        with open(cfg_file, "w") as f:
            json.dump(cm._data, f, indent=2)
    cm.save = patched_save
    return cm, cfg_file


class TestConfigDefaults:
    def test_defaults_when_no_file(self, tmp_path):
        cm, _ = _make_config(str(tmp_path))
        assert cm.notes == []
        assert cm.current_index == 0
        assert cm.x == 60
        assert cm.y == 60
        assert cm.width == 320
        assert cm.height == 380
        assert cm.opacity == 0.95

    def test_loads_existing_config(self, tmp_path):
        data = {"notes": ["/tmp/a.md"], "current_index": 1,
                "x": 100, "y": 200, "width": 400, "height": 500, "opacity": 0.8}
        cm, _ = _make_config(str(tmp_path), data)
        assert cm.notes == ["/tmp/a.md"]
        assert cm.current_index == 1
        assert cm.x == 100
        assert cm.opacity == 0.8

    def test_fills_missing_keys(self, tmp_path):
        data = {"notes": ["/tmp/b.md"]}
        cm, _ = _make_config(str(tmp_path), data)
        assert cm.notes == ["/tmp/b.md"]
        assert cm.width == 320  # default filled

    def test_handles_corrupt_config(self, tmp_path):
        cfg_file = os.path.join(str(tmp_path), "test_config.json")
        with open(cfg_file, "w") as f:
            f.write("not json{{{")
        original = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = cfg_file
        cm = config_module.ConfigManager()
        config_module.CONFIG_FILE = original
        assert cm.notes == []


class TestConfigOperations:
    def test_add_note(self, tmp_path):
        cm, cfg_file = _make_config(str(tmp_path))
        cm.add_note("/tmp/note1.md")
        assert "/tmp/note1.md" in cm.notes

    def test_add_duplicate_note(self, tmp_path):
        cm, _ = _make_config(str(tmp_path))
        cm.add_note("/tmp/note1.md")
        cm.add_note("/tmp/note1.md")
        assert cm.notes.count("/tmp/note1.md") == 1

    def test_remove_note(self, tmp_path):
        data = {"notes": ["/tmp/a.md", "/tmp/b.md", "/tmp/c.md"],
                "current_index": 1}
        cm, _ = _make_config(str(tmp_path), data)
        cm.remove_note(1)
        assert "/tmp/b.md" not in cm.notes
        assert len(cm.notes) == 2
        assert cm.current_index == 0

    def test_remove_first_note(self, tmp_path):
        data = {"notes": ["/tmp/a.md", "/tmp/b.md"], "current_index": 0}
        cm, _ = _make_config(str(tmp_path), data)
        cm.remove_note(0)
        assert cm.current_index == 0
        assert cm.notes == ["/tmp/b.md"]

    def test_set_current_index(self, tmp_path):
        cm, _ = _make_config(str(tmp_path))
        cm.current_index = 5
        assert cm.current_index == 5

    def test_update_window_state(self, tmp_path):
        cm, cfg_file = _make_config(str(tmp_path))
        cm.update_window_state(10, 20, 300, 400)
        assert cm.x == 10
        assert cm.y == 20
        assert cm.width == 300
        assert cm.height == 400
        # Verify saved to file
        with open(cfg_file) as f:
            saved = json.load(f)
        assert saved["x"] == 10

    def test_save_persists(self, tmp_path):
        cm, cfg_file = _make_config(str(tmp_path))
        cm.add_note("/tmp/test.md")
        with open(cfg_file) as f:
            saved = json.load(f)
        assert "/tmp/test.md" in saved["notes"]
