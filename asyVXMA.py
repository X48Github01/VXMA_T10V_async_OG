import asyncio
import ccxt.async_support as ccxt  
import time
import pandas as pd
pd.set_option('display.max_rows', None)
from line_notify import LineNotify 
import configparser
from datetime import datetime as dt
import warnings
warnings.filterwarnings('ignore')
from tabulate import tabulate
import logging
import util as indi
import mplfinance as mplf

logging.basicConfig(filename='log.log', format='%(asctime)s - %(message)s', level=logging.INFO)
print('benchmarking bot (Form Tradingview)By Vaz.')
print('Donate XMR : 87tT3DZqi4mhGuJjEp3Yebi1Wa13Ne6J7RGi9QxU21FkcGGNtFHkfdyLjaPLRv8T2CMrz264iPYQ2dCsJs2MGJ27GnoJFbm')
config = configparser.ConfigParser()
config.read('config.ini')

timedelay = config['KEY']['time_delay']
API_KEY = config['KEY']['API_KEY']
API_SECRET = config['KEY']['API_SECRET']
BNBCZ = {
    "apiKey": API_KEY,
    "secret": API_SECRET,
    'options': {
    'defaultType': 'future'
    },
    'enableRateLimit': True,
    'adjustForTimeDifference': True
    }
LINE_TOKEN = config['KEY']['LINE_TOKEN']
notify = LineNotify(LINE_TOKEN)
#Bot setting
USELONG     = bool(config['STAT']['Open_LONG'])
USESHORT    = bool(config['STAT']['Open_SHORT'])
USETP       = bool(config['STAT']['USE_TP'])
USESL       = bool(config['STAT']['USE_SL'])
Tailing_SL  = bool(config['STAT']['Tailing_SL'])
max_margin  = str(config['STAT']['Free_Balance'])
MIN_BALANCE = config['STAT']['MIN_BALANCE']
RISK        = config['STAT']['LOST_PER_TARDE']
Max_Size    = str(config['STAT']['MAX_Margin_USE_Per_Trade'])
TPRR1       = config['STAT']['RiskReward_TP1']
TPRR2       = config['STAT']['RiskReward_TP2']
TPPer       = int(config['STAT']['Percent_TP1'])
TPPer2      = int(config['STAT']['Percent_TP2'])
#STAT setting
SYMBOL_NAME = list((config['BOT']['SYMBOL_NAME'].split(",")))
Blacklist   = list((config['BOT']['Blacklist'].split(",")))
leverage    = int(config['BOT']['LEVERAGE'])
TF          = config['BOT']['TF']
tf = TF

aldynoti = False
aldynotiday = False

if MIN_BALANCE[0]=='$':
    min_balance=float(MIN_BALANCE[1:len(MIN_BALANCE)])
    print("MIN_BALANCE=",min_balance)
if Max_Size[0]=='$' :
    Max_Size = float(Max_Size[1:len(Max_Size)])
    print(f'Max_Margin/Trade: {Max_Size}$')
else:
    Max_Size = float(Max_Size)
    print(f'Max_Margin/Trade: {Max_Size}$')
    
if max_margin[0]=='$' :
    max_margin = float(max_margin[1:len(max_margin)])
    print(f'Margin Allow : {max_margin}$')
else:
    max_margin = float(max_margin)
    print(f'Margin Allow : {max_margin}$')

