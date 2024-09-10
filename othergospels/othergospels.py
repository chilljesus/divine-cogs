from redbot.core import commands, Config
import discord
import aiohttp
from discord import app_commands
import re
from discord.ui import View, Button, Select
import math

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
                books_per_page = 15
                total_pages = math.ceil(len(data) / books_per_page)
                #embed = format_books_text(data, page=1, books_per_page=books_per_page)
                view = BooksPaginator(data, books_per_page=books_per_page, total_pages=total_pages)
                await interaction.response.send_message(embed=view.create_embed(), view=view)
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
                embed = discord.Embed(title=f"{data.get('name')} {data.get('cite')}", description=scripture_text_formatted)
                embed.set_footer(text="Powered by othergospels.com")
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
                embed = discord.Embed(title=f"{data.get('name')} {data.get('cite')}", description=scripture_text_formatted)
                embed.set_footer(text="Powered by othergospels.com")
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to fetch random scripture.")

    @app_commands.command(name="search", description="Search scriptures with the option to include or exclude traditions.")
    async def search_command(self, interaction: discord.Interaction, query: str):
        view = SearchTraditionView()
        await interaction.response.send_message("Select the traditions to include or exclude in the search:", view=view)
        await view.wait_for_selection()
        search_url = await build_search_query(query, view.selected_includes, view.selected_excludes)
        async with self.session.get(search_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                embed = discord.Embed(title=f"Search results for '{query}'")
                for result in data.get("results", []):
                    embed.add_field(name=result.get("title", "No Title"), value=result.get("snippet", "No Snippet"), inline=False)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Failed to fetch search results from the API.")

class BooksPaginator(View):
    def __init__(self, data, books_per_page=15, total_pages=1):
        super().__init__()
        self.data = data
        self.books_per_page = books_per_page
        self.total_pages = total_pages
        self.page = 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        if self.page > 1:
            self.page -= 1
            embed = self.create_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.page < self.total_pages:
            self.page += 1
            embed = self.create_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)

    def update_buttons(self):
        self.prev_page.disabled = self.page == 1
        self.next_page.disabled = self.page == self.total_pages

    def create_embed(self):
        books_text = format_books_text(self.data, page=self.page, books_per_page=self.books_per_page)
        embed = discord.Embed(title="Available Scriptures")
        embed.description = books_text
        embed.set_footer(text=f"Powered by othergospels.com | Page {self.page}/{self.total_pages}")
        return embed

class SearchTraditionView(View):
    def __init__(self):
        super().__init__()
        self.selected_includes = []
        self.selected_excludes = []
        self.include_menu.disabled = False
        self.exclude_menu.disabled = False

    @discord.ui.select(
        placeholder="Select traditions to include...",
        min_values=0,
        max_values=3,
        options=[
            discord.SelectOption(label="Gnostic", value="gnostic_true", description="Include Gnostic tradition"),
            discord.SelectOption(label="Bible", value="bible_true", description="Include Bible tradition"),
            discord.SelectOption(label="Orthodox", value="orthodox_true", description="Include Orthodox tradition")
        ]
    )

    async def include_menu(self, select: Select, interaction: discord.Interaction):
        self.selected_includes = select.values
        self.exclude_menu.disabled = True
        await interaction.response.edit_message(content=f"Including: {', '.join([opt.label for opt in select.options if opt.value in select.values])}", view=self)

    @discord.ui.select(
        placeholder="Select traditions to exclude...",
        min_values=0,
        max_values=3,
        options=[
            discord.SelectOption(label="Gnostic", value="gnostic_false", description="Exclude Gnostic tradition"),
            discord.SelectOption(label="Bible", value="bible_false", description="Exclude Bible tradition"),
            discord.SelectOption(label="Orthodox", value="orthodox_false", description="Exclude Orthodox tradition")
        ]
    )

    async def exclude_menu(self, select: Select, interaction: discord.Interaction):
        self.selected_excludes = select.values
        self.include_menu.disabled = True
        await interaction.response.edit_message(content=f"Excluding: {', '.join([opt.label for opt in select.options if opt.value in select.values])}", view=self)

    async def wait_for_selection(self):
        await self.wait()

def clean_and_format_scripture(text, book):
    clean = re.compile('<.*?>')
    cleaned_text = re.sub(clean, '', text)
    def replace_number_with_link(match):
        number = match.group(1)
        return f"[**{number}**](https://othergospels.com/{book}/#{number})"
    formatted_text = re.sub(r"\*\*(\d+)\.\*\*", replace_number_with_link, cleaned_text)
    return formatted_text

def format_books_text(books, page=1, books_per_page=15):
    lines = []
    start_idx = (page - 1) * books_per_page
    end_idx = start_idx + books_per_page
    paginated_books = books[start_idx:end_idx]

    for book in paginated_books:
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
    return "\n".join(lines)

async def build_search_query(query, selected_includes, selected_excludes):
    base_url = f"https://othergospels.com/api/search?query={query}"
    params = []
    for option in selected_includes + selected_excludes:
        key, value = option.split("_")
        params.append(f"{key}={value}")
    if params:
        base_url += "&" + "&".join(params)
    return base_url

async def setup(bot):
    cog = OtherGospels(bot)
    bot.add_cog(cog)