from .massmod import MassMod

def setup(bot):
    cog = MassMod(bot)
    bot.add_cog(cog)