def candle(df,symbol,tf):
    data = df.tail(1000)
    rcs = {"axes.labelcolor":"none",
            "axes.spines.left": False,
            "axes.spines.right": False,
            "axes.axisbelow": False,
            "axes.grid": True,
            "grid.linestyle": ":",
            "figure.titlesize": "xx-large",
            "figure.titleweight": "bold",
            "figure.frameon": False,
            "figure.subplot.left":  0.0,
            "figure.subplot.right":  0.01,
            "figure.subplot.bottom": 0.0,
            "figure.subplot.top":    0.01,
            "figure.subplot.wspace": 0.01,
            "figure.subplot.hspace": 0.01,
            "figure.constrained_layout.use": True            
            }
    titles = f'{symbol}_{tf}'
    color = mplf.make_marketcolors(up='white',down='blue',wick='blue',edge='blue')   
    s = mplf.make_mpf_style(rc=rcs,marketcolors=color,figcolor='white',gridaxis='horizontal', y_on_right=True)
    try:
        vxma = mplf.make_addplot(data.vxma,secondary_y=False,color='red',width=1.5) #,savefig='candle.png'
        bPrice = mplf.make_addplot(data.buyPrice,secondary_y=False,color='green',type='scatter', marker='^', markersize=100) #,savefig='candle.png'
        sPrice = mplf.make_addplot(data.sellPrice,secondary_y=False,color='red',type='scatter', marker='v', markersize=100)
        mplf.plot(data,type='candle',title=titles,addplot=[vxma,bPrice,sPrice], style=s, volume=True, tight_layout=True, figratio=(10,8),datetime_format='%y/%b/%d %H:%M', xrotation=20, volume_panel=1, volume_yscale="linear")
    except AttributeError as e:
        print(f'{e}')
        mplf.plot(data,type='candle',title=titles, style=s, volume=True, tight_layout=True, figratio=(10,8),datetime_format='%y/%b/%d %H:%M', xrotation=20, volume_panel=1, volume_yscale="linear")
    notify.send(f'info : {titles}',image_path=('./candle.png'))
    return 

async def get_symbol(exchange):
    symbols = pd.DataFrame()
    syms = []
    print('fecthing Symbol of Top 10 Volume...')
    try:
        market = await exchange.fetchTickers(params={'type':'future'})
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        market = await exchange.fetchTickers(params={'type':'future'})
        # will retry
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        market = await exchange.fetchTickers(params={'type':'future'})
        # will retry
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        market = await exchange.fetchTickers(params={'type':'future'})
        # will retry
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        market = await exchange.fetchTickers(params={'type':'future'})
    if len(SYMBOL_NAME) > 0:
        for i in SYMBOL_NAME:
            symbo = i +'/USDT'
            syms.append(symbo)
    for x,y in market.items()    :
        if y['symbol'][len(y['symbol'])-4:len(y['symbol'])] == "USDT":
            symbols = symbols.append(y , ignore_index=True)
    symbols = symbols.set_index('symbol')
    symbols['datetime'] = pd.to_datetime(symbols['timestamp'], unit='ms', utc=True).map(lambda x: x.tz_convert('Asia/Bangkok'))
    symbols = symbols.sort_values(by=['quoteVolume'],ascending=False)
    symbols.drop(['timestamp','high','low','average'],axis=1,inplace=True)
    symbols.drop(['bid','bidVolume','ask','askVolume'],axis=1,inplace=True)
    symbols.drop(['vwap','open','baseVolume','info'],axis=1,inplace=True)
    symbols.drop(['close','previousClose','datetime'],axis=1,inplace=True)
    symbols = symbols.head(10)
    newsym = []
    if len(syms) > 0:
        for symbol in syms:
            newsym.append(symbol)
    for symbol in symbols.index:
        newsym.append(symbol)
    print(tabulate(symbols, headers = 'keys', tablefmt = 'grid'))
    newsym = list(dict.fromkeys(newsym))
    if len(Blacklist) > 0:
        for symbol in Blacklist:
            symbo = symbol +'/USDT'
            try:
                newsym.remove(symbo)
            except:
                continue
    print(f'Interested : {newsym}')
    return newsym 

async def fetchbars(symbol,timeframe,exchange):
    bars = 1502
    print(f"Benchmarking new bars for {symbol , timeframe , dt.now().isoformat()}")
    try:
        bars = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since = None, limit =bars)
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        bars = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since = None, limit =bars)
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        bars = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since = None, limit =bars)
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        bars = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since = None, limit =bars)
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        bars = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since = None, limit =bars)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).map(lambda x: x.tz_convert('Asia/Bangkok'))
    df = df.set_index('timestamp')
    return df
