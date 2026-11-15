import pytest
import pandas as pd
from pathlib import Path
from bot.services.importer import parse_import_file, create_sample_excel_template, create_sample_csv_template

def test_sample_excel_import(tmp_path: Path):
    excel_path = tmp_path / "sample.xlsx"
    create_sample_excel_template(excel_path)
    assert excel_path.exists()

    result = parse_import_file(excel_path)
    assert result.total_rows == 5
    assert result.valid_count == 5
    assert result.invalid_count == 0
    assert len(result.valid_questions) == 5
    assert result.valid_questions[0]["correct_answer"] == "B"

def test_sample_csv_import(tmp_path: Path):
    csv_path = tmp_path / "sample.csv"
    create_sample_csv_template(csv_path)
    assert csv_path.exists()

    result = parse_import_file(csv_path)
    assert result.total_rows == 2
    assert result.valid_count == 2
    assert result.invalid_count == 0

def test_bulk_1200_questions_import_performance(tmp_path: Path):
    """Verify system handles 1,000+ questions per import smoothly and quickly."""
    large_excel = tmp_path / "bulk_1200.xlsx"
    
    questions = []
    for i in range(1200):
        questions.append({
            "question": f"Test Question Number {i + 1}: What is 2 + {i}?",
            "option_a": f"{2 + i}",
            "option_b": f"{3 + i}",
            "option_c": f"{4 + i}",
            "option_d": f"{5 + i}",
            "correct_answer": "A",
            "explanation": f"2 + {i} is equal to {2 + i}.",
            "topic": "Mathematics",
            "difficulty": "Easy" if i < 400 else ("Medium" if i < 800 else "Hard"),
            "timer": 20
        })

    df = pd.DataFrame(questions)
    with pd.ExcelWriter(large_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    # Parse large batch
    result = parse_import_file(large_excel)
    assert result.total_rows == 1200
    assert result.valid_count == 1200
    assert result.invalid_count == 0
    assert result.duplicate_count == 0
    # Must parse fast (e.g. well under 5 seconds)
    assert result.duration_seconds < 10.0

def test_invalid_rows_reported(tmp_path: Path):
    csv_path = tmp_path / "flawed.csv"
    data = [
        {"question": "Valid Q1", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "A"},
        {"question": "", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "A"}, # Row 3: Missing question
        {"question": "Valid Q3", "option_a": "1", "option_b": "", "option_c": "3", "option_d": "4", "correct_answer": "A"}, # Row 4: Missing option_b
        {"question": "Valid Q4", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "INVALID"}, # Row 5: Bad correct answer
        {"question": "Valid Q1", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4", "correct_answer": "A"}, # Row 6: Duplicate
    ]
    pd.DataFrame(data).to_csv(csv_path, index=False, encoding="utf-8")

    result = parse_import_file(csv_path)
    assert result.total_rows == 5
    assert result.valid_count == 1
    assert result.invalid_count == 3
    assert result.duplicate_count == 1
    assert len(result.errors) >= 4
    summary = result.get_summary_text()
    assert "Missing question text" in summary
    assert "Option B is missing" in summary
    assert "Duplicate question" in summary
