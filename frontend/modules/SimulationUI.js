/**
 * SimulationUI handles the left side panel for inputs
 * and the right side panel for AI insights, interacting with the new
 * /simulation endpoints on FastAPI.
 */

export class SimulationUI {
  constructor() {
    this.elements = {
      // Panel toggle
      toggleBtn: document.getElementById('toggle-feed-twin'),
      simPanel: document.getElementById('simulation-panel'),
      closeBtn: document.getElementById('sim-panel-close'),

      // Inputs
      mealName: document.getElementById('input-meal-name'),
      cal: document.getElementById('input-cal'),
      carbs: document.getElementById('input-carbs'),
      protein: document.getElementById('input-protein'),
      fat: document.getElementById('input-fat'),
      sugar: document.getElementById('input-sugar'),
      fiber: document.getElementById('input-fiber'),
      sodium: document.getElementById('input-sodium'),
      calcium: document.getElementById('input-calcium'),
      iron: document.getElementById('input-iron'),
      useOllama: document.getElementById('input-use-ollama'),
      autoApply: document.getElementById('input-auto-apply'),

      // Insights Display
      insightsBody: document.getElementById('insights-body'),

      // Buttons
      btnSimulate: document.getElementById('btn-simulate'),
      btnTrain: document.getElementById('btn-train'),
      btnReset: document.getElementById('btn-reset'),
    };

    this.bindEvents();
    this.loadInitialState();
  }

  bindEvents() {
    // Toggle Feed Twin side panel
    this.elements.toggleBtn.addEventListener('click', () => {
      this.elements.simPanel.classList.toggle('hidden');
    });
    this.elements.closeBtn.addEventListener('click', () => {
      this.elements.simPanel.classList.add('hidden');
    });

    // Actions
    this.elements.btnSimulate.addEventListener('click', () => this.simulateMeal());
    this.elements.btnTrain.addEventListener('click', () => this.trainAgent());
    this.elements.btnReset.addEventListener('click', () => this.resetSimulation());
  }

  async loadInitialState() {
    try {
      const resp = await fetch('/simulation/state');
      const data = await resp.json();
      this.renderInsights(data.explanations || [], data.meal_history || []);
    } catch (err) {
      console.error('Error loading simulation state:', err);
    }
  }

  getNutrients() {
    return {
      calories: parseFloat(this.elements.cal.value) || 0,
      carbs: parseFloat(this.elements.carbs.value) || 0,
      protein: parseFloat(this.elements.protein.value) || 0,
      fat: parseFloat(this.elements.fat.value) || 0,
      sugar: parseFloat(this.elements.sugar.value) || 0,
      fiber: parseFloat(this.elements.fiber.value) || 0,
      sodium: parseFloat(this.elements.sodium.value) || 0,
      calcium: parseFloat(this.elements.calcium.value) || 0,
      iron: parseFloat(this.elements.iron.value) || 0
    };
  }

