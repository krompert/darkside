from .events import OdinEvent

def setup(bot):
    cog = OdinEvent(bot)
    bot.add_cog(cog)
