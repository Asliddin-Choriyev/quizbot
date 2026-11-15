import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import aiosqlite

from bot.database.models import (
    User, Quiz, Question, QuestionOption, QuizSession,
    SessionAnswer, GroupCompetition, GroupParticipant
)

logger = logging.getLogger(__name__)

# ==========================================
# USER QUERIES
# ==========================================

async def upsert_user(
    conn: aiosqlite.Connection,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    language_code: str = "uz",
    is_admin: bool = False
) -> User:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, last_name, language_code, is_admin, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            is_admin = CASE WHEN excluded.is_admin = 1 THEN 1 ELSE users.is_admin END,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *
        """,
        (telegram_id, username, first_name, last_name, language_code, int(is_admin))
    ) as cursor:
        row = await cursor.fetchone()
        await conn.commit()
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            real_name=row["real_name"] if "real_name" in row.keys() else None,
            phone_number=row["phone_number"] if "phone_number" in row.keys() else None,
            student_group=row["student_group"] if "student_group" in row.keys() else None,
            language_code=row["language_code"],
            is_admin=bool(row["is_admin"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

async def get_user(conn: aiosqlite.Connection, telegram_id: int) -> Optional[User]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            real_name=row["real_name"] if "real_name" in row.keys() else None,
            phone_number=row["phone_number"] if "phone_number" in row.keys() else None,
            student_group=row["student_group"] if "student_group" in row.keys() else None,
            language_code=row["language_code"],
            is_admin=bool(row["is_admin"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

async def update_user_profile(
    conn: aiosqlite.Connection,
    telegram_id: int,
    real_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    student_group: Optional[str] = None
) -> bool:
    updates = []
    params = []
    if real_name is not None:
        updates.append("real_name = ?")
        params.append(real_name)
    if phone_number is not None:
        updates.append("phone_number = ?")
        params.append(phone_number)
    if student_group is not None:
        updates.append("student_group = ?")
        params.append(student_group)
    if not updates:
        return False
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(telegram_id)
    await conn.execute(
        f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?",
        params
    )
    await conn.commit()
    return True

async def get_user_stats(conn: aiosqlite.Connection, telegram_id: int) -> Dict[str, Any]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            COUNT(id) as total_attempts,
            SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_count,
            AVG(score_percentage) as avg_score,
            SUM(correct_count) as total_correct,
            SUM(total_questions) as total_questions_answered,
            SUM(duration_seconds) as total_duration
        FROM quiz_sessions
        WHERE user_id = ? AND status = 'completed'
        """,
        (telegram_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row or row["total_attempts"] == 0:
            return {
                "total_attempts": 0,
                "passed_count": 0,
                "avg_score": 0.0,
                "total_correct": 0,
                "total_questions_answered": 0,
                "total_duration": 0.0
            }
        return {
            "total_attempts": row["total_attempts"] or 0,
            "passed_count": row["passed_count"] or 0,
            "avg_score": round(row["avg_score"] or 0.0, 1),
            "total_correct": row["total_correct"] or 0,
            "total_questions_answered": row["total_questions_answered"] or 0,
            "total_duration": round(row["total_duration"] or 0.0, 1)
        }

async def list_users(
    conn: aiosqlite.Connection,
    page: int = 0,
    page_size: int = 8,
    exclude_admins: bool = True
) -> Tuple[List[Dict[str, Any]], int]:
    conn.row_factory = aiosqlite.Row
    total = await count_users(conn, exclude_admins=exclude_admins)
    offset = page * page_size
    where_clause = "WHERE u.is_admin = 0" if exclude_admins else ""
    async with conn.execute(
        f"""
        SELECT 
            u.*,
            COUNT(qs.id) as total_attempts,
            AVG(qs.score_percentage) as avg_score
        FROM users u
        LEFT JOIN quiz_sessions qs ON u.telegram_id = qs.user_id AND qs.status = 'completed'
        {where_clause}
        GROUP BY u.id
        ORDER BY u.id DESC
        LIMIT ? OFFSET ?
        """,
        (page_size, offset)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows], total

async def get_user_details(conn: aiosqlite.Connection, telegram_id: int) -> Optional[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            u.*,
            COUNT(qs.id) as total_attempts,
            SUM(CASE WHEN qs.passed = 1 THEN 1 ELSE 0 END) as passed_count,
            AVG(qs.score_percentage) as avg_score,
            MAX(qs.start_time) as last_active
        FROM users u
        LEFT JOIN quiz_sessions qs ON u.telegram_id = qs.user_id AND qs.status = 'completed'
        WHERE u.telegram_id = ?
        GROUP BY u.id
        """,
        (telegram_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_all_users_export_data(conn: aiosqlite.Connection, exclude_admins: bool = True) -> List[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    where_clause = "WHERE u.is_admin = 0" if exclude_admins else ""
    async with conn.execute(
        f"""
        SELECT 
            u.id,
            u.telegram_id,
            u.username,
            u.first_name,
            u.last_name,
            u.real_name,
            u.student_group,
            u.phone_number,
            u.language_code,
            u.created_at,
            COUNT(qs.id) as total_attempts,
            SUM(CASE WHEN qs.passed = 1 THEN 1 ELSE 0 END) as passed_count,
            AVG(qs.score_percentage) as avg_score,
            MAX(qs.start_time) as last_active
        FROM users u
        LEFT JOIN quiz_sessions qs ON u.telegram_id = qs.user_id AND qs.status = 'completed'
        {where_clause}
        GROUP BY u.id
        ORDER BY u.id ASC
        """
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def set_user_language(conn: aiosqlite.Connection, telegram_id: int, language_code: str) -> bool:
    await conn.execute(
        "UPDATE users SET language_code = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
        (language_code, telegram_id)
    )
    await conn.commit()
    return True

async def count_users(conn: aiosqlite.Connection, exclude_admins: bool = True) -> int:
    sql = "SELECT COUNT(*) FROM users WHERE is_admin = 0" if exclude_admins else "SELECT COUNT(*) FROM users"
    async with conn.execute(sql) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0

async def delete_user(conn: aiosqlite.Connection, telegram_id: int) -> bool:
    await conn.execute("PRAGMA foreign_keys = ON;")
    # Cascading cleanup
    await conn.execute(
        """
        DELETE FROM session_answers 
        WHERE session_id IN (SELECT id FROM quiz_sessions WHERE user_id = ?)
           OR user_id = ?
        """,
        (telegram_id, telegram_id)
    )
    await conn.execute("DELETE FROM quiz_sessions WHERE user_id = ?", (telegram_id,))
    await conn.execute("DELETE FROM group_answers WHERE user_id = ?", (telegram_id,))
    await conn.execute("DELETE FROM group_participants WHERE user_id = ?", (telegram_id,))
    await conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
    await conn.commit()
    return True

async def clear_all_non_admin_users(conn: aiosqlite.Connection) -> int:
    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute(
        """
        DELETE FROM session_answers 
        WHERE user_id IN (SELECT telegram_id FROM users WHERE is_admin = 0)
        """
    )
    await conn.execute(
        """
        DELETE FROM quiz_sessions 
        WHERE user_id IN (SELECT telegram_id FROM users WHERE is_admin = 0)
        """
    )
    await conn.execute(
        """
        DELETE FROM group_answers 
        WHERE user_id IN (SELECT telegram_id FROM users WHERE is_admin = 0)
        """
    )
    await conn.execute(
        """
        DELETE FROM group_participants 
        WHERE user_id IN (SELECT telegram_id FROM users WHERE is_admin = 0)
        """
    )
    async with conn.execute("DELETE FROM users WHERE is_admin = 0") as cursor:
        deleted = cursor.rowcount
    await conn.commit()
    return deleted

# ==========================================
# QUIZ QUERIES
# ==========================================

async def create_quiz(
    conn: aiosqlite.Connection,
    title: str,
    description: Optional[str] = None,
    category: str = "General",
    default_timer: int = 30,
    shuffle_options: bool = True,
    show_explanation: bool = True,
    pass_percentage: int = 60,
    is_published: bool = True,
    created_by: Optional[int] = None
) -> int:
    async with conn.execute(
        """
        INSERT INTO quizzes (
            title, description, category, default_timer, shuffle_options,
            show_explanation, pass_percentage, is_published, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title, description, category, default_timer,
            int(shuffle_options), int(show_explanation),
            pass_percentage, int(is_published), created_by
        )
    ) as cursor:
        quiz_id = cursor.lastrowid
        await conn.commit()
        return quiz_id

async def get_quiz(conn: aiosqlite.Connection, quiz_id: int) -> Optional[Quiz]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT q.*, COUNT(qs.id) as question_count
        FROM quizzes q
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        WHERE q.id = ?
        GROUP BY q.id
        """,
        (quiz_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        return Quiz(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            default_timer=row["default_timer"],
            shuffle_options=bool(row["shuffle_options"]),
            show_explanation=bool(row["show_explanation"]),
            pass_percentage=row["pass_percentage"],
            is_published=bool(row["is_published"]),
            created_by=row["created_by"],
            question_count=row["question_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

async def list_quizzes(
    conn: aiosqlite.Connection,
    published_only: bool = False,
    offset: int = 0,
    limit: int = 50
) -> List[Quiz]:
    conn.row_factory = aiosqlite.Row
    where_clause = "WHERE q.is_published = 1" if published_only else ""
    sql = f"""
        SELECT q.*, COUNT(qs.id) as question_count
        FROM quizzes q
        LEFT JOIN questions qs ON q.id = qs.quiz_id
        {where_clause}
        GROUP BY q.id
        ORDER BY q.id DESC
        LIMIT ? OFFSET ?
    """
    async with conn.execute(sql, (limit, offset)) as cursor:
        rows = await cursor.fetchall()
        quizzes = []
        for r in rows:
            quizzes.append(
                Quiz(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"],
                    category=r["category"],
                    default_timer=r["default_timer"],
                    shuffle_options=bool(r["shuffle_options"]),
                    show_explanation=bool(r["show_explanation"]),
                    pass_percentage=r["pass_percentage"],
                    is_published=bool(r["is_published"]),
                    created_by=r["created_by"],
                    question_count=r["question_count"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"]
                )
            )
        return quizzes

async def count_quizzes(conn: aiosqlite.Connection, published_only: bool = False) -> int:
    where = "WHERE is_published = 1" if published_only else ""
    async with conn.execute(f"SELECT COUNT(*) FROM quizzes {where}") as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_quiz(conn: aiosqlite.Connection, quiz_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    values = [int(v) if isinstance(v, bool) else v for v in kwargs.values()]
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    set_clause += ", updated_at = CURRENT_TIMESTAMP"
    values.append(quiz_id)
    await conn.execute(f"UPDATE quizzes SET {set_clause} WHERE id = ?", values)
    await conn.commit()
    return True

async def delete_quiz(conn: aiosqlite.Connection, quiz_id: int) -> bool:
    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute("DELETE FROM question_options WHERE question_id IN (SELECT id FROM questions WHERE quiz_id = ?)", (quiz_id,))
    await conn.execute("DELETE FROM questions WHERE quiz_id = ?", (quiz_id,))
    await conn.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    await conn.commit()
    return True

async def toggle_quiz_publish(conn: aiosqlite.Connection, quiz_id: int) -> bool:
    await conn.execute(
        "UPDATE quizzes SET is_published = 1 - is_published, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (quiz_id,)
    )
    await conn.commit()
    return True

async def get_quiz_stats(conn: aiosqlite.Connection, quiz_id: int) -> Dict[str, Any]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            COUNT(*) as total_plays,
            COALESCE(AVG(score_percentage), 0.0) as avg_score,
            COALESCE(SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END), 0) as passed_count,
            COALESCE(AVG(duration_seconds), 0.0) as avg_duration
        FROM quiz_sessions
        WHERE quiz_id = ? AND status = 'completed'
        """,
        (quiz_id,)
    ) as cursor:
        row = await cursor.fetchone()
        total = row["total_plays"]
        passed = row["passed_count"]
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0
        return {
            "total_plays": total,
            "avg_score": round(row["avg_score"], 1),
            "passed_count": passed,
            "pass_rate": round(pass_rate, 1),
            "avg_duration": round(row["avg_duration"], 1)
        }

