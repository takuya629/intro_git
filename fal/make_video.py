"""
AI動画編集のコツ シリーズ 動画生成スクリプト
9:16 縦型 15秒 ショート動画
"""
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import struct
import wave
import math

# ── 設定 ──────────────────────────────────────────
W, H = 1080, 1920          # 9:16
FPS = 30
DURATION = 15              # 秒
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT_DIR = "/home/user/intro_git/fal"

# シリーズカラー
BG      = "#533AFC"   # 紫（背景）
ACCENT  = "#FFD464"   # 黄（強調）
WHITE   = "#FFFFFF"

# シーン定義: (開始秒, 終了秒, メインテキスト, サブテキスト, 文字色)
SCENES = [
    (0,  4,  "AI動画編集のコツ\n第２回",          "",                     ACCENT),
    (4,  11, "効果音は\n入れすぎない",             "音が多いと\n内容が入らない",      WHITE),
    (11, 15, "明日から\n使えます。",               "",                     ACCENT),
]

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        return ImageFont.load_default()

def draw_frame(scene_idx, progress):
    """1フレームを描画して PIL Image を返す"""
    start, end, main_text, sub_text, color = SCENES[scene_idx]
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # 装飾: 上下に黄色のバー
    bar_h = 12
    draw.rectangle([0, 0, W, bar_h], fill=ACCENT)
    draw.rectangle([0, H - bar_h, W, H], fill=ACCENT)

    # メインテキスト
    font_main = load_font(130)
    lines = main_text.split("\n")
    total_h = len(lines) * 150
    y_start = H // 2 - total_h // 2 - (100 if sub_text else 0)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        # シャドウ
        draw.text((x+4, y_start + i*155 + 4), line, font=font_main, fill="#00000066")
        draw.text((x, y_start + i*155), line, font=font_main, fill=color)

    # サブテキスト
    if sub_text:
        font_sub = load_font(68)
        sub_lines = sub_text.split("\n")
        y_sub = y_start + len(lines) * 155 + 60
        for i, line in enumerate(sub_lines):
            bbox = draw.textbbox((0, 0), line, font=font_sub)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            draw.text((x+2, y_sub + i*85 + 2), line, font=font_sub, fill="#00000066")
            draw.text((x, y_sub + i*85), line, font=font_sub, fill=WHITE)

    # シリーズロゴ（右下）
    font_logo = load_font(36)
    logo = "AI動画編集のコツ"
    bbox = draw.textbbox((0, 0), logo, font=font_logo)
    tw = bbox[2] - bbox[0]
    draw.text((W - tw - 30, H - 70), logo, font=font_logo, fill=ACCENT)

    return img

def make_bgm(path, duration=15, sr=44100):
    """シンプルなBGMをローカル生成（サイン波ループ）"""
    # コード進行: Am -> F -> C -> G (各4拍)
    freqs = [220, 174.6, 261.6, 196.0]  # A3, F3, C4, G3
    n_samples = sr * duration
    data = []
    for i in range(n_samples):
        t = i / sr
        chord_idx = int(t / (duration / len(freqs))) % len(freqs)
        # 基音 + 倍音で厚みを出す
        f = freqs[chord_idx]
        v = (math.sin(2 * math.pi * f * t) * 0.4 +
             math.sin(2 * math.pi * f * 2 * t) * 0.2 +
             math.sin(2 * math.pi * f * 3 * t) * 0.1)
        # フェードイン/アウト
        fade = 1.0
        if i < sr: fade = i / sr
        elif i > n_samples - sr: fade = (n_samples - i) / sr
        val = int(v * fade * 8000)
        data.append(struct.pack('<h', max(-32768, min(32767, val))))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b''.join(data))
    print(f"BGM生成: {path}")

def render_video():
    frames_dir = f"{OUT_DIR}/frames"
    os.makedirs(frames_dir, exist_ok=True)
    bgm_path = f"{OUT_DIR}/bgm.wav"
    out_path  = f"{OUT_DIR}/ep02_sound.mp4"

    total_frames = FPS * DURATION
    print(f"フレーム生成中... ({total_frames}枚)")

    for f in range(total_frames):
        t = f / FPS
        # シーン判定
        scene_idx = 0
        for i, (s, e, *_) in enumerate(SCENES):
            if s <= t < e:
                scene_idx = i
                progress = (t - s) / (e - s)
                break
        else:
            scene_idx = len(SCENES) - 1
            progress = 1.0

        img = draw_frame(scene_idx, progress)
        img.save(f"{frames_dir}/frame_{f:05d}.png")

        if f % 60 == 0:
            print(f"  {f}/{total_frames} フレーム完了")

    print("BGM生成中...")
    make_bgm(bgm_path)

    print("動画エンコード中...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_dir}/frame_%05d.png",
        "-i", bgm_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpegエラー:", result.stderr[-500:])
    else:
        size = os.path.getsize(out_path) / 1024 / 1024
        print(f"\n完成: {out_path} ({size:.1f} MB)")

    # フレーム画像を削除
    import shutil
    shutil.rmtree(frames_dir)

if __name__ == "__main__":
    render_video()
