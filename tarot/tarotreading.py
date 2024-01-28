import os
import json
import random
import discord
from typing import Optional
from datetime import datetime
from redbot.core import commands

class TarotReading(commands.Cog):
    """Tarot card reading cog"""

    def __init__(self, bot):
        self.bot = bot

    def get_card_path(self, deck_name):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cards_path = os.path.join(dir_path, 'cards', f'{deck_name}.json')
        return cards_path

    def list_decks(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cards_path = os.path.join(dir_path, 'cards')
        return [f.replace('.json', '') for f in os.listdir(cards_path) if f.endswith('.json')]

    @commands.hybrid_command(name="tarot", description="Perform a tarot reading")
    async def _tarot(self, ctx, deck: Optional[str] = None, user: Optional[discord.Member] = None):
        """Performs a tarot reading. Optionally specify a deck and a user."""
        user = user or ctx.author
        if deck and deck not in self.list_decks():
            deck = random.choice(self.list_decks())
        deck = deck or random.choice(self.list_decks())
        card = await self.get_random_card(deck)
        position = random.choice(['upright', 'reversed'])        
        embed = discord.Embed(title=card['card_name'],
                      url=card['card_url'],
                      colour=0xffc0cb,
                      timestamp=datetime.now())

        embed.set_author(name=f"Reading for {user.display_name}", icon_url=user.display_avatar)
        embed.add_field(name="Card Description", value=card['card_meaning'], inline=True)
        embed.add_field(name=f"{position} Meaning", value=card[f"{position}_meaning"], inline=True)
        embed.set_thumbnail(url=card['card_image'])
        embed.set_footer(text=f"Deck: {deck}", icon_url="https://nekoism.co/images/logo-small.png")
        
        await ctx.send(embed=embed)

    async def get_random_card(self, deck_name):
        card_path = self.get_card_path(deck_name)
        with open(card_path, 'r') as file:
            deck = json.load(file)
            card_name = random.choice(list(deck.keys()))
            return deck[card_name]

