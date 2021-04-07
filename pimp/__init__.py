from .pimp import Pimp

def setup(bot):
    cog = Pimp(bot)
    bot.add_cog(cog)
