import os


class NoteManager:
    def __init__(self, config, on_note_loaded, on_no_notes):
        self._config = config
        self._on_note_loaded = on_note_loaded
        self._on_no_notes = on_no_notes
        self._last_mtime = 0

    def load_current(self):
        notes = self._config.notes
        if not notes:
            self._on_no_notes()
            return

        idx = max(0, min(self._config.current_index, len(notes) - 1))
        self._config.current_index = idx
        path = notes[idx]

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._last_mtime = self._get_mtime(path)
            self._on_note_loaded(path, content, idx, len(notes))
        except Exception as e:
            self._on_note_loaded(path, f"Read error:\n{e}", idx, len(notes))

    def save_current(self, content):
        notes = self._config.notes
        if not notes:
            return
        path = notes[self._config.current_index]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._last_mtime = self._get_mtime(path)
        except Exception as e:
            print(f"Save error: {e}")

    def navigate_to(self, delta, current_content):
        notes = self._config.notes
        if not notes:
            return
        self.save_current(current_content)
        self._config.current_index = (self._config.current_index + delta) % len(notes)
        self._config.save()
        self.load_current()

    def add_notes(self, paths):
        for path in paths:
            self._config.add_note(path)
        self.load_current()

    def remove_current(self):
        notes = self._config.notes
        if not notes:
            return
        self._config.remove_note(self._config.current_index)
        self.load_current()

    def poll_external_changes(self):
        notes = self._config.notes
        if not notes:
            return True
        path = notes[self._config.current_index]
        mtime = self._get_mtime(path)
        if mtime and mtime != self._last_mtime:
            self.load_current()
        return True

    def _get_mtime(self, path):
        return os.path.getmtime(path) if os.path.exists(path) else 0
