from redbot.core import commands, Config
from redbot.core.bot import Red
from discord.ext import tasks
from datetime import datetime, timedelta
import pytz
import discord
import aiohttp


class MommyMinder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20240203, force_registration=True)
        self.session = aiohttp.ClientSession()
        
        default_guild = {
            "bot_name": "",
            "bot_avatar": "",
        }
        
        default_user = {
            "reminders": [],
            "accountable_buddies": []
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    def cog_unload(self):
        self.reminder_check.cancel()
        self.bot.loop.create_task(self.session.close())

    ### REMINDER SHIZ ###

    @tasks.loop(minutes=1.0)
    async def reminder_check(self):
        now = datetime.now(pytz.utc)
        all_users = await self.config.all_users()
        
        for user_id, data in all_users.items():
            reminders = data.get("reminders", [])
            for reminder in reminders:
                reminder_time = datetime.fromisoformat(reminder["time"])
                if now >= reminder_time and now < (reminder_time + timedelta(minutes=1)):
                    await self.send_reminder(user_id, reminder)
                    
    async def send_reminder(self, user_id: int, reminder: dict):
        user = self.bot.get_user(user_id)
        if not user:
            return
        
        await user.send(f"Reminder: {reminder['name']}")
        accountable_buddy = reminder.get("accountable_buddy")
        
        if accountable_buddy:
            buddy = self.bot.get_user(accountable_buddy)
            if buddy:
                await buddy.send(f"{user.name} has a reminder: {reminder['name']}")
        
        # Confirm task completion
        def check(msg):
            return msg.author == user and msg.content.lower() == "done"

        try:
            await self.bot.wait_for("message", timeout=1800.0, check=check)
        except TimeoutError:
            if accountable_buddy:
                buddy = self.bot.get_user(accountable_buddy)
                if buddy:
                    await buddy.send(f"{user.name} did not confirm their reminder: {reminder['name']}")

    @commands.group(name="mommyminder")
    async def ollama(self, ctx):
        """MommyMinder configuration commands."""
        pass

    ### SETUP COMMANDS ###
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None and not message.author.bot:
            await self.handle_dm(message)

    async def handle_dm(self, message: discord.Message):
        user = message.author
        await user.send("Please use the slash commands to set up your reminders.")

    @commands.hybrid_command(name="setreminder", description="Setup a new reminder")
    async def set_reminder(self, ctx: commands.Context):
        await ctx.defer()
        modal = ReminderSetupModal(bot=self.bot, ctx=ctx)
        await ctx.send_modal(modal)

    ### GENERAL COMMANDS ###

#    @commands.admin()
#    @MommyMinder.commands(name="settings")
#    async def showsettings(self, ctx):
#        """Displays the current settings for the guild or DM."""
#        if ctx.guild is not None:
#            settings = await self.config.guild(ctx.guild).all()
#            scope = "Guild"
#        else:
#            settings = await self.config.user(ctx.author).all()
#            scope = "DM"
#        settings_formatted = "\n".join([f"{key}: {value}" for key, value in settings.items()])
#        await ctx.send(f"**{scope} Settings:**\n```{settings_formatted}```")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None and not message.author.bot:
            await self.handle_dm(message)

    async def handle_dm(self, message: discord.Message):
        user = message.author
        await user.send("Please use the slash commands to set up your reminders.")


    ### SERVER / DM STUFF ###

#    @commands.admin()
#    @MommyMinder.command(name="name")
#    async def set_bot_name(self, ctx, *, name: str):
#        """Set the bot name."""
#        if len(name) > 15:
#            await ctx.send("The bot name must be under 15 characters.")
#            return
#        if ctx.guild is not None:
#            await self.config.guild(ctx.guild).bot_name.set(name)
#            scope = "Guild"
#        await ctx.send(f"{scope} bot name updated successfully.")

#    @commands.admin()
#    @MommyMinder.command(name="avatar")
#    async def set_bot_avatar(self, ctx, *, url: str):
#        """Set the bot avatar URL."""
#        if not url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
#            await ctx.send("Please provide a valid image URL. Accepted formats: PNG, JPG, JPEG, GIF")
#            return
#        if ctx.guild is not None:
#            await self.config.guild(ctx.guild).bot_avatar.set(url)
#            scope = "Guild"
#        await ctx.send(f"{scope} bot avatar updated successfully.")

### THE ACTUAL SETUP SHIZ ###

class ReminderSetupModal(discord.ui.Modal):
    def __init__(self, bot: Red, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx
        super().__init__(title="Set Reminder")

        self.name = discord.ui.TextInput(label="Reminder Name", placeholder="e.g. Take Medication")
        self.add_item(self.name)

        self.time = discord.ui.TextInput(label="Reminder Time (HH:MM, 24-hour)", placeholder="e.g. 14:00")
        self.add_item(self.time)

        self.timezone = discord.ui.TextInput(label="Time Zone", placeholder="e.g. UTC, PST, EST")
        self.add_item(self.timezone)

        self.frequency = discord.ui.Select(placeholder="Frequency", options=[
            discord.SelectOption(label="Daily", value="daily"),
            discord.SelectOption(label="Weekly", value="weekly")
        ])
        self.add_item(self.frequency)

        self.buddy = discord.ui.TextInput(label="Accountable Buddy (User ID)", placeholder="e.g. 123456789012345678")
        self.add_item(self.buddy)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        name = self.name.value
        time_str = self.time.value
        tz_str = self.timezone.value
        frequency = self.frequency.values[0]
        buddy_id = int(self.buddy.value)
        
        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            await interaction.response.send_message("Invalid time format. Please use HH:MM (24-hour).", ephemeral=True)
            return
        
        try:
            tz = pytz.timezone(tz_str)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message("Invalid time zone. Please provide a correct time zone abbreviation.", ephemeral=True)
            return

        now = datetime.now(tz)
        reminder_datetime = datetime.combine(now.date(), time_obj, tz)
        if reminder_datetime < now:
            reminder_datetime += timedelta(days=1)

        reminder = {
            "name": name,
            "time": reminder_datetime.isoformat(),
            "frequency": frequency,
            "accountable_buddy": buddy_id
        }

        async with self.bot.config.user(user).reminders() as reminders:
            reminders.append(reminder)

        await interaction.response.send_message(f"Reminder '{name}' set for {time_str} {tz_str} ({frequency}).")

async def setup(bot):
    cog = MommyMinder(bot)
    bot.add_cog(cog)