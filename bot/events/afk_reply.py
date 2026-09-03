import discord
import datetime
import asyncio
import random

from discord.ext import commands, tasks

from utils import config
from utils import console

class AFKReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = config.Config()
        self.already_replied_users = set()
        self.reset_already_replied_users.start()
        
    async def handle_afk_message(self, message: discord.Message):
        afk_cfg = self.cfg.get("afk") if self.cfg.get("afk") else {"afk_response": "I'm away from the keyboard right now, I'll get back to you as soon as I can.", "afk_times": [8, 18], "enabled": False}
        
        if not afk_cfg["enabled"]:
            return
        
        current_hour = datetime.datetime.now().hour
        afk_times = afk_cfg["afk_times"]
        afk_response = afk_cfg["afk_response"]
        in_afk_time = any(start <= current_hour < end for (start, end) in [(afk_times[0], afk_times[1]), (0, 6)])
        
        if isinstance(message.channel, discord.DMChannel) and not message.author.bot and message.author.id != self.bot.user.id and in_afk_time:
            if message.author.id not in self.already_replied_users:
                self.already_replied_users.add(message.author.id)
                console.info(f"DM from {message.author}")
                console.info(f"'{message.content}'")
                
                await asyncio.sleep(random.randint(1, 3))  # Add a small delay before replying to simulate human behavior
                async with message.channel.typing():
                    await asyncio.sleep(len(afk_response) * 0.01)  # Simulate typing delay
                
                await message.reply(afk_response)
                console.info(f"Auto-replied to DM from {message.author}.")
        
    @tasks.loop(hours=24)
    async def reset_already_replied_users(self):
        self.already_replied_users.clear()
        console.info("Reset the already_replied_users set.")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        await self.handle_afk_message(message)
    
def setup(bot):
    bot.add_cog(AFKReply(bot))