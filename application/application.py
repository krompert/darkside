import asyncio
import discord

from discord.utils import get
from datetime import datetime, timedelta

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.antispam import AntiSpam

from redbot.core.bot import Red


class Application(commands.Cog):
    """
    Simple application cog, basically.
    **Use `[p]applysetup` first.**
    """

    __author__ = "Darkside"
    __version__ = "1.2.5"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, 5641654654621651651, force_registration=True
        )
        self.antispam = {}
        self.config.register_guild(
            applicant_id=None,
            accepter_id=None,
            channel_id=None,
        )

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def apply(self, ctx: commands.Context):
        """Apply for server transfer."""
        try:
            role_add = get(ctx.guild.roles, id = await self.config.guild(ctx.guild).applicant_id())
        except TypeError:
            role_add = None
        if not role_add:
            role_add = get(ctx.guild.roles, name = "Server Aspirant")
            if not role_add:
                return await ctx.send("Uh oh, the configuration is not correct. Ask the Admins to set it.")
        try:
            channel = get(ctx.guild.text_channels, id = await self.config.guild(ctx.guild).channel_id())
        except TypeError:
            channel = None
        if not channel:
            channel = get(ctx.guild.text_channels, name = "transfers")
            if not channel:
                return await ctx.send("Uh oh, the configuration is not correct. Ask the Admins to set it.")
        if ctx.guild not in self.antispam:
            self.antispam[ctx.guild] = {}
        if ctx.author not in self.antispam[ctx.guild]:
            self.antispam[ctx.guild][ctx.author] = AntiSpam([(timedelta(days=7), 1)])
        if self.antispam[ctx.guild][ctx.author].spammy:
            return await ctx.send("Uh oh, you're doing this way too frequently. Please be patient, Transfer applications can take up to 7 days.")
        if not role_add:
            return await ctx.send(
                "Uh oh. Looks like your Admins haven't added the required role."
            )
        if not channel:
            return await ctx.send(
                "Uh oh. Looks like your Admins haven't added the required channel."
            )
        try:
            await ctx.author.send(
                "Let's start right away! You have maximum of 2 minutes for each question.\nWhat is your current server?"
            )
        except discord.Forbidden:
            return await ctx.send(
                "I don't seem to be able to DM you. Do you have closed DMs?"
            )
        await ctx.send(f"Okay, {ctx.author.mention}, I've sent you a DM.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel

        try:
            server = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("What is your current VIP level?")
        try:
            vip = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("Why have you chosen our server?")
        try:
            why = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("What timezone are you in? (Google is your friend.)")
        try:
            timezone = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("How Many 5 Star heroes do you currently have?")
        try:
            heroes = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("What branch are you, Combat or Mech? And how advance?")
        try:
            branch = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send(
            "What level are your current components?"
        )
        try:
            comps = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        await ctx.author.send("Please add any comments that would help leaders reviwing your application. Further review may take place with Server Leaders.")
        try:
            comments = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        embed = discord.Embed(color=await ctx.embed_colour(), timestamp=datetime.now())
        embed.set_author(name="New application!", icon_url=ctx.author.avatar_url)
        embed.set_footer(
            text=f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        )
        embed.title = (
            f"User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        )
        embed.add_field(name="VIP Level:", value=vip.content, inline=True)
        embed.add_field(name="Why Our Server:", value=why.content, inline=True)
        embed.add_field(name="Timezone:", value=timezone.content, inline=True)
        embed.add_field(name="Current Server:", value=server.content, inline=True)
        embed.add_field(name="Hero's 5 Stars:", value=heroes.content, inline=True)
        embed.add_field(name="Branch/Level:", value=branch.content, inline=True)
        embed.add_field(
            name="Components Level:", value=comps.content, inline=False
        )
        embed.add_field(name="Extra Comments:", value=comments.content, inline=False)

        await channel.send(embed=embed)

        await ctx.author.add_roles(role_add)

        await ctx.author.send(
            "Your application has been sent to the server leaders, Please be patient, applications could take up to 7 days. Thank you!"
        )
        self.antispam[ctx.guild][ctx.author].stamp()

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True, manage_roles=True)
    async def applysetup(self, ctx: commands.Context):
        """Go through the initial setup process."""
        pred = MessagePredicate.yes_or_no(ctx)
        role = MessagePredicate.valid_role(ctx)

        applicant = get(ctx.guild.roles, name="Server Aspirant")
        channel = get(ctx.guild.text_channels, name="transfers")

        await ctx.send(
            "This will create required channel and role. Do you wish to continue? (yes/no)"
        )
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if not pred.result:
            return await ctx.send("Setup cancelled.")
        if not applicant:
            try:
                applicant = await ctx.guild.create_role(
                    name="Server Aspirant", reason="Application cog setup"
                )
            except discord.Forbidden:
                return await ctx.send(
                    "Uh oh. Looks like I don't have permissions to manage roles."
                )
        if not channel:
            await ctx.send(
                "Do you want everyone to see the transfers channel? (yes/no)"
            )
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            if pred.result:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        send_messages=False
                    ),
                    ctx.guild.me: discord.PermissionOverwrite(send_messages=True),
                }
            else:
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    ctx.guild.me: discord.PermissionOverwrite(read_messages=True),
                }
            try:
                channel = await ctx.guild.create_text_channel(
                    "transfers",
                    overwrites=overwrites,
                    reason="Transfers cog setup",
                )
            except discord.Forbidden:
                return await ctx.send(
                    "Uh oh. Looks like I don't have permissions to manage channels."
                )
        await ctx.send(f"What role can accept or reject tranfers?")
        try:
            await self.bot.wait_for("message", timeout=30, check=role)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        accepter = role.result
        await self.config.guild(ctx.guild).applicant_id.set(applicant.id)
        await self.config.guild(ctx.guild).channel_id.set(channel.id)
        await self.config.guild(ctx.guild).accepter_id.set(accepter.id)
        await ctx.send(
            "You have finished the setup! Please, move your new channel to the category you want it in."
        )

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def accept(self, ctx: commands.Context, target: discord.Member):
        """Accept a server transfer aspirant.

        <target> can be a mention or an ID."""
        try:
            accepter = get(ctx.guild.roles, id = await self.config.guild(ctx.guild).accepter_id())
        except TypeError:
            accepter = None
        if not accepter:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("Uh oh, you cannot use this command.")
        else:
            if accepter not in ctx.author.roles:
                return await ctx.send("Uh oh, you cannot use this command.")
        try:
            applicant = get(ctx.guild.roles, id = await self.config.guild(ctx.guild).applicant_id())
        except TypeError:
            applicant = None
        if not applicant:
            applicant = get(ctx.guild.roles, name="Server Aspirant")
            if not applicant:
                return await ctx.send("Uh oh, the configuration is not correct. Ask the Admins to set it.")
        role = MessagePredicate.valid_role(ctx)
        if applicant in target.roles:
            await ctx.send(f"What role do you want to accept {target.name} as?")
            try:
                await self.bot.wait_for("message", timeout=30, check=role)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            role_add = role.result
            try:
                await target.add_roles(role_add)
            except discord.Forbidden:
                return await ctx.send("Uh oh, I cannot give them the role. It might be above all of my roles.")
            await target.remove_roles(applicant)
            await ctx.send(f"Accepted {target.mention} as {role_add}.")
            await target.send(
                f"You have been accepted as {role_add} in {ctx.guild.name}."
            )
        else:
            await ctx.send(
                f"Uh oh. Looks like {target.mention} hasn't applied for anything."
            )

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def deny(self, ctx: commands.Context, target: discord.Member):
        """Deny a server transfer aspirant.

        <target> can be a mention or an ID"""
        try:
            accepter = get(ctx.guild.roles, id = await self.config.guild(ctx.guild).accepter_id())
        except TypeError:
            accepter = None
        if not accepter:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("Uh oh, you cannot use this command.")
        else:
            if accepter not in ctx.author.roles:
                return await ctx.send("Uh oh, you cannot use this command.")
        try:
            applicant = get(ctx.guild.roles, id = await self.config.guild(ctx.guild).applicant_id())
        except TypeError:
            applicant = None
        if not applicant:
            applicant = get(ctx.guild.roles, name="Server Aspirant")
            if not applicant:
                return await ctx.send("Uh oh, the configuration is not correct. Ask the Admins to set it.")
        if applicant in target.roles:
            await ctx.send("Would you like to specify a reason? (yes/no)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            if pred.result:
                await ctx.send("Please, specify your reason now.")

                def check(m):
                    return m.author == ctx.author

                try:
                    reason = await self.bot.wait_for(
                        "message", timeout=120, check=check
                    )
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                await target.send(
                    f"Your transfer in {ctx.guild.name} has been denied.\n*Reason:* {reason.content}"
                )
            else:
                await target.send(
                    f"Your transfer in {ctx.guild.name} has been denied."
                )
            await target.remove_roles(applicant)
            await ctx.send(f"Denied {target.mention}'s transfer.")
        else:
            await ctx.send(
                f"Uh oh. Looks like {target.mention} hasn't applied for anything."
            )
