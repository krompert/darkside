from .purge import PurgeMessages

def setup(bot):
    cog = PurgeMessages(bot)
    bot.add_cog(cog)
