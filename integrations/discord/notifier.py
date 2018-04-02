import discord
import asyncio
import time

from state import storage
import local_config

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        print ("channel: %v", message.channel)
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')

    elif message.content.startswith('!add'):
        steam_id = message.content.strip("!add ")
        await client.send_message(message.channel, 'Adding %s to the list for this channel...' % steam_id)
        storage.players[steam_id].append(message.channel)
        await client.send_message(message.channel, 'Added %s to the list for this channel.' % steam_id)


async def push_notifications():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(3)
        print("attempting to say hello to %d users" % len(storage.players))
        for steam_id, channels in storage.players.items():
            message = "HELLO WORLD %s" % str(steam_id)
            for channel in channels:
                await client.send_message(channel, message)

client.loop.create_task(push_notifications())
client.run(local_config.DISCORD_BOT_API_KEY)
