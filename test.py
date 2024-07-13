from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.builtin import CommandStart
from aiogram.dispatcher.middlewares import BaseMiddleware
import logging

from db.sqlite import Database

db = Database(path_to_db="data/main.db")

CHANNELS = ['channels_name']
PROXY_URL = 'http://proxy.server:3128/'
BOT_TOKEN = 'bot_token'

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

user_data = {}


class RedirectCallbackQueryMiddleware(BaseMiddleware):

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.text == '/start':
            user_id = message.from_user.id
            user_data[user_id] = {
                'current_page': 1,
                'page': 0,
                'max_page': 7,
            }

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        user_id = callback_query.from_user.id
        user_data[user_id] = {
            'current_page': 1,
            'page': 0,
            'max_page': 7,
        }
        if callback_query.data == 'check_subscribe':
            counter = 1
            for channel in CHANNELS:
                user_channel_status = await bot.get_chat_member(chat_id=channel, user_id=callback_query.from_user.id)
                is_member = user_channel_status["status"] != "left"
                current_channel = f"channel{counter}"
                if is_member:
                    if db.check_subscribe(current_channel, callback_query.from_user.id)[0] == 0:
                        db.add_subscriber(current_channel,
                                          callback_query.from_user.full_name,
                                          callback_query.from_user.id)
                else:
                    db.delete_subscriber(current_channel, callback_query.from_user.id)
                counter += 1

            check_subscribe = db.check_subscribe('channel1', callback_query.from_user.id)[0] and db.check_subscribe(
                'channel2', callback_query.from_user.id)[0] and db.check_subscribe(
                'channel3', callback_query.from_user.id)[0]

            if check_subscribe:
                await bot.answer_callback_query(callback_query.id)
                await show_voters(callback_query)
            else:
                await bot.answer_callback_query(callback_query.id)
                await check(callback_query)


def create_pagination_keyboard(current_page):
    keyboard = InlineKeyboardMarkup(row_width=3)
    max_page = 7
    if current_page > 1:
        keyboard.insert(InlineKeyboardButton(text=" « Арқаға", callback_data=f"page: {current_page - 1}"))

    keyboard.insert(
        InlineKeyboardButton(text=f"{current_page}/{max_page}",
                             callback_data='current'))

    if current_page < max_page:
        keyboard.insert(
            InlineKeyboardButton(text="Кейнги »", callback_data=f"page: {current_page + 1}"))

    return keyboard


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):


    keyboard = InlineKeyboardMarkup(row_width=1)
    counter = 1
    for channel in CHANNELS:
        chat = await bot.get_chat(channel)
        invite_link = await chat.export_invite_link()
        keyboard.add(InlineKeyboardButton(text=f"Канал - {counter}", url=f"{invite_link}"))
        counter += 1
    keyboard.add(InlineKeyboardButton(text='Ағза болдым', callback_data='check_subscribe'))
    await message.answer(
        f"<b>Даўыс бериў ушын томендеги каналларға ағза болыўыңыз керек:</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@dp.callback_query_handler(lambda call: call.data == 'check_subscribe')
async def check(call: types.CallbackQuery):
    user_id = call.from_user.id
    keyboard = InlineKeyboardMarkup(row_width=1)
    counter = 1
    for channel in CHANNELS:
        user_channel_status = await bot.get_chat_member(chat_id=channel, user_id=call.from_user.id)
        chat = await bot.get_chat(channel)
        invite_link = await chat.export_invite_link()
        is_member = user_channel_status["status"] != "left"
        if not is_member:
            keyboard.add(InlineKeyboardButton(text=f"Канал - {counter}", url=f"{invite_link}"))
        counter += 1
    keyboard.add(InlineKeyboardButton(text='Ағза болдым', callback_data="check_subscribe"))

    await bot.edit_message_text(
        f"<b>Даўыс бериў ушын томендеги каналларға ағза болыўыңыз керек:</b>",
        message_id=call.message.message_id,
        chat_id=call.from_user.id,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )

    await call.answer()


@dp.callback_query_handler(lambda call: call.data == 'show_voters')
async def show_voters(call: types.CallbackQuery):
    user_id = call.from_user.id
    users = db.select_all_users(user_data[user_id]['page'])

    keyboard2 = create_pagination_keyboard(user_data[user_id]['current_page'])

    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in users:
        keyboard.add(InlineKeyboardButton(text=f"{user[1]}",
                                          callback_data=f"vote: {user[0]}"))

    keyboard.add(InlineKeyboardButton(text='Қатнасыушылар дизимин көриў', callback_data='show_users'))
    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])

    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    await call.message.answer('Махалла ақсакалын танлаң:', reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(lambda call: call.data.startswith('page:'))
async def getUsers(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data[user_id]['current_page'] = int(call.data.split(':')[1])

    if user_data[user_id]['current_page'] == 1:
        user_data[user_id]['page'] = 0
    elif user_data[user_id]['current_page'] == 2:
        user_data[user_id]['page'] = 10
    elif user_data[user_id]['current_page'] == 3:
        user_data[user_id]['page'] = 20
    elif user_data[user_id]['current_page'] == 4:
        user_data[user_id]['page'] = 30
    elif user_data[user_id]['current_page'] == 5:
        user_data[user_id]['page'] = 40
    elif user_data[user_id]['current_page'] == 6:
        user_data[user_id]['page'] = 50
    elif user_data[user_id]['current_page'] == 7:
        user_data[user_id]['page'] = 60

    keyboard2 = create_pagination_keyboard(user_data[user_id]['current_page'])
    users = db.select_all_users(user_data[user_id]['page'])
    keyboard = InlineKeyboardMarkup(row_width=1)
    for user in users:
        keyboard.add(InlineKeyboardButton(text=f"{user[1]}",
                                          callback_data=f"vote: {user[0]}"))
    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])

    await bot.edit_message_text(text='Махалла ақсакалын танлаң', message_id=call.message.message_id, chat_id=call.from_user.id, reply_markup=keyboard)
    await call.answer()



