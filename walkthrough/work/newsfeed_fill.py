# Replaces the empty news-feed image placeholders in the "improve" step with illustrations (art/a1..a3.png),
# following each card as the feed scrolls. Edits phone/pNNNN.jpg in place; run after extracting phone frames.
import json
import numpy as np
from PIL import Image, ImageDraw
from newsfeed_boxes import find_boxes

X0, X1, BOX_H, RADIUS = 26, 970, 526, 22   # image slot inside the card (996px-wide phone frames)
CLIP_TOP, CLIP_BOT = 141, 1938             # content scrolls under the status bar / above the tab bar
WA = (894, 1823, 43)                       # floating WhatsApp button (centre x, y, radius) stays on top
ART = [Image.open(f'art/a{i}.png').convert('RGB').resize((X1 - X0, BOX_H), Image.LANCZOS) for i in (1, 2, 3)]

mask_full = Image.new('L', (X1 - X0, BOX_H), 0)
ImageDraw.Draw(mask_full).rounded_rectangle((0, 0, X1 - X0 - 1, BOX_H - 1), RADIUS, fill=255)
wa_mask = Image.new('L', (996, 2160), 0)
ImageDraw.Draw(wa_mask).ellipse((WA[0] - WA[2], WA[1] - WA[2], WA[0] + WA[2], WA[1] + WA[2]), fill=255)

step = {s['id']: s for s in json.load(open('timeline.json'))}['improve']
f0, f1 = round(step['start'] * 30), round(step['end'] * 30)

prev, next_id, placed = [], 0, 0
for f in range(f0, f1):
    path = f'phone/p{f:04d}.jpg'
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(int)
    cur = []
    for b in find_boxes(a):
        h = b['vis_y1'] - b['vis_y0']
        if b['vis_y0'] <= CLIP_TOP + 2 and h < BOX_H - 6:
            top = b['vis_y1'] + 2 - BOX_H          # clipped by the status bar: anchor to the bottom edge
        else:
            top = b['vis_y0']
        # same card as last frame if its top moved by less than a scroll step; otherwise a new card
        match = [p for p in prev if abs(p[1] - top) < 200]
        cid = match[0][0] if match else next_id
        if not match: next_id += 1
        cur.append((cid, top))
    out = im.copy()
    for cid, top in cur:
        art = ART[min(cid, len(ART) - 1)]
        y0, y1 = max(top, CLIP_TOP), min(top + BOX_H, CLIP_BOT)
        if y1 <= y0: continue
        crop = (0, y0 - top, X1 - X0, y1 - top)
        out.paste(art.crop(crop), (X0, y0), mask_full.crop(crop))
        placed += 1
    if cur:
        out.paste(im, (0, 0), wa_mask)            # floating button back on top
        out.save(path, quality=95)
    prev = cur
print('frames', f1 - f0, 'cards placed', placed, 'distinct cards', next_id)
