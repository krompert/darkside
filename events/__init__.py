from .events import Odinreg

def setup(bot):
    cog = Giveaways(bot)
    bot.add_cog(cog)
