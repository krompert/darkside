from .takeover import Takeover

def setup(bot):
    cog = Takeover(bot)
    bot.add_cog(cog)
