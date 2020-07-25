import discord
from redbot.core import Config, commands


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=202005111)
        self.bot = bot
        default_guild = {
            "message": None,
            "auto_role": None,
            "bots_auto_role": None
        }
        self.config.register_guild(**default_guild)

# Commands

    @commands.group(name="autorole")
    @commands.has_permissions(administrator=True)
    async def _auto_role(self, ctx):
        pass

    @_auto_role.command(name="settings", aliases=["stats"], help="Show current settings of the Auto Role.")
    async def _check_stats(self, ctx):
        message = await self.config.guild(ctx.guild).message()
        autorole = await self.config.guild(ctx.guild).auto_role()
        botautorole = await self.config.guild(ctx.guild).bots_auto_role()
        e = discord.Embed(
            title="Auto Role Settings",
            color=0x0000ff
        )
        e.add_field(name="Auto Role", value=str(autorole))
        e.add_field(name="Bots Auto Role", value=str(botautorole))
        e.add_field(name="Message", value=str(message))
        await ctx.send(embed=e)

    @_auto_role.command(name="message", help="Set the message to be sent to the new members in dm's.")
    async def _set_message(self, ctx, *, message=None):
        if not message:
            e = discord.Embed(
                title="Message Variables", 
                description="{server} - shows server name.\n{user} - shows username#xxxx\n{membercount} - shows amount of members in the server.", 
                color=0x0000ff
            )
            await ctx.send(embed=e)
            return
        await self.config.guild(ctx.guild).message.set(message)
        await ctx.send(f"New members will get this message sent to their dm's.\n\n{message}")

    @_auto_role.command(name="botrole", help="Set a role as an auto role for bots.")
    async def _bot_auto_role_set(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).bots_auto_role.set(role.id)
        await ctx.send(f"New bots will now get **{role.name}** when they join.\nDo you wish to assign this new role to all current bots?\nReply with `yes` or `no`")
        def check(message):
            return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ["yes", "no"]
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "no":
                await ctx.send("No roles will be assigned.")
                return
            for member in ctx.guild.members:
                if not member.bot:
                    continue
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except:
                        continue
            await ctx.send("All roles have been successfully assigned to the bots.")
        except:
            await ctx.send("You took too long to respond, so action was cancelled.")

    @_auto_role.command(name="role", help="Set a role as an auto role for members.")
    async def _auto_role_set(self, ctx, role: discord.Role):
        await self.config.guild(ctx.guild).auto_role.set(role.id)
        await ctx.send(f"New members will now get **{role.name}** when they join.\nDo you wish to assign this new role to all current members? (Exclusing bots)\nReply with `yes` or `no`")
        def check(message):
            return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ["yes", "no"]
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "no":
                await ctx.send("No roles will be assigned.")
                return
            for member in ctx.guild.members:
                if member.bot:
                    continue
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except:
                        continue
            await ctx.send("All roles have been successfully assigned to the members.")
        except:
            await ctx.send("You took too long to respond, so action was cancelled.")

    @_auto_role.command(name="botassign", help="Current bot auto role is given to all bots.")
    async def _assign_bots(self, ctx):
        role_id = await self.config.guild(ctx.guild).bots_auto_role()
        if role_id == None:
            await ctx.send("You have not set a bots auto role yet.")
            return
        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.send("Reassign a bots auto role, previous set role was deleted.")
            await self.config.guild(ctx.guild).bots_auto_role.set(None)
            return
        await ctx.send(f"Do you wish to assign this new **{role.name}** to all current bots?\nReply with `yes` or `no`")
        def check(message):
            return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ["yes", "no"]
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "no":
                await ctx.send("No roles will be assigned.")
                return
            for member in ctx.guild.members:
                if not member.bot:
                    continue
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except:
                        continue
            await ctx.send("All roles have been successfully assigned to the bots.")
        except:
            await ctx.send("You took too long to respond, so action was cancelled.")
    
    @_auto_role.command(name="assign", help="Current auto role is given to all members.")
    async def _assign_members(self, ctx):
        role_id = await self.config.guild(ctx.guild).auto_role()
        if role_id == None:
            await ctx.send("You have not set a auto role yet.")
            return
        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.send("Reassign a auto role, previous set role was deleted.")
            await self.config.guild(ctx.guild).auto_role.set(None)
            return
        await ctx.send(f"Do you wish to assign this new **{role.name}** to all current members? (Excluding bots)\nReply with `yes` or `no`")
        def check(message):
            return message.channel == ctx.channel and message.author == ctx.author and message.content.lower() in ["yes", "no"]
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if msg.content.lower() == "no":
                await ctx.send("No roles will be assigned.")
                return
            for member in ctx.guild.members:
                if member.bot:
                    continue
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except:
                        continue
            await ctx.send("All roles have been successfully assigned to the members.")
        except:
            await ctx.send("You took too long to respond, so action was cancelled.")

# Events

    @commands.Cog.listener("on_member_join")
    async def auto_role_assigner(self, member):
        guild = member.guild
        if member.bot:
            role_id = await self.config.guild(guild).bots_auto_role()
            if role_id == None:
                return
            role = guild.get_role(role_id)
            if not role:
                await self.config.guild(guild).bots_auto_role.set(None)
                return
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"-----------\nError in AutoRoles\n{e}\n------------")
            return
        role_id = await self.config.guild(guild).auto_role()
        if role_id == None:
            return
        role = guild.get_role(role_id)
        if not role:
            await self.config.guild(guild).auto_role.set(None)
            return
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"-----------\nError in AutoRoles\n{e}\n------------")
        message = await self.config.guild(guild).message()
        if message == None:
            return
        message = message.replace("{user}", str(member)).replace("{server}", guild.name).replace("{membercount}", str(len(guild.members)))
        try:
            await member.send(message)
        except:
            pass
            