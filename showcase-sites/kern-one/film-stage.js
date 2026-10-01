// Deterministic source scene for the first-party optical-sequence.mp4 loop.
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.179.1/build/three.module.js';

const canvas = document.querySelector('#film');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.65;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x060b11);
const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, .1, 40);
camera.position.set(0, 0, 7.9);

scene.add(new THREE.AmbientLight(0x39536b, 1.15));
const key = new THREE.PointLight(0xe9f5ef, 120, 18); key.position.set(-3.5, 4.5, 5); scene.add(key);
const blue = new THREE.PointLight(0x3ac9f7, 95, 13); blue.position.set(3.4, -1, 3.2); scene.add(blue);
const warm = new THREE.PointLight(0xf86a42, 65, 12); warm.position.set(-3, -3, -1.5); scene.add(warm);

const rig = new THREE.Group();
rig.rotation.set(-.12, .32, -.18);
scene.add(rig);
const moving = [];
const titanium = new THREE.MeshPhysicalMaterial({ color: 0xc2ced0, metalness: .88, roughness: .23, clearcoat: .35 });
const graphite = new THREE.MeshPhysicalMaterial({ color: 0x151c22, metalness: .73, roughness: .32, clearcoat: .3 });
const graphiteEdge = new THREE.MeshPhysicalMaterial({ color: 0x4d5960, metalness: .95, roughness: .2 });
const copper = new THREE.MeshPhysicalMaterial({ color: 0xe36a47, metalness: .76, roughness: .26 });
const glass = new THREE.MeshPhysicalMaterial({ color: 0x5bc5e1, metalness: .15, roughness: .04, transmission: .64, thickness: .42, clearcoat: 1, transparent: true, opacity: .92, side: THREE.DoubleSide });
const frontGlassMaterial = new THREE.MeshPhysicalMaterial({ color: 0x102f41, metalness: .3, roughness: .045, transmission: .25, thickness: .25, clearcoat: 1, transparent: true, opacity: .96, side: THREE.DoubleSide });

function add(geometry, material, z, offset = 0) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.z = z;
  mesh.userData.z = z;
  mesh.userData.offset = offset;
  rig.add(mesh);
  if (offset) moving.push(mesh);
  return mesh;
}
function ring(radius, tube, z, material, offset) {
  return add(new THREE.TorusGeometry(radius, tube, 16, 96), material, z, offset);
}
function sleeve(radius, depth, z, material, offset) {
  const mesh = add(new THREE.CylinderGeometry(radius, radius, depth, 96, 1, true), material, z, offset);
  mesh.rotation.x = Math.PI / 2;
  return mesh;
}

sleeve(1.31, .42, -.78, graphite, -1.12);
ring(1.31, .08, -.98, titanium, -1.12);
ring(1.34, .035, -.58, copper, -1.12);
sleeve(1.39, .55, -.12, graphite, -.3);
ring(1.39, .1, -.4, graphiteEdge, -.3);
ring(1.4, .075, .18, titanium, -.3);
sleeve(1.22, .32, .48, titanium, .5);
ring(1.24, .095, .65, graphiteEdge, .5);
ring(1.05, .032, .72, copper, .5);
ring(.91, .07, 1.04, graphite, 1.18);
ring(.84, .024, 1.1, titanium, 1.18);

const rearGlass = add(new THREE.SphereGeometry(1, 64, 32), glass, -.68, -.82);
rearGlass.scale.set(1.09, 1.09, .19);
const midGlass = add(new THREE.SphereGeometry(1, 64, 32), glass, .23, .25);
midGlass.scale.set(1.17, 1.17, .22);
const frontGlass = add(new THREE.SphereGeometry(1, 64, 32), frontGlassMaterial, 1.01, 1.28);
frontGlass.scale.set(.84, .84, .17);
add(new THREE.CircleGeometry(.48, 64), new THREE.MeshBasicMaterial({ color: 0x020b13 }), 1.195, 1.28);
ring(.52, .018, 1.2, copper, 1.28);
ring(.33, .009, 1.205, titanium, 1.28);
ring(.16, .007, 1.21, new THREE.MeshBasicMaterial({ color: 0x69d2f5 }), 1.28);

const aperture = add(new THREE.CircleGeometry(.76, 64), new THREE.MeshBasicMaterial({ color: 0x02070b, side: THREE.DoubleSide }), -.79, -.8);
for (let i = 0; i < 7; i++) {
  const blade = new THREE.Mesh(new THREE.CircleGeometry(.48, 3), graphiteEdge);
  blade.position.set(Math.cos(i * Math.PI * 2 / 7) * .23, Math.sin(i * Math.PI * 2 / 7) * .23, .01);
  blade.rotation.z = i * Math.PI * 2 / 7 + .4;
  aperture.add(blade);
}

const knurl = new THREE.Group();
knurl.position.z = -.12;
knurl.userData.z = -.12;
knurl.userData.offset = -.3;
rig.add(knurl);
moving.push(knurl);
const tooth = new THREE.BoxGeometry(.045, .085, .52);
for (let i = 0; i < 88; i++) {
  const angle = i * Math.PI * 2 / 88;
  const mesh = new THREE.Mesh(tooth, graphiteEdge);
  mesh.position.set(Math.cos(angle) * 1.4, Math.sin(angle) * 1.4, 0);
  mesh.rotation.z = angle;
  knurl.add(mesh);
}

const halo = new THREE.Group();
scene.add(halo);
for (const radius of [2.1, 2.53, 3.05]) {
  const arc = new THREE.Mesh(new THREE.TorusGeometry(radius, .006, 4, 128), new THREE.MeshBasicMaterial({ color: 0x456172, transparent: true, opacity: .25 }));
  halo.add(arc);
}
const rayMaterial = new THREE.LineBasicMaterial({ color: 0xa8e8f4, transparent: true, opacity: 0 });
const rayPositions = new Float32Array([-3.2, 0, -2.3, 3.2, 0, 2.9, -3.2, .13, -2.3, 3.2, .13, 2.9, -3.2, -.13, -2.3, 3.2, -.13, 2.9]);
const rayGeometry = new THREE.BufferGeometry();
rayGeometry.setAttribute('position', new THREE.BufferAttribute(rayPositions, 3));
const rays = new THREE.LineSegments(rayGeometry, rayMaterial);
scene.add(rays);

function setFilmTime(seconds) {
  const phase = (seconds / 4) * Math.PI * 2;
  const open = (1 - Math.cos(phase)) * .5;
  for (const mesh of moving) mesh.position.z = mesh.userData.z + mesh.userData.offset * open;
  rig.rotation.y = .32 + Math.sin(phase) * .24;
  rig.rotation.x = -.12 + Math.sin(phase + .8) * .07;
  rig.rotation.z = -.18 + Math.sin(phase) * .035;
  rig.scale.setScalar(1 + Math.sin(phase) * .025);
  halo.rotation.z = phase * .16;
  rayMaterial.opacity = open * .38;
  blue.intensity = 95 + Math.sin(phase) * 18;
  renderer.render(scene, camera);
}

window.setFilmTime = setFilmTime;
window.filmReady = true;
setFilmTime(0);
