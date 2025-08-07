import json
import pyotp
import pandas as pd
import os
import requests
import requests_cache
# import zipfile
from time import sleep
from datetime import datetime, timedelta
# from NorenRestApiPy.NorenApi import NorenApi
import httpx
import asyncio
import hashlib
from urllib.parse import urlparse, parse_qs
import logging
session_cache = requests_cache.CachedSession('requests_cache', expire_after=12*60*60)
from NorenRestApiPy.NorenApi import NorenApi
import cryptography.fernet 
import base64
from concurrent.futures import ThreadPoolExecutor 
import time

def retry_decorator(func):
    def inner(*args, **kwargs):
        max_retry = 2
        retry_count = 0
        res = func(*args, **kwargs)
        while (res is None or len(res)<=0) and retry_count < max_retry:
            sleep(0.5)
            retry_count += 1
            print(f"\nUnable to get data from API, Retrying : {retry_count} \nres={res}, instrument_token={args[1]}, kwargs={kwargs}")
            res = func(*args, **kwargs)
        return res
    return inner


class FlatTradeApiPy(NorenApi):
    def __init__(self, emulation=True):
        self.root_url = 'https://piconnect.flattrade.in/PiConnectTP/'
        # NorenApi.__init__(self, host=f'{self.root_url}/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        NorenApi.__init__(self, host=self.root_url, websocket='wss://piconnect.flattrade.in/PiConnectWSTp/') #, eodhost='https://web.flattrade.in/chartApi/getdata/'

        
        # self.curr_dir = os.path.dirname(os.path.dirname(__file__))
        self.curr_dir = __file__.replace(os.path.basename(__file__),"")


        self.emulation = emulation
        self.master_order_type = {
            "LIMIT" : "LMT",
            "MARKET" : "MKT",
            "SL" : "SL-LMT",
            "LMT" : "LIMIT",
            "MKT" : "MARKET",
            "SL-LMT" : "SL",
        }
        self.master_transaction_type = {
            "BUY" : "B",
            "SELL" : "S",
            "B" : "BUY",
            "S" : "SELL",
        }
        
        if not emulation:
            token_data = self.get_token()
            token_is_invalid = True
            cred = self.get_cred()
            if cred is None:
                print("Credentials not found. Please check your cred.json file.")
                return None
            if token_data:
                key = base64.b64decode(token_data["key"]).decode()
                del token_data["key"]
                cipher = cryptography.fernet.Fernet(key)
                decoded_token = base64.b64decode(token_data["usertoken"]).decode()
                decrypted_token = cipher.decrypt(decoded_token).decode()
                token_data["usertoken"] = decrypted_token
                self.set_session(**token_data)
                token_is_invalid = False if self.get_user_details(cred["userid"], decrypted_token) else True
                print(token_is_invalid)
            if token_is_invalid:
                res = get_flattrade_token()
                key = cryptography.fernet.Fernet.generate_key() 
                cipher = cryptography.fernet.Fernet(key)
                encrypted_token =  cipher.encrypt(res.encode())
                key = base64.b64encode(key).decode('utf-8')
                encoded_token = base64.b64encode(encrypted_token).decode('utf-8')
                self.save_token(cred["userid"], cred["password"],encoded_token , key)
                print("Token Expired! Generated new Flattrade usertoken.")
                time.sleep(5)
                

    def check_user_login(self):
        token_data = self.get_token()
        user_valid = False
        cred = self.get_cred()
        if token_data:
            key = base64.b64decode(token_data["key"]).decode()
            del token_data["key"]
            
            cipher = cryptography.fernet.Fernet(key)
            decoded_token = base64.b64decode(token_data["usertoken"]).decode()
            decrypted_token = cipher.decrypt(decoded_token).decode()
            token_data["usertoken"] = decrypted_token
            user_valid = True if self.get_user_details(cred["userid"], decrypted_token) else False
        return user_valid
    
    def parse_order_type(self, order_type):
        return self.master_order_type.get(order_type)


    def parse_transaction_type(self, transaction_type):
        return self.master_transaction_type.get(transaction_type)


    def get_cred(self):
        # cred_path = "_data/cred_flattrade.json"
        cred_path = os.path.join(self.curr_dir, "cred.json")
        print(cred_path)
        try:
            cred = json.load(open(cred_path))
            user_id = cred["userid"]
            password = cred["password"]
            totp_key = cred["twoFAKey"]
            vc = cred["vendor_code"]
            app_key = cred["api_secret"]
            imei = cred["imei"]
        except Exception as e:
            print('Problem in credentials : ', e)
            print(f'Please correct {cred_path} and try again !!')
            return None
    
        cred = json.load(open(cred_path))
        totp = pyotp.TOTP(cred.pop("twoFAKey"))    
        cred["twoFA"] = totp.now()
        return cred
    

    def save_token(self, userid, password, susertoken , key):
        print("Saving token to file...")
        token_path = os.path.join(self.curr_dir, "token.json")
        data = {
            "userid" : userid,
            "password" : password,
            "usertoken" : susertoken,
            "key":key,
            "generated_at" : str(datetime.now())
        }
        with open(token_path,"w") as f:
            json.dump(data, f)



    def get_token(self):
        print("Getting token from file...")
        token_path = os.path.join(self.curr_dir, "token.json")
        data = []
        if os.path.exists(token_path):
            data = json.load(open(token_path))
            del data["generated_at"]
        return data
    

    def get_user_details(self, username, susertoken):
        url = f"{self.root_url}/UserDetails"      
        values = {"uid":username}  
        payload = 'jData=' + json.dumps(values) + f'&jKey={susertoken}'
        res = requests.post(url, data=payload)
        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None
        return resDict



    # def place_order(self, tradingsymbol, transaction_type, order_type, quantity, price=0.0, trigger_price=None, exchange="NFO",remarks="ENTRY"):
    #     if self.emulation:
    #         res = {
    #             "request_time": "10:48:03 20-05-2020", 
    #             "stat": "Ok", 
    #             "norenordno": "20052000000017"
    #         }
    #     else:
    #         while True:
    #             res = super().place_order(
    #                 buy_or_sell=self.parse_transaction_type(transaction_type),
    #                 # product_type="M" if exchange=="BFO" else "I",
    #                 # M-Normal Order , I- MIS Order
    #                 product_type="I",
    #                 exchange=exchange,
    #                 tradingsymbol=tradingsymbol,
    #                 # price_type=self.parse_order_type(order_type),
    #                 price_type=order_type,
    #                 quantity=quantity,
    #                 discloseqty=0,
    #                 price=price,
    #                 trigger_price=trigger_price,
    #                 remarks=remarks
    #             )
    #             if res is not None:
    #                 break
    #     if res["stat"] == "Ok":
    #         return res["norenordno"], True
    #     else:
    #         return res, False


    # def modify_order(self, order_id, tradingsymbol, order_type, quantity, price=0.0, trigger_price=None, exchange="NFO"):
    #     if self.emulation:
    #         res =  {
    #             "request_time":"14:14:08 26-05-2020", 
    #             "stat":"Ok", 
    #             "result":"20052000000017" 
    #         }
    #     else:
    #         res = super().modify_order(
    #             orderno=order_id,
    #             exchange=exchange,
    #             tradingsymbol=tradingsymbol,
    #             newprice_type=self.master_order_type.get(order_type,"MKT"),
    #             newquantity=quantity,
    #             newprice=price,
    #             newtrigger_price=trigger_price,
    #         )
    #     if res["stat"] == "Ok":
    #         return res["result"], True
    #     else:
    #         return res, False


    def get_order_details(self, order_id, format_order_details=True, emulation_context={}):
        if self.emulation or emulation_context.get("status", "COMPLETE").endswith("_LC"):
            res = {
                "stat": "Ok",
                "norenordno": "20052000000017",
                "uid": "DEMO1",
                "actid": "DEMO1",
                "exch": "NSE",
                "tsym": "",
                "qty": "0",
                "trantype": "B",
                "prctyp": "MKT",
                "ret": "DAY",
                "token": "7053",
                "pp": "2",
                "ls": "1",
                "ti": "0.05",
                "prc": "0",
                "prd": "M",
                "status": "PENDING",
                "rpt": "NewAck",
                "norentm": pd.to_datetime(datetime.now().replace(microsecond=0)),
                "remarks": "TEST Order"
            }
            if emulation_context:
                if emulation_context.get("transaction_type"):
                    res["trantype"] = self.parse_transaction_type(emulation_context["transaction_type"])
                if emulation_context.get("order_type"):
                    res["prctyp"] = self.parse_order_type(emulation_context["order_type"])
                if emulation_context.get("status"):
                    res["status"] = emulation_context["status"]
                if emulation_context.get("quantity"):
                    res["qty"] = emulation_context["quantity"]
                if emulation_context.get("trigger_price"):
                    res["trgprc"] = emulation_context["trigger_price"]
            res = [res]
        else:
            res = super().single_order_history(orderno=str(order_id))
                
        if isinstance(res, list):
            res = self.format_order_details(res[0]) if format_order_details else res
            return res, True
        else:
            return res, False

    
    def format_order_details(self, order_details):
        formatted_order_details = {
            "order_id" : order_details["norenordno"],
            "signal_timestamp" : "",
            "order_timestamp" : pd.to_datetime(order_details["norentm"], dayfirst=True),
            "exchange_timestamp" : pd.to_datetime(order_details.get("exch_tm", datetime.now().replace(microsecond=0)), dayfirst=True),
            "tradingsymbol" : order_details["tsym"],
            "transaction_type" : self.parse_transaction_type(order_details["trantype"]),
            "order_type" : self.parse_order_type(order_details["prctyp"]),
            "quantity" : order_details["qty"],
            "signal_price" : 0,
            "trigger_price" : float(order_details.get("trgprc",0)),
            "price" : float(order_details.get("avgprc",0)) or float(order_details["prc"]),
            "pnl" : 0,
            "status" : order_details["status"],
        }
        return formatted_order_details
    
    def get_orders_book(self, format_order_details=True, emulation_context={}):
        if self.emulation or emulation_context.get("status", "COMPLETE").endswith("_LC"):
            res = {
                "stat": "Ok",
                "norenordno": "20052000000017",
                "uid": "DEMO1",
                "actid": "DEMO1",
                "exch": "NSE",
                "tsym": "",
                "qty": "0",
                "trantype": "B",
                "prctyp": "MKT",
                "ret": "DAY",
                "token": "7053",
                "pp": "2",
                "ls": "1",
                "ti": "0.05",
                "prc": "0",
                "prd": "M",
                "status": "PENDING",
                "rpt": "NewAck",
                "norentm": pd.to_datetime(datetime.now().replace(microsecond=0)),
                "remarks": "TEST Order"
            }
            if emulation_context:
                if emulation_context.get("transaction_type"):
                    res["trantype"] = self.parse_transaction_type(emulation_context["transaction_type"])
                if emulation_context.get("order_type"):
                    res["prctyp"] = self.parse_order_type(emulation_context["order_type"])
                if emulation_context.get("status"):
                    res["status"] = emulation_context["status"]
                if emulation_context.get("quantity"):
                    res["qty"] = emulation_context["quantity"]
            res = [res]
            
        else:
            res = super().get_order_book()
                
        if isinstance(res, list):
            result = []
            if format_order_details:
                result.append([self.format_order_details(res[i]) for i in range(len(res))])
            else:
                result = res
            return result, True
        else:
            return res, False


    def get_exchange_from_token(self, token, exchange = "NFO"):
        try:    
            token = int(token)
            exchange = "NSE"
            if token in [26009, 26000, 26037, 26074]:
                exchange = "NSE"
            elif token in [1]:
                exchange = "BSE"
            elif token > 500000:
                exchange = "BFO"
        except:
            pass
        return exchange


    # def get_quotes(self, token, exchange = "NFO"):
    #     # while True:
    #     res = super().get_quotes(exchange=self.get_exchange_from_token(token, exchange), token=str(token))
    #         # if res is not None:
    #         #     break
    #     if res["stat"] == "Ok":
    #         return res, True
    #     else:
    #         return res, False
        

    def ltp(self, token, exchange = "NFO"):
        res, is_ok = self.get_quotes(token, exchange=exchange)
        if is_ok:
            new_res = {
                "request_time" : res["request_time"],
                "tradingsymbol" : res["tsym"],
                "last_trade_time" : res.get("ltt"),
                "last_price" : float(res["lp"]),
            }
            return new_res, True
        else:
            return res, False


    def instruments(self, exchange="NFO"):
        zip_file = f"{exchange}_symbols.txt.zip"
        txt_file = zip_file.replace(".zip","")
        res = session_cache.get(f"https://api.shoonya.com/{zip_file}", allow_redirects=True)

        with open(zip_file, 'wb') as f:
            f.write(res.content)
        import zipfile
        with zipfile.ZipFile(zip_file) as z:
            z.extractall()
        
        os.remove(zip_file)
        df = pd.read_csv(txt_file)
        df.rename(columns={
            "Token" : "instrument_token",
            "TradingSymbol" : "tradingsymbol",
            "Symbol" : "name",
            "Expiry" : "expiry",
            "StrikePrice" : "strike",
            "TickSize" : "tick_size",
            "LotSize" : "lot_size",
            "OptionType" : "instrument_type",
            "Instrument" : "segment",
            "Exchange" : "exchange",
        }, inplace=True)
        df["segment"].replace(to_replace={
            "FUTIDX" : f"{exchange}-FUT",
            "FUTSTK" : f"{exchange}-FUT",
            "OPTIDX" : f"{exchange}-OPT",
            "OPTSTK" : f"{exchange}-OPT",
        }, inplace=True)
        df = df[df["segment"] == "EQ"]
        df["name"] = df["name"].apply(lambda x : "SENSEX" if x in ["BSXOPT", "SX50FUT"] else x)
        df.dropna(inplace=True, axis=1)
        
        os.remove(txt_file)
        return df
    

    def get_timestamp(self, date):
        # Ensure `date` is a `datetime` object
        if isinstance(date, datetime):
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Convert `date` to `datetime` if it's a `date` object
            date = datetime.combine(date, datetime.min.time())
        
        return date.timestamp()
    

    def parse_interval(self, interval):
        interval = interval.replace("minute","")
        interval = interval if interval else 1
        return interval
    
    def cancel_order(self, orderno):
        return super().cancel_order(orderno)
    
    
    def format_candle_data_response(self, res, oi=False, return_df=False):
        if not res:
            return []

        col_to_be_drop = ["stat", "ssboe", "intoi"]
        if not oi:
            col_to_be_drop.append("oi")
        df = pd.DataFrame(res)
        df["time"] = pd.to_datetime(df["time"], dayfirst=True)
        df.drop(col_to_be_drop, axis=1, inplace=True)
        df.rename(columns={
            'time': 'date', 
            "into":"open", 
            "inth":"high",
            "intl":"low",
            "intc":"close",
            "intv":"volume",
            "v":"comb_volume"
            }, inplace=True)
        
        float_cols = list(df.columns)[1:]
        df[float_cols] = df[float_cols].astype(float)
        df = df.sort_values(by=["date"]).reset_index(drop=True)
        if return_df:
            return df
        else:
            return df.to_dict(orient="records")


    def historical_data(self, instrument_token, from_date, to_date, interval="minute", oi=False, return_df=False):
        from_date = self.get_timestamp(from_date)
        to_date = self.get_timestamp(to_date)
        interval = self.parse_interval(interval)
        res = self.get_time_price_series(exchange=self.get_exchange_from_token(instrument_token), token=str(instrument_token), starttime=from_date, interval=interval)
        return self.format_candle_data_response(res, oi, return_df)
    
     
    def getLastQuote(self,scrip):
        scripdata = super().get_quotes(exchange=scrip['exch'], token=scrip['token'])
        return scripdata
    
    def get_multiple_lastQuote(self,values):
        result =[]
        with ThreadPoolExecutor(max_workers=10) as exe:
            # Maps the method 'getLastQuote' with a list of values.
            result = exe.map(self.getLastQuote,values)
        final_res = {}
        for r in result:
            final_res[str(float(r["lp"]))] = [r["tsym"],r["token"]]
        return final_res
    


