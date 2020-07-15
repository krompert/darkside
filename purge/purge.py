import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core import checks
import re

class PurgeMessages(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

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
            reinvite = re.compile("(?:[\s \S]|)*(?:https?://)?(?:www.)?(?:discord.gg|(?:canary.)?discordapp.com/invite)/((?:[a-zA-Z0-9]){2,32})(?:[\s \S]|)*", re.IGNORECASE)
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
