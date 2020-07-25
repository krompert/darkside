from .golivenotif import GoLiveNotifications

def setup(bot):
    bot.add_cog(GoLiveNotifications(bot))