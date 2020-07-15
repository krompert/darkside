from .automod import AutoMod

def setup(bot):
    cog = AutoMod(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog.unmute_user_loop())
