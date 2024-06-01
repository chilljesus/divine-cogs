from redbot.core import commands, Config, app_commands
from redbot.core.bot import Red
from discord.ext import tasks
from datetime import datetime, timedelta
from discord.ui import Button, View
import pytz
import discord
import aiohttp
import random
import asyncio

responses = {
    "masculine": {
        "notification": [
            ["It's time to get this done, handsome. No more delays. You wouldn't want to disappoint me, would you?", "wave"],
            ["You're not going to let this slip by, are you? Get on it, now. Remember, I'm watching you.", "poke"],
            ["Come on, my strong man. Show me how capable you are and get it done.", "smile"],
            ["Hey there, big guy. It's time to tackle your task and make me proud.", "smug"],
            ["Let's not waste any more time, darling. I expect you to handle this now.", "thumbsup"],
            ["You know what you need to do, puppy. Get started and don't keep me waiting.", "wave"],
            ["I need you to focus and get this done, champ. No excuses.", "poke"],
            ["It's time to shine, my warrior. Finish this task and show me your strength.", "smile"],
            ["Don't keep me waiting, my lion. I expect you to finish this promptly.", "smug"],
            ["Alright, my king. Show me how you conquer this task with your might.", "thumbsup"]
        ],
        "confirmation": [
            ["Great job! I knew you could do it, champ. You've made me very proud.", "highfive"],
            ["Well done, my hero. You're making me proud every single day.", "thumbsup"],
            ["That's my strong man. You handled that perfectly, just as I knew you would.", "happy"],
            ["Excellent work, my lion. You've shown me your strength once again.", "pat"],
            ["You're incredible, my warrior. Keep making me proud.", "smile"],
            ["Fantastic job, my knight. Your dedication is truly admirable.", "highfive"],
            ["Bravo, my champion. You've surpassed my expectations once again.", "thumbsup"],
            ["Amazing work, my king. Your effort is truly commendable.", "happy"],
            ["You've done wonderfully, my prince. Keep up the great work.", "pat"],
            ["Outstanding performance, my hero. You never cease to amaze me.", "smile"]
        ],
        "notifybuddy": [
            ["Hey, your buddy needs a little push. Can you help him out? He could use some of your strength.", "stare"],
            ["Your friend is slacking off again. Give him a nudge, he needs your guidance.", "slap"],
            ["Looks like your buddy is in need of a reminder. Help him out, will you?", "cry"],
            ["Your friend is falling behind. A gentle push from you could do wonders.", "pout"],
            ["He needs your help to stay on track. Give him a reminder.", "stare"],
            ["Your buddy needs a boost. Can you give him a hand?", "slap"],
            ["Help your friend out. He's struggling and could use your encouragement.", "cry"],
            ["Your friend could use a little motivation. Give him a nudge.", "pout"],
            ["Lend a hand to your buddy. He needs your strength right now.", "stare"],
            ["Your friend is in need of support. Give him a push to get going.", "slap"]
        ]
    },
    "feminine": {
        "notification": [
            ["It's time to get this done, beautiful. No more delays. You wouldn't want to disappoint me, would you?", "smile"],
            ["You're not going to let this slip by, are you? Get on it, now. Remember, I'm watching you.", "poke"],
            ["Come on, my lovely lady. Show me how capable you are and get it done.", "wave"],
            ["Hey there, gorgeous. It's time to tackle your task and make me proud.", "smug"],
            ["Let's not waste any more time, sweetheart. I expect you to handle this now.", "thumbsup"],
            ["You know what you need to do, kitten. Get started and don't keep me waiting.", "wave"],
            ["I need you to focus and get this done, darling. No excuses.", "poke"],
            ["It's time to shine, my queen. Finish this task and show me your strength.", "smile"],
            ["Don't keep me waiting, my lioness. I expect you to finish this promptly.", "smug"],
            ["Alright, my princess. Show me how you conquer this task with your grace.", "thumbsup"]
        ],
        "confirmation": [
            ["Great job! I knew you could do it, darling. You've made me very proud.", "highfive"],
            ["Well done, my heroine. You're making me proud every single day.", "thumbsup"],
            ["That's my strong woman. You handled that perfectly, just as I knew you would.", "happy"],
            ["Excellent work, my lioness. You've shown me your strength once again.", "pat"],
            ["You're incredible, my warrior. Keep making me proud.", "smile"],
            ["Fantastic job, my knightess. Your dedication is truly admirable.", "highfive"],
            ["Bravo, my champion. You've surpassed my expectations once again.", "thumbsup"],
            ["Amazing work, my queen. Your effort is truly commendable.", "happy"],
            ["You've done wonderfully, my princess. Keep up the great work.", "pat"],
            ["Outstanding performance, my heroine. You never cease to amaze me.", "smile"]
        ],
        "notifybuddy": [
            ["Hey, your buddy needs a little push. Can you help her out? She could use some of your strength.", "stare"],
            ["Your friend is slacking off again. Give her a nudge, she needs your guidance.", "slap"],
            ["Looks like your buddy is in need of a reminder. Help her out, will you?", "cry"],
            ["Your friend is falling behind. A gentle push from you could do wonders.", "pout"],
            ["She needs your help to stay on track. Give her a reminder.", "stare"],
            ["Your buddy needs a boost. Can you give her a hand?", "slap"],
            ["Help your friend out. She's struggling and could use your encouragement.", "cry"],
            ["Your friend could use a little motivation. Give her a nudge.", "pout"],
            ["Lend a hand to your buddy. She needs your strength right now.", "stare"],
            ["Your friend is in need of support. Give her a push to get going.", "slap"]
        ]
    },
    "neutral": {
        "notification": [
            ["It's time to get this done, superstar. No more delays. You wouldn't want to disappoint me, would you?", "wave"],
            ["You're not going to let this slip by, are you? Get on it, now. Remember, I'm watching you.", "smug"],
            ["Come on, my capable one. Show me how competent you are and get it done.", "smile"],
            ["Hey there, champ. It's time to tackle your task and make me proud.", "poke"],
            ["Let's not waste any more time, dear. I expect you to handle this now.", "thumbsup"],
            ["You know what you need to do, tiger. Get started and don't keep me waiting.", "wave"],
            ["I need you to focus and get this done, ace. No excuses.", "poke"],
            ["It's time to shine, my star. Finish this task and show me your strength.", "smile"],
            ["Don't keep me waiting, my hero. I expect you to finish this promptly.", "smug"],
            ["Alright, my warrior. Show me how you conquer this task with your prowess.", "thumbsup"]
        ],
        "confirmation": [
            ["Great job! I knew you could do it, champ. You've made me very proud.", "highfive"],
            ["Well done, my champion. You're making me proud every single day.", "thumbsup"],
            ["That's my strong one. You handled that perfectly, just as I knew you would.", "happy"],
            ["Excellent work, my hero. You've shown me your strength once again.", "pat"],
            ["You're incredible, my warrior. Keep making me proud.", "smile"],
            ["Fantastic job, my ace. Your dedication is truly admirable.", "highfive"],
            ["Bravo, my champion. You've surpassed my expectations once again.", "thumbsup"],
            ["Amazing work, my star. Your effort is truly commendable.", "happy"],
            ["You've done wonderfully, my hero. Keep up the great work.", "pat"],
            ["Outstanding performance, my champion. You never cease to amaze me.", "smile"]
        ],
        "notifybuddy": [
            ["Hey, your buddy needs a little push. Can you help them out? They could use some of your strength.", "stare"],
            ["Your friend is slacking off again. Give them a nudge, they need your guidance.", "slap"],
            ["Looks like your buddy is in need of a reminder. Help them out, will you?", "cry"],
            ["Your friend is falling behind. A gentle push from you could do wonders.", "pout"],
            ["They need your help to stay on track. Give them a reminder.", "stare"],
            ["Your buddy needs a boost. Can you give them a hand?", "slap"],
            ["Help your friend out. They're struggling and could use your encouragement.", "cry"],
            ["Your friend could use a little motivation. Give them a nudge.", "pout"],
            ["Lend a hand to your buddy. They need your strength right now.", "stare"],
            ["Your friend is in need of support. Give them a push to get going.", "slap"]
        ]
    }
}

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
            "buddy": None,
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
        all_users = await self.config.all_users()
        for user_id, data in all_users.items():
            reminders = data.get("reminders", [])
            for i, reminder in enumerate(reminders):
                tz = pytz.timezone(await self.config.user_from_id(user_id).timezone())
                remaining = datetime.fromisoformat(reminder["remaining"])
                if now >= remaining:
                    await self.send_reminder(user_id, reminder, i)

    async def send_reminder(self, user_id: int, reminder: dict, index: int):
        user = self.bot.get_user(user_id)
        if not user:
            return
        
        user_data = await self.config.user(user).all()
        gender = user_data.get("gender", "neutral")
        if gender == "fluid":
            gender = random.choice(["masculine", "feminine", "neutral"])
        notification_responses = responses[gender]["notification"]
        selected_response = random.choice(notification_responses)
        statement, action = selected_response
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://nekos.best/api/v2/{action}") as resp:
                image = await resp.json()
        embed = discord.Embed(title=reminder["name"], color=discord.Color.purple(), description=statement)
        embed.set_image(url=image["results"][0]["url"])
        button = Button(style=discord.ButtonStyle.red, label="Done!", custom_id="confirm")
        view = View()
        view.add_item(button)
        message = await user.send(embed=embed, view=view)
           
        def check(interaction: discord.Interaction):
            return interaction.user == user and interaction.message.id == message.id

        try:
            interaction = await self.bot.wait_for("interaction", timeout=1800.0, check=check)
            if interaction.data['custom_id'] == "confirm":
                await interaction.response.defer()
                confirmation_responses = responses[gender]["confirmation"]
                selected_response = random.choice(confirmation_responses)
                statement, action = selected_response
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://nekos.best/api/v2/{action}") as resp:
                        image = await resp.json()
                embed = discord.Embed(title=reminder["name"], color=discord.Color.purple(), description=statement)
                embed.set_image(url=image["results"][0]["url"])
                await message.edit(embed=embed, view=None)
                await self.update_reminder_time(user_id, reminder, index)
            
        except asyncio.TimeoutError:
            accountable_buddy = reminder.get("accountable_buddy")
            if accountable_buddy:
                buddy = self.bot.get_user(accountable_buddy)
                if buddy:
                    embed.set_footer(text=f"I've notified {buddy.name}")
                    await message.edit(embed=embed, view=None)
                    notifybuddy_responses = responses[gender]["notifybuddy"]
                    selected_response = random.choice(notifybuddy_responses)
                    statement, action = selected_response
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"https://nekos.best/api/v2/{action}") as resp:
                            image = await resp.json()
                    embed = discord.Embed(title=reminder["name"], color=discord.Color.purple(), description=statement)
                    embed.add_field(name="Time", value=reminder["time"], inline=False)
                    embed.add_field(name="Friend", value=f"<@{user.id}>")
                    embed.set_image(url=image["results"][0]["url"])
                    await buddy.send(embed=embed)
            await self.update_reminder_time(user_id, reminder, index)

    async def update_reminder_time(self, user_id: int, reminder: dict, index: int):
        remaining = datetime.fromisoformat(reminder["remaining"])
        if reminder["frequency"] == "daily":
            next_reminder_datetime = remaining + timedelta(days=1)
        elif reminder["frequency"] == "weekly":
            next_reminder_datetime = remaining + timedelta(weeks=1)
        reminder["remaining"] = next_reminder_datetime.isoformat()
        
        async with self.config.user_from_id(user_id).reminders() as user_reminders:
            user_reminders[index] = reminder
            
    @commands.group(name="mommyminder")
    async def mommyminder(self, ctx):
        """MommyMinder configuration commands."""
        pass
                
    ### GENERAL COMMANDS ###
    
    @app_commands.command(name="help", description="Get command usage and stuff.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Commands Usage",
                      description="**/settings**\nDisplays your set timezone, buddy, pronouns\n\n**/setpronouns**\nAllows you to set masculine, feminine, neutral (enby), and fluid (genderfluid). This determines how the bot refers to you.\n\n**/setbuddy**\nSelect someone from the dropdown list in order to automatically put their id into the reminder modal. For both this command and the modal, they must share a server with the bot.\n\n**/settimezone** *(required)*\nSets your timezone using [TZ Identifiers](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) (the long ones), allowing the bot to message you at the appropriate time. This is a required setting for the bot to work.\n\n**/setreminder**\nOpens a modal allowing you to input a new task to complete, the frequency of it (daily / weekly), the time, and who you want to account for you.\n\n**/reminders**\nShows a paginated view of the reminders you have setup, when the next one will be, the buddy used for them, and allows deletion of reminders.",
                      colour=discord.Color.purple())
        embed.set_image(url="https://small.fileditchstuff.me/s11/FsVJWkFplszyjIKhmNjt.gif")
        embed.set_footer(text="@nekojesus • https://jesus.sh")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="settings", description="Displays your settings.")
    async def settings(self, interaction: discord.Interaction):
        user = interaction.user
        user_data = await self.config.user(user).all()
        gender = user_data.get("gender", "Not set")
        timezone = user_data.get("timezone", "Not set")
        buddy = user_data.get("buddy", "Not set")
        embed = discord.Embed(title="Your Settings", color=discord.Color.purple())
        embed.add_field(name="Gender", value=gender, inline=False)
        embed.add_field(name="Timezone", value=timezone, inline=False)
        embed.add_field(name="Default Buddy", value=f"<@{buddy}>", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
         
    @app_commands.command(name="setreminder", description="Set a new reminder.")
    async def set_reminder(self, interaction: discord.Interaction):
        try:
            user_data = await self.config.user(interaction.user).all()
            #buddy = user_data.get("buddy")
            modal = ReminderSetupModal(bot=self.bot, user=interaction.user, buddyid=user_data.get("buddy"))
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
            await interaction.response.send_message(f"Your timezone has been set to {timezone}.", ephemeral=True)
        except pytz.UnknownTimeZoneError:
            await interaction.response.send_message("Invalid timezone. Please provide a valid timezone identifier (e.g., 'US/Eastern').", ephemeral=True)
     
    @app_commands.command(name="setbuddy", description="Set a default acountability buddy")
    async def set_buddy(self, interaction: discord.Interaction, buddy: discord.User):
        await self.config.user(interaction.user).buddy.set(buddy.id)
        await interaction.response.send_message(f"Your default buddy has been set to <@{buddy.id}>", ephemeral=True)
        
    @app_commands.command(name="reminders", description="See and edit your reminders")
    async def edit_reminders(self, interaction: discord.Interaction):
        user_data = await self.config.user(interaction.user).all()
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
        #try:
        #    print(f"Success: {float(reminder['success'])} & {reminder['success']}, Fail: {float(reminder['fail'])} & {reminder['fail']}")
        #    rate = (float(reminder["success"])+float(reminder["fail"]))/float(reminder["success"])
        #except Exception as error:
        #    rate = None
        #    print(f"Oops: {error}")
        embed = discord.Embed(title=f"Reminder {index + 1}/{len(reminders)}", color=discord.Color.purple())
        embed.add_field(name="Name", value=reminder["name"], inline=False)
        embed.add_field(name="Next Reminder", value=datetime.fromisoformat(reminder["remaining"]), inline=False)
        #embed.add_field(name="Success Rate", value=f"{rate}%")
        embed.add_field(name="Time", value=reminder["time"], inline=False)
        embed.add_field(name="Frequency", value=reminder["frequency"], inline=False)
        embed.add_field(name="Accountable Buddy", value=f"<@{reminder['accountable_buddy']}>", inline=False)
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
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index -= 1
        embed = self.create_reminder_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, disabled=False)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index += 1
        embed = self.create_reminder_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        #try:
        #    print(f"Success: {float(reminder['success'])} & {reminder['success']}, Fail: {float(reminder['fail'])} & {reminder['fail']}")
        #    rate = (float(reminder["success"])+float(reminder["fail"]))/float(reminder["success"])
        #except Exception as error:
        #    rate = "Error"
        #    print(f"Oops: {error}")
        embed = discord.Embed(title=f"Reminder {self.current_index + 1}/{len(self.reminders)}", color=discord.Color.purple())
        embed.add_field(name="Name", value=reminder["name"], inline=False)
        embed.add_field(name="Next Reminder", value=datetime.fromisoformat(reminder["remaining"]), inline=False)
        #embed.add_field(name="Success Rate", value=f"{rate}%")
        embed.add_field(name="Time", value=reminder["time"], inline=False)
        embed.add_field(name="Frequency", value=reminder["frequency"], inline=False)
        embed.add_field(name="Accountable Buddy", value=f"<@{reminder['accountable_buddy']}>", inline=False)
        return embed

    def update_buttons(self):
        self.previous.disabled = self.current_index == 0
        self.next.disabled = self.current_index == len(self.reminders) - 1
                    
