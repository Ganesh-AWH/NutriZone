from pydantic import BaseModel
from typing import Dict, Optional


# ---------- INPUTS ----------

class UserInput(BaseModel):
    age: int
    gender: str
    height: float
    weight: float
    activity_level: str
    goal: str

    blood_pressure: Optional[str] = None
    blood_sugar: Optional[str] = None
    cholesterol: Optional[str] = None
    thyroid: Optional[bool] = None
    pcos: Optional[bool] = None
    digestive_issues: Optional[str] = None

    allergies: Optional[list[str]] = []
    culture: Optional[str] = None
    region: Optional[str] = None
    state: Optional[str] = None


class FeedbackInput(BaseModel):
    yesterday_plan: Dict
    hunger: Optional[int] = None
    energy: Optional[int] = None
    weight_change: Optional[float] = None
    meal_feedback: Optional[Dict] = {}
    suggestions: Optional[str] = None


class PlanFeedbackRequest(BaseModel):
    """Single body for POST /plan/feedback: user profile + feedback."""
    user_input: UserInput
    feedback: FeedbackInput


# ---------- RESPONSES ----------

class PlanResponse(BaseModel):
    profile: Dict
    plan: Dict
    explanation: str

class WeeklyPlanResponse(BaseModel):
    week_plan: Dict
    weekly_summary: Dict
