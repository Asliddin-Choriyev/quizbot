import re
from typing import Dict, Any, Tuple, Optional, List

# Allowed column mapping synonyms
COLUMN_SYNONYMS = {
    "question": ["question", "savol", "вопрос", "question_text"],
    "option_a": ["option_a", "option a", "a", "variant_a", "variant a", "javob_a"],
    "option_b": ["option_b", "option b", "b", "variant_b", "variant b", "javob_b"],
    "option_c": ["option_c", "option c", "c", "variant_c", "variant c", "javob_c"],
    "option_d": ["option_d", "option d", "d", "variant_d", "variant d", "javob_d"],
    "correct_answer": [
        "correct_answer", "correct answer", "correct", "answer",
        "javob", "tugri_javob", "to'g'ri javob", "to_g_ri_javob", "правильный ответ"
    ],
    "explanation": ["explanation", "izoh", "объяснение", "comment"],
    "topic": ["topic", "mavzu", "тема", "category"],
    "difficulty": ["difficulty", "qiyinlik", "сложность", "level"],
    "timer": ["timer", "vaqt", "таймер", "time", "seconds"],
    "image": ["image", "rasm", "photo", "картинка", "img"]
}

CORRECT_ANSWER_MAP = {
    "A": "A", "1": "A", "OPTION_A": "A", "VARIANT_A": "A",
    "B": "B", "2": "B", "OPTION_B": "B", "VARIANT_B": "B",
    "C": "C", "3": "C", "OPTION_C": "C", "VARIANT_C": "C",
    "D": "D", "4": "D", "OPTION_D": "D", "VARIANT_D": "D",
}

def normalize_column_name(col: str) -> Optional[str]:
    """Map raw header name to standard column key."""
    clean = str(col).strip().lower().replace("-", "_")
    clean = re.sub(r"\s+", " ", clean)
    for canonical, synonyms in COLUMN_SYNONYMS.items():
        if clean == canonical or clean in synonyms:
            return canonical
    return None

def clean_cell_text(val: Any) -> str:
    """Safely convert cell value to string with UTF-8 / Uzbek character safety."""
    if val is None:
        return ""
    text = str(val).strip()
    if text.lower() in ("nan", "none", "null"):
        return ""
    return text

def validate_row(
    row_num: int,
    raw_row: Dict[str, Any],
    seen_questions: set
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate a single question row.
    Returns: (is_valid, parsed_dict, error_message)
    """
    # 1. Question text
    q_text = clean_cell_text(raw_row.get("question"))
    if not q_text:
        return False, None, f"Row {row_num}: Missing question text."
    
    # Check duplicate in current batch
    q_norm = re.sub(r"\s+", " ", q_text.lower()).strip()
    if q_norm in seen_questions:
        return False, None, f"Row {row_num}: Duplicate question detected."
    
    # 2. Four options required
    opt_a = clean_cell_text(raw_row.get("option_a"))
    opt_b = clean_cell_text(raw_row.get("option_b"))
    opt_c = clean_cell_text(raw_row.get("option_c"))
    opt_d = clean_cell_text(raw_row.get("option_d"))

    if not opt_a:
        return False, None, f"Row {row_num}: Option A is missing."
    if not opt_b:
        return False, None, f"Row {row_num}: Option B is missing."
    if not opt_c:
        return False, None, f"Row {row_num}: Option C is missing."
    if not opt_d:
        return False, None, f"Row {row_num}: Option D is missing."

    # 3. Correct answer
    raw_correct = clean_cell_text(raw_row.get("correct_answer")).upper()
    correct = CORRECT_ANSWER_MAP.get(raw_correct)
    if not correct:
        return False, None, f"Row {row_num}: Invalid correct_answer '{raw_correct}'. Must be A, B, C, or D."

    # 4. Optional fields
    explanation = clean_cell_text(raw_row.get("explanation")) or None
    topic = clean_cell_text(raw_row.get("topic")) or "General"
    difficulty = clean_cell_text(raw_row.get("difficulty")) or "Medium"
    if difficulty.capitalize() in ("Easy", "Medium", "Hard"):
        difficulty = difficulty.capitalize()

    # Timer override
    raw_timer = clean_cell_text(raw_row.get("timer"))
    timer_seconds = None
    if raw_timer:
        try:
            # Handle float strings like "30.0" from excel
            val = int(float(raw_timer))
            if 5 <= val <= 600:
                timer_seconds = val
        except ValueError:
            pass

    image_url = clean_cell_text(raw_row.get("image")) or None

    parsed = {
        "question": q_text,
        "option_a": opt_a,
        "option_b": opt_b,
        "option_c": opt_c,
        "option_d": opt_d,
        "correct_answer": correct,
        "explanation": explanation,
        "topic": topic,
        "difficulty": difficulty,
        "timer": timer_seconds,
        "image": image_url
    }
    return True, parsed, None
