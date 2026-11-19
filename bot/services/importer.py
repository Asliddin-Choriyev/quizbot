import os
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import gc
import openpyxl

from bot.database.models import Question
from bot.utils.validator import normalize_column_name, validate_row

logger = logging.getLogger(__name__)

class ImportResult:
    def __init__(self, filename: str):
        self.filename = filename
        self.total_rows: int = 0
        self.valid_count: int = 0
        self.invalid_count: int = 0
        self.duplicate_count: int = 0
        self.errors: List[str] = []
        self.valid_questions: List[Dict[str, Any]] = []
        self.duration_seconds: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.valid_count > 0 and len(self.errors) == 0

    @property
    def has_partial(self) -> bool:
        return self.valid_count > 0 and (self.invalid_count > 0 or self.duplicate_count > 0)

    def get_summary_text(self, max_errors: int = 8) -> str:
        error_sample = ""
        if self.errors:
            error_sample = "\n<b>⚠️ Issues found:</b>\n" + "\n".join(f"• {e}" for e in self.errors[:max_errors])
            if len(self.errors) > max_errors:
                error_sample += f"\n• <i>...and {len(self.errors) - max_errors} more errors.</i>"
        return error_sample

def parse_import_file(file_path: Path, max_rows: int = 50000) -> ImportResult:
    """
    Parse and validate questions from an Excel (.xlsx) or CSV file using openpyxl & csv.
    Supports 10,000+ questions with high performance without heavy pandas.
    """
    start_time = time.time()
    file_path = Path(file_path)
    result = ImportResult(file_path.name)

    ext = file_path.suffix.lower()
    raw_records = []

    if ext in (".xlsx", ".xls"):
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            try:
                raw_headers = next(rows_iter)
            except StopIteration:
                result.errors.append("The uploaded file contains no data.")
                return result

            headers = [normalize_column_name(str(h or "").strip()) for h in raw_headers]
            for row in rows_iter:
                if not any(row):
                    continue
                row_dict = {}
                for i, val in enumerate(row):
                    if i < len(headers) and headers[i]:
                        row_dict[headers[i]] = str(val).strip() if val is not None else ""
                raw_records.append(row_dict)
                if len(raw_records) >= max_rows:
                    break
            wb.close()
        except Exception as e:
            result.errors.append(f"Error reading Excel file: {e}")
            return result

    elif ext == ".csv":
        encodings = ["utf-8-sig", "utf-8", "cp1251", "latin1"]
        decoded = False
        for enc in encodings:
            try:
                with open(file_path, mode="r", encoding=enc) as f:
                    reader = csv.reader(f)
                    try:
                        raw_headers = next(reader)
                    except StopIteration:
                        result.errors.append("The uploaded file contains no data.")
                        return result
                    headers = [normalize_column_name(str(h or "").strip()) for h in raw_headers]
                    for row in reader:
                        if not any(row):
                            continue
                        row_dict = {}
                        for i, val in enumerate(row):
                            if i < len(headers) and headers[i]:
                                row_dict[headers[i]] = str(val).strip() if val is not None else ""
                        raw_records.append(row_dict)
                        if len(raw_records) >= max_rows:
                            break
                decoded = True
                break
            except Exception:
                continue
        if not decoded:
            result.errors.append("Unable to decode CSV file. Please ensure UTF-8 encoding.")
            return result
    else:
        result.errors.append(f"Unsupported file format '{ext}'. Only .xlsx and .csv are supported.")
        return result

    if not raw_records:
        result.errors.append("The uploaded file contains no data or could not be read.")
        return result

    required_columns = ["question", "option_a", "option_b", "option_c", "option_d", "correct_answer"]
    sample_keys = raw_records[0].keys() if raw_records else []
    missing_required = [c for c in required_columns if c not in sample_keys]
    if missing_required:
        result.errors.append(f"Missing required columns: {', '.join(missing_required)}")
        return result

    result.total_rows = len(raw_records)
    seen_questions = set()

    for idx, raw_row in enumerate(raw_records):
        excel_row_num = idx + 2
        is_valid, parsed_dict, err_msg = validate_row(excel_row_num, raw_row, seen_questions)

        if is_valid and parsed_dict:
            q_norm = parsed_dict["question"].strip().lower()
            seen_questions.add(q_norm)
            result.valid_questions.append(parsed_dict)
            result.valid_count += 1
        else:
            if "Duplicate question" in str(err_msg):
                result.duplicate_count += 1
            else:
                result.invalid_count += 1
            if err_msg:
                result.errors.append(err_msg)

    result.duration_seconds = round(time.time() - start_time, 2)
    logger.info(
        f"Parsed {file_path.name}: {result.valid_count} valid, "
        f"{result.invalid_count} invalid, {result.duplicate_count} dups in {result.duration_seconds}s"
    )
    gc.collect()
    return result

