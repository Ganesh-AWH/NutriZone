from typing import Dict


class UserProfileAgent:
    def __init__(self, user_input: Dict):
        self.user = user_input

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def build_profile(self) -> Dict:
        profile = {}

        profile["bmr"] = self._calculate_bmr()
        profile["tdee"] = self._calculate_tdee(profile["bmr"])
        profile["daily_calories"] = self._adjust_for_goal(profile["tdee"])

        profile["protein_target"] = self._protein_target()
        profile["sugar_limit"] = self._sugar_limit()
        profile["sodium_limit"] = self._sodium_limit()
        profile["fat_strategy"] = self._fat_strategy()

        profile["food_restrictions"] = self._food_restrictions()
        profile["diet_style"] = self._diet_style()

        return profile

    # =========================
    # CORE CALCULATIONS
    # =========================
    def _calculate_bmr(self) -> float:
        """
        Mifflin-St Jeor Equation
        """
        weight = self.user["weight"]
        height = self.user["height"]
        age = self.user["age"]
        gender = self.user["gender"]

        if gender.lower() == "male":
            return 10 * weight + 6.25 * height - 5 * age + 5
        else:
            return 10 * weight + 6.25 * height - 5 * age - 161

    def _calculate_tdee(self, bmr: float) -> float:
        activity_map = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        factor = activity_map.get(self.user["activity_level"], 1.2)
        return bmr * factor

    def _adjust_for_goal(self, tdee: float) -> float:
        goal = self.user["goal"]

        if goal == "fat_loss":
            return tdee - 500
        if goal == "muscle_gain":
            return tdee + 300
        return tdee  # maintenance

    # =========================
    # NUTRIENT TARGETS
    # =========================
    def _protein_target(self) -> float:
        weight = self.user["weight"]
        goal = self.user["goal"]

        if goal == "muscle_gain":
            return weight * 2.0
        if goal == "fat_loss":
            return weight * 1.6
        return weight * 1.2

    def _sugar_limit(self) -> float:
        if self.user.get("blood_sugar") == "high":
            return 20
        return 40

    def _sodium_limit(self) -> float:
        if self.user.get("blood_pressure") == "high":
            return 1500
        return 2300

    def _fat_strategy(self) -> str:
        if self.user.get("cholesterol") == "high":
            return "low_saturated"
        return "balanced"

    # =========================
    # RESTRICTIONS & STYLE
    # =========================
    def _food_restrictions(self):
        restrictions = []

        if self.user.get("allergies"):
            restrictions.extend(self.user["allergies"])

        if self.user.get("pcos"):
            restrictions.append("high_gi_foods")

        if self.user.get("thyroid"):
            restrictions.append("raw_cruciferous")

        if self.user.get("digestive_issues") == "ibs":
            restrictions.append("high_fodmap")

        return restrictions

    def _diet_style(self):
        return {
            "culture": self.user.get("culture"),
            "region": self.user.get("region"),
            "state": self.user.get("state"),
            "veg_preference": self.user.get("diet_preference", "any")
        }
