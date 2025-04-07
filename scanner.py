import requests as rq
import redis, time, os
from tradingview_ta import TA_Handler, Interval
from worker.tasks import send_signal, create_table
from dotenv import load_dotenv
load_dotenv()

INTERVAL_IN_MINUTE = 1
PERCENT = 3
NUMBER_OF_COINS = 500
TIME_UPDATED_LIST_COINS = 60 # 1 hour

r_coins = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True,
)
r_open = redis.Redis(
    host="redis",
    port=6379,
    db=1,
    decode_responses=True,
)
r_coins.flushdb()
r_open.flushdb()

def get_list_coins():
    headers = {
        'X-CMC_PRO_API_KEY': os.getenv("API_KEY"),
        }
    body = {
        "limit": NUMBER_OF_COINS,
        }
    res = rq.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                  headers = headers,
                  params = body)
    
    data = res.json()
    coins_symbol = []

    for coin in data['data']:
        coins_symbol.append(coin['symbol'])

    return coins_symbol


def scanner(minute):
    print(f"Идёт {minute} минута...") # log
    coins_symbol = r_coins.smembers("coins")

    if len(coins_symbol) == 0:
        coins_symbol = get_list_coins()
        r_coins.sadd("coins", *coins_symbol) # updated every hour
        r_coins.expire("coins", TIME_UPDATED_LIST_COINS * 60)
        print("Обновлён список криптовалют") # log

    max_percent = 0
    best_coin = ""

    for coin in coins_symbol:
        handler = TA_Handler(
            screener="crypto",
            exchange="BINANCE",
            symbol=f"{coin}USDT",
            interval=Interval.INTERVAL_1_MINUTE,
        )

        try:
            analis = handler.get_analysis()
        except Exception as e:
            # print(f"Error: {coin}")
            continue

        indicators = analis.indicators
        open = indicators["open"]
        close_coin = indicators["close"]

        r_open.rpush(coin, open)
        if r_open.llen(coin) > INTERVAL_IN_MINUTE:
            r_open.lpop(coin)

        open_coin = float(r_open.lindex(coin, 0))

        pump = (close_coin - open_coin) / open_coin * 100
        dump = (open_coin - close_coin) / open_coin * 100

       if pump >= PERCENT:
    change = round(close_coin - base_open, 4)
    message = choice(PUMP_MESSAGES).format(
        coin=coin,
        percent=round(pump, 2)
    )
    message += f"\n💵 Изменение: ${change}\n📊 График: https://www.tradingview.com/symbols/{coin}USDT/"
    print(f"{coin} PUMP!!!")  # log
    send_signal.delay(coin, message)
    r_open.delete(coin)

elif dump >= PERCENT:
    change = round(base_open - close_coin, 4)
    message = choice(DUMP_MESSAGES).format(
        coin=coin,
        percent=round(dump, 2)
    )
    message += f"\n💵 Изменение: ${change}\n📊 График: https://www.tradingview.com/symbols/{coin}USDT/"
    print(f"{coin} DUMP!!!")  # log
    send_signal.delay(coin, message)
    r_open.delete(coin)

            
        if max(pump, dump) > max_percent:
            max_percent = max(pump, dump)
            best_coin = coin

    print(f"{max_percent} is {best_coin}") # log


create_table.delay()

minute = 0
while True:
    start_time = time.time()
    minute += 1
    scanner(minute)
    time.sleep(60 - time.time() + start_time) # work every minute