def create_sample_excel_template(target_path: Path) -> Path:
    """Generate sample Excel file with sample questions in English and Uzbek."""
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            "question": "What is the capital city of Uzbekistan?",
            "option_a": "Samarkand",
            "option_b": "Tashkent",
            "option_c": "Bukhara",
            "option_d": "Khiva",
            "correct_answer": "B",
            "explanation": "Tashkent is the capital and largest city of Uzbekistan.",
            "topic": "Geography",
            "difficulty": "Easy",
            "timer": 20,
            "image": ""
        },
        {
            "question": "O'zbekiston Respublikasi Konstitutsiyasi qachon qabul qilingan?",
            "option_a": "1991-yil 1-sentyabr",
            "option_b": "1992-yil 8-dekabr",
            "option_c": "1993-yil 2-iyul",
            "option_d": "1990-yil 20-iyun",
            "correct_answer": "B",
            "explanation": "O'zbekiston Konstitutsiyasi 1992-yil 8-dekabrda qabul qilingan.",
            "topic": "Huquq",
            "difficulty": "Medium",
            "timer": 30,
            "image": ""
        },
        {
            "question": "Which Python keyword is used to define an asynchronous function?",
            "option_a": "def async",
            "option_b": "async def",
            "option_c": "await func",
            "option_d": "thread def",
            "correct_answer": "B",
            "explanation": "In Python, coroutines are defined using 'async def'.",
            "topic": "Python Programming",
            "difficulty": "Easy",
            "timer": 15,
            "image": ""
        },
        {
            "question": "Quyosh sistemasidagi eng katta sayyora qaysi?",
            "option_a": "Mars",
            "option_b": "Venera",
            "option_c": "Yupiter",
            "option_d": "Saturn",
            "correct_answer": "C",
            "explanation": "Yupiter Quyosh tizimidagi eng katta va massiv sayyoradir.",
            "topic": "Astronomiya",
            "difficulty": "Easy",
            "timer": 20,
            "image": ""
        },
        {
            "question": "What does SQLite WAL mode stand for?",
            "option_a": "Wide Access Lock",
            "option_b": "Write-Ahead Logging",
            "option_c": "Write-After-Load",
            "option_d": "Web App Layer",
            "correct_answer": "B",
            "explanation": "WAL stands for Write-Ahead Logging in database systems.",
            "topic": "Databases",
            "difficulty": "Medium",
            "timer": 30,
            "image": ""
        }
    ]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Questions"

    headers = ["question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation", "topic", "difficulty", "timer", "image"]
    ws.append(headers)

    for item in data:
        ws.append([item.get(h, "") for h in headers])

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    wb.save(target_path)
    return target_path

def create_sample_csv_template(target_path: Path) -> Path:
    """Generate sample CSV file with UTF-8 encoding."""
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            "question": "Alisher Navoiy qaysi yilda tavallud topgan?",
            "option_a": "1441-yil",
            "option_b": "1436-yil",
            "option_c": "1483-yil",
            "option_d": "1501-yil",
            "correct_answer": "A",
            "explanation": "Alisher Navoiy 1441-yil 9-fevralda Hirotda tug'ilgan.",
            "topic": "Adabiyot",
            "difficulty": "Medium",
            "timer": 25,
            "image": ""
        },
        {
            "question": "Tibbiyot qonunlari asari kim tomonidan yozilgan?",
            "option_a": "Abu Rayhon Beruniy",
            "option_b": "Abu Ali ibn Sino",
            "option_c": "Al-Xorazmiy",
            "option_d": "Mirzo Ulug'bek",
            "correct_answer": "B",
            "explanation": "Tibbiyot qonunlari (Al-Qonun fit-tibb) Abu Ali ibn Sino qalamiga mansub.",
            "topic": "Tarix",
            "difficulty": "Easy",
            "timer": 20,
            "image": ""
        }
    ]

    fieldnames = ["question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation", "topic", "difficulty", "timer", "image"]
    with open(target_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return target_path
