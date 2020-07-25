from .autorole import AutoRole

def setup(bot):
    bot.add_cog(AutoRole(bot))