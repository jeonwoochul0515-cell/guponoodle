# -*- coding: utf-8 -*-
"""s01 — 1940년대 낙동강 국수 건조장 아침. 소실점으로 빨려드는 국수 터널."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cinema")
os.makedirs(OUT, exist_ok=True)
SS = int(os.environ.get("SS", "2"))

FOG = np.array([0.505, 0.470, 0.408], np.float32)
D = 0.0068


def render():
    cam = C.Cam(1920, 1080, ss=SS, focal=1150.0, vp=(0.5, 0.452), eye=1.55)
    img = cam.new()
    Xn = cam.X / cam.rw
    Yn = cam.Y / cam.rh
    hor = cam.cy

    # ── 하늘
    t = C.sat(np.broadcast_to(cam.Y, (cam.rh, cam.rw)) / hor)
    sky = C.mix(np.array([0.098, 0.092, 0.084], np.float32),
                np.array([0.290, 0.263, 0.222], np.float32),
                C.smoothstep(0.0, 0.72, t)[..., None])
    sky = C.mix(sky, np.array([0.610, 0.562, 0.472], np.float32),
                C.smoothstep(0.64, 1.0, t)[..., None])
    cl = C.fbm(Xn * 2.6, Yn * 7.0, seed=21, octaves=5)
    cl = C.sat((cl - 0.44) * 3.0) * C.smoothstep(0.04, 0.42, t) * (1.0 - C.smoothstep(0.80, 1.0, t))
    sky += (cl * 0.135)[..., None] * np.array([1.0, 0.95, 0.86], np.float32)
    cl2 = C.fbm(Xn * 7.5 + 4.0, Yn * 19.0, seed=22, octaves=4)
    sky -= (C.sat((cl2 - 0.60) * 2.0) * C.smoothstep(0.10, 0.55, t) *
            (1.0 - C.smoothstep(0.76, 1.0, t)) * 0.022)[..., None]
    img[:] = sky

    # ── 해 — 소실점 바로 위, 역광의 근원
    sunx, suny = 0.5 * cam.rw, hor - 0.020 * cam.rh
    rd = np.sqrt((cam.X - sunx) ** 2 + (cam.Y - suny) ** 2) / cam.rw
    img += (np.exp(-rd * 30.0) * 0.95)[..., None] * np.array([1.0, 0.95, 0.83], np.float32)
    img += (np.exp(-rd * 5.0) * 0.15)[..., None] * np.array([1.0, 0.90, 0.74], np.float32)

    # ── 원산
    for amp, base, col, op, sd in ((0.055, 0.014, (0.200, 0.185, 0.160), 0.85, 31),
                                   (0.033, 0.004, (0.150, 0.137, 0.117), 0.88, 32),
                                   (0.016, -0.005, (0.112, 0.102, 0.086), 0.85, 33)):
        ridge = hor - base * cam.rh - amp * cam.rh * (C.fbm1(Xn[0] * 4.0 + sd, seed=sd, octaves=5) - 0.35)
        m = C.smoothstep(-1.5, 1.5, cam.Y - ridge[None, :]) * C.smoothstep(hor + 8, hor - 30, cam.Y)
        img = C.over(img, np.array(col, np.float32), np.broadcast_to(m, (cam.rh, cam.rw)) * op)

    # ── 낙동강
    rb0, rb1 = hor - 0.003 * cam.rh, hor + 0.024 * cam.rh
    riv = C.smoothstep(rb0 - 2, rb0 + 3, cam.Y) * (1.0 - C.smoothstep(rb1 - 5, rb1 + 3, cam.Y))
    riv = np.broadcast_to(riv, (cam.rh, cam.rw))
    img = C.over(img, np.array([0.268, 0.247, 0.212], np.float32), riv * 0.95)
    st = C.fbm(Xn * 55.0, (cam.Y - rb0) / (rb1 - rb0) * 2.4, seed=41, octaves=3)
    glint = C.sat((st - 0.57) * 4.2) * riv * np.exp(-np.abs(Xn - 0.5) * 3.2)
    img += (glint * 0.80)[..., None] * np.array([1.0, 0.96, 0.87], np.float32)

    # ── 지면: 낙동강 모래 둑
    zg, gm = cam.ground_z()
    wxg = np.broadcast_to(cam.dx, (cam.rh, cam.rw)) * zg / cam.f
    uu, vv = wxg * 1.5, zg * 1.5
    tone = 0.100 + 0.140 * C.fbm(uu, vv, seed=51, octaves=5) \
                 + 0.050 * C.fbm(uu * 6.0, vv * 6.0, seed=52, octaves=3)
    wet = C.sat((C.fbm(uu * 0.45, vv * 0.45, seed=53, octaves=4) - 0.54) * 3.2)
    tone = tone * (1.0 - 0.42 * wet)
    # 다져진 통로 — 바퀴 자국 두 줄
    ruts = np.exp(-((np.abs(wxg) - 0.85) / 0.24) ** 2)
    tone *= (1.0 - 0.10 * C.smoothstep(2.4, 0.6, np.abs(wxg)) - 0.22 * ruts)
    gnd = np.stack([tone, tone * 0.928, tone * 0.802], -1)
    gnd = C.mix(gnd, FOG.reshape(1, 1, 3), (1.0 - np.exp(-zg * D))[..., None] * 0.96)
    img = C.over(img, gnd, np.where(gm, 1.0, 0.0).astype(np.float32))

    # ── 건조대
    Z = [172.0, 120.0, 85.0, 61.0, 44.0, 32.0, 23.2, 16.8, 12.1, 8.7, 6.3, 4.55, 3.30, 2.42]
    X_IN, X_OUT = 1.95, 9.60
    Y_TOP, Y_BOT = 0.88, -1.20

    # ── 원경 갈대밭 (건조장 바깥)
    redge = 8.4 + 1.6 * C.fbm(zg * 0.45, wxg * 0.3, seed=62, octaves=3)
    rmask = C.smoothstep(-0.6, 0.6, np.abs(wxg) - redge) * C.smoothstep(12.0, 26.0, zg) * \
        (1.0 - C.smoothstep(700.0, 1200.0, zg))
    rn = C.fbm(wxg * 5.0, zg * 0.7, seed=61, octaves=3)
    rcol = np.stack([0.105 + 0.105 * rn, 0.099 + 0.095 * rn, 0.084 + 0.077 * rn], -1)
    rcol = C.mix(rcol, FOG.reshape(1, 1, 3), (1.0 - np.exp(-zg * D))[..., None] * 0.96)
    img = C.over(img, rcol, rmask * np.float32(0.88))

    # 그림자 — 해가 정면, 그림자는 카메라 쪽으로 눕는다.
    # 국수 가닥 사이로 빛이 새므로 줄무늬가 남는다.
    stripe = 0.52 + 0.48 * C.fbm1(wxg * 26.0, seed=64, octaves=3)
    for z in Z[2:11]:
        sh = C.smoothstep(-0.25, 0.25, np.abs(wxg) - X_IN * 0.94) * \
            (1.0 - C.smoothstep(X_OUT * 0.9, X_OUT * 1.15, np.abs(wxg))) * \
            C.smoothstep(z * 1.02, z * 0.88, zg) * C.smoothstep(z * 0.42, z * 0.58, zg)
        img *= (1.0 - sh * stripe * np.float32(0.46))[..., None]

    # 인물 — 통로 안에만 세운다. 발밑 접지 그림자가 없으면 사람이 뜬다.
    PEOPLE = [(30.0, -1.52, 1.60, 1, True, 1),
              (24.0, 0.80, 1.58, 0, True, -1),
              (19.0, 1.60, 1.56, 0, True, -1),
              (12.4, -1.02, 1.67, 2, False, 1),
              (9.4, -0.70, 1.10, 5, False, 1),
              (7.6, -1.40, 1.62, 1, False, 1)]
    sh_acc = np.zeros((cam.rh, cam.rw), np.float32)
    for pz, xp, _h, _p, _hb, _fc in PEOPLE:
        sh_acc += C.contact_shadow(wxg, zg, xp, pz, rx=0.30, rz=0.42, strength=0.66)
    img *= (1.0 - C.sat(sh_acc) * np.float32(0.60))[..., None]

    def draw_people(z_far, z_near):
        """z_near < pz <= z_far 구간의 사람"""
        for pz, xp, h, pose, hb, fc in PEOPLE:
            if not (z_near < pz <= z_far):
                continue
            m, pbox = C.person(cam, pz, xp, h, pose, hanbok=hb, facing=fc)
            if m is None:
                continue
            pfg = float(1.0 - np.exp(-pz * D))
            col = C.mix(np.array([0.030, 0.026, 0.021], np.float32), FOG, np.float32(pfg * 0.93))
            C.over_box(img, col, m * np.float32(0.96), pbox)

    for i, z in enumerate(Z):
        draw_people(Z[i - 1] if i else 1e9, z)
        fg = float(1.0 - np.exp(-z * D))
        rgb, a, box = C.noodle_curtain(
            cam, z, X_IN, X_OUT, Y_TOP, Y_BOT,
            period=0.0115, seed=60 + i * 4, sway=0.085, ragged=0.30,
            bright=(0.960, 0.926, 0.850), dark=(0.150, 0.136, 0.114),
            base_alpha=0.94, bundle=0.62, bundle_w=0.50)
        if a is not None:
            rgb = C.mix(rgb, FOG.reshape(1, 1, 3), np.float32(fg * 0.96))
            C.over_box(img, rgb, a * np.float32(1.0 - fg * 0.22), box)

        # 목재 프레임
        fbox = cam.box_of(z, X_OUT + 0.1, Y_TOP + 0.10, -cam.eye - 0.02, pad=3)
        if fbox is None:
            continue
        wx, wy = cam.sub_world(z, fbox)
        ax = np.abs(wx)
        bar = (ax > X_IN - 0.07) & (ax < X_OUT + 0.07) & (wy > Y_TOP) & (wy < Y_TOP + 0.052)
        bar = bar & (wy < Y_TOP + 0.038 + 0.014 * C.fbm1(ax * 3.0 + z, seed=66, octaves=2))
        legs = ((np.abs(ax - (X_IN + 0.10)) < 0.026) | (np.abs(ax - (X_OUT - 0.30)) < 0.024) |
                (np.abs(ax - (X_IN + X_OUT) * 0.5) < 0.022)) & (wy < Y_TOP + 0.03) & (wy > -1.56)
        wood = C.mix(np.array([0.046, 0.040, 0.031], np.float32), FOG, np.float32(fg * 0.96))
        C.over_box(img, wood, np.where(bar | legs, 0.95, 0.0).astype(np.float32), fbox)

    draw_people(Z[-1], 0.0)

    # ── 공중 입자 (역광에 반짝)
    part = C.fbm(Xn * 175.0, Yn * 175.0, seed=71, octaves=2)
    pm = C.sat((part - 0.888) * 10.0) * C.smoothstep(0.22, 0.92, Yn) * np.exp(-np.abs(Xn - 0.5) * 1.5)
    img += (pm * 0.40)[..., None] * np.array([1.0, 0.97, 0.90], np.float32)

    # ── 수평선 물안개
    mist = C.smoothstep(0.405, 0.475, Yn) * (1.0 - C.smoothstep(0.49, 0.66, Yn))
    mn = C.fbm(Xn * 3.4, Yn * 6.5, seed=81, octaves=4)
    img = C.over(img, FOG, C.sat(np.broadcast_to(mist, (cam.rh, cam.rw)) * (0.28 + 0.45 * mn)) * 0.46)

    # ── 광선 · 블룸 · 필름 룩
    img = C.god_rays(cam, img, (0.5, 0.452), strength=0.062,
                     tint=(1.0, 0.94, 0.80), seed=91, near=46.0, far=7.4)
    img = C.bloom(img, thresh=0.50, radius=0.026, amount=0.58)
    img = C.filmic(img * 1.14)
    img = C.monotint(img, tint=(1.035, 0.900, 0.705), black=0.014, white=0.962,
                     gamma=0.97, s_curve=0.60,
                     split=((0.85, 0.895, 1.03), (1.06, 1.00, 0.92)))
    img = C.vignette(cam, img, amount=0.50, power=1.9)
    img = C.grain(img, amount=0.032, seed=5, size=1.35)
    return cam, img


if __name__ == "__main__":
    cam, img = render()
    p = os.path.join(OUT, "s01.webp")
    C.save(cam, img, p, quality=84)
    print("s01.webp", os.path.getsize(p) // 1024, "KB")
