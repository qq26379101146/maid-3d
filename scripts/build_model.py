# -*- coding: utf-8 -*-
"""歪毛小女仆 —— 程序化建模主脚本（Blender 4.5 / 纯 bpy，不联网）。

跑法（在 Blender 里，MCP execute_blender_code）：
    p = r"C:/Users/001/Documents/deepseek-harness/default-workspace/projects/maid-3d/scripts/build_model.py"
    exec(compile(open(p, encoding="utf-8").read(), "build_model.py", "exec"), {"__name__": "__main__"})

参考立绘：Q 版蓝发女仆（白色蕾丝女仆头带 / 深蓝 A 字连衣裙 / 白围裙蕾丝 /
蓝宝石领结 / 双手合胸 / 呆毛 / 大波浪双马尾）。

v5 改动：刘海直接做进发壳（波浪形开口 = 分股刘海），删掉那排"葡萄球"；
腮红缩小、白围裙收窄、裙摆蕾丝更细、双马尾再收细、嘴加大。
"""
import bpy
import bmesh
import math

BASE = r"C:/Users/001/Documents/deepseek-harness/default-workspace/projects/maid-3d"
LIB = BASE + "/scripts/maid_lib.py"
exec(compile(open(LIB, encoding="utf-8").read(), "maid_lib.py", "exec"), globals())

TAU = math.tau

clear_scene()
boot_materials()
COLL = get_collection()

# ---------------------------------------------------------------- 发型壳工具


def hair_shell(name, center, r, mat=None, cut=None, scale=(1, 1, 1),
               seg=72, ring=36, solidify=0.012):
    """球壳挖开口 —— 动漫发型的"罩"。cut 收到归一化坐标 (nx, ny, nz)，True 表示删掉。"""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring,
                                         radius=r, location=center)
    o = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(o.data)
    kill = []
    if cut is not None:
        for f in bm.faces:
            c = f.calc_center_median()
            if cut((c.x / r, c.y / r, c.z / r)):
                kill.append(f)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(o.data)
    bm.free()
    o.scale = scale
    _finish(o, name, mat)
    if solidify:
        m = o.modifiers.new("Solidify", "SOLIDIFY")
        m.thickness = solidify
        m.offset = 0.0
    return o


# ================================================================== 1 头 / 脸
sphere("MD_face", (0.0, -0.010, 0.850), 0.300, scale=(1.00, 0.98, 1.02),
       mat=M("skin"), seg=64, ring=32)
sphere("MD_chin", (0.0, -0.048, 0.712), 0.205, scale=(0.90, 0.90, 0.66),
       mat=M("skin"), seg=48, ring=24)
for sx in (1, -1):
    sphere("MD_ear_%s" % ("L" if sx > 0 else "R"), (0.286 * sx, 0.020, 0.846),
           0.062, scale=(0.45, 0.75, 1.05), mat=M("skin"), seg=24, ring=12)

# ================================================================== 2 头发


def _hair_cut(n):
    """脸的开口：前面中间挖掉，上沿用波浪线 —— 波浪就是分股的刘海。"""
    nx, ny, nz = n
    if ny >= -0.24 or abs(nx) > 0.84:
        return False
    rim = 0.290 + 0.055 * math.cos(nx * 9.5)
    return nz < rim


hair_shell("MD_hair_shell", (0.0, 0.012, 0.856), 0.326, mat=M("hair"),
           cut=_hair_cut, seg=96, ring=48, solidify=0.014)
sphere("MD_hair_back", (0.0, 0.085, 0.856), 0.310, scale=(1.02, 1.00, 1.02),
       mat=M("hair"), seg=48, ring=24)
for sx in (1, -1):
    sphere("MD_hair_cheek_%s" % ("L" if sx > 0 else "R"), (0.292 * sx, -0.056, 0.858),
           0.150, scale=(0.40, 0.78, 1.12), mat=M("hair"), seg=32, ring=16)
sphere("MD_hair_long", (0.0, 0.118, 0.640), 1.0, scale=(0.282, 0.232, 0.395),
       mat=M("hair"), seg=48, ring=24)
strand("MD_hair_fall",
           [(0.0, 0.150, 0.455), (0.0, 0.190, 0.330), (0.0, 0.198, 0.215)],
           lambda t: 0.220 - 0.085 * t, M("hair"), n=10, seg=32, ring=16,
           scale=(1.0, 0.70, 1.0))
