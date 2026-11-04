#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把转台帧序列做成 GIF / MP4 / 分享卡。

用法：
    ~/bin/python make_share.py [帧目录] [输出目录]

产物（都在 out 目录）：
    chibi_maid_turn.gif    480px 循环 GIF，约 3~4 MB，微信/QQ 都能发
    chibi_maid_turn_small.gif  300px 轻量版，约 1.5 MB，流量友好
    chibi_maid_turn.mp4    560px H.264 视频，画质最好
    share_card.png         竖版分享卡：模型图 + 标题，方便直接发
"""
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "renders", "turntable")
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "share")
os.makedirs(OUT_DIR, exist_ok=True)

frames = sorted(f for f in os.listdir(FRAMES_DIR) if f.lower().endswith(".png"))
if not frames:
    raise SystemExit("没有找到帧: %s" % FRAMES_DIR)
print("帧数 %d" % len(frames))
# 转台帧是透明底（RGBA）。统一合成到同一个纯色底上：
# 背景因此绝对均匀，不会出现"一侧被灯打亮"的色差。
BG_RGB = (46, 52, 76)
_raw = [Image.open(os.path.join(FRAMES_DIR, f)) for f in frames]
imgs = []
for im in _raw:
    im = im.convert("RGBA")
    bg = Image.new("RGB", im.size, BG_RGB)
    bg.paste(im, (0, 0), im)          # 用 alpha 贴图
    imgs.append(bg)
W, H = imgs[0].size
print("尺寸 %dx%d" % (W, H))


def save_gif(path, size, frame_ms, colors=200, dither=False):
    """所有帧共用一套调色板，避免逐帧抖动产生的闪烁（GIF 发出去最忌讳这个）。

    frame_ms = 每帧毫秒数。注意 save(duration=) 收的是毫秒，别传成秒也别再乘 1000。
    """
    scaled = [im.resize((size, size), Image.LANCZOS) for im in imgs]
    # 用所有帧拼成的长图求一次全局调色板
    strip = Image.new("RGB", (size, size * len(scaled)))
    for i, im in enumerate(scaled):
        strip.paste(im, (0, i * size))
    pal = strip.quantize(colors=colors, method=Image.MEDIANCUT, dither=dither)
    qframes = [im.quantize(palette=pal, dither=Image.FLOYDSTEINBERG if dither else Image.NONE)
               for im in scaled]
    # 循环：36 帧转满 360°，第 36 帧本来就该回到 0°。
    # 所以直接收 36 帧、首帧接尾帧 —— 不要再补一张重复的首帧，
    # 补了会连续两帧一样，转起来"顿一下"。
    assert len(qframes) == 36, len(qframes)
    # Pillow 写 GIF 时会对 duration 做 centisecond 取整（10ms 一个台阶），
    # 传 48 会被写成 40；要想要 50ms 就传 50。
    qframes[0].save(path, save_all=True, append_images=qframes[1:],
                    duration=frame_ms, loop=0,
                    optimize=False, disposal=2)
    return os.path.getsize(path)


FRAME_MS = 50   # 36 帧 × 50ms = 每圈 1.8 秒，转得从容；GIF 延迟按 10ms 取整，正好 50
g1 = save_gif(os.path.join(OUT_DIR, "chibi_maid_turn.gif"), 480, FRAME_MS, colors=220)
print("gif(480) %.2f MB" % (g1 / 1048576.0))
g2 = save_gif(os.path.join(OUT_DIR, "chibi_maid_turn_small.gif"), 300, FRAME_MS, colors=180)
print("gif(300) %.2f MB" % (g2 / 1048576.0))

# ---------------------------------------------------------------- MP4
# 注意 ~/bin/ffmpeg 是个 bash 包装脚本，subprocess 直接调用会失败；
# 要找到真正的 exe（winget 的 Links 目录 / 系统 PATH 里都可能）。
FFMPEG_CANDIDATES = [
    os.path.expanduser(r"~/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"),
    r"C:/Users/001/bin/ffmpeg.exe",
]
ffmpeg = next((p for p in FFMPEG_CANDIDATES if os.path.exists(p)), None)
mp4_out = os.path.join(OUT_DIR, "chibi_maid_turn.mp4")
if ffmpeg:
    cmd = [ffmpeg, "-y", "-framerate", "22", "-i", os.path.join(FRAMES_DIR, "frame_%03d.png"),
           "-vf", "scale=560:560:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-movflags", "+faststart",
           mp4_out]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(mp4_out):
            print("mp4 %.2f MB" % (os.path.getsize(mp4_out) / 1048576.0))
        else:
            print("mp4 失败:", (r.stderr or "")[-300:])
    except Exception as e:
        print("mp4 异常:", e)
else:
    print("找不到 ffmpeg 的 exe，跳过 mp4（GIF 已经够用了）")

# ---------------------------------------------------------------- 分享卡（竖版）
# 帧已经合成到纯色底 (46,52,76)，卡片用同一个色 —— 模型图贴上去没有任何边界。
CARD_W, CARD_H = 1080, 1440
card = Image.new("RGB", (CARD_W, CARD_H), BG_RGB)
dr = ImageDraw.Draw(card)

HERO_Y = 250
hero = imgs[0].resize((CARD_W, CARD_W), Image.LANCZOS)
card.paste(hero, (0, HERO_Y))

def font(size, bold=False):
    for p in (r"C:/Windows/Fonts/msyhbd.ttc" if bold else r"C:/Windows/Fonts/msyh.ttc",
              r"C:/Windows/Fonts/simhei.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

title = "歪毛小女仆"
sub = "3D 模型 · 360° 转台"
f1, f2 = font(84, True), font(34)
tw = dr.textlength(title, font=f1)
dr.text(((CARD_W - tw) / 2, 62), title, font=f1, fill=(255, 255, 255))
sw = dr.textlength(sub, font=f2)
dr.text(((CARD_W - sw) / 2, 168), sub, font=f2, fill=(168, 196, 246))

foot = "Blender 纯程序化建模 · 大肥鱼"
f3 = font(28)
fw = dr.textlength(foot, font=f3)
dr.text(((CARD_W - fw) / 2, CARD_H - 96), foot, font=f3, fill=(150, 170, 210))

card_path = os.path.join(OUT_DIR, "share_card.png")
card.save(card_path)
print("card %.2f MB %s" % (os.path.getsize(card_path) / 1048576.0, card_path))

print("\n完成，文件都在:", OUT_DIR)
for f in sorted(os.listdir(OUT_DIR)):
    p = os.path.join(OUT_DIR, f)
    print("  %-28s %.2f MB" % (f, os.path.getsize(p) / 1048576.0))
