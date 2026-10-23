#!/usr/bin/env python3
"""Gör spelklara galopp- och hoppbilder av en målad häst.

Användning:
  python3 -I tools/make_gallop.py docs/assets/horses/saga saga a,e,g,h,b,c,d,f 3,4,1,2

Förutsätter att <nyckel>_master.png (stående) redan körts genom make_sprites.py (för <nyckel>.json).
Galoppbilderna ligger som gallop_<bokstav>_master.png och hoppbilderna som jump_<nummer>_master.png.
Ordningen anger rörelsen i tid (galoppcykeln; hoppet från avstamp till landning).

Vad som görs:
- skalar alla bilder med en gemensam faktor så att pälsytan matchar den stående bilden
- justerar färgen jämnt (en faktor per kanal) så att alla poser blir samma häst
- registrerar sidled mot kroppens tyngdpunkt, höjdled mot en gemensam marklinje:
    galopp: fast marklinje (hovarna i stödfas når marken, i svävfas lyfter de)
    hopp:   marklinjen sätts så att kroppen ligger på normal höjd men hovarna aldrig hamnar under marken
- beskär och skriver bara den lilla storleken (320 px-skala, flocken); stor behövs bara för stående
- skriver <nyckel>_gallop.json med mått och ankarpunkter
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter

d, key = sys.argv[1], sys.argv[2]
gorder = sys.argv[3].split(',')
jorder = sys.argv[4].split(',') if len(sys.argv) > 4 else []
std = json.load(open(os.path.join(d, key + '.json')))
W = std['crop_px'][0]
fS = 320 / W
GROUND = 956          # hovarnas nedre kant i stödfas (gemensam marklinje för galoppbilderna)
TORSO_SHIFT = 19      # stående bildens ankare ligger 19 px (originalpixlar) bakom kroppens tyngdpunkt


def load(path):
    a = np.array(Image.open(path).convert('RGBA'))
    a[..., 3] = np.where(a[..., 3] >= 250, 255, a[..., 3])
    return a


def coat(a):
    r, g, b = [a[..., i].astype(float) for i in range(3)]
    return (a[..., 3] >= 128) & (r > 110) & (r > g * 1.15) & (g > b * 1.05) & (r - b > 60)


def torso(a):
    m = coat(a)
    sm = Image.fromarray((m * 255).astype(np.uint8)).resize((a.shape[1] // 4, a.shape[0] // 4), Image.BOX)
    sm = sm.point(lambda v: 255 if v > 128 else 0)
    op = np.array(sm.filter(ImageFilter.MinFilter(33)).filter(ImageFilter.MaxFilter(33))) > 0
    ys, xs = np.where(op)
    return float(xs.mean() * 4), float(ys.mean() * 4)


stand = load(os.path.join(d, key + '_master.png'))
sm_mask = coat(stand)
stand_mean = stand[sm_mask][:, :3].mean(axis=0)
stand_area = sm_mask.sum()
files = [('gallop', c, os.path.join(d, f'gallop_{c}_master.png')) for c in gorder] + \
        [('jump', j, os.path.join(d, f'jump_{j}_master.png')) for j in jorder]
frames = {(k, c): load(p) for k, c, p in files}
masks = {kc: coat(a) for kc, a in frames.items()}
g_mean = np.mean([frames[kc][masks[kc]][:, :3].mean(axis=0) for kc in frames], axis=0)
g_area = np.mean([masks[kc].sum() for kc in frames])
cfac = stand_mean / g_mean
s = float(np.sqrt(stand_area / g_area))
tors = {kc: torso(a) for kc, a in frames.items()}
BODY_H = float(np.mean([GROUND - tors[kc][1] for kc in frames if kc[0] == 'gallop']))  # kroppens normala höjd över marken
print('färgfaktor', cfac.round(3), 'skala', round(s, 4), 'normal kroppshöjd', round(BODY_H))

meta = {'colorFactor': [round(float(v), 4) for v in cfac], 'scale': round(s, 4), 'gallop': {'order': gorder, 'frames': []}, 'jump': {'order': jorder, 'frames': []}}
for (kind, c, _p) in files:
    a = frames[(kind, c)].copy()
    tcx, tcy = tors[(kind, c)]
    a[..., :3] = np.clip(a[..., :3].astype(float) * cfac, 0, 255).astype(np.uint8)
    lowest = float(np.where(a[..., 3] >= 128)[0].max())
    ground = GROUND if kind == 'gallop' else max(tcy + BODY_H, lowest)
    im = Image.fromarray(a)
    nw, nh = round(a.shape[1] * s), round(a.shape[0] * s)
    im = im.convert('RGBa').resize((nw, nh), Image.LANCZOS).convert('RGBA')
    ax, ay = (tcx + TORSO_SHIFT) * s, ground * s
    al = np.array(im)[..., 3]
    ys, xs = np.where(al > 8)
    pad = 14
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, nw)
    y0, y1 = int(min(ys.min() - pad, ay - 1)), int(max(ys.max() + pad + 1, ay + 1))
    # fyll ut med genomskinlig yta om marklinjen ligger utanför bilden (hopp)
    canvas = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
    canvas.alpha_composite(im.crop((x0, max(y0, 0), x1, min(y1, nh))), (0, max(0, -y0)))
    idx = len(meta[kind]['frames'])
    w, h = round(canvas.width * fS), round(canvas.height * fS)
    r = canvas.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA').filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2))
    fn = f'{key}_{kind}{idx}_small.png'
    r.save(os.path.join(d, fn), optimize=True)
    meta[kind]['frames'].append({'letter': c, 'small': {'file': fn, 'w': w, 'h': h, 'ax': round((ax - x0) * fS, 1), 'ay': round((ay - y0) * fS, 1)}})
    print(fn, w, h, os.path.getsize(os.path.join(d, fn)) // 1024, 'kB', '| marklinje', round(ground))
json.dump(meta, open(os.path.join(d, key + '_gallop.json'), 'w'), indent=1)
