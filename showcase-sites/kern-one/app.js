let THREE;

const container = document.querySelector('#product-scene');
const canvas = container.querySelector('canvas');
const poster = document.querySelector('.product-poster');
const status = document.querySelector('#scene-status');
const resetButton = document.querySelector('#reset-view');
const explodeButton = document.querySelector('#toggle-explode');
const captureButton = document.querySelector('#capture');
const hero = document.querySelector('.hero');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const supportsWebGL = (() => {
  try { return Boolean(document.createElement('canvas').getContext('webgl2') || document.createElement('canvas').getContext('webgl')); } catch { return false; }
})();

let renderer;
let scene;
let camera;
let product;
let animationFrame;
let visible = true;
let dragging = false;
let lastPointerX = 0;
let targetRotationX = -.08;
let targetRotationY = -.35;
let explodeProgress = 0;
let targetExplode = 0;
let manualExplode = false;
let revealProgress = 1;
let capturedFrames = 0;
const parts = [];

function material(color, roughness = .72, metalness = .15) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness });
}

function addPart(geometry, partMaterial, position, explodeOffset = [0, 0, 0]) {
  const mesh = new THREE.Mesh(geometry, partMaterial);
  mesh.position.set(...position);
  mesh.userData.base = mesh.position.clone();
  mesh.userData.offset = new THREE.Vector3(...explodeOffset);
  product.add(mesh);
  parts.push(mesh);
  return mesh;
}

function buildProduct() {
  product = new THREE.Group();
  scene.add(product);
  const bone = material(0xe9e5d8, .58, .28);
  const black = material(0x171712, .48, .35);
  const red = material(0xf04a31, .62, .12);
  const glass = material(0x6f969d, .18, .5);

  addPart(new THREE.BoxGeometry(3.5, 2.2, 1.15), bone, [0, 0, 0], [-1.3, 0, 0]);
  addPart(new THREE.BoxGeometry(1.15, .38, .72), black, [-.75, 1.23, -.05], [-.3, 1.35, 0]);
  addPart(new THREE.BoxGeometry(.62, .22, .62), black, [1.05, 1.2, -.03], [.8, 1.15, 0]);
  addPart(new THREE.CylinderGeometry(.84, 1.02, 1.05, 48), black, [0, .02, .93], [0, 0, 1.35]).rotation.x = Math.PI / 2;
  addPart(new THREE.CylinderGeometry(.61, .72, .63, 48), glass, [0, .02, 1.62], [0, 0, 2.15]).rotation.x = Math.PI / 2;
  addPart(new THREE.TorusGeometry(.77, .09, 14, 48), red, [0, .02, 1.34], [0, 0, 1.7]);
  addPart(new THREE.BoxGeometry(1.55, .24, .75), red, [-.7, -1.18, -.02], [-.5, -1.3, 0]);
  addPart(new THREE.BoxGeometry(3.14, 1.84, .13), black, [0, 0, -.64], [1.3, 0, -1.4]);

  const labelCanvas = document.createElement('canvas');
  labelCanvas.width = 512; labelCanvas.height = 128;
  const labelContext = labelCanvas.getContext('2d');
  labelContext.fillStyle = '#e9e5d8'; labelContext.fillRect(0, 0, 512, 128);
  labelContext.fillStyle = '#171712'; labelContext.font = '500 46px monospace'; labelContext.fillText('KERN / ONE', 28, 82);
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1.45, .36), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(labelCanvas) }));
  label.position.set(-.9, .62, .585); product.add(label);
  product.rotation.set(targetRotationX, targetRotationY, 0);
}

function init() {
  if (!supportsWebGL) throw new Error('WebGL unavailable');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 720 ? 1.35 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(33, 1, .1, 100);
  camera.position.set(0, .2, 8.5);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x39403c, 2.5));
  const key = new THREE.DirectionalLight(0xffffff, 3.8); key.position.set(4, 7, 6); scene.add(key);
  const rim = new THREE.DirectionalLight(0xf04a31, 2.2); rim.position.set(-5, 1, -2); scene.add(rim);
  buildProduct();
  if (!reducedMotion) {
    explodeProgress = 1;
    revealProgress = 0;
    product.scale.setScalar(.72);
    product.rotation.y = -1.2;
  }
  poster.hidden = false;
  status.textContent = reducedMotion ? '3D ready / motion reduced' : 'Assembling optical system';
  resize();
  render();
}

