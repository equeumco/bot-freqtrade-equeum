# freqtrade bot from Roman with love

Freqtrade bot, utilizing equeum API.

# Setting up the bot

Byt default this bot in the repository is configured to run in the [dry mode](https://www.freqtrade.io/en/stable/configuration/#considerations-for-dry-run) and trade all available pairs to demonstrate you capabilities of the data equeum provides.

To switch to production mode please carefully read [this part of documentation](https://www.freqtrade.io/en/stable/configuration/#switch-to-production-mode) and setup exchange and tokens you want to trade.

Also don't forget to put the right `API Token` from [eqeueum app](https://app.equeum.com/app) to the configuration file at section `eqeueum.api_token`.



# Running bot with Docker:

1. Make sure you have Docker installed and running (https://www.docker.com/)
2. Open Shell/terminal/cmd and `cd` to repo folder
3. Download docker images with command  `docker compose -f docker-compose-futures.yml pull`
4. Run the image with command (one of these, of your choice):
	- `docker compose -f docker-compose-futures.yml up -d` - to run futures setup
	- `docker compose -f docker-compose-spot.yml up -d` - to run spot setup
	- `docker compose -f docker-compose-benchmark.yml up -d` - to run both futures and spot together

Thats all all, now the bot is running and you can [access it](#how-to-access-the-bot).

# Running bot on host machine

If you want to run the bot on your host machine, consider to follow installation guide for [*nix platforms](https://www.freqtrade.io/en/stable/installation/) and [windows](https://www.freqtrade.io/en/stable/windows_installation).

Then merge the `user_data` folder from this repository into the folder, you've creted during the installation.

To start the bot on futures run this in terminal:
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

By default spot & futures bots are running on different ports:
- futures - http://localhost:8080
- spot - http://localhost:8081

For benchmark you can access any of them and configure both bots in one UI.
It is strongly recommended to read documentation about [freqtrade user interface](https://www.freqtrade.io/en/stable/rest-api/#frequi)

# How to add equium to existing strategy:

Add this into your configuration file:
```json

    "equeum": {
        "api_token": "PUT YOUR TOKEN HERE",
        "api_endpoint": "https://graphql-apis.equeum.com/tickers/signals",
        "enable_long": true,
        "enable_short": true
    },
```

And this to your stategy file:

```py
	equeum_data = {}
    
    equem_ticker_map = {
        "1000SHIB": "SHIB"
    }
	
    def map_equeum_ticker(self, ft_ticker):
        if ft_ticker in self.equem_ticker_map:
            return self.equem_ticker_map[ft_ticker]
        
        return ft_ticker
	
	def populate_equeum_data(self, df: DataFrame, ticker) -> DataFrame:
        # update ticker
        ticker = self.map_equeum_ticker(ticker)
        
        # request data to API
        params = {
            "ticker": ticker,
            "token": self.config['equeum']['api_token']
        }
        
        res = requests.get(self.config['equeum']['api_endpoint'], params)
        eq_data = res.json()
        
        if not ticker in self.equeum_data:
            self.equeum_data[ticker] = []
        
        # store it localy in memory
        self.equeum_data[ticker].append(eq_data)
        
        # store only last 999 or less data points, since dataframe is always 999 candles
        self.equeum_data[ticker] = self.equeum_data[ticker][-df.shape[0]:]
        
        # merge equeum data into dataframe
        for index, item in enumerate(reversed(self.equeum_data[ticker])):
            df.at[df.index[-(index+1)], 'equeum_trendline'] = item['trendline']
            df.at[df.index[-(index+1)], 'equeum_duration'] = item['duration']
            df.at[df.index[-(index+1)], 'equeum_value'] = item['value']
            
        return df

```

Now it's tome to update `populate_indicators`:

```py
self.populate_equeum_data(df, ticker)
```

And finally modify entry/exit signals based on equeum data:

```py
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
```