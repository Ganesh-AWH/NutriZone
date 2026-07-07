import requests
import json
from simulation.config import ORGAN_BASELINES

class OllamaDigitalTwinExplainer:
    """BioMistral-powered LLM that explains digital twin responses.
    
    Uses BioMistral — a medical-domain model trained on PubMed literature —
    for clinically-grounded nutrition and organ health explanations.
    Falls back to rule-based explanations when Ollama is unavailable.
    """
    
    SYSTEM_PROMPT = (
        "You are a board-certified clinical nutritionist and internal medicine "
        "specialist. Ground every claim in established pathophysiology. "
        "Cite nutrient-organ mechanisms (e.g., Na⁺/K⁺-ATPase, hepatic "
        "de-novo lipogenesis, GFR filtration). Be concise, medically accurate, "
        "and actionable. Use metric units."
    )
    
    def __init__(self, base_url="http://localhost:11434", model_name="biomistral"):
        self.base_url = base_url
        self.model_name = model_name  # BioMistral — medical-domain model
    
    def _query_ollama(self, prompt, max_tokens=300, temperature=0.7):
        """Unified Ollama API call with system prompt injection."""
        full_prompt = f"[INST] <<SYS>>\n{self.SYSTEM_PROMPT}\n<</SYS>>\n\n{prompt} [/INST]"
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception:
            pass
        return None
        
    def explain_organ_response(self, organ_name, impact_data, nutrients):
        """Get medically-grounded LLM explanation for organ response."""
        
        prompt = f"""Analyse the following digital-twin organ response.

ORGAN: {organ_name}
NUTRIENT INTAKE: {json.dumps(nutrients, indent=2)}
HEALTH IMPACT: {impact_data['impact']:.3f} (Positive = beneficial, Negative = harmful)
NEW HEALTH SCORE: {impact_data['new_health']:.1%}

Respond in exactly 3 sections:
1. **Pathophysiology** — The biological mechanism explaining this organ's response (cite specific pathways, e.g. RAAS for kidney/sodium, insulin signalling for pancreas/sugar).
2. **Nutrient Analysis** — Which nutrients drove this impact and by how much. Reference the exact intake values provided.
3. **Evidence-Based Advice** — 2-3 specific, actionable dietary changes for the next meal, grounded in clinical guidelines (e.g. AHA sodium limits, WHO sugar recommendations).

Keep the total response under 200 words."""
        
        result = self._query_ollama(prompt, max_tokens=350)
        if result:
            return result
        return self._fallback_explanation(organ_name, impact_data, nutrients)
    
    def explain_agent_decision(self, agent_action, organ_states, nutrients, action_idx, reward=None):
        """Explain why the DQN agent chose a specific action, grounded in medical reasoning."""
        
        prompt = f"""A reinforcement-learning nutrition agent recommended: "{agent_action}"

CURRENT ORGAN HEALTH (0-1 scale):
{json.dumps(organ_states, indent=2)}

CURRENT NUTRIENT INTAKE:
{json.dumps(nutrients, indent=2)}

{"REWARD SIGNAL: " + f"{reward:.3f}" if reward is not None else ""}

Provide a clinical rationale in 4 parts:
1. **At-Risk Organs** — Which organs are below 0.7 health and the pathophysiology of their decline.
2. **Mechanism of Action** — How this dietary recommendation addresses the identified risks (cite 2-3 specific biochemical pathways).
3. **Expected Outcomes** — Predicted physiological improvements within 24-48 hours.
4. **Food Prescription** — 3-4 specific foods that implement this recommendation, with approximate serving sizes.

Keep under 250 words."""
        
        result = self._query_ollama(prompt, max_tokens=400)
        if result:
            return result
        return self._fallback_agent_explanation(agent_action, action_idx)
    
    def _fallback_explanation(self, organ_name, impact_data, nutrients):
        """Fallback explanation if Ollama/BioMistral is unavailable"""
        explanations = {
            "heart": f"❤️ Heart: Sodium ({nutrients.get('sodium',0)}mg) affects blood pressure via RAAS pathway. Fat ({nutrients.get('fat',0)}g) influences LDL cholesterol and atherosclerosis risk. Fiber ({nutrients.get('fiber',0)}g) binds bile acids to lower cholesterol.",
            "lungs": f"🫁 Lungs: Sugar ({nutrients.get('sugar',0)}g) drives systemic inflammation via NF-κB pathway. Iron ({nutrients.get('iron',0)}mg) supports hemoglobin synthesis for oxygen transport.",
            "brain": f"🧠 Brain: Sugar ({nutrients.get('sugar',0)}g) causes glycemic instability affecting neuronal energy. Fat ({nutrients.get('fat',0)}g) supports myelin sheath integrity. Protein ({nutrients.get('protein',0)}g) provides tryptophan/tyrosine for neurotransmitter synthesis.",
            "kidneys": f"🫘 Kidneys: Sodium ({nutrients.get('sodium',0)}mg) increases GFR workload. Protein ({nutrients.get('protein',0)}g) generates urea nitrogen requiring filtration. Adequate hydration essential.",
            "pancreas": f"🟨 Pancreas: Sugar ({nutrients.get('sugar',0)}g) triggers β-cell insulin secretion. Fiber ({nutrients.get('fiber',0)}g) slows gastric emptying reducing glycemic load. Carbs ({nutrients.get('carbs',0)}g) affect postprandial glucose.",
            "liver": f"🟤 Liver: Sugar ({nutrients.get('sugar',0)}g) drives hepatic de-novo lipogenesis. Fat ({nutrients.get('fat',0)}g) affects hepatic steatosis risk. Protein ({nutrients.get('protein',0)}g) supports hepatocyte regeneration. Fiber ({nutrients.get('fiber',0)}g) reduces portal endotoxin load.",
            "gut": f"🧬 Gut: Fiber ({nutrients.get('fiber',0)}g) feeds beneficial microbiota via SCFA production. Sugar ({nutrients.get('sugar',0)}g) promotes pathogenic bacterial overgrowth. Protein ({nutrients.get('protein',0)}g) supports enterocyte turnover.",
            "skin": f"🧴 Skin: Sugar ({nutrients.get('sugar',0)}g) causes AGE-mediated collagen cross-linking. Protein ({nutrients.get('protein',0)}g) provides proline/glycine for collagen synthesis. Fat ({nutrients.get('fat',0)}g) maintains stratum corneum lipid barrier.",
            "immune": f"🛡️ Immune: Protein ({nutrients.get('protein',0)}g) supports immunoglobulin synthesis. Iron ({nutrients.get('iron',0)}mg) enables myeloperoxidase activity in neutrophils. Excess sugar ({nutrients.get('sugar',0)}g) impairs phagocytic capacity for 5+ hours.",
            "muscles": f"💪 Muscles: Protein ({nutrients.get('protein',0)}g) activates mTOR pathway for muscle protein synthesis. Calories ({nutrients.get('calories',0)}) provide ATP for contraction. Iron ({nutrients.get('iron',0)}mg) supports myoglobin oxygen storage."
        }
        return explanations.get(organ_name, "Organ response analysis unavailable.")
    
    def _fallback_agent_explanation(self, agent_action, action_idx):
        """Fallback agent explanation"""
        explanations = {
            0: "🔬 AI suggests increasing protein for organ repair and muscle maintenance via mTOR activation.",
            1: "🔬 AI recommends reducing sugar to lower systemic inflammation (NF-κB) and protect pancreatic β-cells.",
            2: "🔬 AI advises boosting fiber for gut microbiome diversity via short-chain fatty acid production.",
            3: "🔬 AI suggests lowering sodium to reduce RAAS-mediated blood pressure and glomerular strain.",
            4: "🔬 AI recommends balancing macronutrients for sustained energy and metabolic homeostasis.",
            5: "🔬 AI advises adding healthy fats (omega-3) for brain function and anti-inflammatory prostaglandin production.",
            6: "🔬 AI suggests improving hydration for renal clearance and cellular osmotic balance.",
            7: "🔬 AI indicates current nutrition pattern supports organ health effectively — maintain course."
        }
        return explanations.get(action_idx, "AI recommendation based on current organ health patterns.")
    