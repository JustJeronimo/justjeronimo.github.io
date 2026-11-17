"""Render small studio 3D models of every grinder in coffee/index.html's GRINDERS table.
Signed-distance-field raymarcher in numpy: no dependencies beyond numpy + Pillow.
Run from the repo root:  python3 drawdown/render/grinders3d.py [id ...]
Writes coffee/assets/grinders/<id>.png (transparent, 192x192).
These are stylised archetypes (hand, box, cone hopper, single-dose, cafe), not product photos."""
import numpy as np, sys, os, json, math
from PIL import Image, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'coffee', 'assets', 'grinders')
SS, SIZE = 2, 192                       # supersample factor, output px
W = H = SIZE * SS

def hexrgb(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) / 255 for i in (0, 2, 4)])
def length(v): return np.sqrt((v * v).sum(-1))

# ---------- SDF primitives (p: N x 3) ----------
def cyl_y(p, c, h, r, rr=0.0):          # vertical capped cylinder centred at c, half-height h, radius r, rounded rr
    q = p - c; d = np.stack([length(q[:, [0, 2]]) - (r - rr), np.abs(q[:, 1]) - (h - rr)], -1)
    return np.minimum(d.max(-1), 0) + length(np.maximum(d, 0)) - rr
def cyl_z(p, c, h, r, rr=0.0):          # cylinder along z (dials on front faces)
    q = (p - c)[:, [0, 2, 1]]; return cyl_y(q, np.zeros(3), h, r, rr)
