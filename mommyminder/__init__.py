from redbot.core.bot import Red

from .mommyminder import MommyMinder

async def setup(bot: Red) -> None:
    cog = MommyMinder(bot)
    await bot.add_cog(cog)
