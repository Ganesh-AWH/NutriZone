/**
 * NutriZone — 3D Digital Twin Visualization
 * ==========================================
 * Main application entry point.
 * Orchestrates scene, organ loading, animation, data fetching, and UI.
 */

import { SceneManager } from '/frontend/modules/SceneManager.js';
import { OrganManager } from '/frontend/modules/OrganManager.js';
import { AnimationController } from '/frontend/modules/AnimationController.js';
import { DataService } from '/frontend/modules/DataService.js';
import { UIController } from '/frontend/modules/UIController.js';
import { InteractionManager } from '/frontend/modules/InteractionManager.js';
import { SimulationUI } from '/frontend/modules/SimulationUI.js';
import { MealPlannerUI } from '/frontend/modules/MealPlannerUI.js';
import { ConnectionManager } from '/frontend/modules/ConnectionManager.js';

// ─── Config ────────────────────────────────────────────────────
const CONFIG = {
  apiBaseUrl: window.location.origin,       // FastAPI serves both static + API
  apiPollInterval: 3000,                    // ms between /body-state polls
  organModelBasePath: '/organs/',             // served by FastAPI static mount
};

// ─── Bootstrap ─────────────────────────────────────────────────
class NutriZoneApp {
  constructor() {
    this.sceneManager = null;
    this.organManager = null;
    this.animationController = null;
    this.dataService = null;
    this.uiController = null;
    this.interactionManager = null;
    this.simulationUI = null;
    this.mealPlannerUI = null;
    this.connectionManager = null;
    this.running = false;
  }

  async init() {
    try {
      this._setLoadingStatus('Creating scene…');

      // 1. Scene (renderer, camera, lights, env)
      const canvas = document.getElementById('three-canvas');
      this.sceneManager = new SceneManager(canvas);

      this._setLoadingStatus('Loading organ models…');

      // 2. Organs
      this.organManager = new OrganManager(this.sceneManager.scene, CONFIG.organModelBasePath);
      await this.organManager.loadAll((loaded, total) => {
        this._setLoadingStatus(`Loading organs… ${loaded}/${total}`);
      });

      // 2.5 Visual connections between organs
      this.connectionManager = new ConnectionManager(this.sceneManager, this.organManager);
      this.connectionManager.buildConnections();

      // 3. Animation controller (drives organ animations per body-state data)
      this.animationController = new AnimationController(this.organManager);

      // 4. Data service (polls /body-state)
      this.dataService = new DataService(CONFIG.apiBaseUrl, CONFIG.apiPollInterval);

      // 5. UI controller (panels, HUD)
      this.uiController = new UIController(this.organManager, this.sceneManager);

      // 6. Interaction (raycasting, hover, click)
      this.interactionManager = new InteractionManager(
        this.sceneManager,
        this.organManager,
        this.uiController
      );

      // 7. Simulation UI (Side panels: Feed Twin, AI Insights)
      this.simulationUI = new SimulationUI();

      // 8. Meal Planner UI (Modal overlay)
      this.mealPlannerUI = new MealPlannerUI();

      this._setupNavigation();

      // Default to Meal Planner on startup
      this.switchTab('nav-meal-planner');

      // Wire up data updates
      this.dataService.onUpdate((bodyState) => {
        this.animationController.applyBodyState(bodyState);
        this.uiController.updateFromBodyState(bodyState);
      });

      this.dataService.onStatusChange((online) => {
        this.uiController.setApiStatus(online);
      });

      // Start data polling
      this.dataService.start();

      // Start render loop
      this.running = true;
      this._animate();

      // Hide loader
      setTimeout(() => {
        document.getElementById('loading-overlay').classList.add('fade-out');
      }, 600);

    } catch (err) {
      console.error('[NutriZone] Init failed:', err);
      this._setLoadingStatus(`Error: ${err.message}`);
    }
  }

  _animate() {
    if (!this.running) return;
    requestAnimationFrame(() => this._animate());

    const delta = this.sceneManager.clock.getDelta();
    const elapsed = this.sceneManager.clock.getElapsedTime();

    // Update animations
    this.animationController.update(delta, elapsed);

    // Update interaction highlights
    this.interactionManager.update();

    // Update connection animations
    if (this.connectionManager) {
      this.connectionManager.update(delta, elapsed);
    }

    // Render
    this.sceneManager.render();
  }

  _setLoadingStatus(text) {
    const el = document.getElementById('loading-status');
    if (el) el.textContent = text;
  }

  // ─── Tab Navigation Logic ──────────────────────────────────────────────────
  _setupNavigation() {
    const navButtons = document.querySelectorAll('.header-btn');
    const pages = document.querySelectorAll('.page-view');
    const threeCanvas = document.getElementById('three-canvas');
    const bottomHud = document.getElementById('bottom-hud');
    const legend = document.getElementById('legend');
    const organPanel = document.getElementById('organ-panel');
    const feedTwinToggle = document.getElementById('toggle-feed-twin');
    const simPanel = document.getElementById('simulation-panel');

    const switchTab = (targetId) => {
      // Remove active state
      navButtons.forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(targetId);
      if (activeBtn) activeBtn.classList.add('active');

      // Hide all pages
      pages.forEach(p => p.classList.add('hidden'));

      // Always close Feed Twin side panel on page switch
      if (simPanel) simPanel.classList.add('hidden');

      if (targetId === 'nav-3d-twin') {
        // Show 3D scene + Feed Twin toggle
        threeCanvas.style.display = 'block';
        bottomHud.style.display = 'block';
        legend.style.display = 'block';
        feedTwinToggle.style.display = 'flex';
      } else {
        // Hide 3D scene elements
        threeCanvas.style.display = 'none';
        bottomHud.style.display = 'none';
        legend.style.display = 'none';
        feedTwinToggle.style.display = 'none';
        if (organPanel) organPanel.classList.add('hidden');

        if (targetId === 'nav-meal-planner') {
          document.getElementById('page-meal-planner').classList.remove('hidden');
        } else if (targetId === 'nav-insights') {
          document.getElementById('page-insights').classList.remove('hidden');
        }
      }
    };

    navButtons.forEach(btn => {
      btn.addEventListener('click', (e) => switchTab(e.currentTarget.id));
    });

    // Provide this to NutriZoneApp instance so we can call it from init
    this.switchTab = switchTab;
  }
}

// ─── Start ─────────────────────────────────────────────────────
const app = new NutriZoneApp();
app.init();
