from functools import wraps
from flask import request, jsonify, g
import aiosqlite
import asyncio

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            return jsonify({"error": "APIキーが必要です"}), 401

        result = asyncio.run(get_guild_and_user_from_api_key(api_key))
        if not result:
            return jsonify({"error": "無効なAPIキーです"}), 403

        # Flaskのグローバルオブジェクト g に値を一時保存
        g.guild_id, g.user_id = result
        return f(*args, **kwargs)
    return decorated_function

async def get_guild_and_user_from_api_key(api_key: str):
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.execute(
            "SELECT guild_id, user_id FROM api_keys WHERE api_key = ?", (api_key,)
        )
        return await cursor.fetchone()  # (guild_id, user_id) or None
