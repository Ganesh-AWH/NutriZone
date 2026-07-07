from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from simulation.dqn_agent import DQNOrganOptimizer
from simulation.llm_explainer import OllamaDigitalTwinExplainer
from simulation.llm_reward_shaper import LLMRewardShaper
from simulation.llm_sensitivity_calibrator import LLMSensitivityCalibrator
from simulation.config import ORGAN_DEFINITIONS

# Share the same digital twin used by the 3D visualizer
from api.body_state import _get_twin as get_twin

simulation_router = APIRouter()

# Global state for the simulation (replacing Streamlit's session_state)
class SimulationState:
    def __init__(self):
        self.reset()

    def reset(self):
        # We also need to reset the shared twin
        twin = get_twin()
        twin.__init__() # Re-init the shared instance
        
        self.dqn_agent = DQNOrganOptimizer(state_size=23, action_size=8)
        self.ollama_explainer = OllamaDigitalTwinExplainer()
        self.llm_reward_shaper = LLMRewardShaper()
        self.llm_sensitivity_calibrator = LLMSensitivityCalibrator()
        
        self.meal_history = []
        self.explanations = []
        self.last_reward = 0
        self.training_loss_history = []
        self.user_conditions = []
        self.sensitivity_calibrated = False

global_state = SimulationState()


class SimulateRequest(BaseModel):
    nutrients: Dict[str, float]
    meal_name: str = "My Meal"
    use_ollama: bool = True
    show_explanations: bool = True
    auto_apply_ai: bool = False
    use_llm_reward: bool = True

class CalibrateRequest(BaseModel):
    conditions: List[str]


@simulation_router.post("/simulation/simulate")
def simulate_meal(req: SimulateRequest):
    twin = get_twin()
    s = global_state
    
    nutrients = dict(req.nutrients)
    
    # Get current state
    state = s.dqn_agent.get_state(twin, nutrients)
    
    # Select action
    action_idx = s.dqn_agent.select_action(state)
    
    # Get modified nutrients if auto-apply is enabled
    original_nutrients = dict(nutrients)
    changes = {}
    if req.auto_apply_ai and action_idx != 7:  # Don't modify if "maintain pattern"
        nutrients = s.dqn_agent.apply_action_to_nutrients(action_idx, nutrients)
        changes = {k: f"{original_nutrients[k]:.1f} → {nutrients[k]:.1f}"
                   for k in nutrients if abs(nutrients[k] - original_nutrients[k]) > 0.01}
    
    # Simulate impact
    impacts, numeric_reward = twin.simulate_meal_impact(nutrients, meal_name=req.meal_name)
    
    reward = numeric_reward
    reward_result = {}
    if req.use_llm_reward and req.use_ollama:
        organ_states = twin.get_organ_states()
        norm_states = {o: st.get("health", 0.5) if isinstance(st, dict) else st
                       for o, st in organ_states.items()}
        action_name = s.dqn_agent.actions[action_idx]
        reward_result = s.llm_reward_shaper.shape_reward(
            numeric_reward, action_name, norm_states, nutrients,
            user_conditions=s.user_conditions or None
        )
        reward = reward_result.get("composite_reward", reward)
        
    s.last_reward = reward
    
    # Get next state for RL
    next_state = s.dqn_agent.get_state(twin, nutrients)
    
    # Store transition for RL training
    s.dqn_agent.store_transition(state.detach(), action_idx, reward, next_state.detach(), False)
    
    # Train agent if enough data
    if len(s.dqn_agent.memory) >= s.dqn_agent.batch_size:
        loss = s.dqn_agent.replay()
        if loss:
            s.training_loss_history.append(float(loss))
            
    # Get recommendation
    recommendation = s.dqn_agent.get_recommendation(action_idx, nutrients)
    
    new_explanations = []
    # Get LLM explanations if enabled
    if req.use_ollama and req.show_explanations:
        try:
            most_impacted = max(impacts.items(), key=lambda x: abs(x[1]["impact"]))
            organ_name, impact_data = most_impacted
            
            explanation = s.ollama_explainer.explain_organ_response(organ_name, impact_data, nutrients)
            exp_organ = {
                "organ": organ_name,
                "explanation": explanation,
                "timestamp": datetime.now().isoformat()
            }
            s.explanations.append(exp_organ)
            new_explanations.append(exp_organ)
            
            agent_explanation = s.ollama_explainer.explain_agent_decision(
                s.dqn_agent.actions[action_idx],
                twin.get_organ_states(),
                nutrients,
                action_idx,
                reward
            )
            exp_agent = {
                "type": "agent_decision",
                "explanation": agent_explanation,
                "timestamp": datetime.now().isoformat(),
                "reward": reward
            }
            s.explanations.append(exp_agent)
            new_explanations.append(exp_agent)
        except Exception as e:
            print("LLM Error:", e)
            
    health_change = twin.get_overall_health() - twin.get_overall_health_previous()
    
    meal_record = {
        "meal": req.meal_name,
        "nutrients": nutrients,
        "overall_impact": float(np.mean([impacts[o]["impact"] for o in impacts])),
        "recommendation": recommendation,
        "action": s.dqn_agent.actions[action_idx],
        "reward": float(reward),
        "health_change": float(health_change),
        "timestamp": datetime.now().isoformat()
    }
    s.meal_history.append(meal_record)
    
    return {
        "status": "success",
        "reward": float(reward),
        "reward_result": reward_result,
        "changes": changes,
        "meal_record": meal_record,
        "new_explanations": new_explanations
    }

