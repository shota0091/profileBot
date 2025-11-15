from PIL import Image, ImageDraw, ImageFont
import os, textwrap

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
ASSETS_DIR = os.path.realpath(ASSETS_DIR)

TEMPLATE_PATH = os.path.join(ASSETS_DIR, "template.jpeg")

# Mac のヒラギノフォント
JP_FONT_PATH = os.path.join(ASSETS_DIR, "ヒラギノ角ゴシック W3.ttc")

def get_font(size=28):
    return ImageFont.truetype(JP_FONT_PATH, size)

def draw_text_box(draw, xy, box_width, box_height, text, font, fill="black", align="left", valign="top"):
    """
    枠内に収めるテキスト描画
    - ピクセル幅で折り返し
    - 縦方向は枠を超える前に最後の行を「…」にして省略
    """
    if not font:
        font = get_font(24)

    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 2  # ちょっと余白
    max_lines = box_height // line_height

    # ===== 折り返し処理 =====
    lines = []
    for raw_line in text.split("\n"):
        line = ""
        for ch in raw_line:
            test_line = line + ch
            if draw.textlength(test_line, font=font) <= box_width:
                line = test_line
            else:
                lines.append(line)
                line = ch
        if line:
            lines.append(line)

    # ===== 縦位置 =====
    if valign == "middle":
        total_height = min(len(lines), max_lines) * line_height
        y = xy[1] + (box_height - total_height)//2
    else:
        y = xy[1]

    # ===== 描画 =====
    for i, line in enumerate(lines):
        if i >= max_lines:
            break

        # 最終行が残り切れない場合は「…」
        if i == max_lines - 1 and i < len(lines) - 1:
            while draw.textlength(line + "…", font=font) > box_width and line:
                line = line[:-1]
            line += "…"

        w = draw.textlength(line, font=font)
        if align == "center":
            x = xy[0] + (box_width - w)//2
        else:
            x = xy[0]

        draw.text((x, y), line, font=font, fill=fill)
        y += line_height

def build_profile_image(
    name, region_or_pref, age, birth, occupation,
    hobby, skill, like_type, comment,
    out_path,sex
):
    img = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)
    font = get_font(26)

# ==== 上部（名前）====
    draw_text_box(draw, (130, 172), 320, 40, name + " " + sex, font, valign="middle")

# ==== プロフィールテーブル ====
    draw_text_box(draw, (120, 240), 200, 35, region_or_pref, get_font(16), valign="middle")  # 地域
    draw_text_box(draw, (378, 240), 120, 35, age, get_font(16), valign="middle")             # 年齢

    draw_text_box(draw, (120, 285), 200, 70, birth, get_font(16), valign="middle")           # 誕生日
    draw_text_box(draw, (378, 285), 120, 70, occupation, get_font(16), valign="middle")      # 職業

# ==== 趣味・特技・好きなタイプ ====
    draw_text_box(draw, (35, 455), 150, 140, hobby, get_font(16), align="center", valign="top")
    draw_text_box(draw, (230, 455), 150, 140, skill, get_font(16), align="center", valign="top")
    draw_text_box(draw, (430, 455), 150, 140, like_type, get_font(16), align="center", valign="top")

# ==== ひとこと ====
    draw_text_box(draw, (230, 690), 450, 110, comment, get_font(16), align="left", valign="top")


    img.save(out_path, "PNG")
    return out_path
