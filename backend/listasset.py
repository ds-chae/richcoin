# Python 3
# pip3 installl pyJwt
# pip install fastapi uvicorn
import jwt 
import uuid
import time
import requests
import hashlib
from urllib.parse import urlencode
import json
import math
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
# main.py
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from starlette.responses import HTMLResponse

# FastAPI app initialization
app = FastAPI(
    title="Asset Management API",
    description="API for managing cryptocurrency assets and orders",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API responses
class AssetResponse(BaseModel):
    currency: str
    balance: float
    locked: float
    avg_buy_price: float
    total_coin: float
    buy_amount: float
    current_amount: float
    current_price: float
    profit_loss: float
    profit_rate: float


class OrderResponse(BaseModel):
    market: str
    currency: str
    side: str
    buysell: str
    uuid: str
    price: float
    state: str
    volume: float
    remaining_volume: float
    locked: float


class SellOrderRequest(BaseModel):
    market: str
    side: str
    volume: float
    price: float
    ord_type: str = "limit"


class CancelOrderRequest(BaseModel):
    uuid: str


class UpdateAssetRequest(BaseModel):
    sell_price: float
    profit_rate: float


class SubmitOldAssetsRequest(BaseModel):
    updates: list[dict]  # List of {currency, sell_price, profit_rate}


class AddOldAssetRequest(BaseModel):
    currency: str
    balance: float
    locked: float
    avg_buy_price: float


class AddOldOrderRequest(BaseModel):
    market: str
    side: str
    price: float
    volume: float
    remaining_volume: float
    state: str


sell_prices = {}

profit_rate = {}
profit_rate['REI'] = 0.02
profit_rate['DBR'] = 0.03
profit_rate['ENA'] = 0.03
profit_rate['BMT'] = 0.05


old_assets = []
old_orders = []


class OneAsset:
    def __init__(self, asset):
        self.currency = asset['currency']
        self.balance = float(asset['balance'])
        self.locked = float(asset['locked'])
        self.total_coin = self.balance + self.locked
        self.avg_buy_price = float(asset['avg_buy_price'])
        self.tosell_price = 0
        self.toprofit_rate = 0
        self.current_price = 0
        self.profit_rate = 0
        self.profit_loss = 0
        self.buy_amount = 0
        self.current_amount = 0

    def __lt__(self, other):
        return self.currency < other.currency

def isSameAsset(s, other):
    return s.currency == other.currency and \
        s.balance == other.balance and \
        s.locked == other.locked and \
        s.avg_buy_price == other.avg_buy_price

class OneOrder:
    def __init__(self, order):
        markets = order['market'].split('-')
        self.market = markets[0]
        self.currency = markets[1]
        self.side = order['side']
        if self.side == 'ask':
            self.buysell = '매도'
        else:
            self.buysell = '매수'
        self.uuid = order['uuid']
        self.price = float(order['price'])
        self.state = order['state']
        self.volume=float(order['volume'])
        self.remaining_volume=float(order['remaining_volume'])
        self.locked=float(order['locked'])

    def __eq__(self, other):
        return isinstance(other, OneOrder) and \
            self.market == other.market and \
            self.currency == other.currency and \
            self.side == other.side and \
            self.uuid == other.uuid and \
            self.price == other.price and \
            self.state == other.state and \
            self.volume == other.volume and \
            self.remaining_volume == other.remaining_volume and \
            self.locked == other.locked

    def __lt__(self, other):
        if self.currency < other.currency:
            return True
        if self.side < other.side:
            return True
        if self.uuid < other.uuid:
            return True
        return False

# Set API parameters
accessKey = ''
secretKey = ''
apiUrl = 'https://api.bithumb.com'

pass_path = os.path.dirname(os.path.abspath(__file__)) + '/../pass.txt'
with open(pass_path, 'r') as f:
    tlines = f.readlines()
    for t in tlines:
        if t[-1] == '\n':
            t = t[:-1]
        tlist = t.split(' ')
        if tlist[0] == 'accessKey' and tlist[1] == '=':
            accessKey = tlist[2][1:-1]
        elif tlist[0] == 'secretKey':
            secretKey = tlist[2][1:-1]

# Generate access token
def get_access_header():
    payload = {
        'access_key': accessKey,
        'nonce': str(uuid.uuid4()),
        'timestamp': round(time.time() * 1000)
    }
    jwt_token = jwt.encode(payload, secretKey)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {
      'Authorization': authorization_token
    }
    return headers


def delete_order(uuid, ):
    param = dict(uuid=uuid)

    # Generate access token
    query = urlencode(param).encode()
    hash = hashlib.sha512()
    hash.update(query)
    query_hash = hash.hexdigest()
    payload = {
        'access_key': accessKey,
        'nonce': str(uuid.uuid4()),
        'timestamp': round(time.time() * 1000),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }
    jwt_token = jwt.encode(payload, secretKey)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {
        'Authorization': authorization_token
    }

    try:
        # Call API
        response = requests.delete(apiUrl + '/v1/order', params=param, headers=headers)
        # handle to success or fail
        print(response.status_code)
        print(response.json())
    except Exception as err:
        # handle exception
        print(err)


def sell_order(market, side, volume, price, ord_type='limit'): # 'bid'-buy 'ask'-sell
    # Set API parameters
    requestBody = dict(market=market, side=side, volume=volume, price=price, ord_type=ord_type)

    # Generate access token
    query = urlencode(requestBody).encode()
    hash = hashlib.sha512()
    hash.update(query)
    query_hash = hash.hexdigest()
    payload = {
        'access_key': accessKey,
        'nonce': str(uuid.uuid4()),
        'timestamp': round(time.time() * 1000),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }
    jwt_token = jwt.encode(payload, secretKey)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {
        'Authorization': authorization_token,
        'Content-Type': 'application/json'
    }

    try:
        # Call API
        response = requests.post(apiUrl + '/v1/orders', data=json.dumps(requestBody), headers=headers)
        # handle to success or fail
        print(response.status_code)
        print(response.json())
    except Exception as err:
        # handle exception
        print(err)



def get_assets():
    # Call API
    response = requests.get(apiUrl + '/v1/accounts', headers=get_access_header())
    # print(response.json())
    assets = []
    if response.status_code == 200 :
        rj = response.json()
        for r in rj:
            asset = OneAsset(r)
            get_current_price(asset)
            assets.append(asset)

    return assets


def get_current_price(asset):
    if(asset.currency == 'P') or (asset.currency == 'KRW'):
        return 0
    asset.current_price = 0
    url = "https://api.bithumb.com/v1/ticker?markets=KRW-" + asset.currency
    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200 :
        rj = response.json()
        asset.current_price = float(rj[0]['trade_price'])
    if asset.current_price != 0 :
        asset.total_coin = (asset.balance + asset.locked)
        asset.buy_amount = math.floor(asset.avg_buy_price * asset.total_coin)
        asset.current_amount = math.floor(asset.current_price * asset.total_coin)
        asset.profit_loss = math.floor(asset.current_amount - asset.buy_amount)
        asset.profit_rate = (asset.profit_loss / asset.buy_amount)
        print(asset.profit_rate)
        asset.profit_rate = round(asset.profit_rate, 4)
        print(asset.profit_rate)

def print_asset(asset):
    try:
        currency = asset.currency
        s = currency + ' '
        s += 'balance={}'.format(asset.balance) + ' '
        s += 'locked={}'.format(asset.locked) + ' '
        s += 'avg_buy_price={}'.format(asset.avg_buy_price) + ' '
        s += 'profit_loss={}'.format(asset.profit_loss) + ' '
        s += 'profit_rate={}'.format(asset.profit_rate)

        print(s)
    except:
        print(asset)

def get_orders():
    response = requests.get(apiUrl + '/v1/orders', headers=get_access_header())
    if response.status_code == 200 :
        orders = response.json()
    else:
        orders = {}

    return orders

def get_sell_price(currency, avg_buy_price):
    exp_sell_price = 0
    if currency in profit_rate :
        exp_sell_price = avg_buy_price * (1 + profit_rate[currency])
    else:
        if currency in sell_prices:
            exp_sell_price = sell_prices[currency]

    if exp_sell_price == 0 :
        return 0

    if exp_sell_price < 100:
        return math.floor(exp_sell_price * 100) / 100
    if exp_sell_price < 1000:
        return math.floor(exp_sell_price)
    return math.floor(exp_sell_price/5) * 5


def cancel_order(order):
    # Set API parameters
    param = dict(uuid=order.uuid)

    # Generate access token
    query = urlencode(param).encode()
    hash = hashlib.sha512()
    hash.update(query)
    query_hash = hash.hexdigest()
    payload = {
        'access_key': accessKey,
        'nonce': str(uuid.uuid4()),
        'timestamp': round(time.time() * 1000),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }
    jwt_token = jwt.encode(payload, secretKey)
    authorization_token = 'Bearer {}'.format(jwt_token)
    headers = {
        'Authorization': authorization_token
    }

    try:
        # Call API
        response = requests.delete(apiUrl + '/v1/order', params=param, headers=headers)
        # handle to success or fail
        print(response.status_code)
        print(response.json())
    except Exception as err:
        # handle exception
        print(err)



def cancel_order_ifnoteq(currency, sell_price, orderlist):
    cancelled = False
    for order in orderlist:
        if order.currency != currency:
            continue
        if order.side != 'ask':  # 매도가 아니면 패스
            continue
        if order.price != sell_price : # 지정된 가격과 다르면 주문 취소
            cancel_order(order)
            cancelled - True
    return cancelled


def sell_balance(assets, orderdict):
    cancel_count = 0
    for asset in assets:
        locked = asset.locked
        if asset.currency == 'P' or asset.currency== 'KRW':
            continue
        sell_price = get_sell_price(asset.currency, asset.avg_buy_price)
        if sell_price != 0 :
            if cancel_order_ifnoteq(asset.currency, sell_price, orderdict):
                cancel_count += 1
            else :
                if asset.balance > 0 :
                    sell_order('KRW-' + asset.currency, 'ask', asset.balance, sell_price)

    return cancel_count


def print_order(order):
    s = 'market={}'.format(order.market) + ' ' + 'currency={}'.format(order.currency) + ' '
    s += 'side={}'.format(order.side) + ',' + order.buysell
    s += 'uuid={}'.format(order.uuid) + ' '
    s += 'price={}'.format(order.price) + ' '
    s += 'state={}'.format(order.state) + ' '
    s += 'volume={}'.format(order.volume) + ' '
    s += 'remaining_volume={}'.format(order.remaining_volume) + ' '
    s += 'locked={}'.format(order.locked)
    print(s)



def different_assets(old_assets, assets):
    if len(old_assets) != len(assets):
        return True
    for i in range(len(old_assets)) :
        if not isSameAsset (old_assets[i], assets[i]):
            return True
    return False

def different_orders(old_orders, orderlist):
    if len(old_orders) != len(orderlist):
        return True
    for i in range(len(old_orders)):
        if old_orders[i] != orderlist[i]:
            return True
    return False


t = 0
def monitor_task():
    global t, old_assets, old_orders
    assets = get_assets()
    assets.sort()
    if different_assets(old_assets, assets) or (t % 10) == 0 :
        for asset in assets:
            print_asset(asset)
        old_assets = assets

    # 주문조회
    orderlist = []
    orders = get_orders()
    for order in orders:
        orderlist.append(OneOrder(order))
    orderlist.sort()

    if different_orders(old_orders, orderlist) or (t % 10) == 0 :
        for order in orderlist:
            print_order(order)
        old_orders = orderlist

    cancel_count = sell_balance(assets, orderlist)

    t += 1



# 백그라운드 스케줄러 설정
scheduler = BackgroundScheduler()
scheduler.add_job(monitor_task, 'interval', seconds=5)  # 매 5초마다 실행
scheduler.start()


# FastAPI Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint"""
    with open("../index.html", "rt", encoding="utf8") as htmlf:
        html = htmlf.read()
        return html


@app.get("/assets", response_model=list[AssetResponse])
async def get_assets_api():
    """Get all assets"""
    try:
        return [
            AssetResponse(
                currency=asset.currency,
                balance=asset.balance,
                locked=asset.locked,
                avg_buy_price=asset.avg_buy_price,
                total_coin=asset.total_coin,
                buy_amount=asset.buy_amount,
                current_amount=asset.current_amount,
                current_price=asset.current_price,
                profit_loss=asset.profit_loss,
                profit_rate=asset.profit_rate
            ) for asset in old_assets
        ]
    except Exception as e:
        return {"error": str(e)}


@app.get("/orders", response_model=list[OrderResponse])
async def get_orders_api():
    """Get all orders"""
    try:
        return [
            OrderResponse(
                market=order.market,
                currency=order.currency,
                side=order.side,
                buysell=order.buysell,
                uuid=order.uuid,
                price=order.price,
                state=order.state,
                volume=order.volume,
                remaining_volume=order.remaining_volume,
                locked=order.locked
            ) for order in old_orders
        ]
    except Exception as e:
        return {"error": str(e)}


@app.post("/sell-order")
async def create_sell_order(request: SellOrderRequest):
    """Create a sell order"""
    try:
        sell_order(
            market=request.market,
            side=request.side,
            volume=request.volume,
            price=request.price,
            ord_type=request.ord_type
        )
        return {"message": "Sell order created successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/cancel-order")
async def async_cancel_order(request: dict):
    """Cancel an order by UUID"""
    try:
        uuid = request.get("uuid")
        if not uuid:
            return {"success": False, "error": "Missing UUID field"}
        
        # Here you would typically call the exchange API to cancel the order
        # For now, we'll just remove it from old_orders list
        global old_orders
        for order in old_orders:
            if order.uuid == uuid :
                cancel_order(order)

        return {
            "success": True,
            "uuid": uuid,
            "message": f"Order {uuid} cancelled successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/sell-price/{currency}")
async def get_sell_price_api(currency: str, avg_buy_price: float):
    """Get sell price for a currency"""
    try:
        price = get_sell_price(currency, avg_buy_price)
        return {"currency": currency, "sell_price": price}
    except Exception as e:
        return {"error": str(e)}


@app.post("/submit-old-assets")
async def submit_old_assets(request: SubmitOldAssetsRequest):
    """Submit multiple old asset updates at once"""
    try:
        for update in request.updates:
            currency = update.get("currency")
            sell_price = update.get("sell_price")
            profit_rate_val = update.get("profit_rate")

            if not currency or not sell_price or profit_rate_val is None:
                return {"success": False, "error": "Invalid update format"}

            # Update the sell_prices dictionary
            sell_prices[currency] = sell_price
            
            # Update the profit_rate dictionary
            if profit_rate_val == 0:
                # Remove from dictionary if profit rate is 0
                if currency in profit_rate:
                    del profit_rate[currency]
            else:
                # Store the profit rate (convert percentage to decimal)
                profit_rate[currency] = profit_rate_val / 100.0
        
        return {"success": True, "message": "Old assets updated successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/add-old-asset")
async def add_old_asset(request: AddOldAssetRequest):
    """Add a new old asset to the list"""
    try:
        old_assets.append(OneAsset(request.dict()))
        return {"message": "Old asset added successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/add-old-order")
async def add_old_order(request: AddOldOrderRequest):
    """Add a new old order to the list"""
    try:
        old_orders.append(OneOrder(request.dict()))
        return {"message": "Old order added successfully"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/sell-prices")
async def get_sell_prices():
    """Get all sell prices dictionary"""
    return sell_prices


@app.get("/profit-rates")
async def get_profit_rates():
    """Get all profit rates dictionary"""
    return {k: v * 100 for k, v in profit_rate.items()}  # Convert back to percentage


@app.post("/update-sell-price")
async def update_sell_price(request: dict):
    """Update sell price and profit rate for a currency"""
    try:
        currency = request.get("currency")
        price = request.get("price")
        rate = request.get("rate")

        if not currency:
            return {"success": False, "error": "Missing currency field"}

        # Update the sell_prices dictionary only if price is not 0
        if price != 0:
            sell_prices[currency] = price
        elif currency in sell_prices:
            # Remove from dictionary if price is 0
            del sell_prices[currency]
        
        # Update the profit_rate dictionary only if rate is not 0
        if rate != 0:
            profit_rate[currency] = rate / 100.0  # Convert percentage to decimal
        elif currency in profit_rate:
            # Remove from dictionary if rate is 0
            del profit_rate[currency]
        
        return {
            "success": True,
            "currency": currency,
            "price": price,
            "rate": rate,
            "message": f"Updated {currency} with sell price {price} and profit rate {rate}%"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)