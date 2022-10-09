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

from equeumBase import EqueumBaseStrategy

# --------------------------------
# Add your lib to import here

logger = logging.getLogger(__name__)

# This class is a sample. Feel free to customize it.


class EqueumBacktestStrategy(EqueumBaseStrategy):
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
    
    def bot_start(self):
        # Can this strategy go short?
        self.can_short = self.config['equeum']['enable_short']
        
        # load backttest history data
        self.equeum_load_data()        
            
    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        
        # populate equeum data
        self.populate_equeum_data(df, metadata['pair'])
        
        # transform trend value for visual enterpretation
        df["equeum_trend"] = np.where(df["equeum_trendline"] == "up",
            100, np.where(df["equeum_trendline"] == "down", -100, 0))
        
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