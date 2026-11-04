# -*- coding: utf-8 -*-
"""转台渲染：让模型绕竖直轴转一圈，逐帧出图，供 ffmpeg 合成 GIF / MP4。

用法（命令行，不进 Blender GUI）：
    blender.exe -b <chibi_maid.blend> --python render_turntable.py -- <输出目录> [帧数] [边长]

场景里必须有 "ChibiMaid_Root"（空物体，模型都挂在它下面）。地面/灯/相机不动，
只转 root —— 这是标准展台效果（阴影和反光会跟着转，看着立体）。

产出一圈完整 360° 的无缝循环帧，第 N 帧 = 第 0 帧（循环不跳）。
"""
import bpy
import math
import os
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = argv[0] if argv else r"C:/Users/001/Documents/deepseek-harness/default-workspace/projects/maid-3d/renders/turntable"
# 注意：相对路径会被 Blender 按它自己的 cwd 解析（不是调用者的 cwd），
# 所以这里强制转成绝对路径，避免帧跑到 C:\projects 这种地方去。
OUT = os.path.abspath(OUT).replace("\\", "/")
FRAMES = int(argv[1]) if len(argv) > 1 else 36
SIZE = int(argv[2]) if len(argv) > 2 else 480

S = bpy.context.scene
ROOT = bpy.data.objects.get("ChibiMaid_Root")
if ROOT is None:
    raise SystemExit("场景里找不到 ChibiMaid_Root")

os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 深蓝渐变背景
# 坑：用 World 做背景时，场景里的面光会把"世界"也照亮 ——
# 于是背景右边被侧灯打出光晕（实测 x=375 起从 64 渐亮到 75），
# 贴到卡片上左右差 90，一眼看出是贴图。
# 解法：渲染透明底（film_transparent），背景交给后期合成时填纯色 ——
# 这样背景永远绝对均匀，跟灯光完全无关。
world = S.world or bpy.data.worlds.new("TurntableWorld")
S.world = world
world.use_nodes = True
nt = world.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.16, 0.20, 0.36, 1.0)
bg.inputs["Strength"].default_value = 0.55
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

S.render.film_transparent = True     # 透明底：背景不受灯光影响，绝对均匀
S.render.image_settings.color_mode = "RGBA"
try:
    S.render.pixel_filter_type = "BLACKMAN_HARRIS"
except Exception as e:
    print("[turntable] pixel_filter:", e)

# 地面：直接隐藏。转台 GIF 里一块平灰地面最碍眼（而且真转起来阴影也不动，
# 反而显得假）。让模型浮在渐变里，发出去更像"数字手办"。
ground = bpy.data.objects.get("MaidGround")
if ground:
    ground.hide_render = True
    ground.hide_viewport = True
    print("[turntable] 地面已隐藏")

# ---------------------------------------------------------------- 对称布光
# 原来 setup_scene 的 Rim 灯在 (+0.7, +2.3, +1.7) —— 后方偏右，
# 于是背景右半边被照亮、左半边黑，贴到卡片上左右色差 90+，一眼看出是贴的。
# 转台要求背景均匀：改成左右对称的两盏侧后方灯 + 正面主光。
for o in list(bpy.data.objects):
    if o.type == "LIGHT" and o.name.startswith("Maid_"):
        bpy.data.objects.remove(o, do_unlink=True)

from mathutils import Vector


def _aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def add_area(name, loc, energy, size, color=(1.0, 0.96, 0.92)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.energy = energy
    o.data.size = size
    o.data.color = color
    _aim(o, (0.0, 0.01, 0.66))
    return o


# 左右对称的柔光，专门保证背景不偏色
add_area("TT_KeyL", (-1.55, -1.70, 1.55), 130.0, 2.4)
add_area("TT_KeyR", (1.55, -1.70, 1.55), 130.0, 2.4)
add_area("TT_Top", (0.0, -0.35, 2.55), 95.0, 2.2, (0.93, 0.96, 1.0))
add_area("TT_BackL", (-1.40, 1.90, 1.30), 55.0, 2.0, (0.80, 0.88, 1.0))
add_area("TT_BackR", (1.40, 1.90, 1.30), 55.0, 2.0, (0.80, 0.88, 1.0))

# ---------------------------------------------------------------- 渲染设置
S.render.engine = "CYCLES"
S.cycles.samples = 40
S.cycles.use_denoising = True
S.cycles.max_bounces = 6
S.render.resolution_x = SIZE
S.render.resolution_y = SIZE
S.render.resolution_percentage = 100
S.render.film_transparent = True
S.render.image_settings.file_format = "PNG"
S.render.image_settings.color_mode = "RGBA"
S.render.image_settings.compression = 60
try:
    S.view_settings.view_transform = "Standard"
    S.view_settings.look = "None"
    S.view_settings.exposure = -0.15
except Exception as e:
    print("[turntable] view settings:", e)

# ---------------------------------------------------------------- 展台相机
# 稍微俯视一点，能看到脸和裙摆，也能看到一点头顶，立体感好
cam = bpy.data.objects.get("MaidCam")
if cam is None:
    cam_data = bpy.data.cameras.new("MaidCam")
    cam = bpy.data.objects.new("MaidCam", cam_data)
    S.collection.objects.link(cam)
S.camera = cam
cam.data.lens = 52.0

TARGET = (0.0, 0.01, 0.66)
DIST = 2.42
ELEV = math.radians(11.0)


def place_camera(az_deg):
    az = math.radians(az_deg)
    x = TARGET[0] + math.sin(az) * math.cos(ELEV) * DIST
    y = TARGET[1] - math.cos(az) * math.cos(ELEV) * DIST
    z = TARGET[2] + math.sin(ELEV) * DIST
    cam.location = (x, y, z)
    d = (TARGET[0] - x, TARGET[1] - y, TARGET[2] - z)
    from mathutils import Vector
    cam.rotation_euler = Vector(d).to_track_quat("-Z", "Y").to_euler()


# 转模型而不是转相机：地面/灯光保持不动，阴影跟着模型转，才有展台的味道
place_camera(0.0)

print("[turntable] %d 帧 · %dx%d · 输出 %s" % (FRAMES, SIZE, SIZE, OUT))
for i in range(FRAMES):
    ROOT.rotation_euler = (0.0, 0.0, 2.0 * math.pi * i / FRAMES)
    S.frame_set(i + 1)
    path = os.path.join(OUT, "frame_%03d.png" % i).replace("\\", "/")
    S.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if i == 0 or (i + 1) % 6 == 0:
        print("[turntable] %d/%d -> %s" % (i + 1, FRAMES, path))

# 复位，别把 blend 存成转了一半的状态
ROOT.rotation_euler = (0.0, 0.0, 0.0)
print("[turntable] done: %s" % OUT)
