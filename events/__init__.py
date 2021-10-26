from .events import Odinreg

def setup(bot):
    cog = Odinreg(bot)
    bot.add_cog(cog)
