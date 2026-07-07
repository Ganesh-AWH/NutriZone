from typing import Dict, List
from agents.nutrition_agent import NutritionAgent


MEAL_SPLIT = {
    "breakfast": 0.3,
    "lunch": 0.4,
    "dinner": 0.3
}


class DailyMealPlanner:
    def __init__(self, user_profile: Dict):
        self.profile = user_profile

        self.daily_calories = user_profile["daily_calories"]
        self.protein_target = user_profile["protein_target"]
        self.sugar_limit = user_profile["sugar_limit"]
        self.food_restrictions = user_profile["food_restrictions"]

        self.nutrition_agent = NutritionAgent(
            max_calories_per_meal=self.daily_calories,
            min_protein_per_meal=self.protein_target / 3,
            max_free_sugar=self.sugar_limit / 3
        )

    # =========================
    # MAIN PLANNER
    # =========================
    
    
    def generate_day_plan(self) -> Dict:
        meal_candidates = self.nutrition_agent.get_meal_candidates()

        day_plan = {}
        totals = self._init_totals()

        for meal_name, ratio in MEAL_SPLIT.items():
            calorie_target = self.daily_calories * ratio

            meal = self._select_meal(
                meal_candidates,
                calorie_target
            )

            day_plan[meal_name] = meal
            self._update_totals(totals, meal)

        day_plan["totals"] = totals
        return day_plan

    # =========================
    # MEAL SELECTION LOGIC
    # =========================
    def _select_meal(self, foods, calorie_target):
        # 1️⃣ strict
        viable = [
            f for f in foods
            if f["calories"] <= calorie_target
            and f["protein"] >= self.protein_target / 3
        ]

        # 2️⃣ relax protein
        if not viable:
            viable = [
                f for f in foods
                if f["calories"] <= calorie_target
            ]

        # 3️⃣ relax calories (+20%)
        if not viable:
            viable = [
                f for f in foods
                if f["calories"] <= calorie_target * 1.2
            ]

        if not viable:
            return {}

        viable.sort(key=lambda f: abs(f["calories"] - calorie_target))
        return viable[0]


    # =========================
    # TOTAL TRACKING
    # =========================
    def _init_totals(self) -> Dict:
        return {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
            "fibre": 0
        }

    def _update_totals(self, totals: Dict, meal: Dict):
        for key in totals:
            totals[key] += meal.get(key, 0)

        for key in totals:
            totals[key] = round(totals[key], 2)
