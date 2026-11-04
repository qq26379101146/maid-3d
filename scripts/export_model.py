# -*- coding: utf-8 -*-
"""交付脚本：导出 .blend / .glb，并渲染成品图。

用法（在 Blender 里 exec 本文件；需先跑过 build_model.py 和 setup_scene.py）：
    p = r".../projects/maid-3d/scripts/export_model.py"
    exec(compile(open(p, encoding="utf-8").read(), "export_model.py", "exec"), {"__name__": "__main__"})

产物：
    model/chibi_maid.blend   完整场景（模型 + 灯光 + 相机）
    model/chibi_maid.glb     只有角色本体，给 Unity/UE/Blender 直接导入
    renders/hero.png         正面主图 1080x1080
    renders/view_front.png / view_three_quarter.png / view_left.png / view_back.png
幂等：重复执行直接覆盖。
"""
import os
import math
import bpy
import mathutils

ROOT = r"C:/Users/001/Documents/deepseek-harness/default-workspace/projects/maid-3d"
MODEL_DIR = os.path.join(ROOT, "model")
REND_DIR = os.path.join(ROOT, "renders")
for d in (MODEL_DIR, REND_DIR):
    os.makedirs(d, exist_ok=True)

scene = bpy.context.scene
maid_objs = [o for o in bpy.data.objects
             if o.type == "MESH" and o.name.startswith("MD_")]
root = bpy.data.objects.get("ChibiMaid_Root")

# ---------------------------------------------------------------- 1) .blend
blend_path = os.path.join(MODEL_DIR, "chibi_maid.blend").replace("\\", "/")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("[export] blend ->", blend_path)

# ---------------------------------------------------------------- 2) .glb（只导角色）
bpy.ops.object.select_all(action="DESELECT")
for o in maid_objs:
    o.select_set(True)
if root:
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
glb_path = os.path.join(MODEL_DIR, "chibi_maid.glb").replace("\\", "/")
bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB",
                          use_selection=True, export_apply=True,
                          export_yup=True)
print("[export] glb ->", glb_path,
      "%.2f MB" % (os.path.getsize(glb_path) / 1048576.0))

# ---------------------------------------------------------------- 3) 渲染多视图
cam_data = bpy.data.cameras.new("MaidViewCam")
cam_data.lens = 58
cam = bpy.data.objects.new("MaidViewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.render.film_transparent = False
# 交付图用 Cycles：EEVEE Next 出来的成品偏平，Cycles 48~64 采样在本地只要 ~15 秒/张
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.use_adaptive_sampling = True
scene.view_settings.exposure = -0.15

TARGET = mathutils.Vector((0.0, 0.01, 0.68))
DIST = 2.75


def shoot(az_deg, elev_deg, path):
    az = math.radians(az_deg)
    el = math.radians(elev_deg)
    loc = TARGET + mathutils.Vector((math.sin(az) * math.cos(el) * DIST,
                                     -math.cos(az) * math.cos(el) * DIST,
                                     math.sin(el) * DIST))
    cam.location = loc
    cam.rotation_euler = (TARGET - loc).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = path.replace("\\", "/")
    bpy.ops.render.render(write_still=True)
    print("[export] render ->", scene.render.filepath)


shots = [(0, 4, "hero.png"),
         (0, 2, "view_front.png"),
         (38, 8, "view_three_quarter.png"),
         (-88, 4, "view_left.png"),
         (180, 6, "view_back.png")]
for az, el, name in shots:
    shoot(az, el, os.path.join(REND_DIR, name))

print("[export] done. objects=%d faces=%d"
      % (len(maid_objs), sum(len(o.data.polygons) for o in maid_objs)))
