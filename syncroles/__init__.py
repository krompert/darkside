from .syncroles import SyncRoles

def setup(bot):
    syncrole = SyncRoles(bot)
    bot.add_cog(syncrole)
