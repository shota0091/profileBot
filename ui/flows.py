# ui/flows.py ーーー 年齢/誕生日 →（ボタン）→ 詳細モーダル
import re
import discord
from discord.ui import View, Select, Modal, TextInput, Button
from typing import Optional
from config.constants import REGIONS, GENDERS
from services.profile_service import ProfileService
from views.profile_view import build_profile_embed

# ========= 誕生日パーサ =========
_VALID_DAY_31 = {1, 3, 5, 7, 8, 10, 12}
_VALID_DAY_30 = {4, 6, 9, 11}

def _parse_birthday(text: str):
    """'7-11' / '0711' / '07月11日' / '711' を (month, day) に。無効や空は (None, None)。"""
    s = (text or "").strip()
    if not s:
        return (None, None)

    parts = [p for p in re.split(r"\D+", s) if p]
    m = d = None

    if len(parts) >= 2:
        m, d = int(parts[0]), int(parts[1])
    else:
        digits = re.sub(r"\D", "", s)
        if len(digits) == 3:     # 711
            m, d = int(digits[0]), int(digits[1:])
        elif len(digits) == 4:   # 0711
            m, d = int(digits[:2]), int(digits[2:])
        else:
            return (None, None)

    if not (1 <= m <= 12):
        return (None, None)
    if m in _VALID_DAY_31 and 1 <= d <= 31:
        return (m, d)
    if m in _VALID_DAY_30 and 1 <= d <= 30:
        return (m, d)
    if m == 2 and 1 <= d <= 28:  # 2/29 は無効
        return (m, d)
    return (None, None)


