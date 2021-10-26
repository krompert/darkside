import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import re
import datetime
import random
import asyncio

class OdinEvent(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=934693420623, force_registration=True)

        default_guild = {
            "odin": {},
            "odinRole": None,
            "logchannel": None,
        }
        self.data.register_guild(**default_guild)
        self.loop = bot.loop.create_task(self.odinreg_loop())

    def cog_unload(self):
        self.loop.cancel()

    async def odinreg_loop(self):
        while True:
            guilds = await self.data.all_guilds()
            if guilds:
                for guild_id in guilds:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    
                    data = await self.data.guild(guild).odin()
                    for odinreg_id in data:
                        odinreg = await self.data.guild(guild).odin.get_raw(odinreg_id)
                        if odinreg["ended"] == False:
                            if datetime.datetime.utcnow().timestamp() >= odinreg["ends_on"]:
                                winners = []
                                for i in range(odinreg['winners']):
                                    winner = await self.end_odinreg(odinreg_id, odinreg, winners)
                                    if winner:
                                        winners.append(winner.mention)
                                winners = await self.winners_message(winners)
                                await self.embed_msg(odinreg_id, odinreg, winners)
                                await self._add_roles(guild, winners)
                                await self.MessageWinners(guild, winners)
                                await self.data.guild(guild).odin.set_raw(odinreg_id, "ended", value=True)
                            else:
                                await self.embed_msg(odinreg_id, await self.data.guild(guild).odin.get_raw(odinreg_id))
            
            await asyncio.sleep(60)
    
    async def MessageWinners(self, guild, winners):
        winners = [guild.get_member(int(x)) for x in re.findall(r'<@!?([0-9]+)>', winners)]
        for winner in winners:
            try:
                await winner.send(f"You have been selected for Odin at {guild.name}")
            except:
                pass

    async def _add_roles(self, guild, winners):
        role = await self.data.guild(guild).odinRole()
        log_channel = await self.data.guild(guild).logchannel()

        if not role:
            return

        role = guild.get_role(int(role))
        if log_channel:
            log_channel = guild.get_channel(int(log_channel))

        if not role:
            return

        winners = [guild.get_member(int(x)) for x in re.findall(r'<@!?([0-9]+)>', winners)]
        for winner in winners:
            try:
                await winner.add_roles(role)
                if log_channel:
                    await log_channel.send(f"{winner.mention} was selected and assigned **{role.name}** role to compete in Odin.")
            except:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        user = await guild.fetch_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        winnerRole = await self.data.guild(guild).odinRole()
        if winnerRole:
            winnerRole = guild.get_role(int(winnerRole))

        if user.bot:
            return

        data = await self.data.guild(guild).odin()
        if str(message.id) not in data:
            return

        if winnerRole in user.roles:
            await message.remove_reaction(payload.emoji, user)
            return

        data = await self.data.guild(guild).odin.get_raw(str(message.id))
        if data['roles_required']:
            roles = [guild.get_role(role) for role in data['roles_required'] if guild.get_role(role)]
            for role in roles:
                if role in user.roles:
                    try:
                        await user.send("You have entered the Odin Registraton.")
                    except:
                        pass
                    return
            
            roles= [x.name for x in roles]
            await user.send(f"You must have either one of these roles be a part of the odin registration: **{','.join(roles)}**")
            await message.remove_reaction(payload.emoji, user)

    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.group()
    async def odinreg(self, ctx):
        """Odin Registration System"""

    @odinreg.command(name="start")
    async def _start(self, ctx):
        """Start an odin registration."""
        response = {
            "roles_required": [],
            "ended": False,
            "channel": ctx.channel.id,
            "creator": ctx.author.id,
            "winners": 0
        }
        e = discord.Embed()
        e.set_author(name="Odin Registration Builder", icon_url=ctx.guild.icon_url)
        e.description = "Please enter a banner name."
        msg = await ctx.send(embed=e)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            res = await self.bot.wait_for("message", check=check, timeout=60)
            response["prize"] = res.content
        except asyncio.TimeoutError:
            await self.delete_message(msg)
            return await ctx.send("Timeout, you took too long to respond.")
        e.add_field(name="Prize", value=response["prize"])
        e.description = "How long should the Odin Registration last for?"
        await msg.edit(embed=e)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and self.time_str(m.content)[0] > 0
        try:
            res = await self.bot.wait_for("message", check=check, timeout=60)
            response["duration"] = duration = self.time_str(res.content)
        except asyncio.TimeoutError:
            await self.delete_message(msg)
            return await ctx.send("Timeout, you took too long to respond.")
        e.add_field(name="Duration", value=response["duration"][1])
        e.description = "How many members should be randomly selected?"
        await msg.edit(embed=e)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and int(m.content) > 0
        try:
            res = await self.bot.wait_for("message", check=check, timeout=60)
            response["winners"] = int(res.content)
        except asyncio.TimeoutError:
            await self.delete_message(msg)
            return await ctx.send("Timeout, you took too long to respond.")
        e.add_field(name="Winners", value=response["winners"])
        e.description = "Would you like to limit this registration to specific roles?\nRespond with role ids, names or mentions or just `no`"
        await msg.edit(embed=e)
        async def check(m):
            if m.content.lower() != "no":
                try:
                    roles = [await commands.RoleConverter().convert(ctx=ctx, argument=arg) for arg in m.content.split(" ")]
                except:
                    return False
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            res = await self.bot.wait_for("message", check=check, timeout=60)
            response["roles_required"] = [(await commands.RoleConverter().convert(ctx=ctx, argument=arg)).id for arg in res.content.split(" ")] if res.content.lower() != "no" else []
            roles = [f"<@&{_id}>" for _id in response["roles_required"] if ctx.guild.get_role(_id)]
        except asyncio.TimeoutError:
            await self.delete_message(msg)
            return await ctx.send("Timeout, you took too long to respond.")
        if roles:
            e.add_field(name="Roles", value=",".join(roles))
        e.description = ""
        await msg.edit(embed=e)

        response.update({
            "created_at": datetime.datetime.utcnow().timestamp(),
            "ends_on": datetime.datetime.utcnow().timestamp() + response["duration"][0],
            "duration": response["duration"][1]
        })

        data = await self.data.guild(ctx.guild).odin()
        
        embed=discord.Embed(description=f"odinreg ends in: **{duration[1]}**\nWinners: **{response['winners']}**\nHosted By: {ctx.author.mention}\n\n**React with 🎟️ to enter!**", title=f"{response['prize'].upper()}")
        embed.set_image(url="https://cdn.discordapp.com/attachments/710898402443001897/902635164952318012/odin-is-with-us-magnus-bruun.gif")
        if response["roles_required"]:
            embed.add_field(name="Roles Required", value=",".join(roles))
        message = await ctx.send(embed=embed)
        await self.data.guild(ctx.guild).odin.set_raw(message.id, value=response)
        await message.add_reaction("🎟️")

    async def delete_message(self, msg):
        try:
            await msg.delete()
        except:
            return 

    @odinreg.command(name="end")
    async def _end(self, ctx, messageID: int):
        """End a Registration."""
        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This registration was ended.")

        winners = []
        for i in range(data['winners']):
            winner = await self.end_odinreg(messageID, data, winners)
            winners.append(winner.mention)
        winners = await self.winners_message(winners)
        await self.MessageWinners(ctx.guild, winners)
        await self.embed_msg(messageID, data, winners)
        await self.data.guild(ctx.guild).odin.set_raw(messageID, "ended", value=True)
        await ctx.send(f"Ended the registration with the message id: `{messageID}`")

    @odinreg.command(name="reroll")
    async def _reroll(self, ctx, messageID: int):
        """Reroll a registration."""
        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if not data['ended']:
            return await ctx.send("This registration hasn't ended yet.")

        winner = await self.end_odinreg(messageID, data, winners)
        await ctx.send(f"🎟️ The new selected member is {winner.mention}! Valhalla Awaits!")

    async def winners_message(self, winners):
        message = "**Winner:** No one entered the registration."

        if len(winners) == 1:
            for winner in winners:
                message = f"**Winner:** {winner}"

        if len(winners) > 1:
            message = f"**Winners:** {', '.join(winners)}"

        return message

    @odinreg.group(name="role", invoke_without_command=True)
    async def _role(self, ctx):
        """Manage the roles required to enter Odin Registration."""

    @_role.command(name="remove")
    async def _remove(self, ctx, messageID, role: discord.Role):
        """Remove a role from the registration."""
        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This registration was ended.")

        roles = data['roles_required']
        if role.id not in roles:
            return await ctx.send("The role doesn't exist in the list.")
        
        roles.remove(role.id)
        await self.data.guild(ctx.guild).odin.set_raw(messageID, "roles_required", value=roles)
        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await self.embed_msg(messageID, data, None, roles)
        await ctx.send(f'Removed the {role.name} from the list')

    @_role.command(name="add")
    async def _add(self, ctx, messageID, role:discord.Role):
        """Add a role for the registation."""

        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This registration was ended.")

        roles = data['roles_required']
        if role.id in roles:
            return await ctx.send("This already exists in the list.")
        
        roles.append(role.id)
        await self.data.guild(ctx.guild).odin.set_raw(messageID, "roles_required", value=roles)
        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await self.embed_msg(messageID, data, None, roles)
        await ctx.send(f"Members with {role.name} will now be allowed to enter the Odin Registration.")
        
    @_role.command(name="list")
    async def _list(self, ctx, messageID):
        """List all the allowed roles for Odin Registration."""
        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This registration was ended.")

        roles = data['roles_required']
        if not roles:
            return await ctx.send("There were no roles allowed for this registration.")

        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await ctx.send(embed=discord.Embed(description=",".join(roles), title="Roles Allowed"))

    @odinreg.group(name="winners", invoke_without_command=True)
    async def _winners(self, ctx):
        """ View the winners of an odin registration."""

    @_winners.command(name="set")
    async def _set(self, ctx, messageID: int, winners: int):
        """ Set the amount of selected members for a Odin Registration."""
        data = await self.data.guild(ctx.guild).odin()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No registration was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).odin.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This registration was ended.")

        if data['winners'] == winners:
            return await ctx.send("Previous winner count is the same as the new one.")

        await self.data.guild(ctx.guild).odin.set_raw(messageID, "winners", value=winners)
        await self.embed_msg(messageID, await self.data.guild(ctx.guild).odin.get_raw(messageID))
        await ctx.send(f"Changed the odin total winners to : **{winners}**.")

    async def embed_msg(self, messageID, data, winners=None, roles=None):
        time_left = self.time_str(data['ends_on'] - datetime.datetime.utcnow().timestamp())
        host = await self.bot.fetch_user(data['creator'])
        host = host.mention if host else "Not Found"
        content = None
        if winners:
            embed=discord.Embed(description=f"{winners}\n**Host:** {host}", title=data['prize'].upper(), timestamp=datetime.datetime.utcnow()).set_footer(text="Ended at")
            content = f"🎟️ Congratulations {winners.replace('**Winner:**', '')}!" + f" You have been selected **{data['prize'].upper()}** in the odin registration. VALHALLA AWAITS!" if winners != "**Winner:** No one entered the registration." else ""
        else:
            embed=discord.Embed(description=f"Odin Registratin ends in: **{time_left[1]}**\nWinners: **{data['winners']}**\nHosted By: {host}\n\n**React with 🎟️ to enter!**", title=data['prize'].upper())
            embed.set_image(url="https://cdn.discordapp.com/attachments/710898402443001897/902635164952318012/odin-is-with-us-magnus-bruun.gif")
            if roles:
                embed.add_field(name="Roles Required", value=",".join(roles))

        channel = self.bot.get_channel(data['channel'])
        if channel:
            message = await channel.fetch_message(messageID)
            if message:
                try:
                    if content:
                        await channel.send(content)
                    return await message.edit(embed=embed)
                except:
                    return None
        
        return None

    async def end_odinreg(self, messageID, data, intialwinners):
        channel = self.bot.get_channel(data['channel'])
        if channel:
            message = await channel.fetch_message(messageID)
            if message:
                reaction = [x for x in message.reactions if x.emoji == "🎟️"][0]
                winners = [x for x in await reaction.users().flatten() if x != self.bot.user]
                if not winners:
                    return None
                
                while True:
                    winner = random.choice(winners)
                    if winner.mention not in intialwinners:
                        break

                return winner

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group()
    async def odinregwinner(self, ctx):
        """Setup autorole for odin selected members and odin channel."""
        if ctx.invoked_subcommand is None:
            pass

    @odinregwinner.command(name="role")
    async def ___role(self, ctx, role: discord.Role=None):
        """Setup autorole for registration winner."""
        if not role:
            await self.data.guild(ctx.guild).odinRole.set(None)
            await ctx.send("Odin role has been reset!")
        if role:
            await self.data.guild(ctx.guild).odinRole.set(role.id)
            await ctx.send(f"Odin role has been set to **{role.name}**!")

    @odinregwinner.command(name="logchannel")
    async def _logchannel(self, ctx, channel: discord.TextChannel=None):
        """Setup a log channel where a message is sent when user is assigned a role."""
        if not channel:
            await self.data.guild(ctx.guild).logchannel.set(None)
            await ctx.send("Log channel has been reset!")
        if channel:
            await self.data.guild(ctx.guild).logchannel.set(channel.id)
            await ctx.send(f"Log channel has been set to **{channel.mention}**!")

    def time_str(self, text, short=False):
        data = []
        t = 0
        t_str = ""
        reg = r"([0-9]+)(?: )?([ywdhms])+"
        if isinstance(text, str):
            data = re.findall(reg, text, re.IGNORECASE)
        if isinstance(text, int) or isinstance(text, float):
            t = text
        for d in data:
            if d[1].lower() == "y":
                t += 604800 * 4.3482 * 12 * int(d[0])
            if d[1] == "M":
                t += 604800 * 4.3482 * int(d[0])
            if d[1].lower() == "w":
                t += 604800 * int(d[0])
            if d[1].lower() == "d":
                t += 86400 * int(d[0])
            if d[1].lower() == "h":
                t += 3600 * int(d[0])
            if d[1] == "m":
                t += 60 * int(d[0])
            if d[1].lower() == "s":
                t += int(d[0])
        y, s = divmod(t, 604800 * 4.3482 * 12)
        M, s = divmod(s, 604800 * 4.3482)
        w, s = divmod(s, 604800)
        d, s = divmod(s, 86400)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        y = int(y)
        M = int(M)
        w = int(w)
        d = int(d)
        h = int(h)
        m = int(m)
        s = int(s)
        if y >= 1:
            t_str += f"{y}y" if short else f"{y} year"
            t_str += "s " if not short and y != 1 else " "
        if M >= 1:
            t_str += f"{M}M" if short else f"{M} month"
            t_str += "s " if not short and M != 1 else " "
        if w >= 1:
            t_str += f"{w}w" if short else f"{w} week"
            t_str += "s " if not short and w != 1 else " "
        if d >= 1:
            t_str += f"{d}d" if short else f"{d} day"
            t_str += "s " if not short and d != 1 else " "
        if h >= 1:
            t_str += f"{h}h" if short else f"{h} hour"
            t_str += "s " if not short and h != 1 else " "
        if m >= 1:
            t_str += f"{m}m" if short else f"{m} minute"
            t_str += "s " if not short and m != 1 else " "
        if s >= 1:
            t_str += f"{s}s" if short else f"{s} second"
            t_str += "s " if not short and s != 1 else " "
        return t, t_str
