import discord
from redbot.core import commands
from redbot.core.bot import Red

class Shoe(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def shoe(self, ctx, user: discord.Member):
        """Throw a shoe at a different user."""

        if user == ctx.author:
            return await ctx.send("You can't throw shoe at urself.")

        if user.bot:
            return await ctx.send("You can't throw shoe at bots.")

        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} aims and throws a shoe at {user.mention}").set_image(url="https://c.tenor.com/RfoJhw57qd8AAAAC/angry-mad.gif"))