  async simulateMeal() {
    const defaultBtnText = this.elements.btnSimulate.innerText;
    this.elements.btnSimulate.innerText = 'Simulating...';
    this.elements.btnSimulate.disabled = true;

    try {
      const payload = {
        nutrients: this.getNutrients(),
        meal_name: this.elements.mealName.value || 'Custom Meal',
        use_ollama: this.elements.useOllama.checked,
        show_explanations: true,
        auto_apply_ai: this.elements.autoApply.checked,
        use_llm_reward: true
      };

      const resp = await fetch('/simulation/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await resp.json();
      
      // Update Inputs if Auto Apply AI modified them
      if (data.changes && Object.keys(data.changes).length > 0) {
          console.log("AI Applied changes:", data.changes);
          if (data.meal_record && data.meal_record.nutrients) {
              const n = data.meal_record.nutrients;
              if(n.calories) this.elements.cal.value = n.calories.toFixed(1);
              if(n.carbs) this.elements.carbs.value = n.carbs.toFixed(1);
              if(n.protein) this.elements.protein.value = n.protein.toFixed(1);
              if(n.fat) this.elements.fat.value = n.fat.toFixed(1);
              if(n.sugar) this.elements.sugar.value = n.sugar.toFixed(1);
              // etc...
          }
      }

      // Reload State to get new insights
      await this.loadInitialState();
      
      // Log if new explanations arrived (user can view them on AI Insights page)
      if (data.new_explanations && data.new_explanations.length > 0) {
        console.log('New AI explanations available — switch to AI Insights page to view.');
      }
    } catch (err) {
      console.error('Error simulating meal:', err);
      alert('Simulation failed. Check console.');
    } finally {
      this.elements.btnSimulate.innerText = defaultBtnText;
      this.elements.btnSimulate.disabled = false;
    }
  }

  async trainAgent() {
    this.elements.btnTrain.innerText = 'Training...';
    try {
      const resp = await fetch('/simulation/train', { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'trained') {
        alert('Agent trained! Loss: ' + data.loss.toFixed(4));
        this.loadInitialState();
      } else {
        alert(data.message || 'Need more meal data to train agent.');
      }
    } catch(err) {
      console.error(err);
    } finally {
      this.elements.btnTrain.innerText = 'Train Agent';
    }
  }

  async resetSimulation() {
    const defaultBtnText = this.elements.btnReset.innerText;
    this.elements.btnReset.innerText = 'Resetting...';
    try {
      await fetch('/simulation/reset', { method: 'POST' });

      // Clear the UI input form fields so the user knows it worked
      this.elements.mealName.value = '';
      this.elements.cal.value = '';
      this.elements.carbs.value = '';
      this.elements.protein.value = '';
      this.elements.fat.value = '';
      this.elements.sugar.value = '';
      this.elements.fiber.value = '';
      this.elements.sodium.value = '';
      this.elements.calcium.value = '';
      this.elements.iron.value = '';

      // Reload the state (this pulls the empty history to clear AI Insights)
      await this.loadInitialState();
      
      // Briefly show Success on button, then restore
      this.elements.btnReset.innerText = 'Twin Reset!';
      setTimeout(() => {
        this.elements.btnReset.innerText = defaultBtnText;
      }, 2000);
      
      console.log('Digital Twin successfully reset.');
    } catch(err) {
      console.error('Failed to reset simulation:', err);
      this.elements.btnReset.innerText = 'Error resetting';
      setTimeout(() => {
        this.elements.btnReset.innerText = defaultBtnText;
      }, 2000);
    }
  }

  renderInsights(explanations, history) {
    if (explanations.length === 0 && history.length === 0) {
      this.elements.insightsBody.innerHTML = '<div class="placeholder">Simulate a meal to see AI insights.</div>';
      return;
    }

    let html = '';

    // Show last meal summary if available
    if (history.length > 0) {
      const lastMeal = history[history.length - 1];
      html += `
        <div class="insight-card">
          <h3>Latest Decision: ${lastMeal.meal}</h3>
          <p><strong>Action:</strong> ${lastMeal.action || 'Unknown'}</p>
          <p><strong>Recommendation:</strong> ${lastMeal.recommendation}</p>
          <div class="insight-metrics">
            <span class="insight-metric">Reward: ${lastMeal.reward.toFixed(3)}</span>
            <span class="insight-metric">Health Impact: ${(lastMeal.health_change > 0 ? '+' : '')}${lastMeal.health_change.toFixed(3)}</span>
          </div>
        </div>
      `;
    }

    const reversedExpl = [...explanations].reverse();
    for (const exp of reversedExpl) {
      const date = new Date(exp.timestamp).toLocaleTimeString();
      if (exp.type === 'agent_decision') {
        html += `
          <div class="insight-history-item agent">
            <h4>🤖 Agent Decision Logic</h4>
            <p>${exp.explanation}</p>
            <div class="insight-date">${date}</div>
          </div>
        `;
      } else if (exp.organ) {
        html += `
          <div class="insight-history-item">
            <h4>🧬 ${exp.organ.toUpperCase()} Response Analysis</h4>
            <p>${exp.explanation}</p>
            <div class="insight-date">${date}</div>
          </div>
        `;
      }
    }

    this.elements.insightsBody.innerHTML = html;
  }
}
