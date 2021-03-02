import discord
from redbot.core import commands, checks
from redbot.core.bot import Red
from typing import Optional, Union

class Channels(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.command(name="createchannel", aliases=['cch'])
    async def _channels(self, ctx, channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]], newChannelName: str, syncPermissions: bool=True):
        """Create a text channel while syncing the permissions from the previous channel."""
        try:
            if isinstance(channel, discord.TextChannel):
                newChannel = await ctx.guild.create_text_channel(newChannelName, overwrites=channel.overwrites if channel.overwrites and syncPermissions else None)
            if isinstance(channel, discord.VoiceChannel):
                newChannel = await ctx.guild.create_voice_channel(newChannelName, overwrites=channel.overwrites if channel.overwrites and syncPermissions else None)

            if syncPermissions:
                await ctx.send(f"Created a new channel: **{newChannel.mention}** and synced permissions with {channel.mention}.")
            else:
                await ctx.send(f"Created a new channel: **{newChannel.mention}** without syncing permissions.")

        except:
            await ctx.send("Missing permissions to create a channel.")

    @commands.command(name='deletechannel', aliases=['dc'])
    @checks.mod_or_permissions(administrator=True)
    async def _deletechannels(self, ctx, channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]]):
        """Delete a channel using the command."""
        try:
            await channel.delete()
            await ctx.send("Successfully delete the channel.")
        except:
            await ctx.send("Failed to delete the channel.")
