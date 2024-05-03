import discord
import os
import logging

from dotenv import load_dotenv
from discord import ApplicationContext

bot = discord.Bot(intents=discord.Intents.all(),
                  activity=discord.Game(name="with numbers."))

load_dotenv()
bot_key = os.getenv('bot_key')
guild_ids = list(map(int, os.getenv('servers').split(",")))

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
                    datefmt='%H:%M:%S',
                    handlers=[
                        logging.FileHandler("bonnbot.log",
                                            mode='w',
                                            encoding='utf-8'),
                        logging.StreamHandler()
                    ])


@bot.event
async def on_ready():
    """Загрузка когов и синхронизация команд

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/events.html#discord.on_ready
    """

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
    """Логирование сообщений с указанием текстового канала

    Параметры
    ---------
    message : discord.Message
        Дискордовское сообщение

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/events.html#discord.on_message
    """

    member = message.author

    if not member.bot:
        logging.info(str(member) + " [" + str(message.channel.name) +
                     "]:" + str(message.content))


@bot.event
async def on_application_command(ctx: ApplicationContext):
    """Логирование всех вызовов команд

    Параметры
    ---------
    ctx : ApplicationContext
        Контекст взаимодействия с командой бота

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/events.html#discord.on_application_command
    """

    logging.info(str(ctx.author) + " used " + ctx.command.name + " command.")


bot.run(bot_key)
