from .seen import Seen

def setup(bot):
    cog = Seen(bot)
    bot.add_cog(cog)
