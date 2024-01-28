from redbot.core import commands
import discord
from discord.ext.commands import BadArgument
import random
import json
import os
from datetime import datetime

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
    #async def _tarot(self, ctx, deck: str = None, user: discord.Member = None):
    async def _tarot(self, ctx, *, arg=None):
        user = ctx.author
        deck = random.choice(self.list_decks())
        if arg:
            args = arg.split()
            for a in args:
                try:
                    # Attempt to convert each argument to a Discord member
                    potential_user = await commands.MemberConverter().convert(ctx, a)
                    user = potential_user
                except BadArgument:
                    # If not a user, check if it's a deck name
                    if a in self.list_decks():
                        deck = a
        else:
            deck = random.choice(self.list_decks())

        user = user or ctx.author
        
        #user = user or ctx.author
        #deck = deck or random.choice(self.list_decks())

        card = await self.get_random_card(deck)

        embed = discord.Embed(title=card['card_name'],
                      url=card['card_url'],
                      colour=0xffc0cb,
                      timestamp=datetime.now())

        embed.set_author(name=f"Reading for {user.display_name}", icon_url=user.display_avatar)
        embed.add_field(name="Card Description", value=card['card_meaning'], inline=True)
        embed.add_field(name="Upright Meaning", value=card['upright_meaning'], inline=True)
        embed.set_thumbnail(url=card['card_image'])
        embed.set_footer(text=f"Deck: {deck}", icon_url="https://nekoism.co/images/logo-small.png")
        
        await ctx.send(embed=embed)

    async def get_random_card(self, deck_name):
        card_path = self.get_card_path(deck_name)
        with open(card_path, 'r') as file:
            deck = json.load(file)
            card_name = random.choice(list(deck.keys()))
            return deck[card_name]

