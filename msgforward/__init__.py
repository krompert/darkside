from .msgforward import MsgForward

def setup(bot):
    cog = MsgForward(bot)
    bot.add_cog(cog)
