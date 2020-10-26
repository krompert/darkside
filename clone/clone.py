import discord
from redbot.core import commands, checks
from redbot.core.bot import Red

class RoleCloner(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @checks.has_permissions(administrator=True)
    @commands.command(aliases=["clonerole", "cr", "cloner"])
    async def clone(self, ctx, role1: discord.Role, role2: str):
        """Clone role1 permissions to role2."""

        if not role1:
            return await ctx.send(f"**{role1.name}** not found.")

        role2_obj = discord.utils.get(ctx.guild.roles, name=role2)
        if not role2_obj:
            role2_obj = await ctx.guild.create_role(name=role2, permissions=role1.permissions, hoist=role1.hoist, mentionable=role1.mentionable)
            await ctx.send(f"**{role2_obj.name}** role has been created.")
        elif role2_obj:
            try:
                await role2_obj.edit(permissions=role1.permissions)
                await ctx.send(f"**{role2_obj.name}** permissions are now same as **{role1.name}**")
            except:
                return await ctx.send("Failed to edit role permissions.")

        n = 0
        for channel in ctx.guild.channels:
            channel_overwrites = channel.overwrites_for(role1)
            if channel_overwrites:
                await channel.set_permissions(role2_obj, overwrite=channel_overwrites)
                n+=1

        await ctx.send(f"Successfully changed {n}/{len(ctx.guild.channels)} channels overwrites for role **{role2_obj.name}** to same as **{role1.name}** role.")


    @checks.has_permissions(administrator=True)
    @commands.command(aliases=["dr", "roledeleter"])
    async def deleterole(self, ctx, role: discord.Role):
        """Delete a role."""
        try:
            await role.delete()
            await ctx.send("Role has been deleted.")
        except:
            await ctx.send("Failed to delete the role.")
            pass
