/**
 * InteractionManager — Raycasting for hover / click on organs.
 * Highlights hovered organ, opens detail panel on click.
 */

import * as THREE from 'three';

export class InteractionManager {
  constructor(sceneManager, organManager, uiController) {
    this.sceneManager = sceneManager;
    this.organManager = organManager;
    this.uiController = uiController;

    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this._hoveredOrgan = null;

    // Highlight material cache
    this._highlightColor = new THREE.Color(0x6366f1);
    this._highlightIntensity = 0.4;

    this._bindEvents();
  }

  /* ─── Events ──────────────────────────────────── */
  _bindEvents() {
    const canvas = this.sceneManager.canvas;

    canvas.addEventListener('mousemove', (e) => {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    canvas.addEventListener('click', (e) => {
      // Ignore if moving (orbiting)
      this._handleClick();
    });

    // Touch support
    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        this.mouse.x = (touch.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(touch.clientY / window.innerHeight) * 2 + 1;
      }
    });

    canvas.addEventListener('touchend', () => {
      this._handleClick();
    });

    // Change cursor on hover
    canvas.style.cursor = 'grab';
  }

  /* ─── Per-frame update ────────────────────────── */
  update() {
    this.raycaster.setFromCamera(this.mouse, this.sceneManager.camera);

    const allMeshes = this.organManager.getAllMeshes();
    const intersects = this.raycaster.intersectObjects(allMeshes, false);

    if (intersects.length > 0) {
      const mesh = intersects[0].object;
      const organInfo = this.organManager.getOrganByMesh(mesh);
      if (organInfo) {
        if (this._hoveredOrgan !== organInfo.name) {
          this._unhighlightCurrent();
          this._hoveredOrgan = organInfo.name;
          this._highlightOrgan(organInfo.name);
          this.sceneManager.canvas.style.cursor = 'pointer';
        }
      }
    } else {
      if (this._hoveredOrgan) {
        this._unhighlightCurrent();
        this._hoveredOrgan = null;
        this.sceneManager.canvas.style.cursor = 'grab';
      }
    }
  }

  /* ─── Click ───────────────────────────────────── */
  _handleClick() {
    if (this._hoveredOrgan) {
      this.uiController.selectOrgan(this._hoveredOrgan);
    }
  }

  /* ─── Highlight ───────────────────────────────── */
  _highlightOrgan(name) {
    const organ = this.organManager.getOrgan(name);
    if (!organ) return;

    organ.meshes.forEach((mesh) => {
      if (mesh.material) {
        // Add emissive glow
        if (mesh.material.emissive) {
          mesh.material.emissive.copy(this._highlightColor);
          mesh.material.emissiveIntensity = this._highlightIntensity;
        }
      }
    });

    // Slight scale bump on the group (once per organ, not per mesh)
    const s = organ.group.scale.x;
    organ.group.scale.setScalar(s * 1.05);
  }

  _unhighlightCurrent() {
    if (!this._hoveredOrgan) return;
    const organ = this.organManager.getOrgan(this._hoveredOrgan);
    if (!organ) return;

    organ.meshes.forEach((mesh) => {
      if (mesh.material && mesh.userData.originalMaterial) {
        if (mesh.material.emissive) {
          mesh.material.emissive.copy(mesh.userData.originalMaterial.emissive || new THREE.Color(0, 0, 0));
          mesh.material.emissiveIntensity = mesh.userData.originalMaterial.emissiveIntensity || 0;
        }
      }
    });

    // Restore exactly to base scale to prevent any continuous drift
    if (organ.baseScale) {
       organ.group.scale.setScalar(organ.baseScale);
    } else {
       // Fallback just in case
       const s = organ.group.scale.x;
       organ.group.scale.setScalar(s / 1.05);
    }
  }
}
