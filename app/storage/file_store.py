import json
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.config import DB_FILE, UPLOAD_DIR, STORAGE_DIR


class FileStore:
    """Thread-safe file storage and metadata registry."""

    def __init__(self):
        self._lock = threading.Lock()
        self._db_path = DB_FILE
        self._store: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self._db_path.exists():
            try:
                with open(self._db_path, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
            except Exception:
                self._store = {}

    def _save(self):
        try:
            with open(self._db_path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            print(f"Error saving DB: {e}")

    def save_file_record(self, file_id: str, record: Dict[str, Any]):
        with self._lock:
            self._store[file_id] = record
            self._save()

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(file_id)

    def list_files(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._store.values())

    def delete_file(self, file_id: str) -> bool:
        with self._lock:
            record = self._store.pop(file_id, None)
            if record:
                saved_path = record.get("filepath")
                if saved_path:
                    path = Path(saved_path) if Path(saved_path).is_absolute() else STORAGE_DIR / saved_path
                    if path.exists():
                        try:
                            path.unlink()
                        except Exception:
                            pass
                self._save()
                return True
            return False


file_store = FileStore()
