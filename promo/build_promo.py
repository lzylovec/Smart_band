"""Build promo PNGs for the Band-11 snake quickapp (design: Phosphor Grid).

Run: python3 promo/build_promo.py
Outputs: promo/repo-banner.png (1920x960), promo/poster-vertical.png (1024x1536),
         promo/feature-plate.png (1536x1024)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = Path("/Users/liuzhenyu_macbookpro/.codex/skills/canvas-design/canvas-fonts")

BLACK = (0, 0, 0)
GRID = (11, 11, 11)
GRID_STRONG = (17, 17, 17)
GREEN = (74, 222, 128)
GREEN_DIM = (34, 97, 63)
RED = (248, 113, 113)
WHITE = (255, 255, 255)
GRAY = (156, 163, 175)
GRAY_DARK = (75, 85, 99)
LINE = (31, 41, 55)
LINE_MID = (55, 65, 81)
INK = (229, 231, 235)

FONT_CJK = {
    "Semibold": ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),  # W6
    "Bold": ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),      # W6
    "Medium": ("/System/Library/Fonts/STHeiti Medium.ttc", 1),      # Heiti SC Medium
    "Regular": ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),    # W3
    "Light": ("/System/Library/Fonts/STHeiti Light.ttc", 1),
}


def cjk_font(size, style_want=("Semibold", "Medium", "Regular")):
    for s in style_want:
        path, idx = FONT_CJK[s]
        try:
            return ImageFont.truetype(path, size, index=idx), f"{s}:{Path(path).stem}"
        except OSError:
            continue
    raise RuntimeError("no CJK font")


def latin_font(size, name="WorkSans-Bold.ttf"):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def sp_text(d, xy, text, font, fill, spacing=0, anchor_left=True):
    """Draw text with manual letter-spacing; returns end x."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor="lm")
        x += d.textlength(ch, font=font) + spacing
    return x


def sp_text_r(d, xy, text, font, fill, spacing=0):
    """Right-aligned spaced text; xy = (right_x, center_y)."""
    x_r, y = xy
    w = sum(d.textlength(c, font=font) for c in text) + spacing * (len(text) - 1)
    sp_text(d, (x_r - w, y), text, font, fill, spacing)
    return x_r - w


def draw_grid(d, w, h, step=52, color=GRID):
    for x in range(step, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(step, h, step):
        d.line([(0, y), (w, y)], fill=color, width=1)


def rounded_shot(path, radius=26, stroke=LINE, sw=2):
    shot = Image.open(path).convert("RGBA")
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, shot.size[0] - 1, shot.size[1] - 1], radius=radius, fill=255
    )
    shot.putalpha(mask)
    if stroke:
        d = ImageDraw.Draw(shot)
        d.rounded_rectangle(
            [sw // 2, sw // 2, shot.size[0] - 1 - sw // 2, shot.size[1] - 1 - sw // 2],
            radius=radius, outline=stroke, width=sw,
        )
    return shot


def scale_shot(img, h):
    w = round(img.size[0] * h / img.size[1])
    return img.resize((w, h), Image.LANCZOS)


def find_color_pixel(img, pred, box=None):
    """Average position of matching pixels (RGB), optionally inside box (l,t,r,b)."""
    im = img.convert("RGB")
    w, h = im.size
    if box:
        box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
    else:
        box = (0, 0, w, h)
    px = im.load()
    xs = ys = n = 0
    for y in range(box[1], box[3], 2):
        for x in range(box[0], box[2], 2):
            r, g, b = px[x, y]
            if pred(r, g, b):
                xs += x; ys += y; n += 1
    if n == 0:
        return None
    return xs / n, ys / n, n


def snake_path_motif(d, x, y, cell=16, gap=4, n=6):
    """A small L-shaped run of green squares ending in a red dot."""
    for i in range(n - 2):
        d.rounded_rectangle(
            [x + i * (cell + gap), y, x + i * (cell + gap) + cell, y + cell],
            radius=4, fill=GREEN if i else GREEN_DIM,
        )
    x2 = x + (n - 2) * (cell + gap)
    d.rounded_rectangle([x2, y, x2 + cell, y + cell], radius=4, fill=GREEN_DIM)
    d.rounded_rectangle(
        [x2, y + cell + gap, x2 + cell, y + cell + gap + cell], radius=4, fill=GREEN_DIM
    )
    cx, cy = x2 + cell // 2, y + cell + gap + cell + gap + cell // 2
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=RED)


