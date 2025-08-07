# -----------------------------------------------------------------------------------------------------------
# Note : Any changes to Global Configurations will only be reflected after restarting all files.
#        Any changes to Specific Configurations will only be reflected after restarting respective main file.
# -----------------------------------------------------------------------------------------------------------

from datetime import time


########################### Global Configurations ###########################

## key-value pair dictionary format, where key should be index name and value should be lot size.
lot_size_dict = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 40,
    "MIDCPNIFTY": 75,
}

## used when calculating quantities, i.e. quantity = lot_size * lot_multiplier w.r.t index name
lot_multiplier = 1

## when the emulation is True, no orders will be placed, and when the emulation is False, then only real orders will be placed.
emulation = True

## it will ask for confirmation whenever emulation will False
emulation_confirm_prompt = True

## save all logs into respective script file
save_log = True

## time in seconds for mandatory gap between the last order and the current order
# gap_between_orders_in_sec = 30

## trading time limits for automatically starting and closing buy and sell script.
# case 1: when the current time will be less than trading_start_time, and you triggered buy/sell script, even then the script will start automatically at given time period only.
# case 2: when the current time will be greater than trading_end_time, and the buy/sell script is running, in this case the script will stop automatically at given time period, and also it will sell all the last bought orders.
trading_start_time = time(9, 20, 5)
trading_end_time = time(14, 55, 0)

# index interval possible string values are "BANKNIFTY", "NIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX" etc
trading_index = ["BANKNIFTY"]
trading_broker = "shoonya"
# trading_broker = "zerodha"

## sell_short configuration
otm_sell = 0
nth_hedging_otm_instrument = 12
re_entry_trade = 1
revarsal_trade = 1

sl_points = 30
target1 = "10%"
trail_sl = "10%"
trigger_price_diff = 0.5

m2m_target = {
    "BANKNIFTY":1000,
    "NIFTY":950,
    "FINNIFTY":1000,
    "MIDCPNIFTY":1000,
}


shoonya_instruments_hedging_file = "shoonya_hedging_instruemnts.json"
shoonya_instruments_file = "shoonya_instruments.json"
instruments_file = "instruments.json"
# -----------------------------------------------------------------------------------------------------------
# Note : Any changes to Global Configurations will only be reflected after restarting all files.
#        Any changes to Specific Configurations will only be reflected after restarting respective main file.
# -----------------------------------------------------------------------------------------------------------