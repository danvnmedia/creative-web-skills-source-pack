import assert from 'node:assert/strict';
import { mkdir, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const baseUrl = process.env.SHOWCASE_URL || 'http://127.0.0.1:4173';
const output = path.resolve(process.argv[2] || '.ai/evidence/browser/TASK-CREATIVE-001');
await mkdir(output, { recursive: true });
assert.equal((await readdir(output)).length, 0, `Output must be fresh: ${output}`);

const routes = ['', 'morrow-archive', 'pelagic-signals', 'kern-one', 'asme-hero'];
const variants = [
  { name: 'desktop', width: 1440, height: 900, reducedMotion: 'no-preference' },
  { name: 'mobile', width: 390, height: 844, reducedMotion: 'no-preference' },
  { name: 'mobile-reduced', width: 390, height: 844, reducedMotion: 'reduce' },
];
const report = { baseUrl, output, startedAt: new Date().toISOString(), results: [], summary: { cases: 0, failures: 0 } };
const browser = await chromium.launch({ headless: true });

async function checkFlow(page, route, reduced) {
  if (!route) {
    for (const slug of ['morrow-archive', 'pelagic-signals', 'kern-one', 'asme-hero']) {
      assert.equal(await page.locator(`.project-link[href="./${slug}/"]`).count(), 1);
    }
  }
  if (route === 'morrow-archive') {
    await page.getByRole('button', { name: /Index/ }).click();
    assert.equal(await page.locator('.menu-panel').isVisible(), true);
    await page.getByRole('link', { name: 'I. The held breath' }).press('Escape');
    assert.equal(await page.locator('.menu-panel').isVisible(), false);
    if (reduced) assert.equal(await page.locator('.opening-curtain').evaluate((el) => getComputedStyle(el).display), 'none');
  }
  if (route === 'pelagic-signals') {
    await page.getByRole('button', { name: /Thermal/ }).click();
    await page.waitForFunction(() => document.querySelector('#metric-value')?.textContent === '+2.7');
    assert.equal(await page.getByRole('button', { name: /Thermal/ }).getAttribute('aria-pressed'), 'true');
    if (reduced) assert.match(await page.locator('#render-status').innerText(), /paused|unavailable/i);
  }
  if (route === 'kern-one') {
    await page.locator('#optical-film').scrollIntoViewIfNeeded();
    await page.waitForFunction(() => document.querySelector('#optical-video')?.readyState >= 2, null, { timeout: 12000 });
    if (reduced) {
      assert.equal(await page.locator('#optical-video').evaluate((video) => video.paused), true);
      assert.equal(await page.locator('#film-toggle').isDisabled(), true);
    } else {
      await page.waitForFunction(() => !document.querySelector('#optical-video')?.paused, null, { timeout: 12000 });
      await page.getByRole('button', { name: 'Pause optical film' }).click();
      assert.equal(await page.locator('#optical-video').evaluate((video) => video.paused), true);
      await page.getByRole('button', { name: 'Play optical film' }).click();
      assert.equal(await page.locator('#optical-video').evaluate((video) => video.paused), false);
    }
    await page.locator('#product-scene').scrollIntoViewIfNeeded();
    await page.waitForFunction(() => /Realtime|Static object|3D ready/.test(document.querySelector('#scene-status')?.textContent || ''), null, { timeout: 12000 });
    await page.locator('#reset-view').click();
    await page.locator('#toggle-explode').click();
    assert.equal(await page.locator('#toggle-explode').getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('#toggle-explode').innerText(), /assemble camera/i);
    await page.getByRole('button', { name: 'Trigger camera shutter' }).click();
    assert.match(await page.locator('#scene-status').innerText(), /Frame captured/i);
  }
  if (route === 'asme-hero') {
    await page.getByRole('button', { name: /Blue hour, inland/ }).click();
    assert.equal(await page.getByRole('button', { name: /Blue hour, inland/ }).getAttribute('aria-pressed'), 'true');
    assert.match(await page.locator('.selection p').innerText(), /ridgelines/);
    await page.getByRole('button', { name: 'After dark' }).click();
    await page.waitForFunction(() => document.querySelector('main')?.classList.contains('phase-night'));
    assert.equal(await page.locator('video').count(), 0);
  }
}

for (const variant of variants) {
  const context = await browser.newContext({ viewport: { width: variant.width, height: variant.height }, reducedMotion: variant.reducedMotion });
  for (const route of routes) {
    const routeName = route || 'hub';
    const page = await context.newPage();
    const result = { route: routeName, variant: variant.name, heading: null, scrollWidth: null, consoleErrors: [], pageErrors: [], httpErrors: [], requestFailures: [], expectedMediaAborts: [], screenshot: null, passed: false, error: null };
    page.on('console', (message) => { if (message.type() === 'error') result.consoleErrors.push(message.text()); });
    page.on('pageerror', (error) => result.pageErrors.push(String(error)));
    page.on('response', (response) => { if (response.status() >= 400) result.httpErrors.push({ url: response.url(), status: response.status(), local: response.url().startsWith(baseUrl) }); });
    page.on('requestfailed', (request) => result.requestFailures.push({ url: request.url(), failure: request.failure()?.errorText, local: request.url().startsWith(baseUrl) }));
    try {
      const response = await page.goto(`${baseUrl}/${route ? `${route}/` : ''}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.equal(response?.status(), 200);
      await page.waitForTimeout(route === 'morrow-archive' ? 1600 : 1200);
      result.heading = await page.locator('h1').first().innerText();
      assert.ok(result.heading.trim());
      result.scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      assert.ok(result.scrollWidth <= variant.width + 1, `horizontal overflow: ${result.scrollWidth} > ${variant.width}`);
      await checkFlow(page, route, variant.reducedMotion === 'reduce');
      for (const section of await page.locator('main section').all()) await section.scrollIntoViewIfNeeded();
      await page.evaluate(() => window.scrollTo(0, 0));
      const brokenImages = await page.locator('img').evaluateAll((images) => images.filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.currentSrc));
      assert.deepEqual(brokenImages, [], 'broken local image');
      await page.waitForTimeout(300);
      result.screenshot = path.join(output, `${routeName}-${variant.name}.png`);
      await page.screenshot({ path: result.screenshot, fullPage: true, animations: 'disabled' });
      assert.equal(result.pageErrors.length, 0, `page errors: ${result.pageErrors.join('; ')}`);
      assert.equal(result.consoleErrors.length, 0, `console errors: ${result.consoleErrors.join('; ')}`);
      assert.equal(result.httpErrors.filter((entry) => entry.local).length, 0, 'local HTTP error');
      // Chromium can cancel a video range request after enough bytes were buffered.
      // checkFlow already proved the film loaded and, when motion is allowed, played.
      const expectedMediaAbort = (entry) => route === 'kern-one'
        && entry.url === `${baseUrl}/kern-one/assets/optical-sequence.mp4`
        && entry.failure === 'net::ERR_ABORTED';
      result.expectedMediaAborts = result.requestFailures.filter(expectedMediaAbort);
      assert.equal(result.requestFailures.filter((entry) => entry.local && !expectedMediaAbort(entry)).length, 0, 'local request failure');
      result.passed = true;
    } catch (error) { result.error = String(error); report.summary.failures++; }
    report.results.push(result);
    report.summary.cases++;
    await page.close();
    console.log(`${result.passed ? 'PASS' : 'FAIL'} ${routeName} ${variant.name}${result.error ? ` — ${result.error}` : ''}`);
  }
  await context.close();
}
await browser.close();
report.finishedAt = new Date().toISOString();
await writeFile(path.join(output, 'browser-report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report.summary));
process.exitCode = report.summary.failures ? 1 : 0;
