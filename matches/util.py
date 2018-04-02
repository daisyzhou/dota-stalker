import http
import json
from collections import defaultdict

import local_config


def create_steamapi_connection():
    return http.client.HTTPConnection(
        "api.steampowered.com",
        timeout=10
    )


def get_heroes():
    connection = create_steamapi_connection()
    connection.request(
        "GET",
        "/IEconDOTA2_570/GetHeroes/v1?key={key}&language=en_us"
            .format(
            key=local_config.DOTA2_API_KEY
        )
    )
    response = connection.getresponse()
    decoded = json.loads(response.read().decode("utf-8"))
    connection.close()
    heroes = defaultdict(lambda: "Unknown Hero")
    for hero_item in decoded["result"]["heroes"]:
        heroes[hero_item["id"]] = hero_item["localized_name"]
    return heroes


def create_match_notification_message(account_id, match, hero_lookup):
    """
    Create a nice notification message that the player with account_id account_id finished the match.
    :param account_id:
    :param match:
    :return: String that summarizes the player's match.
    """
    msg_template = "just %s a game playing hero %s! Match ID: %d"
    radiant = False
    hero_id = None
    for index, player in enumerate(match["players"]):
        if player == account_id:
            hero_id = player["hero_id"]
            if index < 5:
                radiant = True
            else:
                radiant = False
            break
    radiant_win = match["radiant_win"]
    if (radiant_win and radiant) or (not radiant_win and not radiant):
        result = "won"
    else:
        result = "lost"

    hero = hero_lookup[hero_id]

    return msg_template % (result, hero, match["match_seq_num"])
