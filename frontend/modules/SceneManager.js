/**
 * SceneManager — Three.js scene, camera, lighting, renderer, controls.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class SceneManager {
  constructor(canvas) {
    this.canvas = canvas;
    this.clock = new THREE.Clock();

    // For smooth camera animation
    this._cameraTargetPos = null;
    this._cameraTargetLook = null;
    this._cameraAnimating = false;

    this._initRenderer();
    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._initEnvironment();

    window.addEventListener('resize', () => this._onResize());
  }

  /* ── Renderer ─────────────────────────────────── */
  _initRenderer() {
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 2.0;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }

  /* ── Scene ────────────────────────────────────── */
  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x06060f);
    this.scene.fog = new THREE.FogExp2(0x06060f, 0.008);
  }

  /* ── Camera ───────────────────────────────────── */
  _initCamera() {
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
    this.camera.position.set(0, 1.8, 7);
    this.camera.lookAt(0, 1.5, 0);
  }

  /* ── Lights ───────────────────────────────────── */
  _initLights() {
    // Ambient — strong enough to see organ details
    const ambient = new THREE.AmbientLight(0x8899bb, 1.0);
    this.scene.add(ambient);

    // Hemisphere — sky / ground
    const hemi = new THREE.HemisphereLight(0xaabbff, 0x443322, 0.6);
    this.scene.add(hemi);

    // Key light — warm directional (strong)
    const key = new THREE.DirectionalLight(0xfff5e6, 1.8);
    key.position.set(5, 10, 7);
    key.castShadow = true;
    key.shadow.mapSize.setScalar(1024);
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 30;
    key.shadow.camera.left = -8;
    key.shadow.camera.right = 8;
    key.shadow.camera.top = 8;
    key.shadow.camera.bottom = -8;
    this.scene.add(key);

    // Fill light — cool from left
    const fill = new THREE.DirectionalLight(0x6366f1, 0.5);
    fill.position.set(-5, 6, -3);
    this.scene.add(fill);

    // Front fill — so organs aren't dark from viewing angle
    const frontFill = new THREE.DirectionalLight(0xdde4ff, 0.6);
    frontFill.position.set(0, 3, 10);
    this.scene.add(frontFill);

    // Rim light — cyan accent from behind
    const rim = new THREE.DirectionalLight(0x06b6d4, 0.5);
    rim.position.set(0, 4, -8);
    this.scene.add(rim);

    // Point light near torso center
    const core = new THREE.PointLight(0x6366f1, 0.5, 12);
    core.position.set(0, 1.5, 0);
    this.scene.add(core);
  }

  /* ── Controls ─────────────────────────────────── */
  _initControls() {
    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.minDistance = 2;
    this.controls.maxDistance = 20;
    this.controls.maxPolarAngle = Math.PI * 0.85;
    this.controls.target.set(0, 1.5, 0);
    this.controls.update();
  }

  /* ── Environment ──────────────────────────────── */
  _initEnvironment() {
    // Subtle ground grid
    const grid = new THREE.GridHelper(30, 30, 0x1a1a3a, 0x0f0f1f);
    grid.position.y = -0.5;
    grid.material.transparent = true;
    grid.material.opacity = 0.3;
    this.scene.add(grid);

    // Particle background
    const particleCount = 300;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 30;
      positions[i * 3 + 1] = Math.random() * 15 - 2;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 30;
    }
    const particleGeom = new THREE.BufferGeometry();
    particleGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.04,
      color: 0x6366f1,
      transparent: true,
      opacity: 0.35,
      sizeAttenuation: true,
    });
    this.particles = new THREE.Points(particleGeom, particleMat);
    this.scene.add(this.particles);
  }

  /* ── Focus camera on a world position ─────────── */
  focusOn(targetPosition, distance = 3.5) {
    this._cameraTargetLook = targetPosition.clone();
    this._cameraTargetPos = new THREE.Vector3(
      targetPosition.x + 0.5,
      targetPosition.y + 0.3,
      targetPosition.z + distance
    );
    this._cameraAnimating = true;
  }

  /* ── Reset camera to overview ─────────────────── */
  resetCamera() {
    this._cameraTargetPos = new THREE.Vector3(0, 1.8, 7);
    this._cameraTargetLook = new THREE.Vector3(0, 1.5, 0);
    this._cameraAnimating = true;
  }

  /* ── Render ───────────────────────────────────── */
  render() {
    // Smooth camera animation
    if (this._cameraAnimating && this._cameraTargetPos) {
      this.camera.position.lerp(this._cameraTargetPos, 0.04);
      this.controls.target.lerp(this._cameraTargetLook, 0.04);

      if (this.camera.position.distanceTo(this._cameraTargetPos) < 0.05) {
        this._cameraAnimating = false;
      }
    }

    this.controls.update();

    // Slowly rotate particles
    if (this.particles) {
      this.particles.rotation.y += 0.0002;
    }

    this.renderer.render(this.scene, this.camera);
  }

  /* ── Resize ───────────────────────────────────── */
  _onResize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }
}
