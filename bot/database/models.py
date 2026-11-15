from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    id: Optional[int]
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    real_name: Optional[str] = None
    phone_number: Optional[str] = None
    student_group: Optional[str] = None
    language_code: str = "uz"
    is_admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class QuestionOption:
    id: Optional[int]
    question_id: int
    option_label: str  # 'A', 'B', 'C', 'D'
    option_text: str
    is_correct: bool = False

@dataclass
class Question:
    id: Optional[int]
    quiz_id: int
    question_text: str
    options: List[QuestionOption] = field(default_factory=list)
    explanation: Optional[str] = None
    topic: Optional[str] = None
    difficulty: str = "Medium"
    timer_seconds: Optional[int] = None
    image_url: Optional[str] = None
    order_num: int = 0
    created_at: Optional[datetime] = None

@dataclass
class Quiz:
    id: Optional[int]
    title: str
    description: Optional[str] = None
    category: str = "General"
    default_timer: int = 30
    shuffle_options: bool = True
    show_explanation: bool = True
    pass_percentage: int = 60
    is_published: bool = True
    created_by: Optional[int] = None
    question_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class QuizSession:
    id: Optional[int]
    session_code: str
    quiz_id: int
    user_id: int
    chat_id: int
    is_group: bool = False
    status: str = "in_progress"
    current_question_index: int = 0
    total_questions: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    unanswered_count: int = 0
    score_percentage: float = 0.0
    passed: bool = False
    question_ids_order: List[int] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

@dataclass
class SessionAnswer:
    id: Optional[int]
    session_id: int
    question_id: int
    user_id: int
    selected_option: Optional[str]  # 'A', 'B', 'C', 'D' or None
    is_correct: bool = False
    response_time_seconds: float = 0.0
    created_at: Optional[datetime] = None

@dataclass
class GroupCompetition:
    id: Optional[int]
    quiz_id: int
    chat_id: int
    message_id: Optional[int] = None
    status: str = "lobby"  # lobby, active, finished, cancelled
    current_question_index: int = 0
    total_questions: int = 0
    timer_seconds: int = 30
    round_end_time: Optional[datetime] = None
    question_ids_order: List[int] = field(default_factory=list)
    created_by: int = 0
    created_at: Optional[datetime] = None

@dataclass
class GroupParticipant:
    id: Optional[int]
    competition_id: int
    user_id: int
    username: Optional[str] = None
    full_name: str = ""
    score: int = 0
    correct_answers: int = 0
    total_answered: int = 0
    total_response_time: float = 0.0
