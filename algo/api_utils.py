from datetime import date, datetime, timedelta , time as candle_count_time

# from config import trail_sl as tsl
from .config import *
import json
import requests
import pyotp
import os
from loguru import logger
import pandas as pd
from .brokers.shoonya.api import ShoonyaApiPy
from .brokers.flattrade.api import FlatTradeApiPy
import time as core_time
import pytz
from tabulate import tabulate
import filelock
# from models import Configuration , Tick_data

import time

BANKNIFTY_lock = filelock.FileLock('BANKNIFTY_signal.lock')
NIFTY_lock = filelock.FileLock('NIFTY_signal.lock')
FINNIFTY_lock = filelock.FileLock('FINNIFTY_signal.lock')
MIDCPNIFTY_lock = filelock.FileLock('MIDCPNIFTY_signal.lock')
SENSEX_lock = filelock.FileLock('SENSEX_signal.lock')

locks={"BANKNIFTY":BANKNIFTY_lock,
    "NIFTY":NIFTY_lock,
    "FINNIFTY":FINNIFTY_lock,
    "MIDCPNIFTY":MIDCPNIFTY_lock,
    "SENSEX":SENSEX_lock,
}

lot_size = {'BANKNIFTY':30,'NIFTY':75,'FINNIFTY':65 , 'MIDCPNIFTY':120, 'SENSEX':20}

tzinfo = pytz.timezone("Asia/Kolkata")
timestamp_format = "%Y-%m-%d %H:%M:%S"
todays_date = date.today()
now = datetime.now()
dayName = now.strftime("%A")
data_directory_path = f"_data/{todays_date}"
log_directory_path = f"_logs/{todays_date}"
# analysis_directory_path = f"_analysis/{todays_date}"
rsi_70_buy_path = f"{data_directory_path}/rsi_70_buy"
rsi_buy = f"{data_directory_path}/rsi_buy"
# rsi_otm_path = f"{data_directory_path}/rsi_otm" 
rsi_ha_30_buy = f"{data_directory_path}/rsi_ha_30_buy" 
rsi_ha_70_opposite_buy = f"{data_directory_path}/rsi_ha_70_opposite_buy" 
rsi_ha_70_sell_2 = f"{data_directory_path}/rsi_ha_70_sell_2" 
if os.name == "posix":
    os.environ['TZ'] = 'Asia/Kolkata'
    core_time.tzset()
os.makedirs(data_directory_path, exist_ok=True)
os.makedirs(log_directory_path, exist_ok=True)
for index in trading_index:
    os.makedirs(os.path.join(data_directory_path,index), exist_ok=True)

# os.makedirs(analysis_directory_path, exist_ok=True)
# os.makedirs(rsi_70_buy_path, exist_ok=True)
# os.makedirs(rsi_buy, exist_ok=True)
# # os.makedirs(rsi_otm_path, exist_ok=True)
# os.makedirs(rsi_ha_30_buy, exist_ok=True)
# os.makedirs(rsi_ha_70_opposite_buy, exist_ok=True)
# os.makedirs(rsi_ha_70_sell_2, exist_ok=True)



def get_user_id():
    credFile = open('./zerodhaCred.json')
    creds = json.load(credFile)
    user_id = creds["user_id"]
    return user_id


def get_totp(hash):
    totp = pyotp.TOTP(hash)
    otp_code = totp.now()
    return otp_code


def generateToken():
    try:
        cred = open('./zerodhaCred.json')
        api_cred = json.load(cred)

        user_id = api_cred["user_id"]
        password = api_cred["password"]
        totp_key = api_cred["totp_key"]
    except Exception as e:
        print('Problem in credentials : ', e)
        print('Please correct zerodhaCred.json and try again !!')
        exit(0)


    data1 = {
        "user_id":user_id,
        "password":password
    }
    r1 = requests.post('https://kite.zerodha.com/api/login', data = data1)
    assert r1.status_code == 200, f"Error in login:\n {r1.json()}"

    data2 = {
        "user_id":user_id,
        "request_id":r1.json()["data"]["request_id"],
        "twofa_value":get_totp(totp_key)
    }
    r2 = requests.post('https://kite.zerodha.com/api/twofa', data = data2)
    assert r2.status_code == 200, f"Error in login:\n {r2.json()}"

    return r2.cookies["enctoken"]


