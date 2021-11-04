from .translator import TranslatorCog

def setup(bot):
    cog = TranslatorCog(bot)
    bot.add_cog(cog)
