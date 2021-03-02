import asyncio
import datetime
import random

import discord
from discord.ext import tasks
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
import typing

class Burn(commands.Cog):
    "Burn Cog."
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=20190511001, force_registration=True)
        default_guild = {
            "insults": {}
        }
        self.data.register_guild(**default_guild)

    @checks.admin_or_permissions(administrator=True)
    @commands.group(invoke_without_command=True, aliases=["burns"])
    async def burn(self, ctx, user: typing.Optional[discord.Member]):
        """Manage scheduled sticky messages.
        
        Usage:
            [p]burn @User
            [p]burn add <insult>
            [p]burn remove <id>
            [p]burn list
        """
        if not ctx.invoked_subcommand:
            insults = await self.data.guild(ctx.guild).insults()
            if not insults:
                return await ctx.send("No insults were added.")
            insult = insults[random.choice(list(insults.keys()))]
            await ctx.send(f"{user.mention}, {insult}")

    @burn.command()
    async def add(self, ctx, *, insult):
        insults = await self.data.guild(ctx.guild).insults()
        for insulti in insults:
            if insults[insulti] == insult:
                return await ctx.send("That burn already exists.")
        while True:
            try:
                insults[str(random.randint(10000,99999))] = insult
                break
            except:
                pass
        await self.data.guild(ctx.guild).insults.set(insults)
        await ctx.send(f"```{insult}``` **was added to the burns list.**")

    @burn.command(aliases=["rem"])
    async def remove(self, ctx, *, insult_id: int):
        insults = await self.data.guild(ctx.guild).insults()
        for insultid, insult in insults.items():
            if int(insultid) == insult_id:
                del insults[insultid]
                await self.data.guild(ctx.guild).insults.set(insults)
                return await ctx.send(f"```{insult}``` **was removed from the burns list.**")
        await ctx.send("That burn doesn't exist.")

    @burn.command(name="list")
    async def _list(self, ctx):
        insults = sorted((await self.data.guild(ctx.guild).insults()).items(), key=lambda x: int(x[0]))
        insults = self.chunks([f"{i[0]}. `{i[1]}`" for i in insults], 5)
        msg = None
        page_no = 0
        while True:
            e = discord.Embed(description="\n\n".join(insults[page_no]), color=ctx.author.color)
            e.set_author(name="Burns list" + f" [{page_no+1}/{len(insults)}]" if len(insults) > 1 else "", icon_url=ctx.guild.icon_url)
            e.set_footer(text=ctx.author.name, icon_url=ctx.guild.avatar_url)
            if not msg:
                msg = await ctx.send(embed=e)
                if len(insults) > 1:
                    await msg.add_reaction("◀️")
                    await msg.add_reaction("▶️")
                    def check(reaction, user):
                        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["◀️","▶️"]
                else:
                    return
            else:
                await msg.edit(embed=e)
            try:
                reaction = await self.bot.wait_for("reaction_add", check=check, timeout=90)[1]
            except Exception:
                try:
                    await msg.clear_reactions()
                except:
                    pass
                break
            if str(reaction.emoji) == "◀️":
                page_no -= 1
                if page_no < 1:
                    page_no = len(insults) - 1
            if str(reaction.emoji) == "▶️":
                page_no += 1
                if page_no > len(insults) - 1:
                    page_no = 1
            try:
                await reaction.remove(ctx.author)
            except:
                pass

    def chunks(self, lst, n):
        result = []
        for i in range(0, len(lst), n):
            result.append(lst[i:i + n])
        return result
