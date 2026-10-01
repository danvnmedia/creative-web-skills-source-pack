let THREE;

const container = document.querySelector('#product-scene');
const canvas = container.querySelector('canvas');
const poster = document.querySelector('.product-poster');
const status = document.querySelector('#scene-status');
const resetButton = document.querySelector('#reset-view');
const explodeButton = document.querySelector('#toggle-explode');
const captureButton = document.querySelector('#capture');
const hero = document.querySelector('.instrument');
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
let previousFrame = 0;
let velocityX = 0;
let velocityY = 0;
let velocityExplode = 0;
let scrollFrame = 0;
let captureTimer;
const parts = [];

function syncExplodeControl(expanded) {
  explodeButton.setAttribute('aria-pressed', String(expanded));
  explodeButton.textContent = expanded ? 'Assemble camera' : 'Exploded view';
}

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
  const body = material(0x222523, .88, .12);
  const top = material(0xd7d4c9, .46, .62);
  const black = material(0x111616, .45, .38);
  const rubber = material(0x202726, .96, .02);
  const steel = material(0x909894, .34, .78);
  const red = material(0xe7523b, .38, .35);
  const glass = new THREE.MeshPhysicalMaterial({ color: 0x123b49, roughness: .06, metalness: .2, clearcoat: 1, clearcoatRoughness: .05 });

  addPart(new THREE.BoxGeometry(3.55, 2.08, 1.04), body, [0, -.04, 0], [-.65, 0, 0]);
  addPart(new THREE.BoxGeometry(3.5, .32, 1.09), top, [0, 1.1, 0], [-.65, .55, 0]);
  addPart(new THREE.BoxGeometry(3.48, .13, 1.08), steel, [0, -.98, 0], [-.65, -.2, 0]);
  addPart(new THREE.BoxGeometry(1.05, 1.48, .07), rubber, [1.2, -.12, .56], [-.65, 0, 0]);
  addPart(new THREE.BoxGeometry(.78, .48, .13), black, [1.15, .57, .59], [-.65, 0, 0]);
  addPart(new THREE.BoxGeometry(.59, .34, .23), black, [-1.06, 1.31, -.2], [-.3, .8, 0]);
  addPart(new THREE.BoxGeometry(3.42, 1.93, .12), black, [0, -.03, -.58], [1.2, 0, -1.1]);

  const dial1 = addPart(new THREE.CylinderGeometry(.38, .38, .19, 48), steel, [1.05, 1.38, 0], [.75, .72, 0]);
  const dial2 = addPart(new THREE.CylinderGeometry(.27, .27, .17, 48), black, [-1.17, 1.34, .03], [-.4, .7, 0]);
  dial1.rotation.y = .08; dial2.rotation.y = -.12;
  addPart(new THREE.CylinderGeometry(.12, .12, .13, 24), red, [.43, 1.42, 0], [.25, .74, 0]);

  addPart(new THREE.CylinderGeometry(.91, .91, .48, 64), steel, [-.27, -.09, .72], [0, 0, .45]).rotation.x = Math.PI / 2;
  addPart(new THREE.CylinderGeometry(.83, .81, .8, 64), black, [-.27, -.09, 1.32], [0, 0, 1.12]).rotation.x = Math.PI / 2;
  addPart(new THREE.CylinderGeometry(.76, .76, .24, 64), rubber, [-.27, -.09, 1.86], [0, 0, 1.62]).rotation.x = Math.PI / 2;
  addPart(new THREE.TorusGeometry(.78, .048, 12, 64), steel, [-.27, -.09, 1.76], [0, 0, 1.45]);
  addPart(new THREE.TorusGeometry(.7, .042, 12, 64), top, [-.27, -.09, 2.03], [0, 0, 1.72]);
  addPart(new THREE.CircleGeometry(.66, 64), glass, [-.27, -.09, 2.075], [0, 0, 1.78]);
  addPart(new THREE.CircleGeometry(.28, 64), material(0x071317, .1, .3), [-.27, -.09, 2.078], [0, 0, 1.78]);

  const labelCanvas = document.createElement('canvas');
  labelCanvas.width = 512; labelCanvas.height = 128;
  const labelContext = labelCanvas.getContext('2d');
  labelContext.fillStyle = '#222523'; labelContext.fillRect(0, 0, 512, 128);
  labelContext.fillStyle = '#e9e5d8'; labelContext.font = '600 48px monospace'; labelContext.fillText('KERN / ONE', 24, 84);
  const label = new THREE.Mesh(new THREE.PlaneGeometry(1.24, .31), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(labelCanvas) }));
  label.position.set(-1.05, .66, .567); product.add(label);
  product.rotation.set(targetRotationX, targetRotationY, 0);
}

