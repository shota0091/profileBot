# views/profile_view.py
import discord

def build_profile_embed(
    *,
    name: str,
    prefecture: str,                 # 表示する文字列（都道府県 or 地域 or 未入力）
    gender: str | None = None,
    age: int | None = None,
    birth_year: int | None = None,
    birth_month: int | None = None,
    birth_day: int | None = None,
    occupation: str | None = None,
    hobby: str | None = None,
    like_type: str | None = None,
    skill: str | None = None,
    comment: str | None = None,
    prefecture_label: str = "都道府県",   # ★ 追加：フィールド名を動的に
) -> discord.Embed:
    age_str = str(age) if age is not None else "秘密"

    if birth_month and birth_day:
        birthday_str = f"{birth_month}月{birth_day}日"
    elif birth_month:
        birthday_str = f"{birth_month}月"
    elif birth_day:
        birthday_str = f"{birth_day}日"
    else:
        birthday_str = "未入力"

    def nz(s: str | None) -> str:
        return (s or "").strip() or "未入力"

    embed = discord.Embed(color=0x2B2D31, title="✅ あなたのプロフィール")
    embed.add_field(name="👤 名前", value=name, inline=False)
    embed.add_field(name=f"🗺️ {prefecture_label}", value=prefecture or "未入力", inline=False)  # ★
    embed.add_field(name="🎂 年齢", value=age_str, inline=False)
    embed.add_field(name="📅 誕生日", value=birthday_str, inline=False)
    embed.add_field(name="💼 職業", value=nz(occupation), inline=False)
    embed.add_field(name="🎯 趣味", value=nz(hobby), inline=False)
    embed.add_field(name="💘 好きなタイプ", value=nz(like_type), inline=False)
    embed.add_field(name="✨ 特技", value=nz(skill), inline=False)
    embed.add_field(name="💬 ひとこと", value=nz(comment), inline=False)

    embed.set_footer(text="再編集はできません。変更したい場合は /delete_profile で削除後に登録し直してください。")
    return embed
