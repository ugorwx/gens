import configparser

from pyrogram import Client
from pyromod import listen

config = configparser.ConfigParser()
config.read("config.ini")

api_id = config.get("api", "id")
api_hash = config.get("api", "hash")
bot_token = config.get("bot", "token")


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