#set leverage
async def setleverage(symbol,exchange):
    try:
        await exchange.set_leverage(lev,symbol)
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        exchange.load_markets()
        lever = await exchange.fetch_positions_risk([symbol])
        for x in range(len(lever)):
            if (lever[x]['symbol']) == symbol:
                lev = round(lever[x]['leverage'],0)
                print(lev)
                await exchange.set_leverage(int(lev),symbol)
                break
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        lever = await exchange.fetch_positions_risk([symbol])
        for x in range(len(lever)):
            if (lever[x]['symbol']) == symbol:
                lev = round(lever[x]['leverage'],0)
                print(lev)
                await exchange.set_leverage(int(lev),symbol)
                break
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        lever = await exchange.fetch_positions_risk([symbol])
        for x in range(len(lever)):
            if (lever[x]['symbol']) == symbol:
                lev = round(lever[x]['leverage'],0)
                print(lev)
                await exchange.set_leverage(int(lev),symbol)
                break
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        lever = await exchange.fetch_positions_risk([symbol])
        for x in range(len(lever)):
            if (lever[x]['symbol']) == symbol:
                lev = round(lever[x]['leverage'],0)
                print(lev)
                await exchange.set_leverage(int(lev),symbol)
                break
    except:
        await asyncio.sleep(1)
        lever = await exchange.fetch_positions_risk([symbol])
        for x in range(len(lever)):
            if (lever[x]['symbol']) == symbol:
                lev = round(lever[x]['leverage'],0)
                print(lev)
                await exchange.set_leverage(int(lev),symbol)
                break
    return round(int(lev),0)

#Position Sizing
def buysize(df,balance,symbol,exchange):
    last = len(df.index) -1
    freeusd = float(balance['free']['USDT'])
    low = float(indi.swinglow(df))
    if RISK[0]=='$' :
        risk = float(RISK[1:len(RISK)])
    else :
        percent = float(RISK)
        risk = (percent/100)*freeusd
    amount = abs(risk  / (df['Close'][last] - low))
    qty_precision = exchange.amount_to_precision(symbol, amount)
    lot = qty_precision
    return float(lot)

def sellsize(df,balance,symbol,exchange):
    last = len(df.index) -1
    freeusd = float(balance['free']['USDT'])
    high = float(indi.swinghigh(df))
    if RISK[0]=='$' :
        risk = float(RISK[1:len(RISK)])
    else :
        percent = float(RISK)
        risk = (percent/100)*freeusd
    amount = abs(risk  / (high - df['Close'][last]))
    qty_precision = exchange.amount_to_precision(symbol, amount)
    lot = qty_precision
    return float(lot)
#TP with Risk:Reward    
def RRTP(df,direction,step,price):
    if direction :
        low = float(indi.swinglow(df))
        if step == 1 :
            target = price *(1+((price-low)/price)*float(TPRR1))
        if step == 2 :
            target = price *(1+((price-low)/price)*float(TPRR2))
    else :
        high = float(indi.swinghigh(df))
        if step == 1 :
            target = price *(1-((high-price)/price)*float(TPRR1))
        if step == 2 :
            target = price *(1-((high-price)/price)*float(TPRR2))    
    return float(target)

def RR1(df,direction,price):
    if direction :
        low = indi.swinglow(df)
        target = price *(1+((price-float(low))/price)*1)
    else :
        high = indi.swinghigh(df)
        target = price *(1-((float(high)-price)/price)*1)
    return target
