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

    elif message.content.startswith('!addme'):
        await client.send_message(message.channel, 'Adding you to the list for this channel...')
        print("debug: message author %s, message channel %s" % (message.author, message.channel))
        storage.users[message.author].append(message.channel)
        print("debug: storage now contains %s" % str(storage.users.items()))
        await client.send_message(message.channel, 'Added you to the list for this channel.')


async def push_notifications():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(3)
        print("attempting to say hello to %d users" % len(storage.users))
        for user, channels in storage.users.items():
            message = "HELLO WORLD %s" % str(user)
            for channel in channels:
                await client.send_message(channel, message)

client.loop.create_task(push_notifications())
client.run(local_config.DISCORD_BOT_API_KEY)
