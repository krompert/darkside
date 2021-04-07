import discord
from redbot.core import commands
from redbot.core.bot import Red

class Pimp(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def pimp(self, ctx, user: discord.Member):
        """Pimp slap a different user."""

        if user == ctx.author:
            return await ctx.send("You can't pimp slap yourself.")

        if user.bot:
            return await ctx.send("You can't pimp slap bots.")

        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} Contracted its hand, and PIMP SLAPPED {user.mention}").set_image(url="https://imgur.com/ioAuqRk"))
