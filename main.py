# Temporary main for testing/verification
from matches import match_stream

ms = match_stream.MatchStream()
ms.start(5)

for match in ms:
    players_in_match = [
        player["account_id"]
        for player in match["players"]
        if "account_id" in player  # Bots have no account_id
    ]
    for player in players_in_match:
        if player in

