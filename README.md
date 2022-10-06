# freqtrade bot from Roman with love

Freqtrade bot, utilizing equeum API.

# How to run the bot with Docker:

1. Make sure you have Docker installed and running (https://www.docker.com/)
2. Open Shell/terminal/cmd and `cd` to repo folder
3. Download docker images with command  `docker compose -f docker-compose-futures.yml pull`
4. Run the image with command (one of these, of your choice):
	- `docker compose -f docker-compose-futures.yml up -d` - to run futures setup
	- `docker compose -f docker-compose-spot.yml up -d` - to run spot setup
	- `docker compose -f docker-compose-benchmark.yml up -d` - to run both futures and spot together

# How to access the bot:
By default spot & futures bots are running on different ports:
- futures - http://localhost:8080
- spot - http://localhost:8081

For benchmark you can access any of them and configure both bots in one UI