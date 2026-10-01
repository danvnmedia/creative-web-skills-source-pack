import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const source = path.join(root, 'showcase-sites');
const output = path.join(root, '.pages-dist');
const repositoryUrl = 'https://github.com/danvnmedia/creative-web-skills-source-pack';

const skills = [
  {
    slug: 'creative-web-studio',
    title: 'Creative Web Studio',
    eyebrow: 'Direction / orchestration / architecture',
    description: 'Direct an idea, brand, reference, or existing codebase into one coherent, art-directed web experience.',
    capabilities: ['Experience thesis and scene planning', 'Rendering boundaries and stack selection', 'Mobile and reduced-motion variants', 'Budgets, acceptance criteria, and handoff packets'],
    prompts: ['$creative-web-studio turn this product brief into a cinematic launch experience.', '$creative-web-studio redesign this landing page with a clear scene system and production budget.'],
  },
  {
    slug: 'motion-choreographer',
    title: 'Motion Choreographer',
    eyebrow: 'Motion / scroll / interaction',
    description: 'Design and implement a purposeful motion language across native CSS, WAAPI, GSAP, Motion, Lenis, and route transitions.',
    capabilities: ['Microinteractions and reveal systems', 'Scroll-triggered and scroll-linked motion', 'FLIP and shared-layout continuity', 'Cleanup, input parity, and reduced motion'],
    prompts: ['$motion-choreographer make this hero feel cinematic without adding 3D.', '$motion-choreographer refactor these scroll effects into one maintainable motion system.'],
  },
  {
    slug: 'immersive-3d-web',
    title: 'Immersive 3D Web',
    eyebrow: 'Three.js / R3F / spatial stories',
    description: 'Build real-time 3D experiences where depth, viewpoint, material, or direct object manipulation carries the idea.',
    capabilities: ['Three.js and React Three Fiber architecture', 'glTF, materials, lighting, and cameras', 'Product explode and assembly sequences', 'Adaptive DPR, disposal, and static fallbacks'],
    prompts: ['$immersive-3d-web build an interactive product viewer with a useful mobile fallback.', '$immersive-3d-web diagnose this R3F scene and reduce GPU cost.'],
  },
  {
    slug: 'shader-web-art',
    title: 'Shader Web Art',
    eyebrow: 'GLSL / WebGL / GPU effects',
    description: 'Create concept-led shader effects, particles, image transitions, and DOM-to-WebGL compositions without generic visual noise.',
    capabilities: ['Displacement, masks, refraction, and feedback', 'Particles and procedural fields', 'DOM-aligned image and video planes', 'WebGL fallbacks and optional WebGPU paths'],
    prompts: ['$shader-web-art create a restrained refraction transition for this editorial gallery.', '$shader-web-art synchronize these DOM cards with WebGL image planes.'],
  },
  {
    slug: 'creative-site-rebuilder',
    title: 'Creative Site Rebuilder',
    eyebrow: 'Analysis / reconstruction / originality',
    description: 'Study a URL, screenshot, recording, or frontend and translate its underlying design logic into an original implementation.',
    capabilities: ['Reference decomposition and interaction inference', 'Originality and IP boundaries', 'Responsive reconstruction', 'Evidence-led implementation planning'],
    prompts: ['$creative-site-rebuilder study this URL and rebuild the interaction principles in our brand.', '$creative-site-rebuilder infer the responsive system from these screenshots.'],
  },
  {
    slug: 'motion-performance-auditor',
    title: 'Motion Performance Auditor',
    eyebrow: 'Performance / accessibility / QA',
    description: 'Audit creative frontends for jank, rendering cost, lifecycle leaks, responsiveness, accessibility, and launch risk.',
    capabilities: ['Core Web Vitals and critical-path review', 'Animation and scroll lifecycle checks', 'WebGL resource and render-loop analysis', 'Mobile, input, and reduced-motion evidence'],
    prompts: ['$motion-performance-auditor audit this site before launch and rank findings by user impact.', '$motion-performance-auditor inspect this Three.js route for frame-time and cleanup risks.'],
  },
  {
    slug: 'accessible-interaction-systems',
    title: 'Accessible Interaction Systems',
    eyebrow: 'Components / semantics / state',
    description: 'Create distinctive reusable controls whose keyboard, touch, focus, and reduced-motion behavior remain coherent.',
    capabilities: ['Semantic states and input parity', 'Visual tokens and component contracts', 'Motion with direct state fallback', 'Keyboard, touch, contrast, and mobile checks'],
    prompts: ['$accessible-interaction-systems build an accessible gallery filter with a quiet view transition.', '$accessible-interaction-systems audit this component set for focus and touch parity.'],
  },
];

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}

