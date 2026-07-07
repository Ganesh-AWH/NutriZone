def explanation_prompt(profile, plan, feedback=None):
    meals = []
    for m in ["breakfast", "lunch", "dinner"]:
        if m in plan and plan[m]:
            meals.append(
                f"{m.title()}: {plan[m]['dish_name']} "
                f"({round(plan[m]['calories'])} kcal)"
            )

    feedback_text = ""
    if feedback:
        feedback_text = f"""
Feedback:
- Hunger: {feedback.get("hunger")}
- Energy: {feedback.get("energy")}
"""

    return f"""
You are a nutrition explanation assistant.
Do NOT suggest new meals or change calories.

User goals:
- Calories: {round(profile['daily_calories'])}
- Protein: {round(profile['protein_target'])}
- Conditions: {profile['food_restrictions']}

Today's plan:
{chr(10).join(meals)}

{feedback_text}

Explain why this plan was chosen in simple language.
"""
