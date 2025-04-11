from databasemanager import DatabaseManager
import aiosqlite
class ServerMoney:
    def __init__(self):
        self.db = DatabaseManager._instance.db

    async def get_balance(self, guild_id: int, user_id: int) -> int:
        cursor = await self.db.execute(
            "SELECT amount FROM server_money WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def add_money(self, guild_id: int, user_id: int, amount: int, reason: str = "system"):
        current = await self.get_balance(guild_id, user_id)
        if current == 0 and amount >= 0:
            await self.db.execute(
                "INSERT INTO server_money (guild_id, user_id, amount) VALUES (?, ?, ?)",
                (guild_id, user_id, amount)
            )
        else:
            await self.db.execute(
                "UPDATE server_money SET amount = amount + ? WHERE guild_id = ? AND user_id = ?",
                (amount, guild_id, user_id)
            )

        await self.db.execute(
            "INSERT INTO money_history (guild_id, user_id, amount, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, amount, reason)
        )
        await self.db.commit()

    async def set_money(self, guild_id: int, user_id: int, amount: int, reason: str = "manual set"):
        await self.db.execute(
            "INSERT OR REPLACE INTO server_money (guild_id, user_id, amount) VALUES (?, ?, ?)",
            (guild_id, user_id, amount)
        )
        await self.db.execute(
            "INSERT INTO money_history (guild_id, user_id, amount, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, amount, reason)
        )
        await self.db.commit()

    async def transfer_money(self, guild_id: int, from_user: int, to_user: int, amount: int):
        from_balance = await self.get_balance(guild_id, from_user)
        if from_balance < amount:
            raise ValueError("残高が足りません。")

        await self.add_money(guild_id, from_user, -amount, reason=f"transfer_to:{to_user}")
        await self.add_money(guild_id, to_user, amount, reason=f"transfer_from:{from_user}")
