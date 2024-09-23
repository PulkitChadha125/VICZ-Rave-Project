import AngelIntegration,AliceBlueIntegration
import time
import traceback
from datetime import datetime, timedelta
import pandas as pd
result_dict={}
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta
AliceBlueIntegration.load_alice()
AliceBlueIntegration.get_nfo_instruments()


def convert_julian_date(date_object):
    year = date_object.year
    month = date_object.month
    day = date_object.day
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn


def get_delta(strikeltp,underlyingprice,strike,timeexpiery,riskfreeinterest,flag):
    # flag me  call  'c' ya put 'p'
    from py_vollib.black_scholes.greeks.analytical import delta
    iv= implied_volatility(price=strikeltp,S=underlyingprice,K=strike,t=timeexpiery,r=riskfreeinterest,flag=flag)
    value = delta(flag,underlyingprice,strike,timeexpiery,riskfreeinterest,iv)
    print("delta",value)
    return value


def option_delta_calculation(symbol,expiery,Tradeexp,strike,optiontype,underlyingprice,MODE):
    date_obj = datetime.strptime(Tradeexp, "%d-%b-%y")
    formatted_date = date_obj.strftime("%d%b%y").upper()
    optionsymbol = f"{symbol}{formatted_date}{strike}{optiontype}"


    fein = 'NFO'
    if symbol == "BANKEX" or symbol == "SENSEX":
        fein = "BFO"
        if MODE == "WEEKLY":
            date_obj = datetime.strptime(Tradeexp, '%d-%b-%y')
            formatted_date = f"{date_obj.strftime('%y')}{int(date_obj.strftime('%m'))}{date_obj.strftime('%d')}"
            optionsymbol=f"{symbol}{formatted_date}{strike}{optiontype}"

        #
        if MODE == "MONTHLY":
            date_obj = datetime.strptime(Tradeexp, '%d-%b-%y')
            formatted_date = f"{date_obj.strftime('%y')}{date_obj.strftime('%b').upper()}"
            optionsymbol=f"{symbol}{formatted_date}{strike}{optiontype}"
            print("delta optionsymbol: ", optionsymbol)

    optionltp=AngelIntegration.get_ltp(segment=fein, symbol=optionsymbol,
                             token=get_token(optionsymbol))
    if MODE == "WEEKLY":
        distanceexp = datetime.strptime(expiery, "%d-%b-%y")  # Convert string to datetime object if necessary
        print("MONTHLY: ", distanceexp)
    if MODE == "MONTHLY":
        distanceexp = datetime.strptime(expiery, "%d-%b-%y")  # Convert string to datetime object if necessary
        print("MONTHLY: ",distanceexp)
    t= (distanceexp-datetime.now())/timedelta(days=1)/365
    print("t: ",t)
    if optiontype=="CE":
        fg="c"
    else :
        fg = "p"
    value=get_delta(strikeltp=optionltp, underlyingprice=underlyingprice, strike=strike, timeexpiery=t,flag=fg ,riskfreeinterest=0.1)
    return value

def round_down_to_interval(dt, interval_minutes):
    remainder = dt.minute % interval_minutes
    minutes_to_current_boundary = remainder
    rounded_dt = dt - timedelta(minutes=minutes_to_current_boundary)
    rounded_dt = rounded_dt.replace(second=0, microsecond=0)
    return rounded_dt

def determine_min(minstr):
    min = 0
    if minstr == "1":
        min = 1
    if minstr == "3":
        min = 3
    if minstr == "5":
        min = 5
    if minstr == "15":
        min = 15
    if minstr == "30":
        min = 30

    return min

