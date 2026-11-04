# -*- coding: utf-8 -*-
"""歪毛小女仆 —— 灯光 / 相机 / 渲染设置 + 出图。

跑法（在 Blender 里）：
    p = r".../scripts/setup_scene.py"
    exec(compile(open(p, encoding="utf-8").read(), "setup_scene.py", "exec"), {"__name__": "__main__"})
参数：环境变量 MAID_RENDER_OUT 指定出图路径（默认 renders/maid_front.png）。
"""
import bpy
import math
import os
from mathutils import Vector

BASE = r"C:/Users/001/Documents/deepseek-harness/default-workspace/projects/maid-3d"
LIB = BASE + "/scripts/maid_lib.py"
exec(compile(open(LIB, encoding="utf-8").read(), "maid_lib.py", "exec"), globals())

S = bpy.context.scene
SUBJECT = Vector((0.0, 0.0, 0.70))


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ------------------------------------------------------------------ 世界
w = bpy.data.worlds.get("MaidWorld") or bpy.data.worlds.new("MaidWorld")
S.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = srgb("#e8ecf8")
bg.inputs[1].default_value = 0.55

# ------------------------------------------------------------------ 清掉旧灯 / 相机
for o in list(bpy.data.objects):
    if o.type in {"LIGHT", "CAMERA"} or o.name.startswith("MaidGround"):
        bpy.data.objects.remove(o, do_unlink=True)

# ------------------------------------------------------------------ 地面
bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, -0.001))
ground = bpy.context.active_object
ground.name = "MaidGround"
gmat = make_mat("MM_ground", "#dee2f0", rough=0.85, spec=0.2)
ground.data.materials.append(gmat)

# ------------------------------------------------------------------ 灯光
def area(name, loc, energy, size, color="#ffffff", target=SUBJECT):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.energy = energy
    o.data.size = size
    o.data.color = srgb(color)[:3]
    aim(o, target)
    move_to_collection(o, get_collection())
    return o


area("Maid_Key", (-1.7, -2.1, 2.3), 140.0, 2.6, "#fff4ea")
area("Maid_Fill", (2.0, -1.7, 0.85), 50.0, 2.2, "#dce6ff")
area("Maid_Rim", (0.7, 2.3, 1.7), 95.0, 1.8, "#cfe0ff")
area("Maid_Bounce", (0.0, -0.9, -0.35), 12.0, 1.6, "#ffffff", target=Vector((0, 0, 0.9)))

# ------------------------------------------------------------------ 相机
bpy.ops.object.camera_add(location=(0.0, -3.05, 0.98))
cam = bpy.context.active_object
cam.name = "MaidCam"
cam.data.lens = 58.0
aim(cam, Vector((0.0, 0.0, 0.715)))
S.camera = cam
move_to_collection(cam, get_collection())

# ------------------------------------------------------------------ 渲染设置
S.render.engine = "BLENDER_EEVEE_NEXT"
S.render.resolution_x = 1080
S.render.resolution_y = 1080
S.render.resolution_percentage = 100
S.render.film_transparent = False
S.render.image_settings.file_format = "PNG"
try:
    S.eevee.taa_render_samples = 64
except Exception as e:
    print("eevee samples:", e)
try:
    S.view_settings.view_transform = "Standard"
    S.view_settings.look = "None"
except Exception as e:
    print("view transform:", e)

out = os.environ.get("MAID_RENDER_OUT", BASE + "/renders/maid_front.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
S.render.filepath = out
print("[setup_scene] world/lights/camera ready -> %s" % out)

if os.environ.get("MAID_RENDER", "1") == "1":
    bpy.ops.render.render(write_still=True)
    print("[setup_scene] rendered:", out)
