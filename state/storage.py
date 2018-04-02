from collections import defaultdict

# map from user -> list of channels they're in
# TODO: will need to persist this somewhere, long term
# TODO: this needs to be made threadsafe
users = defaultdict(lambda: [])

