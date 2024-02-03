from redbot.core import commands, Config
import discord
import aiohttp

class Ollama(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20240203, force_registration=True)
        self.session = aiohttp.ClientSession()
        default_global = {
            "api_hostname": "localhost",
            "api_port": 8000,
            "api_endpoint": "/api/chat",
            "model": "",
            "threads": False
        }
        self.config.register_global(**default_global)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="ollama")
    async def ollama(self, ctx):
        """Ollama configuration commands."""
        pass

    @ollama.command(name="setapi")
    async def setapi(self, ctx, hostname: str, port: int, endpoint: str):
        """Set the API hostname, port, and endpoint."""
        await self.config.api_hostname.set(hostname)
        await self.config.api_port.set(port)
        await self.config.api_endpoint.set(endpoint)
        await ctx.send("API settings updated.")

    @ollama.command(name="setmodel")
    async def setmodel(self, ctx, model: str):
        """Set the model variable."""
        await self.config.model.set(model)
        await ctx.send("Model variable updated.")

    @ollama.command(name="setthreads")
    async def setthreads(self, ctx, threads: bool):
        """Enable or disable response in threads."""
        await self.config.threads.set(threads)
        await ctx.send("Threads setting updated.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.id == self.bot.user.id:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore commands

        # Check if the bot is mentioned or if the message is a reply to the bot
        if self.bot.user.mentioned_in(message) or (message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id):
            await self.process_message(message)

    async def process_message(self, message):
        threads = await self.config.threads()
        if threads:
            # Create a thread named after the user's name
            thread_name = f"{message.author.display_name} Chat"
            thread = await message.create_thread(name=thread_name, auto_archive_duration=60)
            await self.respond_in_thread(thread, message)
        else:
            await self.send_response(message, [message])

    async def respond_in_thread(self, thread, initial_message):
        # Collect messages in the thread, ensuring to filter and format correctly
        async for msg in thread.history(limit=100):
            if msg.author.bot:
                continue  # Skip bot messages
            formatted_messages = [{"role": "assistant" if msg.author.id == self.bot.user.id else "user", "content": msg.content} for msg in await thread.history(limit=100).flatten() if not msg.author.bot]
            await self.send_response(thread, formatted_messages)
            break  # Exit after processing to avoid repeating the send_response call

    async def send_response(self, destination, formatted_messages):
        model = await self.config.model()
        json_payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": False
        }
        api_url = f"http://{await self.config.api_hostname()}:{await self.config.api_port()}{await self.config.api_endpoint()}"

        async with self.session.post(api_url, json=json_payload) as response:
            if response.status == 200:
                data = await response.json()
                response_message = data.get("message", {}).get("content", "Sorry, I couldn't process your request.")
                await destination.send(response_message)
            else:
                await destination.send("Error contacting the API.")

async def setup(bot):
    cog = Ollama(bot)
    bot.add_cog(cog)