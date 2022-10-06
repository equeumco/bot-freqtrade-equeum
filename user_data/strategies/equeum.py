# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---

from pandas import DataFrame
import requests
import logging
import numpy as np

from freqtrade.strategy import (IStrategy, informative)

# --------------------------------
# Add your lib to import here

logger = logging.getLogger(__name__)

# This class is a sample. Feel free to customize it.


class EqueumStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = True

    # disable ROI
    minimal_roi = {
        "0": 100
    }

    # disable stop loss, right?
    stoploss = -1
    trailing_stop = False

    # Optimal timeframe for the strategy.
    timeframe = '1m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 0
    
    equeum_data = {}

    plot_config = {
        "main_plot": {},
        "subplots": {
            "equeum": {
                "equeum_trend": {
                    "color": "#6ac554",
                    "type": "line"
                },
                "equeum_value": {
                    "color": "#911255",
                    "type": "line"
                },
                "equeum_trendline": {
                    "color": "#e8525e",
                    "type": "line"
                }
            }
        }
    }

    def populate_equeum_data(self, df: DataFrame, ticker) -> DataFrame:
        # request data to API
        params = {
            "ticker": ticker,
            "token": self.config['equeum']['api_token']
        }
        # logger.info(f"equeum: requesting: {self.config['equeum']['api_endpoint']} with payload: {params}")
        
        res = requests.get(self.config['equeum']['api_endpoint'], params)
        eq_data = res.json()
        
        if not ticker in self.equeum_data:
            self.equeum_data[ticker] = []
        
        # store it localy in memory
        self.equeum_data[ticker].append(eq_data)
        
        # logger.info(f"equeum: response: {eq_data}")
        
        # store only last 999 or less data points, since dataframe is always 999 candles
        self.equeum_data[ticker] = self.equeum_data[ticker][-df.shape[0]:]
        
        # merge equeum data into dataframe
        for index, item in enumerate(reversed(self.equeum_data[ticker])):
            df.at[df.index[-(index+1)], 'equeum_trendline'] = item['trendline']
            df.at[df.index[-(index+1)], 'equeum_duration'] = item['duration']
            df.at[df.index[-(index+1)], 'equeum_value'] = item['value']
            
        return df
        
        

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # request prediction data
        ticker = metadata['pair'].split('/')[0]
        
        self.populate_equeum_data(df, ticker)

        # transform trend value for visual enterpretation
        df["equeum_trend"] = np.where(df["equeum_trendline"] == "up", 100, np.where(df["equeum_trendline"] == "down", -100, 0))

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df['equeum_trendline'] == 'up') &
                (self.config['equeum']['enable_long'])
            ),
            'enter_long'] = 1

        df.loc[
            (
                (df['equeum_trendline'] == 'down') &
                (self.config['equeum']['enable_short'])
            ),
            'enter_short'] = 1

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (
                (df['equeum_trendline'] == 'down')
            ),

            'exit_long'] = 1

        df.loc[
            (
                (df['equeum_trendline'] == 'up')
            ),
            'exit_short'] = 1

        return df