def box(p, c, b, rr=0.0):
    q = np.abs(p - c) - (np.array(b) - rr)
    return length(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - rr
def capsule(p, a, b, r):
    pa, ba = p - a, np.array(b) - a; h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return length(pa - h[:, None] * ba) - r
def cone(p, c, h, r1, r2):              # frustum, r1 bottom, r2 top
    q = p - c; qx = length(q[:, [0, 2]]); qy = q[:, 1]
    k1 = np.array([r2, h]); k2 = np.array([r2 - r1, 2 * h])
    ca = np.stack([qx - np.minimum(qx, np.where(qy < 0, r1, r2)), np.abs(qy) - h], -1)
    kq = np.stack([qx, qy], -1)
    t = np.clip(((k1 - kq) @ k2) / (k2 @ k2), 0, 1)
    cb = kq - k1 + t[:, None] * k2
    s = np.where((cb[:, 0] < 0) & (ca[:, 1] < 0), -1, 1)
    return s * np.sqrt(np.minimum((ca * ca).sum(-1), (cb * cb).sum(-1)))

# ---------- archetypes: list of (sdf_fn, material) ----------
def M(color, spec=0.35, gloss=40, metal=False, glass=False):
    return dict(c=hexrgb(color), spec=spec, gloss=gloss, metal=metal, glass=glass)

def hand(g):
    r, h = g.get('r', .2), g.get('h', .95); jar = g.get('jar', .38)
    body, catch, cap, arm, knob = M(g['body'], .5, 60, g.get('metal', False)), M(g.get('catch', g['body']), .6, 80, glass=g.get('glass', False)), M(g.get('cap', g['body']), .5, 60, g.get('metal', False)), M(g.get('arm', '#c9ccd0'), .9, 120, True), M(g.get('knob', '#2a2a2a'), .4, 30)
    top = h; parts = [
        (lambda p: cyl_y(p, np.array([0, jar / 2, 0]), jar / 2, r, .03), catch),
        (lambda p: cyl_y(p, np.array([0, jar + (top - jar) / 2, 0]), (top - jar) / 2, r, .02), body),
        (lambda p: cyl_y(p, np.array([0, top + .03, 0]), .03, r * .75, .015), cap),
        (lambda p: cyl_y(p, np.array([0, top + .09, 0]), .04, .035, .01), arm),
        (lambda p: capsule(p, np.array([0, top + .13, 0]), np.array([.42, top + .17, 0]), .022), arm),
        (lambda p: cyl_y(p, np.array([.42, top + .24, 0]), .07, g.get('kr', .055), .03), knob)]
    if g.get('flare'):                      # Skerton-style wide glass base
        parts[0] = (lambda p: cone(p, np.array([0, jar / 2, 0]), jar / 2, r * 1.35, r * 1.05), catch)
    return parts

def boxy(g):                                 # Ode-style box with front catch
    b, a, k = M(g['body'], .35, 30), M(g.get('accent', '#1a1a1a'), .6, 90), M(g.get('dial', '#d6d6d6'), .8, 100, True)
    return [
        (lambda p: box(p, np.array([0, .36, -.05]), [.33, .36, .26], .06), b),
        (lambda p: cyl_y(p, np.array([0, .74, -.05]), .03, .2, .02), a),
        (lambda p: cyl_y(p, np.array([0, .16, .29]), .16, .15, .03), a),
        (lambda p: cyl_z(p, np.array([.0, .55, .22]), .03, .11, .02), k)]

def conehop(g):                              # Encore-style base + cone hopper + bin
    b, hp, binm = M(g['body'], .35, 30, g.get('metal', False)), M(g.get('hopper', '#3a3f45'), .8, 120, glass=True), M(g.get('bin', '#202020'), .5, 60)
    return [
        (lambda p: box(p, np.array([0, .3, 0]), [.25, .3, .27], .05), b),
        (lambda p: cone(p, np.array([0, .82, 0]), .22, .15, .25), hp),
        (lambda p: cyl_y(p, np.array([0, 1.06, 0]), .025, .25, .015), b),
        (lambda p: box(p, np.array([0, .14, .25]), [.19, .13, .07], .03), binm),
        (lambda p: cyl_z(p, np.array([.0, .44, .25]), .02, .05, .01), M('#d0d0d0', .8, 100, True))]

def single(g):                               # DF64 / 064S style: drum body, small hopper, chute
    b, a, k = M(g['body'], .45, 50, g.get('metal', False)), M(g.get('accent', '#cfd2d6'), .9, 120, True), M(g.get('lid', g['body']), .5, 60)
    return [
        (lambda p: cyl_y(p, np.array([0, .06, .02]), .06, .33, .03), b),
        (lambda p: cyl_y(p, np.array([0, .45, -.04]), .27, .24, .04), b),
        (lambda p: cyl_y(p, np.array([0, .74, -.04]), .035, .25, .015), a),
        (lambda p: cone(p, np.array([0, .9, -.04]), .13, .12, .17), k),
        (lambda p: capsule(p, np.array([0, .5, .18]), np.array([0, .36, .32]), .055), b),
        (lambda p: cyl_y(p, np.array([0, .2, .32]), .06, .1, .02), M('#1c1c1c', .5, 60))]

def cafe(g):                                 # Mignon / X54 / EK43 style
    s = g.get('scale', 1.0)
    b, hp, a = M(g['body'], .4, 40, g.get('metal', False)), M(g.get('hopper', '#3a3f45'), .8, 120, glass=True), M(g.get('accent', '#c9ccd0'), .9, 120, True)
    return [
        (lambda p: box(p / s, np.array([0, .36, -.04]), [.24, .36, .28], .05) * s, b),
        (lambda p: cone(p / s, np.array([0, .9, -.04]), .18, .1, .22) * s, hp),
        (lambda p: cyl_y(p / s, np.array([0, 1.09, -.04]), .02, .22, .01) * s, b),
        (lambda p: box(p / s, np.array([0, .28, .28]), [.12, .03, .06], .02) * s, a),
        (lambda p: cyl_z(p / s, np.array([.0, .55, .24]), .02, .06, .01) * s, a)]

ARCH = dict(hand=hand, box=boxy, cone=conehop, single=single, cafe=cafe)

# ---------- per-grinder look (archetype + colours + proportions) ----------
STEEL, BLACK, GRAPH, WOOD, DARKWOOD, GLASS = '#c3c7cc', '#1d1d1f', '#3b3e43', '#b98552', '#5a3a26', '#9fb0bb'
LOOK = {
 'comandante-c40': ('hand', dict(body=BLACK, catch=GLASS, glass=True, knob=WOOD, r=.2, h=1.0, jar=.36)),
 'comandante-c40-red': ('hand', dict(body='#a3302a', catch=GLASS, glass=True, knob=WOOD, r=.2, h=1.0, jar=.36)),
 'comandante-x25': ('hand', dict(body=BLACK, catch=BLACK, knob=BLACK, r=.2, h=.9, jar=.32)),
 '1zpresso-k-ultra': ('hand', dict(body=STEEL, metal=True, knob=DARKWOOD, r=.23, h=.95, jar=.4)),
 '1zpresso-k-max': ('hand', dict(body=STEEL, metal=True, knob=BLACK, r=.23, h=.95, jar=.4)),
 '1zpresso-k-plus': ('hand', dict(body=STEEL, metal=True, knob=WOOD, r=.23, h=.95, jar=.4)),
 '1zpresso-jx-pro': ('hand', dict(body=STEEL, metal=True, cap=BLACK, knob=WOOD, r=.2, h=1.0, jar=.4)),
 '1zpresso-jx': ('hand', dict(body=STEEL, metal=True, knob=WOOD, r=.2, h=1.0, jar=.4)),
 '1zpresso-j-ultra': ('hand', dict(body=STEEL, metal=True, cap=BLACK, knob=BLACK, r=.21, h=1.0, jar=.4)),
 '1zpresso-x-ultra': ('hand', dict(body=STEEL, metal=True, knob=WOOD, r=.19, h=.9, jar=.36)),
 '1zpresso-x-pro': ('hand', dict(body=STEEL, metal=True, knob=WOOD, r=.19, h=.9, jar=.36)),
 '1zpresso-q2': ('hand', dict(body=STEEL, metal=True, knob=BLACK, r=.17, h=.82, jar=.32)),
 '1zpresso-zp6': ('hand', dict(body=STEEL, metal=True, knob=DARKWOOD, r=.23, h=.98, jar=.4)),
 'timemore-c2': ('hand', dict(body=GRAPH, knob=BLACK, r=.19, h=.92, jar=.36)),
 'timemore-c3': ('hand', dict(body=GRAPH, knob=DARKWOOD, r=.19, h=.92, jar=.36)),
 'timemore-c3-esp': ('hand', dict(body='#2b2d31', knob=DARKWOOD, r=.19, h=.95, jar=.36)),
 'timemore-c5-esp': ('hand', dict(body='#2b2d31', knob=WOOD, r=.21, h=.98, jar=.38)),
 'timemore-g1': ('hand', dict(body=STEEL, metal=True, knob=DARKWOOD, r=.21, h=.95, jar=.38)),
 'timemore-nano': ('hand', dict(body=GRAPH, knob=BLACK, r=.17, h=.8, jar=.3)),
 'kingrinder-k': ('hand', dict(body='#4a4d52', knob=BLACK, r=.21, h=.98, jar=.38)),
 'kingrinder-p': ('hand', dict(body=BLACK, knob=BLACK, r=.19, h=.9, jar=.34)),
 'hario-skerton': ('hand', dict(body=BLACK, catch=GLASS, glass=True, flare=True, knob=BLACK, r=.2, h=1.0, jar=.48)),
 'hario-mini-mill': ('hand', dict(body='#2a2a2a', catch=GLASS, glass=True, knob=BLACK, r=.16, h=.95, jar=.42)),
 'porlex-ii': ('hand', dict(body=STEEL, metal=True, knob=BLACK, r=.17, h=1.0, jar=.4)),
 'porlex-i': ('hand', dict(body=STEEL, metal=True, knob=BLACK, r=.16, h=.9, jar=.36)),
 'kinu-m47': ('hand', dict(body=STEEL, metal=True, knob=BLACK, r=.22, h=1.05, jar=.42)),
 'knock-feld47': ('hand', dict(body=BLACK, cap=STEEL, knob=BLACK, r=.2, h=.98, jar=.38)),
 'wacaco-exagrind': ('hand', dict(body=BLACK, knob=GRAPH, r=.17, h=.82, jar=.3)),
 'varia-hand': ('hand', dict(body=BLACK, cap=STEEL, knob=BLACK, r=.2, h=.95, jar=.36)),
 'helor-101': ('hand', dict(body=STEEL, metal=True, knob=WOOD, r=.21, h=.98, jar=.38)),
 'lagom-mini': ('hand', dict(body='#6b6e72', knob=BLACK, r=.2, h=.9, jar=.34)),
 'fellow-ode-2': ('box', dict(body='#232325', accent='#141414', dial='#d8d8d8')),
 'fellow-ode-1': ('box', dict(body='#1b1b1c', accent='#101010', dial='#bdbdbd')),
 'fellow-opus': ('single', dict(body='#1c1c1e', accent='#9a9a9a', lid='#2a2a2c')),
 'baratza-encore': ('cone', dict(body='#1e1e1f')),
 'baratza-encore-esp': ('cone', dict(body='#2a2a2c')),
 'baratza-virtuoso': ('cone', dict(body='#b9bdc2', metal=True)),
 'baratza-sette': ('cafe', dict(body='#2a2a2c', accent='#8a8d92')),
 'baratza-vario': ('cafe', dict(body='#1d1d1f', accent=STEEL)),
 'baratza-forte': ('cafe', dict(body='#c3c6ca', metal=True, accent='#2a2a2a')),
 'wilfa-uniform': ('cone', dict(body='#c7cacd', metal=True, bin='#2a2a2a')),
 'wilfa-svart': ('cone', dict(body='#1a1a1a')),
 'sage-sgp': ('cone', dict(body='#b5b9be', metal=True)),
 'df64-2': ('single', dict(body='#1b1b1d', accent=STEEL)),
 'df64v': ('single', dict(body='#d9d9d6', accent='#8f9297')),
 'df83v': ('single', dict(body='#1b1b1d', accent='#e0e0e0')),
 'mk-x54': ('cafe', dict(body='#1d1d1f', accent='#bfc2c6')),
 'mk-ek43': ('cafe', dict(body='#e9e7e2', accent='#2a2a2a', scale=1.12)),
 'eureka-specialita': ('cafe', dict(body='#1f1f21', accent=STEEL)),
 'eureka-oro': ('cafe', dict(body='#2a2a2c', accent='#c9a86a')),
 'timemore-078s': ('single', dict(body='#e6e4df', accent='#2a2a2a')),
 'timemore-064s': ('single', dict(body='#bcc0c5', metal=True, accent='#2a2a2a')),
 'lagom-p64': ('single', dict(body='#c9ccd0', metal=True, accent='#2b2b2b')),
 'varia-vs3': ('single', dict(body='#141414', accent='#9a9a9a')),
 'oxo-conical': ('cone', dict(body='#c2c5c9', metal=True, bin='#222222')),
 'hario-v60-electric': ('cone', dict(body='#1c1c1c')),
}

# ---------- renderer ----------
CAM = np.array([2.6, 1.75, 2.6]); TARGET = np.array([0.04, .62, 0]); FOV = 23.5
KEY = np.array([-.55, .75, .55]); KEY /= np.linalg.norm(KEY)
RIM = np.array([.7, .35, -.75]); RIM /= np.linalg.norm(RIM)

def scene(parts, p):
    d = np.full(len(p), 1e9); mid = np.zeros(len(p), int)
    for i, (f, _) in enumerate(parts):
        di = f(p); m = di < d; d = np.where(m, di, d); mid = np.where(m, i, mid)
    return d, mid

def render(gid):
    arch, look = LOOK[gid]; parts = ARCH[arch](look)
    fw = TARGET - CAM; fw /= np.linalg.norm(fw); rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    t = math.tan(math.radians(FOV) / 2)
    ys, xs = np.mgrid[0:H, 0:W]; u = (xs + .5) / W * 2 - 1; v = 1 - (ys + .5) / H * 2
    dirs = fw + u.reshape(-1, 1) * t * rt + v.reshape(-1, 1) * t * up; dirs /= length(dirs)[:, None]
    n = len(dirs); dist = np.zeros(n); hit = np.zeros(n, bool); alive = np.ones(n, bool)
    for _ in range(110):
        idx = np.nonzero(alive)[0]
        if not len(idx): break
        p = CAM + dirs[idx] * dist[idx, None]; d, _ = scene(parts, p)
        dist[idx] += d * .9
        h = d < 1e-3; hit[idx[h]] = True; alive[idx[h]] = False
        alive[idx[dist[idx] > 8]] = False
    img = np.zeros((n, 4))
    hi = np.nonzero(hit)[0]
    if len(hi):
        p = CAM + dirs[hi] * dist[hi, None]; _, mid = scene(parts, p)
        e = 1e-3; nrm = np.stack([scene(parts, p + np.array(o) * e)[0] - scene(parts, p - np.array(o) * e)[0] for o in ([1, 0, 0], [0, 1, 0], [0, 0, 1])], -1)
        nrm /= length(nrm)[:, None] + 1e-9
        ao = np.ones(len(p))
        for k in range(1, 5):
            s = .03 * k; ao -= (s - scene(parts, p + nrm * s)[0]).clip(0) * (1.6 / k)
        ao = ao.clip(.35, 1)
        V = -dirs[hi]; col = np.zeros((len(p), 3))
        for i, (_, m) in enumerate(parts):
            sel = mid == i
            if not sel.any(): continue
            N = nrm[sel]; base = m['c']
            dif = (N @ KEY).clip(0); rim = (N @ RIM).clip(0) ** 2; amb = .28 + .22 * N[:, 1].clip(-1, 1)
            Hh = KEY + V[sel]; Hh /= length(Hh)[:, None]
            sp = ((N * Hh).sum(-1).clip(0)) ** m['gloss'] * m['spec']
            fres = (1 - (N * V[sel]).sum(-1).clip(0, 1)) ** 3
            c = base * (amb + .85 * dif)[:, None] + (sp[:, None] * (base if m['metal'] else 1) * 1.2) + .55 * rim[:, None] + .18 * fres[:, None]
            if m['glass']: c = c * .75 + .12 + .35 * fres[:, None]
            col[sel] = c * ao[sel, None]
        img[hi, :3] = col.clip(0, 1); img[hi, 3] = 1
    rgba = (img.reshape(H, W, 4) * 255).astype(np.uint8)
    im = Image.fromarray(rgba, 'RGBA')
    # soft contact shadow under the object
    sh = Image.new('L', (W, H), 0); from PIL import ImageDraw
    ImageDraw.Draw(sh).ellipse([W * .2, H * .84, W * .82, H * .97], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(W * .03))
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0)); base.putalpha(sh)
    base.alpha_composite(im)
    return base.resize((SIZE, SIZE), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ids = sys.argv[1:] or list(LOOK)
    for gid in ids:
        render(gid).save(os.path.join(OUT, gid + '.png'), optimize=True); print('rendered', gid, flush=True)
