import discord
import os
import time
import random
import logging

from discord import option
from dotenv import load_dotenv

# Инициализация бота.
bot = discord.Bot(intents=discord.Intents.all(), activity=discord.Game(name="with numbers."))

# Подтягивание информации из .env.
load_dotenv()
bot_key = os.getenv('bot_key')
owner_id = os.getenv('owner_id')
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
        'coalition'
    ]

    for cog in cogs_list:
        bot.load_extension(f'cogs.{cog}')
        logging.info(cog + " cog loaded.")
    
    await bot.sync_commands(guild_ids=["192581088592265216"])

    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info('------')


@bot.event
async def on_message(message):
    member = message.author
            
    if not member.bot:
        t = time.localtime()
        logging.info(str(member) + ":" + str(message.content))
        logging.info('------')


@bot.slash_command(name="say", description="Команда для владельца, позволяет отправить сообщение от имени бота.") # ID владельца подтягивается из .env
@option("file", description="Дополнительный файл к сообщению.", required=False)
async def _say(ctx, args, file):
    if ctx.author.id == owner_id:
        message = ""
        for piece in args:
            message += str(piece)

        if file is not None:
            await ctx.send(message, file=discord.File("images\\" + file))
        else:
            await ctx.send(message)


@bot.slash_command(name="roll", description="Кидает кубик от 1 до значения аргумента.")
@option("arg", description="До скольки?")
async def _roll(ctx, arg):
    if not arg.isnumeric():
        await ctx.respond("Мы используем десятичную СС, а не счет древних русов.")
        return

    num = random.randint(1, int(arg))
    message = "Все мы игрушки в руках судьбы, <...> и теперь наше будущее зависит от того, как лягут игральные кости."\
        "Не дрогнет ли рука провидения?... \n"
    message += "Выпало " + str(num)

    if num == 1:
        message += ". Кол!"
    elif num == 3:
        message += ". Трое!"
    elif num == 10:
        message += ". Бычий глаз!"
    elif num == 11:
        message += ". Барабанные палочки!"
    elif num == 12:
        message += ". Дюжина!"
    elif num == 13:
        message += ". Чертова дюжина!"
    elif num == 18:
        message += ". В первый раз!"
    elif num == 22:
        message += ". Утята!"
    elif num == 25:
        message += ". Опять 25!"
    elif num == 44:
        message += ". Стульчики!"
    elif num == 50:
        message += ". Полста!"
    elif num == 55:
        message += ". Перчатки!"
    elif num == 66:
        message += ". Валенки!"
    elif num == 69:
        message += ". Nice!"
    elif num == 77:
        message += ". Топорики!"
    elif num == 88:
        message += ". Бабушка!"
    elif num == 89:
        message += ". Дедушкин сосед!"
    elif num == 90:
        message += ". Дедушка!"

    await ctx.respond(message)


@bot.slash_command(name="flip", description="Подкидывает монетку.")
async def _flip(ctx):
    num = random.randint(0, 1)

    message = "Счастье и горе — это две стороны монеты, которую жизнь периодически ставит на ребро...\n"

    if num:
        message += ctx.author.mention + ", выпал орел!"
    elif num:
        message += ctx.author.mention + ", выпала режка!"
    else:
        message += "Выпало... ребро?"

    await ctx.respond(message)


@bot.slash_command(name="mute", guild_ids=guild_ids, description="Упралвение микрофоном всех пользователей в текущем голосовом канале.")
@option("switch", description="Вкл/Выкл?", choices=["on", "off"])
async def _mute(ctx, switch):
    if ctx.author.guild_permissions.administrator:
        channel = ctx.author.voice.channel
        members = channel.members

        if switch == "on":
            await ctx.send(file=discord.File("images\\mute\\" + random.choice(os.listdir("images\\mute"))))
            for member in members:
                if not member.guild_permissions.administrator:
                    await member.edit(mute=True)

        elif switch == "off":
            await ctx.send("Да будет звук.")
            for member in members:
                if not member.guild_permissions.administrator:
                    await member.edit(mute=False)


@bot.slash_command(name="move", guild_ids=guild_ids, description="Перемещает всех пользователей текущего канала в выбранный голосовой канал.")
@option("channel", discord.VoiceChannel, description="Куда? (Если не нашел желаемый канал можно использовать ID)")
async def _move(ctx, channel):
    if ctx.author.guild_permissions.administrator:
        current_channel = ctx.author.voice.channel
        members = current_channel.members
        guild = bot.get_guild(ctx.guild.id)

        await ctx.send("Переезд в " + channel.mention, file=discord.File(("images\\move\\" + random.choice(os.listdir("images\\move")))))

        for member in members:
            user = await guild.fetch_member(member.id)
            await user.move_to(channel)


bot.run(bot_key)
