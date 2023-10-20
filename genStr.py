from asyncio import sleep
from asyncio.exceptions import TimeoutError

from pyromod import listen
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded
)

from bot import Bot, api_id, api_hash

bot = Bot()


@bot.on_message(
    filters.private 
    & filters.command("start")
)
async def _gens(bot: Bot, msg: Message):
    msg_connect = await msg.reply("Connecting...")
    chat = msg.chat
    client = Client(
        name="User",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True
    )

    await client.connect()
    await msg_connect.delete()
    while True:
        number = await bot.ask(
            chat.id,
            "Send the phone number.\n"
            "e.g. `+628`xxx\n\n"
            "Press /cancel to cancel."
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
        code = await client.send_code(phone)
        await msg_send.delete()
    except FloodWait as e:
        await msg.reply(
            f"You have floodwait of {e.value}s.")
        return await client.disconnect()
    except PhoneNumberInvalid:
        await msg.reply(
            "Phone number is invalid!\n\n"
            "Press /start to create again."
        )
        await msg_send.delete()
        return await client.disconnect()
    try:
        otp = await bot.ask(
            chat.id, 
            "Send OTP with space.\n"
            "e.g. `1  2  3  4  5`\n\n"
            "Press /cancel to cancel.",
            timeout=300
        )
        otp_code = otp.text
    except TimeoutError:
        await msg.reply(
            "Time limit reached of 300s.\n\n"
            "Press /start to create again."
        )
        return await client.disconnect()
    if await _cancel(msg, otp.text):
        return await client.disconnect()
    try:
        await client.sign_in(
            phone, 
            code.phone_code_hash, 
            phone_code=' '.join(str(otp_code))
        )
    except PhoneCodeInvalid:
        await msg.reply(
            "OTP invalid!\n\n"
            "Press /start to create again."
        )
        return await client.disconnect()
    except PhoneCodeExpired:
        await msg.reply(
            "OTP expired!\n\n"
            "Press /start to create again."
        )
        return await client.disconnect()
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "Send two-step verification code."
                "\n\nPress /cancel to Cancel.",
                timeout=300
            )
            new_code = two_step_code.text
        except TimeoutError:
            await msg.reply(
                "Time limit reached of 300s."
                "\n\nPress /start to create again."
            )
            return await client.disconnect()
        if await _cancel(msg, two_step_code.text):
            return await client.disconnect()
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"`{str(e)}`")
            return await client.disconnect()
    except Exception as e:
        await bot.send_message(
            chat.id,
            f"`{str(e)}`"
        )
        return await client.disconnect()
    string = await client.export_session_string()
    await bot.send_message(chat.id, string)
    return await client.disconnect()


async def _cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Cancelled!")
        return True
    return False


if __name__ == "__main__":
    bot.run()