def banner():
    W, H = 1920, 960
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)
    draw_grid(d, W, H, step=60)

    shot = scale_shot(rounded_shot(ROOT / "shot-play.png"), 770)
    sx, sy = 170, (H - shot.size[1]) // 2
    img.paste(shot, (sx, sy), shot)

    f_lbl = latin_font(24)
    f_title, tname = cjk_font(176, ("Semibold",))
    f_sub, _ = cjk_font(46, ("Semibold",))
    f_tag, _ = cjk_font(30, ("Medium",))
    f_mono = latin_font(20)

    x0 = 620
    sp_text(d, (x0, 150), "SMART BAND 11 · VELA QUICKAPP", f_lbl, GRAY, spacing=5)
    f_cred, _ = cjk_font(24, ("Medium",))
    sp_text_r(d, (W - 120, 150), "作者 · 刘镇瑜", f_cred, GRAY, spacing=4)

    d.text((x0, 320), "贪吃蛇", font=f_title, fill=GREEN, anchor="lm")

    d.line([(x0, 445), (W - 120, 445)], fill=LINE, width=1)
    d.rectangle([x0, 441, x0 + 56, 449], fill=GREEN)

    d.text((x0, 510), "小米手环 11 · 快应用", font=f_sub, fill=WHITE, anchor="lm")
    d.ellipse([x0 + 2, 572, x0 + 18, 588], fill=RED)
    d.text((x0 + 34, 580), "免费开源 · AstroBox 一键侧载", font=f_tag, fill=GRAY, anchor="lm")

    snake_path_motif(d, x0, 650)

    sp_text(d, (x0, H - 60), "13 × 30 GRID · TICK 200 → 80 MS", f_mono, GRAY_DARK, spacing=3)
    d.text((W - 120, H - 60), "FIG. 00 — SNAKE / BAND11", font=f_mono, fill=GRAY_DARK, anchor="rm")

    img.save(ROOT / "repo-banner.png")
    print("banner ok", tname)


def poster():
    W, H = 1024, 1536
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)
    draw_grid(d, W, H, step=52)

    f_lbl = latin_font(22)
    f_title, _ = cjk_font(150, ("Semibold",))
    f_sub, _ = cjk_font(44, ("Semibold",))
    f_feat, _ = cjk_font(30, ("Medium",))
    f_mono = latin_font(20)

    sp_text(d, (72, 96), "OPEN SOURCE", f_lbl, GRAY, spacing=5)
    f_cred, _ = cjk_font(24, ("Medium",))
    sp_text_r(d, (W - 112, 96), "作者 · 刘镇瑜", f_cred, GRAY, spacing=4)
    d.ellipse([W - 84, 86, W - 66, 104], fill=RED)

    d.text((72, 210), "贪吃蛇", font=f_title, fill=GREEN, anchor="lm")
    d.rectangle([72, 310, 192, 318], fill=GREEN)
    d.text((72, 380), "小米手环 11 · 快应用", font=f_sub, fill=WHITE, anchor="lm")

    shot = scale_shot(rounded_shot(ROOT / "shot-play.png"), 800)
    sx, sy = (W - shot.size[0]) // 2, 480
    # stadium outline motif hugging the screen (kept clear of its corners)
    pad_x, pad_y = 50, 40
    d.rounded_rectangle(
        [sx - pad_x, sy - pad_y, sx + shot.size[0] + pad_x, sy + shot.size[1] + pad_y],
        radius=(shot.size[1] + pad_y * 2) // 2, outline=LINE, width=2,
    )
    img.paste(shot, (sx, sy), shot)

    feats = ["滑动操控", "最高分记录", "免费开源"]
    gap = 56
    widths = [d.textlength(t, font=f_feat) for t in feats]
    total = sum(widths) + gap * (len(feats) - 1)
    fx = (W - total) / 2
    fy = 1370
    for i, t in enumerate(feats):
        d.text((fx, fy), t, font=f_feat, fill=GRAY, anchor="lm")
        fx += widths[i]
        if i < len(feats) - 1:
            mx = fx + gap / 2
            d.rectangle([mx - 6, fy - 6, mx + 6, fy + 6], fill=GREEN_DIM)
            fx += gap

    d.line([(72, H - 96), (W - 72, H - 96)], fill=LINE, width=1)
    sp_text(d, (72, H - 56), "FIG. 01 — SNAKE FOR BAND 11", f_mono, GRAY_DARK, spacing=3)
    d.text((W - 72, H - 56), "ASTROBOX SIDELOAD", font=f_mono, fill=GRAY_DARK, anchor="rm")

    img.save(ROOT / "poster-vertical.png")
    print("poster ok")


