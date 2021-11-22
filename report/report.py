import discord
from redbot.core import commands, Config, checks
from redbot.core.bot import Red
import datetime
from PIL import Image
from io import BytesIO
import requests

class Report(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=98461984651981, force_registration=True)

        default_guild = {
            "logChannel": None,
            "reports": {}
            }
        
        self.data.register_guild(**default_guild)

    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.group(name="tracker")
    async def _tracker(self, ctx):
        """Tracker report system"""

    @_tracker.command(name="channel")
    async def _channel(self, ctx, channel: discord.TextChannel):
        """Set a log channel."""

        await self.data.guild(ctx.guild).logChannel.set(channel.id)
        await ctx.send(f"Successfully set the log channel as {channel.mention}")

    @_tracker.command(name="offense")
    async def _offense(self, ctx, name: str, page_no: int=None):
        """List all the offenses reported  for a user."""

        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.guild(ctx.guild).reports()
        if not data or name.lower() not in data :
            return await ctx.send("There is no available data to show for this user.")

        pages = await self.get_pages_user(data[name.lower()], ctx.guild)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        e=discord.Embed(title=f"Offenses", description=pages[page_no], colour=ctx.author.color)
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
            e=discord.Embed(title=f"Offenses", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break

    @_tracker.command(name="list")
    async def _list(self, ctx, page_no: int=None):
        """List all the  reported users with total violations."""

        if page_no is None or page_no <= 0:
            page_no = 1

        data = await self.data.guild(ctx.guild).reports()
        if not data:
            return await ctx.send("There is no available data to show.")

        pages = await self.get_pages(data, ctx.guild)

        if len(pages) < page_no:
            page_no = len(pages)

        page_no = page_no - 1

        e=discord.Embed(title=f"Reports List - {len(data)}", description=pages[page_no], colour=ctx.author.color)
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
            e=discord.Embed(title=f"Reports List - {len(data)}", description=pages[page_no], colour=ctx.author.color)
            e.set_footer(text=f"Page No: {page_no+1}/{len(pages)}")
            try:
                await sent.edit(embed=e)
            except:
                break
            try:
                await reaction.remove(ctx.author)
            except:
                break


    @_tracker.command(name="report")
    async def _report(self, ctx):
        """Report a user to the staff team."""

        logChannel = await self.data.guild(ctx.guild).logChannel()
        if not logChannel:
            return await ctx.send(f"Please notify an admin to set the log channel for reports using `{ctx.prefix}tracker channel` command.")

        logChannel = ctx.guild.get_channel(logChannel)
        if not logChannel:
            return await ctx.send(f"Please notify an admin that log channel was not found and to reset the channel using `{ctx.prefix}tracker channel` command.")

        data = await self.data.guild(ctx.guild).reports()

        offenseData = {
            "offender": None,
            "detail": None,
            "proof": None,
            "reporter": ctx.author.id}

        def check(m):
            return m.author == ctx.author and m.channel == ctx.author.dm_channel
        
        await ctx.author.send(embed=discord.Embed(description="Please reply with the user name of the person you are trying to report.").set_footer(text="Reply with 'exit' if you want to exit."))

        try:
            DM = await self.bot.wait_for("message", check=check, timeout=120)
        except:
            return await ctx.author.send("You timed out.")

        if DM:
            if DM.content.lower() == "exit":
                return await ctx.author.send(embed=discord.Embed(description="You have exited the report menu."))

            offenseData['offender'] = DM.content.lower()
            
            if offenseData['offender'] in data and len(data[offenseData['offender']]) == 3:
                return await ctx.author.send("User has already reached their maximum limits (3).")

        await ctx.author.send(embed=discord.Embed(description="Please explain what is the offense user commited?").set_footer(text="Reply with 'exit' if you want to exit."))
        
        try:
            DM = await self.bot.wait_for("message", check=check, timeout=180)
        except:
            return await ctx.author.send("You timed out.")

        if DM:
            if DM.content.lower() == "exit":
                return await ctx.author.send(embed=discord.Embed(description="You have exited the report menu."))

            offenseData['detail'] = DM.content

        await ctx.author.send(embed=discord.Embed(description="Please attach a screenshot proving your claims?").set_footer(text="Reply with 'exit' if you want to exit."))

        while True:
            try:
                DM = await self.bot.wait_for("message", check=check, timeout=180)
            except:
                return await ctx.author.send("You timed out.")

            if DM.content and DM.content.lower() == "exit":
                return await ctx.author.send(embed=discord.Embed(description="You have exited the report menu."))
            else:
                if "http" in DM.content or "https" in DM.content:
                    imagebytes =  await self.LinkToByes(DM.content)
                    
                elif DM.attachments:
                    attachmentUrl = DM.attachments[0].url
                    imagebytes =  await self.LinkToByes(attachmentUrl)
                else:
                    await ctx.author.send("No proof was provided, please attach a screenshot.")
                    continue

                if not imagebytes:
                    await ctx.author.send("No a valid screenshot, please attach a screenshot.")
                    continue

                imageFile = discord.File(fp=imagebytes, filename="test.png")
                break
        
        embed=discord.Embed(description=f"User Reported: {offenseData['offender']} \nReporter: {ctx.author.mention}\nReason: {offenseData['detail']}")
        embed.set_image(url="attachment://test.png")
        if offenseData['offender'] in data and len(data[offenseData['offender']]) == 2:
            SentMsg = await logChannel.send(embed=embed, content="@everyone This is the 3rd report for the user.", file=imageFile)
        else:
            SentMsg = await logChannel.send(embed=embed, file=imageFile)
        
        offenseData['proof'] =  SentMsg.embeds[0].image.url

        ListData = []
        if offenseData['offender'] not in data:
            ListData.append(offenseData)
            await self.data.guild(ctx.guild).reports.set_raw(offenseData['offender'], value=ListData)
        else:
            ListData = data[offenseData['offender']]
            ListData.append(offenseData)
            await self.data.guild(ctx.guild).reports.set_raw(offenseData['offender'], value=ListData)


    async def LinkToByes(self, link):
        try:
            response = requests.get(link)
            img = Image.open(BytesIO(response.content))
        except Exception as e:
            print(e)
            return

        image_binary = BytesIO()
        img.save(image_binary, "png")
        image_binary.seek(0)
        return image_binary

    async def get_pages_user(self, data, guild):
        page_size = 1
        i = 0
        output_data = []
        text = ""
        for report in data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            text += f"`Reason`: {report['detail']}\n`Proof`: {report['proof']}\n`Reporter:` <@{report['reporter']}>\n`Total Reports:` {len(data)}\n\n\n"

        if text != "":
            output_data.append(text)
        return output_data

    async def get_pages(self, data, guild):
        page_size = 5
        i = 0
        output_data = []
        text = ""
        n = 0
        for offenders in data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            text += f"`Name:` {offenders}\n`Total Reports:` {len(data[offenders])}\n\n\n"
            n += 1
        if text != "":
            output_data.append(text)
        return output_data