// The Liquid Ponzi pyramid as a real 3D object: a glass pyramid with glowing edges, filling with violet liquid.
// Exposes window.Pyramid3D.draw(opts) -> a square canvas with a transparent background.
import * as THREE from 'three';

const SIZE = 1200;
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(SIZE, SIZE, false);
renderer.setClearColor(0x000000, 0);
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.localClippingEnabled = true;

const scene = new THREE.Scene();

// studio environment: dark room, a violet softbox, a peach strip and an overhead key, for reflections
function studio() {
  const env = new THREE.Scene();
  env.add(new THREE.Mesh(new THREE.SphereGeometry(20, 32, 16), new THREE.MeshBasicMaterial({ color: 0x0c0a12, side: THREE.BackSide })));
  const panel = (w, h, x, y, z, c, v) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(c).multiplyScalar(v), side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m);
  };
  panel(8, 6, -8, 6, 6, 0xbda1f9, 3.5);
  panel(2.5, 12, 9, 1, 5, 0xf1b6a2, 4);
  panel(12, 2.5, 0, 11, 0, 0xffffff, 3);
  panel(6, 10, 6, -2, -9, 0xff783f, 2);
  return env;
}
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(studio(), 0.02).texture;

const FOV = 24;
const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 100);
const key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(-3, 6, 5); scene.add(key);
const rim = new THREE.DirectionalLight(0xff9a6a, 1.6); rim.position.set(5, 1, -4); scene.add(rim);

// pyramid: base half-diagonal R, height Hh, base at y = -Hh/2
const R = 1.0, Hh = 1.45, BASE = -Hh / 2;
const group = new THREE.Group();
scene.add(group);

const glass = new THREE.MeshPhysicalMaterial({
  color: 0xd9c8ff, metalness: 0, roughness: 0.06, transmission: 1, thickness: 0.9, ior: 1.5,
  attenuationColor: new THREE.Color(0x8b5cf6), attenuationDistance: 2.2, clearcoat: 1, clearcoatRoughness: 0.05,
  iridescence: 0.35, iridescenceIOR: 1.3, transparent: true, side: THREE.DoubleSide
});
const shell = new THREE.Mesh(new THREE.ConeGeometry(R, Hh, 4, 1, false), glass);
group.add(shell);

// glowing edges: thin capsules along the 8 edges
const apex = new THREE.Vector3(0, Hh / 2, 0);
const corners = [0, 1, 2, 3].map(i => { const a = i * Math.PI / 2; return new THREE.Vector3(Math.sin(a) * R, BASE, Math.cos(a) * R); });
const edgeMat = new THREE.MeshStandardMaterial({ color: 0xffd7c6, emissive: 0xf1a68c, emissiveIntensity: 1.6, metalness: 0.3, roughness: 0.3 });
function edge(a, b, r = 0.012) {
  const d = new THREE.Vector3().subVectors(b, a);
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, d.length(), 10), edgeMat);
  m.position.copy(a).addScaledVector(d, 0.5);
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
  group.add(m);
}
corners.forEach((c, i) => { edge(apex, c); edge(c, corners[(i + 1) % 4]); });

// liquid: an inner pyramid clipped at the fill level, plus a glowing surface cap
const clip = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
const liquidMat = new THREE.MeshPhysicalMaterial({ vertexColors: true, emissive: 0x2a1460, emissiveIntensity: 0.3, roughness: 0.12, metalness: 0.05, clearcoat: 1, clippingPlanes: [clip], side: THREE.DoubleSide });
const IN = 0.9;
const liqGeo = new THREE.ConeGeometry(R * IN, Hh * IN, 4, 24, false);
{ // violet at the bottom -> peach at the top, like the site's wordmark
  const pos = liqGeo.attributes.position, col = [];
  const lo = new THREE.Color(0x6a3cf0), mid = new THREE.Color(0xb48cff), hi = new THREE.Color(0xf6b49a);
  for (let i = 0; i < pos.count; i++) {
    const u = (pos.getY(i) + Hh * IN / 2) / (Hh * IN);
    const c = u < 0.5 ? lo.clone().lerp(mid, u / 0.5) : mid.clone().lerp(hi, (u - 0.5) / 0.5);
    col.push(c.r, c.g, c.b);
  }
  liqGeo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
}
const liquid = new THREE.Mesh(liqGeo, liquidMat);
liquid.position.y = BASE + Hh * IN / 2 + 0.02;
group.add(liquid);
const capMat = new THREE.MeshStandardMaterial({ color: 0xffc4ad, emissive: 0xff8a5c, emissiveIntensity: 1.1, roughness: 0.25, transparent: true, opacity: 0.92, side: THREE.DoubleSide });
const cap = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), capMat);
cap.rotation.x = -Math.PI / 2;
group.add(cap);

window.Pyramid3D = {
  size: SIZE,
  height: Hh,
  // opts: ry, rx (radians), extent (world half-height framed), level 0..1 (liquid fill by height)
  draw(o = {}) {
    const extent = o.extent || 1.15;
    camera.position.set(0, 0.12, extent / Math.tan((FOV / 2) * Math.PI / 180));
    camera.lookAt(0, 0, 0);
    group.rotation.set(o.rx ?? 0.12, o.ry ?? 0.6, 0);
    group.scale.setScalar(o.s ?? 1);
    const lev = Math.max(0.001, Math.min(0.97, o.level ?? 0));
    const yLiq0 = BASE + 0.02, hLiq = Hh * IN;
    const y = yLiq0 + hLiq * lev;                      // liquid surface height in local space
    const show = (o.level ?? 0) > 0.002;
    liquid.visible = show; cap.visible = show;
    // clipping planes are in world space: follow the group transform
    group.updateMatrixWorld(true);
    const n = new THREE.Vector3(0, -1, 0).applyQuaternion(group.quaternion);
    const p = new THREE.Vector3(0, y + (o.wave || 0) * 0.01, 0).applyMatrix4(group.matrixWorld);
    clip.setFromNormalAndCoplanarPoint(n, p);
    const r = R * IN * (1 - lev);                      // half-diagonal of the cross-section
    cap.position.set(0, y, 0);
    cap.scale.set(r * Math.SQRT2 * 0.995, r * Math.SQRT2 * 0.995, 1);
    cap.rotation.z = Math.PI / 4;
    edgeMat.emissiveIntensity = o.edge ?? 1.6;
    renderer.render(scene, camera);
    return renderer.domElement;
  }
};