strand("MD_hair_fall_hi",
           [(0.0, 0.126, 0.435), (0.0, 0.166, 0.310)],
           lambda t: 0.125 - 0.045 * t, M("hair_hi"), n=7, seg=24, ring=12,
           scale=(1.0, 0.58, 1.0))

# ---- 刘海层次：中分两撮长丝 + 几片贴在壳面上的扁发片
for sx in (1, -1):
    strand("MD_bang_mid_%s" % ("L" if sx > 0 else "R"),
               [(0.050 * sx, -0.302, 1.010), (0.076 * sx, -0.320, 0.944),
                (0.090 * sx, -0.312, 0.902)],
               lambda t: 0.054 - 0.018 * t, M("hair"), n=9, seg=22, ring=11,
               scale=(0.60, 0.44, 1.28))
for i, (bx, bz, ang) in enumerate(((-0.206, 0.952, -0.58), (-0.108, 0.978, -0.24),
                                   (0.108, 0.978, 0.24), (0.206, 0.952, 0.58))):
    sphere("MD_bang_layer_%d" % i, (bx, -0.272, bz), 0.084,
           scale=(1.05, 0.26, 1.30), mat=M("hair"),
           rot=(-0.18, 0.0, ang), seg=24, ring=12)
# 额头两侧的斜发（柔化开口边缘）
for sx in (1, -1):
    sphere("MD_bang_side_%s" % ("L" if sx > 0 else "R"), (0.250 * sx, -0.180, 0.958),
           0.080, scale=(0.86, 0.58, 1.32), mat=M("hair"),
           rot=(-0.10, 0.0, -sx * 1.05), seg=24, ring=12)
# 鬓发
for sx in (1, -1):
    strand("MD_sidelock_%s" % ("L" if sx > 0 else "R"),
               [(0.294 * sx, -0.132, 0.958), (0.318 * sx, -0.092, 0.800),
                (0.312 * sx, -0.066, 0.660)],
               lambda t: 0.066 - 0.024 * t, M("hair"), n=10, seg=24, ring=12,
               scale=(0.60, 0.74, 1.0))

# ---- 双马尾
for side, sx in (("L", 1), ("R", -1)):
    pts = [(0.250 * sx, 0.148, 0.936),
           (0.352 * sx, 0.208, 0.782),
           (0.378 * sx, 0.124, 0.596),
           (0.330 * sx, 0.020, 0.424),
           (0.306 * sx, -0.064, 0.318),
           (0.246 * sx, -0.118, 0.286)]
    strand("MD_twintail_%s" % side, pts,
               lambda t: 0.076 * (1 - t) ** 0.55 + 0.017,
               M("hair"), n=42, seg=24, ring=12, scale=(1.0, 0.94, 1.06))
    strand("MD_twintail_hi_%s" % side,
               [(0.298 * sx, 0.198, 0.862), (0.392 * sx, 0.148, 0.664),
                (0.356 * sx, 0.052, 0.474)],
               lambda t: 0.020 - 0.008 * t, M("hair_hi"), n=18, seg=20, ring=10,
               scale=(0.62, 0.70, 1.30))
    strand("MD_twintail_curl_%s" % side,
               [(0.244 * sx, -0.130, 0.306), (0.190 * sx, -0.168, 0.360),
                (0.166 * sx, -0.146, 0.432)],
               lambda t: 0.040 - 0.019 * t, M("hair_hi"), n=10, seg=20, ring=10)
    torus("MD_twintail_band_%s" % side, (0.258 * sx, 0.156, 0.912), 0.070, 0.015,
          mat=M("lace"), rot=(0.42, 0.0, 0.0), mseg=32, nseg=10)
# 背后的发丝层次。
# 教训：后背发球在 z=0.48 处表面已到 y≈0.330，用细 strand 塞在 y≈0.33 会被整个吞掉（白做两次）；
# 反过来堆大椭球又变成"四颗蛋"贴在背上，更难看。
# 正解：按椭球方程**算出表面**，让每根发丝正好压在表面上 +0.015，这样无论怎么转都是分层发丝。
HL_C = (0.0, 0.118, 0.640)          # MD_hair_long 的中心
HL_R = (0.282, 0.232, 0.395)        # 它的三轴半径
HB_C = (0.0, 0.085, 0.856)          # MD_hair_back 的中心
HB_R = (0.310 * 1.02, 0.310, 0.310 * 1.02)


def _ellip_y(c, r, x, z):
    u = (x - c[0]) / r[0]
    w = (z - c[2]) / r[2]
    k = 1.0 - u * u - w * w
    if k <= 0.0:
        return None
    return c[1] + r[1] * math.sqrt(k)


