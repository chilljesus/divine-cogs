from redbot.core import commands, Config
import discord
import aiohttp
from discord import app_commands, Interaction
import re
from discord.ui import View, Button, Select
import math
from typing import Optional

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

    @app_commands.command(name="search", description="Search scriptures with options to include or exclude traditions.")
    @app_commands.describe(
        query="The search query (e.g., a phrase, word, or reference)",
        #include_options="Traditions to include in the search",
        exclude_options="Traditions to exclude from the search"
    )
    async def search_command(
        self,
        interaction: Interaction,
        query: str,
        #include_options: Optional[str] = None,
        exclude_options: Optional[str] = None
    ):
        #if include_options and exclude_options:
        #    await interaction.response.send_message("You can only choose to either include or exclude traditions, not both.", ephemeral=True)
        #    return
        #include_list = [include_options] if include_options else []
        exclude_list = [exclude_options] if exclude_options else []
        search_url = await build_search_query(query, exclude_list)

        async with self.session.get(search_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                passages = data.get("passages", [])
                urls = data.get("urls", {})
                if not passages:
                    await interaction.response.send_message("No results found.", ephemeral=True)
                    return
                view = SearchPaginator(passages, urls)
                embed = view.create_embed()
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("Failed to fetch search results from the API.", ephemeral=True)

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

class SearchPaginator(View):
    def __init__(self, data, urls, passages_per_page=8):
        super().__init__()
        self.data = data
        self.urls = urls
        self.page = 0
        if len(data) == 1:
            self.passage_text = data[0]['text']
            self.passage_name = data[0]['name']
            self.passage_ref = data[0]['ref']
            self.passage_url = urls.get(self.passage_name, '')
            self.numbered_sections = re.split(r"(\*\*\d+\.\*\*)", self.passage_text)
            self.sections = [
                f"{self.numbered_sections[i]}{self.numbered_sections[i+1]}"
                for i in range(1, len(self.numbered_sections) - 1, 2)
            ]
            self.title = re.sub(r'\*\*\d+\.\*\*', '', self.numbered_sections[0]).strip()
            self.verses_per_page = 8
            self.total_pages = math.ceil(len(self.sections) / self.verses_per_page)
            self.paginate_by_verses = True
        else:
            self.paginate_by_verses = False
            self.passages_per_page = passages_per_page
            self.total_pages = math.ceil(len(data) / passages_per_page)

        self.update_buttons()

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        if self.page > 0:
            self.page -= 1
            embed = self.create_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            embed = self.create_embed()
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)

    def update_buttons(self):
        self.prev_page.disabled = self.page == 0
        self.next_page.disabled = self.page >= self.total_pages - 1

    def create_embed(self):
        embed = discord.Embed(title=f"Search Results (Page {self.page + 1}/{self.total_pages})")
        if self.paginate_by_verses:
            start_idx = self.page * self.verses_per_page
            end_idx = start_idx + self.verses_per_page
            paginated_sections = self.sections[start_idx:end_idx]
            formatted_text = "".join(paginated_sections)
            formatted_text = clean_and_format_scripture(
                formatted_text,
                self.passage_name,
                self.urls
            )
            embed.add_field(
                name=f"{self.passage_name} {self.passage_ref} - {self.title}",
                value=formatted_text,
                inline=False
            )
        else:
            start_idx = self.page * self.passages_per_page
            end_idx = start_idx + self.passages_per_page
            paginated_passages = self.data[start_idx:end_idx]
            for passage in paginated_passages:
                formatted_text = clean_and_format_scripture(
                    passage['text'],
                    passage['name'],
                    self.urls
                )
                embed.add_field(name=f"{passage['name']} {passage['ref']}", value=formatted_text, inline=False)
        return embed

def clean_and_format_scripture(text, book, urls=None):
    clean = re.compile('<.*?>')
    cleaned_text = re.sub(clean, '', text)
    def replace_number_with_link(match):
        number = match.group(1)
        if urls and book in urls:
            url = f"https://othergospels.com/{urls[book]}/#{number}"
        else:
            url = f"https://othergospels.com/{book}/#{number}"
        return f"[**{number}**]({url})"
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

async def build_search_query(query, exclude_options):
    params = {
        "gnostic": "true",
        "orthodox": "true",
        "bible": "true"
    }
    if exclude_options:
        for opt in exclude_options:
            if opt in params:
                params[opt] = "false"
    base_url = f"https://othergospels.com/api/search?query={query}"
    param_str = "&".join([f"{key}={value}" for key, value in params.items()])
    base_url += "&" + param_str

    print(base_url)
    return base_url

async def setup(bot):
    cog = OtherGospels(bot)
    bot.add_cog(cog)