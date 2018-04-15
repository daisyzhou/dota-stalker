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
DISCORD_BOT_CLIENT_ID = ""
DISCORD_BOT_CLIENT_SECRET = ""
```

## database
```sql
create table subscriptions (id integer primary key, owner text, steam_id integer, sub_channel text, sub_user text);
```

```sql
create index on subscriptions(steam_id);
```

## other dependencies
### For discord integration:
Setup:
```bash
venv/bin/pip3  install -r requirements.txt -r integrations/discord/oauth/requirements.txt
```

To add the bot to a server: https://discordapp.com/oauth2/authorize?client_id=BOT_CLIENT_ID_GOES_HERE&scope=bot&permissions=0


# TODO
* make the storage threadsafe (it's super definitely not right now... o_o)
* might want to stop using discord.py library and implement all that gateway stuff ourselves?
* add a testing framework for the discord bot (use a mock MatchStream)
* persist state somewhere
* disallow using the anonymous user ID
* if it starts getting too slow, parallelize the sending messages to discord part

