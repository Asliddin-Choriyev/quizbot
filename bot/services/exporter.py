from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import gc
import openpyxl

def export_quiz_results_to_excel(quiz_title: str, results: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Export quiz participant results to a formatted Excel file using openpyxl directly.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clean_title = "".join(c for c in quiz_title if c.isalnum() or c in (" ", "_", "-")).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"Results_{clean_title}_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"

    headers = [
        "Rank", "User ID", "Username", "Full Name", "Score (%)",
        "Correct", "Incorrect", "Unanswered", "Total Questions",
        "Passed", "Duration (s)", "Completed At", "Group", "Phone"
    ]
    ws.append(headers)

    for idx, r in enumerate(results):
        full_name = r.get("real_name") or f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
        ws.append([
            idx + 1,
            r.get("user_id"),
            f"@{r.get('username')}" if r.get("username") else "",
            full_name or "Anonymous",
            r.get("score_percentage", 0.0),
            r.get("correct_count", 0),
            r.get("incorrect_count", 0),
            r.get("unanswered_count", 0),
            r.get("total_questions", 0),
            "YES" if r.get("passed") else "NO",
            round(r.get("duration_seconds", 0.0), 1),
            str(r.get("end_time") or ""),
            r.get("student_group") or "",
            r.get("phone_number") or ""
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(file_path)
    gc.collect()
    return file_path

def export_all_users_to_excel(users: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Export all bot users and their aggregate exam statistics to an Excel file using openpyxl.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"Users_Report_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"

    headers = [
        "№", "User ID", "Username", "Telegram Name", "Real Name (F.I.SH.)",
        "Group", "Phone Number", "Language", "Total Tests Taken",
        "Passed Tests", "Average Score (%)", "Registered At", "Last Active"
    ]
    ws.append(headers)

    for idx, u in enumerate(users):
        tg_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
        avg_score = round(u.get("avg_score", 0.0), 1) if u.get("avg_score") is not None else 0.0
        ws.append([
            idx + 1,
            u.get("telegram_id"),
            f"@{u.get('username')}" if u.get("username") else "",
            tg_name or "Anonymous",
            u.get("real_name") or "Not set",
            u.get("student_group") or "Not set",
            u.get("phone_number") or "Not set",
            u.get("language_code", "uz"),
            u.get("total_attempts", 0),
            u.get("passed_count", 0),
            avg_score,
            str(u.get("created_at") or ""),
            str(u.get("last_active") or u.get("created_at") or "")
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(file_path)
    gc.collect()
    return file_path
