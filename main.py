from os import getenv
from dotenv import load_dotenv

from bot import MusicBot
from discord.ext import commands

load_dotenv()

PREFIX = getenv('PREFIX')
TOKEN = getenv('TOKEN')

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='Relatively simple music bot example')

@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')

bot.add_cog(MusicBot(bot))
bot.run(TOKEN)
