from pydantic import BaseModel, Field



class MoneyAddition(BaseModel):
    guild_id:int
    user_id:int
    amount:int
    reason:str


class MoneySetting(BaseModel):
    guild_id:int
    user_id:int
    amount:int
    reason:str

class MoneyTransfer(BaseModel):
    guild_id:int
    from_user_id:int
    to_user_id:int
    amount:int
    reason:str
