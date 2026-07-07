from fastapi import APIRouter
from api.schemas import UserInput, FeedbackInput, PlanResponse, PlanFeedbackRequest
from agents.orchestrator import NutritionOrchestrator
from agents.weekly_planner_agent import WeeklyMealPlanner
from api.schemas import WeeklyPlanResponse


# THIS NAME MUST BE `router`
router = APIRouter()

orchestrator = NutritionOrchestrator()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "nutrition-ai"}


@router.post("/plan/day", response_model=PlanResponse)
def generate_day_plan(user_input: UserInput):
    return orchestrator.run_day(user_input.dict())


@router.post("/plan/feedback", response_model=PlanResponse)
def generate_plan_with_feedback(body: PlanFeedbackRequest):
    return orchestrator.run_day(
        body.user_input.dict(),
        body.feedback.dict()
    )

@router.post("/plan/week", response_model=WeeklyPlanResponse)
def generate_week_plan(user_input: UserInput):
    orchestrator_profile = orchestrator.run_day(user_input.dict())["profile"]

    weekly_planner = WeeklyMealPlanner(orchestrator_profile)
    return weekly_planner.generate_week_plan()