@retry_decorator
def get_past_candle_for_instrument(api_obj, token, interval="minute", no_of_days=4, return_df=False):
    return api_obj.historical_data(
        instrument_token=token,
        interval=interval,
        from_date=datetime.today() - timedelta(days=no_of_days),
        to_date=datetime.today(),
        oi=True,
        return_df=return_df,
    )



'''
###############################################################
---------------Enter Your Credentials Below--------------------
###############################################################
'''
curr_dir = os.path.dirname(os.path.dirname(__file__))

USER = "" # Flattrade user id
PWD = "" # Password
TOTP_KEY = "" 
API_KEY = ""
API_SECRET = ""
RURL = "https://127.0.0.1:5000/?"

###############################################################

HOST = "https://auth.flattrade.in"
API_HOST = "https://authapi.flattrade.in"

routes = {
    "session" : f"{API_HOST}/auth/session",
    "ftauth" : f"{API_HOST}/ftauth",
    "apitoken" : f"{API_HOST}/trade/apitoken",
}

headers = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Host": "authapi.flattrade.in",
    "Origin": f"{HOST}",
    "Referer": f"{HOST}/",
}
def get_cred():
        global USER , PWD,TOTP_KEY,API_KEY , API_SECRET

        c_path =  __file__.replace(os.path.basename(__file__),"")
        crd_path = os.path.join(c_path, "cred.json")
        
        cred_path =crd_path
        try:
            cred = json.load(open(cred_path))
            USER  = cred["userid"]
            PWD = cred["password"]
            TOTP_KEY = cred["twoFAKey"]
            # vc = cred["vendor_code"]
            API_KEY  = cred["api_key"]
            API_SECRET  = cred["api_secret"]
            # imei = cred["imei"]
        except Exception as e:
            print('Problem in credentials : ', e)
            print(f'Please correct {cred_path} and try again !!')
            return None
    
        # cred = json.load(open(cred_path))
        # totp = pyotp.TOTP(cred.pop("twoFAKey"))    
        # cred["twoFA"] = totp.now()
        # return cred
