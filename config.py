import os
import json

CONFIG_FILE = os.path.expanduser("~/.obsidian_sticky_v2.json")

_DEFAULTS = {
    "notes": [],
    "current_index": 0,
    "x": 60,
    "y": 60,
    "width": 320,
    "height": 380,
    "opacity": 0.95,
}


class ConfigManager:
    def __init__(self):
        self._data = _DEFAULTS.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    loaded = json.load(f)
                for k, v in _DEFAULTS.items():
                    loaded.setdefault(k, v)
                self._data = loaded
            except Exception:
                pass

    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")

    @property
    def notes(self):
        return self._data["notes"]

    @property
    def current_index(self):
        return self._data["current_index"]

    @current_index.setter
    def current_index(self, value):
        self._data["current_index"] = value

    @property
    def x(self):
        return self._data["x"]

    @property
    def y(self):
        return self._data["y"]

    @property
    def width(self):
        return self._data["width"]

    @property
    def height(self):
        return self._data["height"]

    @property
    def opacity(self):
        return self._data["opacity"]

    def add_note(self, path):
        if path not in self._data["notes"]:
            self._data["notes"].append(path)
            self.save()

    def remove_note(self, index):
        self._data["notes"].pop(index)
        self._data["current_index"] = max(0, index - 1)
        self.save()

    def update_window_state(self, x, y, w, h):
        self._data.update({"x": x, "y": y, "width": w, "height": h})
        self.save()
