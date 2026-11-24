import csv
import logging
from pathlib import Path
from typing import Optional
import config
from bot.database.db import Database
from bot.database import queries

logger = logging.getLogger(__name__)

ANATOMY_COLLECTIONS = [
    (1, "1-rasm, 2-rasm", "Umurtqa va Dumg'aza suyaklari", "anatomiya_collection_01.csv"),
    (2, "3-rasm, 4-rasm", "Umurtqa pog'onasi va Qo'l suyaklari", "anatomiya_collection_02.csv"),
    (3, "5-rasm, 6-rasm", "Oyoq va Yelka suyaklari", "anatomiya_collection_03.csv"),
    (4, "7-rasm, 8-rasm", "Son va Boldir suyaklari", "anatomiya_collection_04.csv"),
    (5, "9-rasm, 10-rasm", "Chanoq suyagi va To'sh-o'mrov bo'g'imi", "anatomiya_collection_05.csv"),
    (6, "11-rasm, 12-rasm", "Umurtqalararo boylamlar va Yelka bo'g'imi", "anatomiya_collection_06.csv"),
    (7, "13-rasm, 14-rasm", "Chanoq-son va Tizza bo'g'imlari", "anatomiya_collection_07.csv"),
    (8, "15-rasm, 16-rasm", "Ko'krak, qorin va orqa mushaklari", "anatomiya_collection_08.csv"),
    (9, "17-rasm, 18-rasm", "Son va boldir mushaklari", "anatomiya_collection_09.csv"),
    (10, "19-rasm, 20-rasm", "Qorin a'zolari va Qo'l mushaklari", "anatomiya_collection_10.csv"),
    (11, "21-rasm, 22-rasm", "Hazm tizimi va Darvoza venasi", "anatomiya_collection_11.csv"),
    (12, "23-rasm, 24-rasm", "Jigar va Oshqozon anatomiyasi", "anatomiya_collection_12.csv"),
    (13, "25-rasm, 26-rasm", "Oshqozon boylamlari va Kalla suyagi", "anatomiya_collection_13.csv"),
    (14, "27-rasm, 28-rasm", "Peshona va Ensa suyaklari", "anatomiya_collection_14.csv"),
    (15, "29-rasm, 30-rasm", "Miya arteriyalari va Bo'ylama kesimi", "anatomiya_collection_15.csv"),
    (16, "31-rasm, 32-rasm", "Uzunchoq miya va Miya bo'laklari", "anatomiya_collection_16.csv"),
    (17, "33-rasm, 34-rasm", "Bosh miya yadrolari va Qorinchalari", "anatomiya_collection_17.csv"),
    (18, "35-rasm, 36-rasm", "Miyacha va Eshitish a'zolari", "anatomiya_collection_18.csv"),
]

MIKROBIOLOGIYA_COLLECTIONS = [
    (1, "Mikrobiologiya: 1-mavzu", "Mikrobiologiya fanidan 1-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_01.csv"),
    (2, "Mikrobiologiya: 2-mavzu", "Mikrobiologiya fanidan 2-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_02.csv"),
    (3, "Mikrobiologiya: 3-mavzu", "Mikrobiologiya fanidan 3-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_03.csv"),
    (4, "Mikrobiologiya: 4-mavzu", "Mikrobiologiya fanidan 4-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_04.csv"),
    (5, "Mikrobiologiya: 5-mavzu", "Mikrobiologiya fanidan 5-mavzu o'zlashtirish testi (1–102)", "mikrobiologiya_mavzu_05.csv"),
    (6, "Mikrobiologiya: 6-mavzu", "Mikrobiologiya fanidan 6-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_06.csv"),
    (7, "Mikrobiologiya: 7-mavzu", "Mikrobiologiya fanidan 7-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_07.csv"),
    (8, "Mikrobiologiya: 8-mavzu", "Mikrobiologiya fanidan 8-mavzu o'zlashtirish testi (1–105)", "mikrobiologiya_mavzu_08.csv"),
    (9, "Mikrobiologiya: 9-mavzu", "Mikrobiologiya fanidan 9-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_09.csv"),
    (10, "Mikrobiologiya: 10-mavzu", "Mikrobiologiya fanidan 10-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_10.csv"),
    (11, "Mikrobiologiya: 11-mavzu", "Mikrobiologiya fanidan 11-mavzu o'zlashtirish testi (1–105)", "mikrobiologiya_mavzu_11.csv"),
    (12, "Mikrobiologiya: 12-mavzu", "Mikrobiologiya fanidan 12-mavzu o'zlashtirish testi (1–100)", "mikrobiologiya_mavzu_12.csv"),
]

