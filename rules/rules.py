import discord
from redbot.core import commands, checks, Config
from redbot.core.bot import Red
import re
import math

emoji_regex = re.compile("<(?:a|):.+:([0-9]+)>")

class Rules(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=343463093253252, force_registration=True)
        default_guild = {
            "roles": {},
            "channel": None,
            "nsfw": {},
            "nonnsfw": {},
        }
        self.data.register_guild(**default_guild)

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group()
    async def rules(self, ctx):
        """Setup roles according to their reactions for RULES cog."""
        if ctx.invoked_subcommand is None:
            pass

    @rules.command(name="add")
    async def _add(self, ctx, role: discord.Role, emoji: str):
        "Link a role to the emoji."
        emote = emoji_regex.match(emoji)
        if emote:
            emote = int(emote.group(1))
        else:
            return await ctx.send("Emote not found!")
        emote = self.bot.get_emoji(emote)
        if emote:
            await self.data.guild(ctx.guild).roles.set_raw(emote.id,  value={"role_id": role.id})
            await ctx.send(f"Successfully linked **{role.name}** role to **{emote}** emoji.")

        else:
            await ctx.send("Unable to find the emoji.")

    @rules.command(name="remove")
    async def _remove(self, ctx, emoji: str):
        "Remove linked roles from an emoji."
        emote = self.bot.get_emoji(int(emoji_regex.match(emoji).group(1)))
        emojis_db = await self.data.guild(ctx.guild).roles()
        if str(emote.id) in emojis_db:
            await self.data.guild(ctx.guild).roles.clear_raw(emote.id)
            await ctx.send(f"Successfully unlinked roles from **{emote}** emoji.")
        elif str(emoji.id) not in emojis_db:
            await ctx.send(f"No roles are linked to **{emote}** emoji.")

    @rules.command(name="nsfw")
    async def _nsfw(self, ctx, role: discord.Role, emoji: str):
        "Link a role for the over 18+ content."
        emote = self.bot.get_emoji(int(emoji_regex.match(emoji).group(1)))
        if emote:
            await self.data.guild(ctx.guild).nsfw.set_raw(emote.id,  value={"role_id": role.id})
            await ctx.send(f"Successfully linked **{role.name}** role to **{emote}** emoji.")

        else:
            await ctx.send("Unable to find the emoji.")

    @rules.command(name="nonnsfw")
    async def _nonnsfw(self, ctx, role: discord.Role, emoji: str):
        "Link a role for the not over 18+ content."
        emote = self.bot.get_emoji(int(emoji_regex.match(emoji).group(1)))
        if emote:
            await self.data.guild(ctx.guild).nonnsfw.set_raw(emote.id,  value={"role_id": role.id})
            await ctx.send(f"Successfully linked **{role.name}** role to **{emote}** emoji.")

        else:
            await ctx.send("Unable to find the emoji.")


    @rules.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel):
        """Set a logging text channel."""
        await self.data.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Successfully set the log channel to {channel.mention}.")

    @commands.command(name="agree")
    async def _agree(self, ctx):
        "Get a role."
        msg = f"""{ctx.author.mention}
                Please react with an emoji below to gain access to the server and proper roles. Ask if you need any assistance.

                 @Over18 will give access to NSFW channels, if you are under 18, please refer yourself from reacting to this role!\n\n"""
        emojis_db = await self.data.guild(ctx.guild).roles()
        nsfw_roles = await self.data.guild(ctx.guild).nsfw()
        nonnsfw_roles = await self.data.guild(ctx.guild).nonnsfw()
        all_reactions = []
        reactions = []
        msgs_ids = []
        msgs_count = 0
        message_obj = None
        if emojis_db:
            for emoji in emojis_db:
                if msgs_count == 10:
                    embed=discord.Embed(description=msg)
                    message_obj = await ctx.send(embed=embed)
                    msgs_ids.append(message_obj.id)
                    await self.add_all_reactions(message_obj, reactions)
                    msg = ""
                    reactions = []
                    msgs_count = 0

                emoji_obj = self.bot.get_emoji(int(emoji))
                if emoji_obj:
                    role = ctx.guild.get_role(emojis_db[emoji]["role_id"])
                    if role:
                        msg += f"**-** React with {emoji_obj} to get the {role.mention} role.\n"
                        reactions.append(emoji_obj)
                        all_reactions.append(emoji_obj)
                        msgs_count += 1

            for emoji in nsfw_roles:
                if msgs_count == 10:
                    embed=discord.Embed(description=msg)
                    message_obj = await ctx.send(embed=embed)
                    msgs_ids.append(message_obj.id)
                    await self.add_all_reactions(message_obj, reactions)
                    msg = ""
                    reactions = []
                    msgs_count = 0

                emoji_obj = self.bot.get_emoji(int(emoji))
                if emoji_obj:
                    role = ctx.guild.get_role(nsfw_roles[emoji]["role_id"])
                    if role:
                        msg += f"**-** React with {emoji_obj} to get the {role.mention} role, allows you access to 18+ content.\n"
                        reactions.append(emoji_obj)
                        all_reactions.append(emoji_obj)
                        msgs_count += 1


            for emoji in nonnsfw_roles:
                if msgs_count == 10:
                    embed=discord.Embed(description=msg)
                    message_obj = await ctx.send(embed=embed)
                    msgs_ids.append(message_obj.id)
                    await self.add_all_reactions(message_obj, reactions)
                    msg = ""
                    reactions = []
                    msgs_count = 0

                emoji_obj = self.bot.get_emoji(int(emoji))
                if emoji_obj:
                    role = ctx.guild.get_role(nonnsfw_roles[emoji]["role_id"])
                    if role:
                        msg += f"**-** React with {emoji_obj} to get the {role.mention} role, if you do not wish to have access to 18+ content.\n"
                        reactions.append(emoji_obj)
                        all_reactions.append(emoji_obj)
                        msgs_count += 1

            if msgs_count <= 10:
                embed=discord.Embed(description=msg)
                message_obj = await ctx.send(embed=embed)
                msgs_ids.append(message_obj.id)
                await self.add_all_reactions(message_obj, reactions)
                msg = ""
                reactions = []
                msgs_count = 0

        def reactioncheck(reaction, user):
            if user != self.bot.user:
                if user == ctx.author:
                    if reaction.message.channel == ctx.channel:
                        if reaction.emoji in all_reactions:
                            if reaction.message.id in msgs_ids:
                                return True

        times_reacted = 0
        role_rewarded_bool = False
        not_nsfw_rewarded = False
        LOG_CHANNEL = await self.data.guild(ctx.guild).channel()
        if LOG_CHANNEL:
            LOG_CHANNEL = ctx.guild.get_channel(int(LOG_CHANNEL))

        while times_reacted < 2:
            try:
                reaction, author = await self.bot.wait_for("reaction_add", timeout=180, check=reactioncheck)
            except:
                try:
                    await ctx.channel.purge(check=lambda m: not m.pinned)
                except:
                    pass

                return

            if reaction.emoji in all_reactions:
                if str(reaction.emoji.id) in emojis_db:
                    if not role_rewarded_bool:
                        role = ctx.guild.get_role(emojis_db[str(reaction.emoji.id)]["role_id"])
                        if role:
                            try:
                                await ctx.author.add_roles(role)
                                role_rewarded_bool = True
                                times_reacted += 1

                                await ctx.send(f"Gave you the **{role.name}** role.")
                                if LOG_CHANNEL:
                                    await LOG_CHANNEL.send(f"**{ctx.author.mention}** was given the **{role.name}** role in.")

                            except:
                                await ctx.send("Couldn't reward the role!")
                    else:
                        await ctx.send("You can't react again for the same category.")
                else:
                    if str(reaction.emoji.id) in nsfw_roles:
                        if not not_nsfw_rewarded:
                            role = ctx.guild.get_role(nsfw_roles[str(reaction.emoji.id)]["role_id"])
                            if role:
                                try:
                                    await ctx.author.add_roles(role)
                                    not_nsfw_rewarded = True
                                    times_reacted += 1

                                    await ctx.send(f"Gave you the **{role.name}** role.")
                                    if LOG_CHANNEL:
                                        await LOG_CHANNEL.send(f"**{ctx.author.mention}** was given the **{role.name}** role in.")

                                except:
                                    await ctx.send("Couldn't reward the role!")
                        else:
                            await ctx.send("You can't react again to the same category.")
                    elif str(reaction.emoji.id) in nonnsfw_roles:
                        if not not_nsfw_rewarded:
                            role = ctx.guild.get_role(nonnsfw_roles[str(reaction.emoji.id)]["role_id"])
                            if role:
                                try:
                                    await ctx.author.add_roles(role)
                                    not_nsfw_rewarded = True
                                    times_reacted += 1

                                    await ctx.send(f"Gave you the **{role.name}** role.")
                                    if LOG_CHANNEL:
                                        await LOG_CHANNEL.send(f"**{ctx.author.mention}** was given the **{role.name}** role in.")

                                except:
                                    await ctx.send("Couldn't reward the role!")
                        else:
                            await ctx.send("You can't react again to the same category.")

        try:
            await ctx.channel.purge(check=lambda m: not m.pinned)
        except:
            pass


    async def add_all_reactions(self, msg, reactions):
        for reaction in reactions:
            try:
                await msg.add_reaction(reaction)
            except:
                pass
