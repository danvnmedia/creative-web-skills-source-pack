const canvas = document.querySelector('#ocean-field');
const image = document.querySelector('.field-image');
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
let texture;
let animationFrame;
let startTime = performance.now();
let activeMode = 0;
let fieldVisible = true;
let impulse = -1;
let renderScale = Math.min(window.devicePixelRatio || 1, window.innerWidth < 720 ? .95 : 1.15);
let lastRenderAt = 0;
let sampledFrames = 0;
let sampledTime = 0;
let uniforms;
let canvasBounds;
const pointer = { x: .72, y: .42 };

const vertexSource = `
  attribute vec2 aPosition;
  void main() { gl_Position = vec4(aPosition, 0.0, 1.0); }
`;
const fragmentSource = `
  precision highp float;
  uniform sampler2D uTexture;
  uniform vec2 uResolution;
  uniform vec2 uPointer;
  uniform float uTime;
  uniform float uMode;
  uniform float uImpulse;

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float aspect = uResolution.x / uResolution.y;
    vec2 p = (uv - .5) * vec2(aspect, 1.0);
    float t = uTime;
    float swell = sin(p.x * 11.0 + p.y * 4.0 - t * .72);
    float crossSwell = sin(p.y * 17.0 - p.x * 3.0 + sin(p.x * 6.0 + t * .43) * 1.5 + t * .61);
    vec2 warp = vec2(swell * .008 + crossSwell * .004, sin(p.x * 8.0 + t * .5) * .007 + crossSwell * .003);
    vec2 fromPointer = (uv - uPointer) * vec2(aspect, 1.0);
    float pointerDistance = length(fromPointer);
    float influence = exp(-pointerDistance * pointerDistance * 25.0);
    warp += normalize(fromPointer + vec2(.0001)) * influence * sin(pointerDistance * 38.0 - t * 4.0) * .013;
    float ring = 0.0;
    if (uImpulse >= 0.0) {
      ring = exp(-pow((pointerDistance - uImpulse * .57) * 45.0, 2.0)) * (1.0 - uImpulse);
      warp += normalize(fromPointer + vec2(.0001)) * ring * .03;
    }
    vec3 color = texture2D(uTexture, clamp(uv + warp, .001, .999)).rgb;
    float luminance = dot(color, vec3(.2126, .7152, .0722));
    float ribbons = pow(max(0.0, sin(p.x * 26.0 + sin(p.y * 13.0 - t * .8) * 2.2 - t * 1.2)), 18.0);
    float glint = ribbons * smoothstep(.12, .48, luminance) * .1;
    vec3 signal = vec3(.35, .95, 1.0);
    if (uMode > .5 && uMode < 1.5) {
      color = mix(color, vec3(.13, .022, .048) + luminance * vec3(1.8, .58, .22), .64);
      signal = vec3(1.0, .58, .34);
    } else if (uMode > 1.5) {
      color = mix(color, vec3(.055, .035, .19) + luminance * vec3(.94, .78, 1.35), .58);
      signal = vec3(.72, .72, 1.0);
    }
    color += signal * (glint + ring * .65 + influence * .018);
    color *= 1.0 - .2 * smoothstep(.28, .8, length(p));
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
  uniforms = Object.fromEntries(['uTexture', 'uResolution', 'uPointer', 'uTime', 'uMode', 'uImpulse'].map((name) => [name, gl.getUniformLocation(program, name)]));
  texture = gl.createTexture();
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
  gl.uniform1i(uniforms.uTexture, 0);
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, 'aPosition');
  gl.enableVertexAttribArray(position);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
  status.textContent = reducedMotion ? 'Field paused / reduced motion' : 'Simulated field / WebGL';
  resize();
  render();
}

function resize() {
  if (!gl) return;
  const box = canvas.getBoundingClientRect();
  canvasBounds = { left: box.left + window.scrollX, top: box.top + window.scrollY, width: box.width, height: box.height };
  canvas.width = Math.max(1, Math.round(box.width * renderScale));
  canvas.height = Math.max(1, Math.round(box.height * renderScale));
  gl.viewport(0, 0, canvas.width, canvas.height);
}

function render(now = startTime) {
  if (!gl) return;
  const delta = lastRenderAt ? Math.min(.05, (now - lastRenderAt) / 1000) : .016;
  if (!reducedMotion && lastRenderAt && now - lastRenderAt < 100) {
    sampledTime += now - lastRenderAt;
    sampledFrames += 1;
    if (sampledFrames >= 40) {
      if (sampledTime / sampledFrames > 20 && renderScale > .7) {
        renderScale = Math.max(.7, renderScale - .15);
        resize();
      }
      sampledTime = 0;
      sampledFrames = 0;
    }
  }
  lastRenderAt = now;
  gl.uniform2f(uniforms.uResolution, canvas.width, canvas.height);
  gl.uniform2f(uniforms.uPointer, pointer.x, 1 - pointer.y);
  gl.uniform1f(uniforms.uTime, reducedMotion ? 0 : (now - startTime) / 1000);
  gl.uniform1f(uniforms.uMode, activeMode);
  gl.uniform1f(uniforms.uImpulse, impulse);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
  if (impulse >= 0) {
    impulse += delta / 1.1;
    if (impulse >= 1) impulse = -1;
  }
  if (!reducedMotion && fieldVisible && !document.hidden) animationFrame = requestAnimationFrame(render);
}

function restartRender() {
  cancelAnimationFrame(animationFrame);
  render(performance.now());
}

let pointerFrame = 0;
let nextPointer;
canvas.addEventListener('pointermove', (event) => {
  nextPointer = { x: event.clientX, y: event.clientY };
  if (pointerFrame) return;
  pointerFrame = requestAnimationFrame(() => {
    pointer.x = Math.max(0, Math.min(1, (nextPointer.x + window.scrollX - canvasBounds.left) / canvasBounds.width));
    pointer.y = Math.max(0, Math.min(1, (nextPointer.y + window.scrollY - canvasBounds.top) / canvasBounds.height));
    probe.style.left = '0';
    probe.style.top = '0';
    probe.style.transform = `translate3d(${(pointer.x * canvasBounds.width).toFixed(1)}px, ${(pointer.y * canvasBounds.height).toFixed(1)}px, 0) translate(-50%, -50%)`;
    probe.classList.toggle('is-right', pointer.x > .64);
    probeDepth.textContent = `−${Math.round(42 + pointer.y * 536)} m`;
    probeFlow.textContent = `${(.62 + pointer.x * 1.84).toFixed(2)} m/s`;
    if (reducedMotion) render();
    pointerFrame = 0;
  });
}, { passive: true });

canvas.addEventListener('pointerdown', () => {
  impulse = reducedMotion ? -1 : 0;
  field.classList.remove('is-pulsing');
  requestAnimationFrame(() => field.classList.add('is-pulsing'));
  restartRender();
});

modeButtons.forEach((button) => button.addEventListener('click', () => {
  activeMode = Number(button.dataset.mode);
  field.dataset.mode = button.dataset.mode;
  modeButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
  const mode = modes[activeMode];
  const updateMetric = () => {
    metricLabel.textContent = mode.label;
    metricValue.textContent = mode.value;
    metricUnit.textContent = mode.unit;
    modeNote.textContent = mode.note;
  };
  if (!reducedMotion && document.startViewTransition) document.startViewTransition(updateMetric);
  else updateMetric();
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

async function boot() {
  try {
    await image.decode();
    initWebGL();
  } catch (error) {
    canvas.hidden = true;
    status.textContent = 'Static field / WebGL unavailable';
    console.warn(error);
  }
}

boot();
