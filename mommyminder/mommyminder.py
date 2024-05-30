from redbot.core import commands, Config, app_commands
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
            "accountable_buddies": [],
            "timezone": "",
            "gender": "",
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

    ### GENERAL COMMANDS ###
    
    @app_commands.command(name="settings", description="Displays your settings and reminders.")
    async def settings(self, interaction: discord.Interaction):
        user = interaction.user
        user_data = await self.config.user(user).all()
        timezone = user_data.get("timezone", "Not set")
        reminders = user_data.get("reminders", [])
        reminders_str = ""
        for reminder in reminders:
            reminders_str += (
                f"**Name:** {reminder['name']}\n"
                f"**Next Reminder:** {reminder['remaining']}\n"
                f"**Time:** {reminder['time']}\n"
                f"**Frequency:** {reminder['frequency']}\n"
                f"**Accountable Buddy:** {reminder['accountable_buddy']}\n\n"
            )
        if not reminders_str:
            reminders_str = "No reminders set."
        embed = discord.Embed(title="Your Settings and Reminders", color=discord.Color.blue())
        embed.add_field(name="Timezone", value=timezone, inline=False)
        embed.add_field(name="Reminders", value=reminders_str, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None and not message.author.bot:
            await self.handle_dm(message)

    async def handle_dm(self, message: discord.Message):
        user = message.author
        await user.send("Please use the slash commands to set up your reminders.")

    ### THE ACTUAL SETUP SHIZ ###
    @app_commands.command(name="setreminder", description="Setup a new reminder.")
    async def set_reminder(self, interaction: discord.Interaction):
        #await ctx.defer()
        modal = ReminderSetupModal(bot=self.bot, user=interaction.user)
        await interaction.response.send_modal(modal)
        
    @app_commands.command(name="setpronouns", description="Add your pronouns.")
    @app_commands.choices(gender=[
         app_commands.Choice(name="Masculine", value="masculine"),
         app_commands.Choice(name="Feminine", value="feminine"),
         app_commands.Choice(name="Neutral", value="neutral"),
         app_commands.Choice(name="Fluid", value="fluid"),
    ])
    async def set_gender(self, interaction: discord.Interaction, gender: app_commands.Choice[str]):
        await self.config.user(ctx.author).gender.set(gender)
        await interaction.response.send_message(f"Your pronouns have been set to be {gender.value}", ephemeral=True)
        
    @app_commands.command(name="settimezone", description="Send your timezone as a tz identifier (google it)")
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        try:
            tz = pytz.timezone(timezone)
            await self.config.user(ctx.author).timezone.set(timezone)
            await ctx.send(f"Your timezone has been set to {timezone}.")
        except pytz.UnknownTimeZoneError:
            await ctx.send("Invalid timezone. Please provide a valid timezone identifier (e.g., 'US/Eastern').")
        
class ReminderSetupModal(discord.ui.Modal, title="Set Reminder"):
    def __init__(self, bot: Red, user: discord.User):
        self.bot = bot
        self.user = user

        self.name = discord.ui.TextInput(label="Reminder Name", placeholder="e.g. Take Medication")
        self.add_item(self.name)

        self.time = discord.ui.TextInput(label="Reminder Time (HH:MM, 24-hour)", placeholder="e.g. 14:00, 02:30")
        self.add_item(self.time)

        self.frequency = discord.ui.TextInput(label="Frequency (Daily/Weekly)", placeholder="e.g. Daily or Weekly")
        self.add_item(self.frequency)

        self.buddy = discord.ui.TextInput(label="Accountable Buddy (User ID)", placeholder="e.g. 123456789012345678")
        self.add_item(self.buddy)

    async def callback(self, interaction: discord.Interaction):
        user = self.user
        name = self.name.value
        time_str = self.time.value
        frequency = self.frequency.values[0]
        buddy_id = int(self.buddy.value)
        tz_str = await self.config.user(user).timezone
        
        if frequency not in ["daily", "weekly"]:
            await interaction.response.send_message("Invalid frequency. Please specify 'Daily' or 'Weekly'.", ephemeral=True)
            return
        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            await interaction.response.send_message("Invalid time format. Please use HH:MM (24-hour).", ephemeral=True)
            return
        try:
            tz = pytz.timezone(tz_str)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message("Invalid timezone. Please set your timezone using the settimezone command.", ephemeral=True)
            return
        
        now = datetime.now(tz)
        reminder_datetime = datetime.combine(now.date(), time_obj, tz)
        
        if reminder_datetime < now:
            if frequency == "daily":
                reminder_datetime += timedelta(days=1)
            else:
                reminder_datetime += timedelta(days=7)
            
        reminder = {
            "name": name,
            "remaining": reminder_datetime.isoformat(),
            "time": time_obj.isoformat(),
            "frequency": frequency,
            "accountable_buddy": buddy_id
        }

        async with self.bot.config.user(user).reminders() as reminders:
            reminders.append(reminder)

        await interaction.response.send_message(f"Reminder '{name}' set for {time_str} {tz_str} ({frequency}).")

async def setup(bot):
    cog = MommyMinder(bot)
    bot.add_cog(cog)