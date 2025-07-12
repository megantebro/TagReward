
import asyncio
import discord
import discord.ext
import discord.ext.commands

disboard_id = 302050872383242240
dissoku_id = 761562078095867916
self_id = 1359305781752893562

async def setup(client:discord.ext.commands.Bot):
    print("extension has loaded")
    client.add_listener(on_message)

async def on_message(message:discord.Message):
    member_id = message.author.id
    channel = message.channel
    print("test_on_message")
    if member_id == self_id: return

    if member_id == disboard_id or member_id == dissoku_id:
        await channel.send("二時間後に通知します")
        await asyncio.sleep(7200)
        await channel.send("<@&1390923287957340240>")



    

    


