from os import getenv

from pyrogram import Client


api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"
bot_token = getenv("BOT_TOKEN")


class Bot(Client):
    def __init__(self):
        kwargs = {
            "name": "Bot",
            "api_id": api_id,
            "api_hash": api_hash,
            "bot_token": bot_token,
            "in_memory": True
        }
        super().__init__(**kwargs)
