from NorenRestApiPy.NorenApi import NorenApi
import json
import pyotp
import pandas as pd
from datetime import datetime
import os
import requests
from loguru import logger

class ShoonyaApiPy(NorenApi):
    # def __init__(self, emulation=True):
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        self.curr_dir = __file__.replace(os.path.basename(__file__),"")
        # self.emulation = emulation
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

        # if not emulation:
        token_data = self.get_token()
        token_is_invalid = True
        if token_data:
            self.set_session(**token_data)
            token_is_invalid = False if self.get_user_details(token_data["userid"], token_data["usertoken"]) else True
        if token_is_invalid:
            cred = self.get_cred()
            res = self.login(**cred)
            self.save_token(cred["userid"], cred["password"], res['susertoken'])
            # print("Token Expired! Generated new shoonya usertoken.")
            logger.info("Token Expired! Generated new shoonya usertoken.")


    def parse_order_type(self, order_type):
        return self.master_order_type.get(order_type)


    def parse_transaction_type(self, transaction_type):
        return self.master_transaction_type.get(transaction_type)


    def get_cred(self):
        cred_path = os.path.join(self.curr_dir, "cred.json")
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
            exit(0)
    
        cred = json.load(open(cred_path))
        totp = pyotp.TOTP(cred.pop("twoFAKey"))    
        cred["twoFA"] = totp.now()
        return cred
    

    def save_token(self, userid, password, susertoken):
        token_path = os.path.join(self.curr_dir, "token.json")
        data = {
            "userid" : userid,
            "password" : password,
            "usertoken" : susertoken,
            "generated_at" : str(datetime.now())
        }
        with open(token_path,"w") as f:
            json.dump(data, f)


    def get_token(self):
        token_path = os.path.join(self.curr_dir, "token.json")
        data = []
        if os.path.exists(token_path):
            data = json.load(open(token_path))
            del data["generated_at"]
        return data
    

    def get_user_details(self, username, susertoken):
        url = f"https://api.shoonya.com/NorenWClientTP/UserDetails"      
        values = {"uid":username}  
        payload = 'jData=' + json.dumps(values) + f'&jKey={susertoken}'
        res = requests.post(url, data=payload)
        resDict = json.loads(res.text)
        if resDict['stat'] != 'Ok':            
            return None
        return resDict



    def place_order(self, tradingsymbol, transaction_type, order_type, quantity, price=0.0, trigger_price=None):
        if self.emulation:
            res = {
                "request_time": "10:48:03 20-05-2020", 
                "stat": "Ok", 
                "norenordno": "20052000000017"
            }
        else:
            res = super().place_order(
                buy_or_sell=self.parse_transaction_type(transaction_type),
                product_type="I",
                exchange='NFO',
                tradingsymbol=tradingsymbol,
                price_type=self.parse_order_type(order_type),
                quantity=quantity,
                discloseqty=0,
                price=price,
                trigger_price=trigger_price,
            )
        if res["stat"] == "Ok":
            return res["norenordno"], True
        else:
            return res, False


    def modify_order(self, order_id, tradingsymbol, order_type, quantity, price=0.0, trigger_price=None):
        if self.emulation:
            res =  {
                "request_time":"14:14:08 26-05-2020", 
                "stat":"Ok", 
                "result":"20052000000017" 
            }
        else:
            res = super().modify_order(
                orderno=order_id,
                exchange='NFO',
                tradingsymbol=tradingsymbol,
                newprice_type=self.master_order_type.get(order_type,"MKT"),
                newquantity=quantity,
                newprice=price,
                newtrigger_price=trigger_price,
            )
        if res["stat"] == "Ok":
            return res["result"], True
        else:
            return res, False


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
                "norentm": pd.to_datetime(datetime.now()),
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
                if emulation_context.get("price"):
                    res["prc"] = emulation_context["price"]
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
            "exchange_timestamp" : pd.to_datetime(order_details.get("exch_tm", pd.NaT), dayfirst=True),
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


    def get_quotes(self,exchange ,token):
        res = super().get_quotes(exchange=exchange, token=token)
        if res["stat"] == "Ok":
            return res, True
        else:
            return res, False



if __name__ == "__main__":
    api_obj = ShoonyaApiPy()
    order_id, is_ok = api_obj.place_order("BANKNIFTY23D0644800CE", "MARKET", "BUY", 10, 200)
    print(order_id, is_ok)

    order_id, is_ok = api_obj.modify_order(order_id, "BANKNIFTY23D0644800CE", "LIMIT", 50, 220)
    print(order_id, is_ok)

    order_details, is_ok = api_obj.get_order_details(order_id)
    print(order_details, is_ok)

    emulation_context = {"transaction_type" : "SELL", "order_type" : "MARKET", "status" : "COMPLETE"}
    order_details, is_ok = api_obj.get_order_details(order_id, emulation_context=emulation_context)
    print(order_details, is_ok)
    