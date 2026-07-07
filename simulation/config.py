# Configuration and constants

ORGAN_BASELINES = {
    "heart": {
        "blood_pressure": 120,
        "cardiac_output": 5.0,
        "oxygen_delivery": 95,
        "arterial_stiffness": 15
    },
    "lungs": {
        "oxygen_saturation": 98,
        "lung_capacity": 4.5,
        "airway_resistance": 2.1,
        "inflammation_markers": 1.2
    },
    "brain": {
        "cognitive_score": 92,
        "blood_flow": 750,
        "neurotransmitters": 88,
        "inflammation": 1.5
    },
    "kidneys": {
        "gfr": 95,
        "creatinine": 0.9,
        "electrolyte_balance": 92,
        "toxin_clearance": 88
    },
    "pancreas": {
        "insulin_sensitivity": 85,
        "beta_cell_function": 78,
        "enzyme_production": 90,
        "inflammation": 2.1
    },
    "liver": {
        "detox_rate": 88,
        "fat_content": 18,
        "enzyme_levels": 92,
        "inflammation": 1.8
    },
    "gut": {
        "microbiome_diversity": 65,
        "absorption_rate": 78,
        "barrier_integrity": 82,
        "inflammation": 2.3
    },
    "skin": {
        "hydration": 85,
        "elasticity": 75,
        "barrier_function": 80
    },
    "immune": {
        "immune_response": 78,
        "antibody_levels": 82,
        "inflammation_control": 75
    },
    "muscles": {
        "strength": 85,
        "endurance": 78,
        "recovery_rate": 72
    }
}

