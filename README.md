# Telegram Quiz Bot (Production Ready)

A high-performance, asynchronous Telegram Quiz & Examination Bot built with **Python 3.10+**, **aiogram 3.x**, and **SQLite (WAL mode)**. Designed to deliver an examination experience inspired by Telegram's official `@QuizBot`, featuring high-capacity bulk question import from Excel and CSV (10,000+ questions per batch), rich student examination interfaces, and interactive real-time group competitions.

---

## ✨ Features

- **⚡ High-Capacity Bulk Import**: Upload `.xlsx` or `.csv` files directly via Telegram to import thousands of questions at once. Validates every row, prevents duplicate entries, and reports exact row numbers for any malformed data.
- **🎯 Individual Examination Experience**:
  - Landing pages with quiz details, question count, pass percentage, and deep links (`https://t.me/<bot>?start=quiz_<id>`).
  - Exactly 4 answer options (A, B, C, D) with answer shuffling.
  - Configurable timers (10s, 15s, 20s, 30s, 45s, 60s, or custom duration) with automatic progression when time expires.
  - Instant visual feedback, optional question explanations, and question progress bars.
  - Comprehensive final score card with pass/fail evaluation, percentage, and completion time.
  - **Review Mistakes**: Students can review questions they answered incorrectly or missed.
- **👥 Real-Time Group Mode**:
  - Host competitions directly in group and supergroup chats.
  - Interactive lobby where members join before starting.
  - Simultaneous answering with duplicate-prevention per question.
  - Round recap showing correct answers and intermediate scores.
  - Final podium leaderboard (🥇 1st, 🥈 2nd, 🥉 3rd) with medals and total points.
- **🛠 Comprehensive Administration Panel** (`/admin`):
  - Accessible strictly to authorized IDs configured in `ADMIN_IDS`.
  - Create and configure quizzes (timers, pass mark, shuffling, explanations, publishing).
  - Add individual questions manually via step-by-step interactive FSM dialog.
  - Preview, browse, and delete questions.
  - Export participant results to Excel (`.xlsx`) with formatted rankings.
  - Live hot SQLite backup downloadable directly in Telegram.
  - Download pre-formatted Excel and CSV question bank templates.
- **🌐 Bilingual Localization**: Built-in support for Uzbek (`uz`) and English (`en`), with full compatibility for Uzbek apostrophes (`o'`, `g'`) and Cyrillic script.
- **🔒 Security & 100% Free Stack**: Zero external paid APIs, zero subscriptions, purely local SQLite database with Write-Ahead Logging (WAL) for safe concurrency.

---

## 📁 Project Structure

```
quizbot/
├── bot/
│   ├── database/
│   │   ├── db.py               # Database manager, schema & hot backup
│   │   ├── models.py           # Dataclasses (Quiz, Question, User, Session, etc.)
│   │   └── queries.py          # Fast async CRUD & batch queries
│   ├── handlers/
│   │   ├── admin.py            # Admin control panel, FSM & bulk import
│   │   ├── common.py           # /start, deep links, /quizzes, /language
│   │   ├── group.py            # Group competitions (/quiz, lobby, answers)
│   │   └── student.py          # Individual quiz runner & mistake review
│   ├── keyboards/
│   │   ├── inline.py           # Modern inline keyboard factories
│   │   └── reply.py            # Reply keyboards
│   ├── middlewares/
│   │   ├── auth.py             # User upsert & admin access control
│   │   └── db_session.py       # Database context injection
│   ├── services/
│   │   ├── exporter.py         # Formatted Excel results exporter
│   │   ├── group_engine.py     # Group competition engine & timers
│   │   ├── importer.py         # High-speed Excel & CSV parser
│   │   └── quiz_engine.py      # Individual quiz session engine & timers
│   └── utils/
│       ├── formatters.py       # Progress bars, time formatting & HTML escaping
│       ├── i18n.py             # Uzbek & English translation dictionary
│       └── validator.py        # Row-by-row validation & synonym normalizer
├── data/                       # Persistent SQLite database & backups
├── exports/                    # Generated Excel result sheets
├── imports/                    # Temporary uploaded files
├── templates/                  # Sample Excel & CSV templates
├── tests/                      # Automated test suite (20 tests)
├── config.py                   # Environment configuration loader
├── launch.bat                  # One-click Windows startup script
├── main.py                     # Bot entrypoint & polling orchestrator
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
├── sample_questions.xlsx       # Ready-to-use sample question bank
├── .env.example                # Example environment variables
└── README.md
```

---

## 🚀 Quick Start (Windows)

### 1. Configure Credentials
1. Copy `.env.example` to `.env`:
   ```cmd
   copy .env.example .env
   ```
2. Open `.env` and fill in your details:
   ```ini
   BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ1234567
   ADMIN_IDS=123456789
   ```
   - **BOT_TOKEN**: Obtain from [@BotFather](https://t.me/BotFather) on Telegram.
   - **ADMIN_IDS**: Your Telegram user ID (comma-separated if multiple admins). You can find your ID by sending `/start` to [@userinfobot](https://t.me/userinfobot).

### 2. Launch with `launch.bat`
Double-click `launch.bat` in the project root. It will:
- Check for Python 3.10+.
- Verify and automatically install dependencies from `requirements.txt`.
- Start the bot.

Or run manually from the terminal:
```bash
pip install -r requirements.txt
python main.py
```

---

## 📊 Spreadsheet Format for Bulk Import

Files may be in **Excel (`.xlsx`)** or **CSV (UTF-8)** format.

| Column | Required | Description | Example |
|---|---|---|---|
| `question` | **Yes** | Question text | What is the capital of Uzbekistan? |
| `option_a` | **Yes** | First answer option | Samarkand |
| `option_b` | **Yes** | Second answer option | Tashkent |
| `option_c` | **Yes** | Third answer option | Bukhara |
| `option_d` | **Yes** | Fourth answer option | Khiva |
| `correct_answer` | **Yes** | `A`, `B`, `C`, or `D` (or `1`, `2`, `3`, `4`) | `B` |
| `explanation` | No | Explanation shown to student | Tashkent is the capital city. |
| `topic` | No | Topic or category | Geography |
| `difficulty` | No | `Easy`, `Medium`, or `Hard` | Easy |
| `timer` | No | Custom timer override in seconds | `25` |
| `image` | No | Optional image URL | `https://example.com/map.jpg` |

*Note: Header synonyms like `Savol`, `Variant A`, `To'g'ri javob`, `Izoh` are automatically supported.*

---

## 🧪 Automated Testing

The project includes an automated test suite covering database queries, bulk import performance, row validation, scoring logic, and group competition concurrency:

```bash
pytest -v
```

All 20 test cases run and pass within ~5 seconds.
