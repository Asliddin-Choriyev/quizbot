import html
from typing import List, Dict, Any

def escape_html(text: str) -> str:
    """Escape text for Telegram HTML mode."""
    if text is None:
        return ""
    return html.escape(str(text))

def format_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Render a clean unicode progress bar."""
    if total <= 0:
        return ""
    pct = max(0.0, min(1.0, current / total))
    filled_len = int(round(length * pct))
    bar = "▓" * filled_len + "░" * (length - filled_len)
    return f"[{bar}] {int(pct * 100)}%"

def format_duration(seconds: float) -> str:
    """Format duration in seconds into human readable text."""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if rem_seconds == 0:
        return f"{minutes}m"
    return f"{minutes}m {rem_seconds}s"

def format_leaderboard(entries: List[Dict[str, Any]], max_items: int = 10) -> str:
    """Format leaderboard rankings with medals."""
    if not entries:
        return "<i>No participants yet.</i>"

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, entry in enumerate(entries[:max_items]):
        rank_icon = medals[idx] if idx < 3 else f"<b>{idx + 1}.</b>"
        display_name = entry.get("real_name") or entry.get("full_name") or entry.get("first_name") or entry.get("username") or "Participant"
        name = escape_html(display_name)
        if entry.get("student_group"):
            name += f" (<i>{escape_html(entry['student_group'])}</i>)"
            
        score = entry.get("score")
        if score is None:
            score = f"{entry.get('best_score', 0)}%"
        else:
            score = f"{score} pts"
        
        correct = entry.get("correct_answers")
        if correct is not None:
            lines.append(f"{rank_icon} {name} — <b>{score}</b> ({correct} correct)")
        else:
            lines.append(f"{rank_icon} {name} — <b>{score}</b>")

    return "\n".join(lines)
