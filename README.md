# Telegram Scraper Bot

This is a Telegram bot for scraping CC information and performing Luhn checks. It is designed to be hosted on Render and supports the following commands:

- `/scr username limit` - Scrapes CC information for the given username and limit.
- `/luhncheck` - Checks a combo file for Luhn validity (owner only).

## Installation

To run the bot locally:

1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt`.
3. Set the `BOT_TOKEN` environment variable with your bot token.
4. Run the bot using `python bot.py`.

## Deploy to Render

To deploy this bot on Render:

1. Fork this repository.
2. Connect your GitHub repository to Render.
3. Set the `BOT_TOKEN` environment variable in Render.
4. Deploy the service.

For detailed instructions on deployment, refer to Render's documentation.