def get_enc_token(generate_token=True):
    try:
        tokenFile = open('./token.json')
        tokens = json.load(tokenFile)
        enc_token = tokens["enc_token"]
        if not generate_token:
            return enc_token
    except Exception as e:
        print('Problem in token.json : ', e)
        print('Generating new token.json ................... \n\n')
        new_token = generateToken()
        data = {
            'generated_on': str(datetime.now()),
            'enc_token':new_token
        }

        data = json.dumps(data, indent=2)
        with open('token.json', 'w') as file:
            file.write(data)
        return new_token
    
    header = {"Authorization" : f"enctoken {enc_token}"}
    r = requests.get('https://kite.zerodha.com/oms/user/profile/full', headers=header)

    if(r.status_code == 200):
        return enc_token    
    else:
        print('Token expired, generating new one.............')
        new_token = generateToken()
        data = {
            'generated_on': str(datetime.now()),
            'enc_token':new_token
        }

        data = json.dumps(data, indent=2)
        with open('token.json', 'w') as file:
            file.write(data)
        return new_token


def get_instruments(want_in_old_format=False, inst_class="OTM", hedging_inst=False):
    instruments = {}
    error_msg = ""
    try:
        if hedging_inst:
            instruments = json.load(open("instruments_dict_hedging.json"))
        else:
            instruments = json.load(open("instruments_dict.json"))
        assert instruments != {}, "empty"
        if want_in_old_format:
            ce_inst = {inst["tradingsymbol"]:inst["instrument_token"] for inst in instruments["CE"] if inst_class in inst["class"]}
            pe_inst = {inst["tradingsymbol"]:inst["instrument_token"] for inst in instruments["PE"] if inst_class in inst["class"]}
            ce_inst.update(pe_inst)
            return ce_inst, error_msg
    except Exception as e:
        error_msg = f"Error : instruments_dict.json : {e}"
    return instruments, error_msg


# def get_indicator_settings_dict(option_type):
#     option_type = option_type.lower()
#     if option_type == "ce":
#         settings = {
#             "supertrend_length" : supertrend_length_ce, 
#             "supertrend_multiplier" : supertrend_multiplier_ce,
#             "bollinger_band_length" : bollinger_band_length_ce,
#             "bollinger_band_sd" : bollinger_band_sd_ce,
#         }
#     elif  option_type == "pe":
#         settings = {
#             "supertrend_length" : supertrend_length_pe, 
#             "supertrend_multiplier" : supertrend_multiplier_pe,
#             "bollinger_band_length" : bollinger_band_length_pe,
#             "bollinger_band_sd" : bollinger_band_sd_pe,
#         }
#     else:
#         settings = {}
#     return settings

def round_to_nearest(num, nearest):
    return round(num / nearest) * nearest

def get_quantity(ticker, lot_size=lot_multiplier):
    for i in lot_size_dict:
        if ticker.startswith(i):
            return lot_size_dict[i] * lot_size


def get_log_filename(file):
    filename = os.path.basename(file)
    base, ext = os.path.splitext(filename)
    return os.path.join(log_directory_path, base+"_{time}.log")


def update_last_order_status(api_obj, orders_df, orders_file_path, emulation_context={}, position="short"):
    last_order = orders_df.iloc[-1].copy()

    order_details, is_ok = api_obj.get_order_details(last_order["order_id"], emulation_context=emulation_context)

    logger.success(order_details)
    keys_to_be_update = ["exchange_timestamp", "price", "trigger_price", "status"]
    values_to_be_update = [order_details["exchange_timestamp"], order_details["price"] or last_order["rt_price"], order_details["trigger_price"], order_details["status"]]
    last_order[keys_to_be_update] = list(values_to_be_update)

    if emulation_context.get("order_type") and emulation:
        last_order["order_type"] = emulation_context["order_type"]
    if order_details.get("trigger_price"):
        last_order["trigger_price"] = order_details["trigger_price"]
    if emulation_context.get("order_timestamp") and emulation:
        last_order["order_timestamp"] = emulation_context["order_timestamp"]

    if position == "long" and last_order["transaction_type"] == "SELL":
        buy_data = orders_df[(orders_df['transaction_type'] == 'BUY') & (orders_df['status'] == 'COMPLETE')]
        last_order["pnl"] = (last_order["price"] - buy_data.iloc[-1]["price"])
        # last_order["pnl"] = (last_order["price"] - buy_data.iloc[-1]["price"]) * (int(last_order["quantity"]) / lot_size_dict[trading_index])
    elif position == "short" and last_order["transaction_type"] == "BUY" and last_order["status"] == "COMPLETE":
        last_order["pnl"] = orders_df.iloc[-2]["price"] - last_order["price"]
    orders_df.iloc[-1] = last_order
    
    orders_df.to_csv(orders_file_path, index=False)
    return last_order


