from agents.user_profile_agent import UserProfileAgent
from agents.meal_planner_agent import DailyMealPlanner
from agents.feedback_agent import FeedbackAgent
from agents.llm_explanation_agent import LLMExplanationAgent
from llm.llama_loader import LlamaLoader
from simulation.organ_twin import OrganDigitalTwin
from simulation.dqn_agent import DQNOrganOptimizer
from simulation.config import DEFAULT_NUTRIENTS

class NutritionOrchestrator:
    def __init__(self):
        self.llm_loader = LlamaLoader()
        self.explainer = LLMExplanationAgent(self.llm_loader.generate)
        self.dqn_agent = DQNOrganOptimizer()

    def run_day(self, user_input, feedback=None):
        profile = UserProfileAgent(user_input).build_profile()

        if feedback:
            feedback_agent = FeedbackAgent(feedback["yesterday_plan"], feedback)
            adjustments = feedback_agent.generate_adjustments()
        else:
            adjustments = None

        # --- DQN Agent Neuro-Symbolic Inference ---
        twin = OrganDigitalTwin(user_id="orchestrator_temp")
        if "diseases" in profile and profile["diseases"]:
            twin.apply_disease_modifiers([d for d in profile["diseases"] if d])
        
        state_tensor = self.dqn_agent.get_state(twin, DEFAULT_NUTRIENTS)
        action_idx = self.dqn_agent.act(state_tensor, epsilon=0.0) # Greedy inference
        dqn_actions = self.dqn_agent.actions
        dqn_strategy = dqn_actions[action_idx] if action_idx < len(dqn_actions) else None
        # ------------------------------------------

        planner = DailyMealPlanner(profile, adjustments, dqn_strategy=dqn_strategy)
        plan = planner.generate_day_plan()

        try:
            explanation = self.explainer.explain_day_plan(
                user_profile=profile,
                day_plan=plan,
                feedback_adjustments=feedback
            )
            if dqn_strategy:
                explanation += f"\n\n🩺 **Clinical AI Override:** Detected via DQN Digital Twin Simulator. Strategy applied: '{dqn_strategy}'."
        except Exception:
            # Never fail the API if the explainer fails
            explanation = ""

        return {
            "profile": profile,
            "plan": plan,
            "explanation": explanation
        }
