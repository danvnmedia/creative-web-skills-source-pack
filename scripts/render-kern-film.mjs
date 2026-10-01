// Render the first-party Kern optical study from its deterministic Three.js scene.
// Run while `npm run dev` serves the built showcase on port 4173.
import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';

const frames = resolve('.ai/evidence/browser/kern-optical-film-20260930');
const output = resolve('showcase-sites/kern-one/assets');
await mkdir(frames, { recursive: true });
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:4173/kern-one/film-stage.html', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.filmReady === true, { timeout: 30000 });
  for (let frame = 0; frame < 96; frame++) {
    await page.evaluate((time) => window.setFilmTime(time), frame / 24);
    await page.screenshot({ path: resolve(frames, `frame-${String(frame).padStart(4, '0')}.png`) });
    if (frame % 24 === 0) process.stdout.write(`Rendered ${frame}/96 frames\n`);
  }
} finally {
  await browser.close();
}
const encode = spawnSync('ffmpeg.exe', [
  '-y', '-framerate', '24', '-i', resolve(frames, 'frame-%04d.png'),
  '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p',
  '-movflags', '+faststart', resolve(output, 'optical-sequence.mp4'),
], { stdio: 'inherit' });
if (encode.status !== 0) throw new Error('ffmpeg video encoding failed');
const poster = spawnSync('magick.exe', [resolve(frames, 'frame-0030.png'), '-quality', '84', resolve(output, 'optical-poster.webp')], { stdio: 'inherit' });
if (poster.status !== 0) throw new Error('Poster export failed');
process.stdout.write('Kern optical film and poster exported.\n');
