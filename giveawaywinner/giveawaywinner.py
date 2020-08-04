import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core import checks

class GiveawayWinner(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=49376386346393, force_registration=True)

        default_guild = {
            "giveaway_channel": None,
            "giveaway_role": None,
            "logchannel": None,
        }
        self.data.register_guild(**default_guild)

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group()
    async def giveawaywinner(self, ctx):
        """Setup autorole for giveaway winners and the giveaway channel."""
        if ctx.invoked_subcommand is None:
            pass

    @giveawaywinner.command(name="role")
    async def _role(self, ctx, role: discord.Role=None):
        """Setup autorole for giveaway winner."""
        if not role:
            await self.data.guild(ctx.guild).giveaway_role.set(None)
            await ctx.send("Giveaway role has been reset!")
        if role:
            await self.data.guild(ctx.guild).giveaway_role.set(role.id)
            await ctx.send(f"Giveaway role has been set to **{role.name}**!")

    @giveawaywinner.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel=None):
        """Setup giveaway channel, where giveaways will be hosted."""
        if not channel:
            await self.data.guild(ctx.guild).giveaway_channel.set(None)
            await ctx.send("Giveaway channel has been reset!")
        if channel:
            await self.data.guild(ctx.guild).giveaway_channel.set(channel.id)
            await ctx.send(f"Giveaway channel has been set to **{channel.mention}**!")

    @giveawaywinner.command(name="logchannel")
    async def _logchannel(self, ctx, channel: discord.TextChannel=None):
        """Setup a log channel where a message is sent when user is assigned a role."""
        if not channel:
            await self.data.guild(ctx.guild).logchannel.set(None)
            await ctx.send("Log channel has been reset!")
        if channel:
            await self.data.guild(ctx.guild).logchannel.set(channel.id)
            await ctx.send(f"Log channel has been set to **{channel.mention}**!")


    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        guild = message.guild

        if not guild:
            return

        author = message.author
        channel = message.channel

        if author.id != 710890809368641696:
            return
            
        if not author or not channel:
            return

        if not message.mentions:
            return

        role = await self.data.guild(guild).giveaway_role()
        channel_to_send = await self.data.guild(guild).giveaway_channel()
        log_channel = await self.data.guild(guild).logchannel()

        if not role or not channel_to_send:
            return

        role = guild.get_role(int(role))
        channel_to_send = guild.get_channel(int(channel_to_send))
        if log_channel:
            log_channel = guild.get_channel(int(log_channel))

        if not role or not channel_to_send:
            return

        if channel_to_send.id != channel.id:
            return

        default_words = ["congratulations", "!", "you", "have", "won"]
        n = 0
        for word in default_words:
            if word in message.content.lower():
                n +=1

        if len(default_words) == n:
            mentions = message.mentions

            for mention in mentions:
                try:
                    await mention.add_roles(role)
                except:
                    pass

                if log_channel:
                    try:
                        await log_channel.send(f"{author.mention} was assigned with **{role.name}** role for winning a giveaway in {channel_to_send.mention}.")
                    except:
                        pass
