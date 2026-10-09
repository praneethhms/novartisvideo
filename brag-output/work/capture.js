// Usage: node capture.js stills t1,t2,...   |   node capture.js frames
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'video.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => Promise.all([...document.images].map(i => i.complete ? 1 : new Promise(r => { i.onload = i.onerror = r; }))));
  const shot = async (t, file) => {
    await page.evaluate(t => window.render(t), t);
    await page.screenshot({ path: file, type: mode === 'frames' ? 'jpeg' : 'png', quality: mode === 'frames' ? 95 : undefined });
  };
  if (mode === 'stills') {
    fs.mkdirSync(path.join(__dirname, 'stills'), { recursive: true });
    for (const t of process.argv[3].split(',').map(Number)) await shot(t, path.join(__dirname, 'stills', `t${t.toFixed(2)}.png`));
  } else {
    const dir = path.join(__dirname, 'frames');
    fs.mkdirSync(dir, { recursive: true });
    const dur = await page.evaluate(() => window.DURATION);
    const n = Math.round(dur * 30);
    for (let i = 0; i < n; i++) await shot(i / 30, path.join(dir, `f${String(i).padStart(4, '0')}.jpg`));
    console.log('frames', n);
  }
  await browser.close();
})();
