from datetime import datetime
import discord
from discord import embeds
import chat_exporter
import io
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from random import randint

class TicketSystem(commands.Cog):
    "TicketSystem Cog."

    def __init__(self, bot: Red):
        self.bot = bot
        self.data = Config.get_conf(self, identifier=4863063434680, force_registration=True)
        default_guild = {
            "ticket":{
                "messageID": None,
                "logChannel": None,
                "archiveChannel": None,
                "perUser": 1,
                "ticketCategory": None,
                "pollToggle": False,
                "pollChannel": None,
                "staffRoles": [],
                "newticketmessage": {"image": str, "message" :str},
            },
            "openTickets": []
        }
        
        self.data.register_guild(**default_guild)

    @checks.admin_or_permissions(administrator=True)
    @commands.group(name="ticket")
    async def _ticket(self, ctx):
        """Manage ticket system."""
        pass

    @_ticket.command()
    async def message(self, ctx, channel: discord.TextChannel, image: str, *, message: str):
        """Set a message which users react to iniate the ticket."""

        embed=discord.Embed(description= message, title='Ticket System')
        embed.set_image(url=image)
        embed.set_footer(text="React to the message to start a ticket.")
        message = await channel.send(embed=embed)
        await message.add_reaction("🎫")

        await self.data.guild(ctx.guild).ticket.set_raw("messageID", value=message.id)
        await ctx.send("Ticket message has been set successfully.")

    @_ticket.command()
    async def ticketmessage(self, ctx, image: str, *, message: str):
        """Set a message that is sent everytime a ticket is created."""
        await self.data.guild(ctx.guild).ticket.set_raw("newticketmessage", "image", value=image)
        await self.data.guild(ctx.guild).ticket.set_raw("newticketmessage", "message", value=message)

        await ctx.send("The message and the image has been changed.")


    @_ticket.command()
    async def logchannel(self, ctx, channel: discord.TextChannel):
        """Setup a log channel where the logs for opening of a ticket will be sent along with the transcript."""
        await self.data.guild(ctx.guild).ticket.set_raw("logChannel", value=channel.id)
        await ctx.send(f"The log channel for the ticket has been set to {channel.mention}")

    @_ticket.command(aliases=['ac'])
    async def archivechannel(self, ctx, channel: discord.TextChannel):
        """Setup a archiveChannel channel where the closing of a ticket will be sent along with the transcript."""
        await self.data.guild(ctx.guild).ticket.set_raw("archiveChannel", value=channel.id)
        await ctx.send(f"The archieve channel for the ticket has been set to {channel.mention}.")

    @_ticket.command(aliases=['tc'])
    async def ticketcategory(self, ctx, category: discord.CategoryChannel):
        """Setup a category where the text channels will be created for all the tickets."""
        await self.data.guild(ctx.guild).ticket.set_raw("ticketCategory", value=category.id)
        await ctx.send(f"The category has been set to **{category.name}**")
        
    @_ticket.command(aliases=['pt'])
    async def polltoggle(self, ctx):
        """Enable/Disable if the polls should be created everytime a ticket is created."""
        data = await self.data.guild(ctx.guild).ticket.get_raw("pollToggle")
        if data:
            await self.data.guild(ctx.guild).ticket.set_raw("pollToggle", value=False)
            await ctx.send("Creation of polls have been disabled.")
        elif not data:
            await self.data.guild(ctx.guild).ticket.set_raw("pollToggle", value=True)
            await ctx.send("Creation of polls has been enabled.")

    @_ticket.command(aliases=['pc'])
    async def pollchannel(self, ctx, channel:discord.TextChannel):
        """Set a channel where the polls will take place."""
        await self.data.guild(ctx.guild).ticket.set_raw("pollChannel", value=channel.id)
        await ctx.send(f"Poll channel has been set to {channel.mention}")

    @_ticket.command(aliases=['ra'])
    async def roleadd(self, ctx, role:discord.Role):
        """Assign roles which have the privelge to end a ticket."""
        data = await self.data.guild(ctx.guild).ticket.get_raw("staffRoles")
        if role.id in data:
            return await ctx.send("This role already exists in the list.")
        elif role.id not in data:
            data.append(role.id)
            await self.data.guild(ctx.guild).ticket.set_raw("staffRoles", value=data)
            await ctx.send(f"**{role.name}** has been added to the list.")

    @_ticket.command(aliases=['rr'])
    async def roleremove(self, ctx, role:discord.Role):
        """Remove roles which have the privelge to end a ticket."""
        data = await self.data.guild(ctx.guild).ticket.get_raw("staffRoles")
        if role.id not in data:
            return await ctx.send("This role does not exist in the list.")
        elif role.id in data:
            data.remove(role.id)
            await self.data.guild(ctx.guild).ticket.set_raw("staffRoles", value=data)
            await ctx.send(f"**{role.name}** has been removed from the list.")

    @_ticket.command(aliases=['pu'])
    async def peruser(self, ctx, number: int):
        """Set how many tickets can a user open at once."""
        await self.data.guild(ctx.guild).ticket.set_raw("perUser", value= number)
        await ctx.send(f"A user can now only open {number} of tickets at a time.")

    @_ticket.command()
    async def settings(self, ctx):
        """View all the ticket settings."""
        data = await self.data.guild(ctx.guild).ticket()
        ticketCategory = data['ticketCategory']
        if ticketCategory:
            ticketCategory = ctx.guild.get_channel(ticketCategory)

        pollchannel = data['pollChannel']
        if pollchannel:
            pollchannel = ctx.guild.get_channel(pollchannel)

        logchannel = data['logChannel']
        if logchannel:
            logchannel = ctx.guild.get_channel(logchannel)

        if data['staffRoles']:
            staffroles = [ctx.guild.get_role(role) for role in data['staffRoles']]
            staffroles = [role.name for role in staffroles if role is not None]
            staffroles = ", ".join(staffroles)
        else:
            staffroles = 'None'

        embed=discord.Embed(title = "Ticket System Settings", description=f""" 
        **Message ID**: {data['messageID']}
        **Log Channel**: {logchannel.mention if logchannel else 'None'}
        **Ticket Category ID**: {ticketCategory.name if ticketCategory else 'None'}
        **Polls**: {'Enabled' if data['pollToggle'] else 'Disabled'}
        **Poll Channel**: {pollchannel.mention if pollchannel else "None"}
        **Staff Roles**: {staffroles}
        """)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        data = await self.data.guild(guild).ticket()
        ticketsdata = await self.data.guild(guild).openTickets()
        logchannel = data['logChannel']
        if logchannel:
            logchannel = guild.get_channel(logchannel)

        for ticket in ticketsdata:
            if ticket['userID'] == member.id:
                channel = guild.get_channel(ticket['channelID'])
                if not channel:
                    continue
                await self.call_ticket_close(channel, logchannel, ticket['userID'], None)

                ticketsdata.remove(ticket)

        await self.data.guild(guild).openTickets.set(ticketsdata)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        data = await self.data.guild(guild).ticket()
        ticketsdata = await self.data.guild(guild).openTickets()

        Validity = await self.checking_validity(user, data['perUser'], ticketsdata)

        POLLCHANNEL = data['pollChannel']
        if POLLCHANNEL:
            POLLCHANNEL = guild.get_channel(POLLCHANNEL)

        ticketCatg = data['ticketCategory']
        if ticketCatg:
            ticketCatg = guild.get_channel(data['ticketCategory'])

        staffroles = []
        if data['staffRoles']:
            staffroles = [guild.get_role(role) for role in data['staffRoles']]
            staffroles = [role for role in staffroles if role is not None]

        logchannel = data['logChannel']
        if logchannel:
            logchannel = guild.get_channel(logchannel)

        archivechannel = data['archiveChannel']
        if archivechannel:
            archivechannel = guild.get_channel(archivechannel)

        if not ticketCatg:
            return await user.send("Ticket system is not setup currently, please reach out to an admin.")
            
        if data['messageID'] and data['messageID'] == message.id:

            if not Validity:
                return await user.send(f"You can only create maximum {data['perUser']} tickets.")

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True, read_message_history=True)
            }

            randomnumber = ''.join(["{}".format(randint(1, 9)) for num in range(0, 5)])

            ticketChannel = await guild.create_text_channel(name=f"{user.name}-{randomnumber}", category=ticketCatg, overwrites=overwrites)
            messageSent = await ticketChannel.send(embed=discord.Embed(description=f"""Welcome {user.mention},
            {data['newticketmessage']['message']}
            
            Please react with ✉️ to close the ticket.""").set_image(url=data['newticketmessage']['image']))

            await messageSent.add_reaction('✉️')
            await messageSent.pin()

            pollMessageID = await self.create_poll(guild, data, user)
            ticketsdata.append({"channelID": ticketChannel.id, 'messageID': messageSent.id, "userID": user.id, "pollMessageID": pollMessageID if pollMessageID else None})
            await self.data.guild(guild).openTickets.set(ticketsdata)

            if logchannel:
                embed = discord.Embed(description=f"{user.mention} has opened a ticket in {ticketChannel.mention}.", timestamp=datetime.utcnow())
                embed.set_footer(text="Ticket created at")
                await logchannel.send(embed=embed)
    
        elif str(payload.emoji) == '✉️':
            for ticket in ticketsdata:
                if ticket['channelID'] == channel.id and ticket['messageID'] == message.id:
                    if not staffroles:
                        return
                    elif staffroles:
                        for role in staffroles:
                            if role in user.roles:
                                await self.call_ticket_close(channel, archivechannel, ticket['userID'], user)
                                if POLLCHANNEL:
                                    pollmessage = await POLLCHANNEL.fetch_message(ticket['pollMessageID'])
                                    TICKetChannel = guild.get_channel(ticket['channelID']) if ticket['channelID'] else None
                                    if pollmessage:
                                        reaction1 = [x for x in pollmessage.reactions if x.emoji == "✅"][0]
                                        reaction1members = [x for x in await reaction1.users().flatten() if x != self.bot.user]

                                        reaction2 = [x for x in pollmessage.reactions if x.emoji == "❌"][0]
                                        reaction2members = [x for x in await reaction2.users().flatten() if x != self.bot.user]

                                        await pollmessage.edit(content=f"The {TICKetChannel.name} poll has ended.\n{len(reaction1members)} voted for ✅.\n{len(reaction2members)} voted for ❌.", embed=None)
                                        await pollmessage.clear_reactions()

                                ticketsdata.remove(ticket)
                                return await self.data.guild(guild).openTickets.set(ticketsdata)

        elif str(payload.emoji) == '🔒':
            if channel.id == data['pollChannel']:
                for ticket in ticketsdata:
                    if ticket['pollMessageID'] == message.id:
                        if user.bot:
                            return
                        
                        TICKetChannel = guild.get_channel(ticket['channelID']) if ticket['channelID'] else None
                        
                        reaction1 = [x for x in message.reactions if x.emoji == "✅"][0]
                        reaction1members = [x for x in await reaction1.users().flatten() if x != self.bot.user]

                        reaction2 = [x for x in message.reactions if x.emoji == "❌"][0]
                        reaction2members = [x for x in await reaction2.users().flatten() if x != self.bot.user]

                        await message.edit(content=f"The {TICKetChannel.name} poll has ended.\n{len(reaction1members)} voted for ✅.\n{len(reaction2members)} voted for ❌.", embed=None)
                        await message.clear_reactions()
                            
                                
    async def checking_validity(self, user, max: int, data):
        "Checks how many tickets can a user create."
        counter = 0
        for ticket in data:
            if ticket['userID'] == user.id:
                counter +=1
        
        if counter >= max:
            return False
        else:
            return True

    async def call_ticket_close(self, channel, logchannel, user, staff):
        """Function to close a ticket."""
        userOBJ = channel.guild.get_member(user)
        filepath = "var/www/html"
        transcript = await chat_exporter.export(channel, channel.guild)
        fileNAME = filepath + f"{channel.name}.html"
        fileNAME2 = filepath + '/' + f"{channel.name}.html"
        if transcript is not None:
            outfile = open(fileNAME, "w", encoding="utf-8")
            outfile.write(transcript)
            outfile.close()

        embed = discord.Embed(description=f"Ticket User - {userOBJ.mention if userOBJ else user}\nTicket Number - transcript-{channel.name}\nClosed By: {staff.mention}\nTicket Transcript - http://tickets.darkh4cks.wtf/{fileNAME2}", timestamp=datetime.utcnow())
        embed.set_footer(text="Ticket closed at")
        await logchannel.send(embed=embed)
        await channel.delete(reason="Ticket Closed")
        member = channel.guild.get_member(user)
        if member:
            await member.send("Your ticket has been closed by the staff member.")
        
    async def create_poll(self, guild, data, user):
        """Creates a poll for the staff."""
        if not data['pollToggle']:
            return
        
        if not data['pollChannel']:
            return

        pollchannel = guild.get_channel(data['pollChannel'])

        if not pollchannel:
            return
        
        embed=discord.Embed(title="POLL", description=f"Poll for the {user.mention}.\n✅ - YES\n❌ - NO\n🔒 - END POLL")
        embed.set_footer(text="Please react to the emojis below to vote.")
        message = await pollchannel.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await message.add_reaction("🔒")
        return message.id
