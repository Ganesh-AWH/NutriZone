"""
/body-state endpoint — exposes real-time organ health data for the
Three.js 3D frontend.

The endpoint creates an OrganDigitalTwin instance (or re-uses a cached
one) and returns the current organ states plus derived animation
parameters.

Add this router to server.py:
    from api.body_state import body_state_router
    app.include_router(body_state_router)
"""

import time
import math
import random
from fastapi import APIRouter
from simulation.organ_twin import OrganDigitalTwin
from simulation.config import ORGAN_DEFINITIONS, ORGAN_WEIGHTS, ORGAN_BASELINES

body_state_router = APIRouter()

# Singleton digital twin for the 3D view
_twin: OrganDigitalTwin | None = None
_start_time: float = time.time()


def _get_twin() -> OrganDigitalTwin:
    global _twin
    if _twin is None:
        _twin = OrganDigitalTwin()
    return _twin


@body_state_router.get("/body-state")
def get_body_state():
    """
    Return full body state for the 3D visualisation.

    Shape:
    {
        "heart_rate": float,
        "breathing_rate": float,
        "calorie_surplus": float,
        "protein_intake": float,
        "glucose_level": float,
        "overall_health": float,
        "organs": {
            "<name>": {
                "health": float,
                "system": str,
                "function": str,
                "riskFactors": [str],
                "metrics": { ... }
            },
            ...
        }
    }
    """
    twin = _get_twin()
    elapsed = time.time() - _start_time

    # ── Build per-organ data ─────────────────────────────────
    organs_data = {}
    for name, organ in twin.organs.items():
        health = organ.get("health", 0.7)
        defn = ORGAN_DEFINITIONS.get(name, {})
        metrics = organ.get("metrics", {})

        # Round metric values for JSON
        clean_metrics = {}
        for k, v in metrics.items():
            if isinstance(v, float):
                clean_metrics[k] = round(v, 2)
            else:
                clean_metrics[k] = v

        organs_data[name] = {
            "health": round(health, 4),
            "system": defn.get("system", "—"),
            "function": defn.get("function", "—"),
            "riskFactors": defn.get("risk_factors", []),
            "metrics": clean_metrics,
        }

    # ── Derived animation parameters ─────────────────────────
    # Simulate subtle variation (so the 3D view always feels alive)
    heart_rate = 72 + math.sin(elapsed * 0.08) * 10 + random.uniform(-2, 2)
    breathing_rate = 15 + math.sin(elapsed * 0.06) * 3 + random.uniform(-1, 1)
    calorie_surplus = math.sin(elapsed * 0.015) * 200 + random.uniform(-20, 20)
    protein_intake = 55 + math.sin(elapsed * 0.04) * 25 + random.uniform(-3, 3)
    glucose_level = 100 + math.sin(elapsed * 0.025) * 35 + random.uniform(-5, 5)

    # ── Overall health ───────────────────────────────────────
    overall_health = sum(
        twin.organs[o]["health"] * w
        for o, w in ORGAN_WEIGHTS.items()
        if o in twin.organs
    )

    # Map gut → intestine and stomach for the 3D view
    # (the Streamlit twin uses "gut", but the 3D frontend has stomach + intestine)
    if "gut" in organs_data:
        gut = organs_data["gut"]
        organs_data["intestine"] = {
            "health": gut["health"],
            "system": "Digestive",
            "function": "Nutrient absorption & microbiome",
            "riskFactors": gut.get("riskFactors", []),
            "metrics": gut["metrics"],
        }
        organs_data["stomach"] = {
            "health": gut["health"],
            "system": "Digestive",
            "function": "Food breakdown & gastric acid production",
            "riskFactors": ["Ulcers", "Gastritis", "GERD"],
            "metrics": {"pH_level": 2.5, "motility": 85},
        }

    # Add synthetic fat data from immune/skin (the Streamlit twin doesn't have fat as a separate organ)
    if "fat" not in organs_data:
        avg_health = overall_health / max(sum(ORGAN_WEIGHTS.values()), 1)
        organs_data["fat"] = {
            "health": round(avg_health, 4),
            "system": "Adipose",
            "function": "Energy storage & hormonal regulation",
            "riskFactors": ["Obesity", "Inflammation", "Insulin resistance"],
            "metrics": {"bmi_contribution": 24.5, "inflammation": 2.5},
        }

    return {
        "heart_rate": round(heart_rate, 1),
        "breathing_rate": round(breathing_rate, 1),
        "calorie_surplus": round(calorie_surplus, 1),
        "protein_intake": round(protein_intake, 1),
        "glucose_level": round(glucose_level, 1),
        "overall_health": round(overall_health, 4),
        "organs": organs_data,
    }
