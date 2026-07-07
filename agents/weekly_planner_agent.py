from typing import Dict, List
from agents.meal_planner_agent import DailyMealPlanner


class WeeklyMealPlanner:
    """
    Generates a 7-day meal plan using DailyMealPlanner
    while encouraging variety across days.
    """

    def __init__(self, user_profile: Dict):
        self.user_profile = user_profile
        self.used_dishes = set()

    def generate_week_plan(self) -> Dict:
        week_plan = {}
        weekly_totals = {
            "calories": 0,
            "protein": 0,
            "fibre": 0
        }

        feedback = None

        for day in range(1, 8):
            # Pass dishes already used on previous days so this day picks different ones
            planner = DailyMealPlanner(
                self.user_profile,
                feedback_adjustments=feedback,
                week_used_dishes=set(self.used_dishes),
            )

            day_plan = planner.generate_day_plan()

            # Track used dishes for diversity (soft memory)
            for meal in ["breakfast", "lunch", "dinner"]:
                if meal in day_plan and day_plan[meal]:
                    self.used_dishes.add(
                        day_plan[meal]["dish_name"].lower()
                    )

            # Accumulate weekly totals
            totals = day_plan.get("totals", {})
            weekly_totals["calories"] += totals.get("calories", 0)
            weekly_totals["protein"] += totals.get("protein", 0)
            weekly_totals["fibre"] += totals.get("fibre", 0)

            week_plan[f"day_{day}"] = day_plan

            # Light feedback simulation (optional)
            feedback = {
                "yesterday_plan": day_plan,
                "hunger": 5,
                "energy": 6,
                "weight_change": 0
            }

        weekly_summary = {
            "avg_calories": round(weekly_totals["calories"] / 7, 1),
            "avg_protein": round(weekly_totals["protein"] / 7, 1),
            "avg_fibre": round(weekly_totals["fibre"] / 7, 1),
            "unique_dishes": len(self.used_dishes)
        }

        return {
            "week_plan": week_plan,
            "weekly_summary": weekly_summary
        }
