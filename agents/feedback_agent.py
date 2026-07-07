from typing import Dict, List


class FeedbackAgent:
    """
    Interprets user feedback and produces
    planner adjustment signals for the next day.
    """

    def __init__(
        self,
        yesterday_plan: Dict,
        feedback: Dict
    ):
        self.plan = yesterday_plan
        self.feedback = feedback

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def generate_adjustments(self) -> Dict:
        adjustments = {
            "calorie_adjustment": 0,
            "protein_bias": 0,
            "fibre_bias": 0,
            "carb_bias": 0,
            "avoid_foods": [],
            "prefer_foods": [],
            "meal_strategy": {}
        }

        self._process_hunger(adjustments)
        self._process_energy(adjustments)
        self._process_weight_change(adjustments)
        self._process_meal_preferences(adjustments)
        self._process_suggestions(adjustments)

        return adjustments

    # =========================
    # FEEDBACK PROCESSORS
    # =========================
    def _process_hunger(self, adj: Dict):
        hunger = self.feedback.get("hunger")

        if hunger is None:
            return

        if hunger >= 7:
            adj["fibre_bias"] += 1
            adj["calorie_adjustment"] += 100

        elif hunger <= 3:
            adj["calorie_adjustment"] -= 50

    def _process_energy(self, adj: Dict):
        energy = self.feedback.get("energy")

        if energy is None:
            return

        if energy <= 5:
            adj["carb_bias"] += 1

    def _process_weight_change(self, adj: Dict):
        weight_change = self.feedback.get("weight_change")

        if weight_change is None:
            return

        # Fat loss goal assumed
        if weight_change >= 0:
            adj["calorie_adjustment"] -= 100

        elif weight_change < -0.7:
            adj["calorie_adjustment"] += 100

    def _process_meal_preferences(self, adj: Dict):
        meal_feedback = self.feedback.get("meal_feedback", {})

        for meal, response in meal_feedback.items():
            meal_data = self.plan.get(meal)

            if not meal_data:
                continue

            dish = meal_data.get("dish_name")

            if not dish:
                continue

            # Like/dislike preference
            if response == "like":
                adj["prefer_foods"].append(dish)
            elif response == "dislike":
                adj["avoid_foods"].append(dish)

            # Tracking: skipped / not_eaten -> avoid suggesting same dish again
            if response in ("skipped", "not_eaten"):
                if dish not in adj["avoid_foods"]:
                    adj["avoid_foods"].append(dish)

    def _process_suggestions(self, adj: Dict):
        """
        Very simple keyword-based interpretation.
        No LLM yet (safe & deterministic).
        """
        text = self.feedback.get("suggestions")
        if not text:
            return
        text = text.lower()

        if "lighter lunch" in text or "light lunch" in text:
            adj["meal_strategy"]["lunch"] = "lighter"

        if "heavy dinner" in text:
            adj["meal_strategy"]["dinner"] = "lighter"

        if "more protein" in text:
            adj["protein_bias"] += 1

        if "more vegetables" in text:
            adj["fibre_bias"] += 1
