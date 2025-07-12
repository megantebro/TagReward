from http import client
from debugpy import connect
import discord
import aiosqlite
import discord.ext
import discord.ext.commands
from platformdirs import user_videos_dir

async def initDB(db:aiosqlite.Connection):

    await db.execute("""
    CREATE TABLE IF NOT EXISTS shops (
    guild_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL UNIQUE,
    cost INTEGER NOT NULL,
    id INTEGER NOT NULL PRIMARY KEY)""")
    await db.commit()

async def setup(client:discord.ext.commands.Bot):
    tree = client.tree

    DB_PATH = "database.db"



    db = await aiosqlite.connect(DB_PATH)
    await initDB(db)

    @tree.command(name="set_shop",description="ポイントで買えるロールを設定します")
    async def set_shop(interaction:discord.Interaction,role:discord.Role,cost:int):
        await db.execute("""
        INSERT INTO shops(guild_id,role_id,cost)
        VALUES (?,?,?)
        ON CONFLICT(role_id)DO UPDATE SET
            guild_id = excluded.guild_id,
            role_id = excluded.role_id,
            cost = excluded.cost
                                      """,
        (interaction.guild_id,role.id,cost))
        await db.commit()
        await interaction.response.send_message(f"<@&{role.id}>をshopに追加しました,{cost}ポイント",ephemeral=True)

    @tree.command(name="view_shop_role",description="ショップで買えるロールを見ることができます")
    async def view_shop(interaction:discord.Interaction):
        cursor = await db.execute(
              """SELECT role_id,cost
                FROM shops
                WHERE guild_id = ?"""
                ,(interaction.guild_id,)
         )
        datas = await cursor.fetchall()
        message = ""
        for data in datas:
            message+= f"<@&{data[0]}>:{data[1]}\n"

        await interaction.response.send_message(message,ephemeral=True)

    @tree.command(name="buy_role",description="ポイントを使用してロールを買えます")
    async def buy_role(interaction:discord.Interaction,role:discord.Role,gift:bool,user:discord.Member=None):
        if not gift and user:
            await interaction.response.send_message("gift時にしかユーザーは指定しません",ephemeral=True)
            return 
        
        cursor = await db.execute("""
        SELECT cost
        FROM shops
        WHERE guild_id = ? AND role_id = ?""",
        (interaction.guild_id,role.id))

        cost = await cursor.fetchone()

        if not cost:
            await interaction.response.send_message("そのロールは販売されていません",ephemeral=True)
            return
        cursor = await db.execute("""
            SELECT amount
            FROM server_money
            WHERE guild_id = ? AND user_id = ?
        """,(interaction.guild_id,interaction.user.id))

        amount = await cursor.fetchone()
        if not amount and amount[0] < cost[0]:
            await interaction.response.send_message("ポイントが足りません",ephemeral=True)
        else:
            await db.execute("""
            UPDATE server_money SET amount = amount - ? WHERE guild_id = ? AND user_id = ?"""
            ,(cost[0],interaction.guild_id,interaction.user.id))
            await db.commit()

            if user:
                await user.add_roles(role)
                await interaction.response.send_message(f"<@&{role.id}>が<@{user.id}>に付与されました",ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"<@&{role.id}>が<@{interaction.user.id}>に付与されました",ephemeral=True)

                