import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
from datetime import datetime
import asyncio
import random

class Joke(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=654654646546, force_registration=True)
        default_guild = {"channel": None}
        default_global = {"jokes": []}
        self.data.register_guild(**default_guild)
        self.data.register_global(**default_global)
        self.loop = bot.loop.create_task(self.joke_loop())

    def cog_unload(self):
        self.loop.cancel()
    
    async def joke_loop(self):
        while True:
            data = await self.data.all_guilds()
            jokes = await self.data.jokes()
            for guild in data:
                guild = self.bot.get_guild(int(guild))
                if not guild:
                    continue

                joke = random.choice(jokes)

                channel = await self.data.guild(guild).channel()
                if channel:
                    channel = guild.get_channel(channel)
                
                if channel:
                    await channel.send(f"Here's a random joke: {joke}")

            await asyncio.sleep(3600)

    @checks.admin_or_permissions(administrator=True)
    @commands.group()
    async def joke(self, ctx):
        """ Setup jokes."""
        pass

    @joke.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel):
        """Set a channel where the jokes should be sent."""
        await self.data.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Successfully set the joke channel to {channel.mention}.")

    @joke.command(name="add")
    async def _add(self, ctx, *, joke: str):
        """Add a joke to the list."""
        jokes = await self.data.jokes()
        if joke not in jokes:
            jokes.append(joke)
            await self.data.jokes.set(jokes)
            await ctx.send(f"`{joke}` has been added to the list.")

        else:
            await ctx.send("That joke already exists in the list.")

    @joke.command(name='remove')
    async def _remove(self, ctx, jokeID: int):
        """Remove a joke from the list using its number."""
        data = await self.data.jokes()
        if jokeID < 0:
            return await ctx.send("jokeID must be equal to or greater than 0.")
        
        if not data:
            return await ctx.send("There were no jokes set up on this server.")

        if len(data)-1 < jokeID:
            return await ctx.send(f"Invalid jokeID provided, make sure the ID you provide is smaller than or equal to {len(data)-1}.")

        try:
            joke = data[jokeID]
        except IndexError:
            return await ctx.send("No data, make sure to provide a valid jokeID.")

        data.remove(joke)
        
        await self.data.jokes.set(data)
        await ctx.send(f"Deleted the joke with ID: `{jokeID}`")

    @joke.command(name='list')
    async def __list(self, ctx, page_no: int=None):
        """View a list of all the jokes."""
        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.jokes()
        if not data:
            return await ctx.send("There is no available data to show.")

        pages = await self.get_pages(data, ctx.guild)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        e=discord.Embed(title=f"Total Jokes - {len(data)}", description=pages[page_no], colour=ctx.author.color)
        e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
        sent = await ctx.send(embed=e)
        if len(pages) == 1:
            return

        try:
            await sent.add_reaction("◀️")
            await sent.add_reaction("▶️")
        except:
            return await ctx.send('Unable to react to the message, please make sure i have the required permissions.')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == sent.id and str(reaction.emoji) in ["◀️","▶️"]
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=120)
                del user
            except Exception:
                try:
                    await sent.clear_reactions()
                except:
                    pass
                break
            if str(reaction.emoji) == "◀️":
                page_no -= 1
                if page_no < 0:
                    page_no = len(pages) - 1
            if str(reaction.emoji) == "▶️":
                page_no += 1
                if page_no > len(pages) - 1:
                    page_no = 0
            e=discord.Embed(title=f"Total Jokes - {len(data)}", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break

    async def get_pages(self, data, guild):
        page_size = 3
        i = 0
        output_data = []
        text = ""
        n = 0
        for joke in data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            text += f"`ID:` **{n}** `-->` {joke}\n\n"
            n += 1
        if text != "":
            output_data.append(text)
        return output_data