# Organ definitions with all properties
# -------------------------------------------------------
# SENSITIVITY SIGN CONVENTION:
#   Positive sensitivity  → the nutrient HARMS this organ (impact subtracts health)
#   Negative sensitivity  → the nutrient BENEFITS this organ (impact adds health)
#
# All sensitivity keys MUST match the nutrient keys supplied by the sidebar:
#   calories, carbs, protein, fat, sugar, fiber, sodium, calcium, iron
# -------------------------------------------------------
ORGAN_DEFINITIONS = {
    "heart": {
        "position": (0, 0, 1.0),
        "size": 0.40,
        "color": "#FF6B6B",
        "system": "Cardiovascular",
        "sensitivity": {
            "sodium": 0.8,       # High sodium → raises blood pressure → harms heart
            "fat": 0.6,          # Excess fat → atherosclerosis risk
            "fiber": -0.4,       # Fiber → lowers cholesterol → benefits heart
            "calories": 0.2,     # Excess calories → weight gain → cardiac strain
            "iron": -0.15        # Iron → oxygen transport → benefits heart
        },
        "function": "Blood circulation & oxygen transport",
        "risk_factors": ["Hypertension", "Atherosclerosis", "Arrhythmia"]
    },
    "lungs": {
        "position": (-0.5, 0.5, 0.8),
        "size": 0.25,
        "color": "#87CEEB",
        "system": "Respiratory",
        "sensitivity": {
            "sugar": 0.7,        # Excess sugar → systemic inflammation → harms lungs
            "iron": -0.3,        # Iron → hemoglobin → better oxygen transport
            "fiber": -0.2,       # Fiber → reduces inflammation
            "fat": 0.3,          # Excess fat → inflammation
            "calcium": -0.15     # Calcium → muscle contraction in airways
        },
        "function": "Gas exchange & oxygenation",
        "risk_factors": ["COPD", "Asthma", "Fibrosis"]
    },
    "brain": {
        "position": (0, 0.8, 1.1),
        "size": 0.18,
        "color": "#DDA0DD",
        "system": "Neurological",
        "sensitivity": {
            "sugar": 0.6,        # Excess sugar → neuroinflammation, energy crashes
            "fat": -0.4,         # Healthy fats → myelin, cell membranes → benefits brain
            "protein": -0.3,     # Protein → neurotransmitter synthesis
            "iron": -0.3,        # Iron → oxygen delivery to brain
            "calories": 0.15     # Excess calories → brain fog
        },
        "function": "Cognition, memory, coordination",
        "risk_factors": ["Neuroinflammation", "Cognitive decline", "Stroke"]
    },
    "kidneys": {
        "position": (0.6, -0.4, 0.6),
        "size": 0.12,
        "color": "#96CEB4",
        "system": "Renal",
        "sensitivity": {
            "sodium": 0.9,       # High sodium → kidney strain
            "protein": 0.4,      # Excess protein → extra nitrogen to filter
            "calcium": -0.2,     # Moderate calcium helps electrolyte balance
            "calories": 0.1,     # Excess calories → metabolic waste
            "fiber": -0.15       # Fiber → reduces toxin load
        },
        "function": "Filtration & waste removal",
        "risk_factors": ["CKD", "Stones", "Hypertension"]
    },
    "pancreas": {
        "position": (0.5, 0.2, 0.7),
        "size": 0.08,
        "color": "#45B7D1",
        "system": "Endocrine",
        "sensitivity": {
            "sugar": 0.9,        # Sugar → insulin demand → strains pancreas
            "fiber": -0.6,       # Fiber → slows sugar absorption → protects pancreas
            "carbs": 0.4,        # Excess carbs → blood sugar spikes
            "fat": 0.2,          # Excess fat → impairs insulin signaling
            "protein": -0.2      # Protein → slower digestion → less sugar spike
        },
        "function": "Blood sugar regulation & digestion",
        "risk_factors": ["Diabetes", "Pancreatitis", "Metabolic syndrome"]
    },
    "liver": {
        "position": (0.7, -0.3, 0.8),
        "size": 0.22,
        "color": "#4ECDC4",
        "system": "Metabolic",
        "sensitivity": {
            "sugar": 0.8,        # Excess sugar → fatty liver
            "fat": 0.5,          # Excess fat → hepatic steatosis
            "protein": -0.3,     # Protein → liver enzyme production, repair
            "iron": -0.2,        # Moderate iron → liver function
            "fiber": -0.3        # Fiber → reduces toxin load
        },
        "function": "Detoxification & metabolism",
        "risk_factors": ["Fatty liver", "Cirrhosis", "Hepatitis"]
    },
    "gut": {
        "position": (0, -0.5, 0.4),
        "size": 0.25,
        "color": "#FFEAA7",
        "system": "Digestive",
        "sensitivity": {
            "fiber": -0.7,       # Fiber → feeds microbiome → great for gut
            "sugar": 0.6,        # Excess sugar → dysbiosis, bad bacteria
            "protein": -0.2,     # Protein → supports gut lining
            "carbs": 0.2,        # Excess refined carbs → fermentation issues
            "calcium": -0.15     # Calcium → supports gut barrier integrity
        },
        "function": "Digestion & nutrient absorption",
        "risk_factors": ["IBD", "Leaky gut", "Dysbiosis"]
    },
    "skin": {
        "position": (0.3, -0.7, 0.3),
        "size": 0.15,
        "color": "#F4A460",
        "system": "Integumentary",
        "sensitivity": {
            "sugar": 0.5,        # Excess sugar → glycation → harms skin
            "fat": -0.3,         # Healthy fats → skin elasticity
            "iron": -0.2,        # Iron → skin cell regeneration
            "protein": -0.3,     # Protein → collagen production
            "calcium": -0.15     # Calcium → skin barrier function
        },
        "function": "Protection & temperature regulation",
        "risk_factors": ["Dehydration", "Sun damage", "Inflammation"],
        "metrics": {"hydration": 85, "elasticity": 75, "barrier_function": 80}
    },
    "immune": {
        "position": (-0.3, -0.7, 0.3),
        "size": 0.12,
        "color": "#9370DB",
        "system": "Immune",
        "sensitivity": {
            "sugar": 0.5,        # Excess sugar → suppresses immune response
            "protein": -0.4,     # Protein → antibody production
            "iron": -0.3,        # Iron → immune cell function
            "calcium": -0.2,     # Calcium → immune signaling
            "fiber": -0.2        # Fiber → gut-immune axis
        },
        "function": "Pathogen defense & immune regulation",
        "risk_factors": ["Autoimmunity", "Immunodeficiency", "Chronic inflammation"],
        "metrics": {"immune_response": 78, "antibody_levels": 82, "inflammation_control": 75}
    },
    "muscles": {
        "position": (0, 0.2, 0.2),
        "size": 0.18,
        "color": "#6495ED",
        "system": "Musculoskeletal",
        "sensitivity": {
            "protein": -0.6,     # Protein → muscle repair & growth
            "calories": -0.2,    # Calories → energy for muscle function
            "carbs": -0.2,       # Carbs → glycogen for muscle energy
            "iron": -0.3,        # Iron → oxygen to muscles
            "calcium": -0.2      # Calcium → muscle contraction
        },
        "function": "Movement & metabolism",
        "risk_factors": ["Atrophy", "Fatigue", "Injury"],
        "metrics": {"strength": 85, "endurance": 78, "recovery_rate": 72}
    }
}

# Additional configuration
DEFAULT_NUTRIENTS = {
    'calories': 300.0,
    'carbs': 45.0,
    'protein': 20.0,
    'fat': 12.0,
    'sugar': 8.0,
    'fiber': 6.0,
    'sodium': 500.0,
    'calcium': 200.0,
    'iron': 3.0
}

# DQN Agent configuration
DQN_CONFIG = {
    "state_size": 23,
    "action_size": 8,
    "gamma": 0.95,
    "epsilon": 0.3,
    "epsilon_decay": 0.995,
    "epsilon_min": 0.05,
    "memory_size": 2000,
    "batch_size": 32,
    "learning_rate": 0.001,
    "target_update_freq": 10
}

# Organ health weights for overall health calculation
ORGAN_WEIGHTS = {
    "heart": 0.15,
    "brain": 0.15,
    "lungs": 0.12,
    "liver": 0.12,
    "kidneys": 0.10,
    "pancreas": 0.10,
    "gut": 0.10,
    "skin": 0.06,
    "immune": 0.10,
    "muscles": 0.10
}