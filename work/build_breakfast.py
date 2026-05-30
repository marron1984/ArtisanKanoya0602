#!/usr/bin/env python3
"""
「世界一の朝食」コンセプト 朝食フォーカス動画
縦型 1080x1920。朝の光を意識した明るくみずみずしいグレーディング。
Ken Burns 風ズーム + クロスフェード + 和文テキスト。
zoompan は単一入力フレーム(-frames:v で制御)から d フレーム生成し暴走を防ぐ。
"""
import os, subprocess, sys

ROOT = "/home/user/ArtisanKanoya0602"
SRC = os.path.join(ROOT, "work", "src")
OUT_DIR = os.path.join(ROOT, "videos")
TMP = os.path.join(ROOT, "work", "clips_bf")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(ROOT, "work", "ffmpeg_bf.log")
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

# Breakfast narrative: smoothie -> smoothie -> salad -> bread -> table -> closing
picks = ["img_001.jpg", "img_010.jpg", "img_046.jpg",
         "img_070.jpg", "img_085.jpg", "img_085.jpg"]
captions = [
    "朝が、待ち遠しくなる。",
    "目覚めの一杯から。",
    "朝の光と、彩り野菜。",
    "焼きたての香りに包まれて。",
    "世界一の朝食、はじめます。",
    "世界一の朝食　—　Artisan Kanoya",
]
# last clip uses a stronger zoom to settle on the brand card
zoom_in = [True, False, True, False, True, False]

W, H = 1080, 1920
CLIP, XF, FPS = 4.5, 1.2, 30
d_frames = int(CLIP * FPS)
sw, sh = int(W * 1.25), int(H * 1.25)


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


logf = open(LOG, "w")


def run(cmd):
    logf.write(" ".join(cmd) + "\n"); logf.flush()
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode


clip_files = []
for i, name in enumerate(picks):
    src = os.path.join(SRC, name)
    if not os.path.exists(src):
        print("MISSING", src); sys.exit(1)
    if zoom_in[i]:
        z = "min(zoom+0.0010,1.20)"
    else:
        z = "if(eq(on,0),1.20,max(zoom-0.0010,1.0))"
    cap = esc(captions[i])
    fs = 50 if i == len(picks) - 1 else 60
    # Bright fresh "morning" grade: lifted brightness, gentle warm highlights, airy.
    vf = (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={sw}:{sh},"
        f"zoompan=z='{z}':d={d_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
        f"eq=brightness=0.05:saturation=1.14:contrast=1.05:gamma=1.04,"
        f"colorbalance=rh=0.04:gh=0.02:bh=-0.02:rm=0.02:bm=-0.01,"
        f"drawtext=fontfile={FONT}:text='{cap}':"
        f"fontcolor=white:fontsize={fs}:"
        f"shadowcolor=black@0.55:shadowx=2:shadowy=2:"
        f"box=1:boxcolor=black@0.30:boxborderw=28:"
        f"x=(w-text_w)/2:y=h-360:"
        f"alpha='if(lt(t,0.6),t/0.6,if(lt(t,{CLIP-0.6}),1,({CLIP}-t)/0.6))',"
        f"setsar=1,format=yuv420p"
    )
    out = os.path.join(TMP, f"clip_{i:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(CLIP),
           "-i", src, "-vf", vf, "-frames:v", str(d_frames),
           "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-preset", "veryfast", out]
    if run(cmd) != 0 or not os.path.exists(out):
        print("CLIP_FAIL", i); sys.exit(2)
    clip_files.append(out)
    print("clip", i, "ok")

cmd = ["ffmpeg", "-y"]
for c in clip_files:
    cmd += ["-i", c]
N = len(clip_files)
parts = []
prev, offset = "0:v", CLIP - XF
for i in range(1, N):
    out = f"x{i}" if i < N - 1 else "xf"
    parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}[{out}]")
    prev = out
    offset += (CLIP - XF)
parts.append("[xf]vignette=PI/6,format=yuv420p[vout]")

out_file = os.path.join(OUT_DIR, "02_worlds_best_breakfast.mp4")
cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "20", "-preset", "medium", "-movflags", "+faststart", out_file]
rc = run(cmd)
logf.close()
ok = rc == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 100_000
print("final_rc", rc, "ok", ok,
      "size", os.path.getsize(out_file) if os.path.exists(out_file) else 0)
sys.exit(0 if ok else 3)
