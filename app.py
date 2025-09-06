import os
import discord
from discord import app_commands
from dotenv import load_dotenv

from ui.flows import RegionSelectView
from services.profile_service import ProfileService

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
svc = ProfileService()

@tree.command(name="profile", description="プロフィール登録を開始します")
async def profile_cmd(itx: discord.Interaction):
    svc = ProfileService()
    if not svc.can_register(itx.user.id):
        await itx.response.send_message(
            "すでに登録済みです。/delete_profile で削除してから再登録してください。",
            ephemeral=True,
        )
        return

    # ★ ここを修正：origin_interaction=itx を渡す
    await itx.response.send_message(
        "まずは地域を選んでください。",
        view=RegionSelectView(itx.user.id, origin_interaction=itx),
        ephemeral=True,
    )


@tree.command(name="delete_profile", description="自分のプロフィール投稿を削除して再入力を可能にします")
async def delete_profile_cmd(itx: discord.Interaction):
    user_id = itx.user.id
    u = svc.get_user(user_id)  # User | None

    channel_id = u.last_channel_id if u else None
    message_id = u.last_message_id if u else None

    deleted = False
    if channel_id and message_id:
        channel = itx.client.get_channel(int(channel_id))
        if channel:
            try:
                msg = await channel.fetch_message(int(message_id))
                await msg.delete()
                deleted = True
            except Exception:
                pass  # 既に削除済み/権限不足/見つからない でも続行

    svc.soft_delete_profile(user_id)

    if deleted:
        await itx.response.send_message("削除しました。再入力できます。", ephemeral=True)
    else:
        await itx.response.send_message(
            "削除しました。再入力できます。\n（直近のプロフィール投稿メッセージは見つかりませんでした）",
            ephemeral=True,
        )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    await tree.sync()
    print("✅ Slash commands synced.")


bot.run(TOKEN)
