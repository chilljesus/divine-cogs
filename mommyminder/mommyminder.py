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
            "timezone": None,
            "gender": None,
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.reminder_check.start()

    def cog_unload(self):
        self.reminder_check.cancel()
        self.bot.loop.create_task(self.session.close())

    ### REMINDER SHIZ ###

    @tasks.loop(minutes=1.0)
    async def reminder_check(self):
        now = datetime.now(pytz.utc)
        print(f"Running reminder check at {now}.") 
        all_users = await self.config.all_users()
        for user_id, data in all_users.items():
            reminders = data.get("reminders", [])
            for i, reminder in enumerate(reminders):
                tz = pytz.timezone(await self.config.user_from_id(user_id).timezone())
                remaining = datetime.fromisoformat(reminder["remaining"])
                if now >= remaining:
                    await self.send_reminder(user_id, reminder)
                    if reminder["frequency"] == "daily":
                        next_reminder_datetime = remaining + timedelta(days=1)
                    elif reminder["frequency"] == "weekly":
                        next_reminder_datetime = remaining + timedelta(weeks=1)
                    reminder["remaining"] = next_reminder_datetime.isoformat()
                    async with self.config.user_from_id(user_id).reminders() as user_reminders:
                        user_reminders[i] = reminder

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
    async def mommyminder(self, ctx):
        """MommyMinder configuration commands."""
        pass

    ### GENERAL COMMANDS ###
    
    @app_commands.command(name="settings", description="Displays your settings and reminders.")
    async def settings(self, interaction: discord.Interaction):
        user = interaction.user
        user_data = await self.config.user(user).all()
        gender = user_data.get("gender", "Not set")
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
        embed = discord.Embed(title="Your Settings and Reminders", color=discord.Color.purple())
        embed.add_field(name="Gender", value=gender, inline=False)
        embed.add_field(name="Timezone", value=timezone, inline=False)
        embed.add_field(name="Reminders", value=reminders_str, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    ### THE ACTUAL SETUP SHIZ ###        
    @app_commands.command(name="setreminder", description="Set a new reminder.")
    async def set_reminder(self, interaction: discord.Interaction):
        try:
            modal = ReminderSetupModal(bot=self.bot, user=interaction.user)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Error sending modal: {e}")
            await interaction.response.send_message("An error occurred while displaying the modal. Please try again.", ephemeral=True)
        
    @app_commands.command(name="setpronouns", description="Add your pronouns.")
    @app_commands.choices(gender=[
         app_commands.Choice(name="Masculine", value="masculine"),
         app_commands.Choice(name="Feminine", value="feminine"),
         app_commands.Choice(name="Neutral", value="neutral"),
         app_commands.Choice(name="Fluid", value="fluid"),
    ])
    async def set_gender(self, interaction: discord.Interaction, gender: app_commands.Choice[str]):
        await self.config.user(interaction.user).gender.set(gender.value)
        await interaction.response.send_message(f"Your pronouns have been set to be {gender.value}", ephemeral=True)

    @app_commands.command(name="settimezone", description="Send your timezone as a tz identifier (google it)")
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        try:
            tz = pytz.timezone(timezone)
            await self.config.user(interaction.user).timezone.set(timezone)
            await interaction.response.send_message(f"Your timezone has been set to {timezone}.")
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message("Invalid timezone. Please provide a valid timezone identifier (e.g., 'US/Eastern').")
     
    @app_commands.command(name="setbuddy", description="Set a default acountability buddy")
    async def set_buddy(self, interaction: discord.Interaction, buddy: discord.Member):
        await self.config.user(interaction.user).buddy.set(buddy.value)
        await interaction.response.send_message(f"Your default buddy has been set to {buddy.value}", ephemeral=True)
        
    @app_commands.command(name="reminders", description="See and edit your reminders")
    async def edit_reminders(self, interaction: discord.Interaction):
        user_data = await self.config.user(user).all()
        reminders = user_data.get("reminders", [])
        if not reminders:
            await interaction.response.send_message("You have no reminders set.", ephemeral=True)
            return
        current_index = 0
        embed = self.create_reminder_embed(reminders, current_index)
        view = ReminderView(reminders, current_index, self.config, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    def create_reminder_embed(self, reminders, index):
        reminder = reminders[index]
        embed = discord.Embed(title=f"Reminder {index + 1}/{len(reminders)}", color=discord.Color.purple())
        embed.add_field(name="Name", value=reminder["name"], inline=False)
        embed.add_field(name="Next Reminder", value=reminder["remaining"], inline=False)
        embed.add_field(name="Time", value=reminder["time"], inline=False)
        embed.add_field(name="Frequency", value=reminder["frequency"], inline=False)
        embed.add_field(name="Accountable Buddy", value=str(reminder["accountable_buddy"]), inline=False)
        return embed
    
class ReminderView(discord.ui.View):
    def __init__(self, reminders, current_index, config, user):
        super().__init__(timeout=None)
        self.reminders = reminders
        self.current_index = current_index
        self.config = config
        self.user = user
        self.update_buttons()

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_index -= 1
        embed = self.create_reminder_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, disabled=False)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_index += 1
        embed = self.create_reminder_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        del self.reminders[self.current_index]
        await self.config.user(self.user).reminders.set(self.reminders)

        if not self.reminders:
            await interaction.response.edit_message(content="All reminders deleted.", embed=None, view=None)
            return

        if self.current_index >= len(self.reminders):
            self.current_index = len(self.reminders) - 1
        
        embed = self.create_reminder_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_reminder_embed(self):
        reminder = self.reminders[self.current_index]
        embed = discord.Embed(title=f"Reminder {self.current_index + 1}/{len(self.reminders)}", color=discord.Color.blue())
        embed.add_field(name="Name", value=reminder["name"], inline=False)
        embed.add_field(name="Next Reminder", value=reminder["remaining"], inline=False)
        embed.add_field(name="Time", value=reminder["time"], inline=False)
        embed.add_field(name="Frequency", value=reminder["frequency"], inline=False)
        embed.add_field(name="Accountable Buddy", value=str(reminder["accountable_buddy"]), inline=False)
        return embed

    def update_buttons(self):
        self.previous.disabled = self.current_index == 0
        self.next.disabled = self.current_index == len(self.reminders) - 1
            
class ReminderSetupModal(discord.ui.Modal, title="Set Reminder"):
    def __init__(self, bot: Red, user: discord.User):
        super().__init__(title="Set Reminder")
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

    async def on_submit(self, interaction: discord.Interaction):
        user = self.user
        name = self.name.value
        time_str = self.time.value
        frequency = self.frequency.value.lower()
        buddy_id = int(self.buddy.value)
        tz_str = await self.bot.get_cog("MommyMinder").config.user(user).timezone()

        print(f"Received modal submission: name={name}, time_str={time_str}, frequency={frequency}, buddy_id={buddy_id}, tz_str={tz_str}")

        # Check if frequency is valid
        if frequency not in ["daily", "weekly"]:
            await interaction.response.send_message("Invalid frequency. Please specify 'Daily' or 'Weekly'.", ephemeral=True)
            return
        
        # Validate the provided time
        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            await interaction.response.send_message("Invalid time format. Please use HH:MM (24-hour).", ephemeral=True)
            return
        
        # Validate the timezone
        try:
            tz = pytz.timezone(tz_str)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message("Invalid timezone. Please set your timezone using the settimezone command.", ephemeral=True)
            return
        
        # Calculate the reminder time
        now = datetime.now(tz)
        today_date = now.date()
        reminder_datetime = tz.localize(datetime.combine(today_date, time_obj))
        
        # Adjust reminder_datetime based on the current time and frequency
        if reminder_datetime < now:
            if frequency == "daily":
                reminder_datetime += timedelta(days=1)
            else:  # frequency == "weekly"
                reminder_datetime += timedelta(days=7)
        
        reminder = {
            "name": name,
            "remaining": reminder_datetime.isoformat(),
            "time": time_obj.isoformat(),
            "frequency": frequency,
            "accountable_buddy": buddy_id
        }

        # Save the reminder
        async with self.bot.get_cog("MommyMinder").config.user(user).reminders() as reminders:
            reminders.append(reminder)
        print("Set variables.")
        await interaction.response.send_message(f"Reminder '{name}' set for {time_str} {tz_str} ({frequency}).")

async def setup(bot):
    cog = MommyMinder(bot)
    bot.add_cog(cog)