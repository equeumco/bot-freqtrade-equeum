# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---

from pandas import DataFrame
import requests
import logging
import numpy as np
import pandas as pd
from equeumBase import EqueumBaseStrategy

from freqtrade.strategy import (IStrategy, informative)

# --------------------------------
# Add your lib to import here

logger = logging.getLogger(__name__)

# This class is a sample. Feel free to customize it.


class EqueumStrategy(EqueumBaseStrategy):
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
    
    can_short = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 0
    
    # EQUEUM CONFIGURATION
    equeum_token = "GET YOUR TOKEN AT HTTPS://APP.EQUEUM.COM"
    
    @property
    def protections(self):
        return  [
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 0
            }
        ]
    
    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # populate equeum data
        df = self.populate_equeum_data(df, metadata['pair'])

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:

        df.loc[
            (
                (df['equeum_trendline'] == 'up')
            ),
            'enter_long'] = 1

        df.loc[
            (
                (df['equeum_trendline'] == 'down')
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
