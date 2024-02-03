from redbot.core.bot import Red

from .core import StableDiffusion

async def setup(bot: Red) -> None:
    cog = Ollama(bot)
    await bot.add_cog(cog)