#OpenLong=Buy
async def OpenLong(df,balance,symbol,lev,exchange,currentMODE,Lside):
    amount = buysize(df,balance,symbol,exchange)
    try:
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    ask = float(info['askPrice'])
    print(f'price : {ask}')
    logging.info(f'Entry Long @{ask} qmt:{amount}')
    leve = await setleverage(symbol,exchange)
    if amount*ask > Max_Size*int(leve):
        amount = Max_Size*int(leve)/ask    
    free = float(balance['free']['USDT'])
    amttp1 = amount*(TPPer/100)
    amttp2 = amount*(TPPer2/100)
    low = indi.swinglow(df)
    if free > min_balance :
        try:
            order = await exchange.createMarketOrder(symbol,'buy',amount,params={'positionSide':Lside})
            logging.info(order)
        except ccxt.InsufficientFunds as e:
            logging.debug(e)
            notify.send(e)
            return    
        if USESL :
            if currentMODE['dualSidePosition']:
                orderSL         = await exchange.create_order(symbol,'stop','sell',amount,float(low),params={'stopPrice':float(low),'triggerPrice':float(low),'positionSide':Lside})
                if Tailing_SL :
                    ordertailingSL  = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET','sell',amount,params ={'activationPrice':float(RR1(df,True,ask)) ,'callbackRate': float(indi.callbackRate(df)),'positionSide':Lside})
            else:
                orderSL         = await exchange.create_order(symbol,'stop','sell',amount,float(low),params={'stopPrice':float(low),'triggerPrice':float(low),'reduceOnly': True ,'positionSide':Lside})
                if Tailing_SL :
                    ordertailingSL  = await exchange.create_order(symbol, 'TRAILING_STOP_MARKET','sell',amount,params ={'activationPrice':float(RR1(df,True,ask)) ,'callbackRate': float(indi.callbackRate(df)),'reduceOnly': True ,'positionSide':Lside})
            if Tailing_SL :
                logging.info(ordertailingSL)
            logging.info(orderSL)
        if USETP :
            orderTP  = await exchange.create_order(symbol,'TAKE_PROFIT_MARKET','sell',amttp1,float(RRTP(df,True,1,ask)),params={'stopPrice':float(RRTP(df,True,1,ask)),'triggerPrice':float(RRTP(df,True,1,ask)),'positionSide':Lside})
            orderTP2 = await exchange.create_order(symbol,'TAKE_PROFIT_MARKET','sell',amttp2,float(RRTP(df,True,2,ask)),params={'stopPrice':float(RRTP(df,True,2,ask)),'triggerPrice':float(RRTP(df,True,2,ask)),'positionSide':Lside})
            logging.info(orderTP)
            logging.info(orderTP2)
        time.sleep(1)
        margin=ask*amount/int(lev)
        total = float(balance['total']['USDT'])
        msg ="BINANCE:\n" + "BOT         : \nCoin        : " + symbol + "\nStatus      : " + "OpenLong[BUY]" + "\nAmount    : " + str(amount) +"("+str(round((amount*ask),2))+" USDT)" + "\nPrice        :" + str(ask) + " USDT" + str(round(margin,2))+  " USDT"+ "\nBalance   :" + str(round(total,2)) + " USDT"
    else :
        msg = "MARGIN-CALL!!!\nยอดเงินต่ำกว่าที่กำหนดไว้  : " + str(min_balance) + '\nยอดปัจจุบัน ' + str(round(free,2)) + ' USD\nบอทจะทำการยกเลิกการเข้า Position ทั้งหมด' 
    notify.send(msg)
    candle(df,symbol,tf)
    #clearconsol()
    return
#OpenShort=Sell
async def OpenShort(df,balance,symbol,lev,exchange,currentMODE,Sside):
    amount = sellsize(df,balance,symbol,exchange)
    try:
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    bid = float(info['bidPrice'])
    logging.info(f'Entry Short @{bid} qmt:{amount}')
    leve = await setleverage(symbol,exchange)
    if amount*bid > Max_Size*int(leve):
        amount = Max_Size*int(leve)/bid  
    free = float(balance['free']['USDT'])
    amttp1 = amount*(TPPer/100)
    amttp2 = amount*(TPPer2/100)
    high = indi.swinghigh(df)
    if free > min_balance :
        try:
            order = await exchange.createMarketOrder(symbol,'sell',amount,params={'positionSide':Sside})
            logging.info(order)
        except ccxt.InsufficientFunds as e:
            logging.debug(e)
            notify.send(e)
            return        
        if USESL :
            if currentMODE['dualSidePosition']:
                orderSL         = await exchange.create_order(symbol,'stop','buy',amount,float(high),params={'stopPrice':float(high),'triggerPrice':float(high),'positionSide':Sside})
                if Tailing_SL :
                    ordertailingSL  = await exchange.create_order(symbol,'TRAILING_STOP_MARKET','buy',amount,params ={'activationPrice':float(RR1(df,False,bid)) ,'callbackRate': float(indi.callbackRate(df)),'positionSide':Sside})
            else :
                orderSL         = await exchange.create_order(symbol,'stop','buy',amount,float(high),params={'stopPrice':float(high),'triggerPrice':float(high),'reduceOnly': True ,'positionSide':Sside})
                if Tailing_SL :
                    ordertailingSL  = await exchange.create_order(symbol,'TRAILING_STOP_MARKET','buy',amount,params ={'activationPrice':float(RR1(df,False,bid)) ,'callbackRate': float(indi.callbackRate(df)),'reduceOnly': True ,'positionSide':Sside})
            if Tailing_SL :    
                logging.info(ordertailingSL)
            logging.info(orderSL)
        if USETP :
            orderTP = await exchange.create_order(symbol,'TAKE_PROFIT_MARKET','buy',amttp1,float(RRTP(df,False,1,bid)),params={'stopPrice':float(RRTP(df,False,1,bid)),'triggerPrice':float(RRTP(df,False,1,bid)),'positionSide':Sside})
            logging.info(orderTP)
            orderTP2 = await exchange.create_order(symbol,'TAKE_PROFIT_MARKET','buy',amttp2,float(RRTP(df,False,2,bid)),params={'stopPrice':float(RRTP(df,False,2,bid)),'triggerPrice':float(RRTP(df,False,2,bid)),'positionSide':Sside})
            logging.info(orderTP2)
        time.sleep(1)
        margin=bid*amount/int(lev)
        total = float(balance['total']['USDT'])
        msg ="BINANCE:\nBOT         : \nCoin        : " + symbol + "\nStatus      : " + "OpenShort[SELL]" + "\nAmount    : " + str(amount) +"("+str(round((amount*bid),2))+" USDT)" + "\nPrice        :" + str(bid) + " USDT" + str(round(margin,2))+  " USDT"+ "\nBalance   :" + str(round(total,2)) + " USDT"
    else :
        msg = "MARGIN-CALL!!!\nยอดเงินต่ำกว่าที่กำหนดไว้  : " + str(min_balance) + '\nยอดปัจจุบัน ' + str(round(free,2)) + ' USD\nบอทจะทำการยกเลิกการเข้า Position ทั้งหมด' 
    notify.send(msg)
    candle(df,symbol,tf)
    # clearconsol()
    return