FIZIOLOGIYA_COLLECTIONS = [
    (1, "Normal fiziologiya: 1-mavzu", "Normal fiziologiya fanidan 1-mavzu: Fiziologiya faniga kirish (1–100)", "fiziologiya_mavzu_01.csv"),
    (2, "Normal fiziologiya: 2-mavzu", "Normal fiziologiya fanidan 2-mavzu: Membrana potensiali va qo'zg'aluvchan to'qimalar (1–100)", "fiziologiya_mavzu_02.csv"),
    (3, "Normal fiziologiya: 3-mavzu", "Normal fiziologiya fanidan 3-mavzu: Muskul fiziologiyasi (1–100)", "fiziologiya_mavzu_03.csv"),
    (4, "Normal fiziologiya: 4-mavzu", "Normal fiziologiya fanidan 4-mavzu: Nerv tolalari va sinapslar (1–100)", "fiziologiya_mavzu_04.csv"),
    (5, "Normal fiziologiya: 5-mavzu", "Normal fiziologiya fanidan 5-mavzu: Qon plazmasi va eritrotsitlar (1–100)", "fiziologiya_mavzu_05.csv"),
    (6, "Normal fiziologiya: 6-mavzu", "Normal fiziologiya fanidan 6-mavzu: Leykotsitlar va qon guruhlari (1–100)", "fiziologiya_mavzu_06.csv"),
    (7, "Normal fiziologiya: 7-mavzu", "Normal fiziologiya fanidan 7-mavzu: Gemostaz va trombotsitlar (1–100)", "fiziologiya_mavzu_07.csv"),
    (8, "Normal fiziologiya: 8-mavzu", "Normal fiziologiya fanidan 8-mavzu: Yurak mushaklari va avtomatiya (1–90)", "fiziologiya_mavzu_08.csv"),
    (9, "Normal fiziologiya: 9-mavzu", "Normal fiziologiya fanidan 9-mavzu: Yurak boshqarilishi (1–90)", "fiziologiya_mavzu_09.csv"),
    (10, "Normal fiziologiya: 10-mavzu", "Normal fiziologiya fanidan 10-mavzu: Mikrosirkulyatsiya va qon bosimi (1–90)", "fiziologiya_mavzu_10.csv"),
    (11, "Normal fiziologiya: 11-mavzu", "Normal fiziologiya fanidan 11-mavzu: Nafas fiziologiyasi (1–90)", "fiziologiya_mavzu_11.csv"),
    (12, "Normal fiziologiya: 12-mavzu", "Normal fiziologiya fanidan 12-mavzu: Nafas boshqarilishi (1–90)", "fiziologiya_mavzu_12.csv"),
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
        await _seed_all_microbiology_collections(conn)
        await _seed_all_physiology_collections(conn)
        await _seed_biochemistry_true_false(conn)
        await _seed_biochemistry_variantli(conn)

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

    # Step 1: Clean up old duplicate sample test if present
    await conn.execute("DELETE FROM quizzes WHERE title LIKE 'Anatomiya: Umurtqa va Dumg%aza suyaklari%'")

    # Step 2: In-place update existing quizzes with new clean names
    for col_num, clean_title, topic, filename in ANATOMY_COLLECTIONS:
        await conn.execute(
            """
            UPDATE quizzes 
            SET title = ?, description = ? 
            WHERE title LIKE ? OR title LIKE ?
            """,
            (
                clean_title,
                f"{topic} mavzusidagi rentgen va anatomik rasmlar orqali tuzilmalarni aniqlash testi.",
                f"Anatomiya {col_num}:%",
                f"{clean_title} (% ta savol)"
            )
        )
    await conn.commit()

    # Step 3: Seed any collections that are not in database yet
    for col_num, clean_title, topic, filename in ANATOMY_COLLECTIONS:
        seed_key = f"seed_anatomiya_collection_{col_num:02d}_v2"

        async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
            if await cursor.fetchone():
                continue

        # Check if quiz already exists
        async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (clean_title,)) as cursor:
            if await cursor.fetchone():
                await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
                await conn.commit()
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

        quiz_id = await queries.create_quiz(
            conn,
            title=clean_title,
            description=f"{topic} mavzusidagi rentgen va anatomik rasmlar orqali tuzilmalarni aniqlash testi.",
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
        logger.info(f"Successfully seeded quiz ID {quiz_id} ('{clean_title}') with {inserted} questions.")

async def _seed_all_microbiology_collections(conn):
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
    collections_dir = config.DATA_DIR / "mikrobiologiya_collections"

    for col_num, clean_title, description, filename in MIKROBIOLOGIYA_COLLECTIONS:
        seed_key = f"seed_mikrobiologiya_mavzu_{col_num:02d}_v1"

        async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
            if await cursor.fetchone():
                continue

        async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (clean_title,)) as cursor:
            if await cursor.fetchone():
                await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
                await conn.commit()
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

        quiz_id = await queries.create_quiz(
            conn,
            title=clean_title,
            description=description,
            category="Mikrobiologiya",
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
        logger.info(f"Successfully seeded quiz ID {quiz_id} ('{clean_title}') with {inserted} questions.")

async def _seed_all_physiology_collections(conn):
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
    collections_dir = config.DATA_DIR / "fiziologiya_collections"

    for col_num, clean_title, description, filename in FIZIOLOGIYA_COLLECTIONS:
        seed_key = f"seed_fiziologiya_mavzu_{col_num:02d}_v1"

        async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
            if await cursor.fetchone():
                continue

        async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (clean_title,)) as cursor:
            if await cursor.fetchone():
                await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
                await conn.commit()
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

        quiz_id = await queries.create_quiz(
            conn,
            title=clean_title,
            description=description,
            category="Normal fiziologiya",
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
        logger.info(f"Successfully seeded quiz ID {quiz_id} ('{clean_title}') with {inserted} questions.")

async def _seed_biochemistry_true_false(conn):
    seed_key = "seed_biokimyo_ha_yoq_120_v2"
    quiz_title = "Biokimyo: Ha / Yo'q testlari"

    async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
        if await cursor.fetchone():
            return

    csv_path = config.DATA_DIR / "biokimyo_collections" / "biokimyo_ha_yoq_120.csv"
    if not csv_path.exists():
        csv_path = config.DATA_DIR / "biokimyo_collections" / "biokimyo_ha_yoq_68.csv"
    if not csv_path.exists():
        logger.warning(f"Seed CSV not found at {csv_path}")
        return

    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
    questions_data = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions_data.append({
                "question": row["question"].strip(),
                "option_a": row["option_a"].strip(),
                "option_b": row["option_b"].strip(),
                "option_c": row.get("option_c", "").strip(),
                "option_d": row.get("option_d", "").strip(),
                "correct_answer": row["correct_answer"].strip().upper(),
                "explanation": row.get("explanation", "").strip(),
                "topic": row.get("topic", "").strip(),
                "difficulty": row.get("difficulty", "Medium").strip(),
                "timer": int(row.get("timer", 20)) if row.get("timer") else 20,
                "image": row.get("image", "").strip() or None
            })

    existing_quiz_id = None
    async with conn.execute(
        "SELECT id FROM quizzes WHERE title = ? OR title = 'Biokimyo: Ha / Yo''q testlari (68 ta savol)'",
        (quiz_title,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            existing_quiz_id = row[0]

    if existing_quiz_id:
        await conn.execute(
            """
            UPDATE quizzes
            SET title = ?,
                description = ?
            WHERE id = ?
            """,
            (
                quiz_title,
                "Biokimyo fanidan 'Ha' yoki 'Yo'q' (to'g'ri/noto'g'ri) tasdiq testlari to'plami (Sabirova, Yuldashev darsligi asosida).",
                existing_quiz_id
            )
        )
        await conn.execute("DELETE FROM question_options WHERE question_id IN (SELECT id FROM questions WHERE quiz_id = ?)", (existing_quiz_id,))
        await conn.execute("DELETE FROM questions WHERE quiz_id = ?", (existing_quiz_id,))
        await conn.commit()
        quiz_id = existing_quiz_id
    else:
        quiz_id = await queries.create_quiz(
            conn,
            title=quiz_title,
            description="Biokimyo fanidan 'Ha' yoki 'Yo'q' (to'g'ri/noto'g'ri) tasdiq testlari to'plami (Sabirova, Yuldashev darsligi asosida).",
            category="Biokimyo",
            default_timer=20,
            shuffle_options=False,
            show_explanation=True,
            pass_percentage=70,
            is_published=True,
            created_by=admin_id
        )

    inserted = await queries.bulk_insert_questions(conn, quiz_id, questions_data)
    await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
    await conn.commit()
    logger.info(f"Successfully seeded quiz ID {quiz_id} ('{quiz_title}') with {inserted} questions.")

async def _seed_biochemistry_variantli(conn):
    seed_key = "seed_biokimyo_variantli_209_v1"
    quiz_title = "biokimyo variantli"

    async with conn.execute("SELECT seed_name FROM system_seeds WHERE seed_name = ?", (seed_key,)) as cursor:
        if await cursor.fetchone():
            return

    async with conn.execute("SELECT id FROM quizzes WHERE title = ?", (quiz_title,)) as cursor:
        if await cursor.fetchone():
            await conn.execute("INSERT OR REPLACE INTO system_seeds (seed_name) VALUES (?)", (seed_key,))
            await conn.commit()
            return

    csv_path = config.DATA_DIR / "biokimyo_collections" / "biokimyo_variantli_209.csv"
    if not csv_path.exists():
        logger.warning(f"Seed CSV not found at {csv_path}")
        return

    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else 5606522749
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

    quiz_id = await queries.create_quiz(
        conn,
        title=quiz_title,
        description="Biokimyo fanidan variantli test savollari to'plami (209 ta savol).",
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


