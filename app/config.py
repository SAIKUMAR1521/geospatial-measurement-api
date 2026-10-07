import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "data_storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
DB_FILE = STORAGE_DIR / "metadata_db.json"

MAX_UPLOAD_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".zip", ".kml"}

# Ensure storage directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
