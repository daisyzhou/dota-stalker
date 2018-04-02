from integrations import notify_queue
from matches import match_stream
from state import storage
from integrations.discord import notifier as discord_notifier

import queue
import threading

ms = match_stream.MatchStream()
ms.start(5)

t = threading.Thread(target=discord_notifier.run_bot, daemon=True)
t.start()

for match in ms:
    players_in_match = set([
        player["account_id"]
        for player in match["players"]
        if "account_id" in player  # Bots have no account_id
    ])
    for player in players_in_match:
        if player in storage.players.keys():
            try:
                notify_queue.matches_to_notify.put((player, match), timeout=5)
            except queue.Full:
                print("ERROR: Queue full when enqueuing match to notify.  Something is probably slow.")