def encode_item(item):
    encoded_item = hashlib.sha256(item.encode()).hexdigest() 
    return encoded_item

async def get_authcode():

    async with httpx.AsyncClient(http2= True, headers= headers) as client:
        response =  await client.post(
                routes["session"]
            )
        if response.status_code == 200:
            sid = response.text

            response =  await client.post(
                routes["ftauth"],
                json = {
                        "UserName": USER,
                        "Password": encode_item(PWD),
                        "App":"",
                        "ClientID":"",
                        "Key":"",
                        "APIKey": API_KEY,
                        "PAN_DOB": pyotp.TOTP(TOTP_KEY).now(),
                        "Sid" : sid,
                        "Override": ""
                        }
                    )    
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("emsg") == "DUPLICATE":
                    response =  await client.post(
                        routes["ftauth"],
                        json = {
                                "UserName": USER,
                                "Password": encode_item(PWD),
                                "App":"",
                                "ClientID":"",
                                "Key":"",
                                "APIKey": API_KEY,
                                "PAN_DOB": pyotp.TOTP(TOTP_KEY).now(),
                                "Sid" : sid,
                                "Override": "Y"
                                }
                            )
                    if response.status_code == 200:
                        response_data = response.json()
                    else:
                        logging.info(response.text)

                redirect_url = response_data.get("RedirectURL", "")

                query_params = parse_qs(urlparse(redirect_url).query)
                if 'code' in query_params:
                    code = query_params['code'][0]
                    logging.info(code)
                    return code
            else:
                logging.info(response.text)
        else:
            logging.info(response.text)

