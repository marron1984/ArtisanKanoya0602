#!/usr/bin/env python3
"""
「世界一のディナー」コンセプト ディナーフォーカス動画
縦型 1080x1920。夜のキャンドルライトを思わせる暖色・ムーディーなグレーディング。
Ken Burns 風ズーム + クロスフェード + 和文テキスト + BGM。
フルコースの流れ(食卓→前菜→スープ→サラダ→魚→地酒→鴨→和牛→デザート)で構成。
zoompan は単一入力フレーム(-frames:v)から d フレーム生成して暴走を防ぐ。
"""
import os, subprocess, sys

ROOT = "/home/user/ArtisanKanoya0602"
SRC = os.path.join(ROOT, "work", "src_dinner")
OUT_DIR = os.path.join(ROOT, "videos")
TMP = os.path.join(ROOT, "work", "clips_dinner")
BGM = os.path.join(ROOT, "ArtisanKanoya.mp3")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(ROOT, "work", "ffmpeg_dinner.log")
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

# Dinner course narrative
picks = ["d_01_table.jpg", "d_02_amuse.jpg", "d_03_soup.jpg",
         "d_04_salad.jpg", "d_05_fish.jpg", "d_06_sake.jpg",
         "d_07_duck.jpg", "d_08_wagyu.jpg", "d_09_dessert.jpg"]
captions = [
    "ようこそ、夜の食卓へ。",
    "はじまりは、ひと皿の物語から。",
    "温かなスープに、心ほどけて。",
    "畑の彩りを、そのままに。",
    "海の恵みを、春の緑とともに。",
    "夜に寄り添う、奈良の地酒。",
    "火入れの妙、鴨のロースト。",
    "そして、主役の和牛へ。",
    "世界一のディナー　—　Artisan Kanoya",
]
# Alternate slow zoom-in / zoom-out; settle (zoom-in) on the closing brand card
zoom_in = [True, False, True, False, True, False, True, False, True]

W, H = 1080, 1920
CLIP, XF, FPS = 4.3, 1.2, 30
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
    fs = 48 if i == len(picks) - 1 else 58
    # Evening grade: deeper shadows, candle-warm highlights/mids, richer color, moody.
    vf = (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={sw}:{sh},"
        f"zoompan=z='{z}':d={d_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
        f"eq=brightness=-0.018:saturation=1.16:contrast=1.10:gamma=0.98,"
        f"colorbalance=rh=0.06:gh=0.02:bh=-0.05:rm=0.04:gm=0.01:bm=-0.04:rs=0.01:bs=0.01,"
        f"drawtext=fontfile={FONT}:text='{cap}':"
        f"fontcolor=white:fontsize={fs}:"
        f"shadowcolor=black@0.6:shadowx=2:shadowy=2:"
        f"box=1:boxcolor=black@0.34:boxborderw=28:"
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

N = len(clip_files)
total = N * CLIP - (N - 1) * XF  # final video length in seconds

cmd = ["ffmpeg", "-y"]
for c in clip_files:
    cmd += ["-i", c]
cmd += ["-i", BGM]
bgm_idx = N

parts = []
prev, offset = "0:v", CLIP - XF
for i in range(1, N):
    out = f"x{i}" if i < N - 1 else "xf"
    parts.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}[{out}]")
    prev = out
    offset += (CLIP - XF)
parts.append("[xf]vignette=PI/4.6,format=yuv420p[vout]")
# BGM: trim to video length with gentle fade in/out
parts.append(
    f"[{bgm_idx}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
    f"afade=t=in:st=0:d=1.0,afade=t=out:st={total-1.4:.3f}:d=1.4,"
    f"volume=0.85[aout]"
)

out_file = os.path.join(OUT_DIR, "03_worlds_best_dinner.mp4")
cmd += ["-filter_complex", ";".join(parts),
        "-map", "[vout]", "-map", "[aout]",
        "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-crf", "20", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", out_file]
rc = run(cmd)
logf.close()
ok = rc == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 100_000
print("total_len", round(total, 2), "final_rc", rc, "ok", ok,
      "size", os.path.getsize(out_file) if os.path.exists(out_file) else 0)
sys.exit(0 if ok else 3)
