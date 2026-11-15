import pytest
import aiosqlite
from pathlib import Path
from bot.database.db import Database
from bot.database import queries

@pytest.mark.asyncio
async def test_database_init_and_crud(tmp_path: Path):
    db_file = tmp_path / "test.db"
    db = Database(db_file)
    await db.init()
    assert db_file.exists()

    async with db.get_connection() as conn:
        # 1. User Upsert
        user = await queries.upsert_user(
            conn,
            telegram_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="uz",
            is_admin=True
        )
        assert user.telegram_id == 12345
        assert user.is_admin is True

        fetched_user = await queries.get_user(conn, 12345)
        assert fetched_user is not None
        assert fetched_user.username == "testuser"

        # Change language
        await queries.set_user_language(conn, 12345, "en")
        updated_user = await queries.get_user(conn, 12345)
        assert updated_user.language_code == "en"

        # 2. Quiz CRUD
        quiz_id = await queries.create_quiz(
            conn,
            title="Python Advanced",
            description="Test your python skills",
            category="Programming",
            default_timer=25,
            shuffle_options=True,
            show_explanation=True,
            pass_percentage=70,
            is_published=True,
            created_by=12345
        )
        assert quiz_id > 0

        quiz = await queries.get_quiz(conn, quiz_id)
        assert quiz.title == "Python Advanced"
        assert quiz.default_timer == 25
        assert quiz.pass_percentage == 70

        # Update quiz
        await queries.update_quiz(conn, quiz_id, default_timer=45, pass_percentage=80)
        q_updated = await queries.get_quiz(conn, quiz_id)
        assert q_updated.default_timer == 45
        assert q_updated.pass_percentage == 80

        # Toggle publish
        await queries.toggle_quiz_publish(conn, quiz_id)
        q_unpub = await queries.get_quiz(conn, quiz_id)
        assert q_unpub.is_published is False

        await queries.toggle_quiz_publish(conn, quiz_id)
        q_pub = await queries.get_quiz(conn, quiz_id)
        assert q_pub.is_published is True

@pytest.mark.asyncio
async def test_bulk_insert_1000_questions(tmp_path: Path):
    db_file = tmp_path / "bulk_test.db"
    db = Database(db_file)
    await db.init()

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Math 1000", default_timer=30)
        
        batch = []
        for i in range(1000):
            batch.append({
                "question": f"Question {i + 1}: What is {i} * 2?",
                "option_a": f"{i * 2}",
                "option_b": f"{i * 2 + 1}",
                "option_c": f"{i * 2 + 2}",
                "option_d": f"{i * 2 + 3}",
                "correct_answer": "A",
                "explanation": f"Explanation for question {i + 1}",
                "topic": "Arithmetic",
                "difficulty": "Easy",
                "timer": 30
            })

        inserted = await queries.bulk_insert_questions(conn, quiz_id, batch)
        assert inserted == 1000

        count = await queries.count_questions(conn, quiz_id)
        assert count == 1000

        q_ids = await queries.get_question_ids_by_quiz(conn, quiz_id)
        assert len(q_ids) == 1000

        # Inspect first question options
        q1 = await queries.get_question(conn, q_ids[0])
        assert q1.question_text == "Question 1: What is 0 * 2?"
        assert len(q1.options) == 4
        correct_opt = next((o for o in q1.options if o.is_correct), None)
        assert correct_opt is not None
        assert correct_opt.option_label == "A"
        assert correct_opt.option_text == "0"

@pytest.mark.asyncio
async def test_session_lifecycle_and_scoring(tmp_path: Path):
    db_file = tmp_path / "session_test.db"
    db = Database(db_file)
    await db.init()

    async with db.get_connection() as conn:
        user = await queries.upsert_user(conn, telegram_id=999, username="student1", first_name="Ali")
        quiz_id = await queries.create_quiz(conn, title="Exam", pass_percentage=50)
        
        # Add 2 questions
        q1_id = await queries.add_question(conn, quiz_id, "Q1")
        await queries.add_question_options(conn, q1_id, [
            {"option_label": "A", "option_text": "Opt A", "is_correct": True},
            {"option_label": "B", "option_text": "Opt B", "is_correct": False},
            {"option_label": "C", "option_text": "Opt C", "is_correct": False},
            {"option_label": "D", "option_text": "Opt D", "is_correct": False},
        ])

        q2_id = await queries.add_question(conn, quiz_id, "Q2")
        await queries.add_question_options(conn, q2_id, [
            {"option_label": "A", "option_text": "Opt A", "is_correct": False},
            {"option_label": "B", "option_text": "Opt B", "is_correct": True},
            {"option_label": "C", "option_text": "Opt C", "is_correct": False},
            {"option_label": "D", "option_text": "Opt D", "is_correct": False},
        ])

        # Create session
        sess_id = await queries.create_session(
            conn,
            session_code="sess_test_1",
            quiz_id=quiz_id,
            user_id=999,
            chat_id=999,
            total_questions=2,
            question_ids=[q1_id, q2_id]
        )
        assert sess_id > 0

        # Answer Q1 correctly
        await queries.record_answer(conn, sess_id, q1_id, 999, "A", is_correct=True, response_time_seconds=3.5)
        # Answer Q2 incorrectly
        await queries.record_answer(conn, sess_id, q2_id, 999, "C", is_correct=False, response_time_seconds=4.0)

        # Complete session: 1 correct out of 2 = 50%
        await queries.complete_session(
            conn,
            session_id=sess_id,
            correct=1,
            incorrect=1,
            unanswered=0,
            score_percentage=50.0,
            passed=True,
            duration_seconds=7.5
        )

        completed_sess = await queries.get_session(conn, sess_id)
        assert completed_sess.status == "completed"
        assert completed_sess.correct_count == 1
        assert completed_sess.score_percentage == 50.0
        assert completed_sess.passed is True

        # Check answers details
        details = await queries.get_session_answers_details(conn, sess_id)
        assert len(details) == 2
        assert details[0]["is_correct"] is True
        assert details[1]["is_correct"] is False

