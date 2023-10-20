from logging import basicConfig, warning

from pyromod import listen
from pyromod.exceptions import ListenerTimeout
from pyromod.helpers import ikb

from pyrogram import filters, Client
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import(
    FloodWait,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import(
    FloodWaitError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError
)

from bot import Bot, api_id, api_hash

basicConfig(format='%(message)s')

bot = Bot()


@bot.on_message(filters.private & filters.command("start"))
async def start(_, msg: Message):
    button = ikb([
        [("Pyrogram", "pyrogram"), ("Telethon", "telethon")],
    ])
    await msg.reply_photo(photo="./photo.png", reply_markup=button)


async def generate(bot: Bot, msg: Message, telethon=False):
    await msg.delete()
    connecting_msg = await msg.reply("Connecting...")
    if telethon:
        client = TelegramClient(StringSession(), api_id, api_hash)
    else:
        client = Client("Pyrogram", api_id, api_hash, in_memory=True)
    await client.connect()
    await connecting_msg.delete()
    while True:
        phone_number = await bot.ask(
            msg.chat.id,
            "Send the phone number.\ne.g. +628xxx\n\nPress /cancel to cancel.",
            filters=filters.text
        )
        if await cancel_task(msg, phone_number.text):
            return await client.disconnect()
        else:
            break
    try:
        requesting_msg = await msg.reply("Requesting...")
        if telethon:
            await client.send_code_request(phone_number.text)
        else:
            code = await client.send_code(phone_number.text)
        await requesting_msg.delete()
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply("Phone number invalid!\n\nPress /start to create again.")
        await requesting_msg.delete()
        return await client.disconnect()
    except (FloodWait, FloodWaitError) as e:
        await msg.reply(str(e))
        return await client.disconnect()
    try:
        phone_code = await bot.ask(
            msg.chat.id,
            "Send OTP with space.\ne.g. 1 2 3 4 5\n\nPress /cancel to cancel.",
            filters=filters.text,
            timeout=300
        )
    except ListenerTimeout:
        await msg.reply("Time limit reached of 300s.\n\nPress /start to create again.")
        return await client.disconnect()
    if await cancel_task(msg, phone_code.text):
        return await client.disconnect()
    try:
        if telethon:
            await client.sign_in(phone_number.text, phone_code.text)
        else:
            await client.sign_in(phone_number.text, code.phone_code_hash, phone_code.text)
    except (PhoneCodeInvalid, PhoneCodeInvalidError):
        await msg.reply("OTP invalid!\n\nPress /start to create again.")
        return await client.disconnect()
    except (PhoneCodeExpired, PhoneCodeExpiredError):
        await msg.reply("OTP expired!\n\nPress /start to create again.")
        return await client.disconnect()
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        try:
            password = await bot.ask(
                msg.chat.id,
                "Send two-step verification code.\n\nPress /cancel to cancel.",
                filters=filters.text,
                timeout=300
            )
        except ListenerTimeout:
            await msg.reply("Time limit reached of 300s.\n\nPress /start to create again.")
            return await client.disconnect()
        if await cancel_task(msg, password.text):
            return await client.disconnect()
        try:
            if telethon:
                await client.sign_in(password=password.text)
            else:
                await client.check_password(password.text)
        except (PasswordHashInvalid, PasswordHashInvalidError):
            await msg.reply("Password invalid!\n\nPress /start to create again.")
            return await client.disconnect()
    except Exception as e:
        warning(str(e))
        return await client.disconnect()
    if telethon:
        session_string = client.session.save()
    else:
        session_string = await client.export_session_string()
    await bot.send_message(
        msg.chat.id,
        f"`{session_string}`\n\nPress /start to create again."
    )
    return await client.disconnect()


async def cancel_task(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Cancelled!\n\nPress /start to create again.")
        return True
    return False


@bot.on_callback_query()
async def callback(_, callbackquery: CallbackQuery):
    callbackquery_data = callbackquery.data.lower()
    if callbackquery_data in ["pyrogram", "telethon"]:
        await callbackquery.answer()
        try:
            if callbackquery_data == "pyrogram":
                await generate(bot, callbackquery.message)
            else:
                await generate(bot, callbackquery.message, telethon=True)
        except Exception as e:
            warning(str(e))

warning("Bot Started!")


if __name__ == "__main__":
    bot.run()
