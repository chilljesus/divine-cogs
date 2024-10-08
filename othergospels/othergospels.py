from redbot.core import commands
import discord
import aiohttp
import re
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import SimpleMenu
from typing import Optional
from discord import app_commands

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

    @app_commands.choices(
        exclude_options=[
            app_commands.Choice(name="gnostic", value="gnostic"),
            app_commands.Choice(name="orthodox", value="orthodox"),
            app_commands.Choice(name="bible", value="bible")
        ]
    )
    @commands.hybrid_command(name="search")
    async def search_command(self, ctx, query: str, exclude_options: Optional[str] = None):
        """Search for scriptures and display passages per page in fields or embed descriptions based on ref format"""
        search_url = await self.build_search_query(query, exclude_options)
        print(search_url)
        async with self.session.get(search_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                passages = data.get("passages", [])
                urls = data.get("urls", {})
                if not passages:
                    await ctx.send("No results found.")
                    return
                embeds = []
                char_count = 0
                current_embed = None
                char_count = 0

                for passage in passages:
                    formatted_text = self.clean_and_format_scripture(passage['text'], passage['name'], passage['ref'], urls)
                    field_title = f"{passage['name']} {passage['ref']}"
                    print(passage['ref'])
                    if ':' not in passage['ref']:
                        #formatted_text_lines = formatted_text.split("\n")
                        #formatted_text = "\n".join(formatted_text_lines)
                        for page in pagify(formatted_text, page_length=2500):
                            if current_embed is None:
                                current_embed = discord.Embed(title=f"{passage['name']} {passage['ref']}")
                                char_count = 0 
                            if char_count + len(page) > 2500:
                                embeds.append(current_embed)
                                current_embed = discord.Embed(title=f"{passage['name']} {passage['ref']}") 
                                char_count = 0 
                            current_embed.description = (current_embed.description or "") + page
                            char_count += len(page)
                    else:
                        for page in pagify(formatted_text, page_length=2500):
                            if current_embed is None:
                                current_embed = discord.Embed(title="Search Results")
                                char_count = 0 
                            if len(current_embed.fields) >= 7 or char_count + len(page) >= 2500:
                                embeds.append(current_embed) 
                                current_embed = discord.Embed(title="Search Results")
                                char_count = 0 
                            current_embed.add_field(name=field_title, value=page, inline=False)
                            char_count += len(page)
                if current_embed and (current_embed.fields or current_embed.description):
                    embeds.append(current_embed)

                if len(current_embed.fields) > 0 or current_embed.description:
                    embeds.append(current_embed)
                await SimpleMenu(embeds).start(ctx)
            else:
                await ctx.send("Failed to fetch search results from the API.")


    async def send_scripture(self, ctx, url, title):
        """Helper function to fetch and send scripture"""
        async with self.session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                formatted_text = self.clean_and_format_scripture(data.get("text", ""), data.get("book", ""), data.get("ref", ""))
                embed = discord.Embed(title=f"{data.get('name')} {data.get('ref')}", description=formatted_text)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Failed to fetch {title.lower()}.")

    def clean_and_format_scripture(self, text, book, ref, urls=None):
        """Clean and format the scripture text, replacing numbers with links using the ref"""
        clean = re.compile('<.*?>')
        cleaned_text = re.sub(clean, '', text)
        print(ref)
        def replace_number_with_link(match):
            number = match.group(1)
            if ':' in ref:
                link_ref = ref
            else:
                link_ref = f"{ref}:{number}"
            if urls and book in urls:
                url = f"https://othergospels.com/{urls[book]}/#{link_ref}"
            else:
                url = f"https://othergospels.com/{book}/#{link_ref}"
            print(url)
            return f"[**{number}.**](<{url}>)"
        formatted_text = re.sub(r"\*\*(\d+)\.\*\*", replace_number_with_link, cleaned_text)
        return formatted_text

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
        print(exclude_options)
        """Build the search query and exclude any options specified"""
        params = {"gnostic": "true", "orthodox": "true", "bible": "true"}
        if exclude_options:
            for opt in exclude_options:
                if opt in params:
                    del params[opt]
        param_str = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"https://othergospels.com/api/search?query={query}&{param_str}"


async def setup(bot):
    bot.add_cog(OtherGospels(bot))
