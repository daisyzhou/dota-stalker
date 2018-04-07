from integrations import notify_queue
from matches import match_stream
from state import storage
from integrations.discord import notifier as discord_notifier
from integrations.discord.oauth import app as discord_oauth_app
from matches import util

import queue
import threading

ms = match_stream.MatchStream()
ms.start(5)

discord_notifier_thread = threading.Thread(target=discord_notifier.run_bot, daemon=True)
discord_notifier_thread.start()

discord_oauth_thread = threading.Thread(target=discord_oauth_app.run_steam_id_getter, daemon=True)
discord_oauth_thread.start()

heroes = util.get_heroes()

for match in ms:
    players_in_match = set([
        player["account_id"]
        for player in match["players"]
        if "account_id" in player  # Bots have no account_id
    ])
    for player in players_in_match:
        if player in storage.players.keys():
            try:
                message = util.create_match_notification_message(player, match, heroes)
                notify_queue.matches_to_notify.put((player, message), timeout=5)
            except queue.Full:
                print("ERROR: Queue full when enqueuing match to notify.  Something is probably slow.")

