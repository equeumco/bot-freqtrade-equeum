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
    process_only_new_candles = False

    use_exit_signal = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 0

    equem_ticker_map = {
        "1000SHIB": "SHIB"
    }

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
                    },
                "equeum_h": {
                    "color": "#333333",
                    "type": "line"
                    },
                "equeum_l": {
                    "color": "#333333",
                    "type": "line"
                    }
                }
        }
    }
    
    @property
    def protections(self):
        return [
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 0
            }
        ]

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        logger.info('----------------------------------')
        logger.info('1. populate_indicators')

        # populate equeum data
        df = self.populate_equeum_data(df, metadata['pair'])

        # transform trend value for visual enterpretation
        df["equeum_trend"] = np.where(df["equeum_trendline"] == "up",
                                      100, np.where(df["equeum_trendline"] == "down", -100, 0))

        df['equeum_h'] = 105
        df['equeum_l'] = -105

        logger.info(df.tail())

        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        logger.info(f"2. populate_entry_trend, equeum={df['equeum_trendline'].iloc[-1]}")
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

        logger.info(f'enter_long={df["enter_long"].iloc[-1]} / enter_short={df["enter_short"].iloc[-1]}')

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        logger.info(f"3. populate_exit_trend, equeum={df['equeum_trendline'].iloc[-1]}")
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
        
        logger.info(f'exit_long={df["exit_long"].iloc[-1]} / exit_short={df["exit_short"].iloc[-1]}')

        return df
