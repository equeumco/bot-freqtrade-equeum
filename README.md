# Equeum freqtrade bot template

This is template strategy from which you can create your own freqtrade bot and start using Equeum forecasts.
## Before you start

- [⚡️ Sign Up to the Platform](https://equeum.com/)
- [🎓 Read Platform Documentation](https://equeum.gitbook.io/docs/)
- [💬 Join Our Discord Community](https://discord.gg/J7Dwh3xPVD)

## About Equeum
[Equeum](https://equeum.com/) is a platform founded on the same principles as those of Wall Street quant funds: the fundamental truth being that prices of assets do not move at random, and that by gathering and analyzing vast amounts of data, developers can extract data-based signals for use in building quantitative pricing models. In short, Equeum is all about doing an open, large-scale version of what Wall Street quant firms have been doing for decades.

[Equeum](https://equeum.com/) has, in essence, built a creator economy for quants. Any developer can use the platform for free.  Developers retain ownership, and are fairly compensated for what they create. The models they create are provided to investors to help investors make better, more informed, data-driven investment decisions. These investors pay for this value, and the majority of the revenue generated flows back to developers.

[Equeum](https://equeum.com/) platform features:
- A powerful time-series engine for analyzing and extracting signals from massive and diverse sets of data
- A domain-specific language, EQL, that enables developers – collaboratively, iteratively, and in real-time – to create asset price models
- Seamless integration of on- and off-platform data
- A built-in set of shared tools to facilitate data collection and analysis

# Setting up the bot

By default the bot in this repository is configured to run in the [dry mode](https://www.freqtrade.io/en/stable/configuration/#considerations-for-dry-run) and trade all available pairs to demonstrate to you the capabilities of the data Equeum provides.

To switch to production mode, please carefully read [this part of documentation](https://www.freqtrade.io/en/stable/configuration/#switch-to-production-mode) and setup exchange and tokens you want to trade.

Also don't forget to put the right `API Token` from [eqeueum app](https://app.equeum.com/app) to the variable `equeum_token` in the Strategy File.



# Running bot with Docker:

1. Make sure you have Docker installed and running (https://www.docker.com/)
2. Open Shell/terminal/cmd and `cd` to repo folder
3. Download docker images with command  `docker compose -f docker-compose-futures.yml pull`
4. Run the image with command (one of these, of your choice):
	- `docker compose up -d` - to run futures setup
	- `docker compose -f docker-compose-spot.yml up -d` - to run spot setup

Thats all. Now the bot is running and you can [access it](#how-to-access-the-bot).

# Available demo strategies
In the `user_data\strategies` folder you could find several demo strategies:
- `equeumBase.py` - base strategy, which contains all equeum integration code
- `equeum.py` - default strategy for Futures Trading
- `equeumSpot.py` - strategy for Spot trading, basically it cannot short
- `equeumRealtime.py` - strategy for futures trading, which updates trend signal every 10s. Make sure you'll not hit equeum rate limit!

# Running bot on host machine

If you want to run the bot on your host machine, follow installation guide for [*nix platforms](https://www.freqtrade.io/en/stable/installation/) and [windows](https://www.freqtrade.io/en/stable/windows_installation).

Then merge the `user_data` folder from this repository into the folder, you've created during the installation.

To start the bot on futures, run this command in your terminal:
```sh
freqtrade trade
    --logfile /freqtrade/user_data/logs/freqtrade.futures.log \
    --db-url sqlite:////freqtrade/user_data/db/equeum.futures.dry.sqlite \
    --config /freqtrade/user_data/config.equeum.futures.json \
    --strategy EqueumStrategy
```

To start on the spot:
```sh
freqtrade trade
    --logfile /freqtrade/user_data/logs/freqtrade.spot.log \
    --db-url sqlite:////freqtrade/user_data/db/equeum.spot.dry.sqlite \
    --config /freqtrade/user_data/config.equeum.spot.json \
    --strategy EqueumStrategy
```

# How to access the bot:

Open page http://localhost:8080, press `Login` button and enter `freqtrader` as login and `123456` as a password.

It is strongly recommended that you read documentation about [freqtrade user interface](https://www.freqtrade.io/en/stable/rest-api/#frequi)

# How to add equium to existing strategy:

We provide base strategy file, which contains all needed methods to populate equeum data both in live and backtesting modes.

To add these capabilities to your existing strategy, just copy file `EqueumBase.py` into your strategy folder and inherit your strategy from `EqueumBaseStrategy` class:
```py
class MyAwesomeStrategy(EqueumBaseStrategy):
```

# Additinal commands

## How to download data with Docker for single coin

```
docker compose run freqtrade download-data \
	-p ETH/USDT \
	--days 365 \
	--exchange binance \
	-t 1m \
	--trading-mode futures \
	--userdir user_data
```

## How to download data with Docker for all equeum tradable coins
```sh
docker compose run freqtrade download-data \
	--pairs-file pairs.json \
	--days 250 \
	--exchange binance \
	-t 1m \
	--trading-mode futures \
	--userdir user_data
```

## How to backtest with Docker

```
docker compose run freqtrade backtesting \
        --timerange=20220201- \
        --strategy-path user_data/strategies \
        --config user_data/config.equeum.ETH.futures.json \
        --strategy EqueumStrategy
```

## Questions?

Join our [Discord community](https://discord.gg/J7Dwh3xPVD) to get fresh news, ask for help and find new strategy ideas.

## Resources

- [⚡️ Website](https://equeum.com/)
- [🎓 Documentation](https://equeum.gitbook.io/docs/)
- [💬 Discord community](https://discord.gg/J7Dwh3xPVD)
- [🤖 Jesse Trade strategy](https://github.com/equeumco/bot-jesse-equeum)
- [🤖 Freqtrade strategy](https://github.com/equeumco/bot-freqtrade-equeum)