function resize() {
  if (!renderer) return;
  const box = container.getBoundingClientRect();
  renderer.setSize(box.width, box.height, false);
  camera.aspect = box.width / box.height;
  camera.updateProjectionMatrix();
  invalidate();
}

function update() {
  const easing = reducedMotion ? 1 : .09;
  revealProgress = Math.min(1, revealProgress + .025);
  const revealEase = 1 - Math.pow(1 - revealProgress, 3);
  product.scale.setScalar(.72 + revealEase * .28);
  product.rotation.x += (targetRotationX - product.rotation.x) * easing;
  product.rotation.y += (targetRotationY - product.rotation.y) * easing;
  explodeProgress += (targetExplode - explodeProgress) * easing;
  parts.forEach((part) => part.position.copy(part.userData.base).addScaledVector(part.userData.offset, explodeProgress));
}

function render() {
  if (!renderer || !visible || document.hidden) return;
  update();
  renderer.render(scene, camera);
  if (reducedMotion || revealProgress > .25) poster.hidden = true;
  if (revealProgress >= 1 && status.textContent === 'Assembling optical system') status.textContent = 'Realtime 3D / drag enabled';
  if (!reducedMotion && (revealProgress < 1 || dragging || Math.abs(product.rotation.y - targetRotationY) > .001 || Math.abs(explodeProgress - targetExplode) > .001)) {
    animationFrame = requestAnimationFrame(render);
  }
}

function invalidate() {
  cancelAnimationFrame(animationFrame);
  animationFrame = requestAnimationFrame(render);
}

container.addEventListener('pointerdown', (event) => {
  dragging = true; lastPointerX = event.clientX; container.setPointerCapture(event.pointerId); invalidate();
});
container.addEventListener('pointermove', (event) => {
  if (!dragging) return;
  targetRotationY += (event.clientX - lastPointerX) * .008;
  lastPointerX = event.clientX;
  invalidate();
});
container.addEventListener('pointerup', (event) => { dragging = false; container.releasePointerCapture(event.pointerId); invalidate(); });

resetButton.addEventListener('click', () => {
  targetRotationX = -.08;
  targetRotationY = -.35;
  targetExplode = 0;
  manualExplode = true;
  explodeButton.setAttribute('aria-pressed', 'false');
  invalidate();
});
explodeButton.addEventListener('click', () => {
  const expanded = explodeButton.getAttribute('aria-pressed') !== 'true';
  manualExplode = true;
  explodeButton.setAttribute('aria-pressed', String(expanded));
  targetExplode = expanded ? 1 : 0;
  invalidate();
});

captureButton.addEventListener('click', () => {
  hero.classList.remove('is-capturing');
  void hero.offsetWidth;
  hero.classList.add('is-capturing');
  targetRotationX -= .035;
  capturedFrames += 1;
  status.textContent = `Frame captured / ${String(capturedFrames).padStart(2, '0')}`;
  invalidate();
  setTimeout(() => {
    hero.classList.remove('is-capturing');
    targetRotationX = -.08;
    status.textContent = 'Realtime 3D / drag enabled';
    invalidate();
  }, 540);
});

function updateFromScroll() {
  if (reducedMotion || manualExplode) return;
  const anatomy = document.querySelector('#anatomy').getBoundingClientRect();
  targetExplode = Math.max(0, Math.min(1, 1 - anatomy.top / window.innerHeight));
  explodeButton.setAttribute('aria-pressed', String(targetExplode > .5));
  invalidate();
}

new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; if (visible) invalidate(); else cancelAnimationFrame(animationFrame); }, { rootMargin: '100px' }).observe(container);
document.addEventListener('visibilitychange', () => { if (!document.hidden && visible) invalidate(); else cancelAnimationFrame(animationFrame); });
window.addEventListener('resize', resize, { passive: true });
window.addEventListener('scroll', updateFromScroll, { passive: true });

window.addEventListener('beforeunload', () => {
  cancelAnimationFrame(animationFrame);
  parts.forEach((part) => { part.geometry.dispose(); part.material.dispose(); });
  renderer?.dispose();
});

async function boot() {
  try {
    THREE = await import('https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js');
    init();
  } catch (error) {
    canvas.hidden = true;
    poster.hidden = false;
    status.textContent = 'Static object / 3D unavailable';
    console.warn(error);
  }
}

boot();
