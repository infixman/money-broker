import locale
import json
import logging
import os
import requests
from bs4 import BeautifulSoup
from cacheout import Cache
from datetime import datetime, timedelta, timezone
from telegram import Update
from lxml import html
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext)

APPNAME = os.environ["APPNAME"]
PORT = int(os.environ.get('PORT', '8443'))
TOKEN = os.environ["TOKEN"]
MOONPAYKEY = os.environ["MOONPAYKEY"]
ETHERSCANKEY = os.environ["ETHERSCANKEY"]
cache = Cache()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def msg_listener(update: Update, context: CallbackContext):
    msg = update.message
    txt = msg.text.strip()
    if '?gas' == txt.lower():
        msg.reply_text(get_gas())
    elif '啪' in txt or '沒了' in txt:
        msg.reply_sticker('CAACAgUAAxkBAAEBLAJgd99sMMuqwAfwa9FOzEtglxLn4AAClwIAArjQcVewe5BU0CNqSB8E')
    elif '崩崩' in txt:
        msg.reply_sticker('CAACAgIAAxkBAAEBLAVgd-FvoMW8F3nVGqx0nOUyxIF-qAACYQQAAonq5QdmC3mfOHu_3h8E')
    elif '梭哈' in txt and '/梭哈' != txt:
        msg.reply_sticker('CAACAgUAAxkBAAEBLAhgd-Grf4bTcZXHaHLUjOtNZMx3cwACNwQAAhwmkVfJpMRsyVY09B8E')
    elif txt.startswith('?pcs ') and len(txt.split(' ')) == 2:
        msg.reply_text('/swap pancake 1 {} wbnb busd'.format(txt.split(' ')[1]))
    elif txt.startswith('?uni ') and len(txt.split(' ')) == 2:
        msg.reply_text('/swap uni 1 {} weth usdt'.format(txt.split(' ')[1]))
    elif txt.startswith('?sushi ') and len(txt.split(' ')) == 2:
        msg.reply_text('/swap sushi 1 {} weth usdt'.format(txt.split(' ')[1]))
    elif txt.startswith('?pcs ') and len(txt.split(' ')) == 3 and isfloat(txt.split(' ')[1]):
        msg.reply_text('/swap pancake {} {} wbnb busd'.format(txt.split(' ')[1], txt.split(' ')[2]))
    elif txt.startswith('?uni ') and len(txt.split(' ')) == 3 and isfloat(txt.split(' ')[1]):
        msg.reply_text('/swap uni {} {} weth usdt'.format(txt.split(' ')[1], txt.split(' ')[2]))
    elif txt.startswith('?sushi ') and len(txt.split(' ')) == 3 and isfloat(txt.split(' ')[1]):
        msg.reply_text('/swap sushi {} {} weth usdt'.format(txt.split(' ')[1], txt.split(' ')[2]))
    elif (txt.endswith('=?') or txt.endswith('=$?')) and ('+' in txt or '-' in txt or '*' in txt or '/' in txt or '^' in txt):
        fomula = txt.split('=')[0].strip().replace('^', '**')
        try:
            if txt.endswith('=$?'):
                locale.setlocale(locale.LC_ALL, 'en_US.utf8')
                msg.reply_text('={}'.format(locale.format("%.2f", eval(fomula), grouping=True)))
            else:
                msg.reply_text('={}'.format(eval(fomula)))
        except:
            msg.reply_sticker('CAACAgUAAxkBAAEBLBFgd_tZGLLQLj5O7kuE-r7chp_LOAAC_wEAAmmSQVVx1ECQ0wcNAh8E')


@cache.memoize(ttl=10 * 60, typed=True)
def ask_mastercard_rate(update: Update, context: CallbackContext):
    update.message.reply_text('USD = {} TWD'.format(get_usd_rete_from_3rd()[0]))


@cache.memoize(ttl=10 * 60, typed=True)
def ask_visa_rate(update: Update, context: CallbackContext):
    update.message.reply_text('USD = {} TWD'.format(get_usd_rete_from_3rd()[1]))


@cache.memoize(ttl=10 * 60, typed=True)
def ask_jcb_rate(update: Update, context: CallbackContext):
    update.message.reply_text('USD = {} TWD'.format(get_usd_rete_from_3rd()[2]))


