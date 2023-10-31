from pyromod import listen
from pyromod.exceptions import ListenerTimeout

from pyrogram import filters, Client
from pyrogram.types import(
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.errors import (
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

bot = Bot()


markup = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        "Pyrogram",
        callback_data="pyrogram"
    ),
    InlineKeyboardButton(
        "Telethon",
        callback_data="telethon"
    )
]])
@bot.on_message(
    filters.private 
    & filters.command("start")
)
async def _start(_, msg: Message):
    await msg.reply(
        "Generate Session String Telegram",
        reply_markup=markup
    )


async def _gens(
    bot: Bot,
    msg: Message,
    telethon=False
):
    msg_connect = await msg.edit("Connecting...")
    chat = msg.chat
    if telethon:
        client = TelegramClient(
            StringSession(),
            api_id,
            api_hash
        )
    else:
        client = Client(
            "User",
            api_id,
            api_hash,
            in_memory=True
        )
    await client.connect()
    await msg_connect.delete()
    while True:
        number = await bot.ask(
            chat.id,
            "Send the phone number."
            "\ne.g. `+628`xxx"
            "\n\nPress /cancel to cancel."
        )
        phone = number.text
        if await _cancel(
            msg, 
            number.text
        ):
            return await client.disconnect()
        else:
            break
    try:
        msg_send = await msg.reply("Connecting...")
        if telethon:
            code = await client.send_code_request(phone)
        else:
            code = await client.send_code(phone)
        await msg_send.delete()
    except (FloodWait, FloodWaitError) as e:
        await msg.reply(e)
        return await client.disconnect()
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply(
            "Phone number invalid!"
            "\n\nPress /start to create again."
        )
        await msg_send.delete()
        return await client.disconnect()
    try:
        otp = await bot.ask(
            chat.id,
            "Send OTP with space."
            "\ne.g. `1  2  3  4  5`"
            "\n\nPress /cancel to cancel.",
            timeout=300
        )
        otp_code = otp.text
    except ListenerTimeout:
        await msg.reply(
            "Time limit reached of 300s."
            "\n\nPress /start to create again."
        )
        return await client.disconnect()
    if await _cancel(msg, otp.text):
        return await client.disconnect()
    try:
        if telethon:
            await client.sign_in(
                phone, 
                otp_code, 
                password=None
            )
        await client.sign_in(
            phone, 
            code.phone_code_hash, 
            phone_code=' '.join(str(otp_code))
        )
    except (PhoneCodeInvalid, PhoneCodeInvalidError):
        await msg.reply(
            "OTP invalid!"
            "\n\nPress /start to create again."
        )
        return await client.disconnect()
    except (PhoneCodeExpired, PhoneCodeExpiredError):
        await msg.reply(
            "OTP expired!"
            "\n\nPress /start to create again."
        )
        return await client.disconnect()
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        try:
            two_step_code = await bot.ask(
                chat.id,
                "Send two-step verification code."
                "\n\nPress /cancel to Cancel.",
                timeout=300
            )
            new_code = two_step_code.text
        except ListenerTimeout:
            await msg.reply(
                "Time limit reached of 300s."
                "\n\nPress /start to create again."
            )
            return await client.disconnect()
        if await _cancel(msg, two_step_code.text):
            return await client.disconnect()
        try:
            if telethon:
                await client.sign_in(password=new_code)
            else:
                await client.check_password(new_code)
        except (PasswordHashInvalid, PasswordHashInvalidError):
            await msg.reply(
                "Password invalid!"
                "\n\nPress /start to create again."
            )
            return await client.disconnect()
    except Exception as e:
        await bot.send_message(
            chat.id,
            str(e),
        )
        return await client.disconnect()
    if telethon:
        string = client.session.save()
    else:
        string = await client.export_session_string()
    await bot.send_message(chat.id, f"`{string}`")
    return await client.disconnect()


async def _cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply(
            "Cancelled!"
            "\n\nPress /start to create again."
        )
        return True
    return False


@bot.on_callback_query()
async def __cbq(bot: Client, cbq: CallbackQuery):
    query = cbq.data.lower()
    if query in ["pyrogram", "telethon"]:
        await cbq.answer()
        try:
            if query == "pyrogram":
                await _gens(bot, cbq.message)
            else:
                await _gens(
                    bot, 
                    cbq.message,
                    telethon=True
                )
        except Exception as e:
            print(e)


if __name__ == "__main__":
    bot.run()
