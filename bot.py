import re

import asyncio
import discord
from asyncio import sleep
from discord.ext import commands
from ytdl import YTDLSource

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actual_url = None
        # Check if the timestamp matches with the 99:99 format
        self.timestamp_format = re.compile(r'^(?:([01]?\d|[0-9][0-9]):([0-5]?\d))$')
        self.song_queue = []
        self.playing = False
        self.actual_message = None

    def on_same_channel(self, ctx):
        return ctx.author.voice.channel and ctx.author.voice.channel == ctx.voice_client.channel

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """
        Executed when a bot joins into a channel
        """
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, url: str):
        """
        Play command. If a song is already playing, the given one will be put in queue
        """
        async with ctx.typing():
            if not self.playing:
                await self._play_song(ctx, url)
            else:
                await self.add_to_queue(ctx, url)

    async def add_to_queue(self, ctx, url):
        """
        Adds a song to queue
        """
        player = await YTDLSource.from_url(url, loop=self.bot.loop)
        self.song_queue.append([player, url])
        await ctx.send(f":watch: La canción '{player.title}' fue añadida a la cola")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """
        Changes the bot volume
        """
        if ctx.voice_client is None:
            return await ctx.send(":no_entry: Necesitas estar conectado a un canal de voz")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(":loud_sound: El volumen ha sido cambiado a {}%".format(volume))

    @commands.command()
    async def skip(self, ctx):
        """
        Skips the current song. If no song is playing, then waits to disconnect
        """
        if not self.song_queue:
            await self._wait_to_disconnect(ctx)
        
        ctx.voice_client.stop()
        self._play_song(ctx)

    async def _wait_to_disconnect(self, ctx):
        """
        Wait n seconds until disconnect. Before disconnect, checks if something
        is playing first
        """
        self.playing = False
        await sleep(5)

        if not self.playing:
            await ctx.voice_client.disconnect()

    def next_song(self, ctx):
        """
        This function is only executed AFTER a song, so, we need to set future coroutines
        """
        if not self.can_play_next:
            return

        if not self.song_queue:
            action = self._wait_to_disconnect(ctx)
        else:
            action = self._play_song(ctx)

        future = asyncio.run_coroutine_threadsafe(action, self.bot.loop)

        try:
            future.result()
        except:
            print('WHooops')

    async def _play_song(self, ctx, url=None, seconds=None):
        """
        Plays a song
        """
        player = None

        if not seconds:
            self.actual_message = await ctx.send('Cargando cancion...')

        if seconds and not url:
            self.can_play_next = False
            ctx.voice_client.stop()
            url = self.actual_url

        if not url and not seconds:
            (player, url) = self.song_queue.pop(0)

        player = player or \
            await YTDLSource.from_url(url, loop=self.bot.loop, stream=False, timestamp=seconds)

        ctx.voice_client.play(player, after=lambda e: self.next_song(ctx))
        self.actual_url = url
        self.can_play_next = True
        self.playing = True

        if not seconds:
            await self.actual_message.edit(content=f':musical_note: Reproduciendo: {player.title}')

    @commands.command()
    async def seek(self, ctx, timestamp: str):
        """
        Seek with 00:00 format
        """
        if ctx.voice_client is None:
            return await ctx.send(":no_entry: Necesitas estar conectado a un canal de voz")

        if not self.timestamp_format.match(timestamp):
            return await ctx.send(":no_entry: El tiempo debe tener formato 00:00")

        async with ctx.typing():
            time_data = timestamp.split(':')
            seconds = (int(time_data[0]) * 60) + int(time_data[1])

            await self._play_song(ctx, seconds=seconds)

        content = self.actual_message.content.split(" ||", 1)[0]
        await self.actual_message.edit(content=f'{content} || :fast_forward: Rebobinado hasta {timestamp}')

    @commands.command()
    async def stop(self, ctx):
        """
        Stops the bot, cleans the queue and waits to disconnect
        """
        ctx.voice_client.stop()
        self.song_queue = []
        await self._wait_to_disconnect(ctx)

    @play.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @volume.before_invoke
    async def ensure_voice(self, ctx):
        """
        Executed when the bot enters into a channel
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(":no_entry: Necesitas estar conectado a un canal de voz")
                raise commands.CommandError(":no_entry: Necesitas estar conectado a un canal de voz")
        elif not self.on_same_channel(ctx):
            await ctx.send(":no_entry: Necesitas estar en el mismo canal que yo para hacer eso")
            raise commands.CommandError(":no_entry: Necesitas estar en el mismo canal que yo para hacer eso")
