import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import re
import datetime

class Seen(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=43604363064340, force_registration=True)
        default_member = {
            "last_seen": None,
            }
        self.data.register_member(**default_member)

    @commands.command(name="seen")
    async def _seen(self, ctx, user: discord.Member=None):
        """View the last time a user sent a message."""
        
        user = ctx.author if not user else user
        
        if user.bot:
            return await ctx.send(embed=discord.Embed(description="Bots don't have a last seen."))
        
        data = await self.data.member(user).last_seen()
        if data:
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} was last online **{self.time_str(datetime.datetime.utcnow().timestamp()-data, True)[1]}** ago.").set_author(name=user.name, icon_url=user.avatar_url))
        
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} haven't been on discord for a while now.").set_author(name=user.name, icon_url=user.avatar_url))
        
    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if not message.guild:
            return
        
        if message.author.bot:
            return
        
        await self.data.member(message.author).last_seen.set(message.created_at.timestamp())
        
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
            
        