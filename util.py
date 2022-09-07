import pandas as pd
pd.set_option('display.max_rows', None)
import talib as ta
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import math 
import os
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

#VXMA
Pivot   = int(config['STAT']['Pivot_lookback'])
#TA setting
atr_p   = int(config['TA']['ATR_Period'])
atr_m   = float(config['TA']['ATR_Mutiply'])
rsi     = int(config['TA']['RSI_Period'])
ema     = int(config['TA']['EMA_Fast'])
linear  = int(config['TA']['SUBHAG_LINEAR'])
smooth  = int(config['TA']['SMOOTH'])
AOL     = int(config['TA']['Andean_Oscillator'])
#standard TA weighing
RSI_W       = int(config['weigh100']['RSI_W'])
ADX_W       = int(config['weigh100']['ADX_W'])
VXMA_W      = int(config['weigh100']['VXMA_W'])
MACD_W      = int(config['weigh100']['MACD_W'])
SMA200_W    = int(config['weigh100']['SMA200_W'])

#Pivot High-Low only calculate last fixed bars
def swinghigh(data):
    m = len(data.index)
    data['Highest'] = data['High']
    for i in range(m - Pivot, m):
        if data['High'][i] > data['Highest'][i-1]:
            data['Highest'][i] = data['High'][i]
        else : data['Highest'][i] = data['Highest'][i-1]
    highest = data['Highest'][i]
    return highest

def swinglow(data):
    m = len(data.index)
    data['Lowest'] = data['Low']
    for i in range(m - Pivot, m):
        if data['Low'][i] < data['Lowest'][i-1]:
            data['Lowest'][i] = data['Low'][i]
        else : data['Lowest'][i] = data['Lowest'][i-1]
    Lowest = data['Lowest'][i]    
    return Lowest

def callbackRate(data):
    highest = swinghigh(data)
    lowest = swinglow(data)
    rate = round((highest-lowest)/highest*100,1)
    if rate > 5 :
        rate = 5
    elif rate < 0.1 :
        rate = 0.1
    return rate 
#VXMA
def vxma(data):
    m = len(data.index)
    alpha = 2/(AOL + 1)
    data['ema'] = ta.EMA(data['Close'],ema)
    data['subhag'] = ta.EMA(ta.LINEARREG(data['Close'],linear),smooth)
    data['atr'] = ta.ATR(data['High'],data['Low'],data['Close'],atr_p)
    data['rsi'] = ta.RSI(data['Close'],rsi)
    data['downT'] = data['High'] + data['atr']* atr_m
    data['upT']   = data['Low'] - data['atr'] * atr_m
    data['alphatrend'] = [np.nan] * m
    data['up1'] = [np.nan] * m 
    data['up2'] = [np.nan] * m 
    data['dn1'] = [np.nan] * m 
    data['dn2'] = [np.nan] * m 
    data['cmpbull'] = [np.nan] * m 
    data['cmpbear'] = [np.nan] * m 
    data['vxma'] = [np.nan] * m 
    data['trend'] = False
    data['pBUY'] = False
    data['pSELL'] = False
    data['buyPrice'] = [np.nan] * m 
    data['sellPrice'] = [np.nan] * m 
    data['BUY'] = False
    data['SELL'] = False
    #AlphaTrend rsibb >= 50 ? upT < nz(AlphaTrend[1]) ? nz(AlphaTrend[1]) : upT : downT > nz(AlphaTrend[1]) ? nz(AlphaTrend[1]) : downT
    for i in range(2, m):
        CloseP = data['Close'][i]
        OpenP = data['Open'][i]
        up1 = data['up1'][i-1]
        up2 = data['up2'][i-1]
        dn1 = data['dn1'][i-1]
        dn2 = data['dn2'][i-1]
        if data['rsi'][i] >= 50 :
            if data['upT'][i] < (data['alphatrend'][i-1] if data['alphatrend'][i-1] is not None else 0):
                data['alphatrend'][i] = (data['alphatrend'][i-1] if data['alphatrend'][i-1] is not None else 0)
            else : data['alphatrend'][i] = data['upT'][i]
        else:
            if data['downT'][i] > (data['alphatrend'][i-1] if data['alphatrend'][i-1] is not None else 0):
                data['alphatrend'][i] = (data['alphatrend'][i-1] if data['alphatrend'][i-1] is not None else 0)
            else : data['alphatrend'][i] = data['downT'][i]
        # up1 := nz(math.max(C, O, up1[1] - (up1[1] - C) * alpha), C)
        up1n = data['up1'][i] = (max(CloseP,OpenP,up1 - (up1 - CloseP)*alpha) if max(CloseP,OpenP,up1 - (up1 - CloseP)*alpha) is not None else data['Close'][i])
        # up2 := nz(math.max(C * C, O * O, up2[1] - (up2[1] - C * C) * alpha), C * C)
        up2n = data['up2'][i] = (max(CloseP*CloseP,OpenP*OpenP,up2 - (up2 - CloseP*CloseP)*alpha) if max(CloseP*CloseP,OpenP*OpenP,up2 - (up2 - CloseP*CloseP)*alpha) is not None else data['Close'][i]*data['Close'][i])
        # dn1 := nz(math.min(C, O, dn1[1] + (C - dn1[1]) * alpha), C)
        dn1n = data['dn1'][i] = (min(CloseP,OpenP,dn1 + (CloseP - dn1)*alpha) if min(CloseP,OpenP,dn1 + (CloseP - dn1)*alpha) is not None else data['Close'][i])
        # dn2 := nz(math.min(C * C, O * O, dn2[1] + (C * C - dn2[1]) * alpha), C * C)
        dn2n = data['dn2'][i] = (min(CloseP*CloseP,OpenP*OpenP,dn2 + (CloseP*CloseP - dn2)*alpha) if min(CloseP*CloseP,OpenP*OpenP,dn2 + (CloseP*CloseP - dn2)*alpha) is not None else data['Close'][i]*data['Close'][i])
        data['cmpbull'][i] = math.sqrt(dn2n - (dn1n * dn1n))
        data['cmpbear'][i] = math.sqrt(up2n - (up1n * up1n))
        EMAFAST = data['ema'][i]
        LINREG = data['subhag'][i]
        ALPHATREND = data['alphatrend'][i-2]
        clohi = max(EMAFAST,LINREG,ALPHATREND)
        clolo = min(EMAFAST,LINREG,ALPHATREND)
            #CloudMA := (bull > bear) ? clolo < nz(CloudMA[1]) ? nz(CloudMA[1]) : clolo :
        if data['cmpbull'][i] > data['cmpbear'][i] :
            if clolo < (data['vxma'][i-1] if data['vxma'][i-1] is not None else 0):
                data['vxma'][i] = (data['vxma'][i-1] if data['vxma'][i-1] is not None else 0)
            else : data['vxma'][i] = clolo
            #  (bear > bull) ? clohi > nz(CloudMA[1]) ? nz(CloudMA[1]) : clohi : nz(CloudMA[1])
        elif data['cmpbull'][i] < data['cmpbear'][i]:
            if clohi > (data['vxma'][i-1] if data['vxma'][i-1] is not None else 0):
                data['vxma'][i] = (data['vxma'][i-1] if data['vxma'][i-1] is not None else 0)
            else : data['vxma'][i] = clohi
        else:
            data['vxma'][i] = (data['vxma'][i-1] if data['vxma'][i-1] is not None else 0)
        #Get trend True = Bull False = Bear
        if data['vxma'][i] > data['vxma'][i-1] and data['vxma'][i-1] > data['vxma'][i-2] :
            data['trend'][i] = True
        elif data['vxma'][i] < data['vxma'][i-1] and data['vxma'][i-1] < data['vxma'][i-2] :
            data['trend'][i] = False
        else:
            data['trend'][i] = data['trend'][i-1] 
        #if trend change get pre-signal
        if data['trend'][i] and not data['trend'][i-1] :
            data['pBUY'][i] = True
            data['pSELL'][i] = False
        elif not data['trend'][i] and data['trend'][i-1] :
            data['pBUY'][i] = False
            data['pSELL'][i] = True
        else :
            data['pBUY'][i] = False
            data['pSELL'][i] = False
        #if close is above cloud is buy signal
        if data['Close'][i] > data['vxma'][i] and (data['pBUY'][i] or data['pBUY'][i-1]) and (not data['BUY'][i-1]):
            data['BUY'][i] = True 
            data['buyPrice'][i] = data['Close'][i] - data['atr'][i]
        elif data['Close'][i] < data['vxma'][i] and (data['pSELL'][i] or data['pSELL'][i-1]) and (not data['SELL'][i-1]):
            data['SELL'][i] = True 
            data['sellPrice'][i] = data['Close'][i] + data['atr'][i]
        else:
            data['BUY'][i] = False
            data['SELL'][i] = False 
    data.drop(['pBUY','pSELL','trend','cmpbull'],axis=1,inplace=True)
    data.drop(['cmpbear','ema','subhag','atr'],axis=1,inplace=True)
    data.drop(['alphatrend','up1','up2','dn1'],axis=1,inplace=True)
    data.drop(['dn2','downT','upT',],axis=1,inplace=True)
    return data
