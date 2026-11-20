import csv
import logging
from pathlib import Path
from typing import Optional
import config
from bot.database.db import Database
from bot.database import queries

logger = logging.getLogger(__name__)

ANATOMY_COLLECTIONS = [
    (1, "Anatomiya 1: Umurtqa va Dumg'aza suyaklari", "anatomiya_collection_01.csv"),
    (2, "Anatomiya 2: Umurtqa pog'onasi va Qo'l suyaklari", "anatomiya_collection_02.csv"),
    (3, "Anatomiya 3: Oyoq va Yelka suyaklari", "anatomiya_collection_03.csv"),
    (4, "Anatomiya 4: Son va Boldir suyaklari", "anatomiya_collection_04.csv"),
    (5, "Anatomiya 5: Chanoq suyagi va To'sh-o'mrov bo'g'imi", "anatomiya_collection_05.csv"),
    (6, "Anatomiya 6: Umurtqalararo boylamlar va Yelka bo'g'imi", "anatomiya_collection_06.csv"),
    (7, "Anatomiya 7: Chanoq-son va Tizza bo'g'imlari", "anatomiya_collection_07.csv"),
    (8, "Anatomiya 8: Ko'krak, qorin va orqa mushaklari", "anatomiya_collection_08.csv"),
    (9, "Anatomiya 9: Son va boldir mushaklari", "anatomiya_collection_09.csv"),
    (10, "Anatomiya 10: Qorin a'zolari va Qo'l mushaklari", "anatomiya_collection_10.csv"),
    (11, "Anatomiya 11: Hazm tizimi va Darvoza venasi", "anatomiya_collection_11.csv"),
    (12, "Anatomiya 12: Jigar va Oshqozon anatomiyasi", "anatomiya_collection_12.csv"),
    (13, "Anatomiya 13: Oshqozon boylamlari va Kalla suyagi", "anatomiya_collection_13.csv"),
    (14, "Anatomiya 14: Peshona va Ensa suyaklari", "anatomiya_collection_14.csv"),
    (15, "Anatomiya 15: Miya arteriyalari va Bo'ylama kesimi", "anatomiya_collection_15.csv"),
    (16, "Anatomiya 16: Uzunchoq miya va Miya bo'laklari", "anatomiya_collection_16.csv"),
    (17, "Anatomiya 17: Bosh miya yadrolari va Qorinchalari", "anatomiya_collection_17.csv"),
    (18, "Anatomiya 18: Miyacha va Eshitish a'zolari", "anatomiya_collection_18.csv"),
]

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

        await _seed_oqsillar(conn)
        await _seed_all_anatomy_collections(conn)

async def _seed_oqsillar(conn):
    seed_key = "seed_oqsillar_85_v2"
    quiz_title = "Oqsillar almashinuvi — To'liq Imtihon (85 ta savol)"

    async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
        if await cursor.fetchone():
            return

    async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (quiz_title,)) as cursor:
        if await cursor.fetchone():
            await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
            await conn.commit()
            return

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
                "image": row.get("image", "").strip() or None
            })

    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
    quiz_id = await queries.create_quiz(
        conn,
        title=quiz_title,
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
    await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
    await conn.commit()
    logger.info(f"Successfully seeded quiz ID {quiz_id} ('{quiz_title}') with {inserted} questions.")

async def _seed_all_anatomy_collections(conn):
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
    collections_dir = config.DATA_DIR / "anatomiya_collections"

    for col_num, base_title, filename in ANATOMY_COLLECTIONS:
        seed_key = f"seed_anatomiya_collection_{col_num:02d}_v1"

        async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
            if await cursor.fetchone():
                continue

        csv_path = collections_dir / filename
        if not csv_path.exists():
            continue

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
                    "image": row.get("image", "").strip() or None
                })

        quiz_title = f"{base_title} ({len(questions_data)} ta savol)"

        # Check if quiz already exists
        async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (quiz_title,)) as cursor:
            if await cursor.fetchone():
                await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
                await conn.commit()
                continue

        quiz_id = await queries.create_quiz(
            conn,
            title=quiz_title,
            description=f"{base_title} mavzusidagi rentgen va anatomik rasmlar orqali tuzilmalarni aniqlash testi.",
            category="Anatomiya",
            default_timer=25,
            shuffle_options=True,
            show_explanation=True,
            pass_percentage=70,
            is_published=True,
            created_by=admin_id
        )

        inserted = await queries.bulk_insert_questions(conn, quiz_id, questions_data)
        await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
        await conn.commit()
        logger.info(f"Successfully seeded quiz ID {quiz_id} ('{quiz_title}') with {inserted} questions.")
