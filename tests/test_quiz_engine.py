import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from aiogram.types import PollAnswer, User as TgUser

from bot.database.db import Database
from bot.database import queries
from bot.services.quiz_engine import QuizEngine

@pytest.mark.asyncio
async def test_quiz_engine_session_and_answers(tmp_path: Path):
    db_file = tmp_path / "engine_test.db"
    db = Database(db_file)
    await db.init()

    # Create mock Bot
    mock_bot = AsyncMock()
    mock_poll = MagicMock()
    mock_poll.id = "poll_test_123"
    mock_poll_msg = MagicMock(message_id=101, poll=mock_poll)
    mock_bot.send_poll.return_value = mock_poll_msg

    engine = QuizEngine(bot=mock_bot, db=db)

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Engine Quiz", pass_percentage=50, default_timer=20, shuffle_options=False)
        # Question 1 (correct: A)
        q1_id = await queries.add_question(conn, quiz_id, "Question 1?")
        await queries.add_question_options(conn, q1_id, [
            {"option_label": "A", "option_text": "Apple", "is_correct": True},
            {"option_label": "B", "option_text": "Banana", "is_correct": False},
            {"option_label": "C", "option_text": "Cherry", "is_correct": False},
            {"option_label": "D", "option_text": "Date", "is_correct": False},
        ])
        # Question 2 (correct: B)
        q2_id = await queries.add_question(conn, quiz_id, "Question 2?")
        await queries.add_question_options(conn, q2_id, [
            {"option_label": "A", "option_text": "Dog", "is_correct": False},
            {"option_label": "B", "option_text": "Cat", "is_correct": True},
            {"option_label": "C", "option_text": "Elephant", "is_correct": False},
            {"option_label": "D", "option_text": "Fox", "is_correct": False},
        ])

    # 1. Start quiz session (sends question 1 as native quiz poll)
    session = await engine.start_quiz_session(user_id=555, chat_id=555, quiz_id=quiz_id, lang="uz")
    assert session is not None
    assert session.status == "in_progress"
    assert session.total_questions == 2
    assert mock_bot.send_poll.called

    # 2. Simulate User answering Question 1 correctly (option index 0 = A)
    poll_answer1 = PollAnswer(
        poll_id="poll_test_123",
        user=TgUser(id=555, is_bot=False, first_name="Ali"),
        option_ids=[0]
    )

    # Next question poll mock
    mock_poll2 = MagicMock()
    mock_poll2.id = "poll_test_456"
    mock_poll_msg2 = MagicMock(message_id=102, poll=mock_poll2)
    mock_bot.send_poll.return_value = mock_poll_msg2

    await engine.process_poll_answer(poll_answer1, lang="uz")

    # Verify session progressed to question 2
    async with db.get_connection() as conn:
        s_mid = await queries.get_session_by_code(conn, session.session_code)
        assert s_mid.current_question_index == 1
        assert s_mid.correct_count == 1
        assert s_mid.incorrect_count == 0

    # 3. Simulate User answering Question 2 incorrectly (option index 2 = C)
    poll_answer2 = PollAnswer(
        poll_id="poll_test_456",
        user=TgUser(id=555, is_bot=False, first_name="Ali"),
        option_ids=[2]
    )
    await engine.process_poll_answer(poll_answer2, lang="uz")

    # Session should now be completed
    async with db.get_connection() as conn:
        s_final = await queries.get_session_by_code(conn, session.session_code)
        assert s_final.status == "completed"
        assert s_final.correct_count == 1
        assert s_final.incorrect_count == 1
        assert s_final.score_percentage == 50.0
        assert s_final.passed is True
