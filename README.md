# Opportunity Radar

A 24/7 agent that scans Devpost, Unstop, GitHub bounties and the open web (via a search engine,
which surfaces LinkedIn posts, Devfolio, Kaggle, HackerEarth...) for hackathons, contests, bounties
and jobs matching your skills and interests, then pings you on Telegram / Discord.

## Setup
    pip install -r requirements.txt
    cp config.example.json config.json   # edit skills + interests
    cp .env.example .env                 # add Telegram/Discord/Anthropic keys (all optional)
    python radar.py once                 # test
    python radar.py run                  # run forever (use systemd, Docker, pm2 or a cheap VPS for 24/7)

Telegram: create a bot with @BotFather, put the token in `.env`, message the bot, then get your chat id
from `https://api.telegram.org/bot<TOKEN>/getUpdates`.

With `ANTHROPIC_API_KEY` set, Claude re-scores each item, drops spam and extracts the prize.

## Notes
- Sources use unofficial public endpoints; they may change. Each source fails independently.
- LinkedIn is covered through search-engine results only. Do not scrape LinkedIn directly (against its ToS).
- Add a source: write a generator yielding dicts (`source,title,url,desc,prize`) and append it to `SOURCES`.

## Security
- Keys live only in your local `.env` (git-ignored). Never paste them into code or `config.json`. On Linux/macOS run `chmod 600 .env`.
- Logs automatically mask configured keys. If a key ever leaks anyway, revoke and regenerate it.
- Run `python test_radar.py` after any change.


## Disclaimer
This project is provided "as is", with no warranty of any kind. It is a hobby project and is not affiliated with
Devpost, Unstop, GitHub, LinkedIn or Anthropic. Results can be wrong, incomplete or out of date, so always check the
official page and its rules before entering anything. You are responsible for following each website's terms of service
and for keeping your own API keys private. Never share your `.env` file.
