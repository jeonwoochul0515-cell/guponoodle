# -*- coding: utf-8 -*-
"""
s03 — 1950년대, 부산항으로 들어온 원조 밀가루.

구포에 국수가 자리잡은 이유다. 전후 원조 밀가루가 부산항으로 들어왔고,
낙동강 물길과 구포장이 만나는 이곳에서 그 밀이 국수가 됐다.

포대 인쇄면은 남아 있는 실물 포대를 보고 다시 그렸다.
"미국 국민이 기증한 밀로 제분된 / 밀가루 / 정미 22KGS /
 팔거나 다른물건과 바꾸지 말것 / 대한제분주식회사"
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cinema")
os.makedirs(OUT, exist_ok=True)
SS = int(os.environ.get("SS", "2"))

HALF_W, CEIL_H, BACK_Z = 4.10, 3.15, 20.0
EYE = 1.45
GAP_Z0, GAP_PITCH, GAP_HALF = 4.0, 6.2, 0.44
LDIR = (0.34, -0.90, 0.28)

FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
FONT_R = "C:/Windows/Fonts/malgun.ttf"


# ─────────────────────────────────────────────────────────────
# 포대 인쇄면 — 실물을 보고 다시 그린다
# ─────────────────────────────────────────────────────────────
def sack_texture(w=900, h=1250):
    img = Image.new("RGB", (w, h), (232, 221, 196))
    d = ImageDraw.Draw(img)
    ink = (48, 42, 34)
    blue = (58, 84, 128)
    red = (176, 58, 44)

    def font(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def center(txt, y, f, fill):
        bb = d.textbbox((0, 0), txt, font=f)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y), txt, font=f, fill=fill)

    # 상단 문구
    center("미국 국민이 기증한 밀로 제분된", 96, font(FONT_B, 54), ink)
    # 큰 글씨
    center("밀가루", 190, font(FONT_B, 210), ink)
    # 붉은 검인
    d.text((w * 0.50, 178), "가 양", font=font(FONT_B, 64), fill=red)

    # 별 셋
    def star(cx, cy, r):
        pts = []
        for i in range(10):
            a = -np.pi / 2 + i * np.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))
        d.polygon(pts, fill=blue)
    for i, cx in enumerate((w * 0.38, w * 0.5, w * 0.62)):
        star(cx, 470, 26)

    # 악수 — 양쪽 소매에서 나온 손이 가운데서 맞잡는다
    y0, hh = 552, 60
    d.rounded_rectangle([w * 0.235, y0, w * 0.435, y0 + hh], 10, fill=blue)
    d.rounded_rectangle([w * 0.565, y0, w * 0.765, y0 + hh], 10, fill=blue)
    for k in range(3):                      # 소매 줄무늬
        xx = w * 0.245 + k * 15
        d.line([(xx, y0 + 6), (xx, y0 + hh - 6)], fill=(232, 221, 196), width=5)
        xx = w * 0.755 - k * 15
        d.line([(xx, y0 + 6), (xx, y0 + hh - 6)], fill=(232, 221, 196), width=5)
    # 맞잡은 손 — 소가락이 보이게
    d.rounded_rectangle([w * 0.425, y0 + 4, w * 0.575, y0 + hh - 4], 18, fill=blue)
    for k in range(3):
        yy = y0 + 14 + k * 13
        d.line([(w * 0.452, yy), (w * 0.548, yy)], fill=(232, 221, 196), width=4)

    center("UNITED STATES OF AMERICA", y0 + 96, font(FONT_B, 44), blue)

    # 붉은 세로 줄 다섯
    for k in range(5):
        x0 = w * 0.30 + k * (w * 0.40 / 5)
        d.rounded_rectangle([x0, y0 + 168, x0 + w * 0.048, y0 + 268], 6, fill=red)

    # 하단 문구
    center("정미 22KGS", 950, font(FONT_B, 48), ink)
    center("팔거나 다른물건과 바꾸지 말것", 1022, font(FONT_R, 44), ink)
    center("대한제분주식회사", 1094, font(FONT_B, 50), ink)

    a = np.asarray(img, np.float32) / 255.0
    # 마대 올 — 성긴 직조
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = (0.5 + 0.5 * np.cos(xx * 1.55)) * 0.5 + (0.5 + 0.5 * np.cos(yy * 1.55)) * 0.5
    a *= (0.90 + 0.13 * weave)[..., None]
    # 얼룩과 접힌 자국
    st = C.fbm(xx / 42.0, yy / 42.0, seed=301, octaves=5)
    a *= (0.82 + 0.26 * st)[..., None]
    fold = np.exp(-((yy - h * 0.46) / 26.0) ** 2) * 0.16
    a *= (1.0 - fold)[..., None]
    return np.clip(a, 0, 1)


# ─────────────────────────────────────────────────────────────
# 평면 텍스처를 화면 사각형에 얹는다
# ─────────────────────────────────────────────────────────────
def homography(src, dst):
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    h = np.linalg.solve(np.asarray(A, np.float64), np.asarray(b, np.float64))
    return np.append(h, 1.0).reshape(3, 3)


def place_quad(cam, img, tex, quad, shade=1.0, bulge=0.30):
    """quad: 화면 비율 좌표 [(x,y)] 좌상·우상·우하·좌하"""
    th, tw = tex.shape[:2]
    dst = [(p[0] * cam.rw, p[1] * cam.rh) for p in quad]
    src = [(0, 0), (tw, 0), (tw, th), (0, th)]
    Hm = homography(src, dst)
    Hi = np.linalg.inv(Hm)

    xs = [p[0] for p in dst]
    ys = [p[1] for p in dst]
    x0, x1 = max(0, int(min(xs)) - 2), min(cam.rw, int(max(xs)) + 2)
    y0, y1 = max(0, int(min(ys)) - 2), min(cam.rh, int(max(ys)) + 2)
    if x1 <= x0 or y1 <= y0:
        return

    X, Y = np.meshgrid(np.arange(x0, x1, dtype=np.float64) + 0.5,
                       np.arange(y0, y1, dtype=np.float64) + 0.5)
    den = Hi[2, 0] * X + Hi[2, 1] * Y + Hi[2, 2]
    u = (Hi[0, 0] * X + Hi[0, 1] * Y + Hi[0, 2]) / den
    v = (Hi[1, 0] * X + Hi[1, 1] * Y + Hi[1, 2]) / den

    # 포대는 평면이 아니라 부풀어 있다. 가로 중앙을 밀어 곡면처럼 보이게.
    un = np.clip(u / tw, 0, 1)
    u = u - bulge * tw * 0.18 * np.sin(np.pi * un) * (un - 0.5) * 2.0

    # 직사각형으로 두면 종이처럼 보인다. 위아래가 잔 자루 실루엣을 쓴다.
    vn = np.clip(v / th, 0, 1)
    un2 = u / tw
    wprof = (1.0 - 0.20 * C.smoothstep(0.15, 0.0, vn)
                 - 0.15 * C.smoothstep(0.85, 1.0, vn))
    inside = ((u >= 0) & (u < tw - 1) & (v >= 0) & (v < th - 1) &
              (np.abs(un2 - 0.5) < wprof * 0.5))
    ui = np.clip(u, 0, tw - 1.001)
    vi = np.clip(v, 0, th - 1.001)
    i0 = ui.astype(np.int32); j0 = vi.astype(np.int32)
    fu = (ui - i0)[..., None]; fv = (vi - j0)[..., None]
    i1 = np.minimum(i0 + 1, tw - 1); j1 = np.minimum(j0 + 1, th - 1)
    col = ((tex[j0, i0] * (1 - fu) + tex[j0, i1] * fu) * (1 - fv) +
           (tex[j1, i0] * (1 - fu) + tex[j1, i1] * fu) * fv)

    # 원통 음영 + 위에서 오는 빛. 가장자로 갈수록 깊게 떨어진다.
    lat = np.clip(np.cos((un - 0.47) * np.pi * 1.02), 0, 1) ** 0.62
    vert = 0.62 + 0.46 * (1.0 - vn) ** 0.9
    # 묶인 윗목과 바닥에 주름이 진다
    crease = (1.0 - 0.30 * np.exp(-((vn - 0.055) / 0.055) ** 2)
                  - 0.22 * np.exp(-((vn - 0.955) / 0.05) ** 2))
    col = col * (0.16 + 0.92 * lat)[..., None] * (vert * crease)[..., None] * shade

    a = np.where(inside, 1.0, 0.0).astype(np.float32)
    a = C.blur(a, 1, 1)
    C.over(img[y0:y1, x0:x1], col.astype(np.float32), a)


def render():
    cam = C.Cam(1920, 1080, ss=SS, focal=1100.0, vp=(0.5, 0.470), eye=EYE)
    img = cam.new()
    Xn = cam.X / cam.rw
    Yn = cam.Y / cam.rh
    dxb = np.broadcast_to(cam.dx, (cam.rh, cam.rw)).astype(np.float32)
    dyb = np.broadcast_to(cam.dy, (cam.rh, cam.rw)).astype(np.float32)

    z, surf, u, v, wx, wy = C.room(cam, HALF_W, CEIL_H, BACK_Z)
    is_f, is_c = surf == C.FLOOR, surf == C.CEIL
    is_l, is_r = surf == C.LEFT, surf == C.RIGHT
    is_b = surf == C.BACK

    alb = np.zeros_like(img)
    ft = 0.20 + 0.20 * C.fbm(u * 2.4, v * 2.4, seed=11, octaves=5)
    ft *= (1.0 + 0.55 * C.sat((C.fbm(u * 1.1, v * 1.1, seed=12, octaves=4) - 0.52) * 2.6))
    alb[is_f] = np.stack([ft, ft * 0.95, ft * 0.86], -1)[is_f]

    ct = 0.16 + 0.14 * C.fbm(u * 3.0, v * 3.0, seed=13, octaves=4)
    ct = np.where(np.abs(((v * 0.9) % 1.7) - 0.85) < 0.17, ct * 0.42, ct)
    alb[is_c] = np.stack([ct, ct * 0.92, ct * 0.80], -1)[is_c]

    wt = 0.30 + 0.24 * C.fbm(u * 1.8, v * 3.6, seed=14, octaves=5)
    wt = np.where(np.abs((u % 2.9) - 1.45) < 0.09, wt * 0.42, wt)
    wall = np.stack([wt, wt * 0.93, wt * 0.80], -1)
    alb[is_l] = wall[is_l]
    alb[is_r] = (wall * 0.88)[is_r]

    bt = 0.24 + 0.16 * C.fbm(u * 2.2, v * 2.6, seed=15, octaves=4)
    bcol = np.stack([bt, bt * 0.92, bt * 0.80], -1)
    door = (np.abs(u + 0.30) < 0.80) & (v > -EYE) & (v < 0.92)
    bcol = np.where(door[..., None], np.array([2.45, 2.30, 2.00], np.float32), bcol)
    alb[is_b] = bcol[is_b]

    surf_lit, vol = C.window_light(cam, z, CEIL_H, L=LDIR, win_z0=GAP_Z0, pitch=GAP_PITCH,
                                   win_half=GAP_HALF, win_y0=-1.55, win_y1=1.55,
                                   steps=18, zmax=BACK_Z, axis="y")
    ndl = np.where(is_f, 0.86, np.where(is_l | is_r, 0.26, 0.12))
    amb = 0.26 + 0.62 * np.exp(-z / 12.0)
    img[:] = alb * (amb * 0.44 + surf_lit * ndl * 1.30)[..., None] * \
        np.array([1.0, 0.96, 0.87], np.float32)

    # ── 쌓인 포대 더미 — 좌우 벽을 따라
    def plane_x(px, sign):
        zz = np.where(sign * dxb > 0.35, px * cam.f / np.maximum(sign * dxb, 0.35), 1e9)
        return zz, -dyb * zz / cam.f

    for sign in (-1, 1):
        zq, wyq = plane_x(2.18, sign)
        stack = (wyq > -EYE) & (wyq < 0.50) & (zq > 2.2) & (zq < BACK_Z) & (zq < z)
        # 포대는 누워서 쳤다. 가로 줄만 보이고 세로 격자는 없다.
        row = np.floor((wyq + EYE) / 0.24)
        jitter = C.fbm1(row * 5.3 + np.floor(zq / 0.72) * 2.1, seed=21, octaves=2)
        lay = np.abs(((wyq + EYE) / 0.24 % 1.0) - 0.5)
        st = 0.34 + 0.20 * jitter
        st = st * (0.55 + 0.75 * C.smoothstep(0.50, 0.16, lay))
        st = st * (0.86 + 0.24 * C.fbm(zq * 2.2, wyq * 6.0, seed=22, octaves=3))
        sh = (0.26 + 0.62 * np.exp(-np.minimum(zq, 99.0) / 12.0)) * 0.26
        C.over(img, np.stack([st, st * 0.95, st * 0.84], -1) * sh[..., None],
               np.where(stack, 1.0, 0.0).astype(np.float32))
        z = np.where(stack, zq, z)

    # ── 인물 — 포대보다 뒤에 서 있다. 포대보다 먼저 그린다.
    for pz, xp, h, pose, fc in ((13.0, 1.35, 1.63, 2, -1), (8.4, -1.70, 1.60, 0, 1)):
        m, pbox = C.person(cam, pz, xp, h, pose, hanbok=False, facing=fc)
        if m is None:
            continue
        att = 0.022 + 0.055 * np.exp(-pz / 10.0)
        C.over_box(img, np.array([att, att * 0.90, att * 0.76], np.float32), m * 0.96, pbox)

    # ── 주인공 포대 — 화면 가운데 살짝 왼쪽에 기대어 세워져 있다
    tex = sack_texture()
    place_quad(cam, img, tex,
               [(0.268, 0.120), (0.600, 0.182), (0.578, 0.975), (0.214, 0.896)],
               shade=0.62, bulge=0.40)
    place_quad(cam, img, tex,
               [(0.648, 0.478), (0.852, 0.506), (0.842, 0.900), (0.636, 0.858)],
               shade=0.44, bulge=0.30)
    place_quad(cam, img, tex,
               [(0.848, 0.402), (0.992, 0.426), (0.992, 0.758), (0.842, 0.734)],
               shade=0.33, bulge=0.26)

    # ── 공기 중 밀가루
    dn = 0.55 + 0.45 * C.fbm(Xn * 6.5, Yn * 4.6, seed=41, octaves=5)
    img += (vol * dn * 1.15)[..., None] * np.array([1.0, 0.94, 0.80], np.float32)
    pn = C.fbm(Xn * 205.0, Yn * 205.0, seed=61, octaves=2)
    img += (C.sat((pn - 0.882) * 11.0) * (0.10 + 6.0 * vol) * 0.52)[..., None] * \
        np.array([1.0, 0.96, 0.87], np.float32)

    img = C.bloom(img, thresh=0.62, radius=0.028, amount=0.44)
    img = C.filmic(img * 1.14)
    img = C.monotint(img, tint=(1.042, 0.896, 0.694), black=0.018, white=0.968,
                     gamma=0.95, s_curve=0.66,
                     split=((0.82, 0.88, 1.05), (1.07, 1.00, 0.90)))
    img = C.vignette(cam, img, amount=0.58, power=1.85)
    img = C.grain(img, amount=0.036, seed=11, size=1.35)
    return cam, img


if __name__ == "__main__":
    cam, img = render()
    p = os.path.join(OUT, "s03.webp")
    C.save(cam, img, p, quality=84)
    print("s03.webp", os.path.getsize(p) // 1024, "KB")
