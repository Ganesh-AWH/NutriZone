/**
 * ConnectionManager — Draws glowing, sweeping lines connecting the 3D organs.
 * Adds to the premium aesthetic by creating a "network" of health.
 */

import * as THREE from 'three';

export class ConnectionManager {
  constructor(sceneManager, organManager) {
    this.sceneManager = sceneManager;
    this.organManager = organManager;
    
    // Group to hold all connection lines
    this.connectionGroup = new THREE.Group();
    this.connectionGroup.name = 'connections-root';
    
    // Add to the organManager's rootGroup so it moves/floats along with the organs
    if (this.organManager.rootGroup) {
      this.organManager.rootGroup.add(this.connectionGroup);
    } else {
      this.sceneManager.scene.add(this.connectionGroup);
    }

    this.lines = [];
    
    // Shader material for glowing, animated lines
    this.lineMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color1: { value: new THREE.Color(0x6366f1) }, // Indigo
        color2: { value: new THREE.Color(0x0ea5e9) }  // Sky blue
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform vec3 color1;
        uniform vec3 color2;
        varying vec2 vUv;
        
        void main() {
          // Animated dash effect
          float dash = sin((vUv.x * 20.0) - (time * 5.0)) * 0.5 + 0.5;
          dash = smoothstep(0.4, 0.6, dash);
          
          // Gradient flow
          vec3 baseColor = mix(color1, color2, vUv.x);
          
          // Add pulse edge
          float alpha = dash * 0.8 + 0.2; // Always slightly visible
          
          gl_FragColor = vec4(baseColor, alpha * 0.5);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide
    });
  }

  /**
   * Called after all organs are loaded to generate the connections.
   */
  buildConnections() {
    const pairs = [
      // Cardiopulmonary
      ['heart', 'lungs'],
      // Digestive
      ['stomach', 'liver'],
      ['stomach', 'pancreas'],
      ['pancreas', 'intestine'],
      ['liver', 'intestine'],
      ['lungs', 'stomach'],
      // Systemic
      ['heart', 'kidneys'],
      ['heart', 'liver'],
      ['intestine', 'muscles'],
      ['intestine', 'fat'],
      ['heart', 'muscles'],
      ['heart', 'fat']
    ];

    pairs.forEach(([fromName, toName]) => {
      const fromOrgan = this.organManager.getOrgan(fromName);
      const toOrgan = this.organManager.getOrgan(toName);

      if (fromOrgan && toOrgan) {
        this._createCurve(fromOrgan, toOrgan);
      }
    });
  }

  _createCurve(fromOrgan, toOrgan) {
    // Get exact group positions (which signify the center of the bounding box)
    const p1 = fromOrgan.group.position.clone();
    const p2 = toOrgan.group.position.clone();

    // Create a beautiful sweeping curve
    const distance = p1.distanceTo(p2);
    
    // Midpoint curved backwards slightly in Z to give a 3D arc effect
    const midPoint = new THREE.Vector3().lerpVectors(p1, p2, 0.5);
    midPoint.z -= distance * 0.4; // Push back into space
    midPoint.x += (Math.random() - 0.5) * 0.2; // Slight irregularity
    midPoint.y += (Math.random() - 0.5) * 0.2;

    const curve = new THREE.QuadraticBezierCurve3(p1, midPoint, p2);

    // Create a tube along the curve
    const tubeGeometry = new THREE.TubeGeometry(curve, 32, 0.008, 6, false);
    
    // Custom material per line for slightly varying colors could be done here, 
    // but we use the shared animated ShaderMaterial for performance and cohesion.
    const tubeMesh = new THREE.Mesh(tubeGeometry, this.lineMaterial);
    
    this.connectionGroup.add(tubeMesh);
    this.lines.push(tubeMesh);
  }

  /**
   * Called every frame in the render loop.
   */
  update(delta, elapsed) {
    if (this.lineMaterial) {
      this.lineMaterial.uniforms.time.value = elapsed;
    }
  }
}
