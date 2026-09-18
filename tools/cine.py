# -*- coding: utf-8 -*-
"""
구포국수 히어로 시네마 — 절차적 렌더 엔진.

픈셀 단위로 계산한다. 핀홀 카메라 + 깊이 레이어 합성 + 볼류메트릭 안개 +
블룸 + 필름 그레인 + 색 그레이딩. 의존성은 numpy / Pillow 둘뿐이다.

좌표계: 월드 x=오른쪽, y=위, z=카메라 정면. 카메라 원점, 눈높이는 장면이 정한다.
레이어는 화면 바운딩박스로 잘라서 계산한다 — 원경 레이어는 비용이 거의 없다.
"""
import numpy as np
from PIL import Image

# ─────────────────────────────────────────────────────────────
# 노이즈 — 1D / 2D 분리
# ─────────────────────────────────────────────────────────────
_T2, _T1 = {}, {}


def tex2(seed, size=256):
    k = (seed, size)
    if k not in _T2:
        _T2[k] = np.random.default_rng(seed * 7919 + 13).random((size, size)).astype(np.float32)
    return _T2[k]


def tex1(seed, size=8192):
    k = (seed, size)
    if k not in _T1:
        _T1[k] = np.random.default_rng(seed * 6151 + 7).random(size).astype(np.float32)
    return _T1[k]


def _clean(a):
    a = np.asarray(a, dtype=np.float32)
    if not np.isfinite(a).all():
        a = np.nan_to_num(a, nan=0.0, posinf=1e6, neginf=-1e6)
    return a


def sample2(t, u, v):
    n = t.shape[0]
    u = _clean(u) % np.float32(n)
    v = _clean(v) % np.float32(n)
    i0 = np.minimum(u.astype(np.int32), n - 1)
    j0 = np.minimum(v.astype(np.int32), n - 1)
    fu = u - i0
    fv = v - j0
    i1 = (i0 + 1) & (n - 1) if (n & (n - 1)) == 0 else (i0 + 1) % n
    j1 = (j0 + 1) & (n - 1) if (n & (n - 1)) == 0 else (j0 + 1) % n
    fu = fu * fu * (3.0 - 2.0 * fu)
    fv = fv * fv * (3.0 - 2.0 * fv)
    a = t[j0, i0]
    b = t[j0, i1]
    c = t[j1, i0]
    d = t[j1, i1]
    top = a + (b - a) * fu
    return top + ((c + (d - c) * fu) - top) * fv


def sample1(t, u):
    n = t.shape[0]
    u = _clean(u) % np.float32(n)
    i0 = np.minimum(u.astype(np.int32), n - 1)
    f = u - i0
    i1 = (i0 + 1) & (n - 1)
    f = f * f * (3.0 - 2.0 * f)
    a = t[i0]
    return a + (t[i1] - a) * f


def fbm(u, v, seed=1, octaves=4, lac=2.03, gain=0.5):
    t = tex2(seed)
    u = _clean(u)
    v = _clean(v)
    total = np.zeros(np.broadcast_shapes(u.shape, v.shape), np.float32)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        total += amp * sample2(t, u, v)
        norm += amp
        u = u * lac + 31.7
        v = v * lac + 17.3
        amp *= gain
    return total / norm


def fbm1(u, seed=1, octaves=4, lac=2.07, gain=0.5):
    """진짜 1D fbm. 가닥 흔들림·산 능선처럼 한 축만 변하는 것에 쓴다."""
    t = tex1(seed)
    u = _clean(u)
    total = np.zeros_like(u)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        total += amp * sample1(t, u)
        norm += amp
        u = u * lac + 41.3
        amp *= gain
    return total / norm


# ─────────────────────────────────────────────────────────────
# 블러
# ─────────────────────────────────────────────────────────────
def _box1(a, r, axis):
    if r < 1:
        return a
    a = np.moveaxis(a, axis, -1)
    n = a.shape[-1]
    pad = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(r, r)], mode="edge")
    c = np.cumsum(pad, axis=-1, dtype=np.float32)
    c = np.concatenate([np.zeros(c.shape[:-1] + (1,), np.float32), c], axis=-1)
    out = (c[..., 2 * r + 1:] - c[..., :n]) / np.float32(2 * r + 1)
    return np.moveaxis(out, -1, axis)


