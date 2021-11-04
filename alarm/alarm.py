import discord
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
import datetime
import re
from discord.ext import tasks
import asyncio

class Alarm(commands.Cog):
    "Alarm Cog."

    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=464651651984, force_registration=True)
        default_guild = {
            "schedules": []
        }
        
        self.data.register_guild(**default_guild)
        self.scheduleLoop.start()

    def cog_unload(self):
        self.scheduleLoop.cancel()

    async def get_pages(self, data, guild):
        page_size = 3
        i = 0
        output_data = []
        text = ""
        n = 0
        for scheduleData in data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            channel = guild.get_channel(scheduleData['channelID'])
            author = guild.get_member(scheduleData['author'])
            text += f"`ID:` **{n}**\n`Channel:` {channel.mention if channel else 'channel not found.'}\n`Author:` {author.mention if author else 'author not found.'}\n`Initial Time:` **{datetime.datetime.fromtimestamp(scheduleData['initialTime']).strftime('%Y-%m-%d %H:%M')}**\n`Message:` **{scheduleData['message']}**\n\n\n"
            n += 1
        if text != "":
            output_data.append(text)
        return output_data

    async def delete_schedule(self, guild, scheduleData):
        data = await self.data.guild(guild).schedules()
        data.remove(scheduleData)
        await self.data.guild(guild).schedules.set(data)
        return data

    @tasks.loop(minutes=2)
    async def scheduleLoop(self):
        for guild in await self.data.all_guilds():
            guild = self.bot.get_guild(int(guild))
            if not guild:
                continue
            data = await self.data.guild(guild).schedules()
            for scheduleData in data:
                if scheduleData['nextTrigger']:
                    time = scheduleData['nextTrigger'] - datetime.datetime.utcnow().timestamp()
                    if time < 30:
                        asyncio.create_task(self.run_schedule(time if time > 0 else 1, guild, scheduleData))
                else:
                    await self.delete_schedule(guild, scheduleData)

    async def run_schedule(self, time, guild, scheduleData):
        await asyncio.sleep(time)
        data = await self.data.guild(guild).schedules()
        if scheduleData not in data:
            return

        channel = guild.get_channel(scheduleData['channelID'])
        if not channel:
            return await self.delete_schedule(guild, scheduleData)

        try:
            await channel.send(scheduleData['message'])
        except:
            pass

        return await self.delete_schedule(guild, scheduleData)
        
    @checks.admin_or_permissions(administrator=True)
    @commands.group(name="alarm")
    async def _alarm(self, ctx):
        """Manage schedule systen on the server."""
        pass

    @_alarm.command(name='list')
    async def _list(self, ctx, page_no: int=None):
        """Shows the vote leaderboard of top users."""
        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.guild(ctx.guild).schedules()
        if not data:
            return await ctx.send("There is no available data to show.")

        pages = await self.get_pages(data, ctx.guild)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        e=discord.Embed(title=f"Total Schedules - {len(data)}", description=pages[page_no], colour=ctx.author.color)
        e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
        sent = await ctx.send(embed=e)
        if len(pages) == 1:
            return

        try:
            await sent.add_reaction("◀️")
            await sent.add_reaction("▶️")
        except:
            return await ctx.send('Unable to react to the message, please make sure i have the required permissions.')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == sent.id and str(reaction.emoji) in ["◀️","▶️"]
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=120)
                del user
            except Exception:
                try:
                    await sent.clear_reactions()
                except:
                    pass
                break
            if str(reaction.emoji) == "◀️":
                page_no -= 1
                if page_no < 0:
                    page_no = len(pages) - 1
            if str(reaction.emoji) == "▶️":
                page_no += 1
                if page_no > len(pages) - 1:
                    page_no = 0
            e=discord.Embed(title=f"Total Schedules - {len(data)}", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break

    @_alarm.command(name="clear")
    async def _clear(self, ctx):
        """Clear all the schedules on a server."""
        await self.data.guild(ctx.guild).schedules.clear()
        await ctx.send("Successfully cleared all the schedules from this server.")

    @_alarm.command(name='delete')
    async def _delete(self, ctx, scheduleID: int):
        """Delete a schedule from the list using its ID."""
        data = await self.data.guild(ctx.guild).schedules()
        if scheduleID < 0:
            return await ctx.send("scheduleID must be equal to or greater than 0.")
        
        if not data:
            return await ctx.send("There were no schedules set up on this server.")

        if len(data)-1 < scheduleID:
            return await ctx.send(f"Invalid schedulID provided, make sure the ID you provide is smaller than or equal to {len(data)-1}.")

        try:
            scheduleData = data[scheduleID]
        except IndexError:
            return await ctx.send("No data, make sure to provide a valid scheduleID.")

        data.remove(scheduleData)
        
        await self.data.guild(ctx.guild).schedules.set(data)
        await ctx.send(f"Deleted the schedule with ID: `{scheduleID}`")

    @_alarm.command(name='edit')
    async def _edit(self, ctx, scheduleID: int, *, message: str):
        """Edit message of a schedule from the list using its ID."""
        data = await self.data.guild(ctx.guild).schedules()
        if scheduleID < 0:
            return await ctx.send("scheduleID must be equal to or greater than 0.")
        
        if not data:
            return await ctx.send("There were no schedules set up on this server.")

        if len(data)-1 < scheduleID:
            return await ctx.send(f"Invalid schedulID provided, make sure the ID you provide is smaller than or equal to {len(data)-1}.")

        try:
            data[scheduleID]
            data[scheduleID]['message'] = message
        except IndexError:
            return await ctx.send("No data, make sure to provide a valid scheduleID.")

        await self.data.guild(ctx.guild).schedules.set(data)
        await ctx.send(f"Successfully changed the message for schedule with ID: `{scheduleID}`.")

    @_alarm.command(name="info", aliases=['view'])
    async def _info(self, ctx, scheduleID: int):
        """View information about an already existing schedule using its ID."""
        data = await self.data.guild(ctx.guild).schedules()
        if scheduleID < 0:
            return await ctx.send("scheduleID must be equal to or greater than 0.")
        
        if not data:
            return await ctx.send("There were no schedules set up on this server.")

        if len(data)-1 < scheduleID:
            return await ctx.send(f"Invalid schedulID provided, make sure the ID you provide is smaller than or equal to {len(data)-1}.")
        
        try:
            scheduleData = data[scheduleID]
        except IndexError:
            return await ctx.send("No data, make sure to provide a valid scheduleID.")
        channel = ctx.guild.get_channel(scheduleData['channelID'])
        author = ctx.guild.get_member(scheduleData['author'])
        embed=discord.Embed(color=ctx.author.color, title='Schedule Info', description=f"Schedule with the ID: `{scheduleID}` was added by {author.mention if author else 'user not found.'}", inline=False)
        embed.add_field(name="Channel", value=channel.mention if channel else "Channel not found.", inline=False)
        embed.add_field(name="Initial Time", value=datetime.datetime.fromtimestamp(scheduleData['initialTime']).strftime('%Y-%m-%d %H:%M'), inline=False)
        embed.add_field(name="message", value=scheduleData['message'],  inline=False)
        await ctx.send(embed=embed)

    @_alarm.command(name="message")
    async def _message(self, ctx, channel: discord.TextChannel, initial_time: str, *, message: str):
        """Schedule a message to be sent.
        
        Usage: 
            [p]schedule message <channel> <intial_time> <message>

        initial_time Example: 
            "2021-02-27 08:15"
            "2021-02-27 00:00"
            "yyyy-mm-dd hh-min"

        message Example:    
            this is a test message 

        Example Usage:
            [p]schedule message #channel "2021-02-27 08:15" this is a test message

        Note:
            Make sure to use speech marks " " around the time if it has space in between else the command will not work.

        """
        initial_time = self.get_time(initial_time)[0]
        print(initial_time)
        initial_time = self.get_initial(initial_time)
        if not initial_time:
            return await ctx.send("Invalid format for initial time provided, make sure its similar to this: `2h or 2m`.")

        data = await self.data.guild(ctx.guild).schedules()
        
        data.append({
            "channelID": channel.id, 
            "initialTime": initial_time,
            "author": ctx.author.id,
            'message': message,
            'nextTrigger': initial_time})

        await self.data.guild(ctx.guild).schedules.set(data)
        await ctx.send(f"New schedule has been set in {channel.mention} by {ctx.author.mention}. Schedule ID: `{len(data)-1}`.")
        
    def get_time(self, text, short=False):
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

    def get_initial(self, time: str):
        'Converting time into a datetime timestamp.'
        try:
            time = datetime.datetime.utcnow().timestamp() + time
            timestamp = datetime.datetime.fromtimestamp(time).timestamp()

            if timestamp <= datetime.datetime.utcnow().timestamp():
                print(datetime.datetime.utcnow())
                print('timestamp is smaller')
                timestamp = None
        except Exception as e:
            print(e)
            timestamp = None
        
        return timestamp