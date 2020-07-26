import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from datetime import datetime
import re
import asyncio


class TimedRoles(commands.Cog):
    def __init__(self, bot: Red):
        self.config = Config.get_conf(self, identifier=202005113)
        self.bot = bot
        default_guild = {
            "timed_roles": []
        }
        default_member = {
            "timed_roles": []
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

# Commands

    @commands.command(name="timedrole", help="Gives a temporary role to a user.")
    @commands.has_permissions(administrator=True)
    async def _timed_role(self, ctx, role: discord.Role, *, time=None):
        roles = await self.config.guild(ctx.guild).timed_roles()
        invalid_time = discord.Embed(
            title="Invalid time format",
            description="Example: 5h | 1 minute | 2 days",
            color=0xff0000
        )
        for srole in roles:
            if srole[0] != role.id:
                continue
            if not time:
                roles.remove(srole)
                await ctx.send(f"Removed **{role.name}** from timed roles.")
            else:
                data = re.search(r"^([0-9]+)(?: )?(minute|m|hour|h|day|d)", time, re.IGNORECASE)
                if not data or len(data.groups()) != 2:
                    await ctx.send(embed=invalid_time)
                    return
                result = data.groups()
                time, time_text = self.time_string(result)
                roles.remove(srole)
                srole[1] = time
                roles.append(srole)
                await ctx.send(f"**{role.name}** is now set to be removed after {result[0]} {time_text}.")
            await self.config.guild(ctx.guild).timed_roles.set(roles)
            return
        if not time:
            await ctx.send(embed=invalid_time)
            return
        data = re.search(r"^([0-9]+)(?: )?(minute|m|hour|h|day|d)", time, re.IGNORECASE)
        if not data or len(data.groups()) != 2:
            await ctx.send(embed=invalid_time)
            return
        result = data.groups()
        time, time_text = self.time_string(result)
        srole = [role.id, time]
        roles.append(srole)
        await ctx.send(f"**{role.name}** was added to timed roles and set to be removed after {result[0]} {time_text}.")
        await self.config.guild(ctx.guild).timed_roles.set(roles)

    def time_string(self, result):
        raw_time = int(result[0])
        if result[1] in ["m", "minute"]:
            time = raw_time * 60
            time_text = "minutes"
            if raw_time == 1:
                time_text = time_text[:-1]
        if result[1] in ["h", "hour"]:
            time = raw_time * 60 * 60
            time_text = "hours"
            if raw_time == 1:
                time_text = time_text[:-1]
        if result[1] in ["d", "day"]:
            time = raw_time * 60 * 60 * 24
            time_text = "days"
            if raw_time == 1:
                time_text = time_text[:-1]
        return time, time_text


#await self.config.guild(ctx.guild).channel.set(channel)
#await self.config.guild(guild).timed_roles()

# Events

    @commands.Cog.listener("on_member_update")
    async def timed_role_handler(self, before, after):
        try:
            roles = await self.config.member(before).timed_roles()
            timed_roles = [r[0] for r in await self.config.guild(before.guild).timed_roles()]
            now = datetime.utcnow().timestamp()
            if before.roles == after.roles:
                return
            before_roles = [r.id for r in before.roles]
            after_roles = [r.id for r in after.roles]
            for after_role in after_roles:
                if after_role in before_roles:
                    continue
                if after_role in timed_roles:
                    srole = [after_role, now]
                    roles.append(srole)
            for before_role in before_roles:
                if before_role not in timed_roles:
                    for role in roles:
                        if role[0] == before_role:
                            roles.remove(role)
                    continue
                if before_role in after_roles:
                    continue
                for role in roles:
                    if role[0] == before_role:
                        roles.remove(role)
            await self.config.member(before).timed_roles.set(roles)
        except Exception as e:
            print(f"{e.__traceback__.tb_lineno} - {e}")

# Tasks

    async def _timed_roles(self):
        while True:
            try:
                await asyncio.sleep(10)
                now = datetime.utcnow().timestamp()
                for guild in self.bot.guilds:
                    roles = await self.config.guild(guild).timed_roles()
                    for srole in roles:
                        role = guild.get_role(srole[0])
                        if not role:
                            roles.remove(srole)
                            await self.config.guild(guild).timed_roles.set(roles)
                            continue
                guilds_data = await self.config.all_guilds()
                for gid in guilds_data:
                    g = self.bot.get_guild(gid)
                    if not g:
                        continue
                    members_data = await self.config.all_members(guild=g)
                    for mid in members_data:
                        member = g.get_member(mid)
                        timed_roles = members_data[mid]["timed_roles"]
                        for mrole in member.roles:
                            if mrole.id in [r[0] for r in await self.config.guild(g).timed_roles()]:
                                if mrole.id not in [r[0] for r in await self.config.member(member).timed_roles()]:
                                    try:
                                        await member.remove_roles(role)
                                    except:
                                        pass
                                    continue
                        for srole in timed_roles:
                            guild_timed_roles = [r[0] for r in await self.config.guild(g).timed_roles()]
                            role = g.get_role(srole[0])
                            if not role:
                                for grole in guild_timed_roles:
                                    if grole[0] == srole[0]:
                                        guild_timed_roles.remove(grole)
                                await self.config.guild(g).timed_roles.set(guild_timed_roles)
                                timed_roles.remove(srole)
                                continue
                            if role.id not in guild_timed_roles:
                                timed_roles.remove(srole)
                                try:
                                    await member.remove_roles(role)
                                except:
                                    pass
                                continue
                            guild_timed_roles = await self.config.guild(g).timed_roles()
                            for grole in guild_timed_roles:
                                if grole[0] != srole[0]:
                                    continue
                                wait = srole[1] + grole[1]
                                if not now > wait: 
                                    continue
                                timed_roles.remove(srole)
                                try:
                                    await member.remove_roles(role)
                                except:
                                    pass
                                continue
                        await self.config.member(member).timed_roles.set(timed_roles)
            except Exception as e:
                print(e)


            