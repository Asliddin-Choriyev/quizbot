import pytest
from pathlib import Path
import openpyxl
from bot.services.exporter import export_quiz_results_to_excel, export_all_users_to_excel

def test_export_results_to_excel(tmp_path: Path):
    results = [
        {
            "user_id": 12345,
            "username": "student_ali",
            "first_name": "Ali",
            "last_name": "Valiyev",
            "score_percentage": 85.5,
            "correct_count": 17,
            "incorrect_count": 2,
            "unanswered_count": 1,
            "total_questions": 20,
            "passed": True,
            "duration_seconds": 142.3,
            "end_time": "2026-11-15 12:30:00"
        },
        {
            "user_id": 67890,
            "username": "student_nodir",
            "first_name": "Nodir",
            "last_name": "Sobirov",
            "score_percentage": 50.0,
            "correct_count": 10,
            "incorrect_count": 8,
            "unanswered_count": 2,
            "total_questions": 20,
            "passed": False,
            "duration_seconds": 180.0,
            "end_time": "2026-11-15 12:35:00"
        }
    ]

    export_file = export_quiz_results_to_excel("History Quiz", results, tmp_path)
    assert export_file.exists()
    assert export_file.suffix == ".xlsx"

    wb = openpyxl.load_workbook(export_file)
    assert "Results" in wb.sheetnames
    sheet = wb["Results"]
    assert sheet.max_row == 3  # Header + 2 data rows
    assert sheet.cell(row=2, column=3).value == "@student_ali"
    assert sheet.cell(row=2, column=5).value == 85.5
    assert sheet.cell(row=2, column=10).value == "YES"
    assert sheet.cell(row=3, column=10).value == "NO"

def test_export_all_users_to_excel(tmp_path: Path):
    users = [
        {
            "telegram_id": 111,
            "username": "user1",
            "first_name": "Vali",
            "last_name": "Aliyev",
            "real_name": "Vali Aliyev",
            "student_group": "201-guruh",
            "phone_number": "+998901112233",
            "language_code": "uz",
            "total_attempts": 5,
            "passed_count": 4,
            "avg_score": 88.0,
            "created_at": "2026-11-15 10:00:00",
            "last_active": "2026-11-15 12:00:00"
        }
    ]
    export_file = export_all_users_to_excel(users, tmp_path)
    assert export_file.exists()
    assert export_file.suffix == ".xlsx"

    wb = openpyxl.load_workbook(export_file)
    assert "Foydalanuvchilar" in wb.sheetnames
    sheet = wb["Foydalanuvchilar"]
    assert sheet.max_row == 2
    assert sheet.cell(row=2, column=2).value == 111
    assert sheet.cell(row=2, column=5).value == "Vali Aliyev"
