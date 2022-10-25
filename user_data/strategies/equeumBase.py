# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---

from datetime import datetime
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

    equem_ticker_map = {
        "1000SHIB": "SHIB",
    }
    
    equeum_data = {}

    def bot_start(self):
        # Can this strategy go short?
        self.can_short = self.config['equeum']['enable_short']

    def equeum_map_ticker(self, pair):
        ticker = pair.split('/')[0]
        if ticker in self.equem_ticker_map:
            return self.equem_ticker_map[ticker]

        return ticker

    def equeum_load_data(self, df: DataFrame):

        for pair in self.config['exchange']['pair_whitelist']:
            ticker = self.equeum_map_ticker(pair)
            # request data to API
            endpoint = self.config['equeum']['history_api_endpoint']
            params = {
                "ticker": f"{ticker}",
                'from': pd.Timestamp(df.iloc[0]['date']).timestamp(),
                'to': pd.Timestamp(df.iloc[-1]['date']).timestamp(),
                "token": self.config['equeum']['api_token']
            }
            logger.info(
                f"equeum: requesting: {self.config['equeum']['history_api_endpoint']} with payload: {params}")

            res = requests.get(endpoint, params)
            eq_data = res.json()
            
            logger.info(f"equeum responses {res.status_code}")

            self.equeum_data[pair] = pd.DataFrame(data=eq_data)

            # logger.info(f"equeum: got response {self.equeum_data[pair].shape}")
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
        if self.config['runmode'].value in ('live', 'dry_run'):
            return self.populate_equeum_data_live(df, pair)
        else:
            return self.populate_equeum_data_backtest(df, pair)

    def populate_equeum_data_backtest(self, df: DataFrame, pair) -> DataFrame:
        # load data
        self.equeum_load_data(df)
        
        # get pair data
        history_data = self.equeum_data[pair]

        history_df = pd.DataFrame(data=history_data)
        history_df['date'] = pd.to_datetime(history_df['time'], unit='s', utc=True)
        df = df.join(history_df.set_index('date'), on='date') # Join all history data to dataframe
        
        df['equeum_trendline'] = np.where(df['forecast'] > 0, 'up', np.where(df['forecast'] < 0, 'down', 'unknown')) 
        
        # logger.info('df', df)
        # logger.info('equeum_trendline', df['equeum_trendline'])
        
        return df

    def populate_equeum_data_live(self, df: DataFrame, pair) -> DataFrame:
        # update ticker
        ticker = self.equeum_map_ticker(pair)

        # request data to API
        params = {
            "ticker": ticker,
            "token": self.config['equeum']['api_token']
        }
        logger.info(f"equeum: requesting: {self.config['equeum']['signals_api_endpoint']} with payload: {params}")

        res = requests.get(self.config['equeum']['signals_api_endpoint'], params)
        eq_data = res.json()
        
        logger.info(f"equeum: response: {res.status_code} = {eq_data}")
        
        date = pd.to_datetime(datetime.strptime(eq_data['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")).tz_localize('utc')

        if eq_data['trendline'] == 'up':
            df.loc[
                (
                    (df['date'] >= date) &
                    (df['volume'] > 0) 
                ),
                'equeum_trendline'] = 'up'
        elif eq_data['trendline'] == 'down':
            df.loc[
                (
                    (df['date'] >= date) &
                    (df['volume'] > 0) 
                ),
                'equeum_trendline'] = 'down'


        return df