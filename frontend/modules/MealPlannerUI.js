/**
 * MealPlannerUI handles the Nutrition AI Meal Planner modal,
 * interacting with the /plan/day and /plan/week endpoints.
 */

export class MealPlannerUI {
  constructor() {
    this.elements = {
      // Actions & Outputs
      btnGenDay: document.getElementById('btn-gen-day'),
      btnGenWeek: document.getElementById('btn-gen-week'),
      resultsDiv: document.getElementById('meal-results'),

      // Inputs
      age: document.getElementById('mp-age'),
      gender: document.getElementById('mp-gender'),
      height: document.getElementById('mp-height'),
      weight: document.getElementById('mp-weight'),
      activity: document.getElementById('mp-activity'),
      goal: document.getElementById('mp-goal'),
      bp: document.getElementById('mp-bp'),
      sugar: document.getElementById('mp-sugar'),
      pcos: document.getElementById('mp-pcos'),
      thyroid: document.getElementById('mp-thyroid'),
      digestive: document.getElementById('mp-digestive'),
    };

    this.bindEvents();
  }

  bindEvents() {
    this.elements.btnGenDay.addEventListener('click', () => this.generatePlan('day'));
    this.elements.btnGenWeek.addEventListener('click', () => this.generatePlan('week'));
  }

  getPayload() {
    const payload = {
      age: parseInt(this.elements.age.value) || 30,
      gender: this.elements.gender.value.toLowerCase(),
      height: parseFloat(this.elements.height.value) || 162.0,
      weight: parseFloat(this.elements.weight.value) || 68.0,
      activity_level: this.elements.activity.value,
      goal: this.elements.goal.value,
    };

    if (this.elements.bp.checked) payload.blood_pressure = 'high';
    if (this.elements.sugar.checked) payload.blood_sugar = 'high';
    if (this.elements.pcos.checked) payload.pcos = true;
    if (this.elements.thyroid.checked) payload.thyroid = true;
    if (this.elements.digestive.checked) payload.digestive_issues = 'ibs';

    return payload;
  }

