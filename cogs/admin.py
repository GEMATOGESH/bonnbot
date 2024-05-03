import discord
import os
import images

from discord import option
from discord import ApplicationContext
from discord.ext import commands
from dotenv import load_dotenv


def setup(bot: discord.bot.Bot): 
    """Необходимая функция для подключения когов

    Параметры
    ---------
    bot : discord.Bot
        Дискордовский бот

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot.load_extension
    """

    bot.add_cog(Admin(bot)) 
    

class Admin(commands.Cog):
    """
    Класс коги с набором команд, доступных только администраторам

    Атрибуты
    --------
    bot : discord.Bot
        Дискордовский бот
    guild_ids : list
        Список идентификаторов серверов, к которым подключен бот
    owner_id : str
        Идентификатор владельца бота, для работы команды say

    Методы
    ------
    _say(self, ctx: ApplicationContext, message: str, file: str)
        Команда, которая отправляет сообщение от имени бота
    _mute(self, ctx: ApplicationContext, switch: str)
        Команда, которая мутит всех пользователей в голосовом канале,
        кроме администраторов
    _move(self, ctx: ApplicationContext, channel: discord.VoiceChannel)
        Перемещает всех пользователей в голосовом канале, в другой
        голосовой канал на выбор
    """

    guild_ids = []

    def __init__(self, bot: discord.bot.Bot):
        """
        Параметры
        ---------
        bot : discord.Bot
            Дискордовский бот
        """

        self.bot = bot

        for guild in bot.guilds:
            self.guild_ids.append(guild.id)

        load_dotenv()
        self.owner_id = os.getenv('owner_id')


    @commands.slash_command(name="say", description="Команда для владельца, позволяет отправить сообщение от имени бота.")
    @discord.default_permissions(administrator=True)
    @option("message", description="Сообщение, которое отправится от имени бота.", required=True)
    @option("file", description="Дополнительный файл к сообщению.", required=False)
    async def _say(self, ctx: ApplicationContext, message: str, file: str):
        """Отправка сообщения от имени бота, с опциональным прикреплением
        файлов

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        message : str
            Сообщение на отправку
        file : str
            Имя файла, который нужно прикрепить к сообщению, опционально
        """

        if str(ctx.author.id) == self.owner_id:
            if file is not None:
                await ctx.send(message, 
                               file=discord.File("images\\say\\" + file))
            else:
                await ctx.send(message)


    @commands.slash_command(name="mute", guild_ids=guild_ids, description="Управление микрофоном всех пользователей в текущем голосовом канале.")
    @discord.default_permissions(administrator=True)
    @option("switch", description="Вкл/Выкл?", choices=["on", "off"])
    async def _mute(self, ctx: ApplicationContext, switch: str):
        """Выключает или включает микрофон всех пользователей в голосовом
        канале

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        switch : str
            Выбор выключения или включения микрофонов
        """

        channel = ctx.author.voice.channel
        members = channel.members

        if switch == "on":
            file = images.get_random_image("images\\mute\\")
            if file is not None:
                await ctx.respond(file=file)
            else:
                await ctx.respond("Помолчим.")

            for member in members:
                if not member.guild_permissions.administrator:
                    await member.edit(mute=True)

        elif switch == "off":
            await ctx.respond("Да будет звук.")
            for member in members:
                if not member.guild_permissions.administrator:
                    await member.edit(mute=False)


    @commands.slash_command(name="move", guild_ids=guild_ids, description="Перемещает всех пользователей текущего канала в выбранный голосовой канал.")
    @discord.default_permissions(administrator=True)
    @option("channel", discord.VoiceChannel, description="Куда? (Если не нашел желаемый канал - можно использовать ID)")
    async def _move(self, ctx: ApplicationContext, channel: discord.VoiceChannel):
        """Перемещение всех пользователей в текущем голосовом канале в 
        канал на выбор

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        channel : discord.VoiceChannel
            Голосовой канал, куда бот всех переместит
        """

        current_channel = ctx.author.voice.channel
        members = current_channel.members
        guild = self.bot.get_guild(ctx.guild.id)

        file = images.get_random_image("images\\move\\")
        if file is not None:
            await ctx.respond("Переезд в " + channel.mention, file=file)
        else:
            await ctx.respond("Переезд в " + channel.mention)

        for member in members:
            user = await guild.fetch_member(member.id)
            await user.move_to(channel)