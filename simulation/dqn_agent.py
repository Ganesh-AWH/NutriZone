import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import numpy as np
from datetime import datetime
from simulation.config import DQN_CONFIG

class DQNOrganOptimizer:
    """DQN agent that learns to optimize organ health"""
    
    def __init__(self, state_size=None, action_size=None):
        self.config = DQN_CONFIG
        self.state_size = state_size or self.config["state_size"]
        self.action_size = action_size or self.config["action_size"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Main network and target network for stable training
        self.model = self._build_network()
        self.target_model = self._build_network()
        self.target_model.load_state_dict(self.model.state_dict())
        self.update_target_counter = 0
        
        # RL parameters
        self.gamma = self.config["gamma"]
        self.epsilon = self.config["epsilon"]
        self.epsilon_decay = self.config["epsilon_decay"]
        self.epsilon_min = self.config["epsilon_min"]
        self.memory = deque(maxlen=self.config["memory_size"])
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.config["learning_rate"])
        self.criterion = nn.MSELoss()
        self.batch_size = self.config["batch_size"]
        self.target_update_freq = self.config["target_update_freq"]
        
        # Action definitions with nutrient modifications
        self.actions = self._define_actions()
        self.action_effects = self._define_action_effects()
        
        self.decision_log = []
        self.training_losses = []
        
    def _build_network(self):
        """Build neural network"""
        return nn.Sequential(
            nn.Linear(self.state_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_size)
        ).to(self.device)
    
    def _define_actions(self):
        """Define available actions"""
        return [
            "Increase Protein & Repair",
            "Reduce Sugar & Inflammation",
            "Boost Fiber & Gut Health",
            "Lower Sodium & Blood Pressure",
            "Balance Carbs & Energy",
            "Add Healthy Fats",
            "Improve Hydration",
            "Maintain Current Pattern"
        ]
    
    def _define_action_effects(self):
        """Define how actions modify nutrients"""
        return {
            0: {"protein": 1.2, "calories": 1.05},
            1: {"sugar": 0.8, "carbs": 0.9},
            2: {"fiber": 1.3, "carbs": 1.05},
            3: {"sodium": 0.7},
            4: {"carbs": 0.9, "protein": 1.1, "fat": 1.1},
            5: {"fat": 1.2, "calories": 1.05},
            6: {"calories": 0.95},
            7: {}
        }
    
    def get_state(self, organ_twin, nutrients):
        """Get state representation"""
        # Define canonical order
        ORGAN_ORDER = [
            "heart", "lungs", "brain", "kidneys", "pancreas",
            "liver", "gut", "skin", "immune", "muscles"
        ]
        
        # Organ health (10 values for 10 organs) - in FIXED order
        organ_health = []
        for organ_name in ORGAN_ORDER:
            if organ_name in organ_twin.organs:
                organ_health.append(organ_twin.organs[organ_name]["health"])
            else:
                organ_health.append(0.5)  # Default if organ missing
        
        # Nutrient ratios (9 values)
        nutrient_features = [
            nutrients.get('calories', 0) / 1000,
            nutrients.get('carbs', 0) / 200,
            nutrients.get('protein', 0) / 100,
            nutrients.get('fat', 0) / 100,
            nutrients.get('sugar', 0) / 100,
            nutrients.get('fiber', 0) / 50,
            nutrients.get('sodium', 0) / 5000,
            nutrients.get('calcium', 0) / 2000,
            nutrients.get('iron', 0) / 50
        ]
        
        # Health metrics (4 values)
        organ_health_array = np.array(organ_health)
        health_metrics = [
            organ_twin.get_overall_health(),
            len([h for h in organ_health if h < 0.6]) / len(organ_health),
            np.std(organ_health_array) if len(organ_health_array) > 1 else 0.1,
            min(organ_health) if organ_health else 0.5
        ]
        
        # Combine: 10 + 9 + 4 = 23 features
        state_vector = organ_health + nutrient_features + health_metrics
        
        # Ensure correct size
        if len(state_vector) != self.state_size:
            # Adjust size
            if len(state_vector) < self.state_size:
                state_vector = state_vector + [0] * (self.state_size - len(state_vector))
            else:
                state_vector = state_vector[:self.state_size]
        
        return torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
    
    def select_action(self, state, explore=True):
        """Select action with epsilon-greedy"""
        if state.shape[1] != self.state_size:
            # Reshape state
            if state.shape[1] < self.state_size:
                padding = torch.zeros(1, self.state_size - state.shape[1], device=self.device)
                state = torch.cat([state, padding], dim=1)
            else:
                state = state[:, :self.state_size]
        
        q_val = None  # Initialize q_val
        
        if explore and random.random() < self.epsilon:
            action_idx = random.randint(0, self.action_size - 1)
        else:
            with torch.no_grad():
                q_values = self.model(state)
                action_idx = q_values.argmax().item()
                q_val = q_values[0][action_idx].item()
        
        # Log decision
        self.decision_log.append({
            "timestamp": datetime.now(),
            "action": self.actions[action_idx],
            "action_idx": action_idx,
            "epsilon": self.epsilon,
            "q_value": q_val
        })
        
        return action_idx
    
    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay memory"""
        # Store tensors, not numpy arrays
        self.memory.append((state, action, reward, next_state, done))
    
    def replay(self):
        """Train on batch from replay memory"""
        if len(self.memory) < self.batch_size:
            return 0
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors - states and next_states are already tensors
        states = torch.cat(states).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.cat(next_states).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)
        
        # Current Q values
        current_q = self.model(states).gather(1, actions)
        
        # Next Q values from target network
        with torch.no_grad():
            next_q = self.target_model(next_states).max(1)[0].unsqueeze(1)
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss
        loss = self.criterion(current_q, target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)  # Gradient clipping
        self.optimizer.step()
        
        # Update target network
        self.update_target_counter += 1
        if self.update_target_counter % self.target_update_freq == 0:
            self.target_model.load_state_dict(self.model.state_dict())
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        self.training_losses.append(loss.item())
        return loss.item()
    
    def apply_action_to_nutrients(self, action_idx, current_nutrients):
        """Apply action to modify nutrients for next meal"""
        effects = self.action_effects.get(action_idx, {})
        modified_nutrients = current_nutrients.copy()
        
        for nutrient, multiplier in effects.items():
            if nutrient in modified_nutrients:
                modified_nutrients[nutrient] *= multiplier
        
        return modified_nutrients
    
    def get_recommendation(self, action_idx, current_nutrients):
        """Get specific recommendation with nutrient changes"""
        effects = self.action_effects.get(action_idx, {})
        
        recommendations = {
            0: f" Increase protein to {current_nutrients.get('protein', 0) * 1.2:.1f}g for organ repair",
            1: f" Reduce sugar to {current_nutrients.get('sugar', 0) * 0.8:.1f}g to lower inflammation",
            2: f" Add fiber to {current_nutrients.get('fiber', 0) * 1.3:.1f}g for microbiome health",
            3: f" Lower sodium to {current_nutrients.get('sodium', 0) * 0.7:.1f}mg for blood pressure",
            4: f" Balance carbs ({current_nutrients.get('carbs', 0) * 0.9:.1f}g) with protein ({current_nutrients.get('protein', 0) * 1.1:.1f}g)",
            5: f" Add healthy fats to {current_nutrients.get('fat', 0) * 1.2:.1f}g (omega-3s)",
            6: f" Increase hydration, reduce calories to {current_nutrients.get('calories', 0) * 0.95:.1f}",
            7: f" Current nutrition pattern is effective"
        }
        return recommendations.get(action_idx, "No specific recommendation")