def blur(a, r, passes=3):
    r = int(max(0, r))
    if r < 1:
        return a.astype(np.float32)
    out = a.astype(np.float32)
    for _ in range(passes):
        out = _box1(out, r, 1)
        out = _box1(out, r, 0)
    return out


def blur_rgb(img, r, passes=3):
    if int(r) < 1:
        return img
    out = np.empty_like(img)
    for ch in range(img.shape[2]):
        out[:, :, ch] = blur(img[:, :, ch], r, passes)
    return out


# ─────────────────────────────────────────────────────────────
# 카메라
# ─────────────────────────────────────────────────────────────
class Cam:
    def __init__(self, w, h, ss=2, focal=1150.0, vp=(0.5, 0.44), eye=1.55):
        self.w, self.h, self.ss = w, h, ss
        self.rw, self.rh = int(w * ss), int(h * ss)
        self.f = focal * ss
        self.cx = vp[0] * self.rw
        self.cy = vp[1] * self.rh
        self.eye = eye
        self._x = (np.arange(self.rw, dtype=np.float32) + 0.5)
        self._y = (np.arange(self.rh, dtype=np.float32) + 0.5)
        self.X = self._x[None, :]
        self.Y = self._y[:, None]
        self.dx = self.X - self.cx
        self.dy = self.Y - self.cy
        rx = (self._x / self.rw - 0.5)[None, :]
        ry = (self._y / self.rh - 0.5)[:, None]
        self.rad = np.sqrt(rx * rx + ry * ry).astype(np.float32)

    # 전체 화면 월드
    def world(self, z):
        k = np.float32(z) / self.f
        return self.dx * k, -self.dy * k

    def ground_z(self, y_plane=None, far=4000.0):
        yp = self.eye if y_plane is None else y_plane
        d = np.broadcast_to(self.dy, (self.rh, self.rw))
        z = np.where(d > 0.35, yp * self.f / np.maximum(d, 0.35), np.float32(far))
        return np.clip(z, 0, far).astype(np.float32), (d > 0.35)

    # ── 바운딩박스 유틸
    def box_of(self, z, x_half, y_top, y_bot, pad=3, x_center=0.0):
        """깊이 z에서 |x-x_center|<=x_half, y_bot<=y<=y_top 인 영역의 화면 박스."""
        k = self.f / z
        x0 = int(np.floor(self.cx + (x_center - x_half) * k)) - pad
        x1 = int(np.ceil(self.cx + (x_center + x_half) * k)) + pad
        y0 = int(np.floor(self.cy - y_top * k)) - pad
        y1 = int(np.ceil(self.cy - y_bot * k)) + pad
        x0 = max(0, min(self.rw, x0)); x1 = max(0, min(self.rw, x1))
        y0 = max(0, min(self.rh, y0)); y1 = max(0, min(self.rh, y1))
        if x1 <= x0 or y1 <= y0:
            return None
        return (y0, y1, x0, x1)

    def sub_world(self, z, box):
        y0, y1, x0, x1 = box
        k = np.float32(z) / self.f
        wx = (self._x[x0:x1][None, :] - self.cx) * k
        wy = -(self._y[y0:y1][:, None] - self.cy) * k
        return wx, wy

    def new(self, rgb=(0, 0, 0)):
        img = np.empty((self.rh, self.rw, 3), np.float32)
        img[:] = np.array(rgb, np.float32)
        return img


FLOOR, CEIL, LEFT, RIGHT, BACK = 0, 1, 2, 3, 4


