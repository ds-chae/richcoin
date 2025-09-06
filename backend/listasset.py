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
from fastapi import FastAPI, HTTPException, Cookie, Response, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
# main.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from starlette.responses import HTMLResponse

# File paths for JSON storage
SELL_PRICES_FILE = "sell_prices.json"
PROFIT_RATES_FILE = "profit_rates.json"

# Initialize dictionaries
sell_prices = {}
profit_rate = {}
auto_sell = True  # Global variable for auto sell toggle

# JWT secret key (in production, use a secure secret key)
secretKey = "your-secret-key-here-change-in-production"

def load_dictionaries_from_json():
    """Load sell_prices and profit_rate from JSON files"""
    global sell_prices, profit_rate
    
    # Load sell_prices
    if os.path.exists(SELL_PRICES_FILE):
        try:
            with open(SELL_PRICES_FILE, 'r') as f:
                sell_prices = json.load(f)
            print(f"Loaded sell_prices from {SELL_PRICES_FILE}: {sell_prices}")
        except Exception as e:
            print(f"Error loading sell_prices: {e}")
            sell_prices = {}
    else:
        sell_prices = {}
        print(f"Created new sell_prices dictionary")
    
    # Load profit_rate
    if os.path.exists(PROFIT_RATES_FILE):
        try:
            with open(PROFIT_RATES_FILE, 'r') as f:
                profit_rate = json.load(f)
            print(f"Loaded profit_rate from {PROFIT_RATES_FILE}: {profit_rate}")
        except Exception as e:
            print(f"Error loading profit_rate: {e}")
            profit_rate = {}
    else:
        profit_rate = {}
        print(f"Created new profit_rate dictionary")

def save_dictionaries_to_json():
    """Save sell_prices and profit_rate to JSON files"""
    try:
        # Save sell_prices
        with open(SELL_PRICES_FILE, 'w') as f:
            json.dump(sell_prices, f, indent=2)
        print(f"Saved sell_prices to {SELL_PRICES_FILE}: {sell_prices}")
    except Exception as e:
        print(f"Error saving sell_prices: {e}")
    
    try:
        # Save profit_rate
        with open(PROFIT_RATES_FILE, 'w') as f:
            json.dump(profit_rate, f, indent=2)
        print(f"Saved profit_rate to {PROFIT_RATES_FILE}: {profit_rate}")
    except Exception as e:
        print(f"Error saving profit_rate: {e}")

