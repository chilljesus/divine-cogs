from redbot.core import commands, Config
import discord
import aiohttp

class Ollama(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20240203, force_registration=True)
        self.session = aiohttp.ClientSession()

        default_global = {
            "models_blacklist": [],
            "history_limit": 15,
            "requests": False
        }

        default_guild = {
            "api_hostname": "localhost",
            "api_port": 11434,
            "api_endpoint": "/api/chat",
            "model": "",
            "threads": False,
            "bot_name": "",
            "bot_avatar": "",
            "chats": []
        }
        
        default_user = {
            "api_hostname": "localhost",
            "api_port": 11434,
            "api_endpoint": "/api/chat",
            "model": "",
            "threads": False,
            "bot_name": "",
            "bot_avatar": ""
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.config.register_global(**default_global)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="ollama")
    async def ollama(self, ctx):
        """Ollama configuration commands."""
        pass

    ### GENERAL COMMANDS ###

    @commands.admin()
    @ollama.command(name="settings")
    async def showsettings(self, ctx):
        """Displays the current settings for the guild or DM."""
        if ctx.guild is not None:
            settings = await self.config.guild(ctx.guild).all()
            scope = "Guild"
        else:
            settings = await self.config.user(ctx.author).all()
            scope = "DM"
        settings_formatted = "\n".join([f"{key}: {value}" for key, value in settings.items()])
        await ctx.send(f"**{scope} Settings:**\n```{settings_formatted}```")

    @commands.admin()
    @ollama.command(name="getmodels")
    async def getmodels(self, ctx):
        """Get the available models."""
        if ctx.guild is not None:
            config_source = self.config.guild(ctx.guild)
        else:
            config_source = self.config.user(ctx.author)

        api_hostname = await config_source.api_hostname()
        api_port = await config_source.api_port()
        api_url = f"{api_hostname}:{api_port}/api/tags"

        blacklist = await self.config.models_blacklist()
        try:
            async with ctx.typing():
                async with self.session.get(api_url) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        data = await response.json()
                        model_names = [model['name'] for model in data['models'] if model['name'] not in blacklist]
                        if model_names:
                            response_message = '\n'.join(model_names)
                            await ctx.send(f"Available models:\n{response_message}")
                        else:
                            await ctx.send("There are no available models after applying the blacklist.")
                    else:
                        await ctx.send(f"Error contacting the API. Status: {response.status}\nResponse: ```{response_text}```")
        except Exception as e:
            await ctx.send(f"An exception occurred: ```{e}```")

    @commands.is_owner()
    @ollama.command(name="getallmodels")
    async def getallmodels(self, ctx):
        """Get all available models (including blacklist)."""
        if ctx.guild is not None:
            config_source = self.config.guild(ctx.guild)
        else:
            config_source = self.config.user(ctx.author)

        api_hostname = await config_source.api_hostname()
        api_port = await config_source.api_port()
        api_url = f"{api_hostname}:{api_port}/api/tags"

        try:
            async with ctx.typing():
                async with self.session.get(api_url) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        data = await response.json()
                        model_names = [model['name'] for model in data['models']]
                        if model_names:
                            response_message = '\n'.join(model_names)
                            await ctx.send(f"Available models:\n{response_message}")
                        else:
                            await ctx.send("There are no available models.")
                    else:
                        await ctx.send(f"Error contacting the API. Status: {response.status}\nResponse: ```{response_text}```")
        except Exception as e:
            await ctx.send(f"An exception occurred: ```{e}```")

    @commands.is_owner()
    @ollama.command(name="history")
    async def sethistory(self, ctx, history: int):
        """Set the message history limit."""
        await self.config.history_limit.set(history)
        await ctx.send(f"History updated to `{history}` messages.")

    @commands.is_owner()
    @ollama.command(name="requests")
    async def requests(self, ctx):
        """Toggles dm'ing when requests are made (very spammy)."""
        await self.config.requests.set(not await self.config.requests())
        await ctx.send(f"Requests setting updated to: `{await self.config.requests()}`")

    @commands.is_owner()
    @ollama.command(name="addmodeltoblacklist")
    async def add_model_to_blacklist(self, ctx, *, model_name: str):
        """Adds a model to the global models blacklist. Bot owner only."""
        async with self.config.models_blacklist() as blacklist:
            if model_name not in blacklist:
                blacklist.append(model_name)
                await ctx.send(f"Model `{model_name}` added to the blacklist.")
            else:
                await ctx.send(f"Model `{model_name}` is already in the blacklist.")

    ### API SETUP ###

    @commands.admin()
    @ollama.command(name="host")
    async def sethost(self, ctx, hostname: str):
        """Set the API hostname."""
        if not hostname.startswith(('http://', 'https://')):
            hostname = f"http://{hostname}"
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).api_hostname.set(hostname)
            config_scope = self.config.guild(ctx.guild)
            scope = "Guild"
        else:
            await self.config.user(ctx.author).api_hostname.set(hostname)
            config_scope = self.config.user(ctx.author)
            scope = "DM"
        full_url = f"{hostname}:{await config_scope.api_port()}{await config_scope.api_endpoint()}"
        await ctx.send(f"{scope} API hostname updated. Current API URL: {full_url}")

    @commands.admin()
    @ollama.command(name="port")
    async def setport(self, ctx, port: int):
        """Set the API port."""
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).api_port.set(port)
            config_scope = self.config.guild(ctx.guild)
            scope = "Guild"
        else:
            await self.config.user(ctx.author).api_port.set(port)
            config_scope = self.config.user(ctx.author)
            scope = "DM"
        full_url = f"{await config_scope.api_hostname()}:{port}{await config_scope.api_endpoint()}"
        await ctx.send(f"{scope} API port updated. Current API URL: {full_url}")

    @commands.admin()
    @ollama.command(name="endpoint")
    async def setendpoint(self, ctx, endpoint: str):
        """Set the API endpoint."""
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).api_endpoint.set(endpoint)
            config_scope = self.config.guild(ctx.guild)
            scope = "Guild"
        else:
            await self.config.user(ctx.author).api_endpoint.set(endpoint)
            config_scope = self.config.user(ctx.author)
            scope = "DM"
        full_url = f"{await config_scope.api_hostname()}:{await config_scope.api_port()}{endpoint}"
        await ctx.send(f"{scope} API endpoint updated. Current API URL: {full_url}")

    ### SERVER / DM STUFF ###

    @commands.admin()
    @ollama.command(name="model")
    async def setmodel(self, ctx, model: str):
        """Set the model variable."""
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).model.set(model)
            scope = "Guild"
        else:
            await self.config.user(ctx.author).model.set(model)
            scope = "DM"
        await ctx.send("Model variable updated.")

    @commands.admin()
    @ollama.command(name="threads")
    async def setthreads(self, ctx):
        """Toggles responding with a thread."""
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).threads.set(not await self.config.guild(ctx.guild).threads())
            await ctx.send(f"Threads setting updated to: {await self.config.guild(ctx.guild).threads()}")
        else:
            await ctx.send("Threads cannot be activated inside private messages.")

    @ollama.command(name="newchat")
    async def newchat(self, ctx):
        if ctx.guild is not None:
            #thread_name = f"{ctx.author.display_name} Chat"
            #thread = await ctx.message.create_thread(name=thread_name, auto_archive_duration=60)
            async with self.config.guild(ctx.guild).chats() as chats:
                if ctx.channel.id not in chats:
                    chats.append(ctx.channel.id)
                    await ctx.send("New Chat Initialized.")
                else:
                    await ctx.send("New Chat Initialized.")
        else:
            await ctx.send("New Chat Initialized.")

    @commands.admin()
    @ollama.command(name="name")
    async def set_bot_name(self, ctx, *, name: str):
        """Set the bot name."""
        if len(name) > 15:
            await ctx.send("The bot name must be under 15 characters.")
            return
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).bot_name.set(name)
            scope = "Guild"
        await ctx.send(f"{scope} bot name updated successfully.")

    @commands.admin()
    @ollama.command(name="avatar")
    async def set_bot_avatar(self, ctx, *, url: str):
        """Set the bot avatar URL."""
        if not url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            await ctx.send("Please provide a valid image URL. Accepted formats: PNG, JPG, JPEG, GIF")
            return
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).bot_avatar.set(url)
            scope = "Guild"
        await ctx.send(f"{scope} bot avatar updated successfully.")

    ### THE SAUCE ###

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.id == self.bot.user.id:
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        if message.guild is not None:
            chats = await self.config.guild(message.guild).chats()
        # or ((message.channel.type == "public_thread" or "private_thread") and message.channel.owner.id == self.bot.user.id)
        if self.bot.user.mentioned_in(message) or (message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id) or isinstance(message.channel, discord.DMChannel) or (message.channel.id in chats):
            await self.process_message(message)

    async def process_message(self, message):
        if message.guild is not None:
            threads = await self.config.guild(message.guild).threads()
            chats = await self.config.guild(message.guild).chats()
        else:
            threads = False
        #  or ((message.channel.type == "public_thread" or "private_thread") and message.channel.owner.id == self.bot.user.id)
        if isinstance(message.channel, discord.DMChannel) or (message.guild and message.channel.id in chats):
            history = []
            async for msg in message.channel.history(limit=await self.config.history_limit()):
                if msg.content == "New Chat Initialized.":
                    break
                history.append(msg)
            history = history[::-1]
            formatted_messages = [{"role": "assistant" if msg.author.bot or message.author.id == self.bot.user.id else "user", "content": msg.content} for msg in history]
            await self.send_response(message, formatted_messages)
        else:
            formatted_message = [{"role": "user", "content": message.content}]
            await self.send_response(message, formatted_message)

    async def send_response(self, message, formatted_messages):
        if message.guild is not None:
            model = await self.config.guild(message.guild).model()
        else:
            model = await self.config.user(message.author).model()
        json_payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "num_predict": 256
            }
        }
        if message.guild is not None:
            config_source = self.config.guild(message.guild)
        else:
            config_source = self.config.user(message.author)

        api_hostname = await config_source.api_hostname()
        api_port = await config_source.api_port()
        api_endpoint = await config_source.api_endpoint()
        api_url = f"{api_hostname}:{api_port}{api_endpoint}"
        bot_name = await config_source.bot_name()
        bot_avatar = await config_source.bot_avatar()
        
        try:
            async with message.channel.typing():
                async with self.session.post(api_url, json=json_payload) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        data = await response.json()
                        if await self.config.requests():
                            await message.author.send(f"Sent\n```{json_payload}```\nReceived\n```{data}```")
                        response_message = data.get("message", {}).get("content")
                        if not response_message or response_message.isspace():
                            await self.send_response(message, formatted_messages)
                            return
                        if bot_name is not None and bot_avatar is not None and isinstance(message.channel, discord.DMChannel) is False:
                            webhook = await message.channel.create_webhook(name=bot_name)
                            await webhook.send(str(f"{response_message}"), username=bot_name, avatar_url=bot_avatar)
                            webhooks = await message.channel.webhooks()
                            for webhook_obj in webhooks:
                                await webhook_obj.delete()
                        else:
                            await message.channel.send(f"{response_message}")
                    else:
                        await message.channel.send(f"Error contacting the API. Status: {response.status}\nResponse: ```{response_text}```")
        except Exception as e:
            await message.channel.send(f"An exception occurred: ```{e}```")