@simulation_router.post("/simulation/train")
def train_agent():
    s = global_state
    if s.dqn_agent.memory:
        loss = s.dqn_agent.replay()
        if loss:
            s.training_loss_history.append(float(loss))
            return {"status": "trained", "loss": float(loss)}
    return {"status": "skipped", "message": "Not enough memory"}

@simulation_router.post("/simulation/reset")
def reset_simulation():
    global_state.reset()
    return {"status": "reset"}

@simulation_router.post("/simulation/calibrate")
def calibrate_sensitivities(req: CalibrateRequest):
    s = global_state
    twin = get_twin()
    s.user_conditions = req.conditions
    
    if req.conditions:
        calibrator = s.llm_sensitivity_calibrator
        organ_states = twin.get_organ_states()
        norm_states = {o: st.get("health", 0.5) if isinstance(st, dict) else st
                       for o, st in organ_states.items()}
        calibrated = calibrator.calibrate(req.conditions, norm_states)
        for organ, sens in calibrated.items():
            if organ in ORGAN_DEFINITIONS:
                ORGAN_DEFINITIONS[organ]["sensitivity"] = sens
        s.sensitivity_calibrated = True
        report = calibrator.get_calibration_report(req.conditions, norm_states)
        return {"status": "calibrated", "report": report}
    return {"status": "skipped"}

@simulation_router.get("/simulation/state")
def get_simulation_state():
    s = global_state
    
    # Calculate some summary stats
    avg_reward = float(np.mean([m.get("reward", 0) for m in s.meal_history[-5:]])) if s.meal_history else 0
    decision_log = []
    for d in s.dqn_agent.decision_log[-10:]:
        log_e = dict(d)
        log_e["timestamp"] = d["timestamp"].isoformat()
        decision_log.append(log_e)
        
    return {
        "user_conditions": s.user_conditions,
        "sensitivity_calibrated": s.sensitivity_calibrated,
        "meal_history": s.meal_history[-20:], # Only last 20 for UI
        "total_meals": len(s.meal_history),
        "last_reward": s.last_reward,
        "training_loss_history": s.training_loss_history[-50:],
        "explanations": s.explanations[-20:],
        "insights": {
            "epsilon": float(s.dqn_agent.epsilon),
            "memory_size": len(s.dqn_agent.memory),
            "decisions_made": len(s.dqn_agent.decision_log),
            "avg_reward_last_5": avg_reward,
            "recent_decisions": decision_log
        }
    }
