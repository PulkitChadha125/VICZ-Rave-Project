import datetime
import math
import pandas_ta as ta
from SmartApi.smartExceptions import DataException
import SmartApi
import pandas as pd
import requests
from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger
import pandas_ta as ta
import numpy as np
apikey="Sg2W3HFf"
secret="9e400a02-cf6a-4e03-887e-a436f413cd36"
USERNAME="S60612177"
PASSWORD="Akki123@"
totp_string="D45IFKPPHUFT3OHK7OAWMSLUCA"
pin = "1234"
smartApi=None


def login(api_key,username,pwd,totp_string):
    global smartApi
    print("login initiated")
    api_key = api_key
    username = username
    pwd = pwd
    smartApi = SmartConnect(api_key)
    try:
        token =totp_string
        totp = pyotp.TOTP(token).now()
    except Exception as e:
        logger.error("Invalid Token: The provided token is not valid.")
        raise e

    correlation_id = "abcde"
    data = smartApi.generateSession(username, pwd, totp)

    if data['status'] == False:
        logger.error(data)

    else:
        authToken = data['data']['jwtToken']

        refreshToken = data['data']['refreshToken']
        feedToken = smartApi.getfeedToken()

        res = smartApi.getProfile(refreshToken)
        smartApi.generateToken(refreshToken)
        res = res['data']['exchanges']

        print(smartApi.getProfile(refreshToken))


def get_ltp(segment,symbol,token):
    global smartApi
    res=smartApi.ltpData(segment,symbol,token)
    ltp_value = res['data']['ltp']
    return ltp_value

def symbolmpping():
    print("Symbol mapping ")
    url="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    d=requests.get(url).json()
    tokendf=pd.DataFrame.from_dict(d)
    tokendf['expiry']=pd.to_datetime(tokendf['expiry'])
    tokendf=tokendf.astype({'strike':float})
    print("instrument file generation")
    tokendf.to_csv("Instrument.csv")



def calculate_vortex(df, period_):
    df['high_shifted'] = df['high'].shift(1)
    df['low_shifted'] = df['low'].shift(1)

    # Calculate VMP (Vortex Movement Positive) and VMM (Vortex Movement Negative)
    df['VMP'] = np.abs(df['high'] - df['low_shifted'])
    df['VMM'] = np.abs(df['low'] - df['high_shifted'])

    df['TR'] = np.maximum((df['high'] - df['low']),
                          np.maximum(np.abs(df['high'] - df['close'].shift(1)),
                                     np.abs(df['low'] - df['close'].shift(1))))
    df['STR'] = df['TR'].rolling(window=period_).sum()
    df['VMP_sum'] = df['VMP'].rolling(window=period_).sum()
    df['VMM_sum'] = df['VMM'].rolling(window=period_).sum()
    # Calculate VIP and VIM
    df['VIP'] = df['VMP_sum'] / df['STR']
    df['VIM'] = df['VMM_sum'] / df['STR']
    df.drop(columns=['high_shifted', 'low_shifted', 'TR', 'VMP_sum', 'VMM_sum'], inplace=True)
    return df
def get_chop_zone_color(angle):
    if angle >= 5:
        return 'Turquoise'
    elif 3.57 <= angle < 5:
        return 'DarkGreen'
    elif 2.14 <= angle < 3.57:
        return 'PaleGreen'
    elif 0.71 <= angle < 2.14:
        return 'Lime'
    elif angle <= -5:
        return 'DarkRed'
    elif -5 < angle <= -3.57:
        return 'Red'
    elif -3.57 < angle <= -2.14:
        return 'Orange'
    elif -2.14 < angle <= -0.71:
        return 'LightOrange'
    else:
        return 'Yellow'








# Function to calculate Chop Zone including colors
def calculate_chop_zone(df):
    periods = 30  # same as in Pine Script
    pi = math.pi

    df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3

    df['highestHigh'] = df['high'].rolling(window=periods).max()
    df['lowestLow'] = df['low'].rolling(window=periods).min()

    df['span'] = 25 / (df['highestHigh'] - df['lowestLow']) * df['lowestLow']

    df['ema34'] = df['close'].ewm(span=34, adjust=False).mean()

    df['y2_ema34'] = (df['ema34'].shift(1) - df['ema34']) / df['hlc3'] * df['span']
    df['c_ema34'] = np.sqrt(1 + df['y2_ema34']**2)

    df['emaAngle_1'] = np.degrees(np.arccos(1 / df['c_ema34']))
    df['emaAngle'] = np.where(df['y2_ema34'] > 0, -df['emaAngle_1'], df['emaAngle_1'])

    df['chopZoneColor'] = df['emaAngle'].apply(get_chop_zone_color)

    return df
def get_historical_data(symbol, token, timeframe, segment,vortexlen,SpPeriod,SpMul):


    global smartApi
    try:
        historicParam = {
            "exchange": segment,
            "symboltoken": token,
            "interval": timeframe,
            "fromdate": "2024-02-08 09:00",
            "todate": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        }
        res = smartApi.getCandleData(historicParam)
        df = pd.DataFrame(res['data'], columns=['date', 'open', 'high', 'low', 'close', 'flag'])
        df['date'] = pd.to_datetime(df['date'])
        df = calculate_vortex(df, period_=vortexlen)
        df = calculate_chop_zone(df)
        colname = f'SUPERT_{int(SpPeriod)}_{SpMul}'
        colname2 = f'SUPERTd_{int(SpPeriod)}_{SpMul}'
        df["Supertrend Values"] = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=SpPeriod,
                                                multiplier=SpMul)[colname]
        df["Supertrend Signal"] = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=SpPeriod,
                                                multiplier=SpMul)[colname2]
        df.to_csv(f"{symbol}.csv")
        last_five_rows = df.tail(5)
        return last_five_rows

    except Exception as e:
        logger.exception(f"Historic Api failed: {e}")

def buy(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "BUY",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error",e)
        logger.error(f"Order placement failed: {e}")
        print(e)

def sell(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)


def SHORT(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "SELL",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)


def cover(symbol,token,quantity,exchange):
    try:
        orderparams = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": "BUY",
            "exchange": exchange,
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "quantity": quantity
        }
        # # Method 1: Place an order and return the order ID
        orderid = smartApi.placeOrder(orderparams)
        logger.info(f"PlaceOrder : {orderid}")
        print(orderid)
    except Exception as e:
        logger.exception(f"Order placement failed: {e}")
        print(e)
    except SmartApi.smartExceptions.DataException as e:
        print("error", e)
        logger.error(f"Order placement failed: {e}")
        print(e)
