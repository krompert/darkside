from .rules import Rules

def setup(bot):
    cog = Rules(bot)
    bot.add_cog(cog)
