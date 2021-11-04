from redbot.core.bot import Red
from .alarm import Alarm
import discord

___red_end_user_data_statement__ = "This cog does not persistently store data about users."

def setup(bot: Red):
    cog = Alarm(bot)
    bot.allowed_mentions = discord.AllowedMentions(everyone=True, roles=True)
    bot.add_cog(cog)