def _back_y(x, z, lift=0.015):
    """后脑最外层的表面 y：同时算 hair_long 和 hair_back，取更靠外的那个。"""
    ys = [y for y in (_ellip_y(HL_C, HL_R, x, z), _ellip_y(HB_C, HB_R, x, z))
          if y is not None]
    if not ys:
        return None
    return max(ys) + lift


for i, bx in enumerate((-0.240, -0.180, -0.118, -0.058, 0.0, 0.058, 0.118, 0.180, 0.240)):
    pts = []
    for z in (0.790, 0.720, 0.650, 0.580, 0.510, 0.440, 0.370, 0.305, 0.250):
        y = _back_y(bx, z, lift=0.008)
        if y is None:
            continue
        pts.append((bx * (1.0 + 0.02 * (0.79 - z)), y, z))
    if len(pts) < 3:
        continue
    # 只用 hair（深靛），极细（0.018），贴面 0.008：
    # 让它在受光时只形成一道很淡的明暗分界，而不是"蓝手指"。
    strand("MD_back_lock_%d" % i, pts,
           lambda t: 0.020 - 0.009 * t,
           M("hair"), n=18, seg=12, ring=6, scale=(1.0, 0.55, 1.0))
# 发梢的小尖，把下沿打破（同样贴着表面）
for i, bx in enumerate((-0.185, -0.062, 0.062, 0.185)):
    y = _back_y(bx, 0.300, 0.018)
    if y is None:
        continue
    sphere("MD_back_tip_%d" % i, (bx, y, 0.292), 0.044,
           scale=(0.80, 0.62, 1.60), mat=M("hair"),
           rot=(0.08, 0.0, bx * 0.5), seg=16, ring=8)

# ================================================================== 3 呆毛
cylinder("MD_ahoge_stem", (0.0, 0.024, 1.222), 0.012, 0.092, mat=M("hair"),
         rot=(0.20, 0.0, 0.0), verts=16)
strand("MD_ahoge_curl",
           [(0.0, 0.018, 1.252), (0.0, -0.022, 1.292), (0.0, -0.064, 1.268),
            (0.0, -0.052, 1.226)],
           lambda t: 0.017 - 0.006 * t, M("hair"), n=12, seg=16, ring=8)

# ================================================================== 4 女仆头带
torus("MD_headband", (0.0, 0.012, 1.030), 0.288, 0.018, mat=M("lace"),
      rot=(math.radians(5), 0.0, 0.0), mseg=80, nseg=12)
lace_ring("MD_headband_ruffle", (0.0, 0.012, 1.052), 0.272, n=14, r=0.019,
          mat=M("lace"), z_wave=0.010, a0=-2.92, a1=-0.22, scale=(1.0, 1.0, 0.85))
for sx in (1, -1):
    sphere("MD_hb_bow_%s" % ("L" if sx > 0 else "R"), (0.212 * sx, -0.170, 1.068),
           0.032, scale=(1.30, 0.58, 0.86), mat=M("lace"),
           rot=(0.0, 0.0, sx * 0.95), seg=20, ring=10)
    sphere("MD_hb_bow_tail_%s" % ("L" if sx > 0 else "R"),
           (0.246 * sx, -0.126, 1.030), 0.024, scale=(0.85, 0.50, 1.25),
           mat=M("lace_soft"), rot=(0.0, 0.0, sx * 0.60), seg=16, ring=8)
for sx in (1, -1):
    for k, (dz, dx, ry) in enumerate(((0.050, 0.262, 0.18),
                                      (0.016, 0.277, 0.06),
                                      (-0.022, 0.267, -0.08))):
        sphere("MD_wing_%s_%d" % ("L" if sx > 0 else "R", k),
               (dx * sx, 0.030, 1.044 + dz), 0.066,
               scale=(0.20, 0.92, 0.52), mat=M("lace"),
               rot=(0.0, sx * ry, math.radians(72) * sx), seg=20, ring=10)