def plate():
    W, H = 1536, 1024
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)
    draw_grid(d, W, H, step=48)

    f_head, _ = cjk_font(40, ("Semibold",))
    f_cap, _ = cjk_font(24, ("Medium",))
    f_lbl, _ = cjk_font(26, ("Medium",))
    f_mono = latin_font(20)
    f_mono_s = latin_font(17)

    d.text((80, 78), "贪吃蛇 · 小米手环 11", font=f_head, fill=WHITE, anchor="lm")
    sp_text(d, (80, 130), "FIG. 02 — GAME STATES / 212 × 520 TRACK SCREEN", f_mono, GRAY, spacing=3)
    f_cred, _ = cjk_font(24, ("Medium",))
    sp_text_r(d, (W - 80, 90), "作者 · 刘镇瑜", f_cred, GRAY, spacing=4)

    shot_h = 620
    a = scale_shot(rounded_shot(ROOT / "shot-start.png"), shot_h)
    b = scale_shot(rounded_shot(ROOT / "shot-play.png"), shot_h)
    ay = by = 230
    ax, bx = 160, 520
    img.paste(a, (ax, ay), a)
    img.paste(b, (bx, by), b)

    cap_y = ay + shot_h + 40
    d.text((ax + a.size[0] // 2, cap_y), "① 开始界面", font=f_cap, fill=GRAY, anchor="mm")
    d.text((bx + b.size[0] // 2, cap_y), "② 游玩中", font=f_cap, fill=GRAY, anchor="mm")

    # annotation targets inside play shot
    play = Image.open(ROOT / "shot-play.png").convert("RGB")
    sc = shot_h / play.size[1]
    green = find_color_pixel(play, lambda r, g, bl: g > 180 and r < 160 and bl < 170)
    red = find_color_pixel(play, lambda r, g, bl: r > 200 and g < 150 and bl < 150)

    tx = bx + play.size[0] * sc
    ann = [
        (300, "跑道屏 212 × 520", (bx + play.size[0] * sc * 0.5, ay + 8)),
        (470, "HUD · 得分 / 最高", (bx + play.size[0] * sc * 0.5, ay + 30 * sc)),
    ]
    if green:
        ann.append((640, "蛇身 #4ADE80",
                    (bx + green[0] * sc, ay + green[1] * sc)))
    if red:
        ann.append((810, "食物 +10 分",
                    (bx + red[0] * sc, ay + red[1] * sc)))

    lx = 1040
    for ly, label, (px_, py_) in ann:
        d.line([(lx, ly), (lx - 40, ly), (px_ + 10, py_)], fill=LINE_MID, width=1)
        d.ellipse([px_ - 4, py_ - 4, px_ + 4, py_ + 4], fill=RED if "食物" in label else GREEN)
        d.text((lx + 16, ly), label, font=f_lbl, fill=INK, anchor="lm")

    sp_text(d, (80, H - 64), "13 × 30 GRID · TICK 200 → 80 MS · +10 / FOOD", f_mono_s, GRAY_DARK, spacing=3)
    d.ellipse([W - 96, H - 74, W - 78, H - 56], fill=RED)

    img.save(ROOT / "feature-plate.png")
    print("plate ok", "green" if green else "no-green", "red" if red else "no-red")


if __name__ == "__main__":
    banner()
    poster()
    plate()