# ==========================================
# QUESTION QUERIES
# ==========================================

async def add_question(
    conn: aiosqlite.Connection,
    quiz_id: int,
    question_text: str,
    explanation: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: str = "Medium",
    timer_seconds: Optional[int] = None,
    image_url: Optional[str] = None,
    order_num: int = 0
) -> int:
    async with conn.execute(
        """
        INSERT INTO questions (
            quiz_id, question_text, explanation, topic,
            difficulty, timer_seconds, image_url, order_num
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (quiz_id, question_text, explanation, topic, difficulty, timer_seconds, image_url, order_num)
    ) as cursor:
        q_id = cursor.lastrowid
        await conn.commit()
        return q_id

async def add_question_options(
    conn: aiosqlite.Connection,
    question_id: int,
    options: List[Dict[str, Any]]
):
    """
    options: List of dicts e.g.
    [{'option_label': 'A', 'option_text': 'Text', 'is_correct': True}, ...]
    """
    params = [
        (question_id, opt["option_label"], opt["option_text"], int(opt.get("is_correct", False)))
        for opt in options
    ]
    await conn.executemany(
        """
        INSERT INTO question_options (question_id, option_label, option_text, is_correct)
        VALUES (?, ?, ?, ?)
        """,
        params
    )
    await conn.commit()

async def bulk_insert_questions(
    conn: aiosqlite.Connection,
    quiz_id: int,
    questions_data: List[Dict[str, Any]]
) -> int:
    """
    High-performance bulk insert for thousands of questions.
    Each item in questions_data contains:
      question, option_a, option_b, option_c, option_d,
      correct_answer ('A','B','C','D'), explanation, topic, difficulty, timer, image
    """
    inserted_count = 0
    await conn.execute("BEGIN TRANSACTION")
    try:
        for idx, item in enumerate(questions_data):
            q_cursor = await conn.execute(
                """
                INSERT INTO questions (
                    quiz_id, question_text, explanation, topic,
                    difficulty, timer_seconds, image_url, order_num
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quiz_id,
                    item["question"],
                    item.get("explanation"),
                    item.get("topic"),
                    item.get("difficulty", "Medium"),
                    item.get("timer"),
                    item.get("image"),
                    idx + 1
                )
            )
            q_id = q_cursor.lastrowid
            correct_label = str(item.get("correct_answer", "")).strip().upper()

            options_to_insert = [
                (q_id, "A", item["option_a"], 1 if correct_label == "A" else 0),
                (q_id, "B", item["option_b"], 1 if correct_label == "B" else 0),
                (q_id, "C", item["option_c"], 1 if correct_label == "C" else 0),
                (q_id, "D", item["option_d"], 1 if correct_label == "D" else 0),
            ]
            await conn.executemany(
                """
                INSERT INTO question_options (question_id, option_label, option_text, is_correct)
                VALUES (?, ?, ?, ?)
                """,
                options_to_insert
            )
            inserted_count += 1

        await conn.commit()
        return inserted_count
    except Exception as e:
        await conn.rollback()
        logger.error(f"Error in bulk_insert_questions: {e}")
        raise

