from collections import defaultdict

# map from steamID -> list of (user, channels) they're in
# TODO: will need to persist this somewhere, long term
# TODO: this needs to be made threadsafe
players = defaultdict(lambda: [])

# map from discord ID -> base64 steam ID
steam_ids = {}