# ================================================================== 5 脸部件
for sx in (1, -1):
    tag = "L" if sx > 0 else "R"
    sphere("MD_eye_dark_" + tag, (0.116 * sx, -0.276, 0.852), 0.086,
           scale=(1.02, 0.30, 1.14), mat=M("eye_dark"),
           rot=(0.0, 0.0, -sx * 0.06), seg=32, ring=16)
    sphere("MD_iris_" + tag, (0.116 * sx, -0.290, 0.846), 0.068,
           scale=(1.00, 0.30, 1.04), mat=M("eye"),
           rot=(0.0, 0.0, -sx * 0.06), seg=32, ring=16)
    sphere("MD_pupil_" + tag, (0.116 * sx, -0.301, 0.839), 0.030,
           scale=(1.0, 0.30, 1.15), mat=M("eye_dark"), seg=20, ring=10)
    sphere("MD_hl_big_" + tag, (0.088 * sx, -0.302, 0.884), 0.023,
           mat=M("eye_white"), seg=20, ring=10)
    sphere("MD_hl_small_" + tag, (0.142 * sx, -0.303, 0.824), 0.013,
           mat=M("eye_white"), seg=16, ring=8)
    sphere("MD_lash_" + tag, (0.116 * sx, -0.272, 0.916), 0.090,
           scale=(1.06, 0.28, 0.20), mat=M("eye_dark"),
           rot=(0.0, 0.0, -sx * 0.10), seg=28, ring=14)
    sphere("MD_brow_" + tag, (0.118 * sx, -0.268, 0.958), 0.048,
           scale=(1.25, 0.25, 0.18), mat=M("brow"),
           rot=(0.0, 0.0, -sx * 0.18), seg=20, ring=10)
    sphere("MD_blush_" + tag, (0.190 * sx, -0.230, 0.792), 0.048,
           scale=(1.15, 0.22, 0.62), mat=M("blush"), seg=24, ring=12)
sphere("MD_mouth", (0.0, -0.296, 0.774), 0.027, scale=(1.40, 0.42, 0.52),
       mat=M("mouth"), seg=20, ring=10)

# ================================================================== 6 身体
cylinder("MD_neck", (0.0, 0.005, 0.575), 0.074, 0.105, mat=M("skin"), verts=32)
sphere("MD_torso", (0.0, 0.0, 0.442), 0.152, scale=(0.94, 0.80, 1.28),
       mat=M("dress"), seg=48, ring=24)
torus("MD_collar", (0.0, 0.0, 0.556), 0.096, 0.022, mat=M("lace"),
      rot=(math.radians(8), 0.0, 0.0), mseg=40, nseg=10)
sphere("MD_apron_bib", (0.0, -0.118, 0.498), 1.0, scale=(0.090, 0.040, 0.082),
       mat=M("lace"), seg=32, ring=16)
for sx in (1, -1):
    sphere("MD_bib_cross_%s" % ("L" if sx > 0 else "R"),
           (0.026 * sx, -0.136, 0.546), 0.015, scale=(1.0, 0.40, 4.0),
           mat=M("lace_soft"), rot=(0.0, sx * 0.75, 0.0), seg=16, ring=8)
    sphere("MD_bow_%s" % ("L" if sx > 0 else "R"), (0.052 * sx, -0.128, 0.560),
           0.048, scale=(1.15, 0.50, 0.80), mat=M("dress_deep"),
           rot=(0.0, 0.0, sx * 0.55), seg=24, ring=12)
sphere("MD_bow_gem", (0.0, -0.146, 0.554), 0.031, scale=(1.0, 0.75, 1.0),
       mat=M("gem"), seg=24, ring=12)

for sx in (1, -1):
    tag = "L" if sx > 0 else "R"
    sphere("MD_puff_" + tag, (0.164 * sx, 0.0, 0.556), 0.082,
           scale=(1.14, 1.00, 1.02), mat=M("dress"), seg=32, ring=16)
    torus("MD_cuff_" + tag, (0.166 * sx, 0.0, 0.496), 0.073, 0.018,
          mat=M("lace"), mseg=32, nseg=10)
    strand("MD_arm_" + tag,
               [(0.170 * sx, -0.022, 0.536), (0.128 * sx, -0.096, 0.472),
                (0.064 * sx, -0.148, 0.440)],
               lambda t: 0.046 - 0.013 * t, M("dress"), n=10, seg=20, ring=10)
    sphere("MD_cuffball_" + tag, (0.062 * sx, -0.150, 0.438), 0.031,
           scale=(1.0, 0.90, 0.82), mat=M("lace"), seg=20, ring=10)
    sphere("MD_hand_" + tag, (0.046 * sx, -0.158, 0.430), 0.047,
           scale=(1.0, 0.92, 0.86), mat=M("skin"), seg=24, ring=12)
    sphere("MD_thumb_" + tag, (0.026 * sx, -0.178, 0.452), 0.020,
           scale=(0.8, 0.9, 1.2), mat=M("skin"), seg=16, ring=8)

