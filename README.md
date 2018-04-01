Bot to notify you when certain players have finished a dota match.
This is just for fun, for myself, for now, so this README serves as notes to myself.

## local config
Requires a file in ./local_config.py that looks like:

```python
# Your dota 2 developer key
# http://steamcommunity.com/dev/apikey
DOTA2_API_KEY = ""

# Your telegram API key if you're using the telegram integration
# https://core.telegram.org/api/obtaining_api_id
TELEGRAM_BOT_API_KEY = ""

# Your discord bot API key if you're using the discord integration
# https://discordapp.com/developers/docs/intro
DISCORD_BOT_API_KEY = ""
```

## other dependencies
### For discord integration:
```bash
venv/bin/pip install -U discord.py
```

To add the bot to a server: https://discordapp.com/oauth2/authorize?client_id=BOT_CLIENT_ID_GOES_HERE&scope=bot&permissions=0

