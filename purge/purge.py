import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import re
import datetime
import asyncio

class PurgeMessages(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=257252395298520, force_registration=True)
        default_guild = {
            "channels": {}
        }
        self.data.register_guild(**default_guild)
        self.loop = bot.loop.create_task(self._purge_loop())

    def cog_unload(self):
        self.loop.cancel()
         
    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group()
    async def purge(self, ctx):
        """Advanced messages purger."""
        if ctx.invoked_subcommand is None:
            pass

    @purge.command(name="channel")
    async def _channel(self, ctx, count:int=100):
        "Delete a number of messages from a channel."
        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=lambda m: not m.pinned)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages in {ctx.channel.mention}.")

    @purge.command(name="user")
    async def _user(self, ctx, user: discord.Member, count:int=100):
        """Delete messages for a user in the channel."""
        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=lambda m: m.author == user and not m.pinned)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages sent by **{user}**!")

    @purge.command()
    async def match(self, ctx, text: str, count:int=100):
        """Delete messages containing text."""

        def msg_check(m):
            return text.lower() in m.content.lower() and not m.pinned

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages that includes **{text}**!")

    @purge.command(name="not")
    async def _not(self, ctx, text: str, count:int=100):
        """Delete messages not containing text."""

        def msg_check(m):
            return text.lower() not in m.content.lower() and not m.pinned

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages which do not include **{text}**!")

    @purge.command(name="startswith")
    async def _startswith(self, ctx, text: str, count:int=100):
        """Delete messages thats starts with specific text."""

        def msg_check(m):
            return m.content.lower().startswith(text.lower()) and not m.pinned

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages which starts with **{text}**!")

    @purge.command(name="endswith")
    async def _endswith(self, ctx, text: str, count:int=100):
        """Delete messages that endswith specific text."""

        def msg_check(m):
            return m.content.lower().endswith(text.lower()) and not m.pinned

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages which ends with **{text}**!")

    @purge.command(name="links")
    async def _link(self, ctx, count:int=100):
        """Delete a number links posted in the channel."""

        def msg_check(m):
            if ("http://" in m.content.lower()) or ("https://" in m.content.lower()):
                if not m.pinned:
                    return True

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages with links!")

    @purge.command(name="invites")
    async def _invites(self, ctx, count:int=100):
        """Delete server invites posted in the channel."""

        def msg_check(m):
            reinvite = re.compile("(?:[\s \S]|)*(?:https?:\/\/)?(?:www.)?(?:discord.gg|(?:canary.)?discordapp.com\/invite)\/((?:[a-zA-Z0-9]){2,32})(?:[\s \S]|)*", re.IGNORECASE)
            if reinvite.match(m.content) and not m.pinned:
                return True
            return False

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages with discord invites!")

    @purge.command(name="images")
    async def _images(self, ctx, count:int=100):
        """ Delete a number of images in the channel."""

        def msg_check(message):
            if message.pinned:
                return False
            if not message.attachments:
                return False
            for att in message.attachments:
                if ".jpg" in att.filename.lower() or ".png" in att.filename.lower() or ".jpeg" in att.filename.lower():
                    return True
            return False

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages that includes images!")

    @purge.command(name="mentions")
    async def _mentions(self, ctx, count:int=100):
        """Delete messages with mentions in the channel."""

        def msg_check(message):
            if message.pinned:
                return False
            if message.mentions or message.role_mentions or message.channel_mentions or message.mention_everyone:
                return True
            return False

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages with mentions!")

    @purge.command(name="embeds")
    async def _embeds(self, ctx, count:int=100):
        """Delete messages containing rich embeds in the channel."""

        def msg_check(message):
            if message.embeds and not message.pinned:
                return True
            return False

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages with embeds!")

    @purge.command(name="bots")
    async def _bots(self, ctx, count:int=100):
        """Delete messages sent by bots."""

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=lambda m: m.author.bot and not m.pinned)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages sent by bots!")

    @purge.command(name="text")
    async def _text(self, ctx, count:int=100):
        """Delete messages containing text, ignoring images/embeds."""

        def image_check(message):
            if not message.attachments:
                return False
            for att in message.attachments:
                if ".jpg" in att.filename.lower() or ".png" in att.filename.lower() or ".jpeg" in att.filename.lower():
                    return True
            return False

        def msg_check(message):
            if message.pinned:
                return False
            if message.embeds or image_check(message):
                return False
            return True

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages, ignoring embeds and images!")

    @purge.command(name="role")
    async def _role(self, ctx, role: discord.Role, count:int=100):
        """Delete messages sent by users with speicfic role."""

        def msg_check(message):
            if message.pinned:
                return False
            if role in message.author.roles:
                return True
            return False

        try:
            msgs = await ctx.channel.purge(limit=count, before=ctx.message, check=msg_check)
        except discord.HTTPException:
            return await ctx.send("Unable to delete the messages older than 14 days.")

        await ctx.send(f"Successfully deleted **{len(msgs)}** messages sent users with the role **{role.name}**!")

    @purge.command(name="timer")
    async def _timer(self, ctx, channel: discord.TextChannel, time: str,*, msg: str):
        """Set a purge timer, along the channel and a message."""
        if time == "0":
            if str(channel.id) in await self.data.guild(ctx.guild).channels():
                await self.data.guild(ctx.guild).channels.clear_raw(channel.id)
                return await ctx.send(f"Removed auto purge for {channel.mention}.")
            else:
                return await ctx.send("That channel doesn't exist in the data.")

        time_conversion, time_text = self.time_str(time, True)
        await self.data.guild(ctx.guild).channels.set_raw(channel.id, value={"time": time_conversion, "msg": msg, "last_purged": datetime.datetime.utcnow().timestamp()})
        await ctx.send(f"Bot will now purge {channel.mention} every **{time_text}** and a message will be sent after the purge is completed.")

    @purge.command(name="list")
    async def _list(self, ctx):
        """Lists of the active loops."""
        loops = await self.data.guild(ctx.guild).channels()
        if not loops:
            return await ctx.send("Auto Purge is not running in any channels.")

        channels = [ctx.guild.get_channel(int(x)).mention for x in loops if ctx.guild.get_channel(int(x))]
        msg = ", ".join(channels)
        embed=discord.Embed(color=ctx.author.color, description=msg, title="Auto Purge is active in the following channels")
        await ctx.send(embed=embed)
    
    async def _purge_loop(self): 
        while True:
            await asyncio.sleep(3)
            data = await self.data.all_guilds()
            if data:
                for guild_id in data:
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue
                    
                    guild_data = await self.data.guild(guild).channels()
                    
                    for channel_id in guild_data:
                        channel = guild.get_channel(int(channel_id))
                        if not channel:
                            await self.data.guild(guild).channels.clear_raw(channel_id)
                            continue
                        
                        time_left = guild_data[channel_id]['last_purged'] + guild_data[channel_id]['time']
                        if time_left < datetime.datetime.utcnow().timestamp():
                            messages = []
                            async for m in channel.history(limit=2000):
                                if not m.pinned:
                                    messages.append(m)

                            while messages:
                                try:
                                    await channel.delete_messages(messages[:100])
                                except discord.errors.HTTPException:
                                    pass
                                
                                messages = messages[100:]
                                await asyncio.sleep(1.5)
                                
                            try:
                                await channel.send(guild_data[channel_id]['msg'])
                            except discord.errors.HTTPException:
                                pass
                            
                            await self.data.guild(guild).channels.set_raw(channel.id, "last_purged", value=datetime.datetime.utcnow().timestamp())
                    
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
