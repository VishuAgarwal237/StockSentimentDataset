import copy
from typing import List
import yfinance as yf
import numpy as np
import json
import json
import ast
import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from stock.stock.stock_ds import StocksAnalysis, StocksPicker
from multiprocessing import Pool
import matplotlib.pyplot as plt

def compute_win_ratio_for_stocks(sa : StocksAnalysis,
                                 target_date,
                                 period_in_days,
                                 stocks,
                                 base_stocks,
                                 observation_period_length):
    assert observation_period_length <= period_in_days
    assert observation_period_length != 0
    assert period_in_days > 1
    index_date = target_date + relativedelta(days=-period_in_days)
    no_of_observation_period = 0
    win_ratio_dict = { s : 0 for s in stocks }
    i = 0
    while i < period_in_days:
        end_date = index_date + relativedelta(days=observation_period_length - 1)
#        end_date = index_date + relativedelta(days=observation_period_length)

        # Compute gain for each stock for the obsertvation period
        base_gain = sa.compute_gain_for_period(index_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), base_stocks)
        for s in stocks:
            opt_gain = sa.compute_gain_for_period(index_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), [s])
            if base_gain < opt_gain: win_ratio_dict[s] += 1
        index_date = end_date + relativedelta(1)
        i += observation_period_length
        no_of_observation_period += 1

    for s in stocks: win_ratio_dict[s] = win_ratio_dict[s] / float(no_of_observation_period)
#    print (win_ratio_dict)
    return win_ratio_dict

def filter_stocks_on_win_ratio(win_ratio_dict,
                               threshold = 0.8):
    stocks = []
    for s in win_ratio_dict:
        if win_ratio_dict[s] >= threshold:
            stocks.append(s)
    return stocks

class NObservationPeriodStockPicker(StocksPicker):
    def __init__(self,
                 base_stocks):
        super().__init__(base_stocks)

    def pick_stocks(self,
                    **kwargs):
        threshold = kwargs.get('threshold')
        target_date = kwargs.get('target_date')
        period_in_days = kwargs.get('period_in_days')
        observation_period_length = kwargs.get('observation_period_length')
        sa = kwargs.get('stock_analysis_instance')
        pre_filtered_stocks = kwargs.get('base_stocks', self.get_filtered_stocks_by_base_stocks_as_indicator(target_date, period_in_days))
        win_ratio = compute_win_ratio_for_stocks(sa,
                                                 target_date,
                                                 period_in_days,
                                                 pre_filtered_stocks,
                                                 self.base_stocks,
                                                 observation_period_length)
        return [pre_filtered_stocks, filter_stocks_on_win_ratio(win_ratio,
                                          threshold)]

if __name__ == '__main__':
    target_date_str = '2018-06-06'
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')

    # Get base stocks
    with open('../../top_stocks.txt') as file:
        lines = file.readlines()
        base_stocks = [line.strip() for line in lines]

    # Read Stock data
    sa = StocksAnalysis(copy.deepcopy(base_stocks))
    with open('stock_prices.json') as f:
        js = json.load(f)
    sa.load_stock_detail_json(js)


    # Pick stocks
    def get_top_stocks(t_base_stocks, threshold=0.8, target_date=None, period_in_days=50, obs_len=10,
                       stock_analysis_ins_t=None):
        sp = NObservationPeriodStockPicker(t_base_stocks)
        sp.set_stock_analysis_instance(sa)
        st_res = sp.pick_stocks(threshold=threshold,
                                target_date=target_date,
                                period_in_days=period_in_days,
                                observation_period_length=obs_len,
                                stock_analysis_instance=stock_analysis_ins_t)
        return st_res

    # Compute gain for period
    def compute_gain_for_period(stock_analysis_ins_t, stocks_t, index_date, target_date):
        return stock_analysis_ins_t.compute_gain_for_period(index_date.strftime("%Y-%m-%d"), target_date.strftime("%Y-%m-%d"), stocks_t)


    # Compute results for year
    def compute_results_for_year(year, t_base_stocks, threshold, period_in_days, obs_len, sa_t):
        result = {}
        for i in range(1, 13):
            res = {}
            target_date_str = str(year) + f'-{i}-01'
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            st_res = get_top_stocks(t_base_stocks, threshold, target_date, period_in_days, obs_len, sa_t)
            prefiltered_stocks, top_stocks = st_res[0], st_res[1]
            pred_target_date = target_date + relativedelta(days=obs_len)
            #        res['top_stocks'] = top_stocks
            res['top_stocks_len'] = len(top_stocks)
            res['sp_stocks_len'] = len(prefiltered_stocks)
            res['base_gain'] = compute_gain_for_period(sa_t, t_base_stocks, target_date, pred_target_date)
            res['sp_gain'] = compute_gain_for_period(sa_t, prefiltered_stocks, target_date, pred_target_date)
            res['top_gain'] = compute_gain_for_period(sa_t, top_stocks, target_date, pred_target_date)
            result[target_date] = res
        return result


    # Compute full result
    result = {}
    st_year = 2015
    while st_year < 2016:
        result[st_year] = compute_results_for_year(st_year, base_stocks, 0.8, 50, 10, sa)
        st_year += 1
"""
    # Pick Stocks
    sp = NObservationPeriodStockPicker(base_stocks)
    sp.set_stock_analysis_instance(sa)
    top_stocks = sp.pick_stocks(threshold=0.8,
                                target_date=target_date,
                                period_in_days=50,
                                observation_period_length=10,
                                stock_analysis_instance = sa)

    # Compute future gain
    pred_index_date = target_date
    pred_target_date = target_date + relativedelta(days=10)
    print (top_stocks)
    print (sa.compute_gain_for_period(pred_index_date.strftime("%Y-%m-%d"), pred_target_date.strftime("%Y-%m-%d"), base_stocks))
    print (sa.compute_gain_for_period(pred_index_date.strftime("%Y-%m-%d"), pred_target_date.strftime("%Y-%m-%d"), top_stocks))
    """
#-0.19764908857534433
#0.13119245537554558
"""
target_date_str = '2019-06-06'
['AOS', 'ABBV']
0.4402004594983872
0.08600066770051262

'2018-06-06'
['ABBV']
0.8436826279773281
0.7355197550968151
"""