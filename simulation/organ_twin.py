import numpy as np
import random
from collections import deque
from datetime import datetime, timedelta
import plotly.graph_objects as go
from simulation.config import ORGAN_BASELINES, ORGAN_DEFINITIONS, ORGAN_WEIGHTS

ORGAN_ICONS = {
    "brain": "🧠",
    "gut": "🧬",
    "heart": "❤️",
    "immune": "🛡️",
    "kidneys": "🫘",
    "liver": "🟤",
    "lungs": "🫁",
    "muscles": "💪",
    "pancreas": "🟨",
    "skin": "🧴",
}

class OrganDigitalTwin:
    """Real-time digital twin of 10 vital organs"""
    
    def __init__(self):
        # Initialize organs with realistic physiology
        self.organs = {}
        self._previous_overall_health = 0.5
        self._initialize_organs()
        
        # Simulation state
        self.history = {organ: deque(maxlen=100) for organ in self.organs}
        self.current_time = datetime.now()
        self.nutrient_history = []
        self.intervention_history = []
    
    def _initialize_organs(self):
        """Initialize all organs with their properties"""
        for organ_name, props in ORGAN_DEFINITIONS.items():
            initial_health = 0.7 + (random.random() * 0.2)  # Start 70-90%
            self.organs[organ_name] = {
                "health": initial_health,
                **props
            }
            # Initialize metrics if not already defined
            if "metrics" not in self.organs[organ_name]:
                self.organs[organ_name]["metrics"] = ORGAN_BASELINES.get(organ_name, {}).copy()
            # Set initial color based on starting health
            self._update_organ_color(organ_name, initial_health)
    
    def simulate_meal_impact(self, nutrients, meal_name="Meal"):
        """Simulate the impact of a meal on all organs"""

        scale = 1.0  # Use exact nutrient input values without portion scaling
        impacts = {}
        organ_states_before = self.get_organ_states()
        self._previous_overall_health = self.get_overall_health()
        
        for organ_name, organ_data in self.organs.items():
            # Calculate organ-specific impact
            impact = self._calculate_organ_impact(organ_name, nutrients, scale)
            
            # Apply impact
            new_health = organ_data["health"] + impact
            
            # Apply bounds and recovery
            new_health = np.clip(new_health, 0.1, 1.0)
            new_health = min(1.0, new_health + 0.001)  # Natural recovery
            
            # Update organ
            organ_data["health"] = new_health
            
            # Update metrics
            self._update_organ_metrics(organ_name, new_health)
            
            # Update color
            self._update_organ_color(organ_name, new_health)
            
            # Record impact
            impacts[organ_name] = {
                "impact": impact,
                "new_health": new_health,
                "stress_level": abs(impact) * 100
            }
            
            # Record history
            self.history[organ_name].append({
                "timestamp": self.current_time,
                "health": new_health,
                "impact": impact,
                "meal": meal_name,
                "nutrients": nutrients.copy()
            })
        
        # Calculate reward for RL agent
        organ_states_after = self.get_organ_states()
        reward = self._calculate_reward(organ_states_before, organ_states_after)
        
        # Record nutrient history
        self.nutrient_history.append({
            "timestamp": self.current_time,
            "meal": meal_name,
            "nutrients": nutrients.copy(),
            "overall_impact": np.mean([impacts[o]["impact"] for o in impacts]),
            "organ_states": organ_states_before,
            "reward": reward,
            "overall_health_before": self._previous_overall_health,
            "overall_health_after": self.get_overall_health()
        })
        
        self.current_time += timedelta(hours=1)  # Advance simulation time
        
        return impacts, reward
    
    # Global scale factor to keep per-meal health changes realistic
    IMPACT_SCALE = 0.12

    def _calculate_organ_impact(self, organ_name, nutrients, scale):
        """Calculate organ-specific impact using deviation from reference.
        
        The impact is based on how far each nutrient is from a "reference"
        per-meal value (norm_value = 1.0).  Only excess or deficiency causes
        a change; a perfectly balanced meal has near-zero impact.
        
        Sign convention:
          - Positive sensitivity → nutrient HARMS when in EXCESS
          - Negative sensitivity → nutrient BENEFITS when in EXCESS
        
        Formula:  impact -= sensitivity × (norm_value − 1.0) × IMPACT_SCALE
        
        Examples with sodium sensitivity +0.8:
          400mg (norm 0.5, deviation -0.5) → -(0.8 × -0.5) × 0.12 = +0.048   (below ref → slight benefit)
          800mg (norm 1.0, deviation  0.0) → -(0.8 ×  0.0) × 0.12 =  0.000   (at ref → neutral)
         1800mg (norm 2.25, deviation +1.25)→ -(0.8 × +1.25)× 0.12 = -0.120  (excess → harms)
        """
        organ = self.organs[organ_name]
        impact = 0
        
        # Reference per-meal values — at these amounts the nutrient has zero impact
        NUTRIENT_REFS = {
            "calories": 500,     # Normal single meal calories
            "carbs":    60,      # Normal single meal carbs (g)
            "protein":  25,      # Normal single meal protein (g)
            "fat":      20,      # Normal single meal fat (g)
            "sugar":    10,      # Moderate single meal sugar (g)
            "fiber":     8,      # Good single meal fiber (g)
            "sodium":  600,      # Normal single meal sodium (mg)
            "calcium": 300,      # Normal single meal calcium (mg)
            "iron":      4,      # Normal single meal iron (mg)
        }
        
        for nutrient, sensitivity in organ["sensitivity"].items():
            if nutrient in nutrients:
                nutrient_value = nutrients[nutrient]
                ref = NUTRIENT_REFS.get(nutrient, 100)
                deviation = (nutrient_value / ref) - 1.0  # 0 at ref, +ve if excess, -ve if deficit
                
                # Negate so that:
                #   positive sensitivity + excess  → health DECREASES
                #   positive sensitivity + deficit → health INCREASES (less of bad thing)
                #   negative sensitivity + excess  → health INCREASES (more of good thing)
                #   negative sensitivity + deficit → health DECREASES (deficiency)
                impact -= sensitivity * deviation * scale
        
        # Apply global scale to keep per-meal changes in a realistic range
        impact *= self.IMPACT_SCALE
        
        # Small random noise for realism
        impact += random.uniform(-0.003, 0.003)
        return impact
    
    def _update_organ_metrics(self, organ_name, new_health):
        """Update organ metrics based on health"""
        organ = self.organs[organ_name]
        
        # Update metrics proportionally to health
        health_factor = 0.6 + (new_health * 0.4)  # Maps 0.1-1.0 to 0.64-1.0
        
        for metric in organ["metrics"]:
            # Use baseline values if available
            base_value = ORGAN_BASELINES.get(organ_name, {}).get(metric, 100)
            current_value = organ["metrics"][metric]
            
            # Move toward target value
            target_value = base_value * health_factor
            adjustment = (target_value - current_value) * 0.1
            
            # Apply bounds based on metric type
            if "pressure" in metric or "creatinine" in metric or "inflammation" in metric:
                organ["metrics"][metric] = np.clip(current_value + adjustment, 
                                                  base_value * 0.5, base_value * 1.5)
            else:
                organ["metrics"][metric] = np.clip(current_value + adjustment, 
                                                  base_value * 0.3, base_value * 1.2)
    
    def _calculate_reward(self, states_before, states_after):
        """Calculate reward for RL agent"""
        # Reward for overall health improvement
        health_before = sum(states_before.values()) / len(states_before)
        health_after = sum(states_after.values()) / len(states_after)
        health_reward = (health_after - health_before) * 50  # Increased from 10 to 50
        
        # Penalty for organs in critical condition
        critical_organs = sum(1 for health in states_after.values() if health < 0.6)
        critical_penalty = -critical_organs * 0.5
        
        # Reward for balanced health (low variance)
        health_variance = np.var(list(states_after.values()))
        balance_reward = -health_variance * 2
        
        # Reward for improving worst organ
        worst_organ_before = min(states_before.values()) if states_before else 0.5
        worst_organ_after = min(states_after.values()) if states_after else 0.5
        worst_organ_reward = (worst_organ_after - worst_organ_before) * 20  # Increased from 5 to 20
        
        total_reward = health_reward + critical_penalty + balance_reward + worst_organ_reward
        return total_reward
    
    def _update_organ_color(self, organ_name, health):
        """Update organ color based on health status.
        
        Color scale:
          ● Green  (≥ 0.80) → Healthy
          ● Yellow (0.60–0.79) → Moderate / Needs attention
          ● Red    (< 0.60) → At risk / Critical
        """
        organ = self.organs[organ_name]
        
        if health >= 0.80:
            # Bright green — healthy
            # Lerp from light-green (0.8) to vivid green (1.0)
            t = min((health - 0.8) / 0.2, 1.0)
            r = int(80 - t * 60)       # 80 → 20
            g = int(200 + t * 55)      # 200 → 255
            b = int(80 - t * 50)       # 80 → 30
            organ["color"] = f"rgb({r}, {g}, {b})"
        elif health >= 0.60:
            # Orange / yellow — moderate
            t = (health - 0.6) / 0.2   # 0 at 0.6, 1 at 0.8
            r = 255
            g = int(140 + t * 80)      # 140 (orange) → 220 (yellow)
            b = int(30 + t * 20)       # 30 → 50
            organ["color"] = f"rgb({r}, {g}, {b})"
        else:
            # Red — at risk / critical
            t = max(health - 0.1, 0) / 0.5  # 0 at 0.1, 1 at 0.6
            r = 255
            g = int(40 + t * 60)       # 40 (deep red) → 100 (lighter red)
            b = int(40 + t * 40)       # 40 → 80
            organ["color"] = f"rgb({r}, {g}, {b})"
    
    def apply_intervention(self, intervention_type, intensity=1.0):
        """Apply a health intervention"""
        impacts = {}
        
        for organ_name in self.organs:
            organ = self.organs[organ_name]
            base_health = organ["health"]
            
            # Calculate intervention impact
            if intervention_type == "exercise":
                impact = 0.02 * intensity if organ_name in ["heart", "lungs", "muscles"] else 0.01 * intensity
            elif intervention_type == "hydration":
                impact = 0.015 * intensity if organ_name in ["kidneys", "brain", "skin"] else 0.008 * intensity
            elif intervention_type == "sleep":
                impact = 0.025 * intensity if organ_name in ["brain", "immune"] else 0.01 * intensity
            elif intervention_type == "stress_reduction":
                impact = 0.03 * intensity if organ_name in ["brain", "heart", "gut"] else 0.015 * intensity
            else:
                impact = 0.01 * intensity
            
            # Apply impact
            new_health = np.clip(base_health + impact, 0.1, 1.0)
            organ["health"] = new_health
            
            # Update metrics and color
            self._update_organ_metrics(organ_name, new_health)
            self._update_organ_color(organ_name, new_health)
            
            impacts[organ_name] = {
                "impact": impact,
                "new_health": new_health
            }
        
        # Record intervention
        self.intervention_history.append({
            "timestamp": self.current_time,
            "intervention": intervention_type,
            "intensity": intensity,
            "impacts": impacts
        })
        
        return impacts
    
    def get_organ_states(self):
        """Get current organ states"""
        return {name: data["health"] for name, data in self.organs.items()}
    
    def get_overall_health(self):
        """Calculate overall health score"""
        total = 0
        for organ_name, weight in ORGAN_WEIGHTS.items():
            if organ_name in self.organs:
                total += self.organs[organ_name]["health"] * weight
        
        return total
    
    def get_overall_health_previous(self):
        """Get previous overall health for delta calculation"""
        return self._previous_overall_health
    
    def _health_status_label(self, health):
        """Return a status label for a given health value."""
        if health >= 0.80:
            return "Healthy"
        elif health >= 0.60:
            return "Moderate"
        else:
            return "At Risk"
    
    def create_3d_visualization(self):
        """Create 3D visualization of organs with color-coded health status"""
        fig = go.Figure()
        
        # Add organs
        for organ_name, organ_data in self.organs.items():
            x, y, z = organ_data["position"]
            size = organ_data["size"] * 35
            health = organ_data["health"]
            status = self._health_status_label(health)
            
            fig.add_trace(go.Scatter3d(
                x=[x],
                y=[y],
                z=[z],
                mode='text',
                text=[ORGAN_ICONS.get(organ_name, '⚕️')],
                textposition="middle center",
                textfont=dict(size=max(20, int(size)), color=organ_data["color"]),
                name=f"{organ_name.title()} ({health:.0%} {status})",
                hoverinfo='text',
                hovertext=f"""
                <b>{organ_name.title()}</b><br>
                Health: {health:.1%}<br>
                Status: {status}<br>
                System: {organ_data['system']}<br>
                Function: {organ_data.get('function', 'N/A')}
                """
            ))

            fig.add_trace(go.Scatter3d(
                x=[x],
                y=[y],
                z=[z],
                mode='text',
                text=[organ_name.title()],
                textposition="bottom center",
                textfont=dict(size=14, color="white"),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # ── Color legend as invisible scatter traces (appear in the legend) ──
        legend_items = [
            ("🟢 Healthy (≥ 80%)", "rgb(20, 255, 30)"),
            ("🟡 Moderate (60–79%)", "rgb(255, 200, 40)"),
            ("🔴 At Risk (< 60%)", "rgb(255, 50, 50)"),
        ]
        for label, color in legend_items:
            fig.add_trace(go.Scatter3d(
                x=[None], y=[None], z=[None],
                mode='markers',
                marker=dict(size=8, color=color),
                name=label,
                showlegend=True,
                hoverinfo='skip'
            ))
        
        # Add connections
        connections = [
            ("heart", "lungs"), ("heart", "brain"), ("liver", "pancreas"),
            ("gut", "liver"), ("kidneys", "heart")
        ]
        
        for org1, org2 in connections:
            if org1 in self.organs and org2 in self.organs:
                x1, y1, z1 = self.organs[org1]["position"]
                x2, y2, z2 = self.organs[org2]["position"]
                
                fig.add_trace(go.Scatter3d(
                    x=[x1, x2, None],
                    y=[y1, y2, None],
                    z=[z1, z2, None],
                    mode='lines',
                    line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
                    showlegend=False,
                    hoverinfo='skip'
                ))
        
        # Layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(visible=False, range=[-1, 1]),
                yaxis=dict(visible=False, range=[-1, 1]),
                zaxis=dict(visible=False, range=[0, 1.5]),
                bgcolor='rgba(10, 10, 20, 1)',
                camera=dict(eye=dict(x=1.8, y=1.8, z=1.2))
            ),
            paper_bgcolor='rgba(10, 10, 20, 1)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=500,
            legend=dict(
                title=dict(text="Health Status", font=dict(color="white", size=14)),
                font=dict(color="white", size=12),
                bgcolor='rgba(30, 30, 50, 0.85)',
                bordercolor='rgba(100, 100, 140, 0.5)',
                borderwidth=1,
                x=0.98,
                y=0.98,
                xanchor='right',
                yanchor='top',
                itemsizing='constant'
            )
        )
        
        return fig
