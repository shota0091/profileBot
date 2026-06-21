# ui/flows.py ーーー 年齢/誕生日 →（ボタン）→ 詳細モーダル
import re
import logging
import discord
from discord.ui import View, Select, Modal, TextInput, Button
from typing import Optional
from config.constants import REGIONS, GENDERS
from services.profile_service import ProfileService
from views.profile_view import build_profile_embed
from discord import File
import os
from views.profile_image import build_profile_image

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
                await itx.response.send_message("年齢は18〜99の範囲で入力してください。", ephemeral=True); return

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
        except Exception as e:
            logging.warning("origin.edit_original_response failed: %s", e)

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
    def __init__(self, region: str | None, prefecture: str | None, gender: str,
                 age: int | None, year: int | None, month: int | None, day: int | None,
                 origin_interaction: discord.Interaction,
                 detail_interaction: Optional[discord.Interaction] = None):

        super().__init__(timeout=180)
        self.region, self.prefecture, self.gender = region, prefecture, gender
        self.age, self.year, self.month, self.day = age, year, month, day
        self.origin = origin_interaction
        self.detail_itx = detail_interaction

        self.occupation = TextInput(label="職業", required=False, max_length=100)

        self.hobby = TextInput(
            label="趣味",
            placeholder="空白で改行できます。最大５つまで。例) 筋トレ ゲーム",
            required=False, max_length=255
        )

        self.skill = TextInput(
            label="特技",
            placeholder="空白で改行できます。最大５つまで。例) 料理 プログラミング",
            required=False, max_length=255
        )

        self.like_type = TextInput(
            label="好きなタイプ",
            placeholder="空白で改行できます。最大５つまで。例) よく食べる人 優しい人",
            required=False, max_length=255
        )

        self.comment = TextInput(label="ひとこと", required=False, max_length=255)

        for x in (self.occupation, self.hobby, self.skill, self.like_type, self.comment):
            self.add_item(x)

    @staticmethod
    def count_check(name: str, value: str):
        """空白区切りで最大5つまで。それ以上ならエラーを返す"""
        if not value:
            return None

        items = value.split()
        if len(items) > 5:
            return f"{name}は最大5つまでです。（現在 {len(items)} 個）"

        return None

    async def on_submit(self, itx: discord.Interaction):
        # Discord は 3秒以内に応答がないとタイムアウトするため最初に defer する
        await itx.response.defer(ephemeral=True)

        # ===== 空白区切りチェック =====
        errors = []

        err = self.count_check("趣味", self.hobby.value)
        if err: errors.append(err)

        err = self.count_check("特技", self.skill.value)
        if err: errors.append(err)

        err = self.count_check("好きなタイプ", self.like_type.value)
        if err: errors.append(err)

        if errors:
            return await itx.followup.send("\n".join(errors), ephemeral=True)

        # ===== ここから保存処理 =====
        svc = ProfileService()
        if not svc.can_register(itx.user.id):
            await itx.followup.send(
                "すでに登録済みです。/delete_profile で削除してから再登録してください。",
                ephemeral=True
            )
            return

        name = (itx.user.display_name or itx.user.name)[:50]

        svc.register(itx.user.id, name, self.age, None, self.month, self.day)

        def nz(s: str | None) -> str:
            return (s or "").strip() or "未入力"

        def nc(s: str | None) -> str:
            return (s or "").strip() or "よろしくお願いします"

        def ns(s: str) -> str:
            if s == "男性":
                return "♂"
            elif s == "女性":
                return "♀"
            return ""

        prefecture_display = self.prefecture or self.region or "未入力"

        birth_str = "未入力"
        if self.month and self.day:
            birth_str = f"{self.month}月{self.day}日"

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(BASE_DIR, "templates", f"{itx.user.id}_profile.png")

        img_path = build_profile_image(
            name=name,
            region_or_pref=prefecture_display,
            age=str(self.age or "未入力"),
            birth=birth_str,
            occupation=nz(self.occupation.value),
            hobby=nz(self.hobby.value),
            skill=nz(self.skill.value),
            like_type=nz(self.like_type.value),
            comment=nc(self.comment.value),
            out_path=out_path,
            sex=ns(self.gender)
        )

        file = File(out_path)
        msg = await itx.followup.send(file=file, wait=True)
        await itx.followup.send("登録しました！", ephemeral=True)


        # ===============================
        # ★ プロフィール登録者にロール付与
        # ===============================
        ROLE_NAME = "プロフィール登録済み"  # ←好きなロール名に変えてOK

        guild = itx.guild
        member = itx.user
        role = discord.utils.get(guild.roles, name=ROLE_NAME)

        if role:
            try:
                await member.add_roles(role)
                logging.info("ロール付与: %s → %s", member, ROLE_NAME)
            except Exception as e:
                logging.warning("ロール付与失敗: %s", e)
        else:
            logging.warning("ロールが見つかりません: %s", ROLE_NAME)

        try:
            svc.save_message_location(itx.user.id, msg.id, itx.channel_id)
        except Exception as e:
            logging.error("save_message_location failed: %s", e)

        try:
            await self.origin.edit_original_response(
                content="入力ありがとうございました。登録が完了しました。",
                view=None
            )
        except Exception as e:
            logging.warning("origin.edit_original_response failed: %s", e)

        if self.detail_itx is not None:
            try:
                await self.detail_itx.edit_original_response(
                    content="詳細入力は完了しました。",
                    view=None
                )
            except Exception as e:
                logging.warning("detail_itx.edit_original_response failed: %s", e)

