from redbot.core.bot import Red

from .ollama import Ollama

async def setup(bot: Red) -> None:
    cog = Ollama(bot)
    await bot.add_cog(cog)
