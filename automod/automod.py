import discord
from redbot.core import commands, checks, Config
from redbot.core.bot import Red
import re
import datetime
import asyncio

class AutoMod(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=439643784643943, force_registration=True)

        default_guild = {
            "log_channel": None,
            "whitelisted_roles": [],
            "whitelisted_members": [],
            "blacklisted_words": [],
            "links": False,
            "invites": False,
            "duplicates": False,
            "fastmessage": False,
            "images": False,
            "spoliers": False,
            "mutetime": 180,
            "maxviolations": 3,
            "mute_role": None,
            "imagemode": [],
            "muted_users": {},
            "invite_channel": None,
            "kicked_users": {},
            "oneword": [],
        }
        default_member = {
            "times_violated": 0,
            "muted": False,
            }
        self.data.register_member(**default_member)
        self.data.register_guild(**default_guild)
        self.spam = {}
        self.duplicates = {}
        self.images_spam = {}
        self.amount_of_messages = 5
        self.amount_of_time = 5
        self.warning_timeout = 180

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @commands.group(name="automod")
    async def automod_(self, ctx):
        """Setup auto moderation on this server"""
        if ctx.invoked_subcommand is None:
            pass

    @automod_.command(name="resetuser")
    async def _resetuser(self, ctx, *, user: discord.Member):
        """Reset violations for a user."""
        await self.data.member(user).times_violated.set(0)
        await self.data.member(user).muted.set(False)
        await ctx.send(f"Violations for **{user.name}** has been reset!")

    @automod_.command(name="logchannel")
    async def _logchannel(self, ctx, *, channel: discord.TextChannel):
        """Setup a moderation log channel."""
        await self.data.guild(ctx.guild).log_channel.set(channel.id)
        await ctx.send(f"Set the auto moderation log channel to {channel.mention}.")

    @automod_.command(name="invitechannel")
    async def _invitechannel(self, ctx, *, channel: discord.TextChannel):
        """Set a channel, for which bot will create invites."""
        await self.data.guild(ctx.guild).invite_channel.set(channel.id)
        await ctx.send(f"Set the invite channel to {channel.mention}.")

    @automod_.command(name="whitelistrole")
    async def _whitelistrole(self, ctx, *, role: discord.Role):
        """Whitelist a role."""
        roles = await self.data.guild(ctx.guild).whitelisted_roles()
        if role.id not in roles:
            roles.append(role.id)
            await self.data.guild(ctx.guild).whitelisted_roles.set(roles)
            return await ctx.send(f"{role.name} has been whitelisted.")
        elif role.id in roles:
            roles.remove(role.id)
            await self.data.guild(ctx.guild).whitelisted_roles.set(roles)
            return await ctx.send(f"{role.name} has been removed from the whitelist.")


    @automod_.command(name="whitelistuser")
    async def _whitelistuser(self, ctx, *, member: discord.Member):
        """Whitelist a user."""
        members = await self.data.guild(ctx.guild).whitelisted_members()
        if member.id not in members:
            members.append(member.id)

            await self.data.guild(ctx.guild).whitelisted_members.set(members)
            return await ctx.send(f"{member.name} has been whitelisted.")
        elif member.id in members:
            members.remove(member.id)
            await self.data.guild(ctx.guild).whitelisted_members.set(members)
            return await ctx.send(f"{member.name} has been removed from the whitelist.")

    @automod_.command(name="word")
    async def _words(self, ctx, *, word: str):
        """Blacklist a word."""
        blacklisted_words = await self.data.guild(ctx.guild).blacklisted_words()
        if word.lower() not in blacklisted_words:
            blacklisted_words.append(word.lower())

            await self.data.guild(ctx.guild).blacklisted_words.set(blacklisted_words)
            return await ctx.send(f"{word} has been blacklisted.")

        await ctx.send(f"{word} is already blacklisted.")

    @automod_.command(name="removeword")
    async def _removeword(self, ctx, *, word: str):
        """Remove a blacklisted word."""
        blacklisted_words = await self.data.guild(ctx.guild).blacklisted_words()
        if word.lower() in blacklisted_words:
            blacklisted_words.remove(word.lower())

            await self.data.guild(ctx.guild).blacklisted_words.set(blacklisted_words)
            return await ctx.send(f"{word} has been removed from the blacklist.")
        elif word.lower() not in blacklisted_words:
            await ctx.send(f"{word} is not blacklisted.")

    @automod_.command(name="listwords")
    async def _listwords(self, ctx):
        """List of blacklisted words."""
        blacklisted_words = await self.data.guild(ctx.guild).blacklisted_words()
        if not blacklisted_words:
            return await ctx.send("There are no blacklisted words on this server!")

        await ctx.send(f"Below are all the blacklisted words.\n\n {', '.join(blacklisted_words)}")

    @automod_.command(name="oneword")
    async def _oneword(self, ctx, channel: discord.TextChannel):
        """Enable or disable one words."""
        oneword = await self.data.guild(ctx.guild).oneword()
        try:
            if isinstance(oneword, boolean):
                await self.data.guild(ctx.guild).oneword.set([])
        except:
            await self.data.guild(ctx.guild).oneword.set([])

        oneword = await self.data.guild(ctx.guild).oneword()
        
        if channel.id in oneword:
            oneword.remove(channel.id)
            await self.data.guild(ctx.guild).oneword.set(oneword)
            await ctx.send(f"{channel.mention} is no longer restricted to oneword.")
        elif channel.id not in oneword:
            oneword.append(channel.id)
            await self.data.guild(ctx.guild).oneword.set(oneword)
            await ctx.send(f"{channel.mention} is now restricted to oneword.")

    @automod_.command(name="links")
    async def _links(self, ctx):
        """Disable links."""
        link = await self.data.guild(ctx.guild).links()

        if link == True:
            await self.data.guild(ctx.guild).links.set(False)
            await ctx.send("Users can now send links.")
        elif link == False:
            await self.data.guild(ctx.guild).links.set(True)
            await ctx.send("Users will not be allowed to send links.")


    @automod_.command(name="imagemode")
    async def _imagemode(self, ctx, channel: discord.TextChannel):
        """Toggle image mode, to allowe users to send images only."""
        imagemode = await self.data.guild(ctx.guild).imagemode()

        if channel.id in imagemode:
            imagemode.remove(channel.id)
            await self.data.guild(ctx.guild).imagemode.set(imagemode)
            await ctx.send(f"{channel.mention} is no longer restricted to images only.")
        elif channel.id not in imagemode:
            imagemode.append(channel.id)
            await self.data.guild(ctx.guild).imagemode.set(imagemode)
            await ctx.send(f"{channel.mention} is now restricted to images only.")

    @automod_.command(name="images")
    async def _images(self, ctx):
        """Disable spam of images & gifs."""
        images = await self.data.guild(ctx.guild).images()

        if images == True:
            await self.data.guild(ctx.guild).images.set(False)
            await ctx.send("Users can now send images.")
        elif images == False:
            await self.data.guild(ctx.guild).images.set(True)
            await ctx.send("Users will not be allowed to send images.")

    @automod_.command(name="invites")
    async def _invites(self, ctx):
        """Disable invite links."""
        invites = await self.data.guild(ctx.guild).invites()

        if invites == True:
            await self.data.guild(ctx.guild).invites.set(False)
            await ctx.send("Users can now send discord invites.")
        elif invites == False:
            await self.data.guild(ctx.guild).invites.set(True)
            await ctx.send("Users will not be allowed to send links.")

    @automod_.command(name="duplicates")
    async def _duplicates(self, ctx):
        """Disable mass duplicates."""
        duplicates = await self.data.guild(ctx.guild).duplicates()

        if duplicates == True:
            await self.data.guild(ctx.guild).duplicates.set(False)
            await ctx.send("Users are allowed to send dublicate texts.")
        elif duplicates == False:
            await self.data.guild(ctx.guild).duplicates.set(True)
            await ctx.send("Users will not be allowed to send dublicate texts.")

    @automod_.command(name="fastmessage")
    async def _fastmessage(self, ctx):
        """Enable antispam."""
        fastmessage = await self.data.guild(ctx.guild).fastmessage()

        if fastmessage == True:
            await self.data.guild(ctx.guild).fastmessage.set(False)
            await ctx.send("Users are now allowed to spam messages.")
        elif fastmessage == False:
            await self.data.guild(ctx.guild).fastmessage.set(True)
            await ctx.send("Users will not be allowed to spam messages.")

    @automod_.command(name="nospoiler")
    async def _nospoiler(self, ctx):
        """Disable messages marked as spolier."""
        spoliers = await self.data.guild(ctx.guild).spoliers()

        if spoliers == True:
            await self.data.guild(ctx.guild).spoliers.set(False)
            await ctx.send("Users are now allowed to send messages marked as spoilers.")
        elif spoliers == False:
            await self.data.guild(ctx.guild).spoliers.set(True)
            await ctx.send("Users will not be allowed to send messages marked as spoliers.")

    @automod_.command(name="mutetime")
    async def _mutetime(self, ctx, *, time: str):
        """Define the time of the mute."""
        try:
            if isinstance(int(time), int):
                time = int(time)
            else:
                time = None
        except:
            time = None
            pass

        if time:
            await self.data.guild(ctx.guild).mutetime.set(int(time*60))
            await ctx.send(f"Mute time has been set to {time} minutes.")
        else:
            return await ctx.send("Invalid time provided, make sure it is just numbers.")

    @automod_.command(name="violations")
    async def _violations(self, ctx, *, violations: int):
        """Define the total violations before user gets warned."""
        await self.data.guild(ctx.guild).maxviolations.set(violations)
        await ctx.send(f"Max violations have been set to {violations} times.")

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        guild = message.guild
        reason = None
        check = None

        if not guild:
            return

        if message.author.bot:
            return

        if await self.whitelisted_check(message.author, message.channel, message.guild):
            return

        await self.check_imagemode(message)

        if await self.data.guild(guild).images():
            check = await self.images_gifs_check(message)
            if check:
                reason = "Anti Images Spam"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).spoliers():
            check = await self.spoilers_check(message)
            if check:
                reason = "Anti-Spoilers"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).blacklisted_words():
            check = await self.check_blacklisted_word(message)
            if check:
                reason = "Blacklisted words"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).invites():
            check = await self.invites_check(message)
            if check:
                reason = "Anti-Invites"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).links():
            check = await self.links_check(message)
            if check:
                reason = "Anti-Links"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).fastmessage():
            check = await self.spam_detection(message)
            if check:
                reason = "Anti-Spam"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

        if await self.data.guild(guild).duplicates():
            check = await self.dublicate_text_check(message)
            if check:
                reason = "Anti-duplicates"
                await self.trigger_punish(message, reason)
                return await self.manage_message(message)

    async def trigger_punish(self, message, reason):
        times_violated = await self.data.member(message.author).times_violated()
        await self.data.member(message.author).times_violated.set(times_violated+1)
        await self.punish_system(user=message.author, reason=reason)

    async def manage_message(self, message):
        if not message.guild:
            return

        if message.author.bot:
            return

        try:
            await message.delete()
        except:
            pass


    async def spam_detection(self, message):
        author = message.author
        guild = message.guild
        author = guild.get_member(author.id)
        if not author:
            return

        created = message.created_at.timestamp()
        channel = message.channel
        maxviolations = await self.data.guild(guild).maxviolations()
        times_violated = await self.data.member(author).times_violated()
        if author.id == self.bot.user.id:
            return
        if str(guild.id) not in self.spam:
            self.spam[str(guild.id)] = {}
            self.spam[str(guild.id)][str(self.bot.user.id)] = 0
        if str(author.id) not in self.spam[str(guild.id)]:
            self.spam[str(guild.id)][str(author.id)] = []
        self.spam[str(guild.id)][str(author.id)].append(created)
        i = 0
        for m in self.spam[str(guild.id)][str(author.id)]:
            if m > created - self.amount_of_time:
                i += 1
            else:
                try:
                    self.spam[str(guild.id)][str(author.id)].remove(m)
                except:
                    pass
        if i >= self.amount_of_messages:
            self.spam[str(guild.id)][str(author.id)] = []

            if maxviolations - await self.data.member(author).times_violated() <= 1:
                try:
                    await channel.purge(limit=5, check=lambda m: m.author == author)
                except:
                    pass
                return True

            return True

        return False

    async def punish_system(self, user, reason: str):
        maxviolations = await self.data.guild(user.guild).maxviolations()
        log_channel = await self.data.guild(user.guild).log_channel()
        times_violated = await self.data.member(user).times_violated()
        if_muted = await self.data.member(user).muted()
        user = user.guild.get_member(user.id)
        if not user:
            return

        if log_channel:
            log_channel = user.guild.get_channel(int(log_channel))

        if if_muted:
            if user.guild.owner == user:
                if log_channel:
                    try:
                        await log_channel.send(f"Failed to kick {user.mention} - ``{user.id}`` for triggering **{reason}** system.")
                    except discord.HTTPException:
                        pass
                    except discord.Forbidden:
                        pass
                await self.data.member(user).times_violated.set(0)
                await self.data.member(user).muted.set(False)
                return

            if user.top_role.position >= user.guild.get_member(self.bot.user.id).top_role.position:
                if log_channel:
                    try:
                        await log_channel.send(f"Failed to kick {user.mention} - ``{user.id}`` for triggering **{reason}** system.")
                    except discord.HTTPException:
                        pass
                    except discord.Forbidden:
                        pass
                await self.data.member(user).times_violated.set(0)
                await self.data.member(user).muted.set(False)
                return

            invite_channel = await self.data.guild(user.guild).invite_channel()
            invite = None
            if invite_channel:
                try:
                    invite_channel =user.guild.get_channel(int(invite_channel))
                except:
                    pass

                if invite_channel:
                    invite = await invite_channel.create_invite(max_age=0, max_uses=1, unique=True, reason="Auto-Mod")

            try:
                if invite:
                    await user.send(f"You have been kicked from {user.guild.name} due to {reason}.\n\n You can join back after 10 minutes using the following invite: {invite} ")
                else:
                    await user.send(f"You have been kicked from {user.guild.name} due to {reason}.")

                users_kicked_invites = await self.data.guild(user.guild).kicked_users()
                if str(user.id) not in users_kicked_invites:
                    await self.data.guild(user.guild).kicked_users.set_raw(user.id, value=datetime.datetime.utcnow().timestamp())

            except discord.HTTPException:
                pass
            except discord.Forbidden:
                pass

            try:
                await user.kick(reason="Auto Mod.")
            except discord.HTTPException:
                pass
            except discord.Forbidden:
                pass

            if log_channel:
                try:
                    if invite:
                        await log_channel.send(f"{user.mention} - ``{user.id}`` has been kicked from the server for triggering **{reason}** system.\n\n User was sent a temporary invite link to rejoin: {invite}")
                    else:
                        await log_channel.send(f"{user.mention} - ``{user.id}`` has been kicked from the server for triggering **{reason}** system.")
                except discord.HTTPException:
                    pass
                except discord.Forbidden:
                    pass

            await self.data.member(user).times_violated.set(0)
            await self.data.member(user).muted.set(False)
            return

        elif times_violated >= maxviolations:
            if log_channel:
                await self.mute_user(user=user, reason=reason, logchannel=log_channel)
            else:
                await self.mute_user(user=user, reason=reason)
        elif times_violated < maxviolations:

            try:
                await user.send(f"You have been warned for triggering **{reason}** system.")
            except:
                pass

            if log_channel:
                try:
                    await log_channel.send(f"{user.mention} - ``{user.id}`` Has been warned for triggering **{reason}** system.")
                except:
                    pass

    async def unmute_user_loop(self):
        while True:
            data = await self.data.all_guilds()
            for server_id in data:
                server = self.bot.get_guild(server_id)
                if server:
                    server_data = await self.data.guild(server).muted_users()
                    if server_data:
                        for user_id in server_data:
                            mute_time = datetime.datetime.utcnow().timestamp() - (await self.data.guild(server).muted_users.get_raw(user_id, "time"))
                            if mute_time > int(data[server.id]["mutetime"]):
                                await self.unmute_user(server, user_id)
            await asyncio.sleep(30)

    async def unmute_user(self, server, user_id):
        user = server.get_member(int(user_id))
        if not user:
            return

        mute_role = await self.data.guild(server).mute_role()
        if mute_role:
            mute_role = server.get_role(int(mute_role))

        if not mute_role:
            return

        log_channel = await self.data.guild(user.guild).log_channel()

        if log_channel:
            log_channel = user.guild.get_channel(int(log_channel))

        try:
            await user.remove_roles(mute_role)
        except:
            pass

        try:
            if log_channel:
                await log_channel.send(f"{user.mention}, has been unmuted as they have served their time for the mute!")
        except:
            pass

        try:
            await user.send(f"You were unmuted on **{server}** as you have served your time for the mute.")
        except:
            pass

        await self.data.guild(server).muted_users.clear_raw(user.id)

    async def mute_user(self, user, reason: str, logchannel: None):
        guild = user.guild
        if not guild:
            return

        mute_role = await self.data.guild(guild).mute_role()

        try:
            if not mute_role:
                mute_role = await self._create_mute_role(guild)
                await user.add_roles(mute_role)

            elif mute_role:
                mute_role = guild.get_role(int(mute_role))
                if not mute_role:
                    mute_role = await self._create_mute_role(guild)

                await user.add_roles(mute_role)

            await user.send(f"You have been muted for triggering the {reason} system.")

            await logchannel.send(f"{user.mention} - ``{user.id}`` has been muted for triggering **{reason}** system.")
        except discord.HTTPException:
            pass
        except discord.Forbidden:
            pass

        await self.data.guild(guild).muted_users.set_raw(user.id, "time", value=datetime.datetime.utcnow().timestamp())
        await self.data.member(user).muted.set(True)

    async def _create_mute_role(self, guild):
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        perms = discord.PermissionOverwrite()
        perms.speak = False
        mute_role = await guild.create_role(name="AutoMod - Muted")
        await self.data.guild(guild).mute_role.set(mute_role.id)
        for channels in guild.text_channels:
            await channels.set_permissions(mute_role, overwrite=overwrite)
        for channels in guild.voice_channels:
            await channels.set_permissions(mute_role, overwrite=perms)

        return mute_role

    async def whitelisted_check(self, user, channel, guild):
        members = await self.data.guild(guild).whitelisted_members()
        roles = await self.data.guild(guild).whitelisted_roles()
        user = guild.get_member(int(user.id))

        if not user:
            return

        if user.id in members:
            return True

        for role in user.roles:
            if role.id in roles:
                return True

        return False

    async def dublicate_text_check(self, message):
        if not message.guild:
            return

        if str(message.author.id) not in self.duplicates:
            self.duplicates[str(message.author.id)] = {"count": 1, "msg": message.content}

        if message.content == self.duplicates[str(message.author.id)]["msg"]:
            if self.duplicates[str(message.author.id)]["count"] <= 3:
                self.duplicates[str(message.author.id)]["count"] += 1
        elif message.content != self.duplicates[str(message.author.id)]["msg"]:
            self.duplicates[str(message.author.id)]["msgs_to_delete"] = []
            self.duplicates[str(message.author.id)]["count"] = 1
            self.duplicates[str(message.author.id)]["msg"] = message.content

        if self.duplicates[str(message.author.id)]["count"] > 3:
            self.duplicates[str(message.author.id)]["count"] = 0
            self.duplicates[str(message.author.id)]["msg"] = None

            try:
                await message.channel.purge(limit=4, check=lambda m: m.author == message.author)
            except:
                pass

            return True

        return False


    async def images_gifs_check(self, message):
        images = await self.data.guild(message.guild).images()
        if images:
            self.formats = [".jpg", ".jpeg", ".png"]
            if message.attachments:
                for format in self.formats:
                    if message.attachments[0].filename.endswith(format):
                        if str(message.author.id) not in self.images_spam:
                            self.images_spam[str(message.author.id)] = 1
                        elif str(message.author.id) in self.images_spam:
                            self.images_spam[str(message.author.id)] += 1

                if self.images_spam[str(message.author.id)] > 3:
                    try:
                        await message.channel.purge(limit=4, check=lambda m: m.author == message.author)
                    except:
                        pass
                    self.images_spam[str(message.author.id)] = 0
                    return True

        return False

    async def check_imagemode(self, message):
        if not message.guild:
            return

        imagemode = await self.data.guild(message.guild).imagemode()
        image_formats = [".jpg", ".jpeg", ".png"]

        if await self.data.guild(message.guild).oneword():
            if message.channel.id in (await self.data.guild(message.guild).oneword()):
                word = message.content
                if word:
                    if word.lower() not in [".donate","donate",".agree"]:
                        try:
                            await message.author.send("You can only send one word in this channel, **.donate**")
                        except:
                            pass
                        try:
                            await message.delete()
                        except:
                            pass
                        return

        if imagemode:
            if message.channel.id not in imagemode:
                return

            if not message.attachments:
                try:
                    await message.delete()
                except:
                    pass

                try:
                    await message.author.send("You can only attach images in this channel.")
                except:
                    pass

                return

            if message.attachments:
                for format in image_formats:
                    if message.attachments[0].filename.endswith(format):
                        return

                try:
                    await message.delete()
                except:
                    pass
                try:
                    await message.author.send("You can only attach images in this channel.")
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        users_kicked_invites = await self.data.guild(member.guild).kicked_users()
        if str(member.id) in users_kicked_invites:
            if datetime.datetime.utcnow().timestamp() - users_kicked_invites[str(member.id)] >= 600:
                await self.data.guild(member.guild).kicked_users.clear_raw(member.id)
            elif datetime.datetime.utcnow().timestamp() - users_kicked_invites[str(member.id)] < 600:
                try:
                    invite_channel = await self.data.guild(member.guild).invite_channel()
                    invite = None
                    if invite_channel:
                        try:
                            invite_channel =member.guild.get_channel(int(invite_channel))
                        except:
                            pass

                        if invite_channel:
                            invite = await invite_channel.create_invite(max_age=0, max_uses=1, unique=True, reason="Auto-Mod")
                    if invite:
                        await member.send(f"You can only join back after 10 minutes of the initial kick time.\n\n New Invite Link: {invite}")
                    else:
                        await member.send(f"You can only join back after 10 minutes of the initial kick time.\n\n Please ask a mod for a valid invite link.")
                except:
                    pass

                try:
                    await member.kick()
                except:
                    pass



    async def spoilers_check(self, message):
        spoliers = await self.data.guild(message.guild).spoliers()
        regex = "(?i)(?:^|\W)\|\|.+\|\|(?:$|\W)"
        if spoliers:
            if re.search(regex, message.content):
                return True

        return False

    async def links_check(self, message):
        link = await self.data.guild(message.guild).links()
        regex = ".*(https?|ftp|file)://[-a-zA-Z0-9+&@#/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#/%=~_|].*"
        if link:
            if re.search(regex, message.content):
                return True

        return False

    async def invites_check(self, message):
        invites = await self.data.guild(message.guild).invites()
        regex = "discord(?:(?:app)?.com/invite|.gg(?:/invite)?)/?[a-zA-Z0-9]+"
        if invites:
            if re.search(regex, message.content):
                return True

        return False

    async def check_blacklisted_word(self, message):
        blacklisted_words = await self.data.guild(message.guild).blacklisted_words()
        list_of_content = message.content.lower().strip(" ")
        for word in blacklisted_words:
            if word in list_of_content:
                return True

        return False