def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
def get_user_settings():
    global result_dict
    # Symbol,lotsize,Stoploss,Target1,Target2,Target3,Target4,Target1Lotsize,Target2Lotsize,Target3Lotsize,Target4Lotsize,BreakEven,ReEntry
    try:
        csv_path = 'TradeSettings.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        result_dict = {}
        # Symbol,EMA1,EMA2,EMA3,EMA4,lotsize,Stoploss,Target,Tsl
        for index, row in df.iterrows():
            # Symbol	Quantity	EXPIERY	BASESYMBOL	EntryTime	ExitTime	strikestep	StrikeNumber	USEEXPIERY	TradeExpiery	AliceblueTradeExp	PRODUCT_TYPE	Votex_length
            symbol_dict = {
                'Symbol': row['Symbol'],'Timeframe':row['Timeframe'],"Quantity":row['Quantity'],'EXPIERY': row['EXPIERY'], 'Votex_length':row['Votex_length'],
                 "BASESYMBOL": row['BASESYMBOL'],'exch':None,'EntryTime': row['EntryTime'], "ExitTime": row['ExitTime'],
                'strikestep': row['strikestep'], "StrikeNumber": row['StrikeNumber'],'USEEXPIERY': row['USEEXPIERY'], "TradeExpiery": row['TradeExpiery'],
                'AliceblueTradeExp': row['AliceblueTradeExp'], "PRODUCT_TYPE": row['PRODUCT_TYPE'],"InitialOnce":None,
                'FifteenHigh': None, "FifteenLow":None,"Bp":None,"Sp":None,"BUY":False,"SHORT":False,'Segement':row['Segement'],
                'Previoustrade':None,"RevTrade":False,"aliceexp": None,"producttype":row['PRODUCT_TYPE'],'TimeBasedExit':None,"segemntfetch":None,
                'Sp_Period':row['Sp_Period'],'Sp_Mul':row['Sp_Mul'],"runtime": datetime.now(),'TF_INT': row['TF_INT'],'UseSp': row['UseSp'],
                'secondlastcol':None,'secvip':None,'secvim':None,'thirdlastcol':None,'thirdvip':None,'thirdvim':None,'spval':None,'sptrade':None,
                'putstrike': None, 'callstrike': None,'Initial':None,"Fetchdelay":row['Fetchdelay']
            }
            result_dict[row['Symbol']] = symbol_dict
        print("result_dict: ", result_dict)
    except Exception as e:
        print("Error happened in fetching symbol", str(e))

