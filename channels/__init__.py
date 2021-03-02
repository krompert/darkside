from .channels import Channels

def setup(bot):
    cog = Channels(bot)
    bot.add_cog(cog)