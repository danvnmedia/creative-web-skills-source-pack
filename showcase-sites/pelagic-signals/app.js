const canvas = document.querySelector('#ocean-field');
const fallback = document.querySelector('.fallback-field');
const status = document.querySelector('#render-status');
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const metricLabel = document.querySelector('#metric-label');
const metricValue = document.querySelector('#metric-value');
const metricUnit = document.querySelector('#metric-unit');
const modeNote = document.querySelector('#mode-note');
const field = document.querySelector('.field');
const probe = document.querySelector('.depth-probe');
const probeDepth = document.querySelector('#probe-depth');
const probeFlow = document.querySelector('#probe-flow');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const modes = [
  { label: 'Surface velocity', value: '1.84', unit: 'm/s', note: 'Current vectors bend around density boundaries, revealing a westward return beneath the visible surface.' },
  { label: 'Thermal anomaly', value: '+2.7', unit: '°C', note: 'A warm filament folds north, carrying surface heat across a colder subsurface boundary.' },
  { label: 'Practical salinity', value: '35.6', unit: 'PSU', note: 'Fine salinity gradients expose the seam where coastal runoff meets the open Atlantic.' }
];

let gl;
let program;
let animationFrame;
let startTime = performance.now();
let activeMode = 0;
let fieldVisible = true;
let impulse = 0;
const pointer = { x: .72, y: .42 };

const vertexSource = `
  attribute vec2 aPosition;
  void main() { gl_Position = vec4(aPosition, 0.0, 1.0); }
`;
const fragmentSource = `
  precision highp float;
  uniform vec2 uResolution;
  uniform vec2 uPointer;
  uniform float uTime;
  uniform float uMode;
  uniform float uImpulse;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.,0.)), f.x), mix(hash(i + vec2(0.,1.)), hash(i + vec2(1.)), f.x), f.y);
  }
  float fbm(vec2 p) {
    float value = 0.0, amplitude = .52;
    for (int i = 0; i < 5; i++) { value += amplitude * noise(p); p = p * 2.03 + 7.1; amplitude *= .48; }
    return value;
  }
  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    vec2 p = (gl_FragCoord.xy * 2.0 - uResolution) / min(uResolution.x, uResolution.y);
    float time = uTime * .08;
    float pointerDistance = distance(uv, uPointer);
    float disturbance = .16 / (.12 + pointerDistance);
    vec2 flow = vec2(fbm(p * 1.5 + time), fbm(p * 1.45 - time + 8.2));
    float field = fbm(p * 2.2 + flow * 2.4 + disturbance * .08);
    float contour = smoothstep(.035, 0.0, abs(fract(field * 10.0 + uMode * .13) - .5) - .46);
    vec3 deep = vec3(.025, .10, .10);
    vec3 mint = vec3(.23, .92, .69);
    vec3 coral = vec3(1.0, .33, .24);
    vec3 color = mix(deep, uMode < .5 ? mint : coral, smoothstep(.42, .86, field) * .58);
    if (uMode > 1.5) color = mix(deep, vec3(.72, .88, .43), smoothstep(.38, .83, field) * .55);
    color += contour * (uMode < .5 ? mint : vec3(1.0,.72,.57)) * .42;
    color += smoothstep(.22, 0.0, distance(uv, uPointer)) * vec3(.15,.5,.38) * .2;
    float impulseRing = smoothstep(.035, 0.0, abs(pointerDistance - uImpulse * .46)) * (1.0 - uImpulse);
    color += impulseRing * vec3(.42,1.0,.82) * 1.4;
    gl_FragColor = vec4(color, 1.0);
  }
`;

function compile(type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
  return shader;
}

function initWebGL() {
  gl = canvas.getContext('webgl', { antialias: false, powerPreference: 'high-performance' });
  if (!gl) throw new Error('WebGL unavailable');
  program = gl.createProgram();
  gl.attachShader(program, compile(gl.VERTEX_SHADER, vertexSource));
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragmentSource));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, 'aPosition');
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
  fallback.hidden = true;
  status.textContent = reducedMotion ? 'Field paused / reduced motion' : 'Live field / WebGL';
  resize();
  render();
}

function resize() {
  if (!gl) return;
  const box = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.max(1, Math.round(box.width * dpr));
  canvas.height = Math.max(1, Math.round(box.height * dpr));
  gl.viewport(0, 0, canvas.width, canvas.height);
}

function render(now = startTime) {
  if (!gl) return;
  gl.uniform2f(gl.getUniformLocation(program, 'uResolution'), canvas.width, canvas.height);
  gl.uniform2f(gl.getUniformLocation(program, 'uPointer'), pointer.x, 1 - pointer.y);
  gl.uniform1f(gl.getUniformLocation(program, 'uTime'), reducedMotion ? 0 : (now - startTime) / 1000);
  gl.uniform1f(gl.getUniformLocation(program, 'uMode'), activeMode);
  gl.uniform1f(gl.getUniformLocation(program, 'uImpulse'), impulse);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
  if (impulse > 0) impulse = Math.max(0, impulse - .018);
  if (!reducedMotion && fieldVisible && !document.hidden) animationFrame = requestAnimationFrame(render);
}

function restartRender() {
  cancelAnimationFrame(animationFrame);
  render(performance.now());
}

canvas.addEventListener('pointermove', (event) => {
  const box = canvas.getBoundingClientRect();
  pointer.x = (event.clientX - box.left) / box.width;
  pointer.y = (event.clientY - box.top) / box.height;
  probe.style.left = `${(pointer.x * 100).toFixed(2)}%`;
  probe.style.top = `${(pointer.y * 100).toFixed(2)}%`;
  probe.classList.toggle('is-right', pointer.x > .64);
  probeDepth.textContent = `−${Math.round(42 + pointer.y * 536)} m`;
  probeFlow.textContent = `${(.62 + pointer.x * 1.84).toFixed(2)} m/s`;
  if (reducedMotion) render();
}, { passive: true });

canvas.addEventListener('pointerdown', () => {
  impulse = .01;
  field.classList.remove('is-pulsing');
  void field.offsetWidth;
  field.classList.add('is-pulsing');
  restartRender();
});

modeButtons.forEach((button) => button.addEventListener('click', () => {
  activeMode = Number(button.dataset.mode);
  modeButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
  const mode = modes[activeMode];
  metricLabel.textContent = mode.label;
  metricValue.textContent = mode.value;
  metricUnit.textContent = mode.unit;
  modeNote.textContent = mode.note;
  restartRender();
}));

new IntersectionObserver(([entry]) => {
  fieldVisible = entry.isIntersecting;
  if (fieldVisible && !document.hidden && !reducedMotion) restartRender();
  else cancelAnimationFrame(animationFrame);
}).observe(canvas);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && fieldVisible && !reducedMotion) restartRender();
  else cancelAnimationFrame(animationFrame);
});
window.addEventListener('resize', () => { resize(); restartRender(); }, { passive: true });

try { initWebGL(); } catch (error) {
  canvas.hidden = true;
  fallback.hidden = false;
  status.textContent = 'Static field / WebGL unavailable';
  console.warn(error);
}