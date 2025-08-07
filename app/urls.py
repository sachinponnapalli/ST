from django.urls import path , include
from .views import *

urlpatterns = [
    path("supertrend-algo/",Supertrend_algo,name='supertrend_algo'),
    path("stats/",Stats,name='stats'),
    path("update_config/",Update_config,name='update_config'),
    path("latest-candle-data/",Latest_data,name='latest_candle_data'),
    path("update-rsi-orderbook/",Update_RSI_orderbook,name='update_orderbook'),

]