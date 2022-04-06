from asyncio import new_event_loop, set_event_loop
from threading import Thread

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from requests import post, get

from app.models import Account
from config import TG_TOKEN, CALL_TOKEN, CALL_CAMPAIGN_ID, CALL_EMERGENCY

CALL_URL = 'https://zvonok.com/manager/cabapi_external/api/v1/phones/call/'

texts = {
    'start': 'This bot will send you notifications when an emergency is detected.\n\n'
             'To link go to <a href="https://fsafe.yegoryakubovich.com/account">My account</a>.',
    'not_linked': 'This telegram account is not linked to FSafe account.\n\n'
                  'To link go to <a href="https://fsafe.yegoryakubovich.com/account">My account</a>.',
    'linked': 'Account @{} successfully linked!\n\n'
              'Go to <a href="https://fsafe.yegoryakubovich.com/account">My account</a>.',
    'unlinked': 'Account @{} successfully unlinked! You will no longer receive notifications.',
    'help': 'FSafe is a smart home module designed to ensure fire safety.\n\n'
            '/stop - disable notifications'
}

bot = Bot(token=TG_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)


def send_notification(account, notification, call=False):
    if account.tg_id:
        send_text = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=html' \
            .format(TG_TOKEN, account.tg_id, notification)
        get(send_text)
    if call:
        # Account
        data = {
            'public_key': CALL_TOKEN,
            'campaign_id': CALL_CAMPAIGN_ID,
            'phone': account.phone,
            'text': '<p>{}</p>'.format(notification),
        }
        post(url=CALL_URL, data=data)


def send_notification_emergency(notification):
    data = {
        'public_key': CALL_TOKEN,
        'campaign_id': CALL_CAMPAIGN_ID,
        'phone': CALL_EMERGENCY,
        'text': notification,
    }
    post(url=CALL_URL, data=data)


@dp.message_handler(commands=['start'])
async def bot_start(message: types.Message):
    tg_id = message.from_user.id
    tg_username = message.from_user.username

    is_tied = Account.get_or_none(Account.tg_id == message.from_user.id)
    account_id = message.text.split()[-1]
    account = Account.get_or_none(Account.id == account_id)

    if is_tied:
        await bot_help(message=message)
    elif not account:
        await message.reply(texts['not_linked'])
    else:
        account.tg_id = tg_id
        account.tg_username = tg_username if tg_username else str(tg_id)
        account.save()
        await message.reply(texts['linked'].format(account.login))


@dp.message_handler(commands=['stop'])
async def bot_stop(message: types.Message):
    account = Account.get_or_none(Account.tg_id == message.from_user.id)

    if not account:
        await message.reply(texts['not_linked'])
    else:
        account.tg_id = None
        account.tg_username = None
        account.save()
        await message.reply(texts['unlinked'].format(account.login))


@dp.message_handler()
async def bot_help(message: types.Message):
    await message.reply(texts['help'])


def bot():
    set_event_loop(new_event_loop())
    executor.start_polling(dp)


def bot_run():
    Thread(target=bot, daemon=True, args=()).start()
