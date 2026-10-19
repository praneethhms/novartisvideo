// Renders the three news-feed illustrations in newsfeed_art.html to art/a1.png .. art/a3.png
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  fs.mkdirSync(path.join(__dirname, 'art'), { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 944, height: 1700 } });
  await p.goto('file://' + path.join(__dirname, 'newsfeed_art.html'));
  for (const id of ['a1', 'a2', 'a3']) await (await p.$('#' + id)).screenshot({ path: path.join(__dirname, 'art', id + '.png') });
  await b.close();
})();
