/**
 * AnimationController — Drives organ animations based on body-state data.
 *
 * Animation mapping:
 *   Heart     → pulsing scale  (heart_rate)
 *   Lungs     → breathing expansion (breathing_rate)
 *   Fat       → scale change (calorie_surplus)
 *   Muscles   → growth (protein_intake)
 *   Liver     → emissive intensity (glucose_level)
 *   Pancreas  → emissive intensity (glucose_level)
 */

import * as THREE from 'three';

export class AnimationController {
  constructor(organManager) {
    this.organManager = organManager;

    // Current body state snapshot (from API)
    this.bodyState = {
      heart_rate: 72,
      breathing_rate: 15,
      calorie_surplus: 0,
      protein_intake: 50,
      glucose_level: 100,
      organs: {},
    };

    // Lerp targets (for smooth transitions)
    this._targetScales = {};
    this._targetEmissive = {};
  }

  /* ─── Apply body state from API ───────────────── */
  applyBodyState(state) {
    if (!state) return;
    this.bodyState = { ...this.bodyState, ...state };
  }

  /* ─── Per-frame update ────────────────────────── */
  update(delta, elapsed) {
    this._animateHeart(delta, elapsed);
    this._animateLungs(delta, elapsed);
    this._animateFat(delta);
    this._animateMuscles(delta);
    this._animateLiverPancreas(delta);
    this._updateMixers(delta);
    this._updateHealthColors(delta);
    this._idleFloat(elapsed);
  }

  /* ─── Heart: Pulse ────────────────────────────── */
  _animateHeart(delta, elapsed) {
    const organ = this.organManager.getOrgan('heart');
    if (!organ) return;

    // Map heart_rate (40–180 BPM) to pulse speed
    const hr = Math.max(40, Math.min(this.bodyState.heart_rate || 72, 180));
    const pulseFreq = hr / 60;  // beats per second
    const pulseAmp = 0.06 + (hr - 60) / 600;  // subtle scaling amplitude

    const pulse = 1 + Math.sin(elapsed * pulseFreq * Math.PI * 2) * pulseAmp;
    const s = organ.baseScale * pulse;
    organ.group.scale.set(s, s, s);
  }

  /* ─── Lungs: Breathing ────────────────────────── */
  _animateLungs(delta, elapsed) {
    const organ = this.organManager.getOrgan('lungs');
    if (!organ) return;

    const br = Math.max(8, Math.min(this.bodyState.breathing_rate || 15, 30));
    const breathFreq = br / 60;  // breaths per second
    const breathAmp = 0.04 + (br - 12) / 400;

    const breathPhase = Math.sin(elapsed * breathFreq * Math.PI * 2);
    const sx = organ.baseScale * (1 + breathPhase * breathAmp * 1.3); // wider
    const sy = organ.baseScale * (1 + breathPhase * breathAmp * 0.6);
    const sz = organ.baseScale * (1 + breathPhase * breathAmp * 1.0);

    organ.group.scale.set(sx, sy, sz);
  }

  /* ─── Fat: Scale based on calorie surplus ──────── */
  _animateFat(delta) {
    const organ = this.organManager.getOrgan('fat');
    if (!organ) return;

    // calorie_surplus: negative = deficit, positive = surplus
    const surplus = this.bodyState.calorie_surplus || 0;
    // Map surplus [-500, +500] → scale [0.85, 1.15] of baseScale
    const factor = 1 + Math.max(-0.15, Math.min(surplus / 3333, 0.15));
    const target = organ.baseScale * factor;

    // Smooth lerp
    const current = organ.group.scale.x;
    const lerped = THREE.MathUtils.lerp(current, target, delta * 1.5);
    organ.group.scale.setScalar(lerped);
  }

  /* ─── Muscles: Growth based on protein intake ──── */
  _animateMuscles(delta) {
    const organ = this.organManager.getOrgan('muscles');
    if (!organ) return;

    const protein = this.bodyState.protein_intake || 50;
    // Map protein [0, 150] → scale [0.9, 1.12]
    const factor = 0.9 + Math.min(protein / 150, 1) * 0.22;
    const target = organ.baseScale * factor;

    const current = organ.group.scale.x;
    const lerped = THREE.MathUtils.lerp(current, target, delta * 1.5);
    organ.group.scale.setScalar(lerped);
  }

  /* ─── Liver & Pancreas: Emissive glow from glucose ── */
  _animateLiverPancreas(delta) {
    const glucose = this.bodyState.glucose_level || 100;

    // Map glucose [70, 200] → intensity [0.0, 0.8]
    const intensity = Math.max(0, Math.min((glucose - 70) / 163, 1)) * 0.8;

    for (const name of ['liver', 'pancreas']) {
      const organ = this.organManager.getOrgan(name);
      if (!organ) continue;

      // Apply emissive to all meshes
      organ.meshes.forEach((mesh) => {
        if (mesh.material && mesh.material.emissive) {
          // High glucose ⇒ warm red emissive; normal ⇒ cool blue/green
          const hue = intensity > 0.4
            ? new THREE.Color(0.8, 0.2, 0.05)  // warm
            : new THREE.Color(0.05, 0.3, 0.6);  // cool
          mesh.material.emissiveIntensity = THREE.MathUtils.lerp(
            mesh.material.emissiveIntensity || 0,
            intensity,
            delta * 2
          );
          mesh.material.emissive.lerp(hue, delta * 2);
        }
      });
    }
  }

  /* ─── Update GLTF animation mixers ────────────── */
  _updateMixers(delta) {
    for (const [, organ] of this.organManager.getAllOrgans()) {
      if (organ.mixer) {
        organ.mixer.update(delta);
      }
    }
  }

  /* ─── Update mesh colors based on health ──────── */
  _updateHealthColors(delta) {
    const organStates = this.bodyState.organs || {};

    const colorModerate = new THREE.Color(0xFFA500); // Orange/warning tint
    const colorAtRisk = new THREE.Color(0xFF3333); // Red/danger tint

    for (const [name, organ] of this.organManager.getAllOrgans()) {
      const stateData = organStates[name];
      if (!stateData) continue;

      const health = stateData.health !== undefined ? stateData.health : (organ.health || 1.0);
      organ.health = health;
      organ.metrics = stateData.metrics || organ.metrics;

      // Determine the target tint entirely based on health score
      let targetColor = null;
      let mixFactor = 0.0;

      if (health < 0.6) {
        // At Risk: High red tint
        targetColor = colorAtRisk;
        mixFactor = 0.6;
      } else if (health < 0.8) {
        // Moderate: Orange tint
        targetColor = colorModerate;
        mixFactor = 0.35;
      } else {
        // Healthy: No tint
        mixFactor = 0.0;
      }

      // Apply diffuse color tint gracefully (keeps hover logic cleanly isolated in emissive)
      organ.meshes.forEach((mesh) => {
        if (mesh.material && mesh.userData.originalMaterial) {
          const origColor = mesh.userData.originalMaterial.color;
          if (origColor) {
            const desiredColor = origColor.clone();
            if (targetColor && mixFactor > 0) {
              desiredColor.lerp(targetColor, mixFactor);
            }
            // Animate transition over time
            mesh.material.color.lerp(desiredColor, delta * 3.0);
          }
        }
      });
    }
  }

  /* ─── Idle floating for atmosphere ────────────── */
  _idleFloat(elapsed) {
    const root = this.organManager.rootGroup;
    if (root) {
      root.position.y = Math.sin(elapsed * 0.3) * 0.05;
    }
  }
}
