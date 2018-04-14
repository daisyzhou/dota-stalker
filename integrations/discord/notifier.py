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
    if message.content.startswith('!help'):
        await client.send_message(message.channel, 'type `!stalker help` for more help from me ^_^')

    elif message.content.startswith('!stalker status'):
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
            First I'll send a link for you to authorize me to look at your Discord integrations, so that I can get your steam ID.  Then I'll add your name to the list of users to stalk for THIS channel.  Obviously this only  works if you've connected your steam account to your discord account.  Once I have your steam ID, I'll update this channel whenever you finish a Dota game!
        `!stalker stop all`
            I'll stop stalking you in ALL channels.

        Add me to your own server: https://discordapp.com/oauth2/authorize?client_id=265362185130082304&scope=bot&permissions=0
        Contact dzbug#2602 on Discord for requests/bug reports.  But seriously, I'm very experimental, so don't expect her to help ._.
        """
        await client.send_message(message.channel, help_message)

    elif message.content.startswith('!stalker stalkme'):
        discord_id = message.author.id
        if discord_id not in storage.steam_to_discord.values():
            await client.send_message(
                message.channel,
                "<@%s>, please authorize me to see your steam ID by clicking here: http://daisy.zone:5005/dota_stalker_add.  I'll wait!" % discord_id)
        while discord_id not in storage.steam_to_discord.values():
            print("DEBUG: waiting for steam ID from user: %s" % discord_id)
            await asyncio.sleep(5)
        storage.player_channels[discord_id].append(message.channel)
        await client.send_message(message.channel, '<@%s>, I have your steam ID.  Added you to the list for this channel.' % discord_id)

    elif message.content.startswith('!stalker stop all'):
        discord_id = message.author.id
        storage.player_channels[discord_id] = []
        for s,d in storage.steam_to_discord.items():
            if d == discord_id:
                del(storage.steam_to_discord, s)
        await client.send_message(message.channel, 'Removed <@%s> from all channels.  You are dead to me.' % discord_id)

    elif message.content.startswith('!stalker'):
        await client.send_message(message.channel, 'Unrecognized command.  try `!stalker help`')

    elif message.content.startswith('!'):
        await client.send_message(message.channel, 'Are you looking for me?  try `!stalker help`')


async def push_notifications():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(0)
        try:
            (player, message_chunk) = notify_queue.matches_to_notify.get_nowait()
        except queue.Empty:
            continue
        messages_sent = 0
        for discord_id, channels in storage.player_channels.items():
            if storage.steam_to_discord[player] == discord_id:
                for channel in channels:
                    start = time.time()
                    message = "%s %s" % ("<@%s> " % discord_id, message_chunk)
                    await client.send_message(channel, message)
                    end = time.time()
                    print("time it took to send message: %d" % (end-start))
                    messages_sent += 1
        if messages_sent == 0:
            print("ERROR: 0 messages sent for player %s" % player)

client.loop.create_task(push_notifications())

def run_bot():
    asyncio.set_event_loop(loop)
    client.run(local_config.DISCORD_BOT_API_KEY)

