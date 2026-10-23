#!/usr/bin/env python3
"""Gör spelklara PNG-bilder av en målad häst.

Användning:  python3 -I tools/make_sprites.py docs/assets/horses/saga/saga_master.png saga

- rensar nästan-opak alfa (>=250 -> 255) och beskär till hästen med lite marginal
- hittar marklinjen (hovarnas nedre kant) och ankarpunkt (mitten mellan hovarna)
- skriver <nyckel>_large.png (1024 px bred, stallet) och <nyckel>_small.png (320 px bred, flocken)
- storleksändring sker med förmultiplicerad alfa så att inga mörka kanter uppstår
- skriver <nyckel>.json med mått (marklinje, ankare, höjd) i pixlar för varje storlek
"""
import sys, json, os
import numpy as np
from PIL import Image, ImageFilter

src, key = sys.argv[1], sys.argv[2]
out = os.path.dirname(src)
im = Image.open(src).convert('RGBA')
a = np.array(im)
al = a[..., 3]
al = np.where(al >= 250, 255, al).astype(np.uint8)
a[..., 3] = al
ys, xs = np.where(al > 8)
PAD = 14
x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, a.shape[1])
y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, a.shape[0])
# marklinje = lägsta solida pixel; ankare = mitten av de fyra hovarna
solid = al >= 128
sy, sx = np.where(solid)
bot = sy.max()
band = sy > bot - 60
cols = np.sort(np.unique(sx[band]))
groups, start, prev = [], cols[0], cols[0]
for c in cols[1:]:
    if c - prev > 8:
        groups.append((start, prev)); start = c
    prev = c
groups.append((start, prev))
mids = [(g[0] + g[1]) / 2 for g in groups if g[1] - g[0] > 20]
anchor_x = float(np.mean(mids)) - x0
base_y = float(bot) - y0
top_y = float(ys.min()) - y0
crop = Image.fromarray(a).crop((x0, y0, x1, y1))
W, H = crop.size
meta = {'source': os.path.basename(src), 'crop_px': [W, H], 'sizes': {}}
for name, width in (('large', 1024), ('small', 320)):
    k = width / W
    nh = round(H * k)
    r = crop.convert('RGBa').resize((width, nh), Image.LANCZOS).convert('RGBA')
    if name == 'small':
        r = r.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2))
    fn = f'{key}_{name}.png'
    r.save(os.path.join(out, fn), optimize=True)
    meta['sizes'][name] = {'file': fn, 'w': width, 'h': nh,
                           'baseline': round(base_y * k, 1), 'anchorX': round(anchor_x * k, 1),
                           'topToBaseline': round((base_y - top_y) * k, 1)}
    print(fn, width, nh, os.path.getsize(os.path.join(out, fn)) // 1024, 'kB')
json.dump(meta, open(os.path.join(out, key + '.json'), 'w'), indent=1)
print(json.dumps(meta['sizes'], indent=1))