async def get_question(conn: aiosqlite.Connection, question_id: int) -> Optional[Question]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)) as cursor:
        q_row = await cursor.fetchone()
        if not q_row:
            return None

    async with conn.execute(
        "SELECT * FROM question_options WHERE question_id = ? ORDER BY option_label ASC",
        (question_id,)
    ) as cursor:
        opt_rows = await cursor.fetchall()
        options = [
            QuestionOption(
                id=o["id"],
                question_id=o["question_id"],
                option_label=o["option_label"],
                option_text=o["option_text"],
                is_correct=bool(o["is_correct"])
            )
            for o in opt_rows
        ]

    return Question(
        id=q_row["id"],
        quiz_id=q_row["quiz_id"],
        question_text=q_row["question_text"],
        options=options,
        explanation=q_row["explanation"],
        topic=q_row["topic"],
        difficulty=q_row["difficulty"],
        timer_seconds=q_row["timer_seconds"],
        image_url=q_row["image_url"],
        order_num=q_row["order_num"],
        created_at=q_row["created_at"]
    )

async def get_question_ids_by_quiz(conn: aiosqlite.Connection, quiz_id: int) -> List[int]:
    async with conn.execute(
        "SELECT id FROM questions WHERE quiz_id = ? ORDER BY order_num ASC, id ASC",
        (quiz_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

async def delete_question(conn: aiosqlite.Connection, question_id: int) -> bool:
    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute("DELETE FROM question_options WHERE question_id = ?", (question_id,))
    await conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    await conn.commit()
    return True

async def count_questions(conn: aiosqlite.Connection, quiz_id: Optional[int] = None) -> int:
    if quiz_id:
        sql = "SELECT COUNT(*) FROM questions WHERE quiz_id = ?"
        params = (quiz_id,)
    else:
        sql = "SELECT COUNT(*) FROM questions"
        params = ()
    async with conn.execute(sql, params) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0

# ==========================================
# QUIZ SESSION QUERIES (Individual)
# ==========================================

async def create_session(
    conn: aiosqlite.Connection,
    session_code: str,
    quiz_id: int,
    user_id: int,
    chat_id: int,
    total_questions: int,
    question_ids: List[int]
) -> int:
    order_json = json.dumps(question_ids)
    async with conn.execute(
        """
        INSERT INTO quiz_sessions (
            session_code, quiz_id, user_id, chat_id, is_group,
            status, current_question_index, total_questions,
            question_ids_order, start_time
        ) VALUES (?, ?, ?, ?, 0, 'in_progress', 0, ?, ?, CURRENT_TIMESTAMP)
        """,
        (session_code, quiz_id, user_id, chat_id, total_questions, order_json)
    ) as cursor:
        s_id = cursor.lastrowid
        await conn.commit()
        return s_id

async def get_session(conn: aiosqlite.Connection, session_id: int) -> Optional[QuizSession]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute("SELECT * FROM quiz_sessions WHERE id = ?", (session_id,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        q_order = json.loads(row["question_ids_order"]) if row["question_ids_order"] else []
        return QuizSession(
            id=row["id"],
            session_code=row["session_code"],
            quiz_id=row["quiz_id"],
            user_id=row["user_id"],
            chat_id=row["chat_id"],
            is_group=bool(row["is_group"]),
            status=row["status"],
            current_question_index=row["current_question_index"],
            total_questions=row["total_questions"],
            correct_count=row["correct_count"],
            incorrect_count=row["incorrect_count"],
            unanswered_count=row["unanswered_count"],
            score_percentage=row["score_percentage"],
            passed=bool(row["passed"]),
            question_ids_order=q_order,
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_seconds=row["duration_seconds"]
        )

async def get_session_by_code(conn: aiosqlite.Connection, code: str) -> Optional[QuizSession]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute("SELECT * FROM quiz_sessions WHERE session_code = ?", (code,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        q_order = json.loads(row["question_ids_order"]) if row["question_ids_order"] else []
        return QuizSession(
            id=row["id"],
            session_code=row["session_code"],
            quiz_id=row["quiz_id"],
            user_id=row["user_id"],
            chat_id=row["chat_id"],
            is_group=bool(row["is_group"]),
            status=row["status"],
            current_question_index=row["current_question_index"],
            total_questions=row["total_questions"],
            correct_count=row["correct_count"],
            incorrect_count=row["incorrect_count"],
            unanswered_count=row["unanswered_count"],
            score_percentage=row["score_percentage"],
            passed=bool(row["passed"]),
            question_ids_order=q_order,
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_seconds=row["duration_seconds"]
        )

async def get_active_session_for_user(conn: aiosqlite.Connection, user_id: int) -> Optional[QuizSession]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT * FROM quiz_sessions 
        WHERE user_id = ? AND status = 'in_progress' AND is_group = 0
        ORDER BY id DESC LIMIT 1
        """,
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        q_order = json.loads(row["question_ids_order"]) if row["question_ids_order"] else []
        return QuizSession(
            id=row["id"],
            session_code=row["session_code"],
            quiz_id=row["quiz_id"],
            user_id=row["user_id"],
            chat_id=row["chat_id"],
            is_group=bool(row["is_group"]),
            status=row["status"],
            current_question_index=row["current_question_index"],
            total_questions=row["total_questions"],
            correct_count=row["correct_count"],
            incorrect_count=row["incorrect_count"],
            unanswered_count=row["unanswered_count"],
            score_percentage=row["score_percentage"],
            passed=bool(row["passed"]),
            question_ids_order=q_order,
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_seconds=row["duration_seconds"]
        )

async def update_session(conn: aiosqlite.Connection, session_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    values = [int(v) if isinstance(v, bool) else v for v in kwargs.values()]
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values.append(session_id)
    await conn.execute(f"UPDATE quiz_sessions SET {set_clause} WHERE id = ?", values)
    await conn.commit()
    return True

async def record_answer(
    conn: aiosqlite.Connection,
    session_id: int,
    question_id: int,
    user_id: int,
    selected_option: Optional[str],
    is_correct: bool,
    response_time_seconds: float
) -> bool:
    await conn.execute(
        """
        INSERT INTO session_answers (
            session_id, question_id, user_id, selected_option, is_correct, response_time_seconds
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id, question_id) DO NOTHING
        """,
        (session_id, question_id, user_id, selected_option, int(is_correct), response_time_seconds)
    )
    await conn.commit()
    return True

async def get_session_answers_details(conn: aiosqlite.Connection, session_id: int) -> List[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            sa.selected_option,
            sa.is_correct,
            sa.response_time_seconds,
            q.id as question_id,
            q.question_text,
            q.explanation
        FROM session_answers sa
        JOIN questions q ON sa.question_id = q.id
        WHERE sa.session_id = ?
        ORDER BY sa.id ASC
        """,
        (session_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "question_id": r["question_id"],
                "question_text": r["question_text"],
                "explanation": r["explanation"],
                "selected_option": r["selected_option"],
                "is_correct": bool(r["is_correct"]),
                "response_time_seconds": r["response_time_seconds"]
            })
        return results

async def complete_session(
    conn: aiosqlite.Connection,
    session_id: int,
    correct: int,
    incorrect: int,
    unanswered: int,
    score_percentage: float,
    passed: bool,
    duration_seconds: float
) -> bool:
    await conn.execute(
        """
        UPDATE quiz_sessions SET
            status = 'completed',
            correct_count = ?,
            incorrect_count = ?,
            unanswered_count = ?,
            score_percentage = ?,
            passed = ?,
            duration_seconds = ?,
            end_time = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (correct, incorrect, unanswered, score_percentage, int(passed), duration_seconds, session_id)
    )
    await conn.commit()
    return True

async def get_user_results(
    conn: aiosqlite.Connection,
    user_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT qs.*, q.title as quiz_title
        FROM quiz_sessions qs
        JOIN quizzes q ON qs.quiz_id = q.id
        WHERE qs.user_id = ? AND qs.status = 'completed'
        ORDER BY qs.id DESC
        LIMIT ?
        """,
        (user_id, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def get_quiz_leaderboard(
    conn: aiosqlite.Connection,
    quiz_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            qs.user_id,
            u.username,
            u.first_name,
            u.last_name,
            u.real_name,
            u.student_group,
            MAX(qs.score_percentage) as best_score,
            MIN(qs.duration_seconds) as best_duration,
            COUNT(qs.id) as attempts
        FROM quiz_sessions qs
        JOIN users u ON qs.user_id = u.telegram_id
        WHERE qs.quiz_id = ? AND qs.status = 'completed' AND u.is_admin = 0
        GROUP BY qs.user_id
        ORDER BY best_score DESC, best_duration ASC
        LIMIT ?
        """,
        (quiz_id, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

# ==========================================
# GROUP COMPETITION QUERIES
# ==========================================

async def create_group_competition(
    conn: aiosqlite.Connection,
    quiz_id: int,
    chat_id: int,
    created_by: int,
    total_questions: int,
    timer_seconds: int,
    question_ids: List[int]
) -> int:
    order_json = json.dumps(question_ids)
    async with conn.execute(
        """
        INSERT INTO group_competitions (
            quiz_id, chat_id, created_by, status,
            current_question_index, total_questions,
            timer_seconds, question_ids_order
        ) VALUES (?, ?, ?, 'lobby', 0, ?, ?, ?)
        """,
        (quiz_id, chat_id, created_by, total_questions, timer_seconds, order_json)
    ) as cursor:
        comp_id = cursor.lastrowid
        await conn.commit()
        return comp_id

async def get_active_group_competition(
    conn: aiosqlite.Connection,
    chat_id: int
) -> Optional[GroupCompetition]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT * FROM group_competitions
        WHERE chat_id = ? AND status IN ('lobby', 'active')
        ORDER BY id DESC LIMIT 1
        """,
        (chat_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        q_order = json.loads(row["question_ids_order"]) if row["question_ids_order"] else []
        return GroupCompetition(
            id=row["id"],
            quiz_id=row["quiz_id"],
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            status=row["status"],
            current_question_index=row["current_question_index"],
            total_questions=row["total_questions"],
            timer_seconds=row["timer_seconds"],
            round_end_time=row["round_end_time"],
            question_ids_order=q_order,
            created_by=row["created_by"],
            created_at=row["created_at"]
        )

async def get_group_competition(
    conn: aiosqlite.Connection,
    comp_id: int
) -> Optional[GroupCompetition]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute("SELECT * FROM group_competitions WHERE id = ?", (comp_id,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        q_order = json.loads(row["question_ids_order"]) if row["question_ids_order"] else []
        return GroupCompetition(
            id=row["id"],
            quiz_id=row["quiz_id"],
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            status=row["status"],
            current_question_index=row["current_question_index"],
            total_questions=row["total_questions"],
            timer_seconds=row["timer_seconds"],
            round_end_time=row["round_end_time"],
            question_ids_order=q_order,
            created_by=row["created_by"],
            created_at=row["created_at"]
        )

async def update_group_competition(conn: aiosqlite.Connection, comp_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    values = [int(v) if isinstance(v, bool) else v for v in kwargs.values()]
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values.append(comp_id)
    await conn.execute(f"UPDATE group_competitions SET {set_clause} WHERE id = ?", values)
    await conn.commit()
    return True

async def register_group_participant(
    conn: aiosqlite.Connection,
    competition_id: int,
    user_id: int,
    username: Optional[str],
    full_name: str
) -> bool:
    await conn.execute(
        """
        INSERT INTO group_participants (competition_id, user_id, username, full_name)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(competition_id, user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
        """,
        (competition_id, user_id, username, full_name)
    )
    await conn.commit()
    return True

async def get_group_participants(
    conn: aiosqlite.Connection,
    competition_id: int
) -> List[GroupParticipant]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT * FROM group_participants
        WHERE competition_id = ?
        ORDER BY score DESC, total_response_time ASC
        """,
        (competition_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [
            GroupParticipant(
                id=r["id"],
                competition_id=r["competition_id"],
                user_id=r["user_id"],
                username=r["username"],
                full_name=r["full_name"],
                score=r["score"],
                correct_answers=r["correct_answers"],
                total_answered=r["total_answered"],
                total_response_time=r["total_response_time"]
            )
            for r in rows
        ]

async def has_user_answered_group_question(
    conn: aiosqlite.Connection,
    competition_id: int,
    question_id: int,
    user_id: int
) -> bool:
    async with conn.execute(
        """
        SELECT id FROM group_answers
        WHERE competition_id = ? AND question_id = ? AND user_id = ?
        """,
        (competition_id, question_id, user_id)
    ) as cursor:
        row = await cursor.fetchone()
        return row is not None

async def record_group_answer(
    conn: aiosqlite.Connection,
    competition_id: int,
    question_id: int,
    user_id: int,
    username: Optional[str],
    full_name: str,
    selected_option: str,
    is_correct: bool,
    response_time_seconds: float,
    points: int = 10
) -> bool:
    # 1. Ensure participant registered
    await register_group_participant(conn, competition_id, user_id, username, full_name)

    # 2. Insert answer
    try:
        await conn.execute(
            """
            INSERT INTO group_answers (
                competition_id, question_id, user_id, selected_option, is_correct, response_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (competition_id, question_id, user_id, selected_option, int(is_correct), response_time_seconds)
        )
    except aiosqlite.IntegrityError:
        # Already answered
        return False

    # 3. Update participant score
    score_increment = points if is_correct else 0
    correct_increment = 1 if is_correct else 0
    await conn.execute(
        """
        UPDATE group_participants SET
            score = score + ?,
            correct_answers = correct_answers + ?,
            total_answered = total_answered + 1,
            total_response_time = total_response_time + ?
        WHERE competition_id = ? AND user_id = ?
        """,
        (score_increment, correct_increment, response_time_seconds, competition_id, user_id)
    )
    await conn.commit()
    return True

async def get_all_results_for_export(conn: aiosqlite.Connection, quiz_id: int) -> List[Dict[str, Any]]:
    conn.row_factory = aiosqlite.Row
    async with conn.execute(
        """
        SELECT 
            qs.id as session_id,
            qs.user_id,
            u.username,
            u.first_name,
            u.last_name,
            u.real_name,
            u.student_group,
            u.phone_number,
            qs.score_percentage,
            qs.correct_count,
            qs.incorrect_count,
            qs.unanswered_count,
            qs.total_questions,
            qs.passed,
            qs.duration_seconds,
            qs.start_time,
            qs.end_time
        FROM quiz_sessions qs
        JOIN users u ON qs.user_id = u.telegram_id
        WHERE qs.quiz_id = ? AND qs.status = 'completed' AND u.is_admin = 0
        ORDER BY qs.score_percentage DESC, qs.duration_seconds ASC
        """,
        (quiz_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