function renderSkill(skill, description) {
  const capabilities = skill.capabilities.map((item, index) => `<li><span>0${index + 1}</span>${escapeHtml(item)}</li>`).join('');
  const prompts = skill.prompts.map((prompt) => `<pre><code>${escapeHtml(prompt)}</code></pre>`).join('');
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="${escapeHtml(description)}">
  <meta name="theme-color" content="#11110f">
  <title>${escapeHtml(skill.title)} — Creative Web Skills Pack</title>
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../skill-pages.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../"><span>CW</span> Skills</a>
    <nav aria-label="Skill navigation"><a href="../#skills">All skills</a><a href="../#showcases">Live showcases</a></nav>
  </header>
  <main>
    <section class="hero">
      <p class="eyebrow">${escapeHtml(skill.eyebrow)}</p>
      <h1>${escapeHtml(skill.title)}</h1>
      <p class="lede">${escapeHtml(skill.description)}</p>
      <div class="actions"><a class="primary" href="${repositoryUrl}/blob/main/${skill.slug}/SKILL.md">Read the full SKILL.md ↗</a><a href="${repositoryUrl}/tree/main/${skill.slug}">Browse source</a></div>
    </section>
    <section class="capabilities" aria-labelledby="capabilities-title">
      <div><p class="eyebrow">What it owns</p><h2 id="capabilities-title">A focused production role.</h2></div>
      <ol>${capabilities}</ol>
    </section>
    <section class="prompts" aria-labelledby="prompts-title">
      <p class="eyebrow">Try it in Codex</p>
      <h2 id="prompts-title">Start with a direct invocation.</h2>
      <div class="prompt-grid">${prompts}</div>
      <p class="note">Install the skill, then paste one of these prompts into Codex. The skill can also trigger automatically when your request matches its description.</p>
    </section>
  </main>
  <footer><span>${escapeHtml(skill.title)}</span><a href="../">Creative Web Skills Pack ↑</a></footer>
</body>
</html>`;
}

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(source, output, { recursive: true });
const candidate = process.env.GITHUB_SHA || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
if (!/^[0-9a-f]{40}$/i.test(candidate)) throw new Error('A full Git revision is required for the Pages build');
const hubPath = path.join(output, 'index.html');
const hub = await readFile(hubPath, 'utf8');
if (!hub.includes('name="build-revision" content="local-source"')) throw new Error('Hub revision marker is missing');
await writeFile(hubPath, hub.replace('name="build-revision" content="local-source"', `name="build-revision" content="${candidate}"`), 'utf8');
await writeFile(path.join(output, 'revision.json'), JSON.stringify({ revision: candidate }, null, 2) + '\n', 'utf8');
await writeFile(path.join(output, '.nojekyll'), '', 'utf8');

for (const skill of skills) {
  const markdown = await readFile(path.join(root, skill.slug, 'SKILL.md'), 'utf8');
  if (!new RegExp(`^name:\\s*["']?${skill.slug}["']?\\s*$`, 'm').test(markdown)) {
    throw new Error(`Skill metadata mismatch: ${skill.slug}`);
  }
  const route = path.join(output, skill.slug);
  await mkdir(route, { recursive: true });
  await writeFile(path.join(route, 'index.html'), renderSkill(skill, skill.description), 'utf8');
}

await writeFile(path.join(output, '404.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found — Creative Web Skills Pack</title><style>body{margin:0;display:grid;place-items:center;min-height:100vh;background:#11110f;color:#f4f1e8;font:16px system-ui}main{max-width:36rem;padding:3rem}h1{font:clamp(3rem,10vw,7rem)/.9 Georgia,serif}a{color:#d7ff3f}</style><main><p>404 / FIELD NOTE</p><h1>This route left the frame.</h1><p><a href="/creative-web-skills-source-pack/">Return to the Creative Web Skills Pack →</a></p></main></html>`, 'utf8');

console.log(`Built ${skills.length} skill routes and ${output}`);
