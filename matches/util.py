from collections import defaultdict
from collections import namedtuple
import http
import json
import math

import local_config
from state import storage


# In binary, this is 32 1s, which is useful for converting steam IDs
THIRTY_TWO_ONES = int(math.pow(2, 32) - 1)


def create_steamapi_connection():
    return http.client.HTTPConnection(
        "api.steampowered.com",
        timeout=10
    )


def get_steam_username(steam_id_32):
    connection = create_steamapi_connection()
    connection.request(
        "GET",
        "ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={steam_id}"
            .format(
            key=local_config.DOTA2_API_KEY,
            steam_id=steam_id_32_to_64(steam_id_32)
        )
    )
    response = connection.getresponse()
    decoded = json.loads(response.read().decode("utf-8"))
    connection.close()
    players = decoded["response"]["players"]
    if len(players) != 1:
        return "Unknown User with ID %s" % steam_id_32
    return players[0]["personaname"]



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


KDA = namedtuple("KDA", ["kills", "deaths", "assists"])


def create_match_notification_message(account_id, match, hero_lookup):
    """
    Create a nice notification message that the player with account_id account_id finished the match.
    :param account_id:
    :param match:
    :return: String that summarizes the player's match.
    """
    msg_template = "{steam_name} just {won_lost} a game playing hero {hero_name} with K/D/A: {k}/{d}/{a}! (match ID: {match})"
    radiant = False
    hero_id = None
    kda = None
    for index, player in enumerate(match["players"]):
        if player["account_id"] == account_id:
            hero_id = player["hero_id"]
            kda = KDA(player["kills"], player["deaths"], player["assists"])
            if index < 5:
                radiant = True
            else:
                radiant = False
            break
    assert hero_id, "No hero found for player {player} in match {match}".format(player=account_id, match=match["match_seq_num"])
    radiant_win = match["radiant_win"]
    if (radiant_win and radiant) or (not radiant_win and not radiant):
        result = "won"
    else:
        result = "lost"

    hero = hero_lookup[hero_id]
    steam_name = get_steam_username(account_id)

    return msg_template.format(steam_name=steam_name, won_lost=result, hero_name=hero, k=kda.kills, d=kda.deaths, a=kda.assists, match=match["match_seq_num"])


def steam_id_32_to_64(steam_id_32):
    """

    :param steam_id_32:
    :return: 64 bit steam ID with some assumptions about the metadata in the first 32 bits
    """
    prefix_64 = 76561197960265728
    return prefix_64 | steam_id_32


def steam_id_64_to_32(steam_id_64):
    steam_id_64 = int(steam_id_64)
    b32_steam_id = steam_id_64 & THIRTY_TWO_ONES
    return b32_steam_id


def validate_and_return_32bit(possible_steam_id):
    """

    :param possible_steam_id:
    :return: Tuple of (bool, int or None) meaning (valid, steam_id)
    """
    try:
        steam_id = int(possible_steam_id)
    except ValueError:
        return (False, None)
    if steam_id & THIRTY_TWO_ONES == steam_id:
        return (True, steam_id)
    return (False, steam_id)


