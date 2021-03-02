from redbot.core.bot import Red
from .burn import Burn

___red_end_user_data_statement__ = "This cog does not persistently store data about users."

def setup(bot: Red):
    cog = Burn(bot)
    bot.add_cog(cog)