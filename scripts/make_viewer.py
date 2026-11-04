# -*- coding: utf-8 -*-
"""生成一个自包含的 3D 查看器网页：把 three.js(r140 UMD)、GLTFLoader、OrbitControls
和 chibi_maid.glb(base64) 全部内联进单个 HTML。产出可直接 file:// 双击打开，无需联网/服务器。
用法：~/bin/python make_viewer.py <three.tgz> <chibi_maid.glb> <输出.html>
"""
import base64
import io
import os
import sys
import tarfile

TGZ, GLB, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
WANT = {
    "package/build/three.min.js": "THREE_JS",
    "package/examples/js/loaders/GLTFLoader.js": "GLTF_LOADER",
    "package/examples/js/controls/OrbitControls.js": "ORBIT",
}

parts = {}
with tarfile.open(TGZ, "r:gz") as tf:
    for member in tf.getmembers():
        if member.name in WANT:
            parts[WANT[member.name]] = tf.extractfile(member).read().decode("utf-8")
missing = set(WANT.values()) - set(parts)
assert not missing, "missing from tarball: %s" % missing
for k, v in parts.items():
    print("%-14s %8.1f KB" % (k, len(v) / 1024.0))

with open(GLB, "rb") as fh:
    glb_b64 = base64.b64encode(fh.read()).decode("ascii")
print("glb base64     %8.1f KB" % (len(glb_b64) / 1024.0))

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>歪毛小女仆 · 3D</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #0d1020; }
  body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; color: #e8ecf8; }
  #app { position: fixed; inset: 0; }
  canvas { display: block; }
  .hud { position: fixed; left: 18px; top: 16px; pointer-events: none; user-select: none; }
  .hud h1 { margin: 0; font-size: 20px; letter-spacing: 2px; font-weight: 600;
            text-shadow: 0 2px 12px rgba(0,0,0,.6); }
  .hud p { margin: 6px 0 0; font-size: 12px; opacity: .72; }
  #bar { position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%);
         display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
  #bar button { cursor: pointer; border: 1px solid rgba(160,190,255,.30);
                background: rgba(28,36,70,.72); color: #dfe7ff; font-size: 13px;
                padding: 7px 14px; border-radius: 999px; backdrop-filter: blur(6px);
                transition: .18s; font-family: inherit; }
  #bar button:hover { background: rgba(60,90,170,.85); border-color: rgba(160,190,255,.7); }
  #bar button.on { background: #4f8fe8; border-color: #8fbcff; color: #fff; }
  #load { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;
          font-size: 15px; letter-spacing: 3px; background: #0d1020; transition: opacity .5s; }
  #load.hide { opacity: 0; pointer-events: none; }
  #err { position: fixed; inset: 0; display: none; align-items: center; justify-content: center;
         text-align: center; padding: 40px; font-size: 14px; line-height: 1.8; color: #ffb4b4; }
</style>
</head>
<body>
<div id="app"></div>
<div class="hud">
  <h1>歪毛小女仆</h1>
  <p>左键拖拽旋转 · 滚轮缩放 · 右键平移</p>
</div>
<div id="bar">
  <button id="bSpin" class="on">自动旋转</button>
  <button data-view="front">正面</button>
  <button data-view="three">3/4 侧</button>
  <button data-view="side">侧面</button>
  <button data-view="back">背面</button>
  <button data-view="face">看脸</button>
  <button data-view="reset">复位</button>
</div>
<div id="load">正在把小女仆请出来…</div>
<div id="err"></div>

