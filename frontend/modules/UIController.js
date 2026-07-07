/**
 * UIController — Manages all HTML overlay UI elements.
 * - Bottom HUD organ chips
 * - Side panel organ details
 * - Overall health display
 * - API status indicator
 */

import { OrganManager } from '/frontend/modules/OrganManager.js';

export class UIController {
  constructor(organManager, sceneManager) {
    this.organManager = organManager;
    this.sceneManager = sceneManager || null;
    this._selectedOrgan = null;
    this._currentBodyState = null;

    this._cacheDOM();
    this._buildHUD();
    this._bindEvents();
  }

  /* ─── Cache DOM refs ──────────────────────────── */
  _cacheDOM() {
    this.els = {
      hudContainer: document.getElementById('hud-organs'),
      panel: document.getElementById('organ-panel'),
      panelClose: document.getElementById('panel-close'),
      panelIcon: document.getElementById('panel-icon'),
      panelTitle: document.getElementById('panel-title'),
      panelSystem: document.getElementById('panel-system'),
      panelHealthPct: document.getElementById('panel-health-pct'),
      panelHealthBar: document.getElementById('panel-health-bar'),
      panelStatus: document.getElementById('panel-status'),
      panelFunction: document.getElementById('panel-function'),
      panelRisks: document.getElementById('panel-risks'),
      panelMetrics: document.getElementById('panel-metrics'),
      apiStatusDot: document.querySelector('#api-status .status-dot'),
      apiStatusLabel: document.querySelector('#api-status .status-label'),
      overallHealthValue: document.getElementById('overall-health-value'),
    };
  }

  /* ─── Build bottom HUD chips ──────────────────── */
  _buildHUD() {
    const registry = OrganManager.getRegistry();
    this.els.hudContainer.innerHTML = '';

    for (const [name, meta] of Object.entries(registry)) {
      const chip = document.createElement('div');
      chip.classList.add('hud-organ');
      chip.dataset.organ = name;
      chip.id = `hud-${name}`;
      chip.innerHTML = `
        <span class="hud-icon">${meta.icon}</span>
        <span class="hud-name">${name}</span>
        <span class="hud-health healthy" data-hud-health="${name}">80%</span>
      `;
      chip.addEventListener('click', () => this.selectOrgan(name));
      this.els.hudContainer.appendChild(chip);
    }
  }

  /* ─── Bind events ─────────────────────────────── */
  _bindEvents() {
    this.els.panelClose.addEventListener('click', () => this.closePanel());
  }

  /* ─── Select organ (show panel + focus camera) ── */
  selectOrgan(name, focusCamera = true) {
    const organ = this.organManager.getOrgan(name);
    if (!organ) return;

    const wasAlreadySelected = this._selectedOrgan === name;
    this._selectedOrgan = name;

    // Mark active HUD chip
    document.querySelectorAll('.hud-organ').forEach((el) => el.classList.remove('active'));
    const chip = document.getElementById(`hud-${name}`);
    if (chip) chip.classList.add('active');

    // Focus camera on organ (only on fresh click, not on data refresh)
    if (focusCamera && !wasAlreadySelected && this.sceneManager) {
      const pos = organ.group.position.clone();
      this.sceneManager.focusOn(pos, 3.0);
    }

    // Populate panel
    const meta = organ.meta;
    const health = organ.health || 0.8;
    const pct = Math.round(health * 100);
    const statusClass = health >= 0.8 ? 'healthy' : health >= 0.6 ? 'moderate' : 'risk';
    const statusLabel = health >= 0.8 ? 'Healthy' : health >= 0.6 ? 'Moderate' : 'At Risk';

    this.els.panelIcon.textContent = meta.icon;
    this.els.panelTitle.textContent = name.charAt(0).toUpperCase() + name.slice(1);
    this.els.panelSystem.textContent = meta.system + ' System';
    this.els.panelHealthPct.textContent = pct + '%';
    this.els.panelHealthBar.style.width = pct + '%';

    // Color the health bar based on status
    if (statusClass === 'healthy') {
      this.els.panelHealthBar.style.background = 'linear-gradient(90deg, #22c55e, #06b6d4)';
    } else if (statusClass === 'moderate') {
      this.els.panelHealthBar.style.background = 'linear-gradient(90deg, #f59e0b, #eab308)';
    } else {
      this.els.panelHealthBar.style.background = 'linear-gradient(90deg, #ef4444, #f97316)';
    }

    this.els.panelStatus.textContent = statusLabel;
    this.els.panelStatus.className = 'panel-status ' + statusClass;

    this.els.panelFunction.textContent = meta.function || '—';

    // Risk factors
    const risks = meta.riskFactors || [];
    this.els.panelRisks.innerHTML = risks.map(r => `<span class="risk-tag">${r}</span>`).join('');

    // Metrics
    const metrics = organ.metrics || {};
    this.els.panelMetrics.innerHTML = '';
    for (const [key, value] of Object.entries(metrics)) {
      const label = key.replace(/_/g, ' ');
      const display = typeof value === 'number' ? value.toFixed(1) : value;
      this.els.panelMetrics.innerHTML += `
        <div class="metric-card">
          <div class="metric-name">${label}</div>
          <div class="metric-value">${display}</div>
        </div>
      `;
    }

    // Show panel
    this.els.panel.classList.remove('hidden');
  }

  /* ─── Close panel ─────────────────────────────── */
  closePanel() {
    this.els.panel.classList.add('hidden');
    this._selectedOrgan = null;
    document.querySelectorAll('.hud-organ').forEach((el) => el.classList.remove('active'));

    // Reset camera to overview
    if (this.sceneManager) {
      this.sceneManager.resetCamera();
    }
  }

  /* ─── Update from body state ──────────────────── */
  updateFromBodyState(bodyState) {
    if (!bodyState) return;
    this._currentBodyState = bodyState;

    // Overall health
    const oh = bodyState.overall_health;
    if (oh !== undefined) {
      this.els.overallHealthValue.textContent = Math.round(oh * 100) + '%';
    }

    // Update HUD chips
    const organStates = bodyState.organs || {};
    for (const [name, data] of Object.entries(organStates)) {
      const healthEl = document.querySelector(`[data-hud-health="${name}"]`);
      if (!healthEl) continue;

      const health = data.health || 0.5;
      const pct = Math.round(health * 100);
      healthEl.textContent = pct + '%';

      // Update color class
      healthEl.classList.remove('healthy', 'moderate', 'risk');
      if (health >= 0.8) healthEl.classList.add('healthy');
      else if (health >= 0.6) healthEl.classList.add('moderate');
      else healthEl.classList.add('risk');
    }

    // If panel is open, refresh selected organ (without re-focusing camera)
    if (this._selectedOrgan && organStates[this._selectedOrgan]) {
      this.selectOrgan(this._selectedOrgan, false);
    }
  }

  /* ─── API status ──────────────────────────────── */
  setApiStatus(online) {
    this.els.apiStatusDot.classList.toggle('online', online);
    this.els.apiStatusDot.classList.toggle('offline', !online);
    this.els.apiStatusLabel.textContent = online ? 'Live' : 'Demo Mode';
  }

  /* ─── Accessor ────────────────────────────────── */
  getSelectedOrgan() {
    return this._selectedOrgan;
  }
}
