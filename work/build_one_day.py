#!/usr/bin/env python3
"""
「カノヤの一日」 朝から夜への一日の物語
モーニングとディナーの素材を一本に繋ぎ、グレーディングを
朝(明るく軽やか) → 夕暮れ(琥珀) → 夜(深い暖色)へと移ろわせる。
新要素: タイポグラフィの黒カード(冒頭/結び)、場面で変えるトランジション、
上部配置の箱なしキャプション。縦型 1080x1920、BGM付き 約29秒。
zoompan は単一入力フレーム(-frames:v)から d フレーム生成して暴走を防ぐ。
"""
import os, subprocess, sys

ROOT = "/home/user/ArtisanKanoya0602"
SRC = os.path.join(ROOT, "work", "day_src")
OUT_DIR = os.path.join(ROOT, "videos")
TMP = os.path.join(ROOT, "work", "clips_day")
BGM = os.path.join(ROOT, "ArtisanKanoya.mp3")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(ROOT, "work", "ffmpeg_day.log")
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

W, H = 1080, 1920
CLIP, XF, FPS = 3.8, 1.0, 30
d_frames = int(CLIP * FPS)
sw, sh = int(W * 1.25), int(H * 1.25)

# (kind, source/text, caption, grade, zoom_in)
#   kind: card=黒タイポカード / img=写真クリップ
#   grade: morning / dusk / night / none(card)
SEQ = [
    ("card", "一日が、\nご馳走になる。",            None,                       "none",    True),
    ("img",  "mo_smoothie.jpg",  "一日は、世界一の朝食から。",   "morning", True),
    ("img",  "mo_bread.jpg",     "朝のひかりと、焼きたての香り。", "morning", False),
    ("img",  "dn_drink0001.jpg", "日が暮れて、灯りがともる。",   "dusk",    True),
    ("img",  "dn_t0174.jpg",     "夜のはじまりに、ひと皿の物語。", "night",   False),
    ("img",  "dn_t0133.jpg",     "海の恵みと、春の緑。",       "night",   True),
    ("img",  "dn_t0093.jpg",     "火を纏う、主役の和牛。",      "night",   False),
    ("img",  "dn_t0218.jpg",     "甘い余韻を、最後に。",       "night",   True),
    ("img",  "dn_g0001.jpg",     "そして今夜も、世界一のディナー。", "night",  False),
    ("card", "L’Artisan Kanoya\n\n世界一の朝食と、\n世界一のディナー。", None, "none", True),
]
# 場面の切り替わりで変えるトランジション(9箇所)
TRANSITIONS = ["fade", "fade", "fadeblack", "fade",
               "slideleft", "fade", "circleopen", "fade", "fadeblack"]

GRADES = {
    "morning": ("eq=brightness=0.05:saturation=1.12:contrast=1.05:gamma=1.04,"
                "colorbalance=rh=0.03:gh=0.02:bh=-0.01:rm=0.02"),
    "dusk":    ("eq=brightness=0.01:saturation=1.10:contrast=1.06,"
                "colorbalance=rh=0.06:gh=0.02:bh=-0.04:rm=0.05:bm=-0.03"),
    "night":   ("eq=brightness=-0.018:saturation=1.16:contrast=1.10:gamma=0.98,"
                "colorbalance=rh=0.06:gh=0.02:bh=-0.05:rm=0.04:gm=0.01:bm=-0.04"),
}


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")


logf = open(LOG, "w")


def run(cmd):
    logf.write(" ".join(cmd) + "\n"); logf.flush()
    return subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL).returncode


clip_files = []
for i, (kind, src_or_text, cap, grade, zoom_in) in enumerate(SEQ):
    out = os.path.join(TMP, f"clip_{i:02d}.mp4")
    if kind == "card":
        # 黒地タイポカード: 静かなフェードで文字が浮かぶ
        lines = esc(src_or_text)
        fs = 64 if i == 0 else 54
        vf = (
            f"drawtext=fontfile={FONT}:text='{lines}':"
            f"fontcolor=white:fontsize={fs}:line_spacing=30:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"alpha='if(lt(t,0.8),t/0.8,if(lt(t,{CLIP-0.5}),1,({CLIP}-t)/0.5))',"
            f"format=yuv420p"
        )
        cmd = ["ffmpeg", "-y", "-f", "lavfi",
               "-i", f"color=c=0x0a0a0c:s={W}x{H}:r={FPS}:d={CLIP}",
               "-vf", vf, "-frames:v", str(d_frames),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "18", "-preset", "veryfast", out]
    else:
        src = os.path.join(SRC, src_or_text)
        if not os.path.exists(src):
            print("MISSING", src); sys.exit(1)
        if zoom_in:
            z = "min(zoom+0.0012,1.22)"
        else:
            z = "if(eq(on,0),1.22,max(zoom-0.0012,1.0))"
        captxt = esc(cap)
        # 箱なし・上部配置のエディトリアル風キャプション
        vf = (
            f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
            f"crop={sw}:{sh},"
            f"zoompan=z='{z}':d={d_frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
            f"{GRADES[grade]},"
            f"drawtext=fontfile={FONT}:text='{captxt}':"
            f"fontcolor=white:fontsize=54:"
            f"shadowcolor=black@0.85:shadowx=3:shadowy=3:"
            f"x=(w-text_w)/2:y=250:"
            f"alpha='if(lt(t,0.6),t/0.6,if(lt(t,{CLIP-0.6}),1,({CLIP}-t)/0.6))',"
            f"setsar=1,format=yuv420p"
        )
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS),
               "-t", str(CLIP), "-i", src, "-vf", vf,
               "-frames:v", str(d_frames), "-r", str(FPS),
               "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-crf", "18", "-preset", "veryfast", out]
    if run(cmd) != 0 or not os.path.exists(out):
        print("CLIP_FAIL", i); sys.exit(2)
    clip_files.append(out)
    print("clip", i, "ok")

N = len(clip_files)
total = N * CLIP - (N - 1) * XF

cmd = ["ffmpeg", "-y"]
for c in clip_files:
    cmd += ["-i", c]
cmd += ["-i", BGM]
bgm_idx = N

parts = []
prev, offset = "0:v", CLIP - XF
for i in range(1, N):
    out = f"x{i}" if i < N - 1 else "xf"
    tr = TRANSITIONS[i - 1]
    parts.append(f"[{prev}][{i}:v]xfade=transition={tr}:duration={XF}:offset={offset:.3f}[{out}]")
    prev = out
    offset += (CLIP - XF)
parts.append("[xf]vignette=PI/4.8,format=yuv420p[vout]")
parts.append(
    f"[{bgm_idx}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
    f"afade=t=in:st=0:d=1.0,afade=t=out:st={total-1.6:.3f}:d=1.6,"
    f"volume=0.85[aout]"
)

out_file = os.path.join(OUT_DIR, "04_one_day_at_kanoya.mp4")
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
