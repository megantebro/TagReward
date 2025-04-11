import discord
from discord import app_commands
import databasemanager
from discord.ext import tasks
import json
import os
from server_money import ServerMoney
import threading
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

@tree.command(name="set_reward_keyward", description="報酬について設定します")
async def set_keyward(
    interaction: discord.Interaction,
    keyward: str,
    reward_value: int = None,
    reward_roll: discord.Role = None
):
    # --- 入力チェック ---
    if not keyward:
        await interaction.response.send_message("タグが入力されていません。プロフィールに書いてもらいたい文言を入力してください。", ephemeral=True)
        return


    # --- データ登録処理 ---
    guild_id = interaction.guild_id
    roll_id = reward_roll.id if reward_roll else None

    await db_manager.set_reward_keyward(
        guild_id=guild_id,
        keyward=keyward,
        reward_value=reward_value,
        roll_id=roll_id
    )

    await interaction.response.send_message("報酬タグが登録されました！", ephemeral=True)

@tree.command(name="test",description="要件を満たしている人に対して報酬を渡したり要件を満たさなくなった人のロールを削除できます")
async def test_check_user_status(interaction:discord.Interaction):
    await check_user_status()
    await interaction.response.send_message("処理が実行されました")


@tasks.loop(hours=12)
async def check_user_status_loop():
    await check_user_status()


async def check_user_status():
    for guild in client.guilds:
        data = await db_manager.get_keyward_and_rewards_by_guild(guild_id=guild.id)
        if not data:return

        matched_user_ids = get_matched_users(guild.members,data["keyward"])

        if data["roll_id"]:
            role_id = data["roll_id"]
            role:discord.Role = guild.get_role(role_id)

            for user_id in matched_user_ids:
                user:discord.Member = await guild.fetch_member(user_id)

                if role not in user.roles:
                    await user.add_roles(role)
            for member in role.members:
                if not member.id in matched_user_ids:
                    await member.remove_roles(role)
        if data["reward_value"]:
            server_money = ServerMoney()
            for user_id in matched_user_ids:
                await server_money.add_money(guild_id=guild.id,user_id=user.id,amount=int(data["reward_value"]),reason="status reward")

def get_matched_users(members:list[discord.Member],keywords):
    matched_users:list[int] = []
    for member in members:
        for activity in member.activities:
            if isinstance(activity,discord.CustomActivity):
                if activity.name and keywords in activity.name:
                    matched_users.append(member.id)
    return matched_users

##ここから下は通貨に関するコマンドの実装
@tree.command(name="balance_set",description="ユーザーの")
async def balance_set(interaction:discord.Interaction,user:discord.Member,amount:int,reason:str=None):
    guild = interaction.guild
    server_money = ServerMoney()
    await server_money.set_money(guild_id=guild.id,user_id=user.id,amount=amount,reason=reason)
    await interaction.response.send_message(f"<@{user.id}>の所持ポイントを{amount}に設定しました")

@tree.command(name="balance_view",description="ユーザーの所持ポイントを表示します")
async def balance_view(interaction:discord.Interaction,user:discord.Member):
    guild = interaction.guild
    server_money = ServerMoney()
    amount = await server_money.get_balance(guild_id=guild.id,user_id=user.id)
    await interaction.response.send_message(f"<@{user.id}>さんは{amount}ポイント持っていました")

@tree.command(name="balance_add",description="ユーザーの所持ポイントを増やします,負の値を入力すれば減らせます、コマンド実行者の資金は減りません")
async def balance_add(interaction:discord.Interaction,user:discord.Member,amount:int):
    guild = interaction.guild
    server_money = ServerMoney()
    old_amount = await server_money.get_balance(guild_id=guild.id,user_id=user.id)
    await server_money.add_money(guild_id=guild.id,user_id=user.id,amount=amount,reason=f"{interaction.user.id}による変更")
    new_amount = await server_money.get_balance(guild_id=guild.id,user_id=user.id)
    await interaction.response.send_message(f"<@{user.id}三の所持ポイントは{old_amount}から{new_amount}になりました>")

@tree.command(name="pay",description="ほかのユーザーに所持ポイントを送金することができます")
async def send_money(interaction:discord.Interaction,to_user:discord.Member,amount:int,):
    guild = interaction.guild
    server_money = ServerMoney()
    try:
        await server_money.transfer_money(guild.id,interaction.user.id,to_user.id,amount)
    except:
        await interaction.followup.send("所持金が足りません",ephemeral=True)
        return
    await interaction.response.send_message(f"<@{to_user.id}>に{amount}ポイント送りました")


if __name__ == "__main__":
    client.run(TOKEN)