def room(cam, half_w, ceil_h, back_z, floor_y=None):
    """
    박스 형태 실내를 래스터화한다. 가시 표면의 깊이, 면 번호, 표면 uv를 돌린다.
    u,v 의미 - 바닥/천장: (x, z), 좌우벽: (z, y), 뒷벽: (x, y)
    """
    fy = cam.eye if floor_y is None else floor_y
    dx = np.broadcast_to(cam.dx, (cam.rh, cam.rw)).astype(np.float32)
    dy = np.broadcast_to(cam.dy, (cam.rh, cam.rw)).astype(np.float32)
    INF = np.float32(1e9)
    eps = np.float32(0.35)

    zf = np.where(dy > eps, fy * cam.f / np.maximum(dy, eps), INF)
    zc = np.where(dy < -eps, ceil_h * cam.f / np.maximum(-dy, eps), INF)
    zl = np.where(dx < -eps, half_w * cam.f / np.maximum(-dx, eps), INF)
    zr = np.where(dx > eps, half_w * cam.f / np.maximum(dx, eps), INF)
    zb = np.float32(back_z)

    z = np.minimum(np.minimum(np.minimum(zf, zc), np.minimum(zl, zr)), zb)
    surf = np.full(dx.shape, BACK, np.uint8)
    surf[z == zf] = FLOOR
    surf[z == zc] = CEIL
    surf[z == zl] = LEFT
    surf[z == zr] = RIGHT
    surf[z >= zb] = BACK

    k = z / cam.f
    wx = dx * k
    wy = -dy * k
    u = np.where((surf == LEFT) | (surf == RIGHT), z, wx).astype(np.float32)
    v = np.where((surf == FLOOR) | (surf == CEIL), z, wy).astype(np.float32)
    return z, surf, u, v, wx, wy


def window_light(cam, z_surf, half_w, L=(0.80, -0.56, 0.24),
                 win_z0=5.0, pitch=4.6, win_half=1.02,
                 win_y0=0.62, win_y1=2.18, steps=16, zmax=30.0, side=-1, axis="x"):
    """
    옆벽의 창을 역추적해서 진짜 빛기둥을 만든다.
    반환 (surf_lit, volume) - 표면에 맺힌 빛 패치와 공기 중 산란량.
    side=-1이면 왼쪽 벽(x=-half_w)에서 빛이 들어온다.
    """
    Lx, Ly, Lz = (np.float32(v) for v in L)
    wz_off = win_z0 + pitch * 0.5

    def hits(px, py, pz):
        if axis == "x":
            t = (px - side * half_w) / Lx
            zh = pz - t * Lz
            oh = py - t * Ly            # 개구부의 세로 좌표
        else:                            # 천장 개구부
            t = (py - half_w) / Ly
            zh = pz - t * Lz
            oh = px - t * Lx            # 개구부의 가로 좌표
        dz = ((zh - wz_off) % pitch) - pitch * 0.5
        return ((np.abs(dz) < win_half) & (oh > win_y0) & (oh < win_y1) &
                (t > 0.0) & (zh > 0.6)).astype(np.float32)

    dxn = np.broadcast_to(cam.dx, (cam.rh, cam.rw)) / cam.f
    dyn = -np.broadcast_to(cam.dy, (cam.rh, cam.rw)) / cam.f

    surf_lit = hits(dxn * z_surf, dyn * z_surf, z_surf)

    vol = np.zeros((cam.rh, cam.rw), np.float32)
    ts = np.linspace(0.8, zmax, steps, dtype=np.float32)
    for zs in ts:
        m = hits(dxn * zs, dyn * zs, np.float32(zs))
        vol += m * (z_surf > zs) / (1.0 + zs * 0.16)
    vol /= steps
    return surf_lit, vol


def over(dst, color, alpha):
    a = alpha[..., None].astype(np.float32)
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = c.reshape((1, 1, 3))
    dst *= (1.0 - a)
    dst += c * a
    return dst


def over_box(dst, color, alpha, box):
    y0, y1, x0, x1 = box
    sub = dst[y0:y1, x0:x1]
    over(sub, color, alpha)
    return dst


