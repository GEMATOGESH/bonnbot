import discord
import vk_api
import yt_dlp
import asyncio
import random
import re
import math
import os
import logging

from vk_api import audio
from discord import option
from discord import ApplicationContext
from discord.ext import commands
from datetime import date, datetime, timedelta
from youtubesearchpython import *
from dotenv import load_dotenv
from threading import Timer


def setup(bot: discord.bot.Bot):
    """Необходимая функция для подключения когов

    Параметры
    ---------
    bot : discord.Bot
        Дискордовский бот

    ЧтоЗа: https://docs.pycord.dev/en/stable/api/clients.html#discord.Bot.load_extension
    """

    bot.add_cog(Music(bot))


class Music(commands.Cog):
    """
    Класс коги с музыкальными командами

    Атрибуты
    --------
    guild_ids : list
        Список идентификаторов серверов, к которым подключен бот

    Методы
    ------
    _captcha_handler(captcha)
        Обработчик капчи для подключения к ВКонтакте
    _two_factor()
        Обработчик двухфакторной аутентификации для подключения к ВКонтакте
    _is_valid_channel(ctx: ApplicationContext)
        Проверка, используется ли нужный текстовый канал для вызова
        музыкальных команд
    _is_playing(ctx: ApplicationContext)
        Проверка играет ли бот в другом голосовом канале
    _is_same_channel(ctx: ApplicationContext)
        Проверка сидит ли пользователь в том же голосовом канале, где
        играет бот
    _msg(reason: str, track_id: int)
        Отправка сообщения ботом
    _start_message()
        Стартовое сообщение бота, при запуске музыкальных команд
    _get_timestamp(is_seeking=False)
        Получение отметки времени текущего трека
    _play(ctx: ApplicationContext, platform: str, track: str, index: int)
        Запуск проигрывания музыки
    _play_vk(ctx: ApplicationContext, music: str, index: int)
        Проигрывание музыки из ВКонтакте
    _play_youtube(ctx: ApplicationContext, music: str, index: int)
        Проигрывание музыки с YouTube
    _play_next(ctx: ApplicationContext)
        Запуск проигрывания следующего трека из музыкальной очереди
    _stop(ctx: ApplicationContext)
        Остановка проигрывания музыки
    _shuffle(ctx: ApplicationContext)
        Рандомизация позиций треков музыкальной очереди
    _skip(ctx: ApplicationContext)
        Пропуск музыкального трека
    _queue(ctx: ApplicationContext, page: int)
        Отображение музыкальной очереди
    _loop(ctx: ApplicationContext, choice: str)
        Включение или выключение повтора трека/очереди
    _remove(ctx: ApplicationContext, track_id: int)
        Удаление трека из музыкальной очереди
    _seek(ctx: ApplicationContext, timestamp: str)
        Перемотка трека
    _nowplaying(ctx: ApplicationContext)
        Отображение информации о текущем треке
    """
    
    guild_ids = []

    def __init__(self, bot: discord.bot.Bot, use_VK=False):
        """
        Параметры
        ---------
        bot : discord.bot.Bot
            Дискордовский бот

        Также конектится к ВКонтакте, для последующего поиска музыки
        """

        self.bot = bot
        self.vk_audio = None
        self.is_vk_connected = False

        self.music_queue = []
        self.seeking = {"is_seeking": False, "timestamp": None, "current_time": None}
        self.repeat_all = False
        self.repeat_one = False
        self.current_view = None

        for guild in bot.guilds:
            self.guild_ids.append(guild.id)

        load_dotenv()
        self.cookie = os.getenv('cookie')
        self.ffmpeg_path = os.getenv('ffmpeg_path')
        self.valid_channel_id = int(os.getenv('valid_channel_id'))
        
        if use_VK:
            vk_login = os.getenv('vk_login')
            vk_password = os.getenv('vk_password')

            if vk_login is not None and vk_password is not None: 
                vk_session = vk_api.VkApi(
                    login=vk_login,
                    password=vk_password,
                    auth_handler=self._two_factor,
                    captcha_handler=self._captcha_handler,
                    app_id=2685278
                )

                try:
                    vk_session.auth(token_only=True)
                    self.vk_audio = audio.VkAudio(vk_session)

                    logging.info("Connected to VK")
                    self.is_vk_connected = True
                except vk_api.AuthError as err:
                    logging.warning("Not connected to VK. Error: ", err)
        else:
            logging.warning("Not connected to VK.")

    def _captcha_handler(self, captcha):
        """Обработчик капчи ВКонтакте

        Параметры
        ---------
        captcha : str
            Ссылка на капчу

        Взято с: https://github.com/python273/vk_api/blob/master/examples/captcha_handle.py
        """

        key = input("Enter captcha code {0}: ".format(
            captcha.get_url())).strip()
        return captcha.try_again(key)

    def _two_factor(self):
        """Обработчик двухфакторной аутентификации ВКонтакте

        Возвращает
        ----------
        tuple[str, bool]
            Код двухфакторной аутентификации и True, чтобы устройство
            было сохранено в список доверенных
        """
        
        code = input('VK code: ')
        return code, True

    async def _is_valid_channel(self, ctx: ApplicationContext) -> bool:
        """Проверяет, используется ли верный текстовый канал для 
        выполнения музыкальных команд, если канал неверный - сообщает
        это пользователю

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота

        Возвращает
        ----------
        bool
            Верный ли канал
        """

        if ctx.channel.id == self.valid_channel_id:
            return True
        else:
            await ctx.respond("Не тот канал.", ephemeral=True)
            return False

    async def _is_playing(self, ctx: ApplicationContext, show_msg=True) -> bool:
        """Проверяет играет ли бот в голосовом канале.
        Если бот не играет - сообщает об этом пользователю.

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота

        Возвращает
        ----------
        bool
            Играет ли бот
        """

        voice_client = discord.utils.get(
            self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client is not None:
            return True
        else:
            if show_msg:
                await ctx.respond("Я даже не играю.", ephemeral=True)
                
            return False

    async def _is_same_channel(self, ctx: ApplicationContext) -> bool:
        """Проверяет играет ли бот в голосовом канале.
        отличном от голового канала пользователя. Если канал отличен -
        сообщает об этом пользователю

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота

        Возвращает
        ----------
        bool
            Играет ли бот в другом канале
        """

        voice_client = ctx.guild.voice_client
        if voice_client is not None and voice_client.channel != ctx.author.voice.channel:
            await ctx.respond("Я играю в другом канале.", ephemeral=True)
            return False

        return True

    async def _msg(self, reason: str, track_id: int):
        """Отправляет сообщение о заказе или запуске проигрывания трека

        Параметры
        ---------
        reason : str
            Причина вызова, от которого зависит название и привязка кнопок
            к сообщению
        track_id : int
            Номер трека в очереди
        """

        channel = self.bot.get_channel(self.valid_channel_id)
        embed = None

        if reason == "order":
            embed = discord.Embed(title="Заказ", color=0xfcf403)
        elif reason == "playing":
            embed = discord.Embed(title="Играет", color=0x00ff44)

        embed.set_thumbnail(url=self.music_queue[track_id]["thumb"])
        embed.add_field(name=str(self.music_queue[track_id]["title"]),
                        value="Продолжительность: ``[" +
                        str(self.music_queue[track_id]["duration"] +
                            "]``\n" + "Заказал " +
                            self.music_queue[track_id]["user"]),
                        inline=True)

        if reason == "order":
            await channel.send(embed=embed)
        elif reason == "playing":
            self.current_view = MusicView(self, self.valid_channel_id)
            await channel.send(embed=embed, view=self.current_view)

    def _start_message(self) -> str:
        """Выбор сообщения, отправляемого при запуске проигрывания музыки

        Возвращает
        ----------
        str
            Текст сообщения
        """

        message = []
        message.append('Ща все будет...')
        message.append('Пиво для ушей пошло...')
        message.append('Ищу...')
        message.append('Запускаю...')
        message.append('В процессе...')
        message.append('Её? Ладно...')
        message.append('Ну ты дурной...')
        message.append('Обрабатываю...')
        message.append('Ща закину...')
        message.append('Бананы в уши, ща музон пойдёт...')
        message.append('Секунду...')
        message.append('Зацени милкше... микстейп...')
        message.append('Бонан сука...')
        message.append('Я не бармен, но заказ принял...')
        message.append('Ща классика заебашит...')
        message.append(
            "Let's break the rules! And really put our backs into it! Max out, pursue it!..")
        message.append("Чел, сейчас бы слушать это в " +
                       str(date.today().year) + " году...")
        message.append("У тебя настолько плохой вкус что ты слушаешь ЭТО?..")
        return random.choice(message)

    def _get_timestamp(self, is_seeking=False) -> str:
        """Получение отметки времени играющего трека

        Параметры
        ---------
        is_seeking : bool, optional
            Вызвана ли функция из-за команды перемотки, by default False

        Возвращает
        ----------
        str
            Отметка времени
        """

        try:
            now = datetime.now()

            if is_seeking:
                now = now - self.seeking[2] + timedelta(hours=self.seeking[1].hour,
                                                        minutes=self.seeking[1].minute,
                                                        seconds=self.seeking[1].second)
            else:
                now = now - self.music_queue[0]["start_time"]

            now = str(now).split(".")[0]
            return now
        except Exception as err:
            logging.error(err)
            return "0:00:00"

    @commands.slash_command(name="play", guild_ids=guild_ids, description="Включает музыку!")
    @option("platform", description="Платформа.", choices=["vk", "youtube"])
    @option("track", description="Ссылка на трек или название, в случае ВК - название.")
    @option("index", description="Номер композиции в результатах поиска, по стандарту - 1.", required=False, default=1)
    async def _play(self, ctx: ApplicationContext, platform: str, track: str, index: int):
        """Запуск проигрывания трека

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        platform : str
            Платформа, где будет производится поиск трека
        track : str
            Название трека
        index : int
            Номер трека в результате поиска
        """

        if await self._is_valid_channel(ctx):
            if ctx.author.voice is None:
                await ctx.respond(ctx.author.mention +
                                  ", зайди в голосовой канал.", ephemeral=True)
                return

            if await self._is_playing(ctx, show_msg=False) and not await self._is_same_channel(ctx):
                return

            if platform == "vk":
                if self.is_vk_connected:
                    result = await self._play_vk(ctx, track, index)
                    if not result:
                        return
                else:
                    await ctx.respond("Музыка с ВК временно (а может и не временно) не поддерживается, пользуйтесь ютубом.")
                    return

            if platform == "youtube":
                result = await self._play_youtube(ctx, track, index)
                if not result:
                    return

            if discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild) is None:
                vc = ctx.author.voice.channel
                await vc.connect()

                voice = ctx.guild.voice_client
                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostats -loglevel 0',
                                  'options': '-vn'}
                
                voice.play(discord.FFmpegPCMAudio(executable=self.ffmpeg_path,
                                                  source=self.music_queue[0]["link"],
                                                  **FFMPEG_OPTIONS),
                           after=lambda e: self._play_next(ctx))

                now = datetime.now()
                self.music_queue[0]["start_time"] = now
                self.music_queue[0]["display_time"] = now

                await self._msg("playing", 0)

    async def _play_vk(self, ctx: ApplicationContext, music: str, index: int) -> bool:
        """Запуск проигрывания трека из ВКонтакте

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        music : str
            Название трека
        index : int
            Номер трека в результате поиска

        Возвращает
        ----------
        bool
            Запустилось ли проигрывание трека
        """

        await ctx.respond(self._start_message())

        # TODO: найти причину почему иногда требуется перезагрузка бота для работы музыки с ВК
        mas = self.vk_audio.search(q=music, count=1, offset=(index - 1))
        arr = []
        try:
            for i in mas:
                arr = i
            URL = arr['url']
        except Exception as err:
            logging.error(err)
            channel = self.bot.get_channel(self.valid_channel_id)
            await channel.send("Я не нашел, попробуйте перезапустить бота.")
            return False

        title = "Placeholder"
        try:
            title = arr['artist'] + " - " + arr['title']
        except:
            logging.warning("Couldn't find title for " + music)

        thumb = None
        try:
            thumb = arr['track_covers'][0]
        except:
            thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/VK.com-logo.svg/192px-VK.com-logo" \
                ".svg.png "

        # Не уверен в необходимости доп. проверки.
        # if thumb is None:
        #     thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/VK.com-logo.svg/192px-VK.com-logo" \
        #         ".svg.png "

        dur = str(timedelta(seconds=arr['duration']))
        self.music_queue.append({"link": URL, "request":  URL, "title":  title,
                                 "thumb":  thumb, "duration": dur,
                                 "user": ctx.author.mention})
        track_id = len(self.music_queue) - 1
        await self._msg("order", track_id)
        return True

    async def _play_youtube(self, ctx: ApplicationContext, music: str, index: int) -> bool:
        """Запуск проигрывания трека с YouTube

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        music : str
            Название трека
        index : int
            Номер трека в результате поиска

        Возвращает
        ----------
        bool
            Запустилось ли проигрывание трека
        """

        channel = self.bot.get_channel(self.valid_channel_id)

        ydl_opts = {'format': 'best', 'cookiefile': self.cookie,
                    'cachedir': False}

        await ctx.respond(self._start_message())

        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # Not a hyperlink
        if re.match(regex, music) is None:
            videosSearch = VideosSearch(music, limit=index)
            music = videosSearch.result()['result'][index - 1]['link']
            if music == "":
                ctx.respond(
                    "Ошибка при поиске. Возможно такой композиции не существует.")
                return False

            music = 'https://youtu.be/' + music[32:]

        # Playlist
        elif ('playlist' in music) or ('&list' in music):
            await ctx.respond("Загружаю плейлист, дай секунду...",
                              ephemeral=True)
            checker = int(index)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(music, download=False)

                for idx, video in enumerate(info['entries'], start=1):
                    if checker <= idx:
                        URL = video['url']
                        video_title = video['title']
                        music = 'https://youtu.be/' + video['id']
                        thumb = video['thumbnails'][len(
                            video['thumbnails']) - 1]['url']
                        dur = str(timedelta(seconds=video['duration']))
                        self.music_queue.append({"link": URL, "request": music,
                                                 "title": video_title,
                                                 "thumb": thumb,
                                                 "duration": dur,
                                                 "user": ctx.author.mention})

                        track_id = len(self.music_queue) - 1
                        await self._msg("order", track_id)

            await channel.send("Загрузка плейлиста завершена.", ephemeral=True)
            return True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(music, download=False)
            URL = info['url']
            video_title = info['title']
            thumb = info['thumbnails'][len(info['thumbnails']) - 1]['url']
            dur = str(timedelta(seconds=info['duration']))
            self.music_queue.append({"link": URL, "request": music,
                                     "title": video_title, "thumb": thumb,
                                     "duration": dur, "user": ctx.author.mention})

            track_id = len(self.music_queue) - 1

        await self._msg("order", track_id)
        return True

    def _play_next(self, ctx: ApplicationContext):
        """Запуск проигрывания следующей композиции из очереди или конец
        проигрывания треков и выход из голосового канала

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """

        voice = ctx.guild.voice_client
        channel = self.bot.get_channel(self.valid_channel_id)

        if len(self.music_queue) > 1 or self.repeat_one or self.seeking["is_seeking"]:
            if voice is not None:
                asyncio.run_coroutine_threadsafe(
                    self.current_view.message.edit(view=None), self.bot.loop)

                if not self.repeat_one and not self.repeat_all and not self.seeking["is_seeking"]:
                    del self.music_queue[0]
                elif self.repeat_all and not self.seeking["is_seeking"]:
                    if len(self.music_queue) > 1:
                        buffer = self.music_queue.pop(0)
                        self.music_queue.append(buffer)

                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 '\
                                  '-reconnect_streamed 1 '\
                                  '-reconnect_delay_max 5 -nostats -loglevel 0',
                                  'options': '-vn'}

                if self.seeking["is_seeking"]:
                    FFMPEG_OPTIONS['options'] = '-vn -ss ' + \
                        str(self.seeking["timestamp"].time())                        

                voice.play(discord.FFmpegPCMAudio(executable=self.ffmpeg_path,
                                                  source=self.music_queue[0]["link"],
                                                  **FFMPEG_OPTIONS),
                           after=lambda e: self._play_next(ctx))

                if not self.seeking["is_seeking"]:
                    now = datetime.now()
                    self.music_queue[0]["start_time"] = now
                    self.music_queue[0]["display_time"] = now
                    asyncio.run_coroutine_threadsafe(
                        self._msg("playing", 0), self.bot.loop)
                else:
                    self.seeking["is_seeking"] = False
                    self.seeking["timestamp"] = None
                    self.seeking["current_time"] = None
        else:
            if voice is not None:
                if len(self.music_queue) > 0:
                    del self.music_queue[0]
                    
                asyncio.run_coroutine_threadsafe(
                    self.current_view.message.edit(view=None), self.bot.loop)
                asyncio.run_coroutine_threadsafe(
                    voice.disconnect(), self.bot.loop)
                asyncio.run_coroutine_threadsafe(channel.send(
                    "Я пошел, если что - циферки знаешь."), self.bot.loop)

    @commands.slash_command(name="stop", guild_ids=guild_ids, description="Останавливает музыку и покидает канал.")
    async def _stop(self, ctx: ApplicationContext):
        """Остановка проигрывания треков, очитска очереди и выход из
        голосового канала

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """

        if await self._is_valid_channel(ctx):
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if not await self._is_same_channel(ctx):
                    return

                await voice_channel.disconnect()

                embed = discord.Embed(title="Остановлено", color=0xff0000)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp(False)
                embed.add_field(name=str(self.music_queue[0]["title"]),
                                value="На ``[" + str(timestamp) + "]``\n" +\
                                      "Заказал " + (self.music_queue[0]["user"]))
                await ctx.respond(embed=embed)

                self.music_queue.clear()
                self.repeat_one = False
                self.repeat_all = False

    @commands.slash_command(name="shuffle", guild_ids=guild_ids, description="Перемешивает музыкальную очередь.")
    async def _shuffle(self, ctx: ApplicationContext):
        """Рандомизация позиций треков в очереди

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """

        if await self._is_valid_channel(ctx):
            if await self._is_playing(ctx):
                if len(self.music_queue) == 1:
                    await ctx.respond("Нечего мешать.")
                    return

                if not await self._is_same_channel(ctx):
                    return

                backup = self.music_queue[0]
                del self.music_queue[0]
                random.shuffle(self.music_queue)
                self.music_queue.insert(0, backup)

                await ctx.respond("Успешно перемешано.")

    @commands.slash_command(name="skip", guild_ids=guild_ids, description="Пропускает текущий трек.")
    async def _skip(self, ctx: ApplicationContext):
        """Завершение проигрывания текущего трека и запуск проигрывания
        следующего из музыкальной очереди, если очередь пуста - выход
        из голосового канала

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """

        if await self._is_valid_channel(ctx):
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if await self._is_playing(ctx):
                voice_channel = ctx.guild.voice_client

                if not await self._is_same_channel(ctx):
                    return

                embed = discord.Embed(title="Пропущено", color=0x9d00ff)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp()
                embed.add_field(name=str(self.music_queue[0]["title"]),
                                value="На ``[" + str(timestamp) + "]``\n" +\
                                      "Заказал " + (self.music_queue[0]["user"]))

                if len(self.music_queue) == 1 and not self.repeat_one and not self.repeat_all:
                    await voice_channel.disconnect()
                    await ctx.respond(embed=embed)

                    self.music_queue.clear()
                    return

                voice.stop()
                await ctx.respond(embed=embed)

    @commands.slash_command(name="queue", guild_ids=guild_ids, description="Текущая музыкальная очередь.")
    @option("page", int, description="Номер страницы очереди.", required=False, default=1)
    async def _queue(self, ctx: ApplicationContext, page: int):
        """Отображение музыкальной очереди страницами по 10 штук

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        page : int
            Номер страницы
        """

        if await self._is_valid_channel(ctx):
            if len(self.music_queue) == 1:
                await ctx.respond("Очередь пуста.", ephemeral=True)
                return

            num_of_pages = math.ceil(len(self.music_queue) / 10)
            if page > num_of_pages or page < 1:
                await ctx.respond("Стольких страниц нет.", ephemeral=True)
                return

            start = (page - 1) * 10
            end = start + 10

            if end > len(self.music_queue):
                end = len(self.music_queue)

            embed = discord.Embed(title="Очередь", color=0x00ddff)
            content = ""
            for i in range(start, end):
                content += str(i + 1) + ") [" +\
                    str(self.music_queue[i]["title"]) + "](<" + str(
                    self.music_queue[i]["request"]) + ">)\n"
                    
            embed.description = content

            embed.set_footer(text="Страница " + str(page) +
                             " из " + str(num_of_pages))
            await ctx.respond(embed=embed)

    @commands.slash_command(name="loop", guild_ids=guild_ids, description="Включает или выключает повтор на боте.")
    @option("choice", description="Повторять всю очередь или только текущий трек? Может вообще выключить?", choices=["one", "all", "off"])
    async def _loop(self, ctx: ApplicationContext, choice: str):
        """Включение или выключение повтора трека или всей очереди

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        choice : str
            Режим повтора: одиночный, всей очереди, выкл
        """

        if await self._is_valid_channel(ctx):
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                if not await self._is_same_channel(ctx):
                    return

                if choice == "all":
                    self.repeat_one = False
                    self.repeat_all = True
                    await ctx.respond("Переключил на повтор всей очереди.")

                elif choice == "one":
                    self.repeat_one = True
                    self.repeat_all = False
                    await ctx.respond("Переключил на повтор текущего трека.")

                elif choice == "off":
                    self.repeat_one = False
                    self.repeat_all = False
                    await ctx.respond("Выключил повтор.")

                else:
                    await ctx.respond("Отсутствие выбора тоже выбор.")

    @commands.slash_command(name="remove", guild_ids=guild_ids, description="Удаляет трек под заданным номером из очереди.")
    @option("track_id", description="Номер трека в очереди")
    async def _remove(self, ctx: ApplicationContext, track_id: int):
        """Удаление трека из музыкальной очереди

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        track_id : int
            Номер трека в очереди
        """

        if await self._is_valid_channel(ctx):
            if await self._is_playing(ctx):
                voice_channel = ctx.guild.voice_client

                if not await self._is_same_channel(ctx):
                    return

                track_id = int(track_id)
                if (track_id > len(self.music_queue)) or (track_id < 1):
                    await ctx.respond("Трека под этим номером нет.", ephemeral=True)
                    return

                if (track_id == len(self.music_queue)) and (track_id == 1):
                    await voice_channel.disconnect()

                    embed = discord.Embed(title="Остановлено", color=0xff0000)
                    embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                    timestamp = self._get_timestamp()
                    embed.add_field(name=str(self.music_queue[0]["title"]),
                                    value="На ``[" + str(timestamp) +\
                                          "]``\n" + "Заказал " +\
                                          (self.music_queue[0]["user"]))
                    await ctx.respond("Ты думал я не могу? А я могу!", embed=embed)

                    self.music_queue.clear()
                    self.repeat_all = False
                    self.repeat_one = False
                    return

                track_id = int(track_id - 1)
                embed = discord.Embed(title="Удалено", color=0xfc0303)
                embed.set_thumbnail(url=self.music_queue[track_id]["thumb"])
                embed.add_field(name=str(self.music_queue[track_id]["title"]),
                                value="Очередь смещена." + "\n" + "Заказал " +\
                                    self.music_queue[track_id]["user"])
                await ctx.respond(embed=embed)

                if track_id == 0:
                    discord.utils.get(self.bot.voice_clients,
                                      guild=ctx.guild).stop()
                else:
                    del self.music_queue[track_id]

    @commands.slash_command(name="seek", guild_ids=guild_ids, description="Перематывает текущий трек.")
    @option("timestamp", description="Интересующее время в формате Ч:ММ:СС")
    async def _seek(self, ctx: ApplicationContext, timestamp: str):
        """Перемотка трека к указанной отметке времени

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        timestamp : str
            Отметка времени, на который нужно перемотать
        """

        if await self._is_valid_channel(ctx):
            if await self._is_playing(ctx):
                if not await self._is_same_channel(ctx):
                    return

                try:
                    seek_time = datetime.strptime(timestamp, '%H:%M:%S')
                except Exception:
                    await ctx.respond("В школе формат записи времени не учили?",
                                      ephemeral=True)
                    return

                self.seeking["is_seeking"] = True
                self.seeking["timestamp"] = seek_time
                self.seeking["current_time"] = datetime.now()

                embed = discord.Embed(title="Перемотка", color=0x030ffc)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                embed.add_field(name=str(self.music_queue[0]["title"]), 
                                value="``[" + str(seek_time.time()) + " / " +\
                                      str(self.music_queue[0]["duration"] +\
                                      "]``\n" + "Заказал " +\
                                      self.music_queue[0]["user"]))

                await ctx.respond(embed=embed)
                discord.utils.get(self.bot.voice_clients,
                                  guild=ctx.guild).stop()

    @commands.slash_command(name="nowplaying", guild_ids=guild_ids, description="Отображает текущий трек.")
    async def _nowplaying(self, ctx: ApplicationContext):
        """Отображение информации о текущем треке

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """

        if await self._is_valid_channel(ctx):
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                if not await self._is_same_channel(ctx):
                    return

                embed = discord.Embed(title="Сейчас играет", color=0xf59e42)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp()
                embed.add_field(name=str(self.music_queue[0]["title"]), 
                                value="``[" + str(timestamp) + " / " +\
                                      str(self.music_queue[0]["duration"] +\
                                      "]``\n" + "Заказал " +\
                                      self.music_queue[0]["user"]))

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("Я даже не играю.", ephemeral=True)


