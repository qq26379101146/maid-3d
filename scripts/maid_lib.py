# -*- coding: utf-8 -*-
"""歪毛小女仆 —— 建模公共库（材质 / 基础体 / 球链）。

在 Blender 里由 build_model.py 导入使用：
    exec(compile(open(LIB, encoding="utf-8").read(), LIB, "exec"), globals())
纯 bpy，不联网、不花钱。
"""
import bpy
import math
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------- 清场


def clear_scene(keep_camera_light=True):
    """删掉默认场景里的所有物体，并清掉无用户的旧数据块。"""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                 bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)
    bpy.context.scene.frame_set(1)


def get_collection(name="ChibiMaid"):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_collection(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


# ---------------------------------------------------------------- 颜色 / 材质

def srgb(hexstr):
    """#RRGGBB -> Blender 线性色（渲染出来才跟立绘一个色）。"""
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def make_mat(name, hexcol, rough=0.5, metal=0.0, spec=0.5,
             emis=None, emis_str=0.0, alpha=1.0, ior=1.45):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    for key in ("Specular IOR Level", "Specular"):
        if key in b.inputs:
            b.inputs[key].default_value = spec
            break
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    if emis:
        for key in ("Emission Color", "Emission"):
            if key in b.inputs:
                b.inputs[key].default_value = srgb(emis)
                break
        if "Emission Strength" in b.inputs:
            b.inputs["Emission Strength"].default_value = emis_str
    return m


PALETTE = {
    "skin":       ("#eccbb6", 0.52, 0.0, 0.42, None, 0.0),
    "hair":       ("#2c3a6e", 0.34, 0.0, 0.55, None, 0.0),
    "hair_deep":  ("#1f2a52", 0.38, 0.0, 0.45, None, 0.0),
    "hair_hi":    ("#45579b", 0.28, 0.0, 0.65, None, 0.0),
    "dress":      ("#1b2142", 0.56, 0.0, 0.40, None, 0.0),
    "dress_deep": ("#12172f", 0.58, 0.0, 0.35, None, 0.0),
    "lace":       ("#f7f5fa", 0.44, 0.0, 0.50, None, 0.0),
    "lace_soft":  ("#e6e4ef", 0.52, 0.0, 0.42, None, 0.0),
    "eye":        ("#2f6fd0", 0.12, 0.0, 0.75, "#1c4fa8", 0.45),
    "eye_dark":   ("#101c3d", 0.14, 0.0, 0.70, None, 0.0),
    "eye_white":  ("#ffffff", 0.10, 0.0, 0.80, "#ffffff", 0.30),
    "gem":        ("#4f8fe8", 0.10, 0.0, 0.85, "#3f7fe0", 1.10),
    "gold":       ("#c9a86a", 0.34, 0.72, 0.55, None, 0.0),
    "shoe":       ("#17171c", 0.26, 0.0, 0.60, None, 0.0),
    "blush":      ("#f7bcc1", 0.62, 0.0, 0.30, None, 0.0),
    "mouth":      ("#b8546a", 0.45, 0.0, 0.40, None, 0.0),
    "brow":       ("#33406e", 0.50, 0.0, 0.30, None, 0.0),
}
MATS = {}


def boot_materials():
    MATS.clear()
    for k, v in PALETTE.items():
        MATS[k] = make_mat("MM_" + k, v[0], rough=v[1], metal=v[2],
                           spec=v[3], emis=v[4], emis_str=v[5])
    return MATS


def M(key):
    return MATS[key]


# ---------------------------------------------------------------- 基础体

def _finish(obj, name, mat, smooth=True):
    obj.name = name
    obj.data.name = name + "_mesh"
    if mat is not None:
        obj.data.materials.append(mat)
    if smooth and hasattr(obj.data, "polygons"):
        for p in obj.data.polygons:
            p.use_smooth = True
    move_to_collection(obj, get_collection())
    return obj


def sphere(name, loc, r=1.0, scale=(1, 1, 1), mat=None, rot=(0, 0, 0),
           seg=48, ring=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring,
                                         radius=r, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return _finish(o, name, mat)


def cylinder(name, loc, r=0.1, depth=0.2, mat=None, rot=(0, 0, 0),
             scale=(1, 1, 1), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return _finish(o, name, mat)


def cone(name, loc, r1=0.3, r2=0.1, depth=0.3, mat=None, rot=(0, 0, 0),
         scale=(1, 1, 1), verts=64):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return _finish(o, name, mat)


def torus(name, loc, major=0.3, minor=0.02, mat=None, rot=(0, 0, 0),
          scale=(1, 1, 1), mseg=64, nseg=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=mseg, minor_segments=nseg,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return _finish(o, name, mat)


def box(name, loc, size=(0.1, 0.1, 0.1), mat=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    return _finish(o, name, mat, smooth=False)


def bezier(p0, p1, p2, n):
    """二次贝塞尔采样，返回 n 个点。"""
    pts = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        a = (1 - t) ** 2
        b = 2 * (1 - t) * t
        c = t ** 2
        pts.append(Vector((a * p0[0] + b * p1[0] + c * p2[0],
                           a * p0[1] + b * p1[1] + c * p2[1],
                           a * p0[2] + b * p1[2] + c * p2[2])))
    return pts


def lerp_chain(points, n):
    """折线重采样成 n 个点（Catmull-Rom 近似平滑）。"""
    if len(points) < 2:
        return [Vector(points[0])] * n
    pts = [Vector(p) for p in points]
    out = []
    for i in range(n):
        t = i / (n - 1) * (len(pts) - 1)
        idx = min(int(t), len(pts) - 2)
        f = t - idx
        p0 = pts[max(idx - 1, 0)]
        p1 = pts[idx]
        p2 = pts[idx + 1]
        p3 = pts[min(idx + 2, len(pts) - 1)]
        f2 = f * f
        f3 = f2 * f
        v = 0.5 * ((2 * p1) + (-p0 + p2) * f +
                   (2 * p0 - 5 * p1 + 4 * p2 - p3) * f2 +
                   (-p0 + 3 * p1 - 3 * p2 + p3) * f3)
        out.append(v)
    return out


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    return j


def blob_chain(name, control_pts, radii, mat, n=None, seg=28, ring=14,
               scale=(1, 1, 1), rot_jitter=0.0):
    """沿控制点串一串球（可粗可细），像挤奶油一样堆出发束/肢体。"""
    if n is None:
        n = max(len(control_pts) * 3, 10)
    pts = lerp_chain(control_pts, n)
    if callable(radii):
        rs = [radii(i / (n - 1)) for i in range(n)]
    elif isinstance(radii, (int, float)):
        rs = [radii] * n
    else:
        rs = list(radii)
    objs = []
    for i, p in enumerate(pts):
        rot = (0, 0, 0)
        if rot_jitter:
            rot = (math.sin(i * 1.7) * rot_jitter, 0, math.cos(i * 1.3) * rot_jitter)
        objs.append(sphere("%s_blob%02d" % (name, i), tuple(p), rs[i],
                           scale=scale, mat=mat, rot=rot, seg=seg, ring=ring))
    j = join_objects(objs, name)
    return j


def apply_transforms(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.select_all(action="DESELECT")


def lace_ring(name, center, radius, n=20, r=0.032, mat=None, z_wave=0.012,
             a0=0.0, a1=math.tau, r_wave=0.0, scale=(1, 1, 1)):
    """沿圆周摆一圈小球 —— 荷叶边 / 蕾丝边。"""
    cx, cy, cz = center
    objs = []
    for i in range(n):
        t = a0 + (a1 - a0) * (i / n)
        rr = radius + (math.sin(t * n / 2) * r_wave if r_wave else 0.0)
        x = cx + math.cos(t) * rr
        y = cy + math.sin(t) * rr
        z = cz + (z_wave if i % 2 == 0 else -z_wave)
        objs.append(sphere("%s_%02d" % (name, i), (x, y, z), r,
                           scale=scale, mat=mat, seg=16, ring=8))
    return join_objects(objs, name)


def strand(name, control_pts, radii, mat=None, n=None, seg=None, ring=None,
           scale=(1, 1, 1), res=14, bevel_res=8, caps=True):
    """沿控制点拉一条光滑发束（贝塞尔曲线 + 变半径 bevel）——
    比「一球球堆」干净得多，没有竹节纹。radii 可以是数值或 t -> 半径 的函数。"""
    pts = [Vector(p) for p in control_pts]
    if len(pts) < 2:
        raise ValueError("strand 至少两个控制点")
    cu = bpy.data.curves.new(name + "_cu", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_depth = 1.0
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = caps
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        t = i / (len(pts) - 1)
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
        if callable(radii):
            bp.radius = max(0.002, radii(t))
        elif isinstance(radii, (int, float)):
            bp.radius = max(0.002, radii)
        else:
            rl = list(radii)
            bp.radius = max(0.002, rl[i] if i < len(rl) else rl[-1])
    ob = bpy.data.objects.new(name, cu)
    get_collection().objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object
    # 关键：曲线转 mesh 后，物体原点在世界原点。此时直接 ob.scale = scale
    # 会把发丝**连同位置一起**按原点缩放（发丝被拽向中轴、越细越往原点缩），
    # 结果就是明明算好的远端位置全被拉回来、永远埋进头发里。
    # 必须先把原点挪到发丝自身中心，再缩放，才是"只压扁形状、不动位置"。
    if scale != (1, 1, 1):
        xs = [v.co for v in ob.data.vertices]
        cx = sum(v.x for v in xs) / len(xs)
        cy = sum(v.y for v in xs) / len(xs)
        cz = sum(v.z for v in xs) / len(xs)
        for v in ob.data.vertices:
            v.co.x -= cx; v.co.y -= cy; v.co.z -= cz
        ob.location = (cx, cy, cz)
        ob.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, name, mat)


def report():
    scn = bpy.context.scene
    objs = [o for o in scn.objects if o.type == "MESH"]
    tris = sum(len(o.data.polygons) for o in objs)
    print("[maid_lib] objects=%d  faces=%d" % (len(objs), tris))
    for o in sorted(objs, key=lambda s: s.name):
        print("   -", o.name)
    return len(objs), tris
