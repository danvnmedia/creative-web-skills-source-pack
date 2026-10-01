import { readFile, access } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const slugs = [
  'creative-web-studio', 'motion-choreographer', 'immersive-3d-web',
  'shader-web-art', 'creative-site-rebuilder', 'motion-performance-auditor',
  'accessible-interaction-systems',
];
const errors = [];
const descriptions = new Set();
const linkPattern = /\[[^\]]+\]\(([^)]+)\)/g;

async function exists(file) {
  try { await access(file); return true; } catch { return false; }
}

function frontmatter(text, file) {
  const block = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!block) { errors.push(`${file}: missing frontmatter`); return null; }
  const name = block[1].match(/^name:\s*["']?([^\r\n"']+)["']?\s*$/m)?.[1]?.trim();
  const line = block[1].match(/^description:\s*(.*)$/m);
  let description = line?.[1]?.trim() || '';
  if (description === '>-' || description === '|') {
    description = block[1].split(/\r?\n/).slice(2).filter((item) => /^\s{2,}\S/.test(item)).map((item) => item.trim()).join(' ');
  }
  return { name, description: description.replace(/^['"]|['"]$/g, '') };
}

async function checkLinks(file, skillRoot) {
  const content = await readFile(file, 'utf8');
  for (const [, raw] of content.matchAll(linkPattern)) {
    if (/^(?:https?:|mailto:|#)/i.test(raw)) continue;
    const href = decodeURIComponent(raw.split(/[?#]/, 1)[0].replace(/\s+".*"$/, ''));
    const target = path.resolve(path.dirname(file), href);
    if (target !== skillRoot && !target.startsWith(`${skillRoot}${path.sep}`)) {
      errors.push(`${path.relative(root, file)}: link escapes skill: ${raw}`);
    } else if (!(await exists(target))) {
      errors.push(`${path.relative(root, file)}: missing link: ${raw}`);
    }
  }
}

for (const slug of slugs) {
  const skillRoot = path.join(root, slug);
  const entry = path.join(skillRoot, 'SKILL.md');
  if (!(await exists(entry))) { errors.push(`${slug}: missing SKILL.md`); continue; }
  const meta = frontmatter(await readFile(entry, 'utf8'), entry);
  if (!meta) continue;
  if (meta.name !== slug) errors.push(`${slug}: frontmatter name mismatch`);
  if (meta.description.length < 70 || meta.description.length > 400) errors.push(`${slug}: description should identify a trigger and boundary in 70–400 characters`);
  if (descriptions.has(meta.description)) errors.push(`${slug}: duplicate description`);
  descriptions.add(meta.description);
  const agentMeta = path.join(skillRoot, 'agents', 'openai.yaml');
  if (!(await exists(agentMeta))) errors.push(`${slug}: missing agents/openai.yaml`);
  else {
    const yaml = await readFile(agentMeta, 'utf8');
    if (!/^\s*display_name:\s*\S+/m.test(yaml) || !/^\s*short_description:\s*\S+/m.test(yaml)) {
      errors.push(`${slug}: incomplete agent metadata`);
    }
  }
  await checkLinks(entry, skillRoot);
  const refs = path.join(skillRoot, 'references');
  if (!(await exists(refs))) errors.push(`${slug}: missing references directory`);
  else {
    const { readdir } = await import('node:fs/promises');
    for (const ref of await readdir(refs)) {
      if (ref.endsWith('.md')) await checkLinks(path.join(refs, ref), skillRoot);
    }
  }
}

const cases = JSON.parse(await readFile(path.join(root, 'scripts', 'skill-routing-cases.json'), 'utf8'));
const seen = new Set();
for (const item of cases) {
  if (!slugs.includes(item.expected) || !item.prompt?.trim()) errors.push('Routing case has an unknown skill or empty prompt');
  if (seen.has(item.prompt)) errors.push(`Duplicate routing prompt: ${item.prompt}`);
  seen.add(item.prompt);
}
for (const slug of slugs) {
  if (cases.filter((item) => item.expected === slug).length < 2) errors.push(`${slug}: fewer than two routing review cases`);
}

if (errors.length) {
  console.error(errors.map((error) => `- ${error}`).join('\n'));
  process.exitCode = 1;
} else {
  console.log(`Validated ${slugs.length} skill structures, metadata, relative reference links, and ${cases.length} routing review cases.`);
  console.log('Routing cases are review fixtures; live activation is not inferred.');
}
