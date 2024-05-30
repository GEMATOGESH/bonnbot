import discord
import os
import images
import datetime

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
    guild_ids : list
        Список идентификаторов серверов, к которым подключен бот

    Методы
    ------
    _say(ctx: ApplicationContext, message: str, file: str)
        Команда, которая отправляет сообщение от имени бота
    _mute(ctx: ApplicationContext, user: discord.Member)
        Выключает микрофон пользователю, включает если он был выключен 
        до этого
    _mute_all(ctx: ApplicationContext, switch: str)
        Команда, которая мутит всех пользователей в голосовом канале,
        кроме администраторов
    _move(ctx: ApplicationContext, channel: discord.VoiceChannel)
        Перемещает всех пользователей в голосовом канале, в другой
        голосовой канал на выбор
    _kick(ctx: ApplicationContext, user: discord.Member)
        Кикает пользователя с сервера
    _ban(ctx: ApplicationContext, user: discord.Member)
        Банит пользователя с сервера
    _timeout(ctx: ApplicationContext, user: discord.Member, timestamp: str)
        Временное ограничение доступа к серверу определенному пользователю
    _avatar_user(self, ctx: ApplicationContext, user: discord.Member, type: str)
        Получение аватара пользователя
    _avatar_guild(self, ctx: ApplicationContext)
        Получение аватара текущего сервера
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
            
    @commands.slash_command(name="mute", guild_ids=guild_ids, description="Выключает микрофон пользователя, включает если был выключен до этого.")
    @discord.default_permissions(administrator=True)
    @option("user", discord.Member, description="Пользователь на выбор, если нет в списке, можно использовать идентификатор пользователя.")
    async def _mute(self, ctx: ApplicationContext, user: discord.Member):
        """Выключает микрофон пользователя, если он уже был выключен - 
        включает его

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        user : discord.Member
            Пользователь, которому выключит/включит микрофон
        """

        embed = None
        if user.voice.mute:
            await user.edit(mute=False)
            
            embed = discord.Embed(title="Исходящий звук",
                                  color=discord.Colour.green(),
                                  description=f"Включил микрофон {user.mention}.")
        else:
            await user.edit(mute=True)
            
            embed = discord.Embed(title="Исходящий звук",
                                  color=discord.Colour.red(),
                                  description=f"Выключил микрофон {user.mention}.")
        
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="mute_all", guild_ids=guild_ids, description="Управление микрофоном всех (кроме администраторов) пользователей в текущем голосовом канале.")
    @discord.default_permissions(administrator=True)
    @option("switch", description="Вкл/Выкл?", choices=["on", "off"])
    async def _mute_all(self, ctx: ApplicationContext, switch: str):
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
            embed = discord.Embed(title=":microphone2: Выключил всем микрофоны.",
                                  color=discord.Colour.red())
            await ctx.respond(embed=embed)
            
            file = images.get_random_image("images\\mute\\")
            if file is not None:
                await ctx.send(file=file)

            for member in members:
                if not member.guild_permissions.administrator:
                    await member.edit(mute=True)

        elif switch == "off":
            embed = discord.Embed(title=":microphone2: Включил всем микрофоны.",
                                  color=discord.Colour.green())
            await ctx.respond(embed=embed)
            
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

        embed = discord.Embed(title=f":airplane_arriving: Переезд в {channel.mention}.",
                              color=discord.Colour.blurple())
        await ctx.respond(embed=embed)
        
        file = images.get_random_image("images\\move\\")
        if file is not None:
            await ctx.send(file=file)
            
        for member in members:
            user = await guild.fetch_member(member.id)
            await user.move_to(channel)
            
    @commands.slash_command(name="kick", guild_ids=guild_ids, description="Выгоняет пользователя с сервера с возможностью возвращения по приглашению.")
    @discord.default_permissions(administrator=True)
    @option("user", discord.Member, description="Пользователь на выбор, если нет в списке, можно использовать идентификатор пользователя.")
    async def _kick(self, ctx: ApplicationContext, user: discord.Member):
        """Кик пользователя с сервера

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        user : discord.Member
            Пользователь, которого кикнут
        """

        await user.kick()
        
        embed = discord.Embed(title=f":exclamation: {user.mention} ({user.name}) был кикнут с сервера.",
                              color=discord.Colour.red(),
                              ephemeral=True)
        await ctx.respond(embed=embed)
            
    @commands.slash_command(name="ban", guild_ids=guild_ids, description="Банит пользователя с сервера без возможности возвращения по приглашению.")
    @discord.default_permissions(administrator=True)
    @option("user", discord.Member, description="Пользователь на выбор, если нет в списке, можно использовать идентификатор пользователя.")
    async def _ban(self, ctx: ApplicationContext, user: discord.Member):
        """Бан пользователя с сервера

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        user : discord.Member
            Пользователь, которого забанит
        """

        await user.ban()
        embed = discord.Embed(title=f":bangbang: {user.mention} ({user.name}) был забанен на сервере.",
                              color=discord.Colour.red(),
                              ephemeral=True)
        await ctx.respond(embed=embed)
            
    @commands.slash_command(name="timeout", guild_ids=guild_ids, description="Временное блокирование пользователя на сервере.")
    @discord.default_permissions(administrator=True)
    @option("user", discord.Member, description="Пользователь на выбор, если нет в списке, можно использовать идентификатор пользователя.")
    @option("timestamp", description="Время ограничения в формате Ч:ММ:СС")
    async def _timeout(self, ctx: ApplicationContext, user: discord.Member, timestamp: str):
        """Временное ограничение доступа пользователя к серверу

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        user : discord.Member
            Пользователь, которому ограничит доступ
        timestamp : str
            Время ограничения в формате Ч:ММ:СС
        """
        
        t = datetime.datetime.strptime(timestamp, '%H:%M:%S')
        delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        await user.timeout_for(duration=delta)
        
        embed = discord.Embed(title=f":warning: Пользователю {user.mention} ({user.name}) "\
                                    f"был ограничен доступ к серверу на ``{timestamp}``",
                              color=discord.Colour.red(),
                              ephemeral=True)
        await ctx.respond(embed=embed)
            
    @commands.slash_command(name="avatar-user", guild_ids=guild_ids, description="Получение аватара пользователя на выбор.")
    @discord.default_permissions(administrator=True)
    @option("user", discord.Member, description="Пользователь на выбор, если нет в списке, можно использовать идентификатор пользователя.")
    @option("type", str, description="Тип автара: основной или серверный", choices=["основной", "серверный"])
    async def _avatar_user(self, ctx: ApplicationContext, user: discord.Member, type: str):
        """Получение аватара пользователя на выбор

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        user : discord.Member
            Пользователь, которому ограничит доступ
        type : str
            Тип автара: собственный или серверный
        """
        
        if type == "основной":
            avatar = user.avatar
            if avatar is not None:
                await ctx.respond(str(avatar), ephemeral=True)
            else:
                await ctx.respond(f"У {user.mention} нет аватара.", ephemeral=True)
        elif type == "серверный":
            avatar = user.guild_avatar
            if avatar is not None:
                await ctx.respond(str(avatar), ephemeral=True)
            else:
                await ctx.respond(f"У {user.mention} нет аватара.", ephemeral=True)
            
    @commands.slash_command(name="avatar-guild", guild_ids=guild_ids, description="Получение аватара сервера.")
    @discord.default_permissions(administrator=True)
    async def _avatar_guild(self, ctx: ApplicationContext):
        """Получение аватара текущего сервера

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """
        
        icon = ctx.guild.icon
        if icon is not None:
            await ctx.respond(str(icon), ephemeral=True)
        else:
            await ctx.respond(f"У {ctx.guild.name} нет аватара.", ephemeral=True)
