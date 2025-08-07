from utils import get_df, update_orders_df, get_instruments, get_quantity, data_directory_path
from loguru import logger
from .api import ShoonyaApiPy


def get_shoonya_hedge_inst(kite_inst):
    hedging_instruments_dict, error_msg = get_instruments(hedging_inst=True)
    hedging_instruments_dict = hedging_instruments_dict[kite_inst[-2:]][0]
    res, is_ok = ShoonyaApiPy(False).get_quotes(hedging_instruments_dict["shoonya_instrument_token"])
    hedging_inst_ltp = float(res["lp"])
    return hedging_instruments_dict["shoonya_tradingsymbol"], hedging_inst_ltp


def buy_hedging_instrument(api_obj, kite_inst, renko_triggered_timestamp):
    hedging_inst, hedging_inst_ltp = get_shoonya_hedge_inst(kite_inst)
    quantity = get_quantity(kite_inst)

    logger.debug("Placing buy order for {} (Hedging Instrument)".format(hedging_inst))
    hedging_orders_file_path = "{}/{}_ORDERS_HEDGING.csv".format(data_directory_path, hedging_inst)
    hedging_orders_df = get_df(hedging_orders_file_path, exception_log=False)
    hedging_order_id, is_ok = api_obj.place_order(hedging_inst, "BUY", "MARKET", quantity)
    emulation_context = {"transaction_type" : "BUY", "order_type" : "MARKET", "quantity":quantity, "status" : "COMPLETE"}
    update_orders_df(api_obj, hedging_order_id, renko_triggered_timestamp, hedging_inst_ltp, hedging_orders_df, hedging_orders_file_path, emulation_context=emulation_context, position="long", remark="hedging")
    logger.debug("Buy order placed successfully (Hedging Instrument).")


def sell_hedging_instrument(api_obj, kite_inst, renko_triggered_timestamp):
    hedging_inst, hedging_inst_ltp = get_shoonya_hedge_inst(kite_inst)
    quantity = get_quantity(kite_inst)

    logger.debug("Placing sell order for {} (Hedging Instrument)".format(hedging_inst))
    hedging_orders_file_path = "{}/{}_ORDERS_HEDGING.csv".format(data_directory_path, hedging_inst)
    hedging_orders_df = get_df(hedging_orders_file_path, exception_log=False)
    hedging_order_id, is_ok = api_obj.place_order(hedging_inst, "SELL", "MARKET", quantity)
    emulation_context = {"transaction_type" : "SELL", "order_type" : "MARKET", "quantity":quantity, "status" : "COMPLETE"}
    update_orders_df(api_obj, hedging_order_id, renko_triggered_timestamp, hedging_inst_ltp, hedging_orders_df, hedging_orders_file_path, emulation_context=emulation_context, position="long", remark="hedging")
    logger.debug("Sell order placed successfully (Hedging Instrument).")