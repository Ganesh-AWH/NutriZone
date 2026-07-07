"""
LLM-in-the-Loop RL Reward Shaper
=================================
Uses BioMistral (medical-domain LLM) to generate supplementary reward
signals for the DQN agent.  The LLM evaluates nutrient-organ interactions
from a clinical perspective and produces a structured reward bonus that is
blended with the numeric organ-health reward.

Architecture:
  ┌──────────┐    state, action     ┌──────────────┐
  │ DQN Agent├──────────────────────► Organ Twin   │
  └────┬─────┘                      └──────┬───────┘
       │                                   │  numeric reward
       │  ┌────────────────────────────────┘
       │  │
       ▼  ▼
  ┌────────────────┐   medical context   ┌────────────────┐
  │ Reward Combiner│◄────────────────────│ LLM Reward     │
  │  (α·R_num +    │                     │ Shaper         │
  │   β·R_llm)     │                     │ (BioMistral)   │
  └────────────────┘                     └────────────────┘
"""

import requests
import json
import re


class LLMRewardShaper:
    """Uses BioMistral to generate medically-informed reward signals for RL.
    
    The LLM evaluates the nutritional action taken by the DQN agent and
    produces a reward modifier in [-1.0, +1.0] based on clinical reasoning.
    This is blended with the numeric reward to create a composite signal.
    
    Parameters
    ----------
    base_url : str
        Ollama server URL.
    model_name : str
        Ollama model to use (default: biomistral).
    alpha : float
        Weight for the numeric (organ-health) reward.  Default 0.7.
    beta : float
        Weight for the LLM-generated reward.  Default 0.3.
    """

    SYSTEM_PROMPT = (
        "You are a clinical nutrition reward evaluator for a reinforcement "
        "learning system. You evaluate dietary actions and return ONLY a "
        "JSON object with a numeric score and brief rationale. "
        "Ground your evaluation in pathophysiology."
    )

    def __init__(self, base_url="http://localhost:11434", model_name="biomistral",
                 alpha=0.7, beta=0.3):
        self.base_url = base_url
        self.model_name = model_name
        self.alpha = alpha
        self.beta = beta
        self._cache = {}  # Simple cache to avoid redundant LLM calls

    def shape_reward(self, numeric_reward, action_name, organ_states,
                     nutrients, user_conditions=None):
        """Compute a composite reward = α·R_numeric + β·R_llm.
        
        Parameters
        ----------
        numeric_reward : float
            The reward computed by OrganDigitalTwin._calculate_reward().
        action_name : str
            The DQN action label (e.g., "Increase Protein").
        organ_states : dict
            Current organ health scores {organ_name: float}.
        nutrients : dict
            Current nutrient intake values.
        user_conditions : list[str] or None
            Optional medical conditions (e.g., ["diabetes", "hypertension"]).
        
        Returns
        -------
        dict
            {
                "composite_reward": float,
                "numeric_reward": float,
                "llm_reward": float,
                "llm_rationale": str,
                "used_llm": bool
            }
        """
        llm_reward, rationale, used_llm = self._get_llm_reward(
            action_name, organ_states, nutrients, user_conditions
        )
        
        composite = self.alpha * numeric_reward + self.beta * llm_reward
        
        return {
            "composite_reward": composite,
            "numeric_reward": numeric_reward,
            "llm_reward": llm_reward,
            "llm_rationale": rationale,
            "used_llm": used_llm
        }

    def _get_llm_reward(self, action_name, organ_states, nutrients, user_conditions):
        """Query BioMistral for a medical reward evaluation.
        
        Returns
        -------
        tuple(float, str, bool)
            (llm_reward, rationale, used_llm)
        """
        # Build cache key from action + critical organ info
        at_risk = [o for o, h in organ_states.items() if h < 0.7]
        cache_key = f"{action_name}|{'_'.join(sorted(at_risk))}"
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return cached["score"], cached["rationale"], True
        
        conditions_text = ""
        if user_conditions:
            conditions_text = f"\nUSER CONDITIONS: {', '.join(user_conditions)}"
        
        prompt = f"""Evaluate this dietary action for a digital-twin patient.

ACTION: {action_name}

ORGAN HEALTH (0-1 scale, <0.7 = at risk):
{json.dumps(organ_states, indent=2)}

NUTRIENT INTAKE:
{json.dumps(nutrients, indent=2)}
{conditions_text}

Return ONLY a JSON object (no markdown, no extra text):
{{
  "score": <float between -1.0 and 1.0>,
  "rationale": "<1-2 sentence clinical justification>"
}}

Scoring guide:
- +0.8 to +1.0: Action directly addresses the most critical organ deficiency via an established pathway
- +0.3 to +0.7: Action is beneficial but not optimally targeted
- -0.3 to +0.3: Action is neutral or marginally relevant
- -0.7 to -0.3: Action could worsen an at-risk organ
- -1.0 to -0.7: Action is medically contraindicated given organ states"""

        full_prompt = f"[INST] <<SYS>>\n{self.SYSTEM_PROMPT}\n<</SYS>>\n\n{prompt} [/INST]"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Low temp for consistent scoring
                        "num_predict": 150
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                raw = response.json().get("response", "")
                result = self._parse_reward_response(raw)
                
                # Cache for reuse
                self._cache[cache_key] = result
                
                return result["score"], result["rationale"], True
                
        except Exception:
            pass
        
        # Fallback: use heuristic reward
        return self._heuristic_reward(action_name, organ_states, nutrients)

    def _parse_reward_response(self, raw_text):
        """Parse LLM JSON response, with fallback extraction."""
        try:
            # Try direct JSON parse
            data = json.loads(raw_text.strip())
            score = max(-1.0, min(1.0, float(data["score"])))
            return {"score": score, "rationale": data.get("rationale", "")}
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
        
        # Try to extract JSON from mixed text
        json_match = re.search(r'\{[^}]+\}', raw_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                score = max(-1.0, min(1.0, float(data["score"])))
                return {"score": score, "rationale": data.get("rationale", "")}
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        
        # Try to extract just a number
        num_match = re.search(r'[-+]?\d*\.?\d+', raw_text)
        if num_match:
            score = max(-1.0, min(1.0, float(num_match.group())))
            return {"score": score, "rationale": raw_text[:100]}
        
        return {"score": 0.0, "rationale": "Could not parse LLM response"}

    def _heuristic_reward(self, action_name, organ_states, nutrients):
        """Rule-based fallback reward when LLM is unavailable.
        
        Returns
        -------
        tuple(float, str, bool)
            (score, rationale, used_llm=False)
        """
        action_lower = action_name.lower()
        at_risk = {o: h for o, h in organ_states.items() if h < 0.7}
        
        score = 0.0
        reasons = []
        
        # Check if action targets the right problem
        if "protein" in action_lower:
            if "muscles" in at_risk:
                score += 0.5
                reasons.append("Protein targets at-risk muscles (mTOR)")
            if "immune" in at_risk:
                score += 0.3
                reasons.append("Protein supports immunoglobulin synthesis")
        
        if "sugar" in action_lower or "reduce sugar" in action_lower:
            if "pancreas" in at_risk:
                score += 0.6
                reasons.append("Reducing sugar protects β-cells")
            if "liver" in at_risk:
                score += 0.3
                reasons.append("Less sugar reduces hepatic lipogenesis")
        
        if "fiber" in action_lower:
            if "gut" in at_risk:
                score += 0.6
                reasons.append("Fiber feeds microbiome via SCFAs")
            if "pancreas" in at_risk:
                score += 0.2
                reasons.append("Fiber slows glucose absorption")
        
        if "sodium" in action_lower:
            if "heart" in at_risk:
                score += 0.5
                reasons.append("Lower sodium reduces RAAS activation")
            if "kidneys" in at_risk:
                score += 0.5
                reasons.append("Lower sodium reduces GFR workload")
        
        if "fat" in action_lower or "healthy fats" in action_lower:
            if "brain" in at_risk:
                score += 0.5
                reasons.append("Omega-3 fats support myelin integrity")
        
        if "hydration" in action_lower:
            if "kidneys" in at_risk:
                score += 0.4
                reasons.append("Hydration supports renal clearance")
        
        # Penalty if no at-risk organs and we're making changes
        if not at_risk and "maintain" not in action_lower:
            score -= 0.1
            reasons.append("No critical organs — conservative approach preferred")
        
        score = max(-1.0, min(1.0, score))
        rationale = "; ".join(reasons) if reasons else "Neutral action"
        
        return score, rationale, False

    def clear_cache(self):
        """Clear the reward evaluation cache."""
        self._cache = {}
