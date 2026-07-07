from typing import Dict, List
from agents.nutrition_agent import NutritionAgent


# =========================
# MEAL SPLIT (3 MEALS ONLY)
# =========================
MEAL_SPLIT = {
    "breakfast": 0.3,
    "lunch": 0.4,
    "dinner": 0.3
}


# =========================
# MEAL TYPE CLASSIFICATION
# =========================
DESSERT_KEYWORDS = [
    "ladoo", "halwa", "barfi", "kheer", "payasam",
    "gulab", "rasgulla", "sweet", "mithai", "jalebi"
]

SNACK_KEYWORDS = [
    "sandwich", "cutlet", "pakora", "samosa",
    "chaat", "bonda", "roll", "burger", "pizza"
]


def classify_meal_type(dish_name: str) -> str:
    name = dish_name.lower()

    if any(k in name for k in DESSERT_KEYWORDS):
        return "dessert"

    if any(k in name for k in SNACK_KEYWORDS):
        return "snack"

    return "main"


# =========================
# DAILY MEAL PLANNER
# =========================
class DailyMealPlanner:
    def __init__(
        self,
        user_profile: Dict,
        feedback_adjustments: Dict = None,
        week_used_dishes: set = None,
        dqn_strategy: str = None
    ):
        self.profile = user_profile
        self.adjustments = feedback_adjustments or {}
        self.week_used_dishes = week_used_dishes or set()
        self.dqn_strategy = dqn_strategy

        # Base targets
        self.daily_calories = (
            user_profile["daily_calories"]
            + self.adjustments.get("calorie_adjustment", 0)
        )

        self.protein_target = user_profile["protein_target"]
        self.sugar_limit = user_profile["sugar_limit"]

        self.food_restrictions = user_profile["food_restrictions"]
        self.avoid_foods = self.adjustments.get("avoid_foods", [])
        self.prefer_foods = self.adjustments.get("prefer_foods", [])

        self.meal_strategy = self.adjustments.get("meal_strategy", {})

        self.nutrition_agent = NutritionAgent(
            max_calories_per_meal=self.daily_calories,
            min_protein_per_meal=0,
            max_free_sugar=self.sugar_limit
        )

    # =========================
    # MAIN PLANNER
    # =========================
    def generate_day_plan(self) -> Dict:
        meal_candidates = self.nutrition_agent.get_meal_candidates()

        day_plan = {}
        totals = self._init_totals()
        used_dishes = set()

        for meal_index, (meal_name, ratio) in enumerate(MEAL_SPLIT.items()):
            if self.meal_strategy.get(meal_name) == "lighter":
                ratio *= 0.8

            calorie_target = self.daily_calories * ratio

            meal = self._select_meal(
                meal_candidates,
                calorie_target,
                used_dishes,
                meal_name,
                meal_index
            )

            day_plan[meal_name] = meal
            self._update_totals(totals, meal)

        day_plan["totals"] = totals
        return day_plan

    # =========================
    # FOOD FILTERING
    # =========================
    def _is_food_allowed(self, food: Dict) -> bool:
        dish = food["dish_name"].lower()

        # Allergy filtering (simple name-based)
        if "peanut" in self.food_restrictions:
            if "peanut" in dish or "groundnut" in dish:
                return False

        # Avoid disliked foods
        if any(bad.lower() in dish for bad in self.avoid_foods):
            return False

        return True

    # =========================
    # MEAL SELECTION WITH DIVERSITY
    # =========================
    def _select_meal(
        self,
        foods: List[Dict],
        calorie_target: float,
        used_dishes: set,
        meal_name: str,
        meal_index: int
    ) -> Dict:
        viable = []

        for food in foods:
            if not self._is_food_allowed(food):
                continue

            meal_type = classify_meal_type(food["dish_name"])
            if meal_type != "main":
                continue

            if food["calories"] <= calorie_target * 1.2:
                viable.append(food)

        if not viable:
            return {}

        def score(food):
            score = 0

            # 1️⃣ Calorie closeness
            score -= abs(food["calories"] - calorie_target)

            # 2️⃣ Protein reward
            score += food.get("protein", 0) * 2

            # 3️⃣ Preference boost
            if self._preference_score(food):
                score += 15

            # 4️⃣ Soft diversity penalty within day
            if meal_index > 0:
                if food["dish_name"].lower() in used_dishes:
                    score -= 50

            # 5️⃣ Strong penalty for dishes already used this week (weekly variety)
            if food["dish_name"].lower() in self.week_used_dishes:
                score -= 150

            # 6️⃣ DQN Neuro-Symbolic Guidance
            if hasattr(self, 'dqn_strategy') and self.dqn_strategy:
                s = self.dqn_strategy.lower()
                if "protein" in s:
                    score += food.get("protein", 0) * 3
                if "sugar" in s:
                    score -= food.get("free_sugar", 0) * 15
                if "sodium" in s:
                    score -= food.get("sodium", 0) * 0.2
                if "fiber" in s:
                    score += food.get("fibre", 0) * 5
                if "fat" in s:
                    score += food.get("fats", 0) * 3

            return score

        viable.sort(key=score, reverse=True)
        chosen = viable[0]

        used_dishes.add(chosen["dish_name"].lower())
        return chosen

    def _preference_score(self, food: Dict) -> int:
        dish = food["dish_name"].lower()
        return 1 if any(p.lower() in dish for p in self.prefer_foods) else 0

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
        if not meal:
            return

        for key in totals:
            totals[key] += meal.get(key, 0)

        for key in totals:
            totals[key] = round(totals[key], 2)
