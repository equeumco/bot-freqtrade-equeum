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
    equeum_signals_api_endpoint = "https://graphql-apis.equeum.com/tickers/signals"
    equeum_history_api_endpoint = "https://graphql-apis.equeum.com/tickers/history"

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
            endpoint = self.equeum_history_api_endpoint
            params = {
                "ticker": f"{ticker}",
                'from': pd.Timestamp(df.iloc[0]['date']).timestamp(),
                'to': pd.Timestamp(df.iloc[-1]['date']).timestamp(),
                "token": self.equeum_token
            }
            logger.info(f"equeum: requesting: {self.equeum_history_api_endpoint} with payload: {params}")

            res = requests.get(endpoint, params)
            eq_data = res.json()
            
            if ('status' in eq_data and eq_data['status'] == 'error'):
                logger.error("Equeum Exception -> " + eq_data['error'])
            
            logger.info(f"equeum responses {res.status_code}")

            self.equeum_data[pair] = pd.DataFrame(data=eq_data)

            logger.info(f"equeum: got response {self.equeum_data[pair].shape}")

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
        self.equeum_load_data(df)
        
        # get pair data
        history_data = self.equeum_data[pair]
        
        logger.info(f'df shape before join {df.shape}')

        history_df = pd.DataFrame(data=history_data)
        history_df['date'] = pd.to_datetime(history_df['time'], unit='s', utc=True)
        df = df.join(history_df.set_index('date'), how="left", on='date') # Join all history data to dataframe
        
        df['equeum_trendline'] = np.where(df['forecast'] > 0, 'up', np.where(df['forecast'] < 0, 'down', 'unknown')) 
        
        logger.info(f'df shape after join {df.shape}')
        # logger.info('df', df)
        # logger.info('equeum_trendline', df['equeum_trendline'])
        
        return df

    def populate_equeum_data_live(self, df: DataFrame, pair) -> DataFrame:
        # update ticker
        ticker = self.equeum_map_ticker(pair)
            
        # request data to API
        params = {
            "ticker": ticker,
            "token": self.equeum_token
        }
        
        # logger.info(f"equeum: requesting: {self.config['equeum']['signals_api_endpoint']} with payload: {params}")

        res = requests.get(self.equeum_signals_api_endpoint, params)
        eq_response = res.json()
        
        # logger.info(f"equeum: response: {res.status_code} = {eq_response}")
        
        # validate response
        if ('status' in eq_response and eq_response['status'] == 'error'):
            logger.error("Equeum Exception -> " + eq_response['error'])
            df['equeum_trendline'] = 'unknown'
            return df
        
        # get timestamp
        date = pd.to_datetime(datetime.strptime(eq_response['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")).tz_localize('utc')
        
        # update dataframe
        df.loc[(df['date'] >= date), 'equeum_trendline'] = eq_response['trendline']

        return df
