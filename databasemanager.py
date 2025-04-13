import aiosqlite
DB_PATH = "database.db"
class DatabaseManager:
    _instance = None
    db= None
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
                reward_value TEXT,
                roll_id INTEGER
            )
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS server_money (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER DEFAULT 0,
                PRIMARY KEY(guild_id,user_id)                 
            )
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS money_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT,
                create_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                api_key TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.db.commit()


    async def set_reward_keyward(self,guild_id:int,keyward:str,reward_value:int=None,roll_id:int=None):
        await self.db.execute(
        """
        INSERT INTO reward_keywards (guild_id, keyward,reward_value, roll_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            keyward=excluded.keyward,
            reward_value=excluded.reward_value,
            roll_id=excluded.roll_id
        """,
        (guild_id, keyward, reward_value, roll_id)
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
            SELECT keyward, roll_id, reward_value
            FROM reward_keywards
            WHERE guild_id = ? 
        """,(guild_id,))
        row = await cursor.fetchone()
        if row:
            return{
                "keyward": row[0],
                "roll_id": row[1],
                "reward_value":row[2],
            }
        return None
    