get_user_settings()
def get_api_credentials():
    credentials = {}

    try:
        df = pd.read_csv('Credentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials


credentials_dict = get_api_credentials()
stockdevaccount=credentials_dict.get('stockdevaccount')
api_key=credentials_dict.get('apikey')
username=credentials_dict.get('USERNAME')
pwd=credentials_dict.get('pin')
totp_string=credentials_dict.get('totp_string')
AngelIntegration.login(api_key=api_key,username=username,pwd=pwd,totp_string=totp_string)

AngelIntegration.symbolmpping()


def get_token(symbol):
    df= pd.read_csv("Instrument.csv")
    row = df.loc[df['symbol'] == symbol]
    if not row.empty:
        token = row.iloc[0]['token']
        return token

def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')



def getstrikes_put(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None

    for i in range(step):
        result[int(ltp + strikestep * (i + 1))] = None
    return result

def getstrikes_call(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None
    for i in range(step):
        result[int(ltp - strikestep * (i + 1))] = None

    return result


def get_max_delta_strike(strikelist):
    max_delta = -float("inf")  # Initialize with negative infinity
    max_delta_strike = None
    for strike, delta in strikelist.items():
        if delta > max_delta:
            max_delta = delta
            max_delta_strike = strike
    return max_delta_strike

def round_to_nearest(number, nearest):
    return round(number / nearest) * nearest

def main_strategy():
    try:
        for symbol, params in result_dict.items():
            symbol_value = params['Symbol']
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            EntryTime = params['EntryTime']
            EntryTime = datetime.strptime(EntryTime, "%H:%M").time()
            ExitTime = params['ExitTime']
            ExitTime = datetime.strptime(ExitTime, "%H:%M").time()
            current_time = datetime.now().time()
            if isinstance(symbol_value, str):

                # AliceBlueIntegration.NormalSellExit(producttype=params["producttype"], exch="MCX",
                #                                     symbol=params['Symbol'], quantity=params['Quantity'])
                if  current_time>EntryTime and current_time < ExitTime and datetime.now() >= params["runtime"]:
                    params["segemntfetch"] = 'NSE'
                    if symbol_value == "BANKEX" or symbol_value == "SENSEX":
                        params["segemntfetch"] = "BSE"

                    if (params['BASESYMBOL'] != "BANKEX" and params['BASESYMBOL'] != "SENSEX"
                            and params['BASESYMBOL'] != "NIFTY" and params['BASESYMBOL'] != "BANKNIFTY"
                            and params['BASESYMBOL'] != "FINNIFTY" and params['BASESYMBOL'] != "MIDCPNIFTY"):
                        params["segemntfetch"] = "MCX"

                    if params['Fetchdelay']==True:
                        time.sleep(4)

                    spotdata=AngelIntegration.get_historical_data(symbol=params['Symbol'],token=get_token(params['Symbol']),
                                                                      timeframe=params["Timeframe"],segment=params["segemntfetch"],
                                                                  vortexlen=params["Votex_length"],SpPeriod=params["Sp_Period"],
                                                                  SpMul=params["Sp_Mul"])
                    last_row = spotdata.iloc[-1]
                    last_rowtime = last_row['date']  # Assuming this is a pandas Timestamp

                    given_time = last_rowtime.time()

                    curr_time = datetime.now()

                    if curr_time.hour == given_time.hour and curr_time.minute == given_time.minute:
                        second_last_row = spotdata.iloc[-2]
                        print("second_last_row time: ",second_last_row['date'])
                        secondlastclose=second_last_row['close']
                        params["secondlastcol"]=second_last_row['chopZoneColor']
                        params["secvip"]=second_last_row['VIP']
                        params["secvim"]=second_last_row['VIM']
                        params["spval"]=second_last_row['Supertrend Signal']

                        third_last_row = spotdata.iloc[-3]
                        print("third_last_row time : ", third_last_row['date'])
                        params["thirdlastcol"]= third_last_row['chopZoneColor']
                        params["thirdvip"]=third_last_row['VIP']
                        params["thirdvim "]= third_last_row['VIM']
                        params["spval"] = second_last_row['Supertrend Signal']

                    else:
                        second_last_row = spotdata.iloc[-1]
                        print("second_last_row time: ", second_last_row['date'])
                        secondlastclose = second_last_row['close']
                        params["secondlastcol"] = second_last_row['chopZoneColor']
                        params["secvip"] = second_last_row['VIP']
                        params["secvim"] = second_last_row['VIM']
                        params["spval"] = second_last_row['Supertrend Signal']

                        third_last_row = spotdata.iloc[-2]
                        print("third_last_row time : ", third_last_row['date'])
                        params["thirdlastcol"] = third_last_row['chopZoneColor']
                        params["thirdvip"] = third_last_row['VIP']
                        params["thirdvim "] = third_last_row['VIM']
                        params["spval"] = second_last_row['Supertrend Signal']


                    next_specific_part_time = datetime.now() + timedelta(
                        seconds=determine_min(str(params["TF_INT"])) * 60)
                    next_specific_part_time = round_down_to_interval(next_specific_part_time,
                                                                     determine_min(str(params["TF_INT"])))
                    print("Next datafetch time = ", next_specific_part_time)
                    params['runtime'] = next_specific_part_time

                if current_time > EntryTime and current_time < ExitTime:
                    if params['UseSp']==True:
                        if params['spval']==1:
                            params['sptrade']="BUY"

                        if params['spval']==-1:
                            params['sptrade']="SELL"

                    if params['UseSp'] == False:
                        params['sptrade'] = "BOTH"

    #                 buy
                    if params['Initial'] is None and (params['sptrade']=="BOTH" or params['sptrade']=="BUY") and params["secondlastcol"]=="Turquoise" and params["secvip"]>params["secvim"]:
                        params['Initial']="BUY"
                        if params['Segement'] == "MCX":
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                           token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Buy @ {symbol_value} @ {ltp} "
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalBuy(producttype=params["producttype"], exch=params['Segement'], symbol=params['BASESYMBOL'], quantity=params['Quantity'])



                        if params['Segement']=="NSE":
                            ltp=AngelIntegration.get_ltp(segment=params["segemntfetch"],symbol=params['Symbol'],token=get_token(params['Symbol']))
                            strikelist = getstrikes_call(
                                ltp=round_to_nearest(number=ltp, nearest=params['strikestep']),
                                step=params['StrikeNumber'],
                                strikestep=params['strikestep'])
                            print("Strikes to check for delta call:", strikelist)
                            for strike in strikelist:
                                date_format = '%d-%b-%y'

                                delta = float(
                                    option_delta_calculation(symbol=params['BASESYMBOL'],
                                                             expiery=str(params['TradeExpiery']),
                                                             Tradeexp=params['TradeExpiery'],
                                                             strike=strike,
                                                             optiontype="CE",
                                                             underlyingprice=ltp,
                                                             MODE=params["USEEXPIERY"]))
                                strikelist[strike] = delta

                            print("strikelist: ", strikelist)
                            final = get_max_delta_strike(strikelist)
                            print("Final strike: ", final)
                            params['callstrike'] = final

                            optionsymbol = f"NSE:{params['BASESYMBOL']}{params['TradeExpiery']}{final}CE"
                            params['exch'] = "NFO"
                            if symbol_value == "BANKEX" or symbol_value == "SENSEX":
                                params["exch"] = "BFO"
                            aliceexp = datetime.strptime(params['AliceblueTradeExp'], '%d-%b-%y')
                            aliceexp = aliceexp.strftime('%Y-%m-%d')
                            params['aliceexp'] = aliceexp
                            print("exch: ", params['exch'])

                            AliceBlueIntegration.buy(quantity=int(params["Quantity"]), exch=params['exch'],
                                                     symbol=params['BASESYMBOL'],
                                                     expiry_date=params['aliceexp'],
                                                     strike=params['callstrike'], call=True,
                                                     producttype=params["producttype"])


                            OrderLog=f"{timestamp} Buy @ {symbol_value} option contract ={optionsymbol}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)


#                   sell

                    if params['Initial']is None and (params['sptrade']=="BOTH" or params['sptrade']=="SELL") and params["secondlastcol"] == "DarkRed" and params["secvip"] < params["secvim"]:
                        params['Initial']="SHORT"
                        if params['Segement'] == "MCX":
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                           token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Sell @ {symbol_value} @ {ltp}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalSell(producttype=params["producttype"], exch=params['Segement'],
                                                           symbol=params['BASESYMBOL'], quantity=params['Quantity'])

                        if params['Segement'] == "NSE":
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                           token=get_token(params['Symbol']))
                            strikelist = getstrikes_put(
                                ltp=round_to_nearest(number=ltp, nearest=params['strikestep']),
                                step=params['StrikeNumber'],
                                strikestep=params['strikestep'])
                            print("Strikes to check for delta put:", strikelist)
                            for strike in strikelist:
                                date_format = '%d-%b-%y'

                                delta = float(
                                    option_delta_calculation(symbol=params['BASESYMBOL'],
                                                             expiery=str(params['TradeExpiery']),
                                                             Tradeexp=params['TradeExpiery'],
                                                             strike=strike,
                                                             optiontype="PE",
                                                             underlyingprice=ltp,
                                                             MODE=params["USEEXPIERY"]))
                                strikelist[strike] = delta

                            print("strikelist: ", strikelist)
                            final = get_max_delta_strike(strikelist)
                            print("Final strike: ", final)
                            params['putstrike'] = final
                            optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{final}PE"
                            params['exch'] = "NFO"
                            if symbol_value == "BANKEX" or symbol_value == "SENSEX":
                                params["exch"] = "BFO"

                            aliceexp = datetime.strptime(params['AliceblueTradeExp'], '%d-%b-%y')
                            aliceexp = aliceexp.strftime('%Y-%m-%d')
                            params['aliceexp'] = aliceexp
                            print("exch: ", params['exch'])
                            print("symbol: ", symbol)

                            AliceBlueIntegration.buy(quantity=int(params["Quantity"]), exch=params['exch'],
                                                     symbol=params['BASESYMBOL'],
                                                     expiry_date=params['aliceexp'],
                                                     strike=params['putstrike'], call=False,
                                                     producttype=params["producttype"])



                            OrderLog = f"{timestamp} Sell @ {symbol_value} option contract ={optionsymbol} "
                            print(OrderLog)
                            write_to_order_logs(OrderLog)

 #                 buyexit

                    if params['Initial']=="BUY" and (params["secvip"] < params["secvim"] or params["secondlastcol"] == "DarkRed"):

                        if params['Segement'] == "MCX":
                            params['Initial'] = None
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                           token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Buy Exit @ {symbol_value} @ {ltp}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalBuyExit(producttype=params["producttype"], exch=params['Segement'],
                                                           symbol=params['BASESYMBOL'], quantity=params['Quantity'])

                        if params['Segement'] == "NSE":
                            params['Initial'] = None
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["callstrike"], call=True,
                                                         producttype=params["producttype"])

                            OrderLog = f"{timestamp} Buy Exit @ {symbol_value} , exit contract ={params['callstrike']} contract ={params['BASESYMBOL']},strike={params['callstrike']}CE"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)