async def get_apitoken(code):
    async with httpx.AsyncClient(http2= True) as client:
        response = await client.post(
            routes["apitoken"],
            json = {
                "api_key": API_KEY,
                "request_code": code, 
                "api_secret": encode_item(f"{API_KEY}{code}{API_SECRET}")
                }
            )
        
        if response.status_code == 200:
            token = response.json().get("token", "")            
            return token
        else:
            logging.info(response.text)

def get_flattrade_token():
    get_cred()
    code = asyncio.run(get_authcode())
    token = asyncio.run(get_apitoken(code))
    return token






if __name__ == "__main__":
    api_obj = FlatTradeApiPy(emulation=False)
    order_id, is_ok = api_obj.place_order("BANKNIFTY04SEP24C50900","BUY", "MARKET", 15)
    print(order_id, is_ok)

    # order_id, is_ok = api_obj.modify_order(order_id, "BANKNIFTY23D0644800CE", "LIMIT", 50, 220)
    # print(order_id, is_ok)

    # order_details, is_ok = api_obj.get_order_details(order_id)
    # print(order_details, is_ok)

    # emulation_context = {"transaction_type" : "SELL", "order_type" : "MARKET", "status" : "COMPLETE"}
    # order_details, is_ok = api_obj.get_order_details(order_id, emulation_context=emulation_context)
    # print(order_details, is_ok)

    # api_obj = FlatTradeApiPy(emulation=False)

    # print(api_obj.instruments())

    # curr_date = datetime.today()
    # from_date = curr_date - timedelta(days=1)
    # res = api_obj.historical_data("36840", from_date, curr_date, interval="minute", return_df=True)
    # print(res)

    # print(get_past_candle_for_instrument(api_obj, "26000", interval="5minute", return_df=True))

    # print(api_obj.ltp("36840"))
    # print(api_obj.ltp("26000"))