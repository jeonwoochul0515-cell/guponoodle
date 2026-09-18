# -*- coding: utf-8 -*-
"""s02 — 1950년대 구포 국수공장 건조실. 높은 창의 빛기둥과 밀가루 먼지."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cinema")
os.makedirs(OUT, exist_ok=True)
SS = int(os.environ.get("SS", "2"))

HALF_W, CEIL_H, BACK_Z = 4.30, 3.05, 27.0
EYE = 1.52
WIN_Z0, PITCH, WIN_HALF = 4.6, 4.5, 1.00
WIN_Y0, WIN_Y1 = 0.70, 2.30
LDIR = (0.82, -0.52, 0.24)


def render():
    cam = C.Cam(1920, 1080, ss=SS, focal=1120.0, vp=(0.5, 0.452), eye=EYE)
    img = cam.new()
    Xn = cam.X / cam.rw
    Yn = cam.Y / cam.rh

    z, surf, u, v, wx, wy = C.room(cam, HALF_W, CEIL_H, BACK_Z)
    is_f, is_c = surf == C.FLOOR, surf == C.CEIL
    is_l, is_r = surf == C.LEFT, surf == C.RIGHT
    is_b = surf == C.BACK

    # ── 표면 알베도
    alb = np.zeros_like(img)
    fn = C.fbm(u * 2.1, v * 2.1, seed=11, octaves=5)
    ft = 0.30 + 0.34 * fn + 0.12 * C.fbm(u * 9.0, v * 9.0, seed=12, octaves=3)
    ft *= (1.0 + 0.45 * C.sat((C.fbm(u * 0.8, v * 0.8, seed=13, octaves=4) - 0.50) * 2.4))
    alb[is_f] = np.stack([ft, ft * 0.95, ft * 0.86], -1)[is_f]

    beam_w = np.abs(((v * 0.82) % 1.55) - 0.775) < 0.16      # 서까래
    ct = 0.40 + 0.26 * C.fbm(u * 3.4, v * 3.4, seed=14, octaves=4)
    ct = np.where(beam_w, ct * 0.42, ct)
    alb[is_c] = np.stack([ct, ct * 0.92, ct * 0.79], -1)[is_c]

    wt = 0.46 + 0.34 * C.fbm(u * 1.7, v * 3.4, seed=15, octaves=5)
    wt = np.where(np.abs((u % 2.55) - 1.275) < 0.075, wt * 0.30, wt)   # 기둥
    wall = np.stack([wt, wt * 0.925, wt * 0.80], -1)
    alb[is_l] = wall[is_l]
    alb[is_r] = (wall * 0.92)[is_r]

    bt = 0.28 + 0.22 * C.fbm(u * 2.4, v * 2.8, seed=16, octaves=4)
    bcol = np.stack([bt, bt * 0.92, bt * 0.80], -1)
    # 뒷벽에 열린 문 - 소실점이 빛난다
    door = (np.abs(u - 0.30) < 0.78) & (v > -EYE) & (v < 0.78)
    bcol = np.where(door[..., None], np.array([2.55, 2.40, 2.10], np.float32), bcol)
    alb[is_b] = bcol[is_b]

    # ── 직사광: 창을 역추적한 진짜 빛 패치 + 공기 중 산란
    surf_lit, vol = C.window_light(cam, z, HALF_W, L=LDIR, win_z0=WIN_Z0, pitch=PITCH,
                                   win_half=WIN_HALF, win_y0=WIN_Y0, win_y1=WIN_Y1,
                                   steps=20, zmax=BACK_Z)
    # 면 법선에 따른 코사인
    ndl = np.where(is_f, 0.52, np.where(is_r, 0.80, np.where(is_b, 0.25, 0.10)))
    # 창틀 그림자(가로 살)
    t_ = (wx + HALF_W) / np.float32(LDIR[0])
    yh = wy - t_ * np.float32(LDIR[1])
    mull = (np.abs(((yh - WIN_Y0) % 0.54) - 0.27) < 0.030).astype(np.float32)
    sun = surf_lit * ndl * (1.0 - 0.70 * mull)

    # 앰비언트: 창 쪽이 밝고 안쪽으로 갈수록 어둡다
    amb = (0.34 + 0.62 * np.exp(-z / 11.0)) * (0.55 + 0.45 * C.sat((wx + HALF_W) / (2 * HALF_W)))
    img[:] = alb * (amb * 0.52 + sun * 1.55)[..., None] * \
        np.array([1.0, 0.965, 0.90], np.float32)

    # ── 창 자체 (좌벽에 뚫린 밝은 개구부)
    dzw = ((u - (WIN_Z0 + PITCH * 0.5)) % PITCH) - PITCH * 0.5
    win = is_l & (np.abs(dzw) < WIN_HALF) & (wy > WIN_Y0) & (wy < WIN_Y1)
    frame = is_l & (np.abs(dzw) < WIN_HALF + 0.13) & (wy > WIN_Y0 - 0.12) & (wy < WIN_Y1 + 0.12)
    img = C.over(img, np.array([0.030, 0.026, 0.020], np.float32),
                 np.where(frame & ~win, 0.92, 0.0).astype(np.float32))
    wmull = (np.abs(((wy - WIN_Y0) % 0.54) - 0.27) < 0.028) | (np.abs(dzw) < 0.030)
    glow = 1.65 / (1.0 + (np.maximum(u, 0.2) / 8.0) ** 1.5)
    img = C.over(img, np.stack([glow * 1.20, glow * 1.13, glow * 0.99], -1),
                 np.where(win & ~wmull, 1.0, 0.0).astype(np.float32))

    # ── 국수 건조 랙 — 실내 터널
    RACK = [22.0, 17.0, 13.0, 9.9, 7.4, 5.6, 4.25, 3.30]
    X_IN, X_OUT = 2.02, 4.25
    Y_TOP, Y_BOT = 1.62, -0.42
    for i, rz in enumerate(RACK):
        rgb, a, box = C.noodle_curtain(
            cam, rz, X_IN, X_OUT, Y_TOP, Y_BOT,
            period=0.0112, seed=210 + i * 4, sway=0.035, ragged=0.20,
            bright=(1.00, 0.962, 0.876), dark=(0.13, 0.117, 0.098),
            base_alpha=0.95, bundle=0.70, bundle_w=0.42)
        if a is not None:
            # 이 깊이의 빛/안개
            lit_here = 0.30 + 0.70 * np.exp(-rz / 12.0)
            _, volz = C.window_light(cam, np.full_like(z, rz + 0.01), HALF_W, L=LDIR,
                                     win_z0=WIN_Z0, pitch=PITCH, win_half=WIN_HALF,
                                     win_y0=WIN_Y0, win_y1=WIN_Y1, steps=1, zmax=rz)
            y0, y1, x0, x1 = box
            sl, _ = C.window_light(cam, np.full_like(z, rz), HALF_W, L=LDIR,
                                   win_z0=WIN_Z0, pitch=PITCH, win_half=WIN_HALF,
                                   win_y0=WIN_Y0, win_y1=WIN_Y1, steps=1, zmax=rz)
            shade = (lit_here * 0.55 + sl[y0:y1, x0:x1] * 1.30)[..., None]
            C.over_box(img, rgb * shade, a, box)

        # 걸이 봉
        rbox = cam.box_of(rz, X_OUT + 0.08, Y_TOP + 0.10, Y_TOP - 0.02, pad=2)
        if rbox is not None:
            rwx, rwy = cam.sub_world(rz, rbox)
            ax = np.abs(rwx)
            rod = (ax > X_IN - 0.06) & (ax < X_OUT + 0.06) & (rwy > Y_TOP) & (rwy < Y_TOP + 0.055)
            C.over_box(img, np.array([0.040, 0.034, 0.026], np.float32),
                       np.where(rod, 0.95, 0.0).astype(np.float32), rbox)

    # ── 인물 (빛기둥 속 실루엣)
    for pz, xp, h, pose, hb, fc in ((15.0, 0.20, 1.60, 3, True, 1),
                                    (8.6, -0.55, 1.66, 1, False, -1),
                                    (4.6, 0.75, 1.63, 3, False, 1)):
        m, pbox = C.person(cam, pz, xp, h, pose, hanbok=hb, facing=fc)
        if m is None:
            continue
        att = 0.016 + 0.055 * np.exp(-pz / 9.0)
        C.over_box(img, np.array([att, att * 0.90, att * 0.76], np.float32), m * 0.97, pbox)

    # ── 빛기둥(공기 산란) + 밀가루 먼지
    dustn = 0.60 + 0.40 * C.fbm(Xn * 6.0, Yn * 4.2, seed=41, octaves=5)
    img += (vol * dustn * 2.35)[..., None] * np.array([1.0, 0.945, 0.815], np.float32)
    pn = C.fbm(Xn * 200.0, Yn * 200.0, seed=61, octaves=2)
    sp = C.sat((pn - 0.880) * 11.0) * (0.10 + 7.0 * vol)
    img += (sp * 0.55)[..., None] * np.array([1.0, 0.96, 0.87], np.float32)

    # ── 룩
    img = C.bloom(img, thresh=0.46, radius=0.030, amount=0.66)
    img = C.filmic(img * 1.16)
    img = C.monotint(img, tint=(1.045, 0.893, 0.686), black=0.018, white=0.972,
                     gamma=0.94, s_curve=0.70,
                     split=((0.80, 0.87, 1.06), (1.08, 1.00, 0.89)))
    img = C.vignette(cam, img, amount=0.60, power=1.85)
    img = C.grain(img, amount=0.038, seed=6, size=1.35)
    return cam, img


if __name__ == "__main__":
    cam, img = render()
    p = os.path.join(OUT, "s02.webp")
    C.save(cam, img, p, quality=84)
    print("s02.webp", os.path.getsize(p) // 1024, "KB")
