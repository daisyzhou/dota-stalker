import asyncio
import discord
import queue
import time

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
        
        I watch Dota 2 matches as they finish and I can update this channel when you finish a game
        Commands:
        `!stalker help`:
            This command.
        `!stalker status`:
            I'll tell you if I'm up and in your channel.
        `!stalker addme`:
            First I'll send a link for you to authorize me to look at your Discord integrations, so that I can get your steam ID.  Then I'll add your name to the list of users to stalk for THIS channel.  This only  works if you've connected your steam account to your discord account and if you have public match info enabled in dota.  Once I have your steam ID, I'll update this channel whenever you finish a Dota game!
        `!stalker removeme`
            I'll stop stalking you in ALL channels.

        Add me to your own server: https://discordapp.com/oauth2/authorize?client_id=265362185130082304&scope=bot&permissions=0
        Contact dzbug#2602 on Discord for requests/bug reports.  But seriously, I'm very experimental, so don't expect her to help ._.
        """
        await client.send_message(message.channel, help_message)

    elif message.content.startswith('!stalker addme'):
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
                user_notification_string = " ".join(["<@%{}> ".format(discord_id) for discord_id in notify_users])
                message = "%s: %s" % (user_notification_string, message_chunk)
                await client.send_message(channel, message)
                end = time.time()
                print("time it took to send message: %d" % (end-start))
                messages_sent += 1
        print("%d messages sent for player %s" % (messages_sent, steam_id))

client.loop.create_task(push_notifications())

def run_bot():
    asyncio.set_event_loop(loop)
    client.run(local_config.DISCORD_BOT_API_KEY)

