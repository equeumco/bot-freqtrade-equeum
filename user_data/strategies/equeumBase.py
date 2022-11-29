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
    
    equeum_token = "GET YOUR TOKEN AT HTTPS://APP.EQUEUM.COM"
    equeum_signals_api_endpoint = "https://graphql-apis.equeum.com/resources/signals"

    equeum_ticker_map = {
        "1000SHIB": "SHIB",
    }
    
    equeum_data = {}

    def equeum_map_ticker(self, pair):
        ticker = pair.split('/')[0]
        if ticker in self.equeum_ticker_map:
            return self.equeum_ticker_map[ticker]

        return ticker

    def equeum_load_data(self, df: DataFrame):

        for pair in self.config['exchange']['pair_whitelist']:
            ticker = self.equeum_map_ticker(pair)
            # request data to API
            endpoint = self.equeum_signals_api_endpoint
            params = {
                "r": f"{ticker}",
                'from': pd.Timestamp(df.iloc[0]['date']).timestamp(),
                'to': pd.Timestamp(df.iloc[-1]['date']).timestamp(),
                "token": self.equeum_token,
                "resFormat": "json"
            }
            logger.info(f"equeum: requesting: {self.equeum_signals_api_endpoint} with payload: {params}")

            res = requests.get(endpoint, params)
            eq_data = res.json()
            
            if ('status' in eq_data and eq_data['status'] == 'error'):
                logger.error("Equeum Exception -> " + eq_data['error'])
            
            logger.info(f"equeum: got response {len(eq_data)}")
            
            return eq_data
            

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
        # choose right environment
        if self.config['runmode'].value in ('live', 'dry_run'):
            return self.populate_equeum_data_live(df, pair)
        else:
            return self.populate_equeum_data_backtest(df, pair)

    def populate_equeum_data_backtest(self, df: DataFrame, pair) -> DataFrame:
        # load data
        history_data = self.equeum_load_data(df)
        
        logger.info(f'df shape before join {df.shape}')

        # prepare dataframe to join
        history_df = pd.DataFrame(data=history_data)
        history_df['date'] = pd.to_datetime(history_df['time'], unit='s', utc=True)
        history_df = history_df.set_index('date')
        history_df = history_df.asfreq(freq="1min", method='ffill')
        
        # Join all history data to dataframe
        df = df.join(history_df, how="left", on='date')
        
        # add signals
        df['equeum_trendline'] = df['trendline']
        
        logger.info(f'df shape after join {df.shape}')
        
        return df

    def populate_equeum_data_live(self, df: DataFrame, pair) -> DataFrame:
        # update ticker
        ticker = self.equeum_map_ticker(pair)
            
        # request data to API
        params = {
            "ticker": ticker,
            "token": self.equeum_token,
            "resFormat": "json"
        }
        
        logger.info(f"equeum: requesting: {self.equeum_signals_api_endpoint} with payload: {params}")

        res = requests.get(self.equeum_signals_api_endpoint, params)
        eq_response = res.json()
        
        logger.info(f"equeum: response: {res.status_code} = {eq_response}")
        
        # validate response
        if ('status' in eq_response and eq_response['status'] == 'error'):
            logger.error("Equeum Exception -> " + eq_response['error'])
            df['equeum_trendline'] = 'unknown'
            return df
        
        signal = eq_response[0]
        
        # get timestamp
        date = pd.to_datetime(signal['time'], unit="s", utc=True)
        
        # update dataframe
        df.loc[(df['date'] >= date), 'equeum_trendline'] = signal['trendline']

        return df
