#!/usr/bin/env python3
"""Gör spelklara galoppbilder av en målad häst (fyra nyckelposer).

Användning:  python3 -I tools/make_gallop.py docs/assets/horses/saga saga a,d,c,b

Förutsätter att <nyckel>_master.png (stående) redan körts genom make_sprites.py (för <nyckel>.json).
Galoppbilderna ligger som gallop_<bokstav>_master.png. Ordningen anger rörelsecykeln.

Vad som görs:
- skalar alla galoppbilder med en gemensam faktor så att pälsytan matchar den stående bilden
- justerar färgen jämnt (en faktor per kanal) så att galopp och stående blir samma häst
- registrerar varje bild mot kroppens tyngdpunkt i sidled och en gemensam marklinje i höjdled,
  så att kroppen inte hoppar mellan bilderna men hovarna lyfter i svävfaserna precis som i målningen
- beskär och gör två storlekar (samma pixelskala som stående: stor och liten), förmultiplicerad alfa
- skriver <nyckel>_gallop.json med mått och ankarpunkter per bild
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter

d, key, order = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
std = json.load(open(os.path.join(d, key + '.json')))
W = std['crop_px'][0]
fL, fS = 1024 / W, 320 / W
GROUND = 956          # hovarnas nedre kant i bild a (stödfas), gemensam marklinje för alla galoppbilder
TORSO_SHIFT = 19      # stående bildens ankare ligger 19 px (originalpixlar) bakom kroppens tyngdpunkt


def load(path):
    a = np.array(Image.open(path).convert('RGBA'))
    a[..., 3] = np.where(a[..., 3] >= 250, 255, a[..., 3])
    return a


def coat(a):
    r, g, b = [a[..., i].astype(float) for i in range(3)]
    return (a[..., 3] >= 128) & (r > 110) & (r > g * 1.15) & (g > b * 1.05) & (r - b > 60)


def torso_cx(a):
    m = coat(a)
    sm = Image.fromarray((m * 255).astype(np.uint8)).resize((a.shape[1] // 4, a.shape[0] // 4), Image.BOX)
    sm = sm.point(lambda v: 255 if v > 128 else 0)
    op = np.array(sm.filter(ImageFilter.MinFilter(33)).filter(ImageFilter.MaxFilter(33))) > 0
    ys, xs = np.where(op)
    return float(xs.mean() * 4)


stand = load(os.path.join(d, key + '_master.png'))
sm_mask = coat(stand)
stand_mean = stand[sm_mask][:, :3].mean(axis=0)
stand_area = sm_mask.sum()
frames = {c: load(os.path.join(d, f'gallop_{c}_master.png')) for c in order}
masks = {c: coat(a) for c, a in frames.items()}
g_mean = np.mean([frames[c][masks[c]][:, :3].mean(axis=0) for c in order], axis=0)
g_area = np.mean([masks[c].sum() for c in order])
cfac = stand_mean / g_mean
s = float(np.sqrt(stand_area / g_area))
print('färgfaktor', cfac.round(3), 'skala', round(s, 4))

meta = {'order': order, 'colorFactor': [round(float(v), 4) for v in cfac], 'scale': round(s, 4), 'frames': []}
for i, c in enumerate(order):
    a = frames[c].copy()
    tcx = torso_cx(a) + TORSO_SHIFT
    rgb = np.clip(a[..., :3].astype(float) * cfac, 0, 255).astype(np.uint8)
    a[..., :3] = rgb
    im = Image.fromarray(a)
    nw, nh = round(a.shape[1] * s), round(a.shape[0] * s)
    im = im.convert('RGBa').resize((nw, nh), Image.LANCZOS).convert('RGBA')
    ax, ay = tcx * s, GROUND * s
    al = np.array(im)[..., 3]
    ys, xs = np.where(al > 8)
    pad = 14
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, nw)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, nh)
    crop = im.crop((x0, y0, x1, y1))
    entry = {'letter': c}
    for name, f in (('large', fL), ('small', fS)):
        w, h = round(crop.width * f), round(crop.height * f)
        r = crop.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
        if name == 'small':
            r = r.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2))
        fn = f'{key}_gallop{i}_{name}.png'
        r.save(os.path.join(d, fn), optimize=True)
        entry[name] = {'file': fn, 'w': w, 'h': h, 'ax': round((ax - x0) * f, 1), 'ay': round((ay - y0) * f, 1)}
        print(fn, w, h, os.path.getsize(os.path.join(d, fn)) // 1024, 'kB')
    meta['frames'].append(entry)
json.dump(meta, open(os.path.join(d, key + '_gallop.json'), 'w'), indent=1)
