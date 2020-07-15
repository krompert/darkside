import discord
import asyncio
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core import Config, checks


class SyncRoles(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=6389602305923502020, force_registration=True)
        default_guild = {
            "sub_servers": {}}

        self.data.register_guild(**default_guild)

    @commands.group()
    @checks.admin()
    async def sync(self, ctx):
        """Set up sync servers."""
        if ctx.invoked_subcommand is None:
            pass

    @sync.group()
    async def roles(self, ctx):
        """Link/unlink roles."""
        if ctx.invoked_subcommand is None:
            pass

    @roles.command()
    async def unlink(self, ctx, main_server:int, sub_server:int):
        """Unlink a role between main server and the sub server."""
        main_server_obj = self.bot.get_guild(main_server)
        sub_server_obj = self.bot.get_guild(sub_server)
        if not main_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{main_server}``.")

        if not sub_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{sub_server}``.")

        confirm_msg = await ctx.send(f"Type **yes** if you wish to reset all the linked roles? Otherwise provide the ID of the role from the **{main_server_obj.name}** main server.")

        def confirmation_msg_check_func(message):
                return message.channel == confirm_msg.channel and ctx.author == message.author
        try:
            confirmation_msg_check = await self.bot.wait_for("message", check=confirmation_msg_check_func, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("You have timed out, please try again.")

        if confirmation_msg_check.content.lower() == "yes":
            await self.data.guild(main_server_obj).sub_servers.clear_raw(sub_server_obj.id, "roles")
            return await ctx.send(f"All the linked roles between **{main_server_obj.name}** main server and **{sub_server_obj.name}** sub server have been reset.")

        try:
            role_id = ctx.guild.get_role(int(confirmation_msg_check.content))
            if not role_id:
                return await ctx.send(f"No role was found with the ID: ``{confirmation_msg_check.content}``")
        except ValueError:
            return await ctx.send("Invalid ID was provided.")

        try:
            roles_data = await self.data.guild(main_server_obj).sub_servers.get_raw(sub_server_obj.id, "roles")
            await ctx.send(roles_data)
            if str(role_id.id) not in roles_data:
                return await ctx.send(f"Couldn't find the link of the role **{role_id.name}**.")
        except:
            return await ctx.send(f"Couldn't find the link of the role **{role_id.name}**.")
        del roles_data[str(role_id.id)]
        await self.data.guild(main_server_obj).sub_servers.set_raw(sub_server_obj.id, "roles", value=roles_data)
        await ctx.send(f"Unlinked all the roles linked to **{role_id.name}** from **{main_server_obj.name}**")

    @roles.command()
    async def link(self, ctx, main_server: int, sub_server: int):
        """Link a role between main server and the sub server."""
        main_server_obj = self.bot.get_guild(main_server)
        sub_server_obj = self.bot.get_guild(sub_server)
        if not main_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{main_server}``.")

        if not sub_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{sub_server}``.")

        confirm_msg = await ctx.send(f"Please provide the ID of the role from main server: **{main_server_obj.name}**")

        def confirmation_msg_check_func(message):
                return message.channel == confirm_msg.channel and ctx.author == message.author
        try:
            confirmation_msg_check = await self.bot.wait_for("message", check=confirmation_msg_check_func, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("You have timed out, please try again.")

        try:
            main_server_role = main_server_obj.get_role(int(confirmation_msg_check.content))
            if not main_server_role:
                return await ctx.send("No role was found with that ID.")
        except:
            return await ctx.send("No role was found with that ID.")

        try:
            await confirmation_msg_check.delete()
            await confirm_msg.edit(content=f"Please provide the ID of the role on the sub server: **{sub_server_obj.name}**")
        except discord.NotFound:
            return await ctx.send("Message not found, please try again.")
        except discord.Forbidden:
            return await ctx.send("Could not edit the message, missing permissinons.")

        try:
            confirmation_msg_check = await self.bot.wait_for("message", check=confirmation_msg_check_func, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("You have timed out, please try again.")

        try:
            sub_server_role = sub_server_obj.get_role(int(confirmation_msg_check.content))
            if not sub_server_role:
                return await ctx.send("No role was found with that ID.")
        except:
            return await ctx.send("No role was found with that ID.")

        roles_data = await self.data.guild(main_server_obj).sub_servers.get_raw(sub_server_obj.id, "roles")

        if str(main_server_role.id) in roles_data:
            roles_data[str(main_server_role.id)] = roles_data[str(main_server_role.id)]
        elif str(main_server_role.id) not in roles_data:
            await self.data.guild(main_server_obj).sub_servers.set_raw(sub_server_obj.id, "roles", main_server_role.id, value=[])
            roles_data = await self.data.guild(main_server_obj).sub_servers.get_raw(sub_server_obj.id, "roles")
            roles_data[str(main_server_role.id)] = roles_data[str(main_server_role.id)]

        roles_data[str(main_server_role.id)].append(str(sub_server_role.id))

        await self.data.guild(main_server_obj).sub_servers.set_raw(sub_server_obj.id, "roles", main_server_role.id, value=roles_data[str(main_server_role.id)])
        await ctx.send(f"**{main_server_role.name}** role from **{main_server_obj.name}** is now linked with **{sub_server_role.name}** role on **{sub_server_obj.name}** server.")

    @sync.group()
    async def sub(self, ctx):
        """Link/Unlink sub servers from the main servers"""
        if ctx.invoked_subcommand is None:
            pass

    @sub.command(name="add")
    async def _add(self, ctx, main_server: int, sub_server: int):
        """Link a sub server to the main server."""
        main_server_obj = self.bot.get_guild(main_server)
        sub_server_obj = self.bot.get_guild(sub_server)
        if not main_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{main_server}``.")

        if not sub_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{sub_server}``.")

        await self.data.guild(main_server_obj).sub_servers.set_raw(sub_server_obj.id, "roles", value={})
        await ctx.send(f"Sub server **{sub_server_obj.name}** has been linked too main server **{main_server_obj.name}**.")

    @sub.command(name="remove")
    async def _remove(self, ctx, main_server: int, sub_server: int):
        """Unlink a sub server from the main server."""
        main_server_obj = self.bot.get_guild(main_server)
        sub_server_obj = self.bot.get_guild(sub_server)
        if not main_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{main_server}``.")

        if not sub_server_obj:
            return await ctx.send(f"No server was found with the ID: ``{sub_server}``.")

        await self.data.guild(main_server_obj).sub_servers.clear_raw(sub_server_obj.id)
        await ctx.send(f"Sub server **{sub_server_obj.name}** has been un-linked from the main server **{main_server_obj.name}**.")

    @sync.group()
    async def main(self, ctx):
        """Add a main server to the list."""
        if ctx.invoked_subcommand is None:
            pass

    @main.command()
    async def add(self, ctx, server_id: int):
        """Link sub-servers to the main server."""
        main_server = self.bot.get_guild(server_id)
        if not main_server:
            return await ctx.send(f"No server was found with the ID: ``{server_id}``.")

        confirm_msg = await ctx.send(f"You have chosen **{main_server.name}** as your main server, type **yes** if you wish to link sub server to it.")

        def confirmation_msg_check_func(message):
                return message.channel == confirm_msg.channel and ctx.author == message.author
        try:
            confirmation_msg_check = await self.bot.wait_for("message", check=confirmation_msg_check_func, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("You have timed out, please try again.")

        if not confirmation_msg_check.content.lower() == "yes":
            await ctx.send("Request to proceed have been denied.")
            return

        try:
            await confirmation_msg_check.delete()
            await confirm_msg.edit(content="Please provide all the server ID's below, each of them separated by a space.")
        except discord.NotFound:
            return await ctx.send("Message not found, please try again.")
        except discord.Forbidden:
            return await ctx.send("Could not edit the message, missing permissinons.")

        try:
            confirmation_msg_check = await self.bot.wait_for("message", check=confirmation_msg_check_func, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("You have timed out, please try again.")

        server_ids = confirmation_msg_check.content.lower().split(" ")
        server_names = await self.get_servers_from_ids(server_ids)
        if server_names:
            server_names_str = (", ").join([server.name for server in server_names])
            for server in server_names:
                await self.data.guild(main_server).sub_servers.set_raw(server.id, "roles", value={})
            await confirmation_msg_check.delete()
            await confirm_msg.edit(content=f"You have linked **{server_names_str}** to the main server: **{main_server.name}**")
        elif not server_names:
            await ctx.send("Failed to fetch servers from the ID's you provided.")

    @main.command()
    async def remove(self, ctx, server_id: int):
        """Unlink all the sub servers from the main one."""
        main_server = self.bot.get_guild(server_id)
        if not main_server:
            return await ctx.send(f"No server was found with the ID: ``{server_id}``.")

        await self.data.guild(main_server).sub_servers.clear_raw()

        await ctx.send(f"All the sub servers and sync roles from **{main_server.name}** server were deleted.")

    async def get_servers_from_ids(self, server_ids):
        servers = []
        for server_id in server_ids:
            try:
                if isinstance(int(server_id), int):
                    server = self.bot.get_guild(int(server_id))
                    if server:
                        servers.append(server)
            except ValueError:
                pass
        return servers

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        server = before.guild
        data = await self.data.guild(server).sub_servers()
        if not data:
            return

        if before.roles != after.roles:
            for role in [x for x in after.roles if x not in before.roles]:
                for server_id in data:
                    server_sub = self.bot.get_guild(int(server_id))
                    if not server_sub:
                        continue
                    member = server_sub.get_member(before.id)
                    if not member:
                        continue
                    if str(role.id) in data[str(server_sub.id)]["roles"]:
                        for rolex in data[str(server_sub.id)]["roles"][str(role.id)]:
                            role_to_add = server_sub.get_role(int(rolex))
                            if role_to_add:
                                await member.add_roles(role_to_add)

            for role in [x for x in before.roles if x not in after.roles]:
                for server_id in data:
                    server_sub = self.bot.get_guild(int(server_id))
                    if not server_sub:
                        continue
                    member = server_sub.get_member(before.id)
                    if not member:
                        continue
                    if str(role.id) in data[str(server_sub.id)]["roles"]:
                        for rolex in data[str(server_sub.id)]["roles"][str(role.id)]:
                            role_to_remove = server_sub.get_role(int(rolex))
                            if role_to_remove:
                                await member.remove_roles(role_to_remove)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        server = member.guild
        data = await self.data.guild(server).sub_servers()
        if not data:
            return

        for server_id in data:
            sub_server = self.bot.get_guild(int(server_id))
            if not sub_server:
                return
            try:
                server_data = data[str(sub_server.id)]["roles"]
            except KeyError:
                return
            for roles_list in server_data:
                for role in server_data[roles_list]:
                    role = sub_server.get_role(int(role))
                    if not role:
                        return
                    try:
                        sub_server_member = sub_server.get_member(member.id)
                        await sub_server_member.remove_roles(role)
                    except discord.Forbidden:
                        return
