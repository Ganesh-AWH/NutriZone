from typing import List, Dict
from database.queries import (
    get_high_protein_foods_full,
    get_low_sugar_foods,
    get_high_fibre_foods,
    get_foods_by_calories
)

# =========================
# FOOD TYPE CLASSIFICATION
# =========================

SPICE_KEYWORDS = [
    "masala", "powder", "chutney", "paste", "spice", "seasoning"
]

BEVERAGE_KEYWORDS = [
    "water", "tea", "coffee", "juice", "buttermilk", "kanji", "canjee"
]

SIDE_KEYWORDS = [
    "pickle", "papad", "raita", "curd", "salad"
]


def classify_food(dish_name: str) -> str:
    name = dish_name.lower()

    if any(k in name for k in SPICE_KEYWORDS):
        return "spice"

    if any(k in name for k in BEVERAGE_KEYWORDS):
        return "beverage"

    if any(k in name for k in SIDE_KEYWORDS):
        return "side"

    return "meal"


# =========================
# PORTION LOGIC (PER 100g → SERVING)
# =========================

DEFAULT_SERVING_GRAMS = {
    "meal": 150,
    "side": 50,
    "spice": 5,
    "beverage": 200
}


def apply_portion(food: Dict) -> Dict:
    food_type = food["food_type"]
    serving = DEFAULT_SERVING_GRAMS[food_type]

    factor = serving / 100.0

    adjusted = food.copy()
    adjusted["serving_grams"] = serving

    # Scale nutritional values
    for key in [
        "calories", "carbs", "protein", "fats",
        "free_sugar", "fibre", "sodium",
        "calcium", "iron", "vitamin_c", "folate"
    ]:
        adjusted[key] = round(food[key] * factor, 2)

    return adjusted


# =========================
# CORE NUTRITION AGENT
# =========================

class NutritionAgent:
    def __init__(
        self,
        max_calories_per_meal: float = 500,
        min_protein_per_meal: float = 10,
        max_free_sugar: float = 5
    ):
        self.max_calories = max_calories_per_meal
        self.min_protein = min_protein_per_meal
        self.max_sugar = max_free_sugar

    def get_meal_candidates(self) -> List[Dict]:
        """
        Return realistic meal candidates only
        """

        raw_foods = get_high_protein_foods_full(
            min_protein=self.min_protein,
            max_calories=self.max_calories,
            limit=50
        )

        candidates = []

        for food in raw_foods:
            food_type = classify_food(food["dish_name"])
            food["food_type"] = food_type

            # ❌ Exclude spices & beverages as meals
            if food_type in ["spice", "beverage"]:
                continue

            # ❌ Exclude high-sugar items
            if food["free_sugar"] > self.max_sugar:
                continue

            # ✅ Apply portion logic
            adjusted_food = apply_portion(food)

            # ❌ Remove nutritionally meaningless meals
            if adjusted_food["calories"] < 50:
                continue

            candidates.append(adjusted_food)

        return candidates
