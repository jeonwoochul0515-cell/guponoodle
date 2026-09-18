# -*- coding: utf-8 -*-
"""s05 — 지금의 낙동강. 금빛 노을과 구포대교. 흑백이 걷히고 현재가 된다."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cine as C

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cinema")
os.makedirs(OUT, exist_ok=True)
SS = int(os.environ.get("SS", "2"))

FOG = np.array([0.720, 0.590, 0.430], np.float32)
D = 0.0060


def render():
    cam = C.Cam(1920, 1080, ss=SS, focal=1150.0, vp=(0.5, 0.488), eye=1.55)
    img = cam.new()
    Xn = cam.X / cam.rw
    Yn = cam.Y / cam.rh
    hor = cam.cy

    # ── 노을 하늘
    t = C.sat(np.broadcast_to(cam.Y, (cam.rh, cam.rw)) / hor)
    sky = C.mix(np.array([0.055, 0.085, 0.175], np.float32),
                np.array([0.330, 0.255, 0.290], np.float32),
                C.smoothstep(0.0, 0.58, t)[..., None])
    sky = C.mix(sky, np.array([0.920, 0.545, 0.245], np.float32),
                C.smoothstep(0.55, 0.92, t)[..., None])
    sky = C.mix(sky, np.array([1.150, 0.760, 0.380], np.float32),
                C.smoothstep(0.90, 1.0, t)[..., None])
    # 구름 — 노을빛을 받는 아래쪽이 밝다
    cl = C.fbm(Xn * 2.4, Yn * 6.0, seed=21, octaves=6)
    cband = C.sat((cl - 0.44) * 2.8) * C.smoothstep(0.06, 0.45, t) * (1.0 - C.smoothstep(0.86, 1.0, t))
    sky = C.mix(sky, np.array([0.118, 0.092, 0.126], np.float32), (cband * 0.72)[..., None])
    sky += (cband * C.smoothstep(0.40, 0.94, t) * 1.45)[..., None] * \
        np.array([1.12, 0.58, 0.24], np.float32)
    # 높은 생량운 띄 — 하늘을 가르진다
    cs = C.fbm(Xn * 1.5 + 9.0, Yn * 11.0, seed=23, octaves=5)
    sky += (C.sat((cs - 0.52) * 3.0) * C.smoothstep(0.10, 0.52, t) *
            (1.0 - C.smoothstep(0.62, 0.86, t)) * 0.50)[..., None] * \
        np.array([1.05, 0.66, 0.42], np.float32)
    img[:] = sky

    # ── 해
    sunx, suny = 0.5 * cam.rw, hor - 0.012 * cam.rh
    rd = np.sqrt((cam.X - sunx) ** 2 + (cam.Y - suny) ** 2) / cam.rw
    img += (np.exp(-rd * 34.0) * 1.35)[..., None] * np.array([1.0, 0.80, 0.50], np.float32)
    img += (np.exp(-rd * 5.2) * 0.34)[..., None] * np.array([1.0, 0.66, 0.34], np.float32)

    # ── 먼 산 + 도시 스카이라인
    ridge = hor - 0.052 * cam.rh * (C.fbm1(Xn[0] * 3.4 + 7.0, seed=31, octaves=5) - 0.32)
    m = C.smoothstep(-1.5, 1.5, cam.Y - ridge[None, :]) * C.smoothstep(hor + 8, hor - 40, cam.Y)
    img = C.over(img, np.array([0.115, 0.098, 0.128], np.float32),
                 np.broadcast_to(m, (cam.rh, cam.rw)) * 0.88)

    # 아파트 스카이라인 — 구포 건너편
    bw = 0.028
    idx = np.floor(Xn[0] / bw)
    bh = 0.020 + 0.055 * C.fbm1(idx * 2.3, seed=33, octaves=3)
    top = hor - bh * cam.rh
    bm = C.smoothstep(-1.2, 1.2, cam.Y - top[None, :]) * C.smoothstep(hor + 6, hor - 30, cam.Y)
    img = C.over(img, np.array([0.085, 0.072, 0.100], np.float32),
                 np.broadcast_to(bm, (cam.rh, cam.rw)) * 0.92)
    # 창문 불빛
    wx_ = (Xn * cam.rw / 6.0)
    wy_ = (cam.Y / 7.0)
    wlit = (C.fbm(wx_ * 0.9, wy_ * 0.9, seed=34, octaves=2) > 0.66).astype(np.float32)
    grid = ((np.abs(((Xn * cam.rw / 6.0) % 1.0) - 0.5) < 0.26) &
            (np.abs(((cam.Y / 7.0) % 1.0) - 0.5) < 0.24)).astype(np.float32)
    img += (np.broadcast_to(bm, (cam.rh, cam.rw)) * wlit * grid * 0.55)[..., None] * \
        np.array([1.0, 0.80, 0.48], np.float32)

    # ── 구포대교 — 수평 상판 + 교각
    deck_y0 = hor - 0.042 * cam.rh
    deck_y1 = hor - 0.016 * cam.rh
    deck = C.smoothstep(deck_y0 - 2, deck_y0 + 2, cam.Y) * (1.0 - C.smoothstep(deck_y1 - 2, deck_y1 + 2, cam.Y))
    deck = np.broadcast_to(deck, (cam.rh, cam.rw))
    img = C.over(img, np.array([0.070, 0.060, 0.082], np.float32), deck * 0.95)
    # 난간
    rail = C.smoothstep(deck_y0 - 7, deck_y0 - 5, cam.Y) * (1.0 - C.smoothstep(deck_y0 - 3, deck_y0 - 1, cam.Y))
    img = C.over(img, np.array([0.095, 0.082, 0.105], np.float32),
                 np.broadcast_to(rail, (cam.rh, cam.rw)) * 0.75)
    # 가로등 불빛
    lampx = np.abs(((Xn * 26.0) % 1.0) - 0.5) < 0.055
    lampy = C.smoothstep(deck_y0 - 12, deck_y0 - 9, cam.Y) * (1.0 - C.smoothstep(deck_y0 - 7, deck_y0 - 4, cam.Y))
    img += (lampx * np.broadcast_to(lampy, (cam.rh, cam.rw)) * 1.1)[..., None] * \
        np.array([1.0, 0.82, 0.52], np.float32)
    # 교각
    pier = (np.abs(((Xn * 7.0) % 1.0) - 0.5) < 0.030)
    piery = C.smoothstep(deck_y1 - 1, deck_y1 + 1, cam.Y) * (1.0 - C.smoothstep(hor + 0.030 * cam.rh, hor + 0.042 * cam.rh, cam.Y))
    img = C.over(img, np.array([0.062, 0.053, 0.072], np.float32),
                 (pier * np.broadcast_to(piery, (cam.rh, cam.rw))) * 0.9)

    # ── 강물
    riv = C.smoothstep(hor - 1, hor + 3, cam.Y)
    zw = np.where(np.broadcast_to(cam.dy, (cam.rh, cam.rw)) > 0.35,
                  1.55 * cam.f / np.maximum(np.broadcast_to(cam.dy, (cam.rh, cam.rw)), 0.35), 4000.0)
    wxw = np.broadcast_to(cam.dx, (cam.rh, cam.rw)) * zw / cam.f
    water = np.array([0.100, 0.098, 0.135], np.float32)
    img = C.over(img, water, np.broadcast_to(riv, (cam.rh, cam.rw)) * 0.96)
    # 금빛 반사 기둥
    ripple = C.fbm(wxw * 2.2, zw * 0.30, seed=41, octaves=5)
    ripple2 = C.fbm(wxw * 9.0, zw * 1.1, seed=42, octaves=4)
    streak = np.exp(-(wxw / (1.6 + zw * 0.035)) ** 2)
    glint = C.sat((ripple * 0.6 + ripple2 * 0.4 - 0.47) * 4.6) * streak * riv
    img += (glint * 1.5)[..., None] * np.array([1.0, 0.73, 0.38], np.float32)
    sparkle = C.sat((C.fbm(wxw * 26.0, zw * 3.2, seed=43, octaves=3) - 0.74) * 7.0) * riv * \
        np.exp(-np.abs(wxw) / 6.0)
    img += (sparkle * 0.9)[..., None] * np.array([1.0, 0.85, 0.58], np.float32)

    # ── 앞쪽 강변 둔치 + 갈대
    bank_y = hor + 0.300 * cam.rh
    bank = C.smoothstep(bank_y - 4, bank_y + 4, cam.Y)
    bank = np.broadcast_to(bank, (cam.rh, cam.rw))
    zb = np.where(np.broadcast_to(cam.dy, (cam.rh, cam.rw)) > 0.35,
                  1.55 * cam.f / np.maximum(np.broadcast_to(cam.dy, (cam.rh, cam.rw)), 0.35), 4000.0)
    wxb = np.broadcast_to(cam.dx, (cam.rh, cam.rw)) * zb / cam.f
    gt = 0.048 + 0.062 * C.fbm(wxb * 2.6, zb * 2.6, seed=51, octaves=5)
    img = C.over(img, np.stack([gt * 1.02, gt * 0.95, gt * 0.80], -1), bank * 0.97)

    # 산책로 — 강변을 따라 휘는 밝은 선
    pathw = 0.34 + 0.10 * C.fbm1(zb[:, 0] * 0.5, seed=52, octaves=3)
    pm2 = C.smoothstep(pathw[:, None] + 0.10, pathw[:, None] - 0.10,
                       np.abs(wxb - 0.6 - 0.35 * C.fbm(zb * 0.22, wxb * 0.0 + 3.0, seed=53, octaves=3)))
    img = C.over(img, np.array([0.135, 0.118, 0.108], np.float32), bank * pm2 * 0.85)

    # 강바람에 누운 풀 — 화면 맨 아래 에지만 부드럽게
    grass = C.fbm(Xn * 46.0, Yn * 5.0, seed=61, octaves=4)
    gm = C.smoothstep(0.955, 1.0, Yn + 0.035 * (grass - 0.5))
    img = C.over(img, np.array([0.058, 0.050, 0.055], np.float32),
                 np.broadcast_to(gm, (cam.rh, cam.rw)) * 0.80)

    # ── 대기 · 룩
    haze = C.smoothstep(0.42, 0.50, Yn) * (1.0 - C.smoothstep(0.52, 0.72, Yn))
    img = C.over(img, FOG, C.sat(np.broadcast_to(haze, (cam.rh, cam.rw))) * 0.22)
    img = C.god_rays(cam, img, (0.5, 0.488), strength=0.085,
                     tint=(1.0, 0.72, 0.40), seed=91, near=40.0, far=6.2)
    img = C.bloom(img, thresh=0.52, radius=0.030, amount=0.72)
    img = C.filmic(img * 1.10)
    img = C.grade(img, gain=(1.05, 0.995, 0.955), gamma=0.97,
                  saturation=1.10, contrast=1.08, pivot=0.44)
    img = C.vignette(cam, img, amount=0.50, power=1.9)
    img = C.grain(img, amount=0.024, seed=9, size=1.30)
    return cam, img


if __name__ == "__main__":
    cam, img = render()
    p = os.path.join(OUT, "s05.webp")
    C.save(cam, img, p, quality=84)
    print("s05.webp", os.path.getsize(p) // 1024, "KB")
