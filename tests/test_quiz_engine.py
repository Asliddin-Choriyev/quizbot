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

@pytest.mark.asyncio
async def test_group_quiz_engine_progression_and_timeout(tmp_path: Path):
    from bot.services.group_engine import GroupQuizEngine, cancel_group_timer

    db_file = tmp_path / "group_engine_test.db"
    db = Database(db_file)
    await db.init()

    mock_bot = AsyncMock()
    mock_msg = MagicMock(message_id=100)
    mock_bot.send_message.return_value = mock_msg
    mock_poll = MagicMock()
    mock_poll.id = "gpoll_1"
    mock_poll_msg = MagicMock(message_id=201, poll=mock_poll)
    mock_bot.send_poll.return_value = mock_poll_msg

    engine = GroupQuizEngine(bot=mock_bot, db=db)

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Group Quiz", pass_percentage=50, default_timer=5, shuffle_options=False)
        q1_id = await queries.add_question(conn, quiz_id, "GQuestion 1?")
        await queries.add_question_options(conn, q1_id, [
            {"option_label": "A", "option_text": "Alpha", "is_correct": True},
            {"option_label": "B", "option_text": "Beta", "is_correct": False},
        ])
        q2_id = await queries.add_question(conn, quiz_id, "GQuestion 2?")
        await queries.add_question_options(conn, q2_id, [
            {"option_label": "A", "option_text": "Gamma", "is_correct": False},
            {"option_label": "B", "option_text": "Delta", "is_correct": True},
        ])

    comp_id = await engine.open_lobby(chat_id=-100123, quiz_id=quiz_id, creator_id=999)
    assert comp_id is not None

    # Join participant
    mock_cb_join = MagicMock()
    mock_cb_join.from_user = TgUser(id=888, is_bot=False, first_name="Student1")
    mock_cb_join.answer = AsyncMock()
    await engine.handle_join(mock_cb_join, comp_id)

    # Start competition
    mock_cb_start = MagicMock()
    mock_cb_start.from_user = TgUser(id=999, is_bot=False, first_name="Host")
    mock_cb_start.answer = AsyncMock()
    await engine.start_competition(mock_cb_start, comp_id)
    assert mock_bot.send_poll.called

    # Student answers Question 1
    poll_ans = PollAnswer(
        poll_id="gpoll_1",
        user=TgUser(id=888, is_bot=False, first_name="Student1"),
        option_ids=[0]
    )
    await engine.process_group_poll_answer(poll_ans)

    # Prepare mock for Question 2 poll
    mock_poll2 = MagicMock()
    mock_poll2.id = "gpoll_2"
    mock_bot.send_poll.return_value = MagicMock(message_id=202, poll=mock_poll2)

    # Trigger round timeout handler (simulates timer expiry without sleeping full duration)
    await engine._handle_group_round_timeout(comp_id, q1_id, "gpoll_1", duration=0, lang="uz")

    # Verify Question 2 was sent!
    assert mock_bot.send_poll.call_count == 2
    async with db.get_connection() as conn:
        comp_mid = await queries.get_group_competition(conn, comp_id)
        assert comp_mid.current_question_index == 1

    # Trigger Question 2 timeout (end of quiz)
    await engine._handle_group_round_timeout(comp_id, q2_id, "gpoll_2", duration=0, lang="uz")

    async with db.get_connection() as conn:
        comp_final = await queries.get_group_competition(conn, comp_id)
        assert comp_final.status == "finished"
        participants = await queries.get_group_participants(conn, comp_id)
        assert len(participants) == 1
        assert participants[0].score == 10

