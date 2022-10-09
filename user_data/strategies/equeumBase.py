# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---

from pandas import DataFrame
import requests
import logging
import numpy as np
import pandas as pd

from freqtrade.strategy import (IStrategy, informative)

# --------------------------------
# Add your lib to import here

logger = logging.getLogger(__name__)


class EqueumBaseStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # disable ROI
    minimal_roi = {
        "0": 100
    }

    # disable stop loss
    stoploss = -1
    trailing_stop = False

    # Optimal timeframe for the strategy.
    timeframe = '1m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    use_exit_signal = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 0

    equeum_data = {}

    equem_ticker_map = {
        "1000SHIB": "SHIB"
    }

    def bot_start(self):
        # Can this strategy go short?
        self.can_short = self.config['equeum']['enable_short']

        # load backtest history data
        if self.config['runmode'].value == 'backtest':
            self.equeum_load_data()

    def equeum_map_ticker(self, pair):
        ticker = pair.split('/')[0]
        if ticker in self.equem_ticker_map:
            return self.equem_ticker_map[ticker]

        return ticker

    def equeum_load_data(self):

        for pair in self.config['exchange']['pair_whitelist']:
            ticker = self.equeum_map_ticker(pair)
            # request data to API
            endpoint = "https://dev-graphql-apis.equeum.com/tickers/history"
            params = {
                "ticker": f"{ticker}",
                "from": 1640984400,  # 1 jan 2022
                "to": 1672520400,  # 1 jan 2023
                "token": "WPyiKanyl-7l0w844qefb7W6OQ1sj3Q671YXMgj5GMT3t"
            }
            logger.info(
                f"equeum: requesting: {self.config['equeum']['api_endpoint']} with payload: {params}")

            res = requests.get(endpoint, params)
            eq_data = res.json()

            self.equeum_data[pair] = pd.DataFrame(data=eq_data)

            logger.info(f"equeum: got response {self.equeum_data[pair].shape}")
            logger.info(f"equeum: got response {self.equeum_data[pair].tail()}")

    def equeum_map_trend(self, timestamp, pair):
        try:
            eqdf = self.equeum_data[pair]
            # find forecast
            forecast = eqdf[eqdf['time'] == timestamp]['forecast'].values[0]

            # map values
            if forecast > 0:
                return 'up'
            elif forecast < 0:
                return 'down'
        except:
            return 'unknown'


    def populate_equeum_data(self, df: DataFrame, pair) -> DataFrame:
        # timestamp 
        df['timestamp'] = df['date'].map(lambda x: int(pd.Timestamp.timestamp(x)))
        
        if self.config['runmode'].value in ('live', 'dry_run'):
            return self.populate_equeum_data_live(df, pair)
        else:
            return self.populate_equeum_data_backtest(df, pair)

    def populate_equeum_data_backtest(self, df: DataFrame, ticker) -> DataFrame:
        df["equeum_trendline"] = df['timestamp'].map(lambda x: self.equeum_map_trend(x, ticker))
        return df

    def populate_equeum_data_live(self, df: DataFrame, pair) -> DataFrame:
        # update ticker
        ticker = self.equeum_map_ticker(pair)

        # request data to API
        params = {
            "ticker": ticker,
            "token": self.config['equeum']['api_token']
        }
        # logger.info(f"equeum: requesting: {self.config['equeum']['api_endpoint']} with payload: {params}")

        res = requests.get(self.config['equeum']['api_endpoint'], params)
        eq_data = res.json()

        # validate the response
        if 'trendline' not in eq_data:
            logger.warning('Provided equeum API is wrong! Please double check your config.')
            # mock the response
            df.at[df.index[-1], 'equeum_trendline'] = 'unknown'
            df.at[df.index[-1], 'equeum_duration'] = ''
            df.at[df.index[-1], 'equeum_value'] = 0
            return df

        if not ticker in self.equeum_data:
            self.equeum_data[ticker] = []

        # store it localy in memory
        self.equeum_data[ticker].append(eq_data)

        # logger.info(f"equeum: response: {eq_data}")

        # store only last 999 or less data points, since dataframe is always 999 candles
        self.equeum_data[ticker] = self.equeum_data[ticker][-df.shape[0]:]

        # merge equeum data into dataframe
        for index, item in enumerate(reversed(self.equeum_data[ticker])):
            df.at[df.index[-(index + 1)], 'equeum_trendline'] = item['trendline']
            df.at[df.index[-(index + 1)], 'equeum_duration'] = item['duration']
            df.at[df.index[-(index + 1)], 'equeum_value'] = item['value']

        return df