def mix(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sat(x):
    return np.clip(x, 0.0, 1.0)


# ─────────────────────────────────────────────────────────────
# SDF 프리미티브 (월드 평면 위)
# ─────────────────────────────────────────────────────────────
def sd_capsule(u, v, ax, ay, bx, by, r):
    pax = u - ax
    pay = v - ay
    bax = bx - ax
    bay = by - ay
    dd = bax * bax + bay * bay + 1e-9
    h = np.clip((pax * bax + pay * bay) / dd, 0.0, 1.0)
    dxx = pax - bax * h
    dyy = pay - bay * h
    return np.sqrt(dxx * dxx + dyy * dyy) - r


def sd_ellipse(u, v, cx, cy, rx, ry):
    return np.sqrt(((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2) - 1.0


def smin(a, b, k=0.04):
    h = sat(0.5 + 0.5 * (b - a) / k)
    return mix(b, a, h) - k * h * (1.0 - h)


# ─────────────────────────────────────────────────────────────
# 인물 실루엣
# ─────────────────────────────────────────────────────────────
def person(cam, z, x_p, height=1.66, pose=0, hanbok=False, facing=1):
    """
    깊이 z 평면에 서 있는 사람. 발은 y=-cam.eye.
    pose 0=서기/걷기 1=양팔 위로 2=머리에 짐 3=반죽 4=팔짱/대화 5=아이가 손뻗기
    반환 (mask, box) — mask는 box 크기.
    """
    h = height
    box = cam.box_of(z, h * 0.42, -cam.eye + h * 1.22, -cam.eye - 0.05,
                     pad=4, x_center=x_p)
    if box is None:
        return None, None
    wx, wy = cam.sub_world(z, box)
    u = wx - x_p
    v = wy + cam.eye                      # 0=발, h=머리끝

    # 비율
    hr = h * 0.037                        # 머리 반폭
    head_c = h - hr * 1.28
    sh_y = h * 0.820                      # 어깨
    sh_w = h * 0.092
    waist_y = h * 0.605
    hip_y = h * 0.480
    hip_w = h * 0.072
    d = np.full(np.broadcast_shapes(u.shape, v.shape), 1e3, np.float32)

    # 머리 + 목
    d = np.minimum(d, sd_ellipse(u, v, 0.0, head_c, hr * 1.00, hr * 1.26) * hr)
    d = np.minimum(d, sd_capsule(u, v, 0.0, sh_y, 0.0, head_c - hr * 0.85, h * 0.023))
    # 모통 — 어깨→허리→골반으로 잘리는 폭
    d = smin(d, sd_capsule(u, v, -sh_w * 0.62, sh_y, -sh_w * 0.34, waist_y, h * 0.044), h * 0.028)
    d = smin(d, sd_capsule(u, v, sh_w * 0.62, sh_y, sh_w * 0.34, waist_y, h * 0.044), h * 0.028)
    d = smin(d, sd_capsule(u, v, -hip_w * 0.5, waist_y, -hip_w * 0.62, hip_y, h * 0.042), h * 0.026)
    d = smin(d, sd_capsule(u, v, hip_w * 0.5, waist_y, hip_w * 0.62, hip_y, h * 0.042), h * 0.026)
    d = smin(d, sd_capsule(u, v, -sh_w, sh_y, sh_w, sh_y, h * 0.026), h * 0.028)
    # 다리 — 사이에 틈이 보이게
    for s in (-1, 1):
        kx = s * h * 0.052
        d = smin(d, sd_capsule(u, v, s * hip_w * 0.70, hip_y, kx, h * 0.240, h * 0.034), h * 0.016)
        d = smin(d, sd_capsule(u, v, kx, h * 0.240, kx * 1.18, h * 0.018, h * 0.027), h * 0.016)
    # 신발
    for s in (-1, 1):
        d = np.minimum(d, sd_capsule(u, v, s * h * 0.060, h * 0.018,
                                     s * h * 0.060 + facing * h * 0.040, h * 0.013, h * 0.019))

    ar = h * 0.028
    if pose == 1:      # 널어 말리는 국수를 걸는 자세 — 팔을 위로 45도
        for s in (-1, 1):
            ex, ey = s * (sh_w + h * 0.055), sh_y + h * 0.085
            hx, hy = s * (sh_w + h * 0.075), sh_y + h * 0.215
            d = smin(d, sd_capsule(u, v, s * sh_w, sh_y, ex, ey, ar), h * 0.018)
            d = smin(d, sd_capsule(u, v, ex, ey, hx, hy, ar * 0.88), h * 0.018)
    elif pose == 2:    # 머리에 짐
        d = np.minimum(d, sd_capsule(u, v, -sh_w * 1.9, h * 1.045, sh_w * 1.9, h * 1.045, h * 0.055))
        d = smin(d, sd_capsule(u, v, sh_w, sh_y, sh_w * 1.35, sh_y + h * 0.13, ar), h * 0.02)
        d = smin(d, sd_capsule(u, v, sh_w * 1.35, sh_y + h * 0.13, sh_w * 0.8, h * 0.99, ar * 0.9), h * 0.02)
        d = smin(d, sd_capsule(u, v, -sh_w, sh_y, -sh_w * 1.1, hip_y + h * 0.04, ar), h * 0.02)
    elif pose == 3:    # 작업대 쪽으로 손
        for s in (-1, 1):
            d = smin(d, sd_capsule(u, v, s * sh_w, sh_y, facing * h * 0.15 + s * sh_w * 0.4,
                                   h * 0.60, ar), h * 0.02)
    elif pose == 4:    # 한 손 허리, 한 손 아래
        d = smin(d, sd_capsule(u, v, -sh_w, sh_y, -sh_w * 1.35, hip_y - h * 0.02, ar), h * 0.02)
        d = smin(d, sd_capsule(u, v, sh_w, sh_y, sh_w * 1.25, hip_y + h * 0.10, ar), h * 0.02)
        d = smin(d, sd_capsule(u, v, sh_w * 1.25, hip_y + h * 0.10, sh_w * 0.55, hip_y + h * 0.05, ar * 0.9), h * 0.02)
    elif pose == 5:    # 아이 — 위로 손 뻗기
        d = smin(d, sd_capsule(u, v, sh_w, sh_y, sh_w * 1.15, sh_y + h * 0.26, ar * 1.05), h * 0.02)
        d = smin(d, sd_capsule(u, v, -sh_w, sh_y, -sh_w * 1.3, hip_y + h * 0.12, ar), h * 0.02)
    else:              # 걷기
        d = smin(d, sd_capsule(u, v, -sh_w, sh_y, -sh_w * 1.25 - facing * h * 0.03, hip_y - h * 0.03, ar), h * 0.02)
        d = smin(d, sd_capsule(u, v, sh_w, sh_y, sh_w * 1.1 + facing * h * 0.05, hip_y + h * 0.02, ar), h * 0.02)

    if hanbok:         # 아래로 퍼지는 치마 실루엣
        t = sat((hip_y + h * 0.10 - v) / (h * 0.42))
        wdt = hip_w * 0.75 + h * 0.115 * t * t
        skirt = np.maximum(np.abs(u) - wdt, np.abs(v - h * 0.27) - h * 0.24)
        d = smin(d, skirt, h * 0.03)

    px_per_m = cam.f / z
    aa = 1.0 / max(1e-6, px_per_m)          # 1픈셀에 해당하는 월드 길이
    m = sat(0.5 - d / (aa * 1.6))
    return m, box


def contact_shadow(wx_ground, z_ground, x_p, z_p, rx=0.34, rz=0.46, strength=0.5):
    """지면에 사람/기닥을 받치는 어림. 이게 없으면 사람이 둔다."""
    k = ((wx_ground - x_p) / rx) ** 2 + ((z_ground - z_p) / rz) ** 2
    return np.exp(-k) * strength


# ─────────────────────────────────────────────────────────────
# 국수 다발 커튼
# ─────────────────────────────────────────────────────────────
def noodle_curtain(cam, z, x_in, x_out, y_top, y_bot,
                   period=0.010, seed=5, sway=0.07, ragged=0.26,
                   bright=(0.95, 0.92, 0.85), dark=(0.18, 0.16, 0.13),
                   base_alpha=0.93, bundle=0.55, bundle_w=0.42):
    """
    깊이 z에 걸린 소면 다발. |x| in (x_in, x_out) 양쪽 대칭.
    bundle: 다발 사이 틈의 세기. bundle_w: 다발 폭(m).
    반환 (rgb, alpha, box)
    """
    box = cam.box_of(z, x_out, y_top + 0.12, y_bot - ragged - 0.05, pad=3)
    if box is None:
        return None, None, None
    wx, wy = cam.sub_world(z, box)
    ax = np.abs(wx)
    in_x = (ax > x_in) & (ax < x_out)
    if not in_x.any():
        return None, None, None

    drop = sat((y_top - wy) / max(1e-6, (y_top - y_bot)))
    swing = (fbm1(wx * 2.2 + z * 0.9, seed=seed + 1, octaves=3) - 0.5) * sway
    wxe = wx + swing * drop * drop

    # 다발 단위 — 틈이 생겨 '여러 다발'로 보인다
    bslot = wxe / bundle_w
    bph = bslot - np.floor(bslot)
    bjit = fbm1(np.floor(bslot) * 3.7 + 11.0, seed=seed + 7, octaves=2)
    gap = 0.11 + 0.085 * bjit
    bmask = smoothstep(0.0, gap, bph) * (1.0 - smoothstep(1.0 - gap, 1.0, bph))
    bmask = mix(np.float32(1.0), bmask, np.float32(bundle))

    # 다발별 길이 — 저주파 물결 + 다발 단위 편차
    lwave = (fbm1(wxe * 1.5, seed=seed + 2, octaves=3) - 0.45)
    lbund = (bjit - 0.5)
    ln = y_bot + ragged * (0.55 * lwave + 0.75 * lbund)
    band = in_x & (wy > ln) & (wy < y_top)

    # 가닥
    ph = wxe / period + 0.30 * (fbm1(wxe * 60.0, seed=seed + 3, octaves=2) - 0.5)
    s = 0.5 + 0.5 * np.cos(ph * np.float32(2.0 * np.pi))
    s = s ** np.float32(1.25)
    s = sat(s * (0.70 + 0.55 * fbm1(wxe * 7.0, seed=seed + 4, octaves=3)))

    vgrad = 0.80 + 0.28 * sat(1.0 - drop * 0.85)
    tip = smoothstep(0.0, 0.055, sat(wy - ln)) * smoothstep(0.0, 0.03, sat(y_top - wy))
    clump = 0.78 + 0.36 * fbm1(wxe * 2.6 + 5.0, seed=seed + 5, octaves=3)

    lit = sat(s * vgrad * clump)
    b = np.asarray(bright, np.float32).reshape(1, 1, 3)
    dk = np.asarray(dark, np.float32).reshape(1, 1, 3)
    rgb = dk + (b - dk) * lit[..., None]

    a = base_alpha * (0.34 + 0.66 * lit) * tip * bmask
    alpha = np.where(band, a, 0.0).astype(np.float32)
    return rgb, alpha, box


# ─────────────────────────────────────────────────────────────
# 후처리
# ─────────────────────────────────────────────────────────────
def luminance(img):
    return (img[:, :, 0] * 0.2126 + img[:, :, 1] * 0.7152 + img[:, :, 2] * 0.0722)


def bloom(img, thresh=0.62, radius=0.028, amount=0.55, passes=(1.0, 0.5, 0.22)):
    h, w = img.shape[:2]
    l = luminance(img)
    k = sat((l - thresh) / max(1e-6, (1.0 - thresh))) ** 1.35
    src = img * k[..., None]
    acc = np.zeros_like(img)
    r0 = max(2, int(radius * w))
    for i, wt in enumerate(passes):
        acc += wt * blur_rgb(src, r0 * (2 ** i), 2)
    return img + acc * amount


def god_rays(cam, img, center, strength=0.12, tint=(1.0, 0.94, 0.80), seed=9,
             near=22.0, far=4.2):
    cxp = center[0] * cam.rw
    cyp = center[1] * cam.rh
    dx = cam.X - cxp
    dy = cam.Y - cyp
    ang = np.arctan2(np.broadcast_to(dy, (cam.rh, cam.rw)),
                     np.broadcast_to(dx, (cam.rh, cam.rw)))
    r = np.sqrt(dx * dx + dy * dy) / cam.rw
    n = fbm1(ang * 5.5, seed=seed, octaves=4)
    n2 = fbm1(ang * 15.0 + 3.0, seed=seed + 1, octaves=3)
    ray = sat((n * 0.6 + n2 * 0.4 - 0.44) * 3.2)
    fade = np.exp(-r * far) * (1.0 - np.exp(-r * near))
    add = (ray * fade * strength).astype(np.float32)
    return img + add[..., None] * np.asarray(tint, np.float32).reshape(1, 1, 3)


def tone_curve(l, black=0.0, white=1.0, gamma=1.0, s_curve=0.0):
    x = np.clip((l - black) / max(1e-6, (white - black)), 0.0, 1.0)
    if gamma != 1.0:
        x = x ** np.float32(gamma)
    if s_curve:
        x = mix(x, x * x * (3.0 - 2.0 * x), np.float32(s_curve))
    return x


def monotint(img, tint=(1.0, 0.90, 0.74), black=0.0, white=1.0,
             gamma=1.0, s_curve=0.5, split=None):
    """흑백으로 내리고 틴트를 곱해 세피아/아날로그 룩을 만든다."""
    l = tone_curve(luminance(img), black, white, gamma, s_curve)
    out = l[..., None] * np.asarray(tint, np.float32).reshape(1, 1, 3)
    if split is not None:
        sh = np.asarray(split[0], np.float32).reshape(1, 1, 3)
        hi = np.asarray(split[1], np.float32).reshape(1, 1, 3)
        out = out * mix(sh, hi, l[..., None])
    return out


def grade(img, lift=(0, 0, 0), gain=(1, 1, 1), gamma=1.0,
          saturation=1.0, contrast=1.0, pivot=0.42):
    out = img * np.asarray(gain, np.float32).reshape(1, 1, 3)
    out = out + np.asarray(lift, np.float32).reshape(1, 1, 3)
    out = np.clip(out, 0, None) ** np.float32(gamma)
    if saturation != 1.0:
        l = luminance(out)[..., None]
        out = l + (out - l) * saturation
    if contrast != 1.0:
        out = (out - pivot) * contrast + pivot
    return out


def filmic(x):
    x = np.clip(x, 0, None)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return sat((x * (a * x + b)) / (x * (c * x + d) + e))


def vignette(cam, img, amount=0.5, power=2.0):
    v = 1.0 - amount * (cam.rad * 2.0 / 1.414) ** power
    return img * sat(v)[..., None]


def grain(img, amount=0.035, seed=4, size=1.4):
    h, w = img.shape[:2]
    rng = np.random.default_rng(seed)
    n = rng.normal(0.0, 1.0, (max(2, int(h / size)), max(2, int(w / size)))).astype(np.float32)
    n = np.asarray(Image.fromarray(n, "F").resize((w, h), Image.BILINEAR), np.float32)
    l = luminance(img)
    k = amount * (0.30 + 0.70 * (1.0 - np.abs(l - 0.45) * 1.9) ** 1.6)
    return img + n[..., None] * np.clip(k, 0, None)[..., None]


def save(cam, img, path, quality=84, scale=1.0):
    a = (sat(img) ** (1.0 / 2.2) * 255.0 + 0.5).astype(np.uint8)
    im = Image.fromarray(a, "RGB")
    tw, th = int(cam.w * scale), int(cam.h * scale)
    if im.size != (tw, th):
        im = im.resize((tw, th), Image.LANCZOS)
    if path.lower().endswith(".webp"):
        im.save(path, "WEBP", quality=quality, method=6)
    else:
        im.save(path, quality=quality, optimize=True, progressive=True)
    return im
