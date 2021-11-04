from .events import Events

def setup(bot):
    cog = Events(bot)
    bot.add_cog(cog)