#CloseLong=Sell
async def CloseLong(df,balance,symbol,amt,pnl,exchange,Lside):
    amount = abs(amt)
    upnl = pnl
    try:
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    bid = float(info['bidPrice'])
    logging.info(f'Close Long @{bid} qmt:{amount}')
    try:
        order = await exchange.createMarketOrder(symbol,'sell',amount,params={'positionSide':Lside})
    except:
        await asyncio.sleep(1)
        order = await exchange.createMarketOrder(symbol,'sell',amount,params={'positionSide':Lside})
    time.sleep(1)
    logging.info(order)
    total = float(balance['total']['USDT'])
    msg ="BINANCE:\n" + "BOT         : \nCoin        : " + symbol + "\nStatus      : " + "CloseLong[SELL]" + "\nAmount    : " + str(amount) +"("+str(round((amount*bid),2))+" USDT)" + "\nPrice        :" + str(bid) + " USDT" + "\nRealized P/L: " + str(round(upnl,2)) + " USDT"  +"\nBalance   :" + str(round(total,2)) + " USDT"
    notify.send(msg)
    candle(df,symbol,tf)
    # clearconsol()
    return
#CloseShort=Buy
async def CloseShort(df,balance,symbol,amt,pnl,exchange,Sside):
    print('Close Short')
    amount = abs(amt)
    upnl = pnl
    try:
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        info = (await exchange.fetchBidsAsks([symbol]))[symbol]['info']
    ask = float(info['askPrice'])
    logging.info(f'Close Short @{ask} qmt:{amount}')
    try:
        order = await exchange.createMarketOrder(symbol,'buy',amount,params={'positionSide':Sside})
    except:
        time.sleep(1)
        order = await exchange.createMarketOrder(symbol,'buy',amount,params={'positionSide':Sside})
    time.sleep(1)
    logging.info(order)
    total = float(balance['total']['USDT'])
    msg ="BINANCE:\n" + "BOT         : \nCoin        : " + symbol + "\nStatus      : " + "CloseShort[BUY]" + "\nAmount    : " + str(amount) +"("+ str(round((amount*ask),2))+" USDT)" + "\nPrice        :" + str(ask) + " USDT" + "\nRealized P/L: " + str(round(upnl,2)) + " USDT"  +"\nBalance   :" + str(round(total,2)) + " USDT"
    notify.send(msg)
    candle(df,symbol,tf)
    # clearconsol()
    return

