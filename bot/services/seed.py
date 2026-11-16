import csv
import logging
from pathlib import Path
from typing import Optional
import config
from bot.database.db import Database
from bot.database import queries

logger = logging.getLogger(__name__)

async def apply_seeds(db: Database):
    """
    Applies system seeds once safely.
    Uses 'system_seeds' table to avoid re-seeding if the admin later deletes or edits quizzes.
    """
    async with db.get_connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_seeds (
                seed_name TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await conn.commit()

        # Check if 85-question quiz seed is already applied
        async with conn.execute(
            "SELECT seed_name FROM system_seeds WHERE seed_name = ?",
            ("seed_oqsillar_85_v2",)
        ) as cursor:
            if await cursor.fetchone():
                return

        # Check if quiz already exists by title
        async with conn.execute(
            "SELECT id FROM quizzes WHERE title = ?",
            ("Oqsillar almashinuvi — To'liq Imtihon (85 ta savol)",)
        ) as cursor:
            if await cursor.fetchone():
                await conn.execute(
                    "INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)",
                    ("seed_oqsillar_85_v2",)
                )
                await conn.commit()
                return

        # Find CSV file
        csv_path = config.DATA_DIR / "oqsillar_almashinuvi_85.csv"
        if not csv_path.exists():
            csv_path = config.TEMPLATES_DIR / "oqsillar_almashinuvi_85.csv"

        if not csv_path.exists():
            logger.warning(f"Seed CSV not found at {csv_path}")
            return

        questions_data = []
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions_data.append({
                    "question": row["question"].strip(),
                    "option_a": row["option_a"].strip(),
                    "option_b": row["option_b"].strip(),
                    "option_c": row["option_c"].strip(),
                    "option_d": row["option_d"].strip(),
                    "correct_answer": row["correct_answer"].strip().upper(),
                    "explanation": row.get("explanation", "").strip(),
                    "topic": row.get("topic", "").strip(),
                    "difficulty": row.get("difficulty", "Medium").strip(),
                    "timer": int(row.get("timer", 25)) if row.get("timer") else 25,
                    "image": None
                })

        admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
        quiz_id = await queries.create_quiz(
            conn,
            title="Oqsillar almashinuvi — To'liq Imtihon (85 ta savol)",
            description="Oqsillar almashinuvi mavzusidagi barcha 85 ta savoldan iborat to'liq imtihon testi.",
            category="Biokimyo",
            default_timer=25,
            shuffle_options=True,
            show_explanation=True,
            pass_percentage=70,
            is_published=True,
            created_by=admin_id
        )

        inserted = await queries.bulk_insert_questions(conn, quiz_id, questions_data)
        await conn.execute(
            "INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)",
            ("seed_oqsillar_85_v2",)
        )
        await conn.commit()
        logger.info(
            f"Successfully seeded quiz ID {quiz_id} "
            f"('Oqsillar almashinuvi — To'liq Imtihon (85 ta savol)') with {inserted} questions."
        )