@cache.memoize(ttl=10 * 60, typed=True)
def ask_usd_rate(update: Update, context: CallbackContext):
    update.message.reply_text(get_usd_rate())

@cache.memoize(ttl=10 * 60, typed=True)
def ask_usd_rate_esunbank(update: Update, context: CallbackContext):
    update.message.reply_text('玉山買入USD = {} TWD'.format(get_usd_rate_esunbank()))


@cache.memoize(ttl=3 * 60, typed=True)
def ask_ace(update: Update, context: CallbackContext):
    utc_now = datetime.now(timezone.utc)
    price = get_ace_price()
    if price > -1:
        update.message.reply_text('Ace\nUSDT = {} TWD'.format(price))
    else:
        update.message.reply_text('Ace\n找不到資料(可能死了)')


@cache.memoize(ttl=3 * 60, typed=True)
def ask_bito(update: Update, context: CallbackContext):
    utc_now = datetime.now(timezone.utc)
    # tw_time = (utc_now + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    price = get_bito_price(utc_now)
    if price > -1:
        update.message.reply_text('BitoPro\nUSDT = {} TWD'.format(price))
    else:
        update.message.reply_text('BitoPro\n找不到資料(可能死了)')


@cache.memoize(ttl=3 * 60, typed=True)
def ask_max(update: Update, context: CallbackContext):
    utc_now = datetime.now(timezone.utc)
    price = get_max_price()
    if price > -1:
        update.message.reply_text('Max\nUSDT = {} TWD'.format(price))
    else:
        update.message.reply_text('Max\n找不到資料(可能死了)')


@cache.memoize(ttl=3 * 60, typed=True)
def ask_usdt(update: Update, context: CallbackContext):
    update.message.reply_text(get_usdt())


@cache.memoize(ttl=60 * 60 * 4, typed=True)
def ask_combine(update: Update, context: CallbackContext):
    update.message.reply_text('{}\n\n{}'.format(get_usdt(), get_usd_rate()))


@cache.memoize(ttl=10 * 60, typed=True)
def ask_ust(update: Update, context: CallbackContext):
    update.message.reply_text('Mirror Wallet UST = {} USD'.format(get_ust()))


def get_usd_rete_from_3rd():
    r = requests.get('https://www.bestxrate.com/card/mastercard/usd.html')
    soup = BeautifulSoup(r.text, 'html.parser')
    masterCardRate = [i.text for i in soup.select('body > div > div:nth-child(3) > div > div > div.panel-body > div:nth-child(4) > div.col-md-10.col-xs-7 > b')][0].replace('\xa0','').strip('0')
    visaRate = [i.text for i in soup.select('#comparison_huilv_Visa')][0].strip('0')
    jcbRate = [i.text for i in soup.select('#comparison_huilv_JCB')][0].strip('0')
    return [masterCardRate, visaRate, jcbRate]


def get_usd_rate():
    return 'USD Rate\n[BUY]\nMastercard: {} TWD\nVisa: {} TWD\nJCB: {} TWD\n[SELL]\n玉山: {} TWD'.format(get_usd_rete_from_3rd()[0], get_usd_rete_from_3rd()[1], get_usd_rete_from_3rd()[2], get_usd_rate_esunbank())


def get_usd_rate_esunbank():
    try:
        dayStr = (datetime.now(timezone.utc) + timedelta(hours = 8)).strftime('%Y-%m-%d')
        timeStr = (datetime.now(timezone.utc) + timedelta(hours = 8)).strftime('%H:%M:%S')
        headers = {'Content-Type': 'application/json',
                'Referer': 'https://www.esunbank.com.tw/bank/personal/deposit/rate/forex/foreign-exchange-rates',
                'Host': 'www.esunbank.com.tw'}
        r = requests.post(
            'https://www.esunbank.com.tw/bank/Layouts/esunbank/Deposit/DpService.aspx/GetForeignExchageRate',
            headers=headers,
            json={'day':dayStr,'time':timeStr})
        obj = json.loads(r.text)
        if not obj['d']:            
            return -1
        else:
            rates = json.loads(obj['d'])
            #result = rates['Rates'][0]['BBoardRate']
            result = list(filter(lambda x: x['Name'] == '美元', rates['Rates']))
            if not result:
                return -1
            else:
                return result[0]['BBoardRate']
    except Exception as e:
        logger.info('except "%s"', e)
        return -1
    return 


