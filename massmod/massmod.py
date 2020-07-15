import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core import checks

class MassMod(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group()
    async def mass(self, ctx):
        """Mass moderation commands."""
        if ctx.invoked_subcommand is None:
            pass

    @mass.command(name="ban")
    async def _ban(self, ctx, role: discord.Role):
        """Mass ban users in specific role."""
        n = len(role.members)
        for member in role.members:
            try:
                await member.ban(reason="Mass Ban")
            except:
                pass

        await ctx.send(f"Successfully banned **{n}** members in **{role.name}** role!")

    @mass.command(name="kick")
    async def _kick(self, ctx, role: discord.Role):
        """Mass kick users in specific role."""
        n = len(role.members)
        for member in role.members:
            try:
                await member.kick(reason="Mass Kick")
            except:
                pass

        await ctx.send(f"Successfully kicked **{n}** members in **{role.name}** role!")

    @mass.command(name="mute")
    async def _mute(self, ctx, role: discord.Role):
        """Mass mute users in a specific role."""
        n = len(role.members)

        rolex = discord.utils.get(ctx.guild.roles, name="Mass-Mute")
        if not role:
            await self._mute_role_check(ctx.guild)
            rolex = discord.utils.get(ctx.guild.roles, name="Mass-Mute")

        for member in role.members:
            await member.add_roles(rolex, reason="Mass mute.")

        await ctx.send(f"Successfully muted **{n}** members in **{role.name}** role.")

    @mass.command(name="unmute")
    async def _unmute(self, ctx, role: discord.Role):
        """Mass unmute users in a specific role."""
        if not role.members:
            return await ctx.send("No users were found in that role.")

        n = len(role.members)
        rolex = discord.utils.get(ctx.guild.roles, name="Mass-Mute")
        for member in role.members:
            try:
                await member.remove_roles(rolex, reason="Mass Unmute")
            except:
                pass

        await ctx.send(f"Successfully unmuted **{n}** members in **{role.name}** role.")

    @mass.command(name="update")
    async def _update(self, ctx):
        """Update all the channels permissions and create the mute role if not done already."""
        await self._mute_role_check(ctx.guild)
        await ctx.send("Updated all the channel permissions.")

    async def _mute_role_check(self, guild):
        role = discord.utils.get(guild.roles, name="Mass-Mute")
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        perms = discord.PermissionOverwrite()
        perms.speak = False

        if not role:
            role = await guild.create_role(name="Mass-Mute", reason="Mass mute role.")

        for channels in guild.text_channels:
            await channels.set_permissions(role, overwrite=overwrite)
        for channels in guild.voice_channels:
            await channels.set_permissions(role, overwrite=perms)
