from redbot.core import commands
import discord
import aiohttp
import re
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import SimpleMenu
from typing import Optional

class OtherGospels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.hybrid_command(name="ogospels")
    async def help_command(self, ctx):
        embed = discord.Embed(title="OtherGospels Commands", description="Available commands:")
        embed.add_field(name="/books", value="Get a list of available books.")
        embed.add_field(name="/daily", value="Get the daily scripture.")
        embed.add_field(name="/random", value="Get a random scripture.")
        embed.add_field(name="/search", value="Search for specific scriptures.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="books")
    async def books_command(self, ctx):
        """Get a list of available scriptures"""
        async with self.session.get("https://othergospels.com/api/books") as resp:
            if resp.status == 200:
                data = await resp.json()
                books_text = self.format_books_text(data)
                pages = list(pagify(books_text, page_length=1024))
                if len(pages) > 1:
                    await SimpleMenu(pages).start(ctx)
                else:
                    await ctx.send(pages[0])
            else:
                await ctx.send("Failed to fetch books from the API.")

    @commands.hybrid_command(name="daily")
    async def daily_command(self, ctx):
        """Get the daily scripture"""
        await self.send_scripture(ctx, "https://othergospels.com/api/daily", "Daily Scripture")

    @commands.hybrid_command(name="random")
    async def random_command(self, ctx):
        """Get a random scripture"""
        await self.send_scripture(ctx, "https://othergospels.com/api/random", "Random Scripture")

    @commands.hybrid_command(name="search")
    async def search_command(self, ctx, query: str, exclude_options: Optional[str] = None):
        """Search for scriptures with options to exclude traditions"""
        search_url = await self.build_search_query(query, exclude_options)
        async with self.session.get(search_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                passages = "\n\n".join([self.clean_and_format_scripture(p['text'], p['name']) for p in data.get("passages", [])])
                pages = list(pagify(passages, page_length=1024))
                if len(pages) > 1:
                    await SimpleMenu(pages).start(ctx)
                else:
                    await ctx.send(pages[0])
            else:
                await ctx.send("Failed to fetch search results from the API.")

    async def send_scripture(self, ctx, url, title):
        """Helper function to fetch and send scripture"""
        async with self.session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                formatted_text = self.clean_and_format_scripture(data.get("text", ""), data.get("book", ""))
                embed = discord.Embed(title=f"{data.get('name')} {data.get('cite')}", description=formatted_text)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Failed to fetch {title.lower()}.")

    def clean_and_format_scripture(self, text, book, urls=None):
        """Format scripture text and replace numbers with links"""
        text = re.sub(r"<.*?>", "", text)
        return re.sub(r"\*\*(\d+)\.\*\*", lambda match: f"[**{match.group(1)}**](<https://othergospels.com/{book}/{match.group(1)}>)", text)

    def format_books_text(self, books):
        """Format the list of books, including alternative names (aka)"""
        return "\n".join(
            f"[{book.get('fullName', book.get('name'))}]"
            f"(<https://othergospels.com/{book['url']}>)"
            f" - {', '.join([cat for cat in ['Gnostic', 'Orthodox', 'Bible'] if book.get(cat.lower())])}"
            f"{' (Other names: ' + ', '.join(book['aka']) + ')' if 'aka' in book and book['aka'] else ''}"
            for book in books
        )

    async def build_search_query(self, query, exclude_options):
        """Build the search query with exclude options"""
        params = {"gnostic": "true", "orthodox": "true", "bible": "true"}
        if exclude_options:
            for opt in exclude_options:
                params[opt] = "false"
        param_str = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"https://othergospels.com/api/search?query={query}&{param_str}"

async def setup(bot):
    bot.add_cog(OtherGospels(bot))
