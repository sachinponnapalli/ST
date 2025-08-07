from utils import *
from loguru import logger
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from models import *



logger.info("--------- Supertrend Algo Script Started ---------")
logger.info("current time: " + str(datetime.now()))
# this script will be run in every one hour
api_obj, error_msg = get_broker_api_obj()

lastBusDay = datetime.today() - timedelta(days=10)
lastBusDay = lastBusDay.replace(hour=0, minute=0, second=0, microsecond=0)

index_data = api_obj.get_time_price_series(exchange="NSE", token="26000", starttime=lastBusDay.timestamp(), interval="60")

index_data_df = convert_data_to_df(index_data)

index_data_df.ta.supertrend(length=10, multiplier=3.5, append=True)

#-1 = bearish trend, 1 = bullish trend

second_last_candle = index_data_df.iloc[0]
last_candle = index_data_df.iloc[-1]

pre_trend = second_last_candle['SUPERTd_10_3.5']
current_trend = last_candle['SUPERTd_10_3.5']

logger.info(index_data_df)

logger.info(f"Previous Trend: {pre_trend}, Current Trend: {current_trend}") 


if current_trend != pre_trend:
    logger.info("Trend has changed, updating signal...")

    signal = Signal.select().where(Signal.id == 1)
    if signal.exists():
        logger.info("Signal object already exists, updating...")
        query = Signal.update(
                    datetime = last_candle.name,
                    open = last_candle['open'],
                    high = last_candle['high'],
                    low = last_candle['low'],
                    close = last_candle['close'],
                    supertrend = last_candle['SUPERT_10_3.5'],
                    trend = current_trend,
                    trade = False
                ).where(Signal.id == 1)

        query.execute()
    else:
        logger.info("Signal object does not exist, creating new one...")
        Signal.create(
            id = 1,
            datetime = last_candle.name,
            open = last_candle['open'],
            high = last_candle['high'],
            low = last_candle['low'],
            close = last_candle['close'],
            supertrend = last_candle['SUPERT_10_3.5'],
            trend = current_trend,
            trade = False
        )
    # Place your trading logic here
else:
    logger.info("No trend change detected, no action taken.")

