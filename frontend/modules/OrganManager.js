/**
 * OrganManager — Loads and positions all organ .glb models.
 *
 * Each organ is wrapped in a THREE.Group so that transforms
 * (position, scale, rotation) can be applied independently.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

/* ─── Organ Registry ─────────────────────────────────────────────
   Maps logical organ name → model file, position, TARGET SIZE
   (bounding-box max dimension in world units), rotation, and metadata.
   After loading, each model is auto-scaled so its largest dimension
   matches targetSize.  Add entries here to extend the system.
   ──────────────────────────────────────────────────────────────── */
const ORGAN_REGISTRY = {
  heart: {
    file: 'heart_-_animated_anatomical_3d_model.glb',
    position: [0.15, 2.2, 0.3],
    targetSize: 0.7,
    rotation: [0, 0, 0],
    icon: '❤️',
    system: 'Cardiovascular',
    function: 'Blood circulation & oxygen transport',
    riskFactors: ['Hypertension', 'Atherosclerosis', 'Arrhythmia'],
    color: '#FF6B6B',
  },
  lungs: {
    file: 'realistic_human_lungs.glb',
    position: [0, 2.6, 0.0],
    targetSize: 1.2,
    rotation: [0, Math.PI, 0],
    icon: '🫁',
    system: 'Respiratory',
    function: 'Gas exchange & oxygenation',
    riskFactors: ['COPD', 'Asthma', 'Fibrosis'],
    color: '#87CEEB',
  },
  liver: {
    file: 'liver_organ.glb',
    position: [-0.45, 1.75, 0.25],
    targetSize: 0.65,
    rotation: [0, Math.PI * 0.3, 0],
    icon: '🟤',
    system: 'Metabolic',
    function: 'Detoxification & metabolism',
    riskFactors: ['Fatty liver', 'Cirrhosis', 'Hepatitis'],
    color: '#4ECDC4',
  },
  kidneys: {
    file: 'cups_left__right_kidney.glb',
    position: [0, 1.4, -0.2],
    targetSize: 0.6,
    rotation: [0, 0, 0],
    icon: '🫘',
    system: 'Renal',
    function: 'Filtration & waste removal',
    riskFactors: ['CKD', 'Stones', 'Hypertension'],
    color: '#96CEB4',
  },
  pancreas: {
    file: 'duodenum_pancreas_spleen.glb',
    position: [0.3, 1.55, 0.2],
    targetSize: 0.55,
    rotation: [0, 0, 0],
    icon: '🟨',
    system: 'Endocrine',
    function: 'Blood sugar regulation & digestion',
    riskFactors: ['Diabetes', 'Pancreatitis', 'Metabolic syndrome'],
    color: '#45B7D1',
  },
  stomach: {
    file: 'stomach.glb',
    position: [0.35, 1.9, 0.3],
    targetSize: 0.6,
    rotation: [0, 0, 0],
    icon: '🫄',
    system: 'Digestive',
    function: 'Food breakdown & gastric acid production',
    riskFactors: ['Ulcers', 'Gastritis', 'GERD'],
    color: '#FFEAA7',
  },
  intestine: {
    file: 'bad-quality_s__l_intestine_dacs_ujat_242e75096.glb',
    position: [0, 0.7, 0.15],
    targetSize: 0.9,
    rotation: [0, 0, 0],
    icon: '🧬',
    system: 'Digestive',
    function: 'Nutrient absorption & microbiome',
    riskFactors: ['IBD', 'Leaky gut', 'Dysbiosis'],
    color: '#F0E68C',
  },
  muscles: {
    file: 'skeletal_muscle_cell_anatomy.glb',
    position: [1.0, 1.2, 0.2],
    targetSize: 0.7,
    rotation: [0, -Math.PI * 0.3, 0],
    icon: '💪',
    system: 'Musculoskeletal',
    function: 'Movement & energy metabolism',
    riskFactors: ['Atrophy', 'Fatigue', 'Injury'],
    color: '#6495ED',
  },
  fat: {
    file: 'perivascular_adipose_tissue_and_nerve.glb',
    position: [-1.0, 1.0, 0.2],
    targetSize: 0.6,
    rotation: [0, 0, 0],
    icon: '🔶',
    system: 'Adipose',
    function: 'Energy storage & hormonal regulation',
    riskFactors: ['Obesity', 'Inflammation', 'Insulin resistance'],
    color: '#F4A460',
  },
};