# ================================================================== 7 裙子
cone("MD_skirt", (0.0, 0.0, 0.276), r1=0.372, r2=0.140, depth=0.300,
     mat=M("dress"), verts=80)
cone("MD_skirt_under", (0.0, 0.0, 0.226), r1=0.322, r2=0.140, depth=0.216,
     mat=M("dress_deep"), verts=72)
sphere("MD_apron_front", (0.0, -0.250, 0.292), 1.0, scale=(0.090, 0.044, 0.152),
       mat=M("lace"), seg=40, ring=20)
torus("MD_waist_gold", (0.0, 0.0, 0.408), 0.148, 0.010, mat=M("gold"),
      mseg=64, nseg=8)
torus("MD_skirt_lace_line", (0.0, 0.0, 0.238), 0.292, 0.012, mat=M("lace"),
      mseg=80, nseg=8, scale=(1.0, 1.0, 0.9))
torus("MD_skirt_gold_line", (0.0, 0.0, 0.172), 0.342, 0.007, mat=M("gold"),
      mseg=80, nseg=8, scale=(1.0, 1.0, 0.9))
lace_ring("MD_hem_ruffle", (0.0, 0.0, 0.130), 0.370, n=88, r=0.013,
          mat=M("lace"), z_wave=0.004, scale=(1.0, 1.0, 0.96))
torus("MD_hem_edge", (0.0, 0.0, 0.120), 0.368, 0.008, mat=M("lace"),
      mseg=96, nseg=8, scale=(1.0, 1.0, 0.9))
# 腰后大蝴蝶结（背面也要有戏，不然转过去就是一片深蓝）
for sx in (1, -1):
    sphere("MD_back_bow_%s" % ("L" if sx > 0 else "R"),
           (0.098 * sx, 0.152, 0.402), 0.072,
           scale=(1.25, 0.62, 0.92), mat=M("lace"),
           rot=(0.0, 0.0, sx * 0.42), seg=24, ring=12)
    strand("MD_back_bow_tail_%s" % ("L" if sx > 0 else "R"),
           [(0.062 * sx, 0.150, 0.362), (0.086 * sx, 0.158, 0.300),
            (0.078 * sx, 0.146, 0.246)],
           lambda t: 0.040 - 0.014 * t, M("lace_soft"), n=8, seg=18, ring=9,
           scale=(1.0, 0.46, 1.0))
sphere("MD_back_bow_knot", (0.0, 0.166, 0.404), 0.046,
       scale=(0.85, 0.62, 0.85), mat=M("gem"), seg=20, ring=10)
# 裙后横向蕾丝线 + 一圈细褶（跟正面的围裙呼应）
torus("MD_skirt_back_lace", (0.0, 0.0, 0.208), 0.332, 0.011, mat=M("lace"),
      mseg=80, nseg=8, scale=(1.0, 1.0, 0.92))
lace_ring("MD_skirt_back_ruffle", (0.0, 0.0, 0.186), 0.318, n=36, r=0.015,
          mat=M("lace_soft"), z_wave=0.006, a0=0.55, a1=2.60,
          scale=(1.0, 1.0, 0.94))

# ================================================================== 8 腿 / 袜 / 鞋
for sx in (1, -1):
    tag = "L" if sx > 0 else "R"
    cylinder("MD_leg_" + tag, (0.082 * sx, 0.005, 0.086), 0.043, 0.115,
             mat=M("skin"), verts=24)
    cylinder("MD_sock_" + tag, (0.082 * sx, 0.005, 0.058), 0.048, 0.076,
             mat=M("lace"), verts=24)
    sphere("MD_shoe_" + tag, (0.082 * sx, -0.018, 0.030), 0.055,
           scale=(1.00, 1.42, 0.62), mat=M("shoe"), seg=28, ring=14)
    sphere("MD_shoe_bow_" + tag, (0.082 * sx, -0.062, 0.058), 0.018,
           scale=(1.2, 0.7, 0.8), mat=M("lace"), seg=16, ring=8)

# ================================================================== 收尾
ROOT = bpy.data.objects.new("ChibiMaid_Root", None)
COLL.objects.link(ROOT)
ROOT.empty_display_size = 0.15
for o in [x for x in COLL.objects if x.type == "MESH"]:
    o.parent = ROOT
    o.matrix_parent_inverse = ROOT.matrix_world.inverted()

bpy.ops.object.select_all(action="DESELECT")
print("=" * 60)
report()
print("[build_model] done. root=%s collection=%s" % (ROOT.name, COLL.name))
