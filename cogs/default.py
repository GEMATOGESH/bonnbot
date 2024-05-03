import discord
import random

from discord import option
from discord import ApplicationContext
from discord.ext import commands


def setup(bot: discord.Bot): 
    """Необходимая функция для подключения когов

    Параметры
    ---------
    bot : discord.Bot
        Дискордовский бот

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot.load_extension
    """

    bot.add_cog(Default(bot)) 
    

class Default(commands.Cog):
    """
    Класс коги с набором команд, доступных каждому пользователю

    Атрибуты
    --------
    bot : discord.Bot
        Дискордовский бот
    guild_ids : list
        Список идентификаторов серверов, к которым подключен бот

    Методы
    ------
    _roll(ctx: ApplicationContext, arg: int)
        Пишет пользователю результат подкидывания кубика от 1 до значения
        аргумента
    _flip(ctx: ApplicationContext)
        Пишет пользователю результат подкидывания монетки
    """

    guild_ids = []

    def __init__(self, bot: discord.Bot):
        """
        Параметры
        ----------
        bot : discord.Bot
            Дискордовский бот
        """

        self.bot = bot

        for guild in bot.guilds:
            self.guild_ids.append(guild.id)


    @commands.slash_command(name="roll", description="Кидает кубик от 1 до значения аргумента.")
    @option("arg", int, description="До скольки?")
    async def _roll(self, ctx: ApplicationContext, arg: int):
        """Подкидывание кубика от 1 до значения аргумента

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        arg : int
            Максимальное значение кубика        
        """

        num = random.randint(1, arg)
        message = "Все мы игрушки в руках судьбы, <...> и теперь наше "\
            "будущее зависит от того, как лягут игральные кости."\
            "Не дрогнет ли рука провидения?... \n"
        message += "Выпало " + str(num)

        match num:
            case 1:
                message += ". Кол!"
            case 3:
                message += ". Трое!"
            case 10:
                message += ". Бычий глаз!"
            case 11:
                message += ". Барабанные палочки!"
            case 12:
                message += ". Дюжина!"
            case 13:
                message += ". Чертова дюжина!"
            case 18:
                message += ". В первый раз!"
            case 22:
                message += ". Утята!"
            case 25:
                message += ". Опять 25!"
            case 44:
                message += ". Стульчики!"
            case 50:
                message += ". Полста!"
            case 55:
                message += ". Перчатки!"
            case 66:
                message += ". Валенки!"
            case 69:
                message += ". Nice!"
            case 77:
                message += ". Топорики!"
            case 88:
                message += ". Бабушка!"
            case 89:
                message += ". Дедушкин сосед!"
            case 90:
                message += ". Дедушка!"

        await ctx.respond(message)


    @commands.slash_command(name="flip", description="Подкидывает монетку.")
    async def _flip(self, ctx: ApplicationContext):
        """Подкидывание монетки

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        num = random.randint(0, 1)

        message = "Счастье и горе — это две стороны монеты, "\
            "которую жизнь периодически ставит на ребро...\n"

        if not num:
            message += ctx.author.mention + ", выпал орел!"
        elif num:
            message += ctx.author.mention + ", выпала режка!"
        else:
            message += "Выпало... ребро?"
        
        await ctx.respond(message)
