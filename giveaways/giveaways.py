import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import re
import datetime
import random
import asyncio

class Giveaways(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=934693420623, force_registration=True)

        default_guild = {
            "giveaways": {}
        }
        self.data.register_guild(**default_guild)
        self.loop = bot.loop.create_task(self.giveaway_loop())

    def cog_unload(self):
        self.loop.cancel()

    async def giveaway_loop(self):
        while True:
            guilds = await self.data.all_guilds()
            if guilds:
                for guild_id in guilds:
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    
                    data = await self.data.guild(guild).giveaways()
                    for giveaway_id in data:
                        giveaway = await self.data.guild(guild).giveaways.get_raw(giveaway_id)
                        if giveaway["ended"] == False:
                            if datetime.datetime.utcnow().timestamp() >= giveaway["ends_on"]:
                                winners = []
                                for i in range(giveaway['winners']):
                                    winner = await self.end_giveaway(giveaway_id, giveaway)
                                    if winner:
                                        winners.append(winner.mention)
                                winners = await self.winners_message(winners)
                                await self.embed_msg(giveaway_id, giveaway, winners)
                                await self.data.guild(guild).giveaways.set_raw(giveaway_id, "ended", value=True)
                            else:
                                await self.embed_msg(giveaway_id, await self.data.guild(guild).giveaways.get_raw(giveaway_id))
            
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = await self.bot.fetch_guild(payload.guild_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        user = await guild.fetch_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        
        if user.bot:
            return

        data = await self.data.guild(guild).giveaways()
        if str(message.id) not in data:
            return

        data = await self.data.guild(guild).giveaways.get_raw(str(message.id))
        if data['roles_required']:
            roles = [guild.get_role(role) for role in data['roles_required'] if guild.get_role(role)]
            for role in roles:
                if role in user.roles:
                    try:
                        await user.send("You have entered the giveaway.")
                    except:
                        pass
                    return
            
            roles= [x.name for x in roles]
            await user.send(f"You must have either one of these roles be a part of the giveaway: **{','.join(roles)}**")
            await message.remove_reaction(payload.emoji, user)

    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.group()
    async def giveaway(self, ctx):
        """Giveaway System"""

    @giveaway.command(name="start")
    async def _start(self, ctx, duration: str, winners: int, *, prize: str):
        """Start a giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        duration = self.time_str(duration)
        if duration[1] == "":
            return await ctx.send("Invalid duration provided, make sure the format is similar to: `1w4d3h2s`.")
        
        embed=discord.Embed(description=f"Giveaway ends in: **{duration[1]}**\nWinners: **{winners}**\nHosted By: {ctx.author.mention}\n\n**React with :tada: to enter!**", title=f"{prize.upper()}")
        message = await ctx.send(embed=embed)
        await self.data.guild(ctx.guild).giveaways.set_raw(message.id, value={"roles_required": [], "ended": False, "prize": prize, "channel": message.channel.id, "created_at": datetime.datetime.utcnow().timestamp(), "creator": ctx.author.id, "winners": winners, "ends_on": datetime.datetime.utcnow().timestamp() + duration[0], "duration": duration[1]})
        await message.add_reaction("🎉")
    
    @giveaway.command(name="end")
    async def _end(self, ctx, messageID: int):
        """End a giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This giveaway was ended.")

        winners = []
        for i in range(data['winners']):
            winner = await self.end_giveaway(messageID, data)
            winners.append(winner.mention)

        winners = await self.winners_message(winners)
        await self.embed_msg(messageID, data, winners)
        await self.data.guild(ctx.guild).giveaways.set_raw(messageID, "ended", value=True)
        await ctx.send(f"Ended the giveawawy with the message id: `{messageID}`")

    @giveaway.command(name="reroll")
    async def _reroll(self, ctx, messageID: int):
        """Reroll a giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if not data['ended']:
            return await ctx.send("This giveaway hasn't ended yet.")

        winner = await self.end_giveaway(messageID, data)
        await ctx.send(f":tada: The new winner is {winner.mention}! Congratulations!")

    async def winners_message(self, winners):
        message = "**Winner:** No one entered the giveaway."

        if len(winners) == 1:
            for winner in winners:
                message = f"**Winner:** {winner}"

        if len(winners) > 1:
            message = f"**Winners:** {', '.join(winners)}"

        return message

    @giveaway.group(name="role", invoke_without_command=True)
    async def _role(self, ctx):
        """Manage the roles required to enter a giveaway."""

    @_role.command(name="remove")
    async def _remove(self, ctx, messageID, role: discord.Role):
        """Remove a role from the giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This giveaway was ended.")

        roles = data['roles_required']
        if role.id not in roles:
            return await ctx.send("The role doesn't exist in the list.")
        
        roles.remove(role.id)
        await self.data.guild(ctx.guild).giveaways.set_raw(messageID, "roles_required", value=roles)
        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await self.embed_msg(messageID, data, None, roles)
        await ctx.send(f'Removed the {role.name} from the list')

    @_role.command(name="add")
    async def _add(self, ctx, messageID, role:discord.Role):
        """Add a role for the giveaway."""

        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This giveaway was ended.")

        roles = data['roles_required']
        if role.id in roles:
            return await ctx.send("This already exists in the list.")
        
        roles.append(role.id)
        await self.data.guild(ctx.guild).giveaways.set_raw(messageID, "roles_required", value=roles)
        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await self.embed_msg(messageID, data, None, roles)
        await ctx.send(f"Users with {role.name} will now be allowed to enter the giveaway.")
        
    @_role.command(name="list")
    async def _list(self, ctx, messageID):
        """List all the allowed roles for a giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This giveaway was ended.")

        roles = data['roles_required']
        if not roles:
            return await ctx.send("There were no roles allowed for this giveaway.")

        roles = [ctx.guild.get_role(role).mention for role in roles if ctx.guild.get_role(role)]
        await ctx.send(embed=discord.Embed(description=",".join(roles), title="Roles Allowed"))

    @giveaway.group(name="winners", invoke_without_command=True)
    async def _winners(self, ctx):
        """ View the winners of a giveaway."""

    @_winners.command(name="set")
    async def _set(self, ctx, messageID: int, winners: int):
        """ Set the amount of winners for a giveaway."""
        data = await self.data.guild(ctx.guild).giveaways()
        if not data or str(messageID) not in data:
            return await ctx.send(f"No giveaway was found with the message id: `{messageID}`")
        
        data = await self.data.guild(ctx.guild).giveaways.get_raw(messageID)
        if data['ended']:
            return await ctx.send("This giveaway was ended.")

        if data['winners'] == winners:
            return await ctx.send("Previous winner count is the same as the new one.")

        await self.data.guild(ctx.guild).giveaways.set_raw(messageID, "winners", value=winners)
        await self.embed_msg(messageID, await self.data.guild(ctx.guild).giveaways.get_raw(messageID))
        await ctx.send(f"Changed the giveaways total winners to : **{winners}**.")

    async def embed_msg(self, messageID, data, winners=None, roles=None):
        time_left = self.time_str(data['ends_on'] - datetime.datetime.utcnow().timestamp())
        host = await self.bot.fetch_user(data['creator'])
        host = host.mention if host else "Not Found"
        content = None
        if winners:
            embed=discord.Embed(description=f"{winners}\n**Host:** {host}", title=data['prize'].upper(), timestamp=datetime.datetime.utcnow()).set_footer(text="Ended at")
            content = f":tada: Congratulations {winners.replace('**Winner:**', '')}! You have won the {data['prize'].upper()} giveaway!"
        else:
            embed=discord.Embed(description=f"Giveaway ends in: **{time_left[1]}**\nWinners: **{data['winners']}**\nHosted By: {host}\n\n**React with :tada: to enter!**", title=data['prize'].upper())
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

    async def end_giveaway(self, messageID, data):
        channel = self.bot.get_channel(data['channel'])
        if channel:
            message = await channel.fetch_message(messageID)
            if message:
                reaction = [x for x in message.reactions if x.emoji == "🎉"][0]
                winners = [x for x in await reaction.users().flatten() if x != self.bot.user]
                if not winners:
                    return None
                
                winner = random.choice(winners)

                return winner


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