#Trending a symbol.
def benchmarking(data):
    tacollum = ['sma_200', 'macd', 'adx', 'adx+', 'adx-']
    datascoe = pd.DataFrame(columns=tacollum)
    datascoe['sma_200'] = ta.SMA(data['Close'],200)
    datascoe['macd'], macdsignal, macdhist = ta.MACD(data['Close'],12,26,9)
    datascoe['adx']  = ta.ADX(data['High'],data['Low'],data['Close'],14)
    datascoe['adx+'] = ta.PLUS_DI(data['High'],data['Low'],data['Close'],14)
    datascoe['adx-'] = ta.MINUS_DI(data['High'],data['Low'],data['Close'],14)
    data = vxma(data)
    m = len(data.index)-1
    adxx = 0
    if float(datascoe['adx'][m]) > 25 and float(datascoe['adx+'][m]) > float(datascoe['adx-'][m]):
        adxx = 10
    elif float(datascoe['adx'][m]) > 25 and float(datascoe['adx+'][m]) < float(datascoe['adx-'][m]):
        adxx = 0
    else : adxx = 5
    macd = (10 if float(datascoe['macd'][m]) > 0 else 0)
    sma = (10 if float(datascoe['sma_200'][m]) < float(data['Close'][m]) else 0)
    rsi = float(data['rsi'][m])/10
    if data['vxma'][m] > data['vxma'][m-1]:
        vxda = 10
    elif data['vxma'][m] < data['vxma'][m-1]:
        vxda = 0
    else: vxda = 5
    score = ((macd*MACD_W)/100 + (adxx*ADX_W)/100 + (sma*SMA200_W)/100 + (rsi*RSI_W)/100 + (vxda*VXMA_W)/100)
    if score > 8 :
        scr = 'Extreme-Bullish'
    elif score > 6 :
        scr = 'Bullish'
    elif score < 4 :
        scr = 'Bearish'
    elif score < 2 :
        scr = 'Extreme-Bearish'
    else:
        scr = 'Side-Way'
    return scr , data

#clearconsol
def clearconsol():
    if os.name == 'posix':
        os.system('clear')
    else:
        os.system('cls') 
    return



