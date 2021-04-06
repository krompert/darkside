from .shoe import Shoe

def setup(bot):
    cog = Shoe(bot)
    bot.add_cog(cog)