@pytest.mark.asyncio
async def test_group_competition(tmp_path: Path):
    db_file = tmp_path / "group_test.db"
    db = Database(db_file)
    await db.init()

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Group Battle")
        q1_id = await queries.add_question(conn, quiz_id, "Capital of France?")
        await queries.add_question_options(conn, q1_id, [
            {"option_label": "A", "option_text": "Paris", "is_correct": True},
            {"option_label": "B", "option_text": "Rome", "is_correct": False},
            {"option_label": "C", "option_text": "Berlin", "is_correct": False},
            {"option_label": "D", "option_text": "Madrid", "is_correct": False},
        ])

        comp_id = await queries.create_group_competition(
            conn,
            quiz_id=quiz_id,
            chat_id=-1001234567,
            created_by=111,
            total_questions=1,
            timer_seconds=20,
            question_ids=[q1_id]
        )
        assert comp_id > 0

        # User 1 registers and answers correctly
        success1 = await queries.record_group_answer(
            conn,
            competition_id=comp_id,
            question_id=q1_id,
            user_id=111,
            username="host",
            full_name="Host User",
            selected_option="A",
            is_correct=True,
            response_time_seconds=2.0,
            points=10
        )
        assert success1 is True

        # Duplicate answer rejected
        duplicate = await queries.record_group_answer(
            conn,
            competition_id=comp_id,
            question_id=q1_id,
            user_id=111,
            username="host",
            full_name="Host User",
            selected_option="B",
            is_correct=False,
            response_time_seconds=3.0,
            points=0
        )
        assert duplicate is False

        # User 2 answers incorrectly
        success2 = await queries.record_group_answer(
            conn,
            competition_id=comp_id,
            question_id=q1_id,
            user_id=222,
            username="player2",
            full_name="Player Two",
            selected_option="C",
            is_correct=False,
            response_time_seconds=4.0,
            points=0
        )
        assert success2 is True

        participants = await queries.get_group_participants(conn, comp_id)
        assert len(participants) == 2
        # Winner is User 1 with 10 points
        assert participants[0].user_id == 111
        assert participants[0].score == 10

@pytest.mark.asyncio
async def test_persistence_and_backup(tmp_path: Path):
    db_file = tmp_path / "persistent.db"
    db = Database(db_file)
    await db.init()

    # Write data
    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Persistent Quiz")
        q_id = await queries.add_question(conn, quiz_id, "Does SQLite persist?")

    # Simulate bot restart by creating new Database object with same path
    new_db = Database(db_file)
    async with new_db.get_connection() as conn:
        quiz = await queries.get_quiz(conn, quiz_id)
        assert quiz is not None
        assert quiz.title == "Persistent Quiz"
        assert quiz.question_count == 1

    # Test hot backup
    backup_dir = tmp_path / "backups"
    backup_file = await new_db.backup(backup_dir)
    assert backup_file.exists()

    # Verify backup contents
    backup_db = Database(backup_file)
    async with backup_db.get_connection() as conn:
        b_quiz = await queries.get_quiz(conn, quiz_id)
        assert b_quiz is not None
        assert b_quiz.title == "Persistent Quiz"

@pytest.mark.asyncio
async def test_user_profile_and_management(tmp_path: Path):
    db_file = tmp_path / "user_test.db"
    db = Database(db_file)
    await db.init()

    async with db.get_connection() as conn:
        # Create user
        await queries.upsert_user(conn, telegram_id=99999, username="student_bob", first_name="Bob")
        
        # Update profile
        updated = await queries.update_user_profile(
            conn,
            telegram_id=99999,
            real_name="Bobur Karimov",
            student_group="302-guruh, Davolash",
            phone_number="+998901234567"
        )
        assert updated is True

        user = await queries.get_user(conn, 99999)
        assert user.real_name == "Bobur Karimov"
        assert user.student_group == "302-guruh, Davolash"
        assert user.phone_number == "+998901234567"

        # Check list users
        users, total = await queries.list_users(conn, page=0, page_size=10)
        assert total == 1
        assert users[0]["telegram_id"] == 99999

        # Check export data
        export_data = await queries.get_all_users_export_data(conn)
        assert len(export_data) == 1
        assert export_data[0]["real_name"] == "Bobur Karimov"
