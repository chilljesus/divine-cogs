from redbot.core import commands, Config
import discord
import aiohttp

class Ollama(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20240203, force_registration=True)
        self.session = aiohttp.ClientSession()

        default_global = {
            "model_blacklist": []
        }

        default_guild = {
            "api_hostname": "localhost",
            "api_port": 8000,
            "api_endpoint": "/api/chat",
            "model": "",
            "threads": False
        }
        
        default_user = {
            "api_hostname": "localhost",
            "api_port": 8000,
            "api_endpoint": "/api/chat",
            "model": "",
            "threads": False
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="ollama")
    async def ollama(self, ctx):
        """Ollama configuration commands."""
        pass

    ### GENERAL COMMANDS ###

    @commands.command(name="settings")
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

    @commands.command(name="getmodels")
    async def getmodels(self, ctx):
        """Get the available models."""
        api_url = f"http://{await self.config.api_hostname()}:{await self.config.api_port()}/api/tags"
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
    @commands.command(name="addmodeltoblacklist")
    async def add_model_to_blacklist(self, ctx, *, model_name: str):
        """Adds a model to the global models blacklist. Bot owner only."""
        async with self.config.models_blacklist() as blacklist:
            if model_name not in blacklist:
                blacklist.append(model_name)
                await ctx.send(f"Model `{model_name}` added to the blacklist.")
            else:
                await ctx.send(f"Model `{model_name}` is already in the blacklist.")

    ### API SETUP ###

    @commands.command(name="sethost")
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

    @commands.command(name="setport")
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
        full_url = f"http://{await config_scope.api_hostname()}:{port}{await config_scope.api_endpoint()}"
        await ctx.send(f"{scope} API port updated. Current API URL: {full_url}")

    @commands.command(name="setendpoint")
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
        full_url = f"http://{await config_scope.api_hostname()}:{await config_scope.api_port()}{endpoint}"
        await ctx.send(f"{scope} API endpoint updated. Current API URL: {full_url}")

    ### SERVER / DM STUFF ###

    @ollama.command(name="setmodel")
    async def setmodel(self, ctx, model: str):
        """Set the model variable."""
        if ctx.guild is not None:
            await self.config.guild(ctx.guild).model.set(model)
            scope = "Guild"
        else:
            await self.config.user(ctx.author).model.set(model)
            scope = "DM"
        await ctx.send("Model variable updated.")

    # todo: make server / dm specific, fix how it works
    @ollama.command(name="setthreads")
    async def setthreads(self, ctx, threads: bool):
        """Toggles responding with a thread."""
        await self.config.threads.set(threads)
        await ctx.send("Threads setting updated.")

    ### THE SAUCE ###

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.id == self.bot.user.id:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
        
        if self.bot.user.mentioned_in(message) or (message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id) or isinstance(message.channel, discord.DMChannel):
            await self.process_message(message)

    async def process_message(self, message):
        threads = await self.config.threads()
        if threads:
            # Create a thread named after the user's name
            thread_name = f"{message.author.display_name} Chat"
            thread = await message.create_thread(name=thread_name, auto_archive_duration=60)
            # The initial message will be processed in respond_in_thread,
            # so we don't need to send it directly here.
            await self.respond_in_thread(thread, message)
        else:
            # When not using threads, format the initial message correctly.
            formatted_message = [{"role": "user", "content": message.content}]
            await self.send_response(message.channel, formatted_message)

    async def respond_in_thread(self, thread, initial_message):
        # Collect messages in the thread, ensuring to filter and format correctly
        async for msg in thread.history(limit=100):
            if msg.author.bot:
                continue
            formatted_messages = [{"role": "assistant" if msg.author.id == self.bot.user.id else "user", "content": msg.content} for msg in await thread.history(limit=100).flatten() if not msg.author.bot]
            await self.send_response(thread, formatted_messages)
            break

    async def send_response(self, destination, formatted_messages):
        model = await self.config.model()
        json_payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "num_predict": 256
            }
        }
        api_url = f"http://{await self.config.api_hostname()}:{await self.config.api_port()}{await self.config.api_endpoint()}"

        try:
            async with destination.typing():
                async with self.session.post(api_url, json=json_payload) as response:
                    response_text = await response.text()  # Get the raw response text
                    if response.status == 200:
                        data = await response.json()
                        response_message = data.get("message", {}).get("content", "Sorry, I couldn't process your request.")
                        #response_message = '.'.join(response_message.split('.')[:-1]) + '.'
                        await destination.send(f"{response_message}")
                    else:
                        await destination.send(f"Error contacting the API. Status: {response.status}\nResponse: ```{response_text}```")
        except Exception as e:
            await destination.send(f"An exception occurred: ```{e}```")

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