#                   sell exit
                    if params['Initial']=="SHORT" and (params["secvip"] > params["secvim"] or params["secondlastcol"] == "Turquoise"):

                        if params['Segement'] == "MCX":
                            params['Initial'] = None
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                           token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Sell Exit @ {symbol_value} @ {ltp}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalSellExit(producttype=params["producttype"], exch=params['Segement'],
                                                           symbol=params['BASESYMBOL'], quantity=params['Quantity'])

                        if params['Segement'] == "NSE":
                            params['Initial'] = None
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                         symbol=params['BASESYMBOL'],
                                                         expiry_date=params['aliceexp'],
                                                         strike=params["putstrike"], call=False,
                                                         producttype=params["producttype"])
                            OrderLog = f"{timestamp} Sell Exit @ {symbol_value} contract ={params['BASESYMBOL']},strike={params['putstrike']}PE"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)

                if current_time >= ExitTime :
                    if params['Initial'] == "BUY":

                        if params['Segement'] == "MCX":
                            params['Initial'] = None
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                               token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Time based Buy Exit @ {symbol_value} @ {ltp}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalBuyExit(producttype=params["producttype"],
                                                                   exch=params['Segement'],
                                                                   symbol=params['BASESYMBOL'],
                                                                   quantity=params['Quantity'])

                        if params['Segement'] == "NSE":
                            params['Initial'] = None
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                             symbol=params['BASESYMBOL'],
                                                             expiry_date=params['aliceexp'],
                                                             strike=params["callstrike"], call=True,
                                                             producttype=params["producttype"])

                            OrderLog = f"{timestamp} Time based Buy Exit @ {symbol_value} "
                            print(OrderLog)
                            write_to_order_logs(OrderLog)


                    if params['Initial'] == "SHORT":

                        if params['Segement'] == "MCX":
                            params['Initial'] = None
                            ltp = AngelIntegration.get_ltp(segment=params["segemntfetch"], symbol=params['Symbol'],
                                                               token=get_token(params['Symbol']))
                            OrderLog = f"{timestamp} Time based Sell Exit @ {symbol_value} @ {ltp}"
                            print(OrderLog)
                            write_to_order_logs(OrderLog)
                            AliceBlueIntegration.NormalSellExit(producttype=params["producttype"],
                                                                    exch=params['Segement'],
                                                                    symbol=params['BASESYMBOL'],
                                                                    quantity=params['Quantity'])

                        if params['Segement'] == "NSE":
                            params['Initial'] = None
                            AliceBlueIntegration.buyexit(quantity=params["Quantity"], exch=params['exch'],
                                                             symbol=params['BASESYMBOL'],
                                                             expiry_date=params['aliceexp'],
                                                             strike=params["putstrike"], call=False,
                                                             producttype=params["producttype"])
                            OrderLog = f"{timestamp} Time based Sell Exit @ {symbol_value} "
                            print(OrderLog)
                            write_to_order_logs(OrderLog)





    except Exception as e:
        print("Error in main strategy : ", str(e))
        traceback.print_exc()


while True:
    main_strategy()
    time.sleep(2)
