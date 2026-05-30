#!/usr/bin/env python3
"""
[①第1木曜・興味喚起] 初夏の屋外カフェ テーザー動画
あえて売らない/印象・保存重視。季節(初夏)・世界観(鹿のいる庭・外のカフェ時間)を演出。
縦型 1080x1920。Ken Burns 風ズーム + クロスフェード + 初夏の暖色グレーディング + 和文テキスト。

実装メモ:
  zoompan は「1入力フレーム -> d 出力フレーム」を出す。-loop 1 で無限フレームを与えると
  入力ごとに d フレーム出て出力が爆発する。よって各画像は zoompan に 1フレームだけ渡し、
  d で希望のクリップ長を作る。各クリップは独立に作って concat ではなく xfade で連結する。
"""
import os, subprocess, sys

ROOT = "/home/user/ArtisanKanoya0602"
SRC = os.path.join(ROOT, "work", "src")
OUT_DIR = os.path.join(ROOT, "videos")
TMP = os.path.join(ROOT, "work", "clips")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(ROOT, "work", "ffmpeg.log")
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

picks = ["img_001.jpg", "img_046.jpg", "img_010.jpg",
         "img_070.jpg", "img_030.jpg", "img_085.jpg"]
captions = [
    "初夏の、朝。",
    "鹿のいる庭を眺めながら。",
    "外で過ごす、ゆっくりの時間。",
    "風がはこぶ、焼きたての香り。",
    "今日は、何もしない贅沢を。",
    "Artisan Kanoya　—　初夏のテラスにて",
]

W, H = 1080, 1920
CLIP, XF, FPS = 4.5, 1.2, 30
d_frames = int(CLIP * FPS)
sw, sh = int(W * 1.25), int(H * 1.25)


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


logf = open(LOG, "w")


def run(cmd):
    logf.write(" ".join(cmd) + "\n")
    logf.flush()
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode


# 1) Build each clip independently (fast, bounded: exactly d_frames frames).
clip_files = []
for i, name in enumerate(picks):
    src = os.path.join(SRC, name)
    if not os.path.exists(src):
        print("MISSING", src); sys.exit(1)
    if i % 2 == 0:
        z = "min(zoom+0.0010,1.20)"
    else:
        z = "if(eq(on,0),1.20,max(zoom-0.0010,1.0))"
    cap = esc(captions[i])
    fs = 52 if i == len(picks) - 1 else 60
    vf = (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={sw}:{sh},"
        f"zoompan=z='{z}':d={d_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
        f"eq=brightness=0.02:saturation=1.12:contrast=1.04,"
        f"colorbalance=rm=0.04:gm=0.01:bm=-0.03,"
        f"drawtext=fontfile={FONT}:text='{cap}':"
        f"fontcolor=white:fontsize={fs}:"
        f"shadowcolor=black@0.5:shadowx=2:shadowy=2:"
        f"box=1:boxcolor=black@0.28:boxborderw=28:"
        f"x=(w-text_w)/2:y=h-360:"
        f"alpha='if(lt(t,0.6),t/0.6,if(lt(t,{CLIP-0.6}),1,({CLIP}-t)/0.6))',"
        f"setsar=1,format=yuv420p"
    )
    out = os.path.join(TMP, f"clip_{i:02d}.mp4")
    # -frames:v 1 on input limits zoompan to ONE source frame -> exactly d_frames out.
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(CLIP),
           "-i", src, "-vf", vf, "-frames:v", str(d_frames),
           "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-preset", "veryfast", out]
    rc = run(cmd)
    if rc != 0 or not os.path.exists(out):
        print("CLIP_FAIL", i, "rc", rc); sys.exit(2)
    clip_files.append(out)
    print("clip", i, "ok")

# 2) Crossfade-chain the clips into the final teaser.
cmd = ["ffmpeg", "-y"]
for c in clip_files:
    cmd += ["-i", c]
N = len(clip_files)
parts = []
prev, offset = "0:v", CLIP - XF
for i in range(1, N):
    cur = f"{i}:v"
    out = f"x{i}" if i < N - 1 else "xf"
    parts.append(f"[{prev}][{cur}]xfade=transition=fade:duration={XF}:offset={offset:.3f}[{out}]")
    prev = out
    offset += (CLIP - XF)
parts.append("[xf]vignette=PI/5,format=yuv420p[vout]")

out_file = os.path.join(OUT_DIR, "01_shoka_outdoor_cafe.mp4")
cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "20", "-preset", "medium", "-movflags", "+faststart", out_file]
rc = run(cmd)
logf.close()

ok = rc == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 100_000
print("final_rc", rc, "ok", ok,
      "size", os.path.getsize(out_file) if os.path.exists(out_file) else 0)
sys.exit(0 if ok else 3)