@dp.callback_query_handler(lambda call: call.data.startswith('vote:'))
async def vote(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = db.select_user(int(call.data.split(':')[1]))
    print('afasdfasdf')
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='Даўыс бериу', callback_data=f'voted: {user[0]}'))
    keyboard.add(InlineKeyboardButton(text='« Арқаға', callback_data='show_voters'))
    phot_url = f'{user[3]}'
    caption = f'<i>Ф.И.О:</i> <b>{user[1]}</b>\n' \
              f'<i>Махалла:</i> <b>{user[2]}</b>\n' \
              f'<i>Топлаған даўыслар саны</i> - <b>{user[4]}</b>\n\n'



    await bot.send_photo(call.message.chat.id, phot_url, caption=caption, reply_markup=keyboard)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    await call.answer()



@dp.callback_query_handler(lambda call: call.data.startswith('voted:'))
async def vote(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = db.select_user(int(call.data.split(':')[1]))
    exist = db.check_voter(user_id)
    if exist[0]:
        await bot.answer_callback_query(call.id, text="Сиз алдын даўыс бердиңиз!!!", show_alert=True)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await call.answer()
    else:
        db.update_user_vote(ident=int(call.data.split(':')[1]))
        db.add_voter(full_name=call.from_user.full_name, telegram_id=call.from_user.id)

        user = db.select_user(int(call.data.split(':')[1]))
        users = db.get_rank()
        rank = None
        keyboard = InlineKeyboardMarkup(row_width=1)
        for user1 in users:
            if user1[0] == user[0]:
                rank = user1[3]
        keyboard.add(InlineKeyboardButton(text='Даўыс бериу', callback_data=f'voted: {user[0]}'))
        keyboard.add(InlineKeyboardButton(text='« Арқаға', callback_data='show_voters'))



        await call.message.answer(text=f'Ассалаўма әлейкум {call.from_user.full_name}, даўыс бергениңиз ушын рахмет!!!\n\nФ.И.О: <b>{user[1]} ({rank} - орын)</b>\nMәҳәлле: <b>{user[2]}</b>\nТоплаган дауыс: <b>{user[4]}</b>')
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await call.answer()

@dp.callback_query_handler(lambda call: call.data == 'show_users')
async def show_users(call: types.CallbackQuery):
    users = db.select_allow_users()
    response = str()
    count = 1
    for user in users:
        response += f'{count}) {user[1]} - {user[4]} дауыс\n'
        count += 1
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='« Арқаға', callback_data='show_voters'))

    await call.answer()
    await bot.edit_message_text(
        text=f'Қатнасыушылар дизими:\n{response}',
        message_id=call.message.message_id,
        chat_id=call.from_user.id,
        reply_markup=keyboard
    )

if __name__ == '__main__':
    dp.middleware.setup(RedirectCallbackQueryMiddleware())
    executor.start_polling(dp, skip_updates=True)