function init() {
  if (!supportsWebGL) throw new Error('WebGL unavailable');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 720 ? 1.35 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(33, 1, .1, 100);
  camera.position.set(0, .2, 14);
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
  product.position.y = 0;
  camera.position.set(0, .18, box.width < 720 ? 12.2 : 10.5);
  camera.lookAt(0, 0, 0);
  camera.aspect = box.width / box.height;
  camera.updateProjectionMatrix();
  invalidate();
}

function spring(value, target, velocity, dt) {
  velocity = (velocity + (target - value) * 105 * dt) * Math.exp(-17 * dt);
  return [value + velocity * dt, velocity];
}

function update(now) {
  const dt = Math.min((now - (previousFrame || now)) / 1000, .05);
  previousFrame = now;
  revealProgress = Math.min(1, revealProgress + (reducedMotion ? 1 : dt / 1.1));
  const revealEase = 1 - Math.pow(1 - revealProgress, 3);
  product.scale.setScalar(.72 + revealEase * .28);
  if (reducedMotion) {
    product.rotation.x = targetRotationX;
    product.rotation.y = targetRotationY;
    explodeProgress = targetExplode;
  } else {
    [product.rotation.x, velocityX] = spring(product.rotation.x, targetRotationX, velocityX, dt);
    [product.rotation.y, velocityY] = spring(product.rotation.y, targetRotationY, velocityY, dt);
    [explodeProgress, velocityExplode] = spring(explodeProgress, targetExplode, velocityExplode, dt);
  }
  parts.forEach((part) => part.position.copy(part.userData.base).addScaledVector(part.userData.offset, explodeProgress));
}

function render(now = performance.now()) {
  if (!renderer || !visible || document.hidden) return;
  update(now);
  renderer.render(scene, camera);
  if (reducedMotion || revealProgress > .25) poster.hidden = true;
  if (revealProgress >= 1 && status.textContent === 'Assembling optical system') status.textContent = 'Realtime 3D / drag enabled';
  if (!reducedMotion && (revealProgress < 1 || dragging || Math.abs(product.rotation.x - targetRotationX) > .001 || Math.abs(product.rotation.y - targetRotationY) > .001 || Math.abs(explodeProgress - targetExplode) > .001 || Math.abs(velocityX) > .001 || Math.abs(velocityY) > .001 || Math.abs(velocityExplode) > .001)) {
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
function finishDrag(event) {
  dragging = false;
  if (container.hasPointerCapture(event.pointerId)) container.releasePointerCapture(event.pointerId);
  invalidate();
}
container.addEventListener('pointerup', finishDrag);
container.addEventListener('pointercancel', finishDrag);

resetButton.addEventListener('click', () => {
  targetRotationX = -.08;
  targetRotationY = -.35;
  targetExplode = 0;
  manualExplode = true;
  syncExplodeControl(false);
  invalidate();
});
explodeButton.addEventListener('click', () => {
  const expanded = explodeButton.getAttribute('aria-pressed') !== 'true';
  manualExplode = true;
  syncExplodeControl(expanded);
  targetExplode = expanded ? (container.clientWidth < 720 ? .55 : .8) : 0;
  invalidate();
});

captureButton.addEventListener('click', () => {
  clearTimeout(captureTimer);
  hero.classList.remove('is-capturing');
  requestAnimationFrame(() => hero.classList.add('is-capturing'));
  targetRotationX -= .035;
  capturedFrames += 1;
  status.textContent = `Frame captured / ${String(capturedFrames).padStart(2, '0')}`;
  invalidate();
  captureTimer = setTimeout(() => {
    hero.classList.remove('is-capturing');
    targetRotationX = -.08;
    status.textContent = 'Realtime 3D / drag enabled';
    invalidate();
  }, 540);
});

function updateFromScroll() {
  if (reducedMotion || manualExplode) return;
  const bounds = container.getBoundingClientRect();
  const progress = Math.max(0, Math.min(1, (window.innerHeight - bounds.top) / (window.innerHeight + bounds.height)));
  targetExplode = progress * (container.clientWidth < 720 ? .35 : .55);
  syncExplodeControl(targetExplode > .25);
  invalidate();
}

function scheduleScroll() {
  if (scrollFrame) return;
  scrollFrame = requestAnimationFrame(() => {
    scrollFrame = 0;
    updateFromScroll();
  });
}

new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; if (visible) invalidate(); else cancelAnimationFrame(animationFrame); }, { rootMargin: '100px' }).observe(container);
document.addEventListener('visibilitychange', () => { if (!document.hidden && visible) invalidate(); else cancelAnimationFrame(animationFrame); });
window.addEventListener('resize', resize, { passive: true });
window.addEventListener('scroll', scheduleScroll, { passive: true });
scheduleScroll();

window.addEventListener('beforeunload', () => {
  cancelAnimationFrame(animationFrame);
  cancelAnimationFrame(scrollFrame);
  clearTimeout(captureTimer);
  product?.traverse((object) => {
    if (!object.isMesh) return;
    object.geometry.dispose();
    object.material.map?.dispose();
    object.material.dispose();
  });
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
