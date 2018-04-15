import asyncio
import discord
import queue
import time

from matches import util
from state import storage
import local_config
from integrations import notify_queue

loop = asyncio.get_event_loop()
client = discord.Client(loop=loop)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!stalker status'):
        print("USER ID IS: {}, type {}".format(message.author.id, type(message.author.id)))
        print("CHANNEL ID IS: {}, type {}".format(message.channel.id, type(message.channel.id)))
        await client.send_message(message.channel, 'I am alive... I think')

    elif message.content.startswith('!stalker help'):
        help_message="""
        ** I'm just an experiment!  Your user info may be lost at any time.  I also might explode.**
        
        I watch Dota 2 matches as they finish.  You can subscribe to any Steam ID and I'll notify you in this channel when they finish a game, but ONLY IF they have public match data enabled.
        I can also send a message to this channel whenever YOU finish a game, using your Steam connection to Discord to find your Steam ID 

        Commands:
        `!stalker help`:
            This command.
        `!stalker status`:
            I'll tell you if I'm up and in your channel.
        `!stalker subscribe <32 bit steam ID>`:
            I'll notify you in this channel, when the player with the provided steam ID finishes a game.  You can find the correct steam ID using dotabuff (last part of URL https://www.dotabuff.com/players/<32 bit steam ID>), or https://steamid.io (last part of steamID3).
        `!stalker subscribeme`:
            If finding a steam ID is too much work ... I can find your steam ID for you if you have your Steam account connected to discord.
            Once I have your steam ID, I'll notify you in this channel whenever YOU finish a Dota game!
        `!stalker removeme`
            I'll remove ALL subscriptions you created in ALL channels.

        Add me to your own server by following this link: https://discordapp.com/oauth2/authorize?client_id=265362185130082304&scope=bot&permissions=0
        Contact dzbug#2602 on Discord for requests/bug reports.  But seriously, I'm very experimental, so don't expect her to help ._.
        """
        await client.send_message(message.channel, help_message)

    elif message.content.startswith('!stalker subscribe '):
        discord_id = message.author.id
        rest_of_message = message.content.strip("!stalker subscribe ")
        valid, steam_id = util.validate_and_return_32bit(rest_of_message.strip())
        if not valid:
            await client.send_message(
                message.channel, "<@%s>, %s is not a valid steam ID." % (discord_id, rest_of_message))
            return

        storage.add_channel_for_discord_id(discord_user=discord_id, steam_id=steam_id, channel=message.channel)
        await client.send_message(message.channel, " <@%s>, successfully added your subscription to %s." % (discord_id, steam_id))

    elif message.content.startswith('!stalker subscribeme'):
        discord_id = message.author.id
        if not storage.check_discord_id_tracked(discord_id):
            await client.send_message(
                message.channel,
                "<@%s>, please authorize me to see your steam ID by clicking here: http://daisy.zone:5005/dota_stalker_add.  I'll wait!" % discord_id)
        while not storage.check_discord_id_tracked(discord_id):
            print("DEBUG: waiting for steam ID from user: %s" % discord_id)
            await asyncio.sleep(5)
        steam_id = storage.steam_from_discord(discord_id)
        storage.add_channel_for_discord_id(discord_id, steam_id, message.channel)
        await client.send_message(message.channel, '<@%s>, I have your steam ID.  Added you to the list for this channel.' % discord_id)

    elif message.content.startswith('!stalker removeme'):
        discord_id = message.author.id
        storage.remove_discord_id(discord_id)
        await client.send_message(message.channel, 'Removed <@%s> from all channels.  You are dead to me.' % discord_id)

    elif message.content.startswith('!stalker'):
        await client.send_message(message.channel, 'Unrecognized command.  try `!stalker help`')

    elif message.content.startswith('!help'):
        await client.send_message(message.channel, 'Are you looking for me?  try `!stalker help`')


async def push_notifications():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(0)
        try:
            (steam_id, message_chunk) = notify_queue.matches_to_notify.get_nowait()
        except queue.Empty:
            continue
        messages_sent = 0
        if storage.check_steam_id_tracked(steam_id):
            channels_map = storage.get_owners_and_channels_for_steam_id(steam_id)
            for channel, notify_users in channels_map.items():
                start = time.time()
                # construct a string for @-mentioning all users who have subscribed to this player
                user_notification_string = " ".join(["<@%s>" % discord_id for discord_id in notify_users if storage.get_discord_id_from_steam(steam_id) != discord_id])
                if len(user_notification_string) > 0:
                    message = "%s: %s" % (user_notification_string, message_chunk)
                else:
                    message = message_chunk
                await client.send_message(channel, message)
                end = time.time()
                print("time it took to send message: %d" % (end-start))
                messages_sent += 1
        print("%d messages sent for player %s" % (messages_sent, steam_id))

client.loop.create_task(push_notifications())

def run_bot():
    asyncio.set_event_loop(loop)
    client.run(local_config.DISCORD_BOT_API_KEY)

