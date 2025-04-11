import aiosqlite
from reward import RewardType
DB_PATH = "database.db"
class DatabaseManager:
    _instance = None
    db = None
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.init_db()
        return cls._instance
    
    async def init_db(self):
        self.db = await aiosqlite.connect(DB_PATH)  # ← async with は使わない！
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS reward_keywards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL UNIQUE,
                keyward TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT,
                roll_id INTEGER
            )
        """)
        await self.db.commit()


    async def add_reward_keyward(self,guild_id:int,keyward:str,reward_type:RewardType,reward_value:int=None,roll_id:int=None):
        await self.db.execute(
        """
        INSERT INTO reward_keywards (guild_id, keyward, reward_type, reward_value, roll_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            keyward=excluded.keyward,
            reward_type=excluded.reward_type,
            reward_value=excluded.reward_value,
            roll_id=excluded.roll_id
        """,
        (guild_id, keyward, reward_type, reward_value, roll_id)
        )
        await self.db.commit()

    async def get_keywords_by_guild(self,guild_id:int):
        cursor = await self.db.execute(
            "SELECT keyward FROM reward_keywards WHERE guild_id = ?",(guild_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def get_keyward_and_rewards_by_guild(self,guild_id:int):
        cursor = await self.db.execute("""
            SELECT keyward, roll_id, reward_value, reward_type
            FROM reward_keywards
            WHERE guild_id = ? 
        """,(guild_id,))
        row = await cursor.fetchone()
        if row:
            return{
                "keyward": row[0],
                "roll_id": row[1],
                "reward_value":row[2],
                "reward_type":row[3]
            }
        return None
    
