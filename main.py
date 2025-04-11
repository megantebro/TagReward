import discord
from discord import app_commands
import databasemanager
from reward import RewardType
from discord.ext import tasks
import json
import os

def init_config():
    # config.json が存在しない場合
    CONFIG_FILE = "config.json"
    if not os.path.exists(CONFIG_FILE):
        print("config.json が見つかりません。新しく作成します。")
        default_config = {"TOKEN": ""}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    # 存在する場合 → 読み込んで返す
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            print("config.json の形式が不正です。新しく作成しなおします。")
            config = {"TOKEN": ""}
            with open(CONFIG_FILE, "w", encoding="utf-8") as wf:
                json.dump(config, wf, indent=4)

    # "TOKEN" キーがない場合 → 追加して上書き保存
    if "TOKEN" not in config:
        print('"TOKEN" キーが見つかりません。追加します。')
        config["TOKEN"] = ""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    return config

intents = discord.Intents.default()
intents.presences = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
TOKEN = init_config()["TOKEN"]

db_manager = None
@client.event
async def on_ready():
    global db_manager
    print("ready")
    await tree.sync()
    db_manager = await databasemanager.DatabaseManager.get_instance()
    check_user_status_loop.start()


@tree.command(name="ping",description="ボットが動いているか確認できます")
async def ping(interaction : discord.Interaction):
    await interaction.response.send_message("ping")


@tree.command(name="check_reward_users",description="報酬条件を満たしているユーザーを表示します")
async def check_reward_users(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild_id = interaction.guild.id
    guild = interaction.guild

    reward_keywords = await db_manager.get_keywords_by_guild(guild_id=guild_id)

    if not reward_keywords:
        await interaction.followup.send("先に/add_reward_keywardを実行して下さい")
        return
    
    matched_user_ids = get_matched_users(members=guild.members,keywords=reward_keywords)
    
    if not matched_user_ids:
        await interaction.followup.send("該当者はいませんでした",ephemeral=True)
        return
    response = "以下に条件を満たしているユーザーの一覧を表示します\n"
    for user_id in matched_user_ids:
        response += f"<@{ user_id }>"

    await interaction.followup.send(response,ephemeral=True)

@tree.command(name="set_reward_keyward", description="ユーザーが報酬を受け取るために自己紹介に書く文言を指定します")
async def set_keyward(
    interaction: discord.Interaction,
    keyward: str,
    reward_type: RewardType,
    reward_value: int = None,
    reward_roll: discord.Role = None
):
    # --- 入力チェック ---
    if not keyward:
        await interaction.response.send_message("タグが入力されていません。プロフィールに書いてもらいたい文言を入力してください。", ephemeral=True)
        return

    if reward_type is None:
        await interaction.response.send_message("報酬タイプを選んでください。", ephemeral=True)
        return

    if reward_type == RewardType.ROLE:
        if not reward_roll:
            await interaction.response.send_message("ロールを入力してください。", ephemeral=True)
            return
        reward_value = None  # ロールタイプなら reward_value は不要にしておく

    elif reward_type == RewardType.SERVER_MONEY:
        if reward_value is None:
            await interaction.response.send_message("金額を指定してください。", ephemeral=True)
            return
        reward_roll = None  # 通貨タイプならロールは使わない

        # 将来的に実装予定ならコメントでも明示しよう
        await interaction.response.send_message("この機能は現在実装されていません。", ephemeral=True)
        return

    # --- データ登録処理 ---
    guild_id = interaction.guild_id
    roll_id = reward_roll.id if reward_roll else None

    await db_manager.add_reward_keyward(
        guild_id=guild_id,
        keyward=keyward,
        reward_type=reward_type,
        reward_value=reward_value,
        roll_id=roll_id
    )

    await interaction.response.send_message("報酬タグが登録されました！", ephemeral=True)

@tree.command(name="test",description="要件を満たしている人に対して報酬を渡したり要件を満たさなくなった人のロールを削除できます")
async def test_check_user_status(interaction:discord.Interaction):
    await check_user_status()
    await interaction.response.send_message("処理が実行されました")


@tasks.loop(minutes=10)
async def check_user_status_loop():
    await check_user_status()


async def check_user_status():
    for guild in client.guilds:
        data = await db_manager.get_keyward_and_rewards_by_guild(guild_id=guild.id)
        if not data:return
        if data["reward_type"] == RewardType.ROLE:
            role_id = data["roll_id"]
            matched_user_ids = get_matched_users(guild.members,data["keyward"])
            role:discord.Role = guild.get_role(role_id)

            for user_id in matched_user_ids:
                user:discord.Member = await guild.fetch_member(user_id)

                if role not in user.roles:
                    await user.add_roles(role)
            for member in role.members:
                if not member.id in matched_user_ids:
                    await member.remove_roles(role)

def get_matched_users(members:list[discord.Member],keywords):
    matched_users:list[int] = []
    for member in members:
        for activity in member.activities:
            if isinstance(activity,discord.CustomActivity):
                if activity.name and keywords in activity.name:
                    matched_users.append(member.id)
    return matched_users                
client.run(TOKEN)