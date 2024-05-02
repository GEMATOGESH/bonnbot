import discord
import random

from discord import option
from discord.ext import commands
from discord.commands.context import ApplicationContext


def setup(bot: discord.bot.Bot): 
    bot.add_cog(Default(bot)) 
    

class Default(commands.Cog):    
    guild_ids = []

    def __init__(self, bot: discord.bot.Bot):
        self.bot = bot

        for guild in bot.guilds:
            self.guild_ids.append(guild.id)


    @commands.slash_command(name="roll", description="Кидает кубик от 1 до значения аргумента.")
    @option("arg", int, description="До скольки?")
    async def _roll(self, ctx: ApplicationContext, arg: int):
        num = random.randint(1, arg)
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


    @commands.slash_command(name="flip", description="Подкидывает монетку.")
    async def _flip(self, ctx: ApplicationContext):
        num = random.randint(0, 1)

        message = "Счастье и горе — это две стороны монеты, которую жизнь периодически ставит на ребро...\n"

        if not num:
            message += ctx.author.mention + ", выпал орел!"
        elif num:
            message += ctx.author.mention + ", выпала режка!"
        else:
            message += "Выпало... ребро?"

        await ctx.respond(message)
