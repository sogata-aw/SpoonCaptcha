import discord
from discord.ext import commands

import asyncio

import play as p
import settings as s
import pytubefix.exceptions

play_task = None


class MusiqueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="play", description="Lance un audio via l'URL youtube")
    async def play(self, ctx, url: str):
        if ctx.guild.name not in self.bot.settings["authorized"]:
            await ctx.send(":warning: Ce serveur n'est pas autorisé à utiliser cette commande")
        global play_task
        vc = None
        state = ctx.author.voice
        if state is None:
            await ctx.send("Vous devez être dans un salon vocal pour utiliser cette commande")
        else:

            if ctx.guild.voice_client is None:
                vc = await state.channel.connect()
                try:
                    embed = await p.add_audio(ctx, url, 0, self.bot.settings)
                    await ctx.send(embed=embed)
                except pytubefix.exceptions.BotDetection:
                    await ctx.send(":warning: le bot ne peut actuellement pas lancer l'audio")
                    await vc.disconnect()

            else:
                try:
                    embed = await p.add_audio(ctx, url, 1, self.bot.settings)
                    await ctx.send(embed=embed)
                except pytubefix.exceptions.BotDetection:
                    await ctx.channel.send_message(":warning: le bot ne peut actuellement pas lancer l'audio")
                    await ctx.guild.voice_client.disconnect()

            if play_task is None:
                play_task = asyncio.create_task(self.boucle_musique(ctx, vc))

    async def boucle_musique(self, ctx, vc):
        global play_task
        first = True
        while vc.is_connected():
            query = self.bot.settings[ctx.guild.name]["query"]
            if not vc.is_playing():
                if len(query) > 0:
                    if not first:
                        embed = p.create_embed(ctx, "Now playing : " + query[0].title, query[0].url, self.bot.settings)
                        await ctx.channel.send(embed=embed)
                    p.play_audio(ctx, vc, self.bot.settings)
                    while vc.is_playing():
                        await asyncio.sleep(1)
                    await asyncio.sleep(1)
                    if len(query) > 0:
                        query = p.supprimer_musique(ctx, query)
            first = False
            await asyncio.sleep(1)
        play_task = None

    @commands.hybrid_command(name="skip", description="Passe à la musique suivante")
    async def skip(self, ctx):
        if len(self.bot.settings[ctx.guild.name]["query"]) < 1:
            await ctx.send(":warning: Il n'y a pas de musique après celle-ci")
        else:
            ctx.guild.voice_client.stop()
            embed = discord.Embed(title=":next_track: Skip")
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="stop", description="Stop la musique et déconnecte le bot")
    async def stop(self, ctx):
        state = ctx.guild.voice_client
        if state is None:
            await ctx.send("Le bot est connecté à aucun salon vocal")
        else:
            await state.disconnect()
            p.supprimer_musique(ctx, self.bot.settings[ctx.guild.name]["query"])
            self.bot.settings[ctx.guild.name]["query"].clear()
            await ctx.send("Déconnecté")

    @commands.hybrid_command(name="queue", description="Affiche la liste de lecture")
    async def queue(self, ctx):
        embed = discord.Embed(title="Liste de lecture")
        query = self.bot.settings[ctx.guild.name]["query"]
        if len(query) <= 0:
            await ctx.send(":warning: La liste est vide")
        else:
            for i in range(len(query)):
                embed.add_field(name=str(i + 1) + ". " + query[i].title, value="", inline=False)
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MusiqueCog(bot))