async def setup(bot):
    cog = Ollama(bot)
    bot.add_cog(cog)
    
#####################################################################
#                                 __                                #
#                           _,-;''';`'-,.                           #
#                        _/',  `;  `;    `\                         #
#        ,        _..,-''    '   `  `      `\                       #
#       | ;._.,,-' .| |,_        ,,          `\                     #
#       | `;'      ;' ;, `,   ; |    '  '  .   \                    #
#       `; __`  ,'__  ` ,  ` ;  |      ;        \                   #
#       ; (6_);  (6_) ; |   ,    \        '      |       /          #
#      ;;   _,' ,.    ` `,   '    `-._           |   __//_________  #
#       ,;.=..`_..=.,' -'          ,''        _,--''------''''      #
#       \,`"=,,,=="',___,,,-----'''----'_'_'_''-;''                 #
#  -----------------------''''''\ \'''''   )   /'                   #
#                                `\`,,,___/__/'_____,               #
#                                  `--,,,--,-,'''\                  #
#                                 __,,-' /'       `                 #
#                               /'_,,--''                           #
#                              | (                                  #
#                               `'                                  #
#                                                                   #
#####################################################################
#                                                                   #
#           AM EEPY, AM SEEP, AM TIERDE AWF FUKXIN PYTHON           #
#                                                                   #
#####################################################################