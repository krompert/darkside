from .joke import Joke

def setup(bot):
    cog = Joke(bot)
    bot.add_cog(cog)
