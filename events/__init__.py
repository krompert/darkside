from .events import Eventsreg

def setup(bot):
    cog = Giveaways(bot)
    bot.add_cog(cog)
