import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMPORTS_DIR = BASE_DIR / "imports"
EXPORTS_DIR = BASE_DIR / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure runtime directories exist
for p in [DATA_DIR, IMPORTS_DIR, EXPORTS_DIR, TEMPLATES_DIR, BACKUP_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Bot credentials & configuration
BOT_TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()

# Admin IDs: comma-separated list of Telegram user IDs
admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS: list[int] = []
if admin_ids_raw:
    for uid in admin_ids_raw.split(","):
        uid = uid.strip()
        if uid.isdigit():
            ADMIN_IDS.append(int(uid))

# Database settings
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "quizbot.db")))

# Default preferences
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "uz").strip().lower()
DEFAULT_TIMER = int(os.getenv("DEFAULT_TIMER", "30"))
MAX_IMPORT_ROWS = int(os.getenv("MAX_IMPORT_ROWS", "50000"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

def is_admin(user_id: int) -> bool:
    """Check if a telegram user ID has administrator privileges."""
    return user_id in ADMIN_IDS
