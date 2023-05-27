from config import token
from aiogram import *
import sqlite3 as sq
import asyncio
from telethon import TelegramClient
from functions_and_keyboards import *
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

bot = Bot(token, parse_mode='HTML')
disp = Dispatcher(bot)

# find at https://my.telegram.org/apps
api_id = 22779440
api_hash = 'a41e54c9a42d85759e557bdc507701aa'
client = TelegramClient('bot', api_id, api_hash)


class MuteMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message, data):
        user_status = await is_muted(message.from_user.id)

        if user_status:
            await message.delete()

            raise CancelHandler()


async def on_startup(_):
    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query1 = 'CREATE TABLE IF NOT EXISTS roles (role VARCHAR(20) UNIQUE);'\
                'CREATE TABLE IF NOT EXISTS users (user_id VARCHAR(40) UNIQUE, user_role INT REFERENCES roles(rowid))'

        cursor.executescript(query1)

        try:
            query2 = 'INSERT INTO roles VALUES ("user");' \
                     'INSERT INTO roles VALUES ("admin");' \
                     'INSERT INTO roles VALUES ("moderator");' \
                     'INSERT INTO roles VALUES ("muted")'

            cursor.executescript(query2)

        except Exception:
            pass

        db.commit()

@disp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def member_enters_the_chat(message):
    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query = f'INSERT INTO users VALUES ("{message["new_chat_member"]["id"]}", 1)'

        cursor.execute(query)

        db.commit()

    bot_msg = await message.reply(f'<b>Добро пожаловать, {message["new_chat_member"]["username"]} !</b>')

    await asyncio.sleep(7)
    await bot_msg.delete()


@disp.message_handler(content_types=types.ContentType.LEFT_CHAT_MEMBER)
async def member_leaves_the_chat(message):
    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query = f'DELETE FROM users WHERE user_id = "{message["left_chat_member"]["id"]}"'

        cursor.execute(query)

        db.commit()

@disp.message_handler(commands=['help'])
async def help_cmd(message):
    bot_msg = await bot.send_message(message.chat.id, '<b>Список команд:\n'
                                                      '▪️/help - список команд\n'
                                                      '▪️/view @username - посмотреть информацию о пользователе(его роль)\n'
                                                      '▪️/give @username role - выдать пользователю роль user/admin/moderator. (только если ваша роль выше выдаваемой роли и роли получателя, а также у получателя нет этой роли)\n'
                                                      '▪️/mute @username time(seconds) comment - замьютить пользователя на конкретное время(в секундах) с комментарием. (Мьютить можно только если ваша роль выше роли нарушителя)</b>')

    await message.delete()

    await asyncio.sleep(7)
    await bot_msg.delete()

@disp.message_handler(lambda message: message.text.startswith('/view'))
async def send_user_info(message):
    username = message.text.split(' ')[1]

    user_id = await get_user_id(username)

    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query = f'SELECT roles.role FROM users INNER JOIN roles ON users.user_role = roles.rowid WHERE user_id = "{user_id}"'

        user_role = cursor.execute(query).fetchone()[0]

    bot_msg = await bot.send_message(message.chat.id, f'<b>{username} - {user_role}</b>')

    await asyncio.sleep(7)
    await bot_msg.delete()


@disp.message_handler(lambda message: message.text.startswith('/give'))
async def give_role(message):
    args = message.text.split(' ')  # member, role

    user_id = await get_user_id(args[1])

    permission = await check_rights(message, args)

    if permission:
        actioned_role_name = args[2]

        with sq.connect('users.db') as db:
            cursor = db.cursor()

            query1 = f'SELECT rowid FROM roles WHERE role = "{actioned_role_name}"'

            actioned_role_id = cursor.execute(query1).fetchone()[0]

            query2 = f'UPDATE users SET user_role = {actioned_role_id} WHERE user_id = "{user_id}"'

            cursor.execute(query2)

            db.commit()

        bot_msg = await message.reply('<b>Операция была выполнена успешно!</b>')

    else:
        bot_msg = await message.reply('<b>Операция некорректна и не может быть выполнена.</b>')


    await asyncio.sleep(7)

    await message.delete()
    await bot_msg.delete()


@disp.message_handler(lambda message: message.text.startswith('/mute'))
async def mute_member(message):
    args = message.text.split(' ')  # member, time(s), comment

    user_id = await get_user_id(args[1])
    args.append(user_id)

    permission = await check_mute_rights(message, args)

    if permission:
        with sq.connect('users.db') as db:
            cursor = db.cursor()

            query1 = f'SELECT user_role FROM users WHERE user_id = "{user_id}"'

            primary_user_role_id = cursor.execute(query1).fetchone()[0]

            query2 = f'UPDATE users SET user_role = 4 WHERE user_id = "{user_id}"'

            cursor.execute(query2)

            db.commit()

        bot_msg = await message.reply(f'<b>Операция была выполнена успешно! Пользователь {args[1]} был замучен пользователем @{message.from_user.username} на {int(args[2])} s с комментарием: {args[3]}</b>')

        await asyncio.sleep(7)

        await message.delete()
        await bot_msg.delete()

        await asyncio.sleep(int(args[2]))

        with sq.connect('users.db') as db:
            cursor = db.cursor()

            query = f'UPDATE users SET user_role = {primary_user_role_id} WHERE user_id = "{user_id}"'

            cursor.execute(query)

            db.commit()

    else:
        bot_msg = await message.reply('<b>Операция некорректна и не может быть выполнена.</b>')

        await asyncio.sleep(7)

        await message.delete()
        await bot_msg.delete()

if __name__ == '__main__':
    disp.middleware.setup(MuteMiddleware())
    executor.start_polling(disp, skip_updates=True, on_startup=on_startup)