export class OrganManager {
  constructor(scene, basePath) {
    this.scene = scene;
    this.basePath = basePath;

    /** @type {Map<string, {group: THREE.Group, meshes: THREE.Mesh[], meta: object, mixer: THREE.AnimationMixer|null}>} */
    this.organs = new Map();

    // Parent group for all organs (easy transforms)
    this.rootGroup = new THREE.Group();
    this.rootGroup.name = 'organs-root';
    this.scene.add(this.rootGroup);

    // Loaders
    this.gltfLoader = new GLTFLoader();
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/');
    this.gltfLoader.setDRACOLoader(dracoLoader);
  }

  /* ─── Load all organs ─────────────────────────────── */
  async loadAll(onProgress) {
    const entries = Object.entries(ORGAN_REGISTRY);
    let loaded = 0;

    const promises = entries.map(([name, meta]) =>
      this._loadOrgan(name, meta)
        .then(() => {
          loaded++;
          if (onProgress) onProgress(loaded, entries.length);
        })
        .catch((err) => {
          console.warn(`[OrganManager] Failed to load "${name}":`, err);
          loaded++;
          if (onProgress) onProgress(loaded, entries.length);
        })
    );

    await Promise.all(promises);
    console.log(`[OrganManager] Loaded ${this.organs.size}/${entries.length} organs`);
  }

  /* ─── Load single organ ───────────────────────────── */
  _loadOrgan(name, meta) {
    return new Promise((resolve, reject) => {
      const url = this.basePath + meta.file;

      this.gltfLoader.load(
        url,
        (gltf) => {
          const group = new THREE.Group();
          group.name = `organ-${name}`;

          // Add model to group
          const model = gltf.scene;
          group.add(model);

          // ── Auto-scale using bounding box ───────────────
          // Compute bounding box of the loaded model
          const box = new THREE.Box3().setFromObject(model);
          const size = new THREE.Vector3();
          box.getSize(size);
          const maxDim = Math.max(size.x, size.y, size.z);

          // Uniform scale so the largest dimension = targetSize
          const targetSize = meta.targetSize || 1.0;
          const autoScale = maxDim > 0 ? targetSize / maxDim : 1;
          group.scale.set(autoScale, autoScale, autoScale);

          // Center the model within its group
          const center = new THREE.Vector3();
          box.getCenter(center);
          model.position.sub(center.multiplyScalar(1));  // Move model so center is at group origin

          // Apply position and rotation from registry
          group.position.set(...meta.position);
          group.rotation.set(...meta.rotation);

          console.log(`[OrganManager] "${name}" native size: ${maxDim.toFixed(1)} → scaled to ${targetSize} (×${autoScale.toFixed(4)})`);

          // Set up animation mixer if the model has animations
          let mixer = null;
          if (gltf.animations && gltf.animations.length > 0) {
            mixer = new THREE.AnimationMixer(model);
            gltf.animations.forEach((clip) => {
              const action = mixer.clipAction(clip);
              action.play();
            });
          }

          // Collect all meshes for raycasting / highlighting
          // Also enhance material brightness for dark models
          const meshes = [];
          const organColor = new THREE.Color(meta.color || '#ffffff');
          model.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;

              // Brighten organ materials for visibility
              if (child.material) {
                // Ensure we're working with a standard material
                if (child.material.isMeshStandardMaterial || child.material.isMeshPhysicalMaterial) {
                  // Reduce metalness slightly so ambient light contributes more
                  child.material.metalness = Math.min(child.material.metalness, 0.3);
                  // Limit roughness to avoid overly matte or overly glossy
                  child.material.roughness = Math.max(child.material.roughness, 0.4);
                }

                // Add subtle emissive glow matching organ color
                if (child.material.emissive !== undefined) {
                  child.material.emissive = organColor.clone().multiplyScalar(0.15);
                  child.material.emissiveIntensity = 0.3;
                }

                child.material.needsUpdate = true;
              }

              // Store original material for highlight restore
              child.userData.originalMaterial = child.material.clone();
              child.userData.organName = name;
              meshes.push(child);
            }
          });

          this.rootGroup.add(group);

          this.organs.set(name, {
            group,
            model,
            meshes,
            meta,
            mixer,
            baseScale: autoScale,
            health: 0.8,       // Default until API provides data
            metrics: {},
          });

          resolve();
        },
        undefined,
        (err) => reject(err)
      );
    });
  }

  /* ─── Accessors ──────────────────────────────────── */
  getOrgan(name) {
    return this.organs.get(name) || null;
  }

  getAllOrgans() {
    return this.organs;
  }

  getAllMeshes() {
    const all = [];
    for (const [, organ] of this.organs) {
      all.push(...organ.meshes);
    }
    return all;
  }

  getOrganByMesh(mesh) {
    const name = mesh.userData.organName;
    return name ? { name, ...this.organs.get(name) } : null;
  }

  /* ─── Registry (for UI) ──────────────────────────── */
  static getRegistry() {
    return ORGAN_REGISTRY;
  }
}
