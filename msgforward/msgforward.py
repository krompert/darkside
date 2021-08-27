import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red

class MsgForward(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=898464565449, force_registration=True)
        default_guild = {'channels':{}}
        self.data.register_guild(**default_guild)

    @checks.admin_or_permissions(administrator=True)
    @commands.group()
    async def ch(self, ctx):
        """Setup message forwarding."""
        pass

    @ch.command(name="allchannels")
    async def _allchannels(self, ctx, serverID: int):
        """View a list of the text channels on the provided server."""
        guild = self.bot.get_guild(serverID)
        if not guild:
            return await ctx.send("No server found with the similiar ID.")
        msg = ""
        for channel in guild.text_channels:
            msg += f"{channel.name} - `{channel.id}`,     \n"
        embed=discord.Embed(description=msg, title="Text Channels")
        await ctx.send(embed=embed)
        

    @ch.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel, targetChannelId: int):
        """Link channel A with channel B."""
        targetChannelId = self.bot.get_channel(targetChannelId)
        if not targetChannelId:
            return await ctx.send("Invalid targetChannelId provided!")
        await self.data.guild(ctx.guild).channels.set_raw(channel.id, targetChannelId.id, value={"toggle": True, 'guildId':targetChannelId.guild.id})
        await ctx.send(f"Messages sent in {channel.mention} will now be forwarded to {targetChannelId.mention}.")
        
    @ch.command(name='delete')
    async def _delete(self, ctx, channel: discord.TextChannel, targetChannelId: int=None):
        """Remove a channel from the list of forwarded channels.
        
        Example:
            - [p]ch delete #channel - Deletes all the links for a channel.
            - [p]ch delete #channel targetChannelId - Deletes the specific channel link."""
        data = await self.data.guild(ctx.guild).channels()

        if str(channel.id) not in data:
            return await ctx.send(f"This channel wasn't found in the data, make sure to provid valid channels.")

        if not targetChannelId:
            await self.data.guild(ctx.guild).channels.clear_raw(str(channel.id))
            return await ctx.send(f"Deleted all the links for {channel.mention}.")

        data = await self.data.guild(ctx.guild).channels.get_raw(channel.id)
        if data and str(targetChannelId) in data:
            await self.data.guild(ctx.guild).channels.clear_raw(str(channel.id), str(targetChannelId))
            await ctx.send(f"Forward link for {channel.mention} was deleted.")
        
        else:
            await ctx.send(f"No link was found for the targetChannel and the {channel.mention}.")

    @ch.command(name='toggle')
    async def _toggle(self, ctx, channel: discord.TextChannel, targetChannelId: int):
        """Toggle message forwarding for a specific channel links."""
        data = await self.data.guild(ctx.guild).channels()

        if str(channel.id) not in data:
            return await ctx.send(f"This channel wasn't found in the data, make sure to provid valid channels.")

        data = await self.data.guild(ctx.guild).channels.get_raw(channel.id)
        targetChannel = self.bot.get_channel(targetChannelId)

        if not targetChannel:
            return await ctx.send("Invalid targetChannelId provided!")

        if data and str(targetChannelId) in data:
            toggleValue = True if data[str(targetChannelId)]['toggle'] == False else False
            await self.data.guild(ctx.guild).channels.set_raw(str(channel.id), str(targetChannelId), 'toggle', value=toggleValue)
            await ctx.send(f"{'Enabled' if toggleValue else 'Disabled'} the message forwarding from {channel.mention} to {targetChannel.mention}.")
        else:
            await ctx.send(f"No link was found for the targetChannel and the {channel.mention}.")

    @ch.command(name='list')
    async def __list(self, ctx, page_no: int=None):
        """View a list of all the linked channels."""
        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.guild(ctx.guild).channels()
        if not data:
            return await ctx.send("There is no available data to show.")

        pages = await self.get_pages(data, ctx.guild)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        if not pages:
            return await ctx.send("There is no available data to show.")

        e=discord.Embed(title=f"Total channels - {len(data)}", description=pages[page_no], colour=ctx.author.color)
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
            e=discord.Embed(title=f"Total channels - {len(data)}", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break

    @ch.command(name='active')
    async def _activelist(self, ctx, page_no: int=None):
        """View a list of all the active linked channels."""
        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.guild(ctx.guild).channels()
        if not data:
            return await ctx.send("There is no available data to show.")

        pages = await self.get_pages(data, ctx.guild, True)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        if not pages:
            return await ctx.send("There is no available data to show.")

        e=discord.Embed(title=f"Total channels - {len(data)}", description=pages[page_no], colour=ctx.author.color)
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
            e=discord.Embed(title=f"Total channels - {len(data)}", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break
    
    def get_data_arranged(self, data, active):
        msgs = []
        for channel in data:
            channelObj = self.bot.get_channel(int(channel))
            if not channelObj:
                continue

            for linkedChannelId in data[str(channel)]:
                linkedChannel = self.bot.get_channel(int(linkedChannelId))
                if not linkedChannel:
                    continue

                if active and data[str(channel)][str(linkedChannelId)]['toggle']:
                    msg = f'{channelObj.mention} `{channelObj.id}` --> {linkedChannel.mention} `{linkedChannel.id}`'
                    msgs.append(msg)
                elif not active:
                    msg = f'{channelObj.mention} `{channelObj.id}` --> {linkedChannel.mention} `{linkedChannel.id}`'
                    msgs.append(msg)

        return msgs

    async def get_pages(self, data, guild, active=False):
        page_size = 5
        i = 0
        output_data = []
        text = ""
        n = 1
        data = self.get_data_arranged(data, active)
        for msg in data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            text += f"`{n}.` {msg}\n\n"
            n += 1
        if text != "":
            output_data.append(text)
        return output_data

    async def get_message(self, message, channel):
        if message.embeds:
            e = discord.Embed.from_dict({**message.embeds[0].to_dict(), "timestamp": str(message.created_at)})
        else:
            e = discord.Embed(description=message.content, timestamp=message.created_at)

            attachments = []
            for attachment in message.attachments:
                if any(attachment.filename.endswith(extension) for extension in ["png",'jpeg', "jpg", "gif"]):
                    e.set_image(url=attachment.url)
                else:
                    attachments.append(f"[{attachment.filename}]({attachment.url})")
            if attachments:
                e.add_field(name="Attachments", value="\n".join(attachments_urls))
            
        try:
            await channel.send(embed=e, content=f'{message.author.mention} said the following in {message.channel.mention} on **{message.guild.name}** server.')
        except:
            pass

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if not message.guild:
            return
        
        if message.author.bot:
            return

        data = await self.data.guild(message.guild).channels()
        if str(message.channel.id) not in data:
            return
        
        channels = [self.bot.get_channel(int(x)) for x in data[str(message.channel.id)] if data[str(message.channel.id)][x]['toggle']]
        channels = [channel for channel in channels if channel is not None]
        
        for channel in channels:
            await self.get_message(message, channel)
