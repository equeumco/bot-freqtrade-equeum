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
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter, 
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here

logger = logging.getLogger(__name__)

# This class is a sample. Feel free to customize it.


class EqueumAdvancedStrategy(EqueumBaseStrategy):
    INTERFACE_VERSION = 3

    # disable ROI
    minimal_roi = {
        "0": 100
    }

    # disable stop loss
    stoploss = -1
    trailing_stop = False

    # Optimal timeframe for the strategy.
    timeframe = '5m'

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
        
    short_ma_type = CategoricalParameter(["ema", "hma", "tema"], default="hma", space="buy")
    short_ma_length = IntParameter(5, 50, default=20, space="buy")
    
    long_ma_type = CategoricalParameter(["ema", "hma", "tema"], default="hma", space="buy")
    long_ma_length = IntParameter(20, 200, default=100, space="buy")
    
    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # populate equeum data
        df = self.populate_equeum_data(df, metadata['pair'])
        
        df["short_ema"] = ta.EMA(df, self.short_ma_length.value)
        df["short_hma"] = qtpylib.hma(df["close"], self.short_ma_length.value)
        df["short_tema"] = ta.TEMA(df, self.short_ma_length.value)
        
        df["long_ema"] = ta.EMA(df, self.long_ma_length.value)
        df["long_hma"] = qtpylib.hma(df["close"], self.long_ma_length.value)
        df["long_tema"] = ta.TEMA(df, self.long_ma_length.value)

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:

        df.loc[
            (
                (qtpylib.crossed_above(df[f"short_{self.short_ma_type.value}"], df[f"long_{self.long_ma_type.value}"])) &
                (df['equeum_trendline'] == 'up')
            ),
            'enter_long'] = 1

        df.loc[
            (
                (qtpylib.crossed_below(df[f"short_{self.short_ma_type.value}"], df[f"long_{self.long_ma_type.value}"])) &
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
