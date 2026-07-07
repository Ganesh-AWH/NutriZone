/**
 * DataService — Polls /body-state endpoint for real-time organ data.
 */

export class DataService {
  constructor(baseUrl, pollInterval = 3000) {
    this.baseUrl = baseUrl;
    this.pollInterval = pollInterval;
    this._timer = null;
    this._callbacks = [];
    this._statusCallbacks = [];
    this._online = false;
    this._lastState = null;
  }

  /* ─── Event subscriptions ─────────────────────── */
  onUpdate(cb) {
    this._callbacks.push(cb);
  }

  onStatusChange(cb) {
    this._statusCallbacks.push(cb);
  }

  /* ─── Start / stop polling ────────────────────── */
  start() {
    this._poll();  // initial immediate fetch
    this._timer = setInterval(() => this._poll(), this.pollInterval);
  }

  stop() {
    if (this._timer) clearInterval(this._timer);
  }

  /* ─── Single poll ─────────────────────────────── */
  async _poll() {
    try {
      const res = await fetch(`${this.baseUrl}/body-state`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      this._lastState = data;

      if (!this._online) {
        this._online = true;
        this._statusCallbacks.forEach(cb => cb(true));
      }

      this._callbacks.forEach(cb => cb(data));

    } catch (err) {
      // If server unreachable, use demo data
      if (this._online || !this._lastState) {
        this._online = false;
        this._statusCallbacks.forEach(cb => cb(false));
      }

      // Provide demo data when API is down
      if (!this._lastState) {
        const demoState = this._generateDemoState();
        this._callbacks.forEach(cb => cb(demoState));
      }
    }
  }

  /* ─── Demo data fallback ──────────────────────── */
  _generateDemoState() {
    const t = Date.now() / 1000;
    return {
      heart_rate: 72 + Math.sin(t * 0.1) * 8,
      breathing_rate: 15 + Math.sin(t * 0.07) * 3,
      calorie_surplus: Math.sin(t * 0.02) * 150,
      protein_intake: 50 + Math.sin(t * 0.05) * 20,
      glucose_level: 100 + Math.sin(t * 0.03) * 30,
      overall_health: 0.78,
      organs: {
        heart:     { health: 0.82 + Math.sin(t * 0.06) * 0.05, metrics: { blood_pressure: 118, cardiac_output: 5.1 } },
        lungs:     { health: 0.85 + Math.sin(t * 0.05) * 0.04, metrics: { oxygen_saturation: 97, lung_capacity: 4.4 } },
        liver:     { health: 0.75 + Math.sin(t * 0.04) * 0.06, metrics: { detox_rate: 86, fat_content: 19 } },
        kidneys:   { health: 0.80 + Math.sin(t * 0.07) * 0.04, metrics: { gfr: 93, creatinine: 0.95 } },
        pancreas:  { health: 0.70 + Math.sin(t * 0.08) * 0.05, metrics: { insulin_sensitivity: 82, beta_cell_function: 76 } },
        stomach:   { health: 0.78 + Math.sin(t * 0.03) * 0.04, metrics: { pH_level: 2.5, motility: 85 } },
        intestine: { health: 0.72 + Math.sin(t * 0.04) * 0.06, metrics: { microbiome_diversity: 63, absorption_rate: 76 } },
        muscles:   { health: 0.83 + Math.sin(t * 0.05) * 0.05, metrics: { strength: 84, endurance: 77 } },
        fat:       { health: 0.68 + Math.sin(t * 0.06) * 0.05, metrics: { bmi_contribution: 24.5, inflammation: 2.8 } },
      },
    };
  }
}
