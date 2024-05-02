import discord
import os
import logging

from dotenv import load_dotenv
from discord.commands.context import ApplicationContext

# Инициализация бота.
bot = discord.Bot(intents=discord.Intents.all(), activity=discord.Game(name="with numbers."))

load_dotenv()
bot_key = os.getenv('bot_key')
guild_ids = list(map(int, os.getenv('servers').split(",")))

logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[
                        logging.FileHandler("bonnbot.log", mode='w', encoding='utf-8'),
                        logging.StreamHandler()
                    ])


@bot.event
async def on_ready():
    cogs_list = [
        'music',
        'coalition',
        'admin',
        'default'
    ]

    for cog in cogs_list:
        bot.load_extension(f'cogs.{cog}')
        logging.info(cog.title() + " cog loaded.")
    
    await bot.sync_commands(guild_ids=guild_ids)

    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info('------')


@bot.event
async def on_message(message: discord.Message):
    member = message.author
            
    if not member.bot:
        logging.info(str(member) + ":" + str(message.content))


@bot.event
async def on_application_command(ctx: ApplicationContext):
    logging.info(str(ctx.author) + " used " + ctx.command.name + " command.")


bot.run(bot_key)
