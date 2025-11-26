from PIL import Image, ImageDraw, ImageFont
import os
import re

# =========================
# パス設定
# =========================
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
ASSETS_DIR = os.path.realpath(ASSETS_DIR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(BASE_DIR, "assets/template.jpeg")

# Mac のヒラギノフォント（assets 内に置いた W3）
JP_FONT_PATH = os.path.join(ASSETS_DIR, "ヒラギノ角ゴシック W3.ttc")


# =========================
# フォント取得
# =========================
def get_font(size: int):
    return ImageFont.truetype(JP_FONT_PATH, size)


# =========================
# スペース改行変換
# =========================
def format_multiline(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[ 　]+", "\n", text.strip())


# =========================
# 自然な折り返し（文字幅ベース）
# =========================
def _wrap_text(text: str, font: ImageFont.FreeTypeFont, box_width: int):
    lines = []

    for raw in text.split("\n"):
        current = ""
        for ch in raw:
            test = current + ch
            w = font.getbbox(test)[2] - font.getbbox(test)[0]

            if w <= box_width:
                current = test
            else:
                lines.append(current)
                current = ch

        if current:
            lines.append(current)

    return lines


# =========================
# 汎用描画関数（折り返し + 「…」省略 + 自動縮小）
# =========================
def draw_text_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    box_width: int,
    box_height: int,
    text: str,
    font: ImageFont.FreeTypeFont | None = None,
    fill: str = "black",
    align: str = "left",
    valign: str = "top",
    auto_shrink: bool = False,
    min_font_size: int = 10,
):
    if not text:
        return

    if font is None:
        font = get_font(24)

    # ===== 自動縮小 =====
    if auto_shrink:
        size = font.size
        while size >= min_font_size:
            test_font = get_font(size)
            ascent, descent = test_font.getmetrics()
            line_h = ascent + descent + 4
            max_lines = max(1, box_height // line_h)

            wrapped = _wrap_text(text, test_font, box_width)

            if len(wrapped) <= max_lines:
                font = test_font
                break

            size -= 1

    # ===== 行分割 =====
    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 4
    max_lines = max(1, box_height // line_height)

    wrapped = _wrap_text(text, font, box_width)

    # ===== はみ出す場合「…」 =====
    if len(wrapped) > max_lines:
        display = wrapped[:max_lines]
        last = display[-1]

        while font.getbbox(last + "…")[2] - font.getbbox(last + "…")[0] > box_width and last:
            last = last[:-1]

        display[-1] = last + "…"
    else:
        display = wrapped

    # ===== 縦位置 =====
    total_h = len(display) * line_height
    y = xy[1] if valign == "top" else xy[1] + (box_height - total_h) // 2

    # ===== 描画 =====
    for line in display:
        w = font.getbbox(line)[2] - font.getbbox(line)[0]

        if align == "left":
            x = xy[0]
        else:
            x = xy[0] + (box_width - w) // 2

        draw.text((x, y), line, font=font, fill=fill)
        y += line_height


# =========================
# プロフィール画像生成
# =========================
def build_profile_image(
    name: str,
    region_or_pref: str,
    age: str,
    birth: str,
    occupation: str,
    hobby: str,
    skill: str,
    like_type: str,
    comment: str,
    out_path: str,
    sex: str = "",
):
    img = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ---- フォント ----
    font_name = get_font(28)
    font_main = get_font(18)
    font_box = get_font(18)
    font_comment = get_font(18)

    # ======================
    # 名前（大枠）
    # ======================
    draw_text_box(
        draw=draw,
        xy=(130, 172),
        box_width=500,
        box_height=40,
        text=name + (" " + sex if sex else ""),
        font=font_name,
        fill="black",
        align="left",
        valign="middle",
        auto_shrink=True,
        min_font_size=16,
    )

    # ======================
    # 地域 / 年齢 / 誕生日 / 職業
    # ======================
    draw_text_box(
        draw=draw,
        xy=(120, 240),
        box_width=200,
        box_height=35,
        text=region_or_pref,
        font=font_main,
        fill="black",
        align="left",
        valign="middle",
        auto_shrink=True,
        min_font_size=12,
    )

    draw_text_box(
        draw=draw,
        xy=(378, 240),
        box_width=200,
        box_height=35,
        text=age,
        font=font_main,
        fill="black",
        align="left",
        valign="middle",
        auto_shrink=True,
        min_font_size=12,
    )

    draw_text_box(
        draw=draw,
        xy=(120, 285),
        box_width=200,
        box_height=70,
        text=birth,
        font=font_main,
        fill="black",
        align="left",
        valign="middle",
        auto_shrink=True,
        min_font_size=12,
    )

    draw_text_box(
        draw=draw,
        xy=(378, 285),
        box_width=150,
        box_height=70,
        text=occupation,
        font=font_main,
        fill="black",
        align="left",
        valign="middle",
        auto_shrink=True,
        min_font_size=12,
    )

    # ======================
    # 趣味・特技・好きなタイプ
    # ======================

    draw_text_box(
        draw=draw,
        xy=(35, 405),
        box_width=150,
        box_height=200,
        text=format_multiline(hobby),
        font=font_box,
        fill="black",
        align="center",
        valign="middle",
        auto_shrink=True,
        min_font_size=10,
    )

    draw_text_box(
        draw=draw,
        xy=(230, 405),
        box_width=150,
        box_height=200,
        text=format_multiline(skill),
        font=font_box,
        fill="black",
        align="center",
        valign="middle",
        auto_shrink=True,
        min_font_size=10,
    )

    draw_text_box(
        draw=draw,
        xy=(430, 405),
        box_width=150,
        box_height=200,
        text=format_multiline(like_type),
        font=font_box,
        fill="black",
        align="center",
        valign="middle",
        auto_shrink=True,
        min_font_size=10,
    )

    # ======================
    # ひとこと欄（大枠）
    # ======================
    draw_text_box(
        draw=draw,
        xy=(40, 680),
        box_width=520,
        box_height=170,
        text=format_multiline(comment),
        font=font_comment,
        fill="black",
        align="left",
        valign="top",
        auto_shrink=True,
        min_font_size=12,
    )

    # 保存
    img.save(out_path, "PNG")
    return out_path
