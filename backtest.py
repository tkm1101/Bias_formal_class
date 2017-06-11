##回测时间: 2017.06.04
#导入数据库
import oandapy
import os
import pandas as pd
import matplotlib.pyplot as plt
%matplotlib inline
import numpy as np

#个人账号信息
account_number=os.getenv("account_number")
access_token=os.getenv("access_token")
oanda=oandapy.API(environment="practice",access_token=access_token)
response=oanda.get_history(instrument="EUR_USD",granularity='M1',count=5000) #获取历史分钟数据

df2=pd.DataFrame(data=response['candles'],index=None) 

df_midclose=pd.DataFrame(data=(df2['closeAsk']+df2['closeBid'])/2,columns=['MidClose']) #中间价

#6,12,24EMA
EMA1=df_midclose['MidClose'].ewm(span=6).mean()
EMA2=df_midclose['MidClose'].ewm(span=12).mean()
EMA3=df_midclose['MidClose'].ewm(span=24).mean()

#乖离率
BIAS1=(df_midclose['MidClose']-EMA1)/EMA1
BIAS2=(df_midclose['MidClose']-EMA2)/EMA2
BIAS3=(df_midclose['MidClose']-EMA3)/EMA3

weighted_bias =(5*BIAS1+3*BIAS2+2*BIAS3)/10

trading_stats = weighted_bias/df_midclose['MidClose']

upper = np.percentile(trading_stats,99.5) #高位临界值
lower = np.percentile(trading_stats,0.5) #低位临界值


buy_trigger = [i for i in range(5000) if trading_stats[i] < lower] #买入条件
sell_trigger = [i for i in range(5000) if trading_stats[i] > upper] #卖出条件

#定义一个新的函数：若在一个十分钟的区间内交易信号连续满足买入/卖出条件，则只取第一个满足信号的时间点
#比如：若在55、56、57、58、70、72、89分钟时交易信号满足条件，真正只取55、70和89分钟。

def real_openning(data):
    real=[data[0]]
    for i in range(len(data)-1):
        if data[i+1] - data[i] < 10:
            pass
        elif data[i+1] - data[i] >10:
            real.append(data[i+1])
    return real

#图像产出
plt.figure(figsize=(20,10))
plt.plot(df_midclose['MidClose'],label = 'EUR_USD Minute graph') #欧元/美元分钟中间价走势
plt.scatter(real_openning(buy_trigger),[df_midclose['MidClose'][real_openning(buy_trigger)]],
            marker = 'o',color='red',s = 80,label = 'Long') #买入点
plt.scatter(real_openning(sell_trigger),[df_midclose['MidClose'][real_openning(sell_trigger)]],
            marker = 'o',color='green',s = 80,label = 'Short') #卖出点
axes = plt.gca()
axes.set_xlim([0,5000])
plt.legend(loc = 'lower right')
plt.show()
