import shutil
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -2048;
PRAGMA temp_store = MEMORY;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    real_name TEXT,
    phone_number TEXT,
    student_group TEXT,
    language_code TEXT DEFAULT 'uz',
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'General',
    default_timer INTEGER DEFAULT 30,
    shuffle_options INTEGER DEFAULT 1,
    show_explanation INTEGER DEFAULT 1,
    pass_percentage INTEGER DEFAULT 60,
    is_published INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(telegram_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    explanation TEXT,
    topic TEXT,
    difficulty TEXT DEFAULT 'Medium',
    timer_seconds INTEGER,
    image_url TEXT,
    order_num INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS question_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_label TEXT NOT NULL, -- 'A', 'B', 'C', 'D'
    option_text TEXT NOT NULL,
    is_correct INTEGER DEFAULT 0,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_code TEXT UNIQUE NOT NULL,
    quiz_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    is_group INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress', -- in_progress, completed, abandoned
    current_question_index INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    unanswered_count INTEGER DEFAULT 0,
    score_percentage REAL DEFAULT 0.0,
    passed INTEGER DEFAULT 0,
    question_ids_order TEXT, -- JSON array of question IDs in randomized/selected order
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL DEFAULT 0.0,
    FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    selected_option TEXT, -- 'A', 'B', 'C', 'D' or NULL if timed out
    is_correct INTEGER DEFAULT 0,
    response_time_seconds REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE(session_id, question_id)
);

CREATE TABLE IF NOT EXISTS group_competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER,
    status TEXT DEFAULT 'lobby', -- lobby, active, finished, cancelled
    current_question_index INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    timer_seconds INTEGER DEFAULT 30,
    round_end_time TIMESTAMP,
    question_ids_order TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_answered INTEGER DEFAULT 0,
    total_response_time REAL DEFAULT 0.0,
    FOREIGN KEY(competition_id) REFERENCES group_competitions(id) ON DELETE CASCADE,
    UNIQUE(competition_id, user_id)
);

CREATE TABLE IF NOT EXISTS group_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    selected_option TEXT NOT NULL,
    is_correct INTEGER DEFAULT 0,
    response_time_seconds REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(competition_id) REFERENCES group_competitions(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE(competition_id, question_id, user_id)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_published ON quizzes(is_published);
CREATE INDEX IF NOT EXISTS idx_questions_quiz_id ON questions(quiz_id);
CREATE INDEX IF NOT EXISTS idx_options_question_id ON question_options(question_id);
CREATE INDEX IF NOT EXISTS idx_sessions_code ON quiz_sessions(session_code);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON quiz_sessions(user_id, quiz_id);
CREATE INDEX IF NOT EXISTS idx_group_comp_chat ON group_competitions(chat_id, status);
CREATE INDEX IF NOT EXISTS idx_group_ans_comp ON group_answers(competition_id, question_id);
"""

class Database:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        """Initialize database tables and indices."""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.executescript(SCHEMA_SQL)
            # Automatic schema migration for users table
            async with conn.execute("PRAGMA table_info(users)") as cursor:
                rows = await cursor.fetchall()
                cols = {r[1] for r in rows}
                if "real_name" not in cols:
                    await conn.execute("ALTER TABLE users ADD COLUMN real_name TEXT")
                if "phone_number" not in cols:
                    await conn.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
                if "student_group" not in cols:
                    await conn.execute("ALTER TABLE users ADD COLUMN student_group TEXT")
            await conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def get_connection(self) -> aiosqlite.Connection:
        """Create an aiosqlite connection context manager."""
        conn = aiosqlite.connect(self.db_path)
        return conn

    async def backup(self, backup_dir: Path) -> Path:
        """Create a timestamped backup copy of the SQLite database."""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"quizbot_backup_{timestamp}.db"
        
        def _do_backup():
            import sqlite3
            with sqlite3.connect(str(self.db_path)) as src:
                with sqlite3.connect(str(backup_file)) as dst:
                    src.backup(dst)

        import asyncio
        await asyncio.to_thread(_do_backup)
        
        logger.info(f"Database backup created: {backup_file}")
        return backup_file