  async generatePlan(type) {
    const btn = type === 'day' ? this.elements.btnGenDay : this.elements.btnGenWeek;
    const defaultText = btn.innerText;
    
    btn.innerText = 'Generating...';
    btn.disabled = true;
    this.elements.resultsDiv.innerHTML = '<div class="placeholder">🤖 AI is crafting your personalized plan. This may take a minute...</div>';

    try {
      const resp = await fetch(`/plan/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.getPayload())
      });

      if (!resp.ok) {
        throw new Error('API Error');
      }

      const data = await resp.json();
      this.renderPlan(type, data);

    } catch (err) {
      console.error(err);
      this.elements.resultsDiv.innerHTML = '<div class="placeholder" style="color: #ef4444;">Error generating plan. Please try again.</div>';
    } finally {
      btn.innerText = defaultText;
      btn.disabled = false;
    }
  }

  renderPlan(type, data) {
    let html = '';

    if (type === 'day') {
      html += `<h3>Today's Nutrition Plan</h3>`;
      const plan = data.plan || {};
      
      const meals = ['breakfast', 'lunch', 'dinner'];
      meals.forEach(meal => {
        if (plan[meal]) {
          html += this.renderMealCard(meal.toUpperCase(), plan[meal]);
        }
      });

      const totals = plan.totals || {};
      html += `
        <div class="meal-card" style="border-left-color: #22c55e">
          <h4>📊 Daily Totals</h4>
          <div class="meal-metrics">
            <span>🔥 ${totals.calories || 0} kcal</span>
            <span>🥩 ${totals.protein || 0}g Prot</span>
            <span>🍞 ${totals.carbs || 0}g Carb</span>
            <span>🥑 ${totals.fats || 0}g Fat</span>
            <span>🌱 ${totals.fibre || 0}g Fiber</span>
          </div>
        </div>
      `;

      if (data.explanation) {
         html += `
          <div class="meal-card" style="border-left-color: #f59e0b">
            <h4>💡 AI Explanation</h4>
            <p>${data.explanation}</p>
          </div>`;
      }

      // Add feedback form
      html += this.renderFeedbackForm();
      this.elements.resultsDiv.innerHTML = html;
      this.bindFeedbackEvents(plan);

    } else if (type === 'week') {
      html += `<h3>Weekly Nutrition Plan</h3>`;
      const weekPlan = data.week_plan || {};
      
      for (let i = 1; i <= 7; i++) {
        const dayKey = `day_${i}`;
        if (weekPlan[dayKey]) {
           html += `<h4 style="color: var(--accent-primary); margin-top: 20px;">DAY ${i}</h4>`;
           const meals = ['breakfast', 'lunch', 'dinner'];
           meals.forEach(meal => {
             if (weekPlan[dayKey][meal]) {
               html += this.renderMealCard(meal.toUpperCase(), weekPlan[dayKey][meal]);
             }
           });
        }
      }
      this.elements.resultsDiv.innerHTML = html;
    }
  }

  renderFeedbackForm() {
    return `
      <div class="feedback-section">
        <h3>Track your meals</h3>
        <p class="caption">Did you eat each meal? This helps the next plan adapt.</p>
        
        <div class="feedback-grid">
          <div class="feedback-col">
            <label>Breakfast</label>
            <div class="radio-group">
              <label><input type="radio" name="track_breakfast" value="eaten" checked> Eaten</label>
              <label><input type="radio" name="track_breakfast" value="skipped"> Skipped</label>
            </div>
          </div>
          <div class="feedback-col">
            <label>Lunch</label>
            <div class="radio-group">
              <label><input type="radio" name="track_lunch" value="eaten" checked> Eaten</label>
              <label><input type="radio" name="track_lunch" value="skipped"> Skipped</label>
            </div>
          </div>
          <div class="feedback-col">
            <label>Dinner</label>
            <div class="radio-group">
              <label><input type="radio" name="track_dinner" value="eaten" checked> Eaten</label>
              <label><input type="radio" name="track_dinner" value="skipped"> Skipped</label>
            </div>
          </div>
        </div>

        <h3>How did you feel?</h3>
        <p class="caption">Optional: help personalize the next plan.</p>
        
        <div class="slider-grid">
          <div class="input-group">
            <label>Hunger (1-10)</label>
            <input type="range" id="fb-hunger" min="1" max="10" value="5">
          </div>
          <div class="input-group">
            <label>Energy (1-10)</label>
            <input type="range" id="fb-energy" min="1" max="10" value="6">
          </div>
          <div class="input-group">
            <label>Weight change (kg)</label>
            <input type="number" id="fb-weight" step="0.1" value="0.0">
          </div>
        </div>

        <div class="input-group">
          <label>Suggestions (optional)</label>
          <input type="text" id="fb-suggestions" placeholder="e.g. lighter lunch, more protein">
        </div>

        <button class="primary-btn" id="btn-gen-feedback">Generate next plan (with feedback)</button>
      </div>
    `;
  }

  bindFeedbackEvents(lastPlan) {
    const btnFeedback = document.getElementById('btn-gen-feedback');
    if (!btnFeedback) return;

    btnFeedback.addEventListener('click', async () => {
      const defaultText = btnFeedback.innerText;
      btnFeedback.innerText = 'Generating...';
      btnFeedback.disabled = true;

      const trackBreakfast = document.querySelector('input[name="track_breakfast"]:checked').value;
      const trackLunch = document.querySelector('input[name="track_lunch"]:checked').value;
      const trackDinner = document.querySelector('input[name="track_dinner"]:checked').value;

      const feedbackPayload = {
        user_input: this.getPayload(),
        feedback: {
          yesterday_plan: lastPlan,
          hunger: parseInt(document.getElementById('fb-hunger').value) || 5,
          energy: parseInt(document.getElementById('fb-energy').value) || 6,
          weight_change: parseFloat(document.getElementById('fb-weight').value) || 0.0,
          meal_feedback: {
            breakfast: trackBreakfast,
            lunch: trackLunch,
            dinner: trackDinner
          },
          suggestions: document.getElementById('fb-suggestions').value.trim() || null
        }
      };

      try {
        const resp = await fetch('/plan/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(feedbackPayload)
        });

        if (!resp.ok) throw new Error('API Error');

        const data = await resp.json();
        this.renderPlan('day', data);

      } catch (err) {
        console.error(err);
        alert('Error generating feedback plan.');
      } finally {
        if (btnFeedback) {
          btnFeedback.innerText = defaultText;
          btnFeedback.disabled = false;
        }
      }
    });
  }

  renderMealCard(mealLabel, mealData) {
    const name = mealData.dish_name || '—';
    const cals = mealData.calories || 0;
    const p = mealData.protein || 0;
    const c = mealData.carbs || 0;
    const f = mealData.fats || 0;
    const fibre = mealData.fibre || 0;

    return `
      <div class="meal-card">
        <h4>${mealLabel} : ${name}</h4>
        <div class="meal-metrics">
          <span>🔥 ${cals} kcal</span>
          <span>🥩 ${p}g Prot</span>
          <span>🍞 ${c}g Carb</span>
          <span>🥑 ${f}g Fat</span>
          <span>🌱 ${fibre}g Fiber</span>
        </div>
      </div>
    `;
  }
}