<script>/*__THREE_JS__*/</script>
<script>/*__GLTF_LOADER__*/</script>
<script>/*__ORBIT__*/</script>
<script id="glb" type="application/octet-stream">__GLB_B64__</script>
<script>
(function () {
  var VIEWS = {
    front: [0.00, 0.72, 2.55], three: [1.60, 0.95, 2.05], side: [2.60, 0.80, 0.05],
    back:  [0.00, 0.72, -2.60], reset: [0.75, 0.95, 2.45], face: [0.30, 1.02, 1.15]
  };
  var TARGET = null, TARGET_FACE = null;

  try {
    // ---- 渲染器 / 场景 / 相机 -------------------------------------------------
    var app = document.getElementById('app');
    var renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setClearColor(0x000000, 0);
    app.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    scene.background = (function () {
      var c = document.createElement('canvas'); c.width = 8; c.height = 256;
      var g = c.getContext('2d').createLinearGradient(0, 0, 0, 256);
      g.addColorStop(0.0, '#2b3a6e'); g.addColorStop(0.45, '#8e9dc4');
      g.addColorStop(0.72, '#dfe4f2'); g.addColorStop(1.0, '#f2f0f7');
      var ctx = c.getContext('2d'); ctx.fillStyle = g; ctx.fillRect(0, 0, 8, 256);
      var t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t;
    })();

    var camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.05, 100);
    camera.position.set(0.75, 0.95, 2.45);

    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.minDistance = 0.7; controls.maxDistance = 8;
    controls.maxPolarAngle = Math.PI * 0.52;
    controls.autoRotate = true; controls.autoRotateSpeed = 1.6;

    // ---- 灯 ----------------------------------------------------------------
    scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x6a6f8a, 1.05));
    var key = new THREE.DirectionalLight(0xfff4ea, 1.5);
    key.position.set(-2.0, 3.2, 2.6); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.near = 0.5; key.shadow.camera.far = 12;
    key.shadow.camera.left = -1.6; key.shadow.camera.right = 1.6;
    key.shadow.camera.top = 2.0; key.shadow.camera.bottom = -0.4;
    key.shadow.bias = -0.0006; key.shadow.radius = 3;
    scene.add(key);
    var rim = new THREE.DirectionalLight(0xcfe0ff, 1.05); rim.position.set(1.6, 2.0, -2.6); scene.add(rim);
    var fill = new THREE.DirectionalLight(0xdce6ff, 0.45); fill.position.set(2.4, 0.8, 1.8); scene.add(fill);

    // ---- 地面上那块柔和的影子 ------------------------------------------------
    var sh = (function () {
      var c = document.createElement('canvas'); c.width = c.height = 256;
      var x = c.getContext('2d');
      var g = x.createRadialGradient(128, 128, 4, 128, 128, 126);
      g.addColorStop(0, 'rgba(40,50,90,.55)'); g.addColorStop(0.55, 'rgba(60,70,110,.22)');
      g.addColorStop(1, 'rgba(60,70,110,0)');
      x.fillStyle = g; x.fillRect(0, 0, 256, 256);
      var t = new THREE.CanvasTexture(c);
      var m = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 2.6),
        new THREE.MeshBasicMaterial({ map: t, transparent: true, depthWrite: false }));
      m.rotation.x = -Math.PI / 2; m.position.y = 0.001; return m;
    })();
    scene.add(sh);

    // ---- 读模型（base64 直接 parse，不碰网络/不做 XHR） -----------------------
    var b64 = document.getElementById('glb').textContent.trim();
    var bin = atob(b64), buf = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);

    new THREE.GLTFLoader().parse(buf.buffer, '', function (gltf) {
      var root = gltf.scene;
      root.traverse(function (o) {
        if (o.isMesh) {
          o.castShadow = true; o.receiveShadow = true;
          if (o.material) { o.material.envMapIntensity = 0.5; }
        }
      });
      scene.add(root);

      var box = new THREE.Box3().setFromObject(root);
      var c = box.getCenter(new THREE.Vector3());
      var h = box.getSize(new THREE.Vector3()).y;
      TARGET = new THREE.Vector3(c.x, box.min.y + h * 0.52, c.z);
      TARGET_FACE = new THREE.Vector3(c.x, box.min.y + h * 0.78, c.z);
      controls.target.copy(TARGET);
      // 影子跟着角色走
      sh.position.set(c.x, 0.001, c.z + 0.05);

      document.getElementById('load').classList.add('hide');
      document.title = '歪毛小女仆 · 3D';
    }, function (e) {
      document.getElementById('load').style.display = 'none';
      var el = document.getElementById('err');
      el.style.display = 'flex';
      el.innerHTML = '模型没读进来 :(<br>' + (e && e.message ? e.message : e);
    });

    // ---- 视角按钮 ------------------------------------------------------------
    function flyTo(v) {
      var p = VIEWS[v]; if (!p) return;
      var want = new THREE.Vector3(p[0], p[1], p[2]);
      var from = camera.position.clone(), n = 0;
      (function step() {
        n++; var t = Math.min(n / 24, 1), e = 1 - Math.pow(1 - t, 3);
        camera.position.lerpVectors(from, want, e);
        controls.target.lerp(v === 'face' ? TARGET_FACE : TARGET, 0.12);
        if (t < 1) requestAnimationFrame(step);
      })();
    }
    document.getElementById('bar').addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return;
      if (b.id === 'bSpin') {
        controls.autoRotate = !controls.autoRotate;
        b.classList.toggle('on', controls.autoRotate); return;
      }
      if (b.dataset.view) flyTo(b.dataset.view);
    });

    window.addEventListener('resize', function () {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    (function loop() {
      requestAnimationFrame(loop);
      if (TARGET) controls.target.lerp(TARGET, 0.0); // 保持不动，留给拖拽
      controls.update();
      renderer.render(scene, camera);
    })();
  } catch (e) {
    var el = document.getElementById('err');
    el.style.display = 'flex';
    el.innerHTML = '这个浏览器跑不动 WebGL :(<br>' + (e && e.message ? e.message : e) +
      '<br><br>换个 Chrome / Edge 试试。';
  }
})();
</script>
</body>
</html>
"""

html = (HTML.replace("/*__THREE_JS__*/", parts["THREE_JS"])
            .replace("/*__GLTF_LOADER__*/", parts["GLTF_LOADER"])
            .replace("/*__ORBIT__*/", parts["ORBIT"])
            .replace("__GLB_B64__", glb_b64))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(html)
print("written %s  %.2f MB" % (OUT, os.path.getsize(OUT) / 1048576.0))
