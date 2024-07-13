from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from db.sqlite import Database

db = Database(path_to_db="data/main.db")

CHANNELS = ['-1002169340185']
# PROXY_URL='http://proxy.server:3128/'
BOT_TOKEN = '7272633725:AAHUtjDv8U99-xGzLgRXm5ToU0rW8yPfyCc'

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

markup = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(text='Тексериу', callback_data='check_subscribe')
    ]
])

checked = types.InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(text='Дауыс бериу', callback_data='checked'),
    ]
])


user_data = {}


def create_pagination_keyboard(current_page):
    keyboard = InlineKeyboardMarkup(row_width=3)
    max_page = 7
    if current_page > 1:
        keyboard.insert(InlineKeyboardButton(text="« Арқаға", callback_data=f"page: {current_page - 1}"))

    keyboard.insert(
        InlineKeyboardButton(text=f"{current_page}/{max_page}",
                             callback_data='current'))

    if current_page < max_page:
        keyboard.insert(
            InlineKeyboardButton(text="Кейнги »", callback_data=f"page: {current_page + 1}"))

    return keyboard


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):

    try:
        db.create_table_users()
        db.create_table_voters()
    except Exception as err:
        print(err)


    user_id = message.from_user.id
    user_data[user_id] = {
        'current_page': 1,
        'final_status': True,
        'page': 0,
        'max_page': 7
    }
    keyboard = InlineKeyboardMarkup(row_width=1)
    counter = 1
    for channel in CHANNELS:
        chat = await bot.get_chat(channel)
        invite_link = await chat.export_invite_link()
        keyboard.add(InlineKeyboardButton(text=f'Канал - {counter}', url=f'{invite_link}'))
        counter += 1

    keyboard.add(InlineKeyboardButton(text='Тексериу', callback_data='check_subscribe'))

    await message.answer(
        "<b>Төмендеги каналларға ағза болың:</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


@dp.callback_query_handler(lambda call: call.data == 'check_subscribe')
async def callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_id = call.from_user.id
    user_data[user_id] = {
        'current_page': 1,
        'final_status': True,
        'page': 0,
        'max_page': 7
    }

    result = str()
    for channel in CHANNELS:
        chat = await bot.get_chat(channel)
        user_channel_status = await bot.get_chat_member(chat_id=channel, user_id=call.from_user.id)
        invite_link = await chat.export_invite_link()
        is_member = user_channel_status["status"] != "left"
        if is_member:
            user_data[user_id]['final_status'] *= is_member
            result += f"✅ {chat.title}\n"
        else:
            user_data[user_id]['final_status'] *= is_member
            result += f'❌ <a href="{invite_link}">{chat.title}</a>\n'

    if user_data[user_id]['final_status']:
        await call.answer()
        await bot.edit_message_text(
            text=f"<b>Төмендеги каналларға ағза болың:</b>\n{result}",
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=checked)
    else:
        await call.answer()
        await bot.edit_message_text(
            text=f"<b>Төмендеги каналларға ағза болың:</b>\n{result}",
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data == 'show_voters')
async def getPages(call: types.CallbackQuery):
    user_id = call.from_user.id
    users = db.select_all_users(user_data[user_id]['page'])

    keyboard2 = create_pagination_keyboard(user_data[user_id]['current_page'])

    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in users:
        keyboard.add(InlineKeyboardButton(text=f"{user[1]} - {user[2]} голосов",
                                          callback_data=f"vote: {user[0]}"))
    keyboard.add(InlineKeyboardButton(text='Қатнасыушылар дизимин көриў', callback_data='show_users'))

    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    await call.message.answer('Дауыс бериң:', reply_markup=keyboard)
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
        keyboard.add(InlineKeyboardButton(text=f"{user[1]} - {user[2]} голосов",
                                          callback_data=f"vote: {user[0]}"))
    keyboard.add(InlineKeyboardButton(text='Қатнасыушылар дизимин көриў', callback_data='show_users'))
    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])
    await call.answer()
    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('vote:'))
async def vote(call: types.CallbackQuery):
    user_id = call.from_user.id
    keyboard2 = create_pagination_keyboard(user_data[user_id]['current_page'])
    exist = db.check_voter(call.from_user.id)

    if exist[0]:
        await bot.answer_callback_query(call.id, text="Сиз алдын даўыс бергенсиз!", show_alert=True)
    else:
        db.update_user_vote(ident=int(call.data.split(':')[1]))
        db.add_voter(full_name=call.from_user.full_name, telegram_id=call.from_user.id)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    users = db.select_all_users(user_data[user_id]['page'])
    for user in users:
        keyboard.add(InlineKeyboardButton(text=f"{user[1]} - {user[2]} голосов",
                                          callback_data=f"vote: {user[0]}"))
    keyboard.add(InlineKeyboardButton(text='Қатнасыушылар дизимин көриў', callback_data='show_users'))
    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])
    print(keyboard)
    await call.answer()
    await bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == 'show_users')
async def show_users(call: types.CallbackQuery):
    users = db.select_allow_users()
    response = str()
    count = 1
    for user in users:
        response += f'{count}) {user[1]} - {user[2]} дауыс\n'
        count += 1
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text='« Арқаға', callback_data='back'))

    await call.answer()
    await bot.edit_message_text(
        text=f'Қатнасыушылар дизими:\n{response}',
        message_id=call.message.message_id,
        chat_id=call.from_user.id,
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda call: call.data == 'back')
async def back(call: types.CallbackQuery):
    user_id = call.from_user.id
    users = db.select_all_users(user_data[user_id]['page'])

    keyboard2 = create_pagination_keyboard(user_data[user_id]['current_page'])

    keyboard = InlineKeyboardMarkup(row_width=1)

    for user in users:
        keyboard.add(InlineKeyboardButton(text=f"{user[1]} - {user[2]} даўыс",
                                          callback_data=f"vote: {user[0]}"))
    keyboard.add(InlineKeyboardButton(text='Қатнасыушылар дизимин көриў', callback_data='show_users'))

    keyboard['inline_keyboard'].extend(keyboard2['inline_keyboard'])

    await call.answer()
    await bot.edit_message_text(
        text='Даўыс bering:',
        message_id=call.message.message_id,
        chat_id=call.from_user.id,
        reply_markup=keyboard
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
