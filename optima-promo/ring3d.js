// The Optima ring as a real 3D object: two half-rings (lime + chrome) lit by a studio environment.
// Exposes window.Ring3D.draw(opts) -> a square canvas with a transparent background.
import * as THREE from 'three';

const SIZE = 1400;
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(SIZE, SIZE, false);
renderer.setClearColor(0x000000, 0);
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();

// ---- studio environment: a bright cyclorama with a few hot softboxes and dark flags for contrast
function studio() {
  const env = new THREE.Scene();
  const geo = new THREE.SphereGeometry(20, 48, 24);
  const col = [];
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 20; // -1 .. 1
    const v = y > 0 ? 0.55 + 0.75 * y : 0.55 + 0.42 * y; // bright overhead, darker floor
    col.push(v, v, v * 0.98);
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  env.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  const panel = (w, h, x, y, z, v, tint = [1, 1, 1]) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(v * tint[0], v * tint[1], v * tint[2]), side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m);
  };
  panel(9, 5, -7, 8, 7, 9);            // key softbox, upper left front
  panel(2.2, 12, 9.6, 2.9, 8.5, 6);    // tall strip, right front: the streak across the chrome face
  panel(12, 2.5, 0, 11, -3, 6);        // overhead strip
  panel(4, 10, -11, 0, -4, 2.5, [0.85, 1, 0.6]); // lime-tinted kicker from behind
  panel(7, 9, 9, -3, -8, 0.02);        // dark flags: give the chrome something to contrast against
  panel(8, 6, -9, -6, 6, 0.03);
  panel(5, 14, 2, 0, 12, 0.04);
  panel(14, 4, 0, -10, 2, 0.05);
  return env;
}
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(studio(), 0.015).texture;
scene.environmentIntensity = 1.0;

const FOV = 26;
const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 100);

const key = new THREE.DirectionalLight(0xffffff, 1.2);
key.position.set(-3, 5, 6);
scene.add(key);
const rim = new THREE.DirectionalLight(0xd8ffa0, 0.6);
rim.position.set(4, -2, -3);
scene.add(rim);

// ---- ring geometry: an extruded, bevelled half-annulus, used twice
function halfRing(a0, a1) {
  const R = 0.92, r = 0.62;
  const s = new THREE.Shape();
  s.absarc(0, 0, R, a0, a1, false);
  s.absarc(0, 0, r, a1, a0, true);
  s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: 0.26, bevelEnabled: true, bevelThickness: 0.11, bevelSize: 0.11, bevelSegments: 12, curveSegments: 128 });
  g.translate(0, 0, -0.13);
  return g;
}
const GAP = 0.045;
const limeMat = new THREE.MeshPhysicalMaterial({ color: 0xa6ea2a, metalness: 0.82, roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.08 });
const chromeMat = new THREE.MeshPhysicalMaterial({ color: 0xf2f4f5, metalness: 1, roughness: 0.09 });
const ring = new THREE.Group();
const split = 0.42; // the split runs lower-left to upper-right, like the logo
const lime = new THREE.Mesh(halfRing(split + GAP, split + Math.PI - GAP), limeMat);
const chrome = new THREE.Mesh(halfRing(split + Math.PI + GAP, split + 2 * Math.PI - GAP), chromeMat);
ring.add(lime, chrome);
scene.add(ring);

// ---- coins (scene 5): lime discs with a label on both faces
function coinFace(label) {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const x = c.getContext('2d');
  x.fillStyle = '#b9f04a'; x.fillRect(0, 0, 512, 512);
  x.strokeStyle = '#24301f'; x.lineWidth = 14; x.beginPath(); x.arc(256, 256, 214, 0, Math.PI * 2); x.stroke();
  x.fillStyle = '#24301f'; x.font = '800 132px DM'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.letterSpacing = '-4px';
  x.fillText(label, 256, 266);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
const coins = [];
function makeCoin(label) {
  const edge = new THREE.MeshPhysicalMaterial({ color: 0xa6ea2a, metalness: 0.85, roughness: 0.2, clearcoat: 1 });
  const face = new THREE.MeshPhysicalMaterial({ map: coinFace(label), metalness: 0.25, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.1 });
  const m = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.07, 72), [edge, face, face]);
  const g = new THREE.Group();
  m.rotation.x = Math.PI / 2; // faces point along z
  m.rotation.y = Math.PI / 2; // label upright
  g.add(m);
  g.visible = false;
  scene.add(g);
  coins.push(g);
}

window.Ring3D = {
  canvas: renderer.domElement,
  size: SIZE,
  async init() { await document.fonts.load('800 100px DM'); makeCoin('USE'); makeCoin('HOLD'); },
  // opts: rx, ry, rz (radians), extent (world half-height framed at z=0), sy (squash), coins: [{a, r, y}]
  draw(o = {}) {
    const extent = o.extent || 1.35;
    camera.position.set(0, 0, extent / Math.tan((FOV / 2) * Math.PI / 180));
    camera.lookAt(0, 0, 0);
    ring.visible = o.ring !== false;
    ring.rotation.set(o.rx ?? -0.12, o.ry ?? 0.42, o.rz ?? 0);
    ring.scale.set(o.sx ?? 1, o.sy ?? 1, 1);
    ring.position.set(0, o.py ?? 0, 0);
    coins.forEach((c, i) => {
      const k = o.coins && o.coins[i];
      c.visible = !!k;
      if (!k) return;
      c.position.set(Math.sin(k.a) * k.r, (k.y || 0) + Math.sin(k.a * 2) * 0.05, Math.cos(k.a) * k.r * 0.9);
      c.rotation.set(0.08, k.spin ?? Math.sin(k.a) * 0.5, 0);
      c.scale.setScalar(k.s ?? 1);
    });
    renderer.render(scene, camera);
    return renderer.domElement;
  }
};
window.dispatchEvent(new Event('ring3d-ready'));