class ReminderSetupModal(discord.ui.Modal, title="Set Reminder"):
    def __init__(self, bot: Red, user: discord.User, buddyid):
        #print(f"Received: {buddyid}")
        super().__init__(title="Set Reminder")
        self.bot = bot
        self.user = user

        self.name = discord.ui.TextInput(label="Reminder Name", placeholder="e.g. Take Medication")
        self.add_item(self.name)

        self.time = discord.ui.TextInput(label="Reminder Time (HH:MM, 24-hour)", placeholder="e.g. 14:00, 02:30", min_length=5, max_length=5)
        self.add_item(self.time)

        self.frequency = discord.ui.TextInput(label="Frequency (Daily/Weekly)", placeholder="e.g. Daily or Weekly", max_length=6)
        self.add_item(self.frequency)

        self.buddy = discord.ui.TextInput(label="Accountable Buddy (User ID)", placeholder="e.g. 123456789012345678", default=buddyid)
        self.add_item(self.buddy)

    async def on_submit(self, interaction: discord.Interaction):
        user = self.user
        name = self.name.value
        time_str = self.time.value
        frequency = self.frequency.value.lower()
        buddy_id = int(self.buddy.value)
        tz_str = await self.bot.get_cog("MommyMinder").config.user(user).timezone()

        #print(f"Received modal submission: name={name}, time_str={time_str}, frequency={frequency}, buddy_id={buddy_id}, tz_str={tz_str}")

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
            "accountable_buddy": buddy_id,
            "success": 0,
            "fail": 0
        }

        # Save the reminder
        async with self.bot.get_cog("MommyMinder").config.user(user).reminders() as reminders:
            reminders.append(reminder)
        #print("Set variables.")
        await interaction.response.send_message(f"Reminder '{name}' set for {time_str} {tz_str} ({frequency}).", ephemeral=True)

async def setup(bot):
    cog = MommyMinder(bot)
    bot.add_cog(cog)