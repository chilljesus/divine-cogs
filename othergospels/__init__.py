from redbot.core.bot import Red

from .othergospels import OtherGospels

async def setup(bot: Red) -> None:
    cog = OtherGospels(bot)
    await bot.add_cog(cog)
