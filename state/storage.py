from collections import defaultdict

# map from discordId -> list of channels they want to be stalked in
# TODO: will need to persist this somewhere, long term
# TODO: this needs to be made threadsafe
player_channels = defaultdict(lambda: [])

# map from base64 steam ID -> discord ID
steam_to_discord = {}


def add_channel_for_discord_id(player, channel):
    player_channels[player].append(channel)


def get_channels_for_discord_id(player):
    return player_channels[player]


def add_discord_id_for_steam(steam_id, discord_id):
    steam_to_discord[steam_id] = discord_id


def get_discord_id_from_steam(steam_id):
    return steam_to_discord[steam_id]


def check_steam_id_tracked(steam_id):
    return steam_id in steam_to_discord.keys()


def check_discord_id_tracked(discord_id):
    return discord_id in steam_to_discord.values()


def remove_discord_id(discord_id):
    player_channels[discord_id] = []
    for s, d in steam_to_discord.items():
        if d == discord_id:
            del(steam_to_discord, s)

