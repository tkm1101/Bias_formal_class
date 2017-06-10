import oandapy
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime
class BIAS:
    def __init__(self,environment,account_id,access_token,instrument):
        self.environment = environment
        self.account_id = account_id
        self.access_token = access_token
        self.oanda=oandapy.API(self.environment,self.access_token)
        self.instrument = instrument
        
        self.minute_granularity = 'M1'
        self.hour_granularity = 'H1'
        self.minute_count = 5000
        self.hour_count = 20
        self.units = 1000
        self.weighted_bias = 0
        self.trading_stats = 0
        self.ema1 = self.ema2 = self.ema3 = pd.Series()
        self.bias1 = self.bias2 = self.bias3 = pd.Series()
        
        
    def trade_status(self):
        invested = self.oanda.get_trades(self.account_id)['trades']
        if invested == []:
            return 'empty'
        elif invested != []:
            if invested[0]['side'] == 'buy':
                return 'buy'
            elif invested[0]['side'] == 'sell':
                return 'sell'
            
    def send_order(self,side,units):
        return self.oanda.create_order(account_id=self.account_id,
                                      instrument=self.instrument,
                                      units=units,
                                      side=side,
                                      type='market')
                                      
    def bull_bear_indicator(self):
        self.df = pd.DataFrame(self.oanda.get_history(instrument=self.instrument,
                                               granularity = self.hour_granularity,
                                              count = self.hour_count)['candles'])
        self.hour_df = pd.DataFrame((self.df['closeAsk']+self.df['closeBid'])/2,
                                    columns=['MidHour'])['MidHour']
        
        if self.hour_df[self.hour_count-1] < self.hour_df.mean():
            return 'bear market'
        elif self.hour_df[self.hour_count-1] > self.hour_df.mean():
            return 'bull market'
    
    def perform_trade_logic(self,trading_stats,lower,upper,mean):
        
        if self.trade_status() == 'empty':
            if self.bull_bear_indicator() == 'bull market' and trading_stats < lower:
                self.send_order('buy',self.units)
            elif self.bull_bear_indicator() == 'bear market' and trading_stats > upper:
                self.send_order('sell',self.units)
        
        elif self.trade_status() == 'buy' and trading_stats > mean:
            self.oanda.close_position(self.account_id,self.instrument)
                            
        elif self.trade_status() == 'sell' and trading_stats < mean:
            self.oanda.close_position(self.account_id,self.instrument)
            
            
    
    def EMA(self,number,data):
        return data.ewm(span=number).mean()
    
    def BIAS(self,number,data,EMA):
        return (data-EMA)/EMA
    
    def analysis(self):
        self.df = pd.DataFrame(self.oanda.get_history(instrument=self.instrument,
                                               granularity = self.minute_granularity,
                                              count = self.minute_count)['candles'])
        self.midclose = pd.DataFrame((self.df['closeAsk']+
                                      self.df['closeBid'])/2,columns=['MidClose'])['MidClose']
        
        self.ema1,self.ema2,self.ema3 = self.EMA(6,self.midclose),self.EMA(12,self.midclose),self.EMA(24,self.midclose)
        
        self.bias1, self.bias2, self.bias3 = self.BIAS(6,self.midclose,self.ema1),self.BIAS(12,self.midclose,self.ema2),self.BIAS(24,self.midclose,self.ema3)
        
        self.weighted_bias = (5*self.bias1+3*self.bias2+2*self.bias3)/10
        
        self.trading_stats = self.weighted_bias/self.midclose
        self.lower = np.percentile(self.trading_stats,10)
        self.upper = np.percentile(self.trading_stats,90)
        self.mean = self.trading_stats.mean()
        
        
        self.perform_trade_logic(self.trading_stats[self.minute_count-1],self.lower,self.upper,self.trading_stats.mean())
        self.print_status(self.trading_stats[self.minute_count-1],self.lower,self.upper)
        
    def print_status(self,trading_stats,lower,upper):
        print('time:',datetime.now())
        print('Market:',self.bull_bear_indicator())
        print('signal:',trading_stats)
        print('upper:',upper)
        print('lower:',lower)
        print('#########################################################')
    
    def trading_begin(self):
        while True:
            try:
                self.analysis()
            except Exception as e:
                print(str(e))
                time.sleep(5)

if __name__ == "__main__":
    account_id=os.getenv("account_number")
    access_token=os.getenv("access_token")
    system = BIAS('practice',account_id,access_token,'EUR_USD')
    system.trading_begin()
