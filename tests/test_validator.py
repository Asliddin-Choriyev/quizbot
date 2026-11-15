import pytest
from bot.utils.validator import validate_row, normalize_column_name

def test_normalize_column_name():
    assert normalize_column_name("question") == "question"
    assert normalize_column_name("Savol") == "question"
    assert normalize_column_name("option_a") == "option_a"
    assert normalize_column_name("Variant A") == "option_a"
    assert normalize_column_name("Option A") == "option_a"
    assert normalize_column_name("correct_answer") == "correct_answer"
    assert normalize_column_name("To'g'ri javob") == "correct_answer"
    assert normalize_column_name("explanation") == "explanation"
    assert normalize_column_name("izoh") == "explanation"
    assert normalize_column_name("timer") == "timer"
    assert normalize_column_name("vaqt") == "timer"
    assert normalize_column_name("unknown_header") is None

def test_validate_valid_row():
    row = {
        "question": "O'zbekiston poytaxti qaysi shahar?",
        "option_a": "Samarqand",
        "option_b": "Toshkent",
        "option_c": "Buxoro",
        "option_d": "Xiva",
        "correct_answer": "B",
        "explanation": "Toshkent O'zbekistonning poytaxti hisoblanadi.",
        "topic": "Geografiya",
        "difficulty": "Easy",
        "timer": "25"
    }
    seen = set()
    is_valid, parsed, err = validate_row(2, row, seen)
    assert is_valid is True
    assert err is None
    assert parsed["question"] == "O'zbekiston poytaxti qaysi shahar?"
    assert parsed["correct_answer"] == "B"
    assert parsed["timer"] == 25
    assert parsed["difficulty"] == "Easy"

def test_validate_missing_fields():
    seen = set()
    # Missing question
    bad_q = {"question": "", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "A"}
    valid, _, err = validate_row(2, bad_q, seen)
    assert not valid
    assert "Missing question text" in err

    # Missing option_c
    bad_c = {"question": "What?", "option_a": "1", "option_b": "2", "option_c": "", "option_d": "4", "correct_answer": "A"}
    valid, _, err = validate_row(3, bad_c, seen)
    assert not valid
    assert "Option C is missing" in err

    # Invalid correct answer
    bad_ans = {"question": "What?", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "E"}
    valid, _, err = validate_row(4, bad_ans, seen)
    assert not valid
    assert "Invalid correct_answer 'E'" in err

def test_validate_duplicate_question():
    seen = {"what is python?"}
    row = {
        "question": "What is Python?",
        "option_a": "Snake",
        "option_b": "Language",
        "option_c": "Fruit",
        "option_d": "Car",
        "correct_answer": "B"
    }
    valid, _, err = validate_row(5, row, seen)
    assert not valid
    assert "Duplicate question detected" in err

def test_validate_correct_answer_variations():
    seen = set()
    # Number 1 maps to A
    r1 = {"question": "Q1?", "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D", "correct_answer": "1"}
    valid, p1, _ = validate_row(2, r1, seen)
    assert valid and p1["correct_answer"] == "A"

    # Lowercase 'c' maps to 'C'
    r2 = {"question": "Q2?", "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D", "correct_answer": "c"}
    valid, p2, _ = validate_row(3, r2, seen)
    assert valid and p2["correct_answer"] == "C"

def test_uzbek_characters_preservation():
    seen = set()
    text = "G'o'za va paxtachilik O'zbekiston qishloq xo'jaligida muhim o'rin tutadi."
    row = {
        "question": text,
        "option_a": "Ha, to'g'ri",
        "option_b": "Yo'q, noto'g'ri",
        "option_c": "Qisman to'g'ri",
        "option_d": "Noma'lum",
        "correct_answer": "A",
        "explanation": "O'zbekistonda paxta yetishtirish an'anaviy tarmoqdir."
    }
    valid, parsed, _ = validate_row(2, row, seen)
    assert valid
    assert parsed["question"] == text
    assert parsed["option_a"] == "Ha, to'g'ri"
