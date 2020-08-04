from .giveawaywinner import GiveawayWinner

def setup(bot):
    cog = GiveawayWinner(bot)
    bot.add_cog(cog)
