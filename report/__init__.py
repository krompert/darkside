from .report import Report
import discord

def setup(bot):
    cog = Report(bot)
    bot.allowed_mentions = discord.AllowedMentions(everyone=True, roles=False)
    bot.add_cog(cog)
