from operator import truediv
from typing import Annotated

from fastapi.security import APIKeyHeader

from databasemanager import DB_PATH
from .api_models import MoneyAddition, MoneySetting, MoneyTransfer
import asyncio
from server_money import ServerMoney 
from fastapi import Depends, FastAPI, HTTPException
import aiosqlite

app = FastAPI()

api_key_header = APIKeyHeader(name="x-api-key")
async def get_api_key(api_key:Annotated[str,Depends(api_key_header)]):
    db = await aiosqlite.connect(DB_PATH)

    cursor = await db.execute("""
    SELECT api_key
    FROM api_keys
    WHERE api_key = ?
    LIMIT 1
    """,(api_key,))

    data = await cursor.fetchone()

    
    if data:
        return api_key
        
    raise HTTPException(403)


@app.get("/api/money")
async def get_money(user_id:int,guild_id:int,api_key:Annotated[str,Depends(get_api_key)]):
    if not guild_id or not user_id:
        return {"error": "guild_id and user_id are required"}, 400

    # 非同期関数を同期的に呼び出す
    balance = await ServerMoney().get_balance(guild_id, user_id)

    return {
        "guild_id": guild_id,
        "user_id": user_id,
        "balance": balance
    }

@app.post("/api/money/add")
async def add_money(data:MoneyAddition):
    guild_id = data.guild_id
    user_id = data.user_id
    amount = data.amount
    reason = data.reason

    await ServerMoney().add_money(**data)

    return {
        "message": "Money added successfully",
        "guild_id": guild_id,
        "user_id": user_id,
        "amount": amount,
        "reason": reason
    }, 200


@app.post("/api/money/set")
async def set_money(data:MoneySetting):
    guild_id = data.guild_id
    user_id = data.user_id
    amount = data.amount
    reason = data.reason

    await ServerMoney().set_money(guild_id, user_id, int(amount), reason)
    return {"message": "Money set successfully"}


@app.route("/api/money/transfer", methods=["POST"])
async def transfer_money(data:MoneyTransfer):
    guild_id = data.guild_id
    from_user = data.from_user_id
    to_user = data.to_user_id
    amount = data.amount
    try:
        await ServerMoney().transfer_money(guild_id, int(from_user), int(to_user), int(amount))
    except ValueError as e:
        return {"error": str(e)}, 400

    return {"message": "Transfer complete"}

def api_run():
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=5002)