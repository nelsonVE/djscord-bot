import re
import os
import logging

import asyncio
import discord
from asyncio import sleep
from discord.ext import commands
from ytdl import YTDLSource

from language import lang

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actual_url = None
        self.actual = {'url': None, 'id': None}
        # Check if the timestamp matches with the 99:99 format
        self.timestamp_format = re.compile(r'^(?:([01]?\d|[0-9][0-9]):([0-5]?\d))$')
        self.song_queue = []
        self.playing = False
        self.actual_message = None
        self.waiting_time = 30

    def on_same_channel(self, ctx):
        """
        Checks if the author and the bot are in the same channel
        """
        return ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_client.channel

    def delete_files(self):
        """
        Deletes all the unused files
        """
        dir = './files'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

    async def change_status(self, status: str, activity_type=discord.ActivityType.listening):
        """
        Updates the bot status (activity)
        """
        activity = discord.Activity(name=status, type=activity_type)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    def get_emoji_number(self, number: int):
        """
        Gets an emoji number by its queue pos. (NOT READY!)
        """
        return (
            ':one:',
            ':two:',
            ':three:',
            ':four:',
            ':five:',
            ':six:',
            ':seven:',
            ':eight:',
            ':nine:',
            ':keycap_ten:',
        )[int(number)]

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """
        Executed when a bot joins into a channel
        """
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def h(self, ctx):
        """
        Help command
        """
        logger.debug("help command called")

        await ctx.send(
        """
        :page_with_curl: Lista de comandos:
        **!play**: Reproduce una canción (o es agregada a la lista de espera)
        **!seek**: Adelanta la canción hasta un tiempo establecido (Formato: 00:00)
        **!stop**: Detiene completamente la reproducción y limpia la lista de espera
        **!skip**: Salta a la siguiente canción de la lista
        **!volume**: Aumenta o disminuye el volumen del bot
        """
        )

    @commands.command()
    async def play(self, ctx, *, url: str=None):
        """
        Play command. If a song is already playing, the given one will be put in queue
        """
        logger.debug("play command called")

        async with ctx.typing():
            if not url:
                return await ctx.send(lang.get('SONG_NEEDED')) 
            if len(self.song_queue) > 9:
                return \
                    await ctx.send(lang.get('QUEUE_MAX_REACHED')) 
            if not self.playing:
                await self._play_song(ctx, url, played_by=ctx.author.name)
            else:
                await self.add_to_queue(ctx, url, played_by=ctx.author.name)

    @commands.command()
    async def list(self, ctx, page: str=0):
        """
        Shows the song queue
        """
        logger.debug("list command called")

        page = int(page)
        queue = ""

        if not self.song_queue:
            return await ctx.send(lang.get('QUEUE_IS_EMPTY'))

        for index, song in enumerate(self.song_queue):
            queue += f"{self.get_emoji_number(index)} - {song[0].title}\n"

        await ctx.send(lang.get('QUEUE_LIST_MESSAGE').format(queue))

    async def add_to_queue(self, ctx, url, played_by):
        """
        Adds a song to queue
        """

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
        except Exception as e:
            print(e)
            return await self.actual_message.edit(content=lang.get('NOT_FOUND'))


        if player:
            self.song_queue.append([player, url, played_by])
            await ctx.send(lang.get('QUEUE_SONG_ADDED').format(player.title))
        else:
            await ctx.send(lang.get('QUEUE_SONG_FAILED'))

    @commands.command()
    async def volume(self, ctx, volume: int=None):
        """
        Changes the bot volume
        """
        logger.debug("volume command called")

        if not volume:
            return await ctx.send(lang.get('ACTUAL_VOLUME').format(int(ctx.voice_client.source.volume * 100)))
        if ctx.voice_client is None:
            return await ctx.send(lang.get('NOT_CONNECTED'))

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(lang.get('VOLUME_CHANGED').format(volume))

    @commands.command()
    async def skip(self, ctx):
        """
        Skips the current song. If no song is playing, then waits to disconnect
        """
        logger.debug("skip command called")

        if not self.song_queue:
            return await self._wait_to_disconnect(ctx)
        
        ctx.voice_client.stop()
        await self._play_song(ctx)

    async def _wait_to_disconnect(self, ctx):
        """
        Wait n seconds until disconnect. Before disconnect, checks if something
        is playing first
        """
        self.delete_files()
        await self.bot.change_presence()
        self.playing = False
        await sleep(self.waiting_time)

        if not self.playing:
            await ctx.voice_client.disconnect()

    def next_song(self, ctx):
        """
        This function is only executed AFTER a song, so, we need to set future coroutines
        """
        if not self.can_play_next:
            return

        if not self.song_queue:
            future = asyncio.run_coroutine_threadsafe(self._wait_to_disconnect(ctx), self.bot.loop)
        else:
            future = asyncio.run_coroutine_threadsafe(self._play_song(ctx), self.bot.loop)

        try:
            future.result()
        except:
            print('Whooops')

    async def _get_next_song(self):
        logger.debug('Popping from list!')
        return self.song_queue.pop(0)

    async def _play_song(self, ctx, url=None, seconds=None, played_by=None):
        """
        Plays a song
        """
        player = None

        if seconds and not url:
            self.can_play_next = False
            ctx.voice_client.stop()
            url = self.actual_url

        if not seconds and url:
            self.actual_message = await ctx.send(lang.get('LOADING_SONG').format(url))

        if not url and not seconds:
            (player, url, played_by) = await self._get_next_song()

        try:
            player = player or \
                await YTDLSource.from_url(url, loop=self.bot.loop, stream=False, timestamp=seconds)
        except Exception as e:
            print(e)
            self.can_play_next = True
            return await self.actual_message.edit(content=lang.get('NOT_FOUND'))

        ctx.voice_client.play(player, after=lambda e: self.next_song(ctx))
        self.actual_url = url
        self.can_play_next = True
        self.playing = True

        if not seconds:
            await self.change_status(player.title)
            await self.actual_message.edit(content=lang.get('PLAYING_SONG').format(player.title, played_by))

    @commands.command()
    async def seek(self, ctx, timestamp: str):
        """
        Seek with 00:00 format
        """
        logger.debug("seek command called")

        if ctx.voice_client is None:
            return await ctx.send(lang.get('NOT_CONNECTED'))

        if not self.timestamp_format.match(timestamp):
            return await ctx.send(lang.get('SEEK_BAD_FORMAT'))

        async with ctx.typing():
            time_data = timestamp.split(':')
            seconds = (int(time_data[0]) * 60) + int(time_data[1])

            await self._play_song(ctx, seconds=seconds or 1)

        content = self.actual_message.content.split(" ||", 1)[0]
        await self.actual_message.edit(content=f'{content} || **[:fast_forward: {timestamp}]**')

    @commands.command()
    async def stop(self, ctx):
        """
        Stops the bot, cleans the queue and waits to disconnect
        """
        logger.debug("stop command called")

        ctx.voice_client.stop()
        self.song_queue = []
        await self._wait_to_disconnect(ctx)

    @commands.command()
    async def disconnect(self, ctx):
        if not self.playing:
            logger.info('Bot disconnected')
            await ctx.voice_client.disconnect()
        else:
            await ctx.send(lang.get('DISCONNECT_WHILE_PLAYING'))

    @play.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @seek.before_invoke
    @volume.before_invoke
    async def ensure_voice(self, ctx):
        """
        Executed when the bot enters into a channel
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(lang.get('NOT_CONNECTED'))
                raise commands.CommandError(lang.get('NOT_CONNECTED'))
        elif not self.on_same_channel(ctx):
            await ctx.send(lang.get('NOT_IN_CHANNEL'))
            raise commands.CommandError(lang.get('NOT_IN_CHANNEL'))
