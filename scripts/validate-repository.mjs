import { access, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const artifact = path.join(root, '.pages-dist');
const skills = [
  'creative-web-studio',
  'motion-choreographer',
  'immersive-3d-web',
  'shader-web-art',
  'creative-site-rebuilder',
  'motion-performance-auditor',
];
const showcases = ['morrow-archive', 'pelagic-signals', 'kern-one', 'asme-hero'];
const errors = [];

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

for (const slug of skills) {
  const file = path.join(root, slug, 'SKILL.md');
  if (!(await exists(file))) {
    errors.push(`Missing ${slug}/SKILL.md`);
    continue;
  }

  const markdown = await readFile(file, 'utf8');
  const frontmatter = markdown.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
  if (!frontmatter) {
    errors.push(`${slug}/SKILL.md has no YAML frontmatter`);
    continue;
  }
  if (!new RegExp(`^name:\\s*["']?${slug}["']?\\s*$`, 'm').test(frontmatter[1])) {
    errors.push(`${slug}/SKILL.md name must match its directory`);
  }
  if (!/^description:\s*\S+/m.test(frontmatter[1])) {
    errors.push(`${slug}/SKILL.md needs a non-empty description`);
  }
}

for (const route of [...skills, ...showcases]) {
  if (!(await exists(path.join(artifact, route, 'index.html')))) {
    errors.push(`Pages artifact is missing /${route}/`);
  }
}

for (const required of ['index.html', '404.html', '.nojekyll']) {
  if (!(await exists(path.join(artifact, required)))) {
    errors.push(`Pages artifact is missing ${required}`);
  }
}

async function htmlFiles(directory) {
  const output = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) output.push(...await htmlFiles(target));
    else if (entry.name.endsWith('.html')) output.push(target);
  }
  return output;
}

for (const htmlFile of await htmlFiles(artifact)) {
  const html = await readFile(htmlFile, 'utf8');
  const references = [...html.matchAll(/(?:href|src)=["']([^"']+)["']/gi)].map((match) => match[1]);
  for (const reference of references) {
    if (/^(?:https?:|mailto:|tel:|data:|#|javascript:)/i.test(reference)) continue;
    const clean = decodeURIComponent(reference.split(/[?#]/, 1)[0]);
    if (!clean) continue;
    const target = clean.startsWith('/')
      ? path.join(artifact, clean.replace(/^\/creative-web-skills-source-pack\/?/, ''))
      : path.resolve(path.dirname(htmlFile), clean);
    const resolved = path.extname(target) ? target : path.join(target, 'index.html');
    if (!(await exists(resolved))) {
      errors.push(`${path.relative(artifact, htmlFile)} references missing ${reference}`);
    }
  }
}

if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join('\n'));
  process.exitCode = 1;
} else {
  console.log(`Validated ${skills.length} skills, ${showcases.length} showcases, and all local Pages links.`);
}