# ===== 1：地域 =====
class RegionSelectView(View):
    def __init__(self, author_id: int, origin_interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.origin = origin_interaction

        region_labels = list(REGIONS.keys())
        region_labels.append("未入力")

        sel = Select(
            placeholder="地域を選択（未入力可）",
            options=[discord.SelectOption(label=r) for r in region_labels],
            min_values=1, max_values=1,
        )
        sel.callback = self.on_region
        self.add_item(sel)

    async def on_region(self, itx: discord.Interaction):
        if itx.user.id != self.author_id:
            await itx.response.send_message("発行者のみ操作できます。", ephemeral=True); return

        picked = itx.data["values"][0]
        region = None if picked == "未入力" else picked

        if region is None:
            # ★ 地域が未入力なら、都道府県ステップはスキップして性別へ
            await itx.response.edit_message(
                content=f"地域: **未入力** → 次に **性別** を選んでください。",
                view=GenderSelectView(self.author_id, self.origin, region, None),
            )
        else:
            # 通常どおり都道府県へ
            await itx.response.edit_message(
                content=f"地域: **{region}** → 次に **都道府県** を選んでください（未入力可）。",
                view=PrefSelectView(self.author_id, self.origin, region),
            )


# ===== 2：都道府県 =====
class PrefSelectView(View):
    def __init__(self, author_id: int, origin: discord.Interaction, region: str | None):
        super().__init__(timeout=180)
        self.author_id, self.origin, self.region = author_id, origin, region

        if region is None:
            options = [discord.SelectOption(label="未入力")]
        else:
            options = [discord.SelectOption(label=p) for p in REGIONS[region]]
            options.append(discord.SelectOption(label="未入力"))  # ★ 常に未入力を用意

        sel = Select(
            placeholder="都道府県を選択（未入力可）",
            options=options,
            min_values=1, max_values=1,
        )
        sel.callback = self.on_pref
        self.add_item(sel)

    async def on_pref(self, itx: discord.Interaction):
        if itx.user.id != self.author_id:
            await itx.response.send_message("発行者のみ操作できます。", ephemeral=True); return
        picked = itx.data["values"][0]
        prefecture = None if picked == "未入力" else picked  # ★ Noneで保持

        # 次は性別
        picked_disp = picked
        await itx.response.edit_message(
            content=f"都道府県: **{picked_disp}** → 次に **性別** を選んでください。",
            view=GenderSelectView(self.author_id, self.origin, self.region, prefecture),  # ★ regionも渡す
        )


# ===== 3：性別 =====
class GenderSelectView(View):
    def __init__(self, author_id: int, origin: discord.Interaction, region: str | None, prefecture: str | None):
        super().__init__(timeout=180)
        self.author_id, self.origin = author_id, origin
        self.region, self.prefecture = region, prefecture

        sel = Select(
            placeholder="性別を選択",
            options=[discord.SelectOption(label=g) for g in GENDERS],
            min_values=1, max_values=1,
        )
        sel.callback = self.on_gender
        self.add_item(sel)

    async def on_gender(self, itx: discord.Interaction):
        if itx.user.id != self.author_id:
            await itx.response.send_message("発行者のみ操作できます。", ephemeral=True); return
        gender = itx.data["values"][0]
        await itx.response.send_modal(
            AgeBirthdayModal(
                region=self.region,
                prefecture=self.prefecture,
                gender=gender,
                origin_interaction=self.origin
            )
        )


# ===== 4：モーダル1（年齢・誕生日） =====
class AgeBirthdayModal(Modal, title="年齢・誕生日の入力（任意）"):
    def __init__(self, region: str | None, prefecture: str | None, gender: str, origin_interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.region, self.prefecture, self.gender = region, prefecture, gender
        self.origin = origin_interaction

        self.age = TextInput(label="年齢", placeholder="例) 20（2桁・18〜99、未入力なら秘密）", required=False, max_length=2)
        self.birthday = TextInput(label="誕生日", placeholder="例）7月11日 （未入力OK）", required=False, max_length=10)
        self.add_item(self.age)
        self.add_item(self.birthday)

    async def on_submit(self, itx: discord.Interaction):
        # （年齢/誕生日のバリデーションは今のまま）
        age_val: int | None = None
        age_txt = (self.age.value or "").strip()
        if age_txt != "":
            if not age_txt.isdigit():
                await itx.response.send_message("年齢は数字のみで入力してください。", ephemeral=True); return
            if len(age_txt) != 2:
                await itx.response.send_message("年齢は2桁で入力してください（例: 18〜99）。", ephemeral=True); return
            age_val = int(age_txt)
            if not (18 <= age_val <= 99):
                await itx.response.send_message("年齢は18〜70の範囲で入力してください。", ephemeral=True); return

        b_month = b_day = None
        b_raw = (self.birthday.value or "").strip()
        if b_raw:
            b_month, b_day = _parse_birthday(b_raw)
            if b_month is None or b_day is None:
                await itx.response.send_message(
                    "誕生日が不正です（例: 7月11日）。6/31や2/29は無効です。",
                    ephemeral=True
                ); return

        # 性別セレクトのエフェメラルを畳む
        try:
            await self.origin.edit_original_response(content="年齢・誕生日の入力を受け付けました。", view=None)
        except Exception:
            pass

        # 詳細ボタン（region/prefectureを引き継ぐ）
        view = DetailButtonView(
            author_id=itx.user.id,
            origin=self.origin,
            region=self.region,
            prefecture=self.prefecture,
            gender=self.gender,
            age=age_val,
            month=b_month,
            day=b_day,
            trigger_itx=itx,
        )
        await itx.response.send_message(
            "次に **職業・趣味・特技・好きなタイプ・ひとこと** を入力してください👇",
            ephemeral=True,
            view=view
        )

# ===== 5：年齢モーダルの後に押すボタン（→ 詳細モーダルを開く） =====
class DetailButtonView(View):
    def __init__(self, author_id:int, origin:discord.Interaction,
                 region:str|None, prefecture:str|None, gender:str, age:int|None,
                 month:int|None, day:int|None, trigger_itx: discord.Interaction):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.origin = origin
        self.region = region
        self.prefecture = prefecture
        self.gender = gender
        self.age = age
        self.month = month
        self.day = day
        self.trigger_itx = trigger_itx

        btn = Button(label="詳細を入力する", style=discord.ButtonStyle.primary)
        btn.callback = self.open_modal
        self.add_item(btn)

    async def open_modal(self, itx: discord.Interaction):
        if itx.user.id != self.author_id:
            await itx.response.send_message("発行者のみ操作できます。", ephemeral=True); return
        await itx.response.send_modal(
            FinalModal(
                region=self.region,
                prefecture=self.prefecture,
                gender=self.gender,
                age=self.age,
                year=None,
                month=self.month,
                day=self.day,
                origin_interaction=self.origin,
                detail_interaction=self.trigger_itx,
            )
        )

# ===== 6：モーダル2（詳細：職業/趣味/好き/好きなタイプ/嫌い） =====
class FinalModal(Modal, title="プロフィール詳細入力"):
    def __init__(self, region:str|None, prefecture:str|None, gender:str,
                 age:int|None, year:int|None, month:int|None, day:int|None,
                 origin_interaction: discord.Interaction,
                 detail_interaction: Optional[discord.Interaction] = None):
        super().__init__(timeout=180)
        self.region, self.prefecture, self.gender = region, prefecture, gender
        self.age, self.year, self.month, self.day = age, year, month, day
        self.origin = origin_interaction
        self.detail_itx = detail_interaction

        self.occupation = TextInput(label="職業", required=False, max_length=100)
        self.hobby      = TextInput(label="趣味", required=False, max_length=255)
        self.skill      = TextInput(label="特技", required=False, max_length=255)
        self.like_type  = TextInput(label="好きなタイプ", required=False, max_length=255)
        self.comment    = TextInput(label="ひとこと", required=False, max_length=255)
        for x in (self.occupation, self.hobby, self.skill, self.like_type, self.comment):
            self.add_item(x)

    async def on_submit(self, itx: discord.Interaction):
        svc = ProfileService()
        if not svc.can_register(itx.user.id):
            await itx.response.send_message("すでに登録済みです。/delete_profile で削除してから再登録してください。", ephemeral=True); return

        name = (itx.user.display_name or itx.user.name)[:50]

        # DB保存（年は常に None）
        svc.register(itx.user.id, name, self.age, None, self.month, self.day)

        def nz(s: str | None) -> str:
            return (s or "").strip() or "未入力"

        # ★ 県が未入力なら地域を表示用に利用。両方Noneなら「未入力」
        prefecture_display = self.prefecture or self.region or "未入力"

        if self.prefecture:                           # 県がある → そのまま都道府県
            prefecture_display = self.prefecture
            prefecture_label = "都道府県"
        elif self.region:                              # 県なし・地域あり → 地域ラベルで表示
            prefecture_display = self.region
            prefecture_label = "地域"
        else:                                          # どちらも未入力
            prefecture_display = "未入力"
            prefecture_label = "都道府県"

        embed = build_profile_embed(
            name=name,
            prefecture=prefecture_display,
            gender=self.gender,
            age=self.age,
            birth_year=None,
            birth_month=self.month,
            birth_day=self.day,
            occupation=nz(self.occupation.value),
            hobby=nz(self.hobby.value),
            like_type=nz(self.like_type.value),
            skill=nz(self.skill.value),
            comment=nz(self.comment.value),
            prefecture_label=prefecture_label,   # ★ ラベルを渡す
        )
        msg = await itx.channel.send(embed=embed)

        try:
            svc.save_message_location(itx.user.id, msg.id, itx.channel.id)
        except Exception:
            pass

        try:
            await self.origin.edit_original_response(content="入力ありがとうございました。登録が完了しました。", view=None)
        except Exception:
            pass

        if self.detail_itx is not None:
            try:
                await self.detail_itx.edit_original_response(content="詳細入力は完了しました。", view=None)
            except Exception:
                pass

        await itx.response.send_message("登録しました！", ephemeral=True)