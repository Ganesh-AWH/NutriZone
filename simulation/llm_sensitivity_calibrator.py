"""
LLM Organ Sensitivity Calibrator
==================================
Uses BioMistral to dynamically generate and calibrate organ sensitivity
values based on medical literature, user conditions, and current organ states.

Instead of relying purely on hardcoded sensitivity values in config.py,
this module queries the LLM to produce condition-aware adjustments.

Architecture:
  ┌──────────────────────┐
  │  User Conditions     │  (e.g., diabetes, hypertension, CKD)
  │  + Current Organ     │
  │    Health States     │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  LLM Sensitivity     │  BioMistral evaluates medical context
  │  Calibrator          │  and adjusts organ sensitivities
  └──────────┬───────────┘
             │  condition-specific sensitivities
             ▼
  ┌──────────────────────┐
  │  Organ Digital Twin  │  Uses calibrated sensitivities for
  │  (organ_twin.py)     │  impact calculations
  └──────────────────────┘
"""

import requests
import json
import re
from simulation.config import ORGAN_DEFINITIONS


class LLMSensitivityCalibrator:
    """Uses BioMistral to dynamically calibrate organ sensitivities.
    
    Given user medical conditions and current organ health, the LLM
    adjusts the sensitivity values that govern how nutrients impact
    each organ in the digital twin simulation.
    
    Parameters
    ----------
    base_url : str
        Ollama server URL.
    model_name : str
        Ollama model (default: biomistral).
    blend_factor : float
        How much to blend LLM-suggested sensitivities with defaults.
        0.0 = use only defaults, 1.0 = use only LLM values.
        Default: 0.5 (50/50 blend).
    """

    SYSTEM_PROMPT = (
        "You are a clinical pathophysiology expert calibrating a digital twin "
        "organ simulation. You adjust nutrient-organ sensitivity coefficients "
        "based on patient conditions and medical evidence. "
        "Return ONLY valid JSON. Use established dose-response relationships."
    )

    # Nutrients the system tracks
    NUTRIENTS = ["calories", "carbs", "protein", "fat", "sugar", "fiber",
                 "sodium", "calcium", "iron"]

    def __init__(self, base_url="http://localhost:11434", model_name="biomistral",
                 blend_factor=0.5):
        self.base_url = base_url
        self.model_name = model_name
        self.blend_factor = max(0.0, min(1.0, blend_factor))
        self._calibration_cache = {}
        self._default_sensitivities = self._extract_defaults()

    def _extract_defaults(self):
        """Extract default sensitivity values from ORGAN_DEFINITIONS."""
        defaults = {}
        for organ, defn in ORGAN_DEFINITIONS.items():
            defaults[organ] = dict(defn.get("sensitivity", {}))
        return defaults

    def calibrate(self, user_conditions=None, organ_states=None):
        """Generate calibrated sensitivity values for all organs.
        
        Parameters
        ----------
        user_conditions : list[str] or None
            Medical conditions, e.g. ["type_2_diabetes", "hypertension"].
        organ_states : dict or None
            Current organ health {organ: float}.
        
        Returns
        -------
        dict
            {organ_name: {nutrient: sensitivity_value, ...}, ...}
            Ready to be applied to ORGAN_DEFINITIONS.
        """
        if not user_conditions:
            return self._default_sensitivities.copy()
        
        # Check cache
        cache_key = "|".join(sorted(user_conditions))
        if cache_key in self._calibration_cache:
            return self._calibration_cache[cache_key]
        
        # Query LLM for condition-specific adjustments
        llm_adjustments = self._query_llm_calibration(user_conditions, organ_states)
        
        if llm_adjustments:
            calibrated = self._blend_sensitivities(
                self._default_sensitivities, llm_adjustments
            )
            # Cache the result
            self._calibration_cache[cache_key] = calibrated
            return calibrated
        
        return self._default_sensitivities.copy()

    def calibrate_single_organ(self, organ_name, user_conditions=None, organ_health=None):
        """Calibrate sensitivities for a single organ.
        
        Parameters
        ----------
        organ_name : str
            Name of the organ to calibrate.
        user_conditions : list[str] or None
            Patient medical conditions.
        organ_health : float or None
            Current health of this organ (0-1).
        
        Returns
        -------
        dict
            {nutrient: sensitivity_value, ...} for the specified organ.
        """
        if not user_conditions or organ_name not in self._default_sensitivities:
            return self._default_sensitivities.get(organ_name, {}).copy()
        
        organ_states = {organ_name: organ_health} if organ_health is not None else None
        
        llm_result = self._query_single_organ(organ_name, user_conditions, organ_states)
        
        if llm_result:
            default = self._default_sensitivities[organ_name]
            return self._blend_single(default, llm_result)
        
        return self._default_sensitivities[organ_name].copy()

    def _query_llm_calibration(self, user_conditions, organ_states):
        """Ask BioMistral to calibrate sensitivities for all organs."""
        
        # Build a compact representation of defaults
        defaults_compact = {}
        for organ, sens in self._default_sensitivities.items():
            defaults_compact[organ] = sens
        
        states_text = ""
        if organ_states:
            at_risk = {o: f"{h:.2f}" for o, h in organ_states.items() if h < 0.75}
            if at_risk:
                states_text = f"\nAT-RISK ORGANS (health < 0.75): {json.dumps(at_risk)}"
        
        prompt = f"""A digital-twin patient has these conditions: {', '.join(user_conditions)}
{states_text}

Current DEFAULT organ-nutrient sensitivity values (positive = harmful, negative = beneficial):
{json.dumps(defaults_compact, indent=2)}

Based on the patient's conditions, adjust the sensitivity values.
Rules:
- Only modify sensitivities that are CLINICALLY RELEVANT to the conditions
- Keep values in range [-1.0, +1.0]
- Positive = nutrient harms the organ; Negative = nutrient benefits the organ
- For diabetes: increase pancreas sugar sensitivity, increase liver sugar sensitivity
- For hypertension: increase heart and kidney sodium sensitivity
- For CKD: increase kidney protein sensitivity
- Cite the pathophysiological basis for each change

Return ONLY a JSON object mapping organ → nutrient → new_value for CHANGED values only:
{{
  "adjustments": {{
    "organ_name": {{"nutrient": new_value, ...}},
    ...
  }},
  "rationale": "Brief clinical reasoning"
}}"""

        full_prompt = f"[INST] <<SYS>>\n{self.SYSTEM_PROMPT}\n<</SYS>>\n\n{prompt} [/INST]"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Very low temp for precision
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                raw = response.json().get("response", "")
                return self._parse_calibration_response(raw)
                
        except Exception:
            pass
        
        # Fallback: use hardcoded condition-specific adjustments
        return self._heuristic_calibration(user_conditions)

    def _query_single_organ(self, organ_name, user_conditions, organ_states):
        """Ask BioMistral to calibrate a single organ's sensitivities."""
        
        default_sens = self._default_sensitivities.get(organ_name, {})
        
        health_text = ""
        if organ_states and organ_name in organ_states:
            health_text = f"\nCurrent {organ_name} health: {organ_states[organ_name]:.2f}"
        
        prompt = f"""Patient conditions: {', '.join(user_conditions)}
{health_text}

Default {organ_name} nutrient sensitivities (positive = harmful, negative = beneficial):
{json.dumps(default_sens, indent=2)}

Adjust these values based on the patient's conditions.
Return ONLY a JSON object with the adjusted values:
{{
  "nutrient_name": adjusted_value,
  ...
}}

Only include nutrients that should change. Keep values in [-1.0, +1.0]."""

        full_prompt = f"[INST] <<SYS>>\n{self.SYSTEM_PROMPT}\n<</SYS>>\n\n{prompt} [/INST]"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 200}
                },
                timeout=20
            )
            
            if response.status_code == 200:
                raw = response.json().get("response", "")
                return self._parse_single_organ_response(raw)
                
        except Exception:
            pass
        
        return None

    def _parse_calibration_response(self, raw_text):
        """Parse multi-organ calibration JSON from LLM."""
        try:
            data = json.loads(raw_text.strip())
            if "adjustments" in data:
                return self._validate_adjustments(data["adjustments"])
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Try extracting JSON block
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if "adjustments" in data:
                    return self._validate_adjustments(data["adjustments"])
                # Maybe the whole thing IS the adjustments dict
                return self._validate_adjustments(data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None

    def _parse_single_organ_response(self, raw_text):
        """Parse single-organ sensitivity JSON from LLM."""
        try:
            data = json.loads(raw_text.strip())
            return self._validate_nutrient_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass
        
        json_match = re.search(r'\{[^}]+\}', raw_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._validate_nutrient_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None

    def _validate_adjustments(self, adjustments):
        """Validate and sanitize the adjustments dictionary."""
        validated = {}
        valid_organs = set(self._default_sensitivities.keys())
        valid_nutrients = set(self.NUTRIENTS)
        
        for organ, sens in adjustments.items():
            if organ not in valid_organs:
                continue
            if not isinstance(sens, dict):
                continue
            validated_sens = {}
            for nutrient, value in sens.items():
                if nutrient in valid_nutrients:
                    try:
                        val = float(value)
                        validated_sens[nutrient] = max(-1.0, min(1.0, val))
                    except (ValueError, TypeError):
                        continue
            if validated_sens:
                validated[organ] = validated_sens
        
        return validated if validated else None

    def _validate_nutrient_dict(self, data):
        """Validate a single nutrient sensitivity dictionary."""
        valid_nutrients = set(self.NUTRIENTS)
        validated = {}
        for nutrient, value in data.items():
            if nutrient in valid_nutrients:
                try:
                    val = float(value)
                    validated[nutrient] = max(-1.0, min(1.0, val))
                except (ValueError, TypeError):
                    continue
        return validated if validated else None

    def _blend_sensitivities(self, defaults, adjustments):
        """Blend default and LLM-adjusted sensitivities.
        
        result = (1 - blend_factor) × default + blend_factor × llm_value
        """
        result = {}
        for organ, default_sens in defaults.items():
            blended = dict(default_sens)  # Start with defaults
            if organ in adjustments:
                for nutrient, llm_val in adjustments[organ].items():
                    if nutrient in blended:
                        blended[nutrient] = (
                            (1 - self.blend_factor) * blended[nutrient] +
                            self.blend_factor * llm_val
                        )
                    else:
                        # LLM added a new sensitivity
                        blended[nutrient] = self.blend_factor * llm_val
            result[organ] = blended
        return result

    def _blend_single(self, default_sens, llm_sens):
        """Blend sensitivities for a single organ."""
        blended = dict(default_sens)
        for nutrient, llm_val in llm_sens.items():
            if nutrient in blended:
                blended[nutrient] = (
                    (1 - self.blend_factor) * blended[nutrient] +
                    self.blend_factor * llm_val
                )
            else:
                blended[nutrient] = self.blend_factor * llm_val
        return blended

    def _heuristic_calibration(self, user_conditions):
        """Hardcoded condition-specific sensitivity adjustments.
        
        Used when BioMistral is unavailable. Based on established
        clinical guidelines.
        """
        conditions = set(c.lower().replace(" ", "_") for c in user_conditions)
        adjustments = {}
        
        # ----- Diabetes / Pre-diabetes -----
        if conditions & {"diabetes", "type_2_diabetes", "type_1_diabetes",
                         "pre_diabetes", "prediabetes", "t2dm", "t1dm"}:
            adjustments["pancreas"] = {
                "sugar": 0.95,      # ↑ from 0.9 — β-cell exhaustion
                "fiber": -0.75,     # ↑ benefit — glycemic control
                "carbs": 0.6,       # ↑ from 0.4 — insulin resistance
                "fat": 0.35,        # ↑ — impairs insulin signaling
            }
            adjustments["liver"] = {
                "sugar": 0.9,       # ↑ from 0.8 — hepatic lipogenesis
                "fat": 0.65,        # ↑ from 0.5 — NAFLD risk
            }
            adjustments["kidneys"] = {
                "protein": 0.55,    # ↑ from 0.4 — diabetic nephropathy
                "sodium": 0.95,     # ↑ — compounded renal stress
            }
            adjustments["heart"] = {
                "fat": 0.75,        # ↑ from 0.6 — accelerated atherosclerosis
            }
        
        # ----- Hypertension -----
        if conditions & {"hypertension", "high_blood_pressure", "htn"}:
            adjustments.setdefault("heart", {})
            adjustments["heart"].update({
                "sodium": 0.95,     # ↑ from 0.8 — RAAS overactivation
                "fat": 0.7,         # ↑ — vascular stiffness
                "fiber": -0.5,      # ↑ benefit — DASH diet evidence
            })
            adjustments.setdefault("kidneys", {})
            adjustments["kidneys"].update({
                "sodium": 0.95,     # ↑ — renal sodium handling impaired
            })
        
        # ----- Chronic Kidney Disease -----
        if conditions & {"ckd", "chronic_kidney_disease", "kidney_disease",
                         "renal_disease"}:
            adjustments.setdefault("kidneys", {})
            adjustments["kidneys"].update({
                "protein": 0.7,     # ↑ from 0.4 — reduced GFR
                "sodium": 0.95,     # ↑ — impaired sodium excretion
                "calcium": -0.35,   # ↑ benefit — bone mineral density
            })
        
        # ----- Liver Disease / NAFLD -----
        if conditions & {"nafld", "fatty_liver", "liver_disease", "cirrhosis",
                         "hepatitis"}:
            adjustments.setdefault("liver", {})
            adjustments["liver"].update({
                "sugar": 0.95,      # ↑ — de novo lipogenesis
                "fat": 0.75,        # ↑ — hepatic steatosis
                "protein": -0.45,   # ↑ benefit — hepatocyte repair
            })
        
        # ----- IBD / Gut issues -----
        if conditions & {"ibd", "crohns", "ulcerative_colitis", "ibs",
                         "leaky_gut"}:
            adjustments.setdefault("gut", {})
            adjustments["gut"].update({
                "sugar": 0.8,       # ↑ — dysbiosis
                "fiber": -0.8,      # ↑ benefit — SCFA production
            })
            adjustments.setdefault("immune", {})
            adjustments["immune"].update({
                "sugar": 0.65,      # ↑ — gut-immune axis inflammation
            })
        
        # ----- Cardiovascular Disease -----
        if conditions & {"cvd", "heart_disease", "cad", "coronary_artery_disease",
                         "atherosclerosis"}:
            adjustments.setdefault("heart", {})
            adjustments["heart"].update({
                "fat": 0.8,         # ↑ — plaque progression
                "sodium": 0.9,      # ↑ — volume overload
                "fiber": -0.55,     # ↑ benefit — cholesterol binding
            })
        
        # ----- Obesity -----
        if conditions & {"obesity", "overweight", "morbid_obesity"}:
            adjustments.setdefault("heart", {})
            adjustments["heart"].update({
                "calories": 0.4,    # ↑ — cardiac workload
            })
            adjustments.setdefault("liver", {})
            adjustments["liver"].update({
                "calories": 0.3,    # new — metabolic burden
            })
            adjustments.setdefault("pancreas", {})
            adjustments["pancreas"].update({
                "sugar": 0.95,      # ↑ — insulin resistance
            })

        return adjustments if adjustments else None

    def get_calibration_report(self, user_conditions, organ_states=None):
        """Generate a human-readable calibration report.
        
        Returns
        -------
        str
            Formatted report of sensitivity adjustments.
        """
        calibrated = self.calibrate(user_conditions, organ_states)
        
        report_lines = [
            "# 🔬 LLM Sensitivity Calibration Report",
            f"**Conditions**: {', '.join(user_conditions)}",
            f"**Blend Factor**: {self.blend_factor:.0%} LLM / {1-self.blend_factor:.0%} Default",
            ""
        ]
        
        for organ, sens in calibrated.items():
            default = self._default_sensitivities.get(organ, {})
            changes = []
            for nutrient, value in sens.items():
                default_val = default.get(nutrient, 0)
                if abs(value - default_val) > 0.01:
                    direction = "↑" if abs(value) > abs(default_val) else "↓"
                    changes.append(
                        f"  - {nutrient}: {default_val:+.2f} → {value:+.2f} {direction}"
                    )
            
            if changes:
                report_lines.append(f"### {organ.title()}")
                report_lines.extend(changes)
                report_lines.append("")
        
        if len(report_lines) <= 4:
            report_lines.append("_No adjustments needed for the given conditions._")
        
        return "\n".join(report_lines)

    def clear_cache(self):
        """Clear the calibration cache."""
        self._calibration_cache = {}
