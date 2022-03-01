import json
from typing import List
import yfinance as yf
from dateutil.relativedelta import relativedelta
from datetime import datetime

class StockTick:
    def __init__(self):
        self.stock_name = None
        self.date = None
        self.open_price = None
        self.close_price = None

    def set_stock_name(self,
                       stock_name):
        self.stock_name = stock_name

    def set_open_close_price(self,
                             date,
                             open_price,
                             close_price):
        self.date = date
        self.open_price = open_price
        self.close_price = close_price

    def get_open_price(self):
        return self.open_price

    def get_close_price(self):
        return self.close_price

    def get_json(self):
        js = {}
        js['stock_name'] = self.stock_name
        js['date'] = self.date
        js['open'] = self.open_price
        js['close'] = self.close_price
        return js

    def load_json(self,
                  js):
        self.set_stock_name(js['stock_name'])
        self.set_open_close_price(js['date'], js['open'], js['close'])

class StockDetail:
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.stock_ticks: List[StockTick] = []
        self.date_to_stock = {}
        self.is_valid_stock = True

    def add_stock_tick(self, stock_tick : StockTick):
        self.stock_ticks.append(stock_tick)
        self.date_to_stock[stock_tick.date] = stock_tick

    def is_record_exists(self, _date):
        if self.date_to_stock.get(_date): return True
        else: return False

    def read_stock_from_yf(self, period_start, period_end):
        stock_retrieval = yf.Ticker(self.stock_name)
        prices_retrieval = stock_retrieval.history(start=period_start, end=period_end)
        return prices_retrieval

    def read_stock(self, period_start, period_end):
        ############ Need better fix for IF Condition #################
        if (self.is_record_exists(period_start) and self.is_record_exists(period_end)) or not self.is_valid_stock or True: return
#        if (self.is_record_exists(period_start) and self.is_record_exists(period_end)) or not self.is_valid_stock: return
        stock_retrieval = yf.Ticker(self.stock_name)
        prices_retrieval = stock_retrieval.history(start=period_start, end=period_end)
        if len(prices_retrieval) == 0:
            print ("Stop Here")
        for index, row in prices_retrieval.iterrows():
            st = StockTick()
            st.set_stock_name(self.stock_name)
            st.set_open_close_price(index.strftime("%Y-%m-%d"), row['Open'], row['Close'])
            self.add_stock_tick(st)

    def get_closest_forward_tick(self,
                                 _date):
        target_date = datetime.strptime(_date, '%Y-%m-%d')
        i = 1
        while i < 10:
            target_date = target_date + relativedelta(days=i)
            index_date_string, target_date_string = _date, target_date.strftime("%Y-%m-%d")
            if self.date_to_stock.get(target_date_string): return self.date_to_stock[target_date_string].open_price
            i += 1
        return None

    def get_closest_backward_tick(self,
                                  _date):

        target_date = datetime.strptime(_date, '%Y-%m-%d')
        i = 1
        while i < 10:
            target_date = target_date + relativedelta(days=-i)
            index_date_string, target_date_string = _date, target_date.strftime("%Y-%m-%d")
            if self.date_to_stock.get(target_date_string): return self.date_to_stock[target_date_string].close_price
            i += 1
        return None

    def get_open_close_price_for_period(self,
                                        index_date,
                                        end_date):
        self.read_stock(index_date, end_date)
        open_price = self.date_to_stock.get(index_date).get_open_price() if self.date_to_stock.get(index_date) is not None else None
        close_price = self.date_to_stock.get(index_date).get_close_price() if self.date_to_stock.get(index_date) is not None else None
        if open_price is None and self.date_to_stock: open_price = self.get_closest_forward_tick(index_date)
        if close_price is None and self.date_to_stock: close_price = self.get_closest_backward_tick(end_date)
        return open_price, close_price

    def compute_gain_for_period(self,
                                index_date,
                                end_date):
        open_price, close_price = self.get_open_close_price_for_period(index_date, end_date)
        if open_price is None or close_price is None: return None
        return ((close_price - open_price) / float(open_price)) * 100

    def get_json(self):
        js = {}
        js['stock_name'] = self.stock_name
        js['stock_ticks'] = [st.get_json() for st in self.stock_ticks]
        return js

    def load_json(self,
                  js):
        self.stock_name = js['stock_name']
        if not js['stock_ticks']: self.is_valid_stock = False
        for st in js['stock_ticks']:
            st_ins = StockTick()
            st_ins.load_json(st)
            self.stock_ticks.append(st_ins)
            self.date_to_stock[st_ins.date] = st_ins