class MusicView(discord.ui.View):
    """
    Класс кнопок для обработки музыкальных команд

    Атрибуты
    --------
    music : Music
        Объект основного класса обработчика музыкальных команд

    Методы
    ------
    _is_playing(self, interaction: discord.Interaction)
        Проверка играет ли бот в другом голосовом канале
    _is_same_channel(interaction: discord.Interaction)
        Проверка сидит ли пользователь в том же голосовом канале, где
        играет бот
    _is_in_voice(interaction: discord.Interaction)
        Проверка сидит ли пользователь в голосовом канале
    next_button_callback(self, button, interaction: discord.Interaction)
        Запуск проигрывания следующего трека из музыкальной очереди
    stop_button_callback(self, button, interaction: discord.Interaction)
        Остановка проигрывания музыки
    shuffle_button_callback(self, button, interaction: discord.Interaction)
        Рандомизация позиций треков музыкальной очереди
    loop_button_callback(self, button, interaction: discord.Interaction)
        Включение или выключение повтора всей очереди
    loop_one_button_callback(self, button, interaction: discord.Interaction)
        Включение или выключение повтора трека
    """

    def __init__(self, music: Music, valid_channel_id):
        """
        Параметры
        ---------
        music : Music
            Объект основного класса обработчика музыкальных команд
        """

        super().__init__()
        self.music = music
        self.valid_channel_id = valid_channel_id

    async def _is_playing(self, interaction: discord.Interaction) -> bool:
        """Проверяет играет ли бот в голосовом канале.
        Если бот не играет - сообщает об этом пользователю.

        Параметры
        ---------
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты

        Возвращает
        ----------
        bool
            Играет ли бот
        """

        voice_client = discord.utils.get(
            self.music.bot.voice_clients, guild=interaction.guild)
        if voice_client is None:
            await interaction.response.send_message("Я даже не играю.", 
                                                    ephemeral=True)
            return False

        return True

    async def _is_same_channel(self, interaction: discord.Interaction) -> bool:
        """Проверяет играет ли бот в голосовом канале.
        отличном от голового канала пользователя. Если канал отличен -
        сообщает об этом пользователю

        Параметры
        ---------
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты

        Возвращает
        ----------
        bool
            Играет ли бот в другом канале
        """
        voice_client = interaction.guild.voice_client
        if voice_client.channel != interaction.user.voice.channel:
            await interaction.response.send_message("Я играю в другом канале.", 
                                                    ephemeral=True)
            return False

        return True

    async def _is_in_voice(self, interaction: discord.Interaction) -> bool:
        """Проверяет находится ли пользователь в голосовом канале

        Параметры
        ---------
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты

        Возвращает
        ----------
        bool
            Находится ли пользователь в голосовом канале
        """

        if interaction.user.voice is None:
            await interaction.response.send_message("Не твое - не трогай.", 
                                                    ephemeral=True)
            return False

        return True

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏹️")
    async def stop_button_callback(self, button, interaction: discord.Interaction):
        """Остановка проигрывания треков, очитска очереди и выход из
        голосового канала

        Параметры
        ---------
        button : discord.ui.button
            Кнопка, с которой происходит взаимодействие
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты
        """

        if await self._is_playing(interaction):
            voice_client = interaction.guild.voice_client

            if not await self._is_in_voice(interaction):
                return
            else:
                if not await self._is_same_channel(interaction):
                    return

            embed = discord.Embed(title="Остановлено", color=0xff0000)
            embed.set_thumbnail(url=self.music.music_queue[0]["thumb"])
            timestamp = self.music._get_timestamp(False)
            embed.add_field(name=str(self.music.music_queue[0]["title"]),
                            value="На ``[" + str(timestamp) + "]``\n" +\
                                  "Заказал " + (self.music.music_queue[0]["user"]))
            await interaction.response.send_message(embed=embed)

            self.music.music_queue.clear()
            self.music.repeat_one = False
            self.music.repeat_all = False

            await voice_client.disconnect()

            await self.message.edit(view=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏭️")
    async def next_button_callback(self, button, interaction: discord.Interaction):
        """Завершение проигрывания текущего трека и запуск проигрывания
        следующего из музыкальной очереди, если очередь пуста - выход
        из голосового канала

        Параметры
        ---------
        button : discord.ui.button
            Кнопка, с которой происходит взаимодействие
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты
        """

        voice = discord.utils.get(
            self.music.bot.voice_clients, guild=interaction.guild)
        if await self._is_playing(interaction):
            voice_channel = interaction.guild.voice_client

            if not await self._is_in_voice(interaction):
                return
            else:
                if not await self._is_same_channel(interaction):
                    return

            embed = discord.Embed(title="Пропущено", color=0x9d00ff)
            embed.set_thumbnail(url=self.music.music_queue[0]["thumb"])
            timestamp = self.music._get_timestamp()
            embed.add_field(name=str(self.music.music_queue[0]["title"]),
                            value="На ``[" + str(timestamp) + "]``\n" +\
                                  "Заказал " + (self.music.music_queue[0]["user"]))

            if len(self.music.music_queue) == 1 and not self.music.repeat_one and not self.music.repeat_all:
                await interaction.response.send_message(embed=embed)
                await voice_channel.disconnect()

                self.music.music_queue.clear()
                return

            voice.stop()
            await interaction.response.send_message(embed=embed)

            await self.message.edit(view=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔀")
    async def shuffle_button_callback(self, button, interaction: discord.Interaction):
        """Рандомизация позиций треков в очереди

        Параметры
        ---------
        button : discord.ui.button
            Кнопка, с которой происходит взаимодействие
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты
        """

        if await self._is_playing(interaction):
            if len(self.music.music_queue) == 1:
                await interaction.response.send_message("Нечего мешать.", 
                                                        ephemeral=True)
                return

            if not await self._is_in_voice(interaction):
                return
            else:
                if not await self._is_same_channel(interaction):
                    return

            backup = self.music.music_queue[0]
            del self.music.music_queue[0]
            random.shuffle(self.music.music_queue)
            self.music.music_queue.insert(0, backup)

            await interaction.response.send_message("Успешно перемешано.", 
                                                    ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔁")
    async def loop_button_callback(self, button, interaction: discord.Interaction):
        """Включение или выключение повтора текущего трека

        Параметры
        ---------
        button : discord.ui.button
            Кнопка, с которой происходит взаимодействие
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты
        """

        if await self._is_playing(interaction):
            if not await self._is_in_voice(interaction):
                return
            else:
                if not await self._is_same_channel(interaction):
                    return

            if not self.music.repeat_all:
                self.music.repeat_one = False
                self.music.repeat_all = True
                await interaction.response.send_message("Переключил на повтор всей очереди.")
            elif self.music.repeat_all:
                self.music.repeat_all = False
                await interaction.response.send_message("Выключил повтор всей очереди.")

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔂")
    async def loop_one_button_callback(self, button, interaction: discord.Interaction):
        """Включение или выключение повтора всей музыкальной очереди

        Параметры
        ---------
        button : discord.ui.button
            Кнопка, с которой происходит взаимодействие
        interaction : discord.Interaction
            Объект взаимодействия с Discord через команды или компоненты
        """

        if await self._is_playing(interaction):
            if not await self._is_in_voice(interaction):
                return
            else:
                if not await self._is_same_channel(interaction):
                    return

            if not self.music.repeat_one:
                self.music.repeat_one = True
                self.music.repeat_all = False
                await interaction.response.send_message("Переключил на повтор трека.")
            elif self.music.repeat_one:
                self.music.repeat_one = False
                await interaction.response.send_message("Выключил повтор трека.")