async def feed(df,symbol,exchange,currentMODE):
    is_in_Long = False
    is_in_Short = False
    is_in_position = False
    posim = symbol.replace('/','')    
    try:    
        balance = await exchange.fetch_balance()
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    positions = balance['info']['positions']
    current_positions = [position for position in positions if float(position['positionAmt']) != 0]
    status = pd.DataFrame(current_positions, columns=["symbol", "entryPrice","positionSide", "unrealizedProfit", "positionAmt", "initialMargin"])   
    print('checking current position on hold...')
    print(tabulate(status, headers = 'keys', tablefmt = 'grid'))
    amt = 0.0
    upnl = 0.0
    margin = 0.0
    netunpl = 0.0
    for i in status.index:
        margin += float(status['initialMargin'][i])
        netunpl += float(status['unrealizedProfit'][i])
    print(f'Margin Used : {margin}')
    print(f'NET unrealizedProfit : {netunpl}')
    if margin > max_margin:
        await notify.send(f'Margin ที่ใช้สูงเกินไปแล้ว\nMargin : {margin}\nที่กำหนดไว้ : {max_margin}',sticker_id=17857, package_id=1070)
    print("checking for buy and sell signals")
    for i in status.index:
        if status['symbol'][i] == posim:
            amt = float(status['positionAmt'][i])
            upnl = float(status['unrealizedProfit'][i])
            break
    # NO Position
    if currentMODE['dualSidePosition']:
        Sside = 'SHORT'
        Lside = 'LONG'
    else:
        Sside = 'BOTH'
        Lside = 'BOTH'
    if not status.empty and amt != 0 :
        is_in_position = True
    # Long position
    if is_in_position and amt > 0  :
        is_in_Long = True
        is_in_Short = False
    # Short position
    elif is_in_position and amt < 0  :
        is_in_Short = True
        is_in_Long = False 
    else: 
        is_in_position = False
        is_in_Short = False
        is_in_Long = False 
    last = len(df.index)-1
    if df['BUY'][last] :
        print("changed to Bullish, buy")
        if is_in_Short :
            print('closeshort')
            await CloseShort(df,balance,symbol,amt,upnl,exchange,Sside)
        if not is_in_Long and USELONG:
            await exchange.cancel_all_orders(symbol)
            await OpenLong(df,balance,symbol,leverage,exchange,currentMODE,Lside)
            is_in_Long = True
        else:
            print("already in position, nothing to do")
    if df['SELL'][last]:
        print("changed to Bearish, Sell")
        if is_in_Long :
            print('closelong')
            await CloseLong(df,balance,symbol,amt,upnl,exchange,Lside)
        if not is_in_Short and USESHORT :
            await exchange.cancel_all_orders(symbol)
            await OpenShort(df,balance,symbol,leverage,exchange,currentMODE,Sside)
            is_in_Short = True
        else:
            print("already in position, nothing to do")
    return 

async def get_dailytasks(exchange):
    symbolist = await get_symbol(exchange)
    daycollum = ['Symbol', 'LastPirce', 'Long-Term', 'Mid-Term', 'Short-Term']
    dfday = pd.DataFrame(columns=daycollum)
    for symbol in symbolist:
        # score , df = benchmarking(df)
        data1 = await fetchbars(symbol,'1d',exchange)
        score1, df1 = indi.benchmarking(data1)
        candle(df1,symbol,'1d')
        await asyncio.sleep(0.1)
        data2 = await fetchbars(symbol,'6h',exchange)
        score2, df2 = indi.benchmarking(data2)
        await asyncio.sleep(0.1)
        data3 = await fetchbars(symbol,'1h',exchange)
        score3, df3 = indi.benchmarking(data3)
        candle(df3,symbol,'1h')
        await asyncio.sleep(0.1)
        ask = data3['Close'][len(data3.index)-1]
        print(symbol,f"Long_Term : {score1} , Mid_Term : {score2} , Short_Term : {score3}")
        dfday = dfday.append(pd.Series([symbol, ask, score1, score2, score3],index=daycollum),ignore_index=True) 
    return  dfday

async def dailyreport(exchange):
    data = await get_dailytasks(exchange)
    todays = str(data)
    logging.info(f'{todays}')
    data = data.set_index('Symbol')
    data.drop(['Mid-Term','LastPirce'],axis=1,inplace=True)
    msg = str(data)
    notify.send(f'คู่เทรดที่น่าสนใจในวันนี้\n{msg}',sticker_id=1990, package_id=446) 
    try:    
        balance = await exchange.fetch_balance()
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
    positions = balance['info']['positions']
    current_positions = [position for position in positions if float(position['positionAmt']) != 0]
    status = pd.DataFrame(current_positions, columns=["symbol", "entryPrice","positionSide", "unrealizedProfit", "positionAmt", "initialMargin"])   
    m = status.index
    margin = 0.0
    netunpl = 0.0
    for i in m:
        margin += float(status['initialMargin'][i])
        netunpl += float(status['unrealizedProfit'][i])
    print(f'Margin Used : {margin}')
    print(f'NET unrealizedProfit : {margin}')
    status = status.sort_values(by=['unrealizedProfit'],ascending=False)
    status = status.head(1)
    sim1 = status['symbol'][0]
    upnl = round(float(status['unrealizedProfit'][0]),2)
    entryP = status['entryPrice'][0]
    metthod = status['positionSide'][0]
    msg2 = f'{sim1} {metthod} at {entryP} \nunrealizedProfit : {upnl}$'
    notify.send(f'Top Performance\n{msg2}\n-----\nNet Margin Used : {round(float(margin),2)}$\nNet unrealizedProfit : {round(float(netunpl),2)}$',sticker_id=1995, package_id=446) 
    return

async def main():
    exchange = ccxt.binance(BNBCZ)
    try:    
        currentMODE = await exchange.fapiPrivate_get_positionside_dual()
    except ccxt.RequestTimeout as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        currentMODE = await exchange.fapiPrivate_get_positionside_dual()
    except ccxt.DDoSProtection as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        currentMODE = await exchange.fapiPrivate_get_positionside_dual()
    except ccxt.ExchangeNotAvailable as e:
        print('[' + type(e).__name__ + ']')
        print(str(e.args)[0:200])
        await asyncio.sleep(1)
        currentMODE = await exchange.fapiPrivate_get_positionside_dual()
    except ccxt.ExchangeError as e:
        print('[' + type(e).__name__ + ']')
        print(str(e)[0:200])
        await asyncio.sleep(1)
        currentMODE = await exchange.fapiPrivate_get_positionside_dual()
    if currentMODE['dualSidePosition']:
        print('You are in Hedge Mode')
    else:
        print('You are in One-way Mode')
    exchange.precisionMode = ccxt.DECIMAL_PLACES
    global aldynoti, aldynotiday
    seconds = time.time()
    local_time = time.ctime(seconds)
    print(str(local_time[14:-9]))
    if str(local_time[14:-9]) == '1':
        aldynoti = False
        aldynotiday = False
    if str(local_time[11:-11]) == '08' and not aldynotiday:
        aldynotiday = True
        aldynoti = True   
        await asyncio.gather(dailyreport(exchange))     
    if str(local_time[14:-9]) == '0' and not aldynoti:
        try:
            balance = await exchange.fetch_balance()    
        except ccxt.RequestTimeout as e:
            print('[' + type(e).__name__ + ']')
            print(str(e)[0:200])
            await asyncio.sleep(1)
            balance = await exchange.fetch_balance()    
        except ccxt.DDoSProtection as e:
            print('[' + type(e).__name__ + ']')
            print(str(e.args)[0:200])
            await asyncio.sleep(1)
            balance = await exchange.fetch_balance()    
        except ccxt.ExchangeNotAvailable as e:
            print('[' + type(e).__name__ + ']')
            print(str(e.args)[0:200])
            await asyncio.sleep(1)
            balance = await exchange.fetch_balance()    
        except ccxt.ExchangeError as e:
            print('[' + type(e).__name__ + ']')
            print(str(e)[0:200])
            await asyncio.sleep(1)
            balance = await exchange.fetch_balance()    
        total = round(float(balance['total']['USDT']),2)
        notify.send(f'Total Balance : {total} USDT',sticker_id=10863, package_id=789)
        aldynoti = True
    symbolist = await get_symbol(exchange)
    for symbol in symbolist:
        data = await fetchbars(symbol,tf,exchange)
        score1, df = indi.benchmarking(data)
        print(f"{symbol} is {score1}")
        await asyncio.gather(feed(df,symbol,exchange,currentMODE))
        await asyncio.sleep(1)
    await exchange.close()


if __name__ == "__main__":
    while True:
        asyncio.run(main())