def get_ace_price():
    try:
        r = requests.get(
        'https://www.ace.io/polarisex/quote/getKline?baseCurrencyId=1&tradeCurrencyId=14&limit=1')
        obj = json.loads(r.text)
        if not obj['attachment']:
            return -1
        else:
            return float(obj['attachment'][0]['closePrice'])
    except:
        return -1


def get_bito_price(utc_now: datetime):
    try:
        to_time = int(utc_now.timestamp())
        from_time = int((utc_now - timedelta(seconds=1800)).timestamp())
        r = requests.get(
            'https://api.bitopro.com/v3/trading-history/usdt_twd?resolution=1m&from={}&to={}'.format(from_time, to_time))
        obj = json.loads(r.text)
        if obj['data'] is None:
            return -1
        else:
            return float(obj['data'][0]['close'])
    except:
        return -1


def get_max_price():
    try:
        headers = {'authority': 'max.maicoin.com',
                'pragma': 'no-cache',
                'cache-control': 'no-cache',
                'dnt': '1',
                'upgrade-insecure-requests': '1',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                            '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                'Chrome/86.0.4240.183 Safari/537.36',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7'}
        r = requests.get(
            'https://max.maicoin.com/trades/usdttwd/recent_trades',
            headers=headers)
        obj = json.loads(r.text)
        if not obj['data']:
            return -1
        else:
            return float(obj['data'][0]['price'])
    except:
        return -1


def get_usdt():
    utc_now = datetime.now(timezone.utc)
    bito_price = str(get_bito_price(utc_now))
    if bito_price == '-1':
        bito_price = '死了(?)'
    else:
        bito_price = bito_price + ' TWD'
    ace_price = str(get_ace_price())
    if ace_price == '-1':
        ace_price = '死了(?)'
    else:
        ace_price = ace_price + ' TWD'
    max_price = str(get_max_price())
    if max_price == '-1':
        max_price = '死了(?)'
    else:
        max_price = max_price + ' TWD'
    return 'USDT Price\nBitoPro: {}\nAce: {}\nMax: {}'.format(bito_price, ace_price, max_price)


def get_ust():
    r = requests.get(
            'https://api.moonpay.io/v3/currencies/ask_price?cryptoCurrencies=ust&fiatCurrencies=twd,usd&apiKey={}'.format(MOONPAYKEY))
    obj = json.loads(r.text)
    return obj['UST']['USD']


@cache.memoize(ttl=3, typed=True)
def get_gas():
    r = requests.get('https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={}'.format(ETHERSCANKEY), 
    headers = {'host': 'etherscan.io', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'})    
    try:
        obj = json.loads(r.text)
        return 'Low: {}\nAvg: {}\nHigh: {}\nfrom etherscan.io'.format(obj['result']['SafeGasPrice'], obj['result']['ProposeGasPrice'], obj['result']['FastGasPrice'])
    except:
        logger.info(r.text)


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False


def main():
    logger.info('Token = {}'.format(TOKEN))
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(CommandHandler('m', ask_mastercard_rate))
    dp.add_handler(CommandHandler('master', ask_mastercard_rate))
    dp.add_handler(CommandHandler('v', ask_visa_rate))
    dp.add_handler(CommandHandler('visa', ask_visa_rate))
    dp.add_handler(CommandHandler('j', ask_jcb_rate))
    dp.add_handler(CommandHandler('jcb', ask_jcb_rate))
    dp.add_handler(CommandHandler('r', ask_usd_rate))
    dp.add_handler(CommandHandler('rate', ask_usd_rate))
    dp.add_handler(CommandHandler('ace', ask_ace))
    dp.add_handler(CommandHandler('bito', ask_bito))
    dp.add_handler(CommandHandler('max', ask_max))
    dp.add_handler(CommandHandler('u', ask_usdt))
    dp.add_handler(CommandHandler('usdt', ask_usdt))
    dp.add_handler(CommandHandler('howdoyouturnthison', ask_combine))
    dp.add_handler(CommandHandler('ust', ask_ust))
    dp.add_handler(CommandHandler('esun', ask_usd_rate_esunbank))
    dp.add_handler(MessageHandler(Filters.text, msg_listener))
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(APPNAME, TOKEN))
    # updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