def update_orders_df(api_obj, order_id, renko_triggered_timestamp, renko_triggered_price_close, orders_df, orders_file_path, emulation_context={}, remark="", position="short"):
    if orders_df is None:
        logger.debug("Order Book Before Update :\n"+tabulate([], headers="keys", tablefmt="psql"))
    else:
        logger.debug("Order Book Before Update :\n"+tabulate(orders_df.tail(5), headers="keys", tablefmt="psql"))
    order_details, is_ok = api_obj.get_order_details(order_id, emulation_context=emulation_context)

    # recursive function for updating orders sheet again, if we are not getting response from kite api.
    if not is_ok:
        core_time.sleep(1)
        logger.error("Not getting orders details from kite API, order_details is empty")
        return update_orders_df(api_obj, order_id, renko_triggered_timestamp, renko_triggered_price_close, orders_df, orders_file_path)

    order_details["rt_timestamp"] = renko_triggered_timestamp
    order_details["rt_price"] = renko_triggered_price_close
    order_details["pnl"] = 0
    order_details["sl"] = 0
    order_details["t1"] = 0
    order_details["t2"] = 0
    order_details["remark"] = remark

    data_to_keep = [
        "order_id",
        "rt_timestamp",
        "order_timestamp",
        "exchange_timestamp",
        "tradingsymbol",
        "order_type",
        "transaction_type",
        "quantity",
        "rt_price",
        "trigger_price",
        "sl",
        "price",
        "t1",
        "t2",
        "pnl",
        "status",
        "remark",
    ]

    order_details = {k:order_details[k] for k in data_to_keep}
    order_details["order_timestamp"] = order_details["order_timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    order_details = [order_details]
    if orders_df is None:
        orders_df = pd.DataFrame(order_details)
    else:
        orders_df = pd.concat([orders_df, pd.DataFrame(order_details)])
    orders_df.to_csv(orders_file_path, index=False)
    update_last_order_status(api_obj, orders_df, orders_file_path, emulation_context=emulation_context, position=position)
    logger.debug("Order Book After Update :\n"+tabulate(orders_df.tail(5), headers="keys", tablefmt="psql"))
    return orders_df


def update_single_order_in_orders_df(api_obj, order_id, renko_triggered_timestamp, renko_triggered_price_close, orders_df, orders_file_path, emulation_context={}):
    order_details, is_ok = api_obj.get_order_details(order_id, emulation_context=emulation_context)
    last_order = orders_df.iloc[-1].copy()

    last_order["order_id"] = order_id
    last_order["order_type"] = order_details["order_type"]
    last_order["status"] = order_details["status"]
    last_order["price"] = order_details["price"]
    last_order["order_timestamp"] = order_details["order_timestamp"]
    # last_order["rt_timestamp"] = renko_triggered_timestamp
    last_order["rt_price"] = renko_triggered_price_close

    orders_df.iloc[-1] = last_order
    orders_df.to_csv(orders_file_path, index=False)
    update_last_order_status(api_obj, orders_df, orders_file_path, emulation_context=emulation_context)
    return orders_df


def check_for_unique_order_for_same_timestamp(orders_df, renko_triggered_timestamp):
    unique_order = True
    if orders_df is not None:
        last_order = orders_df.iloc[-1]
        # time_gap = datetime.now() - pd.to_datetime(last_order["order_timestamp"])
        orders_df["rt_timestamp"] = pd.to_datetime(orders_df["rt_timestamp"])
        same_timestamp_order_count = len(orders_df[orders_df["rt_timestamp"]==renko_triggered_timestamp])
        if same_timestamp_order_count > 0:
            unique_order = False
            logger.info(f"renko_triggered_timestamp={renko_triggered_timestamp}, same_timestamp_order_count={same_timestamp_order_count}")
        # elif time_gap.total_seconds() <= gap_between_orders_in_sec:
        #     unique_order = False
    logger.info("unique order found {}".format(unique_order))
    return unique_order


def get_df(file_path: str, exception_log: bool = True) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        if exception_log:
            logger.error(e)
        return None


def check_for_last_buy_order(api_obj, orders_df, orders_file_path, bypass_none=False) -> bool:
    if orders_df is None:
        return True if bypass_none else False
    else:
        last_order = orders_df.iloc[-1]
        if last_order["status"] != "COMPLETE":
            last_order = update_last_order_status(api_obj, orders_df, orders_file_path)
        return last_order["transaction_type"] == "BUY" and last_order["status"] == "COMPLETE"


def check_for_last_sell_order(api_obj, orders_df, orders_file_path, bypass_none=False) -> bool:
    if orders_df is None:
        return True if bypass_none else False
    else:
        last_order = orders_df.iloc[-1]
        if last_order["status"] != "COMPLETE":
            last_order = update_last_order_status(api_obj, orders_df, orders_file_path)
        return last_order["transaction_type"] == "SELL" and last_order["status"] == "COMPLETE"
    
    
def check_for_last_sell_order_and_sl_trigger_order(api_obj, orders_df, orders_file_path, bypass_none=False) -> bool:
    if orders_df is None:
        return [True,True] if bypass_none else [False,False]
    else:
        sell_order = orders_df.iloc[-2]
        last_order = orders_df.iloc[-1]
        if last_order["status"] != "COMPLETE":
            last_order = update_last_order_status(api_obj, orders_df, orders_file_path)
        last_sell_status =  sell_order["transaction_type"] == "SELL" and sell_order["status"] == "COMPLETE"
        sl_trigger_status = last_order["transaction_type"] == "BUY" and last_order["status"] in ['TRIGGER_PENDING', 'OPEN']
        return [last_sell_status, sl_trigger_status]


def check_for_last_open_limit_sell_order(api_obj, orders_df, orders_file_path) -> bool:
    if orders_df is None:
        return False
    else:
        last_order = orders_df.iloc[-1]
        if last_order["status"] != "COMPLETE":
            last_order = update_last_order_status(api_obj, orders_df, orders_file_path)
        return last_order["transaction_type"] == "SELL" and last_order["order_type"] == "LIMIT" and last_order["status"] == "OPEN_LC"


def validate_trading_start_time(delay_sec = 0):
    curr_time = datetime.now()
    trading_start_time = Configuration.get_field_value("trading_start_time")

    trading_start_datetime = datetime.combine(date.today(), trading_start_time) + timedelta(seconds=delay_sec)

    while curr_time < trading_start_datetime:
        time_difference =  trading_start_datetime - curr_time
        minutes, seconds = divmod(time_difference.seconds, 60) 
        logger.info(f"Script will auto start in {minutes} minutes and {seconds} seconds")
        core_time.sleep(1)
        curr_time = datetime.now()


def auto_terminate_decorator(func):
    def inner(*args):
        curr_time = datetime.now().time()
        if curr_time > trading_end_time:
            logger.info("Auto termination of the script because trading hours are closed")
            os._exit(1)
        return func(*args)
    return inner


def calculate_percent_points(price, percent_or_points):
    is_percent = "%" in str(percent_or_points)
    if is_percent:
        percent = float(percent_or_points.strip("% "))
        points = (price*percent)/100
    else:
        points = float(percent_or_points)
    return points



def get_broker_api_obj():
    error_msg = ""
    trading_broker_lw = 'flattrade'
    # emulation =  Configuration.get_field_value("emulation")
    try:
        # if trading_broker_lw == "shoonya":
        #     # api_obj = ShoonyaApiPy(emulation=emulation)
        #     api_obj = ShoonyaApiPy()
        if trading_broker_lw == "flattrade":
            # api_obj = ShoonyaApiPy(emulation=emulation)
            api_obj = FlatTradeApiPy(emulation=False)
        else:
            api_obj = None
            error_msg = f"Invalid trading broker : {trading_broker}"
    except Exception as e:
        api_obj = None
        error_msg = f"Error : {trading_broker} api : {str(e)}"
    return api_obj, error_msg


def get_target_stop_loss_price_dict(orders_df):
    price_dict = {"sl_price":float("inf"), "t1_price":0, "t2_price":0}
    if orders_df is not None:
        last_order = orders_df.iloc[-1]
        last_sell_price = last_order["price"]
        price_dict["sl_price"] = last_sell_price - calculate_percent_points(last_sell_price, stop_loss)
        price_dict["t1_price"] = last_sell_price + calculate_percent_points(last_sell_price, target1)
        price_dict["t2_price"] = last_sell_price + calculate_percent_points(last_sell_price, target2)
    return price_dict


def sl_price_modify_validation(old_sl_price, new_sl_price):
    validated = False
    if new_sl_price > old_sl_price:
        validated = True
    return validated


def update_target_stop_loss(orders_df, orders_file_path, price_dict = None):
    if orders_df is not None:
        last_order = orders_df.iloc[-1].copy()
        # print("here")
        if not price_dict:
            price_dict = get_target_stop_loss_price_dict(orders_df)
       
        if price_dict.get("sl_price"):
            last_order["sl"] = price_dict["sl_price"]
        if price_dict.get("t1_price"):
            last_order["t1"] = price_dict["t1_price"]
        if price_dict.get("t2_price"):
            last_order["t2"] = price_dict["t2_price"]
        orders_df.iloc[-1] = last_order
        orders_df.to_csv(orders_file_path, index=False)
        logger.info(f"Updated Target Stop Loss : {price_dict}")
    return orders_df


def trail_stop_loss(orders_df, orders_file_path, old_sl, new_sl, strategy_name):
    price_dict = {"sl_price":new_sl}
    trail_condition = sl_price_modify_validation(old_sl, new_sl)
    logger.info(f"Trailing SL : trail_condition={trail_condition}, old_sl={old_sl}, new_sl={new_sl}")
    if trail_condition:
        logger.info(f"Trailing SL : {old_sl} => {new_sl} based on {strategy_name}")
        # if strategy_name == "target1_hit_c2c":
        #     price_dict["t1_price"] = "0"
        update_target_stop_loss(orders_df, orders_file_path, price_dict=price_dict)


# trailing only when provided trail_sl points changed in ltp
def trail_sl_with_percent_change(df, orders_df, orders_file_path):
    last_data = df.iloc[-1]
    ltp = last_data["ltp"]
    # ltp = 579.7
    last_buy_order = orders_df.iloc[-1]
    # last_sl_order = orders_df.iloc[-1]

    if last_buy_order["transaction_type"] == "BUY":
        old_sl = last_buy_order["sl"]
        first_target = False
        if old_sl < last_buy_order["price"]:
            trail_sl = target1
            first_target = True
        else:
            trail_sl = tsl
        trail_sl_points = calculate_percent_points(last_buy_order["price"], trail_sl)
        # old_sl = last_sl_order["sl"]
        # old_sl = last_sl_order["trigger_price"]
        points_changed = ltp - old_sl
        time_gap = datetime.now() - datetime.strptime(last_data["datetime"], timestamp_format)
        is_latest_data = 0 <= time_gap.total_seconds() <= 10
        # is_latest_data = True
        if first_target:
            trail_condition = ltp >= (last_buy_order["price"]+trail_sl_points)
        else:
            
            trail_condition = points_changed >= (trail_sl_points*2)
            # print(trail_sl)
            # print("Second Target Trail condition ",trail_condition)
        
        logger.info(f"is_latest_data={is_latest_data}, time_gap={time_gap.total_seconds()}")
        logger.info(f"trail_condition={trail_condition}, points_changed={points_changed}, trail_sl_points={trail_sl_points}, ltp={ltp}, buy={last_buy_order['price']}, old_sl={old_sl}")
        if is_latest_data and trail_condition:
            if first_target:
                new_sl = last_buy_order["price"]
            else:
                new_sl = old_sl + trail_sl_points
            trail_stop_loss(orders_df, orders_file_path, old_sl, new_sl, "percent_change")





def getIndex(x):
    index = {
        'B': 'BANKNIFTY',
        'N':'NIFTY',
        'F':'FINNIFTY'
    }
    return index[x]


def save_state_json(data):
    with open("state.json", "w") as f:
        json.dump(data, f)


def get_state_json(init=False):
    if not os.path.exists("state.json") or init:
        data = {"tradingsymbol" : {}}
        save_state_json(data)
    return json.load(open("state.json"))


def check_for_holding_any_trade():
    state_json = get_state_json()
    holding_trade = True if state_json.get("tradingsymbol") else False
    return holding_trade


def read_json_file_with_retry(filename, max_attempts=5, delay_seconds=1):
    attempts = 0
    while attempts < max_attempts:
        try:
            with open(filename, 'r') as file:
                signal_data = json.load(file)
            return signal_data
        except Exception as e:
            print(f"Error reading file: {e}")
            attempts += 1
            if attempts < max_attempts:
                print(f"Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)


def write_json_file_with_retry(filename, data, max_attempts=5, delay_seconds=1):
    attempts = 0
    while attempts < max_attempts:
        try:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=2)
            return
        except Exception as e:
            print(f"Error writing to file: {e}")
            attempts += 1
            if attempts < max_attempts:
                print(f"Retrying in {delay_seconds} seconds...")
                time.sleep(delay_seconds)

def buy_sell_instruments(instruments_file_name, option_type = "all"):
    instruments = {}
    error_msg = ""
    try:
        instruments = json.load(open(f"{instruments_file_name}"))
        if option_type != "all":
            instruments = {key: value for key, value in instruments.items() if key[-6] == option_type}
        assert instruments != {}, "empty"
    except Exception as e:
        error_msg = f"Error : instruments.json : {e}"
    return instruments, error_msg


def kite_buy_sell_instruments(instruments_file_name, option_type = "all"):
    option_type = option_type.lower()
    instruments = {}
    error_msg = ""
    try:
        instruments = json.load(open(f"{instruments_file_name}"))
        if option_type != "all":
            instruments = dict(filter(lambda x: x[0].lower().endswith(option_type), instruments.items()))
        assert instruments != {}, "empty"
    except Exception as e:
        error_msg = f"Error : instruments.json : {e}"
    return instruments, error_msg


def check_stop_loss_hit(data, close, stop_loss_price):
    try:
        if data["status"] != "COMPLETE":
            return False
        last_buy_price = data['price']
        # is_percent = "%" in str(per)
        # if is_percent:
        #     per = float(per.strip("% "))
        #     limit_price = last_buy_price - (last_buy_price*per)/100
        # else:
        #     limit_price = last_buy_price - per
        logger.info(f"current_price = {close}, buy_price = {last_buy_price}, stop_loss_price = {stop_loss_price}")
        if(close <= stop_loss_price):
            logger.info("Stop Loss buy price ::", stop_loss_price, "Last buy price ::" , last_buy_price , ' :: Stop Loss order signal found !!')
            return True
        else:
            return False
    except Exception as e:
        return False
    


def check_target_hit(data, close, per):
    try:
        last_buy_price = data['price']
        target_price = data['t2']
        logger.success(f"current_price = {close}, buy_price = {last_buy_price}, target_price = {target_price}")
        if(close >= target_price):
            logger.info("Target buy price ::", target_price, "Last buy price ::" , last_buy_price , ' :: Target order signal found !!')
            return True
        else:
            return False
    except Exception as e:
        return False
    
def get_trading_symbol_ltp(trading_symbol):
    trading_broker_lw = trading_broker.lower()
    if trading_broker_lw == "shoonya":
        api_obj = ShoonyaApiPy(emulation=False)
        res, is_ok = api_obj.get_quotes(trading_symbol)
        ltp = float(res["lp"])
    return ltp


def get_enc_token():
    return  "rQZ1PnW1QGDHy1HyRR6sTWlK5c8/stou1PXNxic8SB4s2nRs4NWZkemaZ30L/LQiadIB5wUlL1DnVKTc3PVGkHvPXCDtI7/7JJFMj7QJA7HKcbmq4EUG5Q=="




def get_today_5_min_candle_count():
    # Market opens at 9:15 AM
    market_open = candle_count_time(9, 15)

    # Current time
    now = datetime.now().time()

    # Total minutes since market open
    minutes_passed = ((datetime.combine(datetime.today(), now) - 
                    datetime.combine(datetime.today(), market_open)).total_seconds()) / 60

    # Number of 5-minute candles so far today
    if minutes_passed >= 0:
        num_candles = int(minutes_passed // 5)
    else:
        num_candles = 0
    return num_candles + 1
    # print(f"Number of 5-minute candles so far today: {num_candles}")



def convert_data(data):
    # Create an empty list to store processed rows
    processed_data = []

    for item in data:
        processed_row = {
            'datetime': pd.to_datetime(item['time'], format='%d-%m-%Y %H:%M:%S'),
            'open': float(item['into']),
            'high': float(item['inth']),
            'low': float(item['intl']),
            'close': float(item['intc']),
        }
        processed_data.append(processed_row)

    # Create a DataFrame
    df = pd.DataFrame(processed_data)

    # Optional: sort the dataframe by datetime (if needed)
    df = df.sort_values('datetime').reset_index(drop=True)

    return df

def fetch_ins_ltp_data(api_obj,tradingsymbol):
    for i in range(1,5):
        quotes =  api_obj.get_quotes(token=tradingsymbol)
        if quotes[0]['stat'] =='Ok':
            ltp = (quotes[0]['lp'])
            return ltp
        else:
            time.sleep(1)
            print('didnt get ltp data')




def filter_completed_candles(df, datetime_col='datetime'):
    """
    Filters the DataFrame to include only fully completed 5-minute candles
    based on the current system time.

    Parameters:
    - df: pandas DataFrame with a datetime column.
    - datetime_col: name of the datetime column (default: 'datetime').

    Returns:
    - Filtered DataFrame with only completed 5-minute candles.
    """
    now = datetime.now()
    # Round current time down to nearest 5-minute interval
    rounded_time = now - timedelta(minutes=now.minute % 5,
                                   seconds=now.second,
                                   microseconds=now.microsecond)
    # Last fully completed 5-min candle
    last_complete_candle_time = rounded_time - timedelta(minutes=5)

    return df[df[datetime_col] <= last_complete_candle_time].copy()



def get_first_5_min_candle_shoonya(api,tradingsymbol):
    for i in range(1,5):
        lastBusDay = datetime.today()
        lastBusDay = lastBusDay.replace(hour=0, minute=0, second=0, microsecond=0)
        ret =  api.get_time_price_series(exchange='NFO', token=tradingsymbol, starttime=lastBusDay.timestamp(), interval=5)
        first_candle = ret[-1]
        if first_candle['stat'] =='Ok':
            return {'low':first_candle['intl'] , 'high':first_candle['inth']}
        else:
            time.sleep(1)
            print('didnt get first 5 min data')





def get_option_strike(price, option_type, position='atm', step=100):
    """
    Returns a single strike price (ITMx, OTMx, or ATM) based on the given parameters.

    :param price: float - Current underlying price (e.g., 45321 for BankNifty)
    :param option_type: str - "CE" for Call or "PE" for Put
    :param position: str - e.g., "itm5", "otm2", "atm"
    :param step: int - Strike interval (100 for BankNifty, 50 for Nifty)
    :return: int - strike price
    """
    position = position.lower()
    option_type = option_type.upper()

    # Round the price to nearest strike
    base_strike = round(price / step) * step

    if position == "atm":
        return base_strike

    if not (position.startswith("itm") or position.startswith("otm")):
        raise ValueError("Position must be 'atm', or start with 'itm' or 'otm' (e.g., 'itm5', 'otm2')")

    try:
        x = int(position[3:])
    except ValueError:
        raise ValueError("Invalid position format. Use like 'itm1', 'otm3', etc.")

    if option_type == "CE":
        if position.startswith("itm"):
            return base_strike - step * x
        else:  # otm
            return base_strike + step * x
    elif option_type == "PE":
        if position.startswith("itm"):
            return base_strike + step * x
        else:  # otm
            return base_strike - step * x
    else:
        raise ValueError("Invalid option_type. Use 'CE' or 'PE'.")