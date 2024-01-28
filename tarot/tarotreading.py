from redbot.core import commands
import discord
import random
import json
import os

class TarotReading(commands.Cog):
    """Tarot card reading cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="tarot", description="Perform a tarot reading")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def _tarot(self, ctx, deck: str = None, user: discord.Member = None):
        """Performs a tarot reading. Optionally specify a deck and a user."""
        user = user or ctx.author
        deck = deck or random.choice(os.listdir('./cards/')).replace('.json', '')
        card = await self.get_random_card(deck)

        embed = discord.Embed(title=f"Tarot Reading for {user.display_name}", description=f"Deck: {deck}")
        embed.add_field(name=card['card_name'], value=card['card_meaning'], inline=False)
        embed.set_image(url=card['card_image'])
        await ctx.send(embed=embed)

    async def get_random_card(self, deck_name):
        with open(f'./cards/{deck_name}.json', 'r') as file:
            deck = json.load(file)
            card_name = random.choice(list(deck.keys()))
            return deck[card_name]

