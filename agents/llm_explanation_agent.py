from typing import Dict, Optional


class LLMExplanationAgent:
    """
    Uses LLM ONLY to explain decisions.
    Never changes meals or numbers.
    """

    def __init__(self, llm):
        """
        llm: a callable with signature llm(prompt:str) -> str
        """
        self.llm = llm

    # =========================
    # PUBLIC ENTRY
    # =========================
    def explain_day_plan(
        self,
        user_profile: Dict,
        day_plan: Dict,
        feedback_adjustments: Optional[Dict] = None
    ) -> str:
        prompt = self._build_prompt(
            user_profile,
            day_plan,
            feedback_adjustments
        )
        return self.llm(prompt)

    # =========================
    # PROMPT CONSTRUCTION
    # =========================
    def _build_prompt(
        self,
        profile: Dict,
        plan: Dict,
        feedback: Optional[Dict]
    ) -> str:
        # ---------- MEAL TEXT (DEFENSIVE) ----------
        meals_text = ""

        for meal in ["breakfast", "lunch", "dinner"]:
            m = plan.get(meal)

            if m and isinstance(m, dict):
                meals_text += (
                    f"{meal.title()}: {m.get('dish_name', 'Unknown dish')} "
                    f"({round(m.get('calories', 0))} kcal, "
                    f"{round(m.get('protein', 0), 1)}g protein)\n"
                )
            else:
                meals_text += f"{meal.title()}: Not planned\n"

        # ---------- FEEDBACK TEXT ----------
        feedback_text = ""
        if feedback:
            feedback_text = f"""
User feedback from previous day:
- Hunger level: {feedback.get("hunger")}
- Energy level: {feedback.get("energy")}
- Weight change: {feedback.get("weight_change")} kg
- Preferred foods: {feedback.get("prefer_foods")}
- Avoided foods: {feedback.get("avoid_foods")}
"""

        # ---------- FINAL PROMPT ----------
        return f"""
You are a nutrition explanation assistant.

IMPORTANT RULES:
- Do NOT suggest new meals
- Do NOT change calories or quantities
- Do NOT give medical advice
- ONLY explain decisions already made

User health profile:
- Daily calorie target: {round(profile.get("daily_calories", 0))} kcal
- Protein target: {round(profile.get("protein_target", 0))} g
- Sodium limit: {profile.get("sodium_limit")} mg
- PCOS: {"Yes" if "pcos" in str(profile.get("food_restrictions", [])).lower() else "No"}
- IBS: {"Yes" if "high_fodmap" in str(profile.get("food_restrictions", [])).lower() else "No"}

Today's meal plan:
{meals_text}
{feedback_text}

Explain in simple, friendly language:
1. Why each meal was chosen
2. How it supports the user's health goals
3. How feedback influenced today's plan (if applicable)

Keep the explanation concise and easy to understand.
"""
