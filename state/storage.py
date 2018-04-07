from collections import defaultdict

# map from discordId -> list of channels they want to be stalked in
# TODO: will need to persist this somewhere, long term
# TODO: this needs to be made threadsafe
player_channels = defaultdict(lambda: [])

# map from base64 steam ID -> discord ID
steam_to_discord = {}
