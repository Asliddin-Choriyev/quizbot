import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import gc

from bot.utils.validator import normalize_column_name, validate_row

logger = logging.getLogger(__name__)

class ImportResult:
    def __init__(self, filename: str):
        self.filename = filename
        self.total_rows: int = 0
        self.valid_count: int = 0
        self.invalid_count: int = 0
        self.duplicate_count: int = 0
        self.duration_seconds: float = 0.0
        self.valid_questions: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def get_summary_text(self, max_errors: int = 8) -> str:
        error_sample = ""
        if self.errors:
            error_sample = "\n<b>⚠️ Issues found:</b>\n" + "\n".join(f"• {e}" for e in self.errors[:max_errors])
            if len(self.errors) > max_errors:
                error_sample += f"\n• <i>...and {len(self.errors) - max_errors} more errors.</i>"
        return error_sample

def parse_import_file(file_path: Path, max_rows: int = 50000) -> ImportResult:
    """
    Parse and validate questions from an Excel (.xlsx) or CSV file.
    Supports 10,000+ questions with high performance.
    """
    import pandas as pd
    start_time = time.time()
    file_path = Path(file_path)
    result = ImportResult(file_path.name)

    # 1. Load DataFrame
    ext = file_path.suffix.lower()
    df = None
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, dtype=str)
    elif ext == ".csv":
        # Detect encoding and delimiter
        encodings = ["utf-8-sig", "utf-8", "cp1251", "latin1"]
        for enc in encodings:
            try:
                # Try comma first
                df = pd.read_csv(file_path, encoding=enc, dtype=str, sep=None, engine="python")
                break
            except Exception:
                continue
        if df is None:
            result.errors.append("Unable to decode CSV file. Please ensure UTF-8 encoding.")
            return result
    else:
        result.errors.append(f"Unsupported file format '{ext}'. Only .xlsx and .csv are supported.")
        return result

    if df is None or df.empty:
        result.errors.append("The uploaded file contains no data or could not be read.")
        return result

    # 2. Normalize column headers
    col_mapping = {}
    for col in df.columns:
        norm = normalize_column_name(col)
        if norm:
            col_mapping[col] = norm

    df = df.rename(columns=col_mapping)

    required_columns = ["question", "option_a", "option_b", "option_c", "option_d", "correct_answer"]
    missing_required = [c for c in required_columns if c not in df.columns]
    if missing_required:
        result.errors.append(f"Missing required columns: {', '.join(missing_required)}")
        return result

    # Limit maximum rows to prevent memory explosion if malicious file
    if len(df) > max_rows:
        df = df.iloc[:max_rows]

    result.total_rows = len(df)
    seen_questions = set()

    # 3. Validate rows
    # Convert df to records for fastest iteration
    records = df.to_dict(orient="records")

    for idx, raw_row in enumerate(records):
        excel_row_num = idx + 2  # 1-based index + 1 for header row
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
    try:
        del df
    except Exception:
        pass
    gc.collect()
    return result

def create_sample_excel_template(target_path: Path) -> Path:
    """Generate sample Excel file with sample questions in English and Uzbek."""
    import pandas as pd
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

    df = pd.DataFrame(data)
    with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Questions")

    return target_path

def create_sample_csv_template(target_path: Path) -> Path:
    """Generate sample CSV file with UTF-8 encoding."""
    import csv
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
            "question": "Which data structure in Python is mutable and unordered?",
            "option_a": "tuple",
            "option_b": "str",
            "option_c": "set",
            "option_d": "int",
            "correct_answer": "C",
            "explanation": "Sets are mutable collections of unique unordered items.",
            "topic": "Programming",
            "difficulty": "Easy",
            "timer": 20,
            "image": ""
        }
    ]

    fieldnames = list(data[0].keys())
    with open(target_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return target_path