# FastAPI app initialization
app = FastAPI(
    title="Asset Management API",
    description="API for managing cryptocurrency assets and orders",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
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

sys_username=''
sys_password=''

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

login_path = os.path.dirname(os.path.abspath(__file__)) + '/../login.txt'
with open(login_path, 'r') as f:
    tlines = f.readlines()
    for t in tlines:
        if t[-1] == '\n':
            t = t[:-1]
        tlist = t.split(' ')
        if tlist[0] == 'username' and tlist[1] == '=':
            sys_username = tlist[2][1:-1]
        elif tlist[0] == 'password':
            sys_password = tlist[2][1:-1]

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
        #print(response.status_code)
        #print(response.json())
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
        #print(response.status_code)
        #print(response.json())
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
        #print(asset.profit_rate)
        asset.profit_rate = round(asset.profit_rate, 4)
        #print(asset.profit_rate)

def print_asset(asset):
    try:
        currency = asset.currency
        s = currency + ' '
        s += 'balance={}'.format(asset.balance) + ' '
        s += 'locked={}'.format(asset.locked) + ' '
        s += 'avg_buy_price={}'.format(asset.avg_buy_price) + ' '
        s += 'profit_loss={}'.format(asset.profit_loss) + ' '
        s += 'profit_rate={}'.format(asset.profit_rate)

        #print(s)
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
    if currency in sell_prices:
        exp_sell_price = sell_prices[currency]
    if exp_sell_price == 0 : # not defined by price
        if currency in profit_rate :
            exp_sell_price = avg_buy_price * (1 + profit_rate[currency])

    if exp_sell_price == 0 :
        return 0

    if exp_sell_price < 1:
        return math.floor(exp_sell_price * 10000) / 10000
    if exp_sell_price < 10:
        return math.floor(exp_sell_price * 1000) / 1000
    if exp_sell_price < 100:
        return math.floor(exp_sell_price * 100) / 100

    if exp_sell_price < 1000:
        return math.floor(exp_sell_price)

    if exp_sell_price < 5000:
        return math.floor(exp_sell_price / 5) * 5
    if exp_sell_price < 10000:
        return math.floor(exp_sell_price / 10) * 10
    if exp_sell_price < 50000:
        return math.floor(exp_sell_price / 50) * 50
    if exp_sell_price < 100000:
        return math.floor(exp_sell_price / 100) * 100
    if exp_sell_price < 500000:
        return math.floor(exp_sell_price / 500) * 500
    return math.floor(exp_sell_price / 1000) * 1000


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
    global auto_sell
    if not auto_sell:
        return 0

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
    #print(s)



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
scheduler.add_job(monitor_task, 'interval', seconds=1.5)  # 매 5초마다 실행
scheduler.start()

def remove_bracing_tags(html_content, str_to_find, open_tag, close_tag) : # 'class="sell-inputs"', '<div', '</div>'
    index_position = html_content.find(str_to_find)
    if index_position != -1 :
        si = index_position
        while si > 0 :
            if html_content[si:si+len(open_tag)] == open_tag :
                ei = si + 4
                while ei < len(html_content):
                    if html_content[ei:ei+len(close_tag)] == close_tag:
                        s0 = html_content[:si]
                        s1 = html_content[ei+len(close_tag)+1:]
                        html_content = s0 + s1
                        break
                    ei += 1
                break
            si = si - 1
    else:
        print('substring {} not found.'.format(str_to_find))

    return html_content


# FastAPI Endpoints
@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request, token: str = Cookie(None)):
    """Root endpoint that returns the HTML dashboard with login button if not authenticated - ROOT ENDPOINT"""
    try:
        # Check authentication status
        auth_status = check_auth_status(token)
        
        # Read index.html
        index_path = os.path.dirname(os.path.abspath(__file__)) + '/../index.html'
        with open(index_path, 'rt', encoding='utf8') as htmlf:
            html_content = htmlf.read()
            
            # Check if request is coming through nginx proxy
            nginx_header = request.headers.get('x-proxy-by', '')
            if 'Nginx' in nginx_header:
                # Remove port 8003 from API base URL when coming through nginx
                html_content = html_content.replace(':8003', '')
            
            # If not authenticated, add login button and hide logout button
            if not auth_status["authenticated"]:
                # Add login button to header
                html_content = html_content.replace(
                    '<button onclick="logout()" class="logout-btn">🚪 Logout</button>',
                    '<button onclick="showLoginModal()" class="login-btn" style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;">🔑 Login</button>'
                )
                
                # Remove delete buttons from sell table (price section)
                html_content = remove_bracing_tags(html_content, 'onclick="deleteSellData(', '<button', '</button>')

                # Remove auto button from sell table
                html_content = remove_bracing_tags(html_content, '"toggleSellAuto()"', '<button', '</button>')

                # Remove update button and input fields from sell table
                html_content = remove_bracing_tags(html_content, 'class="sell-inputs"', '<div', '</div>')

                # Remove cancel buttons from orders table
                html_content = remove_bracing_tags(html_content, 'onclick="cancelOrder', '<button', '</button>')

                # Add login modal HTML before closing body tag
                login_modal = '''
                <div id="loginModal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5);">
                    <div style="background-color: white; margin: 15% auto; padding: 20px; border-radius: 10px; width: 80%; max-width: 400px;">
                        <h2 style="text-align: center; margin-bottom: 20px;">🍶 SojuCoin Login</h2>
                        <form id="loginForm">
                            <div style="margin-bottom: 15px;">
                                <label for="username" style="display: block; margin-bottom: 5px; font-weight: bold;">Username:</label>
                                <input type="text" id="username" name="username" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;">
                            </div>
                            <div style="margin-bottom: 20px;">
                                <label for="password" style="display: block; margin-bottom: 5px; font-weight: bold;">Password:</label>
                                <input type="password" id="password" name="password" required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;">
                            </div>
                            <div style="text-align: center;">
                                <button type="submit" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">Login</button>
                                <button type="button" onclick="hideLoginModal()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Cancel</button>
                            </div>
                        </form>
                        <div id="loginMessage" style="margin-top: 15px; text-align: center; display: none;"></div>
                    </div>
                </div>
                '''
                
                # Add login modal JavaScript before closing body tag
                login_script = '''
                <script>
                    function showLoginModal() {
                        document.getElementById('loginModal').style.display = 'block';
                    }
                    
                    function hideLoginModal() {
                        document.getElementById('loginModal').style.display = 'none';
                        document.getElementById('loginMessage').style.display = 'none';
                    }
                    
                    document.getElementById('loginForm').addEventListener('submit', async function(e) {
                        e.preventDefault();
                        
                        const username = document.getElementById('username').value;
                        const password = document.getElementById('password').value;
                        const messageDiv = document.getElementById('loginMessage');
                        
                        try {
                            const formData = new FormData();
                            formData.append('username', username);
                            formData.append('password', password);
                            
                            const response = await fetch('/login', {
                                method: 'POST',
                                body: formData
                            });
                            
                            if (response.ok) {
                                messageDiv.textContent = 'Login successful! Refreshing page...';
                                messageDiv.style.color = '#28a745';
                                messageDiv.style.display = 'block';
                                
                                setTimeout(() => {
                                    window.location.reload();
                                }, 1000);
                            } else {
                                const errorData = await response.json();
                                messageDiv.textContent = errorData.detail || 'Login failed';
                                messageDiv.style.color = '#dc3545';
                                messageDiv.style.display = 'block';
                            }
                        } catch (error) {
                            messageDiv.textContent = 'Network error. Please try again.';
                            messageDiv.style.color = '#dc3545';
                            messageDiv.style.display = 'block';
                        }
                    });
                    
                    // Close modal when clicking outside
                    window.onclick = function(event) {
                        const modal = document.getElementById('loginModal');
                        if (event.target === modal) {
                            hideLoginModal();
                        }
                    }
                </script>
                '''
                
                # Insert modal and script before closing body tag
                html_content = html_content.replace('</body>', login_modal + login_script + '</body>')
            
            return HTMLResponse(html_content)
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Not Found</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #e74c3c; font-size: 1.2em; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>📄 File Not Found</h1>
            <div class="error">index.html file not found. Please check the file path.</div>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #e74c3c; font-size: 1.2em; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>❌ Error</h1>
            <div class="error">Error reading index.html: {str(e)}</div>
        </body>
        </html>
        """)


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if sys_username == '' or sys_password == '':
        raise HTTPException(status_code=401, detail="Invalid username or password")

    """Login endpoint to validate credentials and set a cookie"""
    if username == sys_username and password == sys_password:
        # Generate a JWT token with 7 days expiration for persistent login
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(days=7) # Token expires in 7 days
        }
        token = jwt.encode(payload, secretKey, algorithm="HS256")
        
        # Set the token as a cookie with 7 days expiration
        response = Response(content=f"Login successful! Token: {token}")
        response.set_cookie(
            key="token", 
            value=token, 
            httponly=True, 
            max_age=7*24*60*60,  # 7 days in seconds
            path="/",
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/refresh-token")
async def refresh_token(token: str = Cookie(None)):
    """Refresh token endpoint to extend session without requiring re-login"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        # Decode the current token
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        
        if username != sys_username:
            raise HTTPException(status_code=403, detail="Unauthorized user")
        
        # Create a new token with extended expiration
        new_payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(days=7) # Extend for another 7 days
        }
        new_token = jwt.encode(new_payload, secretKey, algorithm="HS256")
        
        # Set the new token as a cookie
        response = Response(content='{"success": true, "message": "Token refreshed successfully"}')
        response.headers['Content-Type'] = 'application/json'
        response.set_cookie(
            key="token", 
            value=new_token, 
            httponly=True, 
            max_age=7*24*60*60,  # 7 days in seconds
            path="/",
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/logout")
async def logout():
    """Logout endpoint to clear authentication cookie"""
    response = Response(content='{"success": true, "message": "Logged out successfully"}')
    response.headers['Content-Type'] = 'application/json'
    # Clear the authentication cookie by setting it to expire and empty value
    response.set_cookie(
        key="token", 
        value="", 
        expires=0, 
        httponly=True, 
        path="/",
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return response


def check_auth_status(token: str = None) -> dict:
    """Check authentication status and return user info"""
    if not token or token.strip() == "":
        return {"authenticated": False, "username": None}
    
    try:
        if len(token.strip()) < 10:  # Basic length check for JWT
            return {"authenticated": False, "username": None}
            
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        
        if username and username == sys_username:
            return {"authenticated": True, "username": username}
        else:
            return {"authenticated": False, "username": None}
            
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return {"authenticated": False, "username": None}
    except Exception:
        return {"authenticated": False, "username": None}











@app.get("/assets", response_model=list[AssetResponse])
async def get_assets_api():
    """Get all assets"""
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


@app.get("/orders", response_model=list[OrderResponse])
async def get_orders_api():
    """Get all orders"""
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


@app.post("/sell-order")
async def create_sell_order(request: SellOrderRequest, token: str = Cookie(None)):
    """Create a sell order"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

        sell_order(
            market=request.market,
            side=request.side,
            volume=request.volume,
            price=request.price,
            ord_type=request.ord_type
        )
        return {"message": "Sell order created successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/cancel-order")
async def async_cancel_order(request: dict, token: str = Cookie(None)):
    """Cancel an order by UUID"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/sell-price/{currency}")
async def get_sell_price_api(currency: str, avg_buy_price: float, token: str = Cookie(None)):
    """Get sell price for a currency"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

        price = get_sell_price(currency, avg_buy_price)
        return {"currency": currency, "sell_price": price}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/submit-old-assets")
async def submit_old_assets(request: SubmitOldAssetsRequest, token: str = Cookie(None)):
    """Submit multiple old asset updates at once"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

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
        
        # Save changes to JSON files
        save_dictionaries_to_json()
        
        return {"success": True, "message": "Old assets updated successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/add-old-asset")
async def add_old_asset(request: AddOldAssetRequest, token: str = Cookie(None)):
    """Add a new old asset to the list"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

        old_assets.append(OneAsset(request.dict()))
        return {"message": "Old asset added successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/add-old-order")
async def add_old_order(request: AddOldOrderRequest, token: str = Cookie(None)):
    """Add a new old order to the list"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

        old_orders.append(OneOrder(request.dict()))
        return {"message": "Old order added successfully"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/sell-prices")
async def get_sell_prices():
    """Get all sell prices dictionary"""
    return sell_prices


@app.get("/profit-rates")
async def get_profit_rates():
    """Get all profit rates dictionary"""
    return {k: v * 100 for k, v in profit_rate.items()}  # Convert back to percentage


@app.get("/auto-sell")
async def get_auto_sell(token: str = Cookie(None)):
    """Get the current auto_sell status"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != sys_username:
            raise HTTPException(status_code=403, detail="Unauthorized user")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"auto_sell": auto_sell}

@app.post("/toggle-auto-sell")
async def toggle_auto_sell(token: str = Cookie(None)):
    """Toggle the auto_sell status"""
    global auto_sell
    
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != sys_username:
            raise HTTPException(status_code=403, detail="Unauthorized user")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auto_sell = not auto_sell
    print(f"Auto sell toggled to: {auto_sell}")
    return {"auto_sell": auto_sell, "success": True}

@app.post("/update-sell-price")
async def update_sell_price(request: dict, token: str = Cookie(None)):
    """Update sell price and profit rate for a currency"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

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
        
        # Save changes to JSON files
        save_dictionaries_to_json()

        print("currency={}, price={}, rate={}".format(currency, price, rate))
        return {
            "success": True,
            "currency": currency,
            "price": price,
            "rate": rate,
            "message": f"Updated {currency} with sell price {price} and profit rate {rate}%"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/delete-sell-data")
async def delete_sell_data(request: dict, token: str = Cookie(None)):
    """Delete sell price and profit rate for a currency"""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, secretKey, algorithms=["HS256"])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized user")

        currency = request.get("currency")

        if not currency:
            return {"success": False, "error": "Missing currency field"}

        # Remove from sell_prices dictionary
        if currency in sell_prices:
            del sell_prices[currency]
        
        # Remove from profit_rate dictionary
        if currency in profit_rate:
            del profit_rate[currency]
        
        # Save changes to JSON files
        save_dictionaries_to_json()

        return {
            "success": True,
            "currency": currency,
            "message": f"Deleted sell data for {currency}"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/coinlist")
async def get_coinlist():
    """Get list of available coins with English and Korean names"""
    # Sample coin data as fallback
    fallback_coinlist = [
        {"symbol": "BTC", "name_en": "Bitcoin", "name_kr": "비트코인"},
        {"symbol": "ETH", "name_en": "Ethereum", "name_kr": "이더리움"},
        {"symbol": "XRP", "name_en": "Ripple", "name_kr": "리플"},
        {"symbol": "ADA", "name_en": "Cardano", "name_kr": "카르다노"},
        {"symbol": "DOT", "name_en": "Polkadot", "name_kr": "폴카닷"},
        {"symbol": "LINK", "name_en": "Chainlink", "name_kr": "체인링크"},
        {"symbol": "LTC", "name_en": "Litecoin", "name_kr": "라이트코인"},
        {"symbol": "BCH", "name_en": "Bitcoin Cash", "name_kr": "비트코인 캐시"},
        {"symbol": "EOS", "name_en": "EOS", "name_kr": "이오스"},
        {"symbol": "TRX", "name_en": "TRON", "name_kr": "트론"},
        {"symbol": "XLM", "name_en": "Stellar", "name_kr": "스텔라"},
        {"symbol": "VET", "name_en": "VeChain", "name_kr": "비체인"},
        {"symbol": "FIL", "name_en": "Filecoin", "name_kr": "파일코인"},
        {"symbol": "THETA", "name_en": "Theta", "name_kr": "쎄타"},
        {"symbol": "AAVE", "name_en": "Aave", "name_kr": "아베"},
        {"symbol": "SUSHI", "name_en": "SushiSwap", "name_kr": "스시스왑"},
        {"symbol": "SNX", "name_en": "Synthetix", "name_kr": "신세틱스"},
        {"symbol": "YFI", "name_en": "Yearn Finance", "name_kr": "이어n 파이낸스"},
        {"symbol": "COMP", "name_en": "Compound", "name_kr": "컴파운드"},
        {"symbol": "MKR", "name_en": "Maker", "name_kr": "메이커"}
    ]

    try:
        # Try to fetch from Bithumb API
        url = "https://api.bithumb.com/v1/market/all?isDetails=false"
        headers = {"accept": "application/json"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        coinjson = json.loads(response.text)
        coinlist = []
        
        for j in coinjson:
            try:
                market = j['market'][4:]  # Remove 'KRW-' prefix
                k_name = j['korean_name']
                e_name = j['english_name']
                coinlist.append({"symbol": market, "name_en": e_name, "name_kr": k_name})
            except (KeyError, IndexError) as e:
                print(f"Error processing coin data: {e}")
                continue
        
        # Return API data if we got any coins, otherwise fallback
        if coinlist:
            return coinlist
        else:
            print("No coins from API, using fallback data")
            return fallback_coinlist
            
    except Exception as e:
        print(f"Error fetching coin list from API: {e}")
        return fallback_coinlist


@app.get("/chart", response_class=HTMLResponse)
async def get_chart_page(coin: str = None):
    """Serve the chart page for the selected coin"""
    if not coin:
        coin = "BTC"  # Default to Bitcoin if no coin specified
    
    try:
        # Read chart.html file from project root
        with open("../chart.html", "r", encoding="utf-8") as f:
            chart_html = f.read()
        
        # Replace {coin} placeholder with actual coin value
        chart_html = chart_html.replace("{coin}", coin)
        
        return chart_html
    except FileNotFoundError:
        return HTMLResponse("<h1>Chart page not found</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading chart page: {str(e)}</h1>", status_code=500)

@app.get("/chart-data/minutes/{currency}")
async def get_chart_data_minutes(currency: str, unit: int = 5):
    """Get minute-level chart data for a currency"""
    try:
        url = f"https://api.bithumb.com/v1/candles/minutes/{unit}?market=KRW-{currency}&count=200"
        headers = {"accept": "application/json"}
        
        print(f"Fetching minute data for {currency} with unit {unit}")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}...")  # First 500 chars
        
        response.raise_for_status()
        
        data = response.json()
        print(f"Parsed data length: {len(data) if isinstance(data, list) else 'Not a list'}")
        return data
    except Exception as e:
        print(f"Error fetching minute data for {currency}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")

@app.get("/chart-data/days/{currency}")
async def get_chart_data_days(currency: str):
    """Get daily chart data for a currency"""
    try:
        url = f"https://api.bithumb.com/v1/candles/days?market=KRW-{currency}&count=200"
        headers = {"accept": "application/json"}
        
        print(f"Fetching daily data for {currency}")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}...")  # First 500 chars
        
        response.raise_for_status()
        
        data = response.json()
        print(f"Parsed data length: {len(data) if isinstance(data, list) else 'Not a list'}")
        return data
    except Exception as e:
        print(f"Error fetching daily data for {currency}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")


def get_minutes(currency, unit):
    import requests

    url = "https://api.bithumb.com/v1/candles/minutes/{}?market=KRW-{}&count=200".format(unit, currency)

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.text



def get_days(currency):
    import requests

    url = "https://api.bithumb.com/v1/candles/days?market=KRW-{}&count=200".format(currency)

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.text


if __name__ == "__main__":
    # Load dictionaries from JSON files at startup
    load_dictionaries_from_json()
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="error")