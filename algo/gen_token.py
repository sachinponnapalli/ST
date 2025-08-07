

from utils import  get_broker_api_obj 
from loguru import logger

try:
    api_obj, error_msg = get_broker_api_obj()
    logger.info(f"Broker API object created successfully: {api_obj}")
except Exception as e:
    logger.error(f"Error in getting broker API object: {e}")
    exit(1)
# user_details = api_obj.get_user_details(api_obj._NorenApi__accountid,api_obj._NorenApi__susertoken)
# logger.info(user_details)
# if user_details.get('stat') == "Ok":
#     logger.success(f"{user_details['uname']} API connected . generated token {api_obj._NorenApi__susertoken}")