class StocksAnalysis:
    def __init__(self,
                 stocks : List[str] = None):
        self.stocks = stocks
        if self.stocks is None: self.stocks = []
        self.stocks_details : List[StockDetail] = []
        self.stocks_details_dic = {}

    def load_stock_detail_for_stocks(self,
                                     stocks,
                                     period_start,
                                     period_end):
        for st in stocks:
            print (st)
            sd = StockDetail(st)
            sd.read_stock(period_start, period_end)
            self.stocks_details.append(sd)
            self.stocks_details_dic[st] = sd
            if st not in self.stocks: self.stocks.append(st)

    def get_stock_detail_json(self):
        js = {}
        for sd in self.stocks_details:
            js[sd.stock_name] = sd.get_json()
        return js

    def load_stock_detail_json(self,
                               js):
        for st in js:
            sd = js[st]
            sd_ins = StockDetail(sd['stock_name'])
            sd_ins.load_json(sd)
            self.stocks_details.append(sd_ins)
            self.stocks_details_dic[sd_ins.stock_name] = sd_ins
            if st not in self.stocks: self.stocks.append(st)

    def set_stock_detail(self,
                         stock_details : List[StockDetail]):
        self.stocks = [sd.stock_name for sd in stock_details]
        self.stocks_details = stock_details
        self.stocks_details_dic = { sd.stock_name : sd for sd in stock_details }

    def add_stock(self,
                  stock_name):
        sd = StockDetail(stock_name)
        if stock_name not in self.stocks: self.stocks.append(stock_name)
        self.stocks_details.append(sd)
        self.stocks_details_dic[stock_name] = sd

    def get_open_close_price_for_period(self,
                                        index_date,
                                        end_date,
                                        stocks=None):
        open_price, close_price = 0,0
        if stocks is None: stocks = self.stocks
        for stock_name in stocks:
            if self.stocks_details_dic.get(stock_name) is None: self.add_stock(stock_name)
            o_p, c_p = self.stocks_details_dic[stock_name].get_open_close_price_for_period(index_date, end_date)
#            print (stock_name, ' ', o_p, ' ', c_p, ' ', open_price, ' ', close_price)
            if o_p is None or c_p is None: continue
            open_price += o_p
            close_price += c_p
        return open_price, close_price

    def compute_gain_for_period(self,
                                index_date,
                                end_date,
                                stocks=None):
        open_price, close_price = self.get_open_close_price_for_period(index_date, end_date, stocks)
#        print ('Open - ', open_price, ' Close - ', close_price)
        if open_price == 0.0:
            return 0
        return ((close_price - open_price) / float(open_price)) * 100

class StocksPicker:
    def __init__(self,
                 base_stocks):
        self.base_stocks = base_stocks
        self.stock_analysis_instance = None

    def set_stock_analysis_instance(self,
                                    sa : StocksAnalysis):
        self.stock_analysis_instance = sa

    def pick_stocks(self,
                    **kwargs):
        pass

    def get_filtered_stocks_by_base_stocks_as_indicator(self,
                                                        target_date,
                                                        period_in_days):
        index_date = target_date + relativedelta(days=-period_in_days)
        index_date_string, target_date_string = index_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d")
        if self.stock_analysis_instance is None: sa = StocksAnalysis(self.base_stocks)
        else: sa = self.stock_analysis_instance
        base_stocks_gain = sa.compute_gain_for_period(index_date_string, target_date_string, self.base_stocks)
        if base_stocks_gain is None: return []
        filtered_stocks = []
        for s in self.base_stocks:
            s_gain = sa.compute_gain_for_period(index_date_string, target_date_string, [s])
            if s_gain is None: continue
            if s_gain > base_stocks_gain: filtered_stocks.append(s)
        return filtered_stocks

if __name__ == '__main__':
    with open('../../top_stocks.txt') as file:
        lines = file.readlines()
        base_stocks = [line.strip() for line in lines]
    sa = StocksAnalysis(base_stocks)
#    res = sa.compute_gain_for_period("2002-01-01", "2002-12-31")
#    print (res)
    sa.load_stock_detail_for_stocks(base_stocks, "1969-01-01", "2022-01-13")
    js = sa.get_stock_detail_json()

    with open('stock_prices.json', 'w') as f:
        json.dump(js, f)
#    sa_new = StocksAnalysis(base_stocks)
#    sa_new.load_stock_detail_json(js)
#    print (sa.stocks)