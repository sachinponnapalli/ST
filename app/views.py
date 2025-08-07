from django.shortcuts import render
from algo.models import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from loguru import logger
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse , JsonResponse
from algo.api_utils import *

# Create your views here.
def Supertrend_algo(request):
    config = list(Config.select().where(Config.id == 1).dicts())
    config = config[0]
    return render(request, 'supertrend.html', {'sell_strike':config['sell_strike'] , 'buy_strike':config['buy_strike']})

@api_view()
def Stats(request):
    signal = list(Signal.select().dicts())
    if signal:
        return Response({"status": "success", "data": signal[0]})
    else:
        return Response({"status": "error", "message": "No signal data found."})
    

@csrf_exempt
def Update_config(request):
    try:
        if request.method == 'POST':
            sell_strike = request.POST.get('sell_strk')
            buy_strike = request.POST.get('buy_strk')
            try:
                query = Config.update(
                    sell_strike = sell_strike,
                    buy_strike = buy_strike,
                ).where(Config.id == 1)

                config_updated = query.execute()

                if config_updated > 0:
                    return JsonResponse({"success": True, "message": "Configuration updated successfully."}, status=200)
                else:
                    return JsonResponse({"success": False, "message": "No changes were made to the configuration or the record does not exist."}, status=200)
            except DoesNotExist:
                return JsonResponse({"success": False, "message": "Configuration with ID 1 does not exist."}, status=404)

        return JsonResponse({"message": "Invalid method", "success": False}, status=400)

    except Exception as e:
        return JsonResponse({"message": f"Error updating config: {str(e)}", "success": False}, status=500)



@api_view()
def Latest_data(request):
    candle = list(Latest_15_min_candle.select().dicts())
    if candle:
        return Response({"status": "success", "data": candle[0]})
    else:
        return Response({"status": "error", "message": "No Candle data found."})
    

def filter_algo_orders(orders):
    algo_orders = []  # filter orders with both ENTRY and EXIT remarks
    for order in orders:
        if "remarks" in order:
            if order['remarks'] == 'ENTRY' or order['remarks'] == 'EXIT':
                algo_orders.append(order)
    return algo_orders


@api_view()
def Update_RSI_orderbook(request):
    api_obj, error_msg = get_broker_api_obj()
    orderbook_data =  api_obj.get_order_book()
    if orderbook_data:
        orderbook_data = filter_algo_orders(orderbook_data)
    else:
        orderbook_data = []
    if orderbook_data:
        return Response(orderbook_data)