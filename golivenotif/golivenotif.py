import discord
from redbot.core import Config, commands
from datetime import datetime


class GoLiveNotifications(commands.Cog):
    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=202005112)
        self.bot = bot
        default_guild = {
            "channel": None
        }
        self.config.register_guild(**default_guild)

# Commands

    @commands.group(name="golive")
    @commands.has_permissions(administrator=True)
    async def _go_live(self, ctx):
        pass

    @_go_live.command(name="channel", help="Sets the channel for Go Live notifications.")
    async def _set_channel(self, ctx, channel: discord.TextChannel=None):
        if not channel:
            await self.config.guild(ctx.guild).channel.set(channel)
            await ctx.send("Go Live notifications reset! I will no longer notify of streams in voice channels.")
        else:
            await self.config.guild(ctx.guild).channel.set(channel.id)
            await ctx.send(f"Go Live notifications set to {channel.mention}! I will now notify of streams in voice channels there.")

# Events

    @commands.Cog.listener("on_voice_state_update")
    async def go_live_detector(self, member, before, after):
        guild = member.guild
        if before.self_stream == False and after.self_stream == True:
            channel_id = await self.config.guild(guild).channel()
            if channel_id == None:
                return
            channel = guild.get_channel(channel_id)
            if not channel:
                await self.config.guild(guild).channel.set(None)
                return
            e = discord.Embed(description=f"{member.mention} is now streaming in {channel.mention}", color=member.color, timestamp=datetime.utcnow())
            e.set_author(name=str(member), icon_url=member.avatar_url)
            e.set_footer(text="Started streaming")
            await channel.send(embed=e)
        if before.self_video == False and after.self_video == True:
            channel_id = await self.config.guild(guild).channel()
            if channel_id == None:
                return
            channel = guild.get_channel(channel_id)
            if not channel:
                await self.config.guild(guild).channel.set(None)
                return
            e = discord.Embed(description=f"{member.mention} is now streaming their camera in {channel.mention}", color=member.color, timestamp=datetime.utcnow())
            e.set_author(name=str(member), icon_url=member.avatar_url)
            e.set_footer(text="Started streaming the camera")
            await channel.send(embed=e)

            