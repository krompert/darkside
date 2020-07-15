from .clone import RoleCloner

def setup(bot):
    cog = RoleCloner(bot)
    bot.add_cog(cog)
