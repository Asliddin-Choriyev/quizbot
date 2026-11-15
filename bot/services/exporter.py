from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import gc

def export_quiz_results_to_excel(quiz_title: str, results: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Export quiz participant results to a formatted Excel file.
    """
    import pandas as pd
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clean_title = "".join(c for c in quiz_title if c.isalnum() or c in (" ", "_", "-")).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"Results_{clean_title}_{timestamp}.xlsx"

    rows = []
    for idx, r in enumerate(results):
        full_name = r.get("real_name") or f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
        rows.append({
            "Rank": idx + 1,
            "User ID": r.get("user_id"),
            "Username": f"@{r.get('username')}" if r.get("username") else "",
            "Full Name": full_name or "Anonymous",
            "Score (%)": r.get("score_percentage", 0.0),
            "Correct": r.get("correct_count", 0),
            "Incorrect": r.get("incorrect_count", 0),
            "Unanswered": r.get("unanswered_count", 0),
            "Total Questions": r.get("total_questions", 0),
            "Passed": "YES" if r.get("passed") else "NO",
            "Duration (s)": round(r.get("duration_seconds", 0.0), 1),
            "Completed At": r.get("end_time", ""),
            "Group": r.get("student_group") or "",
            "Phone": r.get("phone_number") or ""
        })

    if not rows:
        # Create empty template
        df = pd.DataFrame(columns=[
            "Rank", "User ID", "Username", "Full Name", "Score (%)",
            "Correct", "Incorrect", "Unanswered", "Total Questions",
            "Passed", "Duration (s)", "Completed At", "Group", "Phone"
        ])
    else:
        df = pd.DataFrame(rows)

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
        # Auto-adjust column widths
        worksheet = writer.sheets["Results"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    gc.collect()
    return file_path


def export_all_users_to_excel(users: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    Export all bot users and their aggregate exam statistics to an Excel file.
    """
    import pandas as pd
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"Users_Report_{timestamp}.xlsx"

    rows = []
    for idx, u in enumerate(users):
        tg_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
        avg_score = round(u.get("avg_score", 0.0), 1) if u.get("avg_score") is not None else 0.0
        rows.append({
            "№": idx + 1,
            "User ID": u.get("telegram_id"),
            "Username": f"@{u.get('username')}" if u.get("username") else "",
            "Telegram Name": tg_name or "Anonymous",
            "Real Name (F.I.SH.)": u.get("real_name") or "Not set",
            "Group": u.get("student_group") or "Not set",
            "Phone Number": u.get("phone_number") or "Not set",
            "Language": u.get("language_code", "uz"),
            "Total Tests Taken": u.get("total_attempts", 0),
            "Passed Tests": u.get("passed_count", 0),
            "Average Score (%)": avg_score,
            "Registered At": u.get("created_at", ""),
            "Last Active": u.get("last_active", "") or u.get("created_at", "")
        })

    if not rows:
        df = pd.DataFrame(columns=[
            "№", "User ID", "Username", "Telegram Name", "Real Name (F.I.SH.)",
            "Group", "Phone Number", "Language", "Total Tests Taken",
            "Passed Tests", "Average Score (%)", "Registered At", "Last Active"
        ])
    else:
        df = pd.DataFrame(rows)

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Foydalanuvchilar")
        worksheet = writer.sheets["Foydalanuvchilar"]
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

    gc.collect()
    return file_path
