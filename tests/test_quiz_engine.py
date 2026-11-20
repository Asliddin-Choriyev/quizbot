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

@pytest.mark.asyncio
async def test_quiz_engine_manual_pause(tmp_path: Path):
    db_file = tmp_path / "engine_pause_test.db"
    db = Database(db_file)
    await db.init()

    mock_bot = AsyncMock()
    mock_poll = MagicMock()
    mock_poll.id = "poll_pause_123"
    mock_poll_msg = MagicMock(message_id=505, poll=mock_poll)
    mock_bot.send_poll.return_value = mock_poll_msg

    engine = QuizEngine(bot=mock_bot, db=db)

    async with db.get_connection() as conn:
        quiz_id = await queries.create_quiz(conn, title="Pause Quiz", pass_percentage=60)
        q_id = await queries.add_question(conn, quiz_id, "Pause Q?")
        await queries.add_question_options(conn, q_id, [
            {"option_label": "A", "option_text": "Option A", "is_correct": True},
            {"option_label": "B", "option_text": "Option B", "is_correct": False},
        ])

    session = await engine.start_quiz_session(user_id=777, chat_id=777, quiz_id=quiz_id, lang="uz")
    assert session is not None
    assert mock_bot.send_poll.called
    # Check reply_markup was passed to send_poll
    call_kwargs = mock_bot.send_poll.call_args.kwargs
    assert "reply_markup" in call_kwargs

    # Unauthorized user cannot pause
    paused_unauth = await engine.pause_quiz_session(session.id, user_id=999, lang="uz")
    assert paused_unauth is False

    # Authorized user pauses session
    paused = await engine.pause_quiz_session(session.id, user_id=777, lang="uz")
    assert paused is True
    # Poll was deleted or stopped
    assert mock_bot.delete_message.called or mock_bot.stop_poll.called
    # Pause status message was sent
    assert mock_bot.send_message.called
    send_msg_kwargs = mock_bot.send_message.call_args.kwargs
    assert "Pauza" in send_msg_kwargs.get("text", "") or "to'xtatildi" in send_msg_kwargs.get("text", "")

def test_share_permissions_and_landing_kb():
    import config
    from bot.keyboards.inline import get_quiz_landing_kb

    # Allowed IDs
    assert config.can_share_quizzes(6250947707) is True
    assert config.can_share_quizzes(5606522749) is True

    # Unauthorized IDs
    assert config.can_share_quizzes(123456789) is False
    assert config.can_share_quizzes(999999999) is False
    assert config.can_share_quizzes(None) is False

    # Normal student landing keyboard (cannot share)
    kb_student = get_quiz_landing_kb(quiz_id=1, bot_username="testbot", can_share=False)
    student_callbacks = [btn.callback_data for row in kb_student.inline_keyboard for btn in row if btn.callback_data]
    student_switches = [btn.switch_inline_query for row in kb_student.inline_keyboard for btn in row if btn.switch_inline_query is not None]
    assert "quiz:start:1" in student_callbacks
    assert len(student_switches) == 0  # No share button!

    # Authorized user landing keyboard (can share)
    kb_auth = get_quiz_landing_kb(quiz_id=1, bot_username="testbot", can_share=True)
    auth_switches = [btn.switch_inline_query for row in kb_auth.inline_keyboard for btn in row if btn.switch_inline_query is not None]
    assert len(auth_switches) == 1
    assert auth_switches[0] == "1"

    # Verify "Guruhda testni boshlash" (startgroup) is hidden for students, but available for authorized users
    all_student_urls = [btn.url for row in kb_student.inline_keyboard for btn in row if btn.url]
    all_auth_urls = [btn.url for row in kb_auth.inline_keyboard for btn in row if btn.url]
    assert not any("startgroup" in url for url in all_student_urls)
    assert any("startgroup" in url for url in all_auth_urls)




