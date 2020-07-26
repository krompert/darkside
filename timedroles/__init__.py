from .timedroles import TimedRoles

def setup(bot):
    cog = TimedRoles(bot)
    bot.add_cog(cog)
    bot.loop.create_task(cog._timed_roles())