from __future__ import annotations

from pathlib import Path

APP_NAME = "HappyCrypt"
APP_VERSION = "1.0.0"
HOST = "127.0.0.1"
PORT = 8000

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
FRONTEND_DIR = BASE_DIR / "frontend"
DB_PATH = DATA_DIR / "happycrypt.db"

# Ensure local storage directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Defaults
DEFAULT_AUTO_LOCK_MINUTES = 10
DEFAULT_CLIPBOARD_CLEAR_SECONDS = 20

# Argon2id parameters
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # KiB (64 MiB)
ARGON2_PARALLELISM = 2
ARGON2_HASH_LEN = 32  # 256-bit key
ARGON2_SALT_LEN = 16

# Session
SESSION_COOKIE_NAME = "happycrypt_session"
SESSION_IDLE_CHECK_SECONDS = 30
