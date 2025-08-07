#this script will be run in every 15 min
from models import Signal , Config , Latest_15_min_candle
from loguru import logger
from utils import *

signal = list(Signal.select().where(Signal.id == 1).dicts())

if signal:
    logger.info("Signal data found")
    signal = signal[0]
    if signal['trade'] == False:
        api_obj, error_msg = get_broker_api_obj()
        
        lastBusDay = datetime.today() - timedelta(days=1)
        lastBusDay = lastBusDay.replace(hour=0, minute=0, second=0, microsecond=0)
        index_data = api_obj.get_time_price_series(exchange="NSE", token="26000", starttime=lastBusDay.timestamp(), interval="15")
        latest_15_min_candle = index_data[0]


        Latest_15_min_candle.truncate_table(restart_identity=True)
        Latest_15_min_candle.create(
            datetime = latest_15_min_candle['time'],
            open = latest_15_min_candle['into'],
            high = latest_15_min_candle['inth'],
            low = latest_15_min_candle['intl'],
            close = latest_15_min_candle['intc']
        )

        logger.info(f"Latest 15 min candle: {latest_15_min_candle}")

        if signal['trend'] == 1:
            #close > high
            logger.info("Bullish trend detected")
            logger.info(f"time = {latest_15_min_candle['time']} , latest_15_min_candle close = {latest_15_min_candle['intc']} , signal['high'] = {signal['high']}")
            
            if float(latest_15_min_candle['intc']) > signal['high']:
                logger.info("Bullish condition met, executing trade")

                ret = api_obj.get_quotes(exchange="NSE", token="26000")
                index_ltp = ret['lp']
                atm_strike = get_strikes(float(index_ltp),50,0)
                logger.info(f"ATM strike: {atm_strike}")

                config = list(Config.select().where(Config.id == 1).dicts())
                config = config[0]

                #sell trade execution
                sell_strike_position = config['sell_strike'] 

                req_sell_strike = abs(index_and_position['NIFTY'][sell_strike_position] - atm_strike)
                logger.info(f"sell order strike: {req_sell_strike}")
                sell_contracts = api_obj.searchscrip(exchange="NFO", searchtext=f"NIFTY {req_sell_strike} PE")

                now = datetime.now()
                current_day = now.weekday()  # Monday=0, ..., Friday=4
                current_time = now.time()

                if current_day == 4 or (current_day == 0 and current_time < datetime.strptime("14:00", "%H:%M").time()):
                    logger.info("its friday or monday before 2pm, executing latest first expiry")
                    sell_contract = sell_contracts['values'][0]
                else:
                    logger.info("its not friday or monday before 2pm, executing second expiry")
                    sell_contract = sell_contracts['values'][1]
                logger.info(f"sell_contract: {sell_contract}")
                #api_obj.place_order(sell_contract)  # pending , No clarity on how to place Normal order
                order_place_response = api_obj.place_order(buy_or_sell='S', product_type='M',
                        exchange='NFO', tradingsymbol=sell_contracts['tsym'], 
                        quantity=75, discloseqty=0 , price_type='MKT', price=0.0,
                        retention='DAY', remarks='ENTRY')
                
                logger.info(f"Order placed response: {order_place_response}")

                #sell order execution successful



                #buy trade execution
                buy_strike_position = config['buy_strike'] 

                req_buy_strike = abs(index_and_position['NIFTY'][buy_strike_position] - atm_strike)
                logger.info(f"buy order strike: {req_buy_strike}")
                buy_contracts = api_obj.searchscrip(exchange="NFO", searchtext=f"NIFTY {req_buy_strike} PE")

                now = datetime.now()
                current_day = now.weekday()  # Monday=0, ..., Friday=4
                current_time = now.time()

                if current_day == 4 or (current_day == 0 and current_time < datetime.strptime("14:00", "%H:%M").time()):
                    logger.info("its friday or monday before 2pm, executing latest first expiry")
                    buy_contract = buy_contracts['values'][0]
                else:
                    logger.info("its not friday or monday before 2pm, executing second expiry")
                    buy_contract = buy_contracts['values'][1]
                logger.info(f"buy_contract: {buy_contract}")
                #api_obj.place_order(buy_contract)  # pending , No clarity on how to place Normal order
                order_place_response = api_obj.place_order(buy_or_sell='B', product_type='M',
                        exchange='NFO', tradingsymbol=buy_contract['tsym'], 
                        quantity=75, discloseqty=0 , price_type='MKT', price=0.0,
                        retention='DAY', remarks='ENTRY')
                
                logger.info(f"Order placed response: {order_place_response}")

                query = Signal.update(trade=True).where(Signal.id == 1)
                query.execute()

        else:
            #close < low
            logger.info("Bearish trend detected")
            logger.info(f"time = {latest_15_min_candle['time']} , latest_15_min_candle close = {latest_15_min_candle['intc']} , signal['low'] = {signal['low']}")
            
            # if float(latest_15_min_candle['intc']) < signal['low']: 
            if 23000 < signal['low']: #888
                logger.info("Bearish condition met, executing trade")
                
                ret = api_obj.get_quotes(exchange="NSE", token="26000")
                index_ltp = ret['lp']
                atm_strike = get_strikes(float(index_ltp),50,0)
                logger.info(f"ATM strike: {atm_strike}")

                config = list(Config.select().where(Config.id == 1).dicts())
                config = config[0]
                
                #sell trade execution
                sell_strike_position = config['sell_strike'] 

                req_sell_strike = index_and_position['NIFTY'][sell_strike_position] + atm_strike
                logger.info(f"sell order strike: {req_sell_strike}")
                sell_contracts = api_obj.searchscrip(exchange="NFO", searchtext=f"NIFTY {req_sell_strike} CE")

                now = datetime.now()
                current_day = now.weekday()  # Monday=0, ..., Friday=4
                current_time = now.time()

                if current_day == 4 or (current_day == 0 and current_time < datetime.strptime("14:00", "%H:%M").time()):
                    logger.info("its friday or monday before 2pm, executing latest first expiry")
                    sell_contract = sell_contracts['values'][0]
                else:
                    logger.info("its not friday or monday before 2pm, executing second expiry")
                    sell_contract = sell_contracts['values'][1]
                logger.info(f"sell_contract: {sell_contract}")
                #api_obj.place_order(sell_contract)  # pending , No clarity on how to place Normal order
                order_place_response = api_obj.place_order(buy_or_sell='S', product_type='M',
                        exchange='NFO', tradingsymbol=sell_contract['tsym'], 
                        quantity=75, discloseqty=0 , price_type='MKT', price=0.0,
                        retention='DAY', remarks='ENTRY')
                
                logger.info(f"Order placed response: {order_place_response}")


                #sell order execution successful
                


                #buy trade execution
                buy_strike_position = config['buy_strike'] 

                req_buy_strike = index_and_position['NIFTY'][buy_strike_position] + atm_strike
                logger.info(f"buy order strike: {req_buy_strike}")
                buy_contracts = api_obj.searchscrip(exchange="NFO", searchtext=f"NIFTY {req_buy_strike} CE")

                now = datetime.now()
                current_day = now.weekday()  # Monday=0, ..., Friday=4
                current_time = now.time()

                if current_day == 4 or (current_day == 0 and current_time < datetime.strptime("14:00", "%H:%M").time()):
                    logger.info("its friday or monday before 2pm, executing latest first expiry")
                    buy_contract = buy_contracts['values'][0]
                else:
                    logger.info("its not friday or monday before 2pm, executing second expiry")
                    buy_contract = buy_contracts['values'][1]
                logger.info(f"buy_contract: {buy_contract}")
                #api_obj.place_order(buy_contract)  # pending , No clarity on how to place Normal order
                
                order_place_response = api_obj.place_order(buy_or_sell='B', product_type='M',
                        exchange='NFO', tradingsymbol=buy_contract['tsym'], 
                        quantity=75, discloseqty=0 , price_type='MKT', price=0.0,
                        retention='DAY', remarks='ENTRY')
                
                logger.info(f"Order placed response: {order_place_response}")

                query = Signal.update(trade=True).where(Signal.id == 1)
                query.execute()

                #buy trade execution successful 

        # Here you can add your trading logi

    else:
        logger.info("Trade already executed on this signal, no action needed")
else:
    logger.info("No signal data found")
