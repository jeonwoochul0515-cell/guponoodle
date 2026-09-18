# -*- coding: utf-8 -*-
"""s04 — 1980년대 구포 제면소. 형광등과 스테인리스 건조 랙. 여기서 색이 돌아온다."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cinema")
os.makedirs(OUT, exist_ok=True)
SS = int(os.environ.get("SS", "2"))

HALF_W, CEIL_H, BACK_Z = 4.55, 2.68, 23.0
EYE = 1.26
WIN_Z0, PITCH, WIN_HALF = 4.2, 5.6, 1.55
WIN_Y0, WIN_Y1 = 0.26, 1.66
LDIR = (0.86, -0.40, 0.20)


def render():
    cam = C.Cam(1920, 1080, ss=SS, focal=1120.0, vp=(0.5, 0.470), eye=EYE)
    img = cam.new()
    Xn = cam.X / cam.rw
    Yn = cam.Y / cam.rh

    z, surf, u, v, wx, wy = C.room(cam, HALF_W, CEIL_H, BACK_Z)
    is_f, is_c = surf == C.FLOOR, surf == C.CEIL
    is_l, is_r = surf == C.LEFT, surf == C.RIGHT
    is_b = surf == C.BACK

    alb = np.zeros_like(img)

    # 바닥: 젖은 타일
    ft = 0.36 + 0.16 * C.fbm(u * 2.4, v * 2.4, seed=11, octaves=5)
    grout = (np.abs(((u / 0.60) % 1.0) - 0.5) > 0.452) | (np.abs(((v / 0.60) % 1.0) - 0.5) > 0.452)
    ft = np.where(grout, ft * 0.60, ft)
    wetf = C.sat((C.fbm(u * 0.9, v * 0.9, seed=13, octaves=4) - 0.50) * 2.6)
    ft *= (1.0 - 0.22 * wetf)
    alb[is_f] = np.stack([ft * 0.95, ft * 0.985, ft], -1)[is_f]

    # 천장: 흰 판 + 형광등 줄
    ct = 0.66 + 0.12 * C.fbm(u * 3.4, v * 3.4, seed=14, octaves=4)
    alb[is_c] = np.stack([ct * 0.97, ct, ct * 0.97], -1)[is_c]

    # 벽: 허리 아래 초록 페인트
    wt = 0.54 + 0.20 * C.fbm(u * 1.9, v * 3.8, seed=15, octaves=5)
    dado = v < 0.58
    wall = np.where(dado[..., None],
                    np.stack([wt * 0.42, wt * 0.78, wt * 0.60], -1),
                    np.stack([wt * 0.99, wt, wt * 0.95], -1))
    alb[is_l] = wall[is_l]
    alb[is_r] = (wall * 0.94)[is_r]

    # 뒷벽 + 열린 문
    bt = 0.46 + 0.16 * C.fbm(u * 2.4, v * 2.8, seed=16, octaves=4)
    bcol = np.stack([bt * 0.95, bt, bt * 0.96], -1)
    door = (np.abs(u - 0.55) < 0.62) & (v > -EYE) & (v < 0.80)
    bcol = np.where(door[..., None], np.array([2.30, 2.34, 2.40], np.float32), bcol)
    alb[is_b] = bcol[is_b]

    # ── 창빛
    surf_lit, vol = C.window_light(cam, z, HALF_W, L=LDIR, win_z0=WIN_Z0, pitch=PITCH,
                                   win_half=WIN_HALF, win_y0=WIN_Y0, win_y1=WIN_Y1,
                                   steps=18, zmax=BACK_Z)
    ndl = np.where(is_f, 0.45, np.where(is_r, 0.78, np.where(is_b, 0.22, 0.10)))
    amb = 0.44 + 0.34 * np.exp(-z / 14.0)
    img[:] = alb * (amb * 0.46 + surf_lit * ndl * 0.92)[..., None] * \
        np.array([1.0, 0.995, 0.975], np.float32)

    # ── 형광등: 천장에 z 방향 줄조명 두 줄
    for lx in (-1.55, 1.55):
        zc = np.where(np.broadcast_to(cam.dy, (cam.rh, cam.rw)) < -0.35,
                      CEIL_H * cam.f / np.maximum(-np.broadcast_to(cam.dy, (cam.rh, cam.rw)), 0.35),
                      1e9)
        wxc = np.broadcast_to(cam.dx, (cam.rh, cam.rw)) * zc / cam.f
        tube = (np.abs(wxc - lx) < 0.11) & (zc > 1.6) & (zc < BACK_Z) & \
               (np.abs(((zc - 1.0) % 3.0) - 1.5) < 1.05)
        img = C.over(img, np.array([2.10, 2.16, 2.24], np.float32),
                     np.where(tube, 1.0, 0.0).astype(np.float32))
        halo = (np.abs(wxc - lx) < 0.45) & (zc > 1.6) & (zc < BACK_Z)
        img += np.where(halo, 0.055, 0.0).astype(np.float32)[..., None] * \
            np.array([1.0, 1.0, 1.02], np.float32)

    # ── 창 개구부
    dzw = ((u - (WIN_Z0 + PITCH * 0.5)) % PITCH) - PITCH * 0.5
    win = is_l & (np.abs(dzw) < WIN_HALF) & (wy > WIN_Y0) & (wy < WIN_Y1)
    frame = is_l & (np.abs(dzw) < WIN_HALF + 0.12) & (wy > WIN_Y0 - 0.11) & (wy < WIN_Y1 + 0.11)
    img = C.over(img, np.array([0.16, 0.17, 0.18], np.float32),
                 np.where(frame & ~win, 0.92, 0.0).astype(np.float32))
    glow = 1.45 / (1.0 + (np.maximum(u, 0.2) / 9.0) ** 1.4)
    img = C.over(img, np.stack([glow * 1.02, glow * 1.06, glow * 1.12], -1),
                 np.where(win & (np.abs(dzw) > 0.035), 1.0, 0.0).astype(np.float32))

    # ── 스테인리스 건조 랙 (두 층)
    RACK = [19.0, 14.6, 11.2, 8.5, 6.4, 4.8, 3.6, 2.75]
    X_IN, X_OUT = 1.88, 4.50
    for lev, (yt, yb) in enumerate(((1.34, 0.44), (0.30, -0.52))):
        for i, rz in enumerate(RACK):
            rgb, a, box = C.noodle_curtain(
                cam, rz, X_IN, X_OUT, yt, yb,
                period=0.0105, seed=310 + lev * 40 + i * 4, sway=0.022, ragged=0.10,
                bright=(0.92, 0.900, 0.845), dark=(0.235, 0.238, 0.228),
                base_alpha=0.96, bundle=0.72, bundle_w=0.36)
            if a is not None:
                sl, _ = C.window_light(cam, np.full_like(z, rz), HALF_W, L=LDIR,
                                       win_z0=WIN_Z0, pitch=PITCH, win_half=WIN_HALF,
                                       win_y0=WIN_Y0, win_y1=WIN_Y1, steps=1, zmax=rz)
                y0, y1, x0, x1 = box
                sh = (0.70 + 0.30 * np.exp(-rz / 12.0)) * 0.72 + sl[y0:y1, x0:x1] * 0.85
                C.over_box(img, rgb * sh[..., None], a, box)

            rbox = cam.box_of(rz, X_OUT + 0.08, yt + 0.10, yt - 0.02, pad=2)
            if rbox is not None:
                rwx, rwy = cam.sub_world(rz, rbox)
                ax = np.abs(rwx)
                rod = (ax > X_IN - 0.06) & (ax < X_OUT + 0.06) & (rwy > yt) & (rwy < yt + 0.05)
                C.over_box(img, np.array([0.40, 0.418, 0.442], np.float32),
                           np.where(rod, 0.96, 0.0).astype(np.float32), rbox)

    # ── 랙 수직 기둥 (스테인리스)
    for rz in RACK:
        pbox = cam.box_of(rz, X_OUT + 0.1, 1.50, -EYE, pad=2)
        if pbox is None:
            continue
        pwx, pwy = cam.sub_world(rz, pbox)
        ax = np.abs(pwx)
        post = ((np.abs(ax - (X_IN + 0.05)) < 0.035) | (np.abs(ax - (X_OUT - 0.25)) < 0.032)) & \
               (pwy < 1.46) & (pwy > -EYE)
        C.over_box(img, np.array([0.345, 0.362, 0.386], np.float32),
                   np.where(post, 0.95, 0.0).astype(np.float32), pbox)

    # ── 인물 (작업복)
    for pz, xp, h, pose, fc in ((12.5, 0.28, 1.62, 3, 1),
                                (7.2, -0.58, 1.68, 1, -1),
                                (4.2, 0.80, 1.60, 3, 1)):
        m, pbox = C.person(cam, pz, xp, h, pose, hanbok=False, facing=fc)
        if m is None:
            continue
        att = 0.085 + 0.13 * np.exp(-pz / 9.0)
        C.over_box(img, np.array([att * 0.78, att * 0.88, att], np.float32), m * 0.97, pbox)

    # ── 공기: 밀가루 먼지 약간
    dustn = 0.60 + 0.40 * C.fbm(Xn * 6.0, Yn * 4.2, seed=41, octaves=5)
    img += (vol * dustn * 1.15)[..., None] * np.array([1.0, 0.985, 0.945], np.float32)
    pn = C.fbm(Xn * 200.0, Yn * 200.0, seed=61, octaves=2)
    img += (C.sat((pn - 0.892) * 11.0) * (0.08 + 4.0 * vol) * 0.42)[..., None] * \
        np.array([1.0, 0.99, 0.95], np.float32)

    # ── 룩: 여기서부터 색이 돌아온다
    img = C.bloom(img, thresh=0.56, radius=0.026, amount=0.46)
    img = C.filmic(img * 0.92)
    img = C.grade(img, gain=(1.02, 1.005, 0.975), gamma=0.99,
                  saturation=1.02, contrast=1.13, pivot=0.44)
    img = C.mix(img, C.monotint(img, tint=(1.02, 0.955, 0.870), s_curve=0.45), np.float32(0.14))
    img = C.vignette(cam, img, amount=0.44, power=1.9)
    img = C.grain(img, amount=0.026, seed=8, size=1.30)
    return cam, img


if __name__ == "__main__":
    cam, img = render()
    p = os.path.join(OUT, "s04.webp")
    C.save(cam, img, p, quality=84)
    print("s04.webp", os.path.getsize(p) // 1024, "KB")
