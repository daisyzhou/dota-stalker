from collections import defaultdict
import psycopg2
from psycopg2.extras import DictCursor

from discord import Object


global_connection = psycopg2.connect("postgresql://postgres:2fats@localhost:5432/postgres")
global_connection.autocommit = True


def add_channel_for_discord_id(discord_user, steam_id, channel):
    with global_connection.cursor() as curs:
        curs.execute("INSERT INTO subscriptions(owner,steam_id,sub_channel,sub_user) VALUES (%s, %s, %s, null)", (discord_user, steam_id, channel.id))


def add_discord_id_for_steam(steam_id, discord_id):
    with global_connection.cursor() as curs:
        curs.execute("INSERT INTO discord_users VALUES (%s, %s)", (discord_id, steam_id))


def get_discord_id_from_steam(steam_id):
    with global_connection.cursor(cursor_factory=DictCursor) as curs:
        curs.execute("SELECT discord_id FROM discord_users WHERE steam_id=%s", (steam_id,))
        result = curs.fetchall()
    if len(result) == 0:
        return None
    return result[0]["discord_id"]


def steam_from_discord(discord_id):
    with global_connection.cursor(cursor_factory=DictCursor) as curs:
        curs.execute("SELECT steam_id FROM discord_users WHERE discord_id=%s", (discord_id,))
        result = curs.fetchall()
    assert len(result) == 1, "Must have exactly one steam ID for discord ID"
    return result[0]["steam_id"]


def get_owners_and_channels_for_steam_id(steam_id):
    """

    :param steam_id:
    :return: Map from channel to set of owners that subscribed to the given steam ID
    """
    with global_connection.cursor(cursor_factory=DictCursor) as curs:
        curs.execute("SELECT owner, sub_channel FROM subscriptions WHERE steam_id=%s", (steam_id,))
        result = curs.fetchall()
    channel_map = defaultdict(lambda: set())
    for row in result:
        sub_channel = Object(id=row["sub_channel"])
        owner = row["owner"]
        channel_map[sub_channel].add(owner)
    return channel_map


def check_steam_id_tracked(steam_id):
    with global_connection.cursor(cursor_factory=DictCursor) as curs:
        curs.execute("SELECT sub_channel FROM subscriptions WHERE steam_id=%s", (steam_id,))
        result = curs.fetchall()
    return len(result) > 0


def check_discord_id_tracked(discord_id):
    with global_connection.cursor(cursor_factory=DictCursor) as curs:
        curs.execute("SELECT steam_id FROM discord_users WHERE discord_id=%s", (discord_id,))
        result = curs.fetchall()
    return len(result) > 0


def remove_discord_id(discord_id):
    with global_connection.cursor() as curs:
        curs.execute("DELETE FROM subscriptions WHERE owner=%s", (discord_id,))
        curs.execute("DELETE FROM discord_users WHERE discord_id=%s", (discord_id,))

