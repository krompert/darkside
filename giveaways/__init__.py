from .giveaways import Giveaways

def setup(bot):
    cog = Giveaways(bot)
    bot.add_cog(cog)
