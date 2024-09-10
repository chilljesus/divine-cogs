from redbot.core import commands, Config
import discord
import aiohttp
from discord import app_commands
import re

class OtherGospels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=20240203, force_registration=True)
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="ogospels")
    async def othergospels(self, ctx):
        """OtherGospels configuration commands."""
        pass

    @app_commands.command(name="help", description="Get command usage and info.")
    async def help(self, interaction: discord.Interaction):
        # Create an embed showing the commands and their usage
        embed = discord.Embed(title="OtherGospels Commands", description="List of available commands:")
        embed.add_field(name="/books", value="Get a list of available books.")
        embed.add_field(name="/daily", value="Get the daily scripture.")
        embed.add_field(name="/random", value="Get a random scripture.")
        embed.add_field(name="/search", value="Search for specific scriptures.")
        embed.set_image(url="https://small.fileditchstuff.me/s11/FsVJWkFplszyjIKhmNjt.gif")
        embed.set_footer(text="@nekojesus • https://jesus.sh")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="books", description="Get a list of available scriptures")
    async def books(self, interaction: discord.Interaction):
        async with self.session.get("https://othergospels.com/api/books") as resp:
            if resp.status == 200:
                data = await resp.json()
                books_text = format_books_text(data, max_lines=15)
                embed = discord.Embed(title="Available Scriptures")
                embed.description = books_text
                embed.set_footer(text="Showing the first 15 books.")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to fetch books from the API.", ephemeral=True)


    @app_commands.command(name="daily", description="Get the daily scripture.")
    async def daily(self, interaction: discord.Interaction):
        async with self.session.get("https://othergospels.com/api/daily") as resp:
            if resp.status == 200:
                data = await resp.json()
                scripture_text = data.get("text", "")
                book = data.get("book", "")
                scripture_text_formatted = clean_and_format_scripture(scripture_text, book)
                embed = discord.Embed(title="Daily Scripture", description=scripture_text_formatted)
                embed.set_footer(text=f"{data.get('name')} {data.get('cite')}")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to fetch daily scripture.")

    @app_commands.command(name="random", description="Get a random scripture.")
    async def random(self, interaction: discord.Interaction):
        async with self.session.get("https://othergospels.com/api/random") as resp:
            if resp.status == 200:
                data = await resp.json()
                scripture_text = data.get("text", "")
                book = data.get("book", "")
                scripture_text_formatted = clean_and_format_scripture(scripture_text, book)
                embed = discord.Embed(title="Random Scripture", description=scripture_text_formatted)
                embed.set_footer(text=f"{data.get('name')} {data.get('cite')}")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to fetch random scripture.")

def clean_and_format_scripture(text, book):
    clean = re.compile('<.*?>')
    cleaned_text = re.sub(clean, '', text)
    def replace_number_with_link(match):
        number = match.group(1)
        return f"[**{number}**](https://othergospels.com/{book}/{number})"
    formatted_text = re.sub(r"\*\*(\d+)\*\*", replace_number_with_link, cleaned_text)
    return formatted_text

def format_books_text(books, max_lines=15):
    lines = []
    for book in books:
        display_name = book.get("fullName", book.get("name"))
        url = f"https://othergospels.com/{book['url']}"
        categories = []
        if book.get("gnostic"):
            categories.append("Gnostic")
        if book.get("orthodox"):
            categories.append("Orthodox")
        if book.get("bible"):
            categories.append("Bible")
        categories_str = ', '.join(categories) if categories else 'Unknown'
        other_names_list = []
        if book.get("name") and book.get("name") != display_name:
            other_names_list.append(book["name"])
        if book.get("aka"):
            other_names_list.extend(book["aka"])
        other_names = f"(Other names: {', '.join(other_names_list)})" if other_names_list else ""
        line = f"[{display_name}]({url}) - {categories_str} {other_names}"
        lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)

async def setup(bot):
    cog = OtherGospels(bot)
    bot.add_cog(cog)