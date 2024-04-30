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
from discord.ext import commands
from datetime import date
from datetime import datetime
from datetime import timedelta
from youtubesearchpython import *
from dotenv import load_dotenv


def setup(bot): 
    bot.add_cog(Music(bot)) 


class Music(commands.Cog):
    bot = None
    guild_ids = []
    vk_audio = None
    is_vk_connected = False

    music_queue = []
    seeking = {"is_seeking": False, "timestamp": None, "current_time": None}
    repeat_all = False
    repeat_one = False
    current_view = None


    def __init__(self, bot):
        self.bot = bot
        
        for guild in bot.guilds:
            self.guild_ids.append(guild.id)

        load_dotenv()
        vk_login = os.getenv('vk_login')
        vk_password = os.getenv('vk_password')
        self.cookie = os.getenv('cookie')
        self.ffmpeg_path = os.getenv('ffmpeg_path')
        
        if vk_login is not None and vk_password is not None:
            vk_session = vk_api.VkApi(
                login=vk_login,
                password=vk_password,
                auth_handler=self._two_factor,
                captcha_handler=self._captcha_handler
            )
            try:
                vk_session.auth(token_only=True)
                self.vk_audio = audio.VkAudio(vk_session)

                logging.info("Connected to VK")
                self.is_vk_connected = True
            except vk_api.AuthError as err:
                logging.warning("Not connected to VK. Error: ", err)


    async def _is_valid_channel(self, ctx):
        if ctx.channel.id == 502142352144728064:
            return True
        else:
            await ctx.respond("Не тот канал.")
            return False


    def _captcha_handler(self, captcha):
        key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
        return captcha.try_again(key)


    def _two_factor(self):
        code = input('VK code: ')
        return code, True


    async def _msg(self, reason, track_id):
        channel = self.bot.get_channel(502142352144728064)
        embed = None

        if reason == "order":
            embed = discord.Embed(title="Заказ", color=0xfcf403)
        elif reason == "playing":
            embed = discord.Embed(title="Играет", color=0x00ff44)

        embed.set_thumbnail(url=self.music_queue[track_id]["thumb"])
        embed.add_field(name=str(self.music_queue[track_id]["title"]), value="Продолжительность: ``[" + str(
            self.music_queue[track_id]["duration"] + "]``\n" + "Заказал " + self.music_queue[track_id]["user"]), inline=True)

        if reason == "order":
            await channel.send(embed=embed)
        elif reason == "playing":
            self.current_view = MusicView(self)
            await channel.send(embed=embed, view=self.current_view)


    def _start_message(self):
        checker = random.randint(1, 18)
        message = ""
        if checker == 1:
            message += 'Ща все будет...'
        elif checker == 2:
            message += 'Пиво для ушей пошло...'
        elif checker == 3:
            message += 'Ищу...'
        elif checker == 4:
            message += 'Запускаю...'
        elif checker == 5:
            message += 'В процессе...'
        elif checker == 6:
            message += 'Её? Ладно...'
        elif checker == 7:
            message += 'Ну ты дурной...'
        elif checker == 8:
            message += 'Обрабатываю...'
        elif checker == 9:
            message += 'Ща закину...'
        elif checker == 10:
            message += 'Бананы в уши, ща музон пойдёт...'
        elif checker == 11:
            message += 'Секунду...'
        elif checker == 12:
            message += 'Зацени милкше... микстейп...'
        elif checker == 13:
            message += 'Бонан сука...'
        elif checker == 14:
            message += 'Я не бармен, но заказ принял...'
        elif checker == 15:
            message += 'Ща классика заебашит...'
        elif checker == 16:
            message += "Let's break the rules! And really put our backs into it! Max out, pursue it!.."
        elif checker == 17:
            message += "Чел, сейчас бы слушать это в " + \
                str(date.today().year) + " году..."
        elif checker == 18:
            message += "У тебя настолько плохой вкус что ты слушаешь ЭТО?.."
        return message

    def _get_timestamp(self, is_seeking=False):
        try:
            now = datetime.now()

            if is_seeking:
                now = now - self.seeking[2] + timedelta(hours=self.seeking[1].hour, minutes=self.seeking[1].minute,
                                                   seconds=self.seeking[1].second)
            else:
                now = now - self.music_queue[0]["start_time"]

            now = str(now).split(".")[0]
            return now
        except Exception as err:
            logging.error(err)
            return "0:00:00"


    @commands.slash_command(name="play", guild_ids=guild_ids, description="Включает музыку!")
    @option("platform", description="Ссылка на трек или название.", choices=["vk", "youtube"])
    @option("track", description="Ссылка на трек или название, в случае ВК - название.")
    @option("index", description="Номер композиции в результатах поиска, по стандарту - 1.", required=False, default=1)
    async def _play(self, ctx, platform: str, track: str, index: int):
        result = await self._is_valid_channel(ctx)
        if result:
            # Basic check.
            if ctx.author.voice is None:
                await ctx.respond(ctx.author.mention + ", зайди в голосовой канал.")
                return

            voice_client = discord.utils.get(
                ctx.bot.voice_clients, guild=ctx.guild)
            if voice_client is not None:
                if voice_client.channel != ctx.author.voice.channel:
                    await ctx.respond("Я уже играю в другом канале.")
                    return

            # Platform loading.
            if platform == "vk":
                if self.is_vk_connected:
                    result = await self._play_vk(ctx, track, index)
                    if not result:
                        return
                else:
                    await ctx.respond("Музыка с ВК временно не поддерживается, пользуйтесь ютубом.")
                    return

            if platform == "youtube":
                result = await self._play_youtube(ctx, track, index)
                if not result:
                    return

            # Start playing if not started already.
            if voice_client is None:
                vc = ctx.author.voice.channel
                await vc.connect()

                voice = ctx.guild.voice_client
                FFMPEG_OPTIONS = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostats -loglevel 0',
                    'options': '-vn'}
                voice.play(discord.FFmpegPCMAudio(executable=self.ffmpeg_path,
                                                  source=self.music_queue[0]["link"], **FFMPEG_OPTIONS),
                           after=lambda e: self._play_next(ctx))

                now = datetime.now()
                self.music_queue[0]["start_time"] = now
                self.music_queue[0]["display_time"] = now

                await self._msg("playing", 0)


    async def _play_vk(self, ctx, music, index):
        await ctx.respond(self._start_message())

        mas = self.vk_audio.search(music, 1, int(index) - 1)
        arr = []
        try:
            for i in mas:
                arr = i
            URL = arr['url']
        except Exception as err:
            logging.error(err)
            channel = self.bot.get_channel(502142352144728064)
            await channel.send("Я не нашел :c")
            return False

        title = "Placeholder"
        try:
            title = arr['artist'] + " - " + arr['title']
        except:
            logging.warning("Я не нашел название!!!!")

        thumb = None
        try:
            thumb = arr['track_covers'][0]
        except:
            thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/VK.com-logo.svg/192px-VK.com-logo" \
                ".svg.png "
        if thumb is None:
            thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/VK.com-logo.svg/192px-VK.com-logo" \
                ".svg.png "

        dur = str(timedelta(seconds=arr['duration']))
        self.music_queue.append({"link": URL, "request":  URL, "title":  title, "thumb":  thumb,
                                 "duration": dur, "user": ctx.author.mention})
        track_id = len(self.music_queue) - 1
        await self._msg("order", track_id)
        return True


    async def _play_youtube(self, ctx, music, index):
        channel = self.bot.get_channel(502142352144728064)

        ydl_opts = {'format': 'bestaudio', 'cookiefile': self.cookie, 'cachedir': False}

        await ctx.respond(self._start_message())

        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            # domain
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'  # optional port
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
            await ctx.respond("Я рот плейлистов шатал, дай секунду...")
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
                        self.music_queue.append(
                            {"link": URL, "request": music, "title": video_title, "thumb": thumb,
                             "duration": dur, "user": ctx.author.mention})

                        track_id = len(self.music_queue) - 1
                        await self._msg("order", track_id)

            await channel.send("Загрузка плейлиста завершена.")
            return True

        # Hyperlink
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(music, download=False)
            URL = info['url']
            video_title = info['title']
            thumb = info['thumbnails'][len(info['thumbnails']) - 1]['url']
            dur = str(timedelta(seconds=info['duration']))
            self.music_queue.append(
                {"link": URL, "request": music, "title": video_title, "thumb": thumb, "duration": dur,
                 "user": ctx.author.mention})

            track_id = len(self.music_queue) - 1

        await self._msg("order", track_id)
        return True


    def _play_next(self, ctx):
        voice = ctx.guild.voice_client
        channel = self.bot.get_channel(502142352144728064)

        if len(self.music_queue) > 1 or self.repeat_one or self.seeking["is_seeking"]:
            if voice is not None:
                asyncio.run_coroutine_threadsafe(self.current_view.message.edit(view=None), self.bot.loop)

                if not self.repeat_one and not self.repeat_all and not self.seeking["is_seeking"]:
                    del self.music_queue[0]
                elif self.repeat_all and not self.seeking["is_seeking"]:
                    if len(self.music_queue) > 1:
                        buffer = self.music_queue.pop(0)
                        self.music_queue.append(buffer)

                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostats -loglevel 0',
                                  'options': '-vn'}

                if self.seeking["is_seeking"]:
                    FFMPEG_OPTIONS['options'] = '-vn -ss ' + \
                        str(self.seeking["timestamp"].time())

                voice.play(discord.FFmpegPCMAudio(executable=self.ffmpeg_path,
                                                  source=self.music_queue[0]["link"], **FFMPEG_OPTIONS),
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

                del self.music_queue[0]
                asyncio.run_coroutine_threadsafe(self.current_view.message.edit(view=None), self.bot.loop)
                asyncio.run_coroutine_threadsafe(voice.disconnect(), self.bot.loop)
                asyncio.run_coroutine_threadsafe(channel.send("Я пошел, если что - циферки знаешь."), self.bot.loop)


    @commands.slash_command(name="stop", guild_ids=guild_ids, description="Останавливает музыку и покидает канал.")
    async def _stop(self, ctx):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Я играю в другом канале.")
                    return

                await voice_channel.disconnect()

                embed = discord.Embed(title="Остановлено", color=0xff0000)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp(False)
                embed.add_field(name=str(self.music_queue[0]["title"]),
                                value="На ``[" + str(timestamp) + "]``\n" + "Заказал " + (self.music_queue[0]["user"]))
                await ctx.respond(embed=embed)

                self.music_queue.clear()
                self.repeat_one = False
                self.repeat_all = False


    @commands.slash_command(name="shuffle", guild_ids=guild_ids, description="Перемешивает музыкальную очередь.")
    async def _shuffle(self, ctx):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                if len(self.music_queue) == 1:
                    await ctx.respond("Нечего мешать.")
                    return

                voice_channel = ctx.guild.voice_client
                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Я играю в другом канале.")
                    return

                backup = self.music_queue[0]
                del self.music_queue[0]
                random.shuffle(self.music_queue)
                self.music_queue.insert(0, backup)

                await ctx.respond("Успешно перемешано.")
            else:
                await ctx.respond("Я даже не играю.")


    @commands.slash_command(name="skip", guild_ids=guild_ids, description="Пропускает текущий трек.")
    async def skip(self, ctx):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Я играю в другом канале.")
                    return

                embed = discord.Embed(title="Пропущено", color=0x9d00ff)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp()
                embed.add_field(name=str(self.music_queue[0]["title"]),
                                value="На ``[" + str(timestamp) + "]``\n" + "Заказал " + (self.music_queue[0]["user"]))

                if len(self.music_queue) == 1 and not self.repeat_one and not self.repeat_all:
                    await voice_channel.disconnect()
                    await ctx.respond(embed=embed)

                    self.music_queue.clear()
                    return

                voice.stop()
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("Я даже не играю.")


    @commands.slash_command(name="queue", guild_ids=guild_ids, description="Текущая музыкальная очередь.")
    @option("index", description="Номер страницы очереди.", required=False, default=0)
    async def _queue(self, ctx, index: int):
        result = await self._is_valid_channel(ctx)
        if result:
            if len(self.music_queue) == 1:
                await ctx.respond("Очередь пуста.")
                return

            pages = int(math.ceil(len(self.music_queue) / 10))
            if int(page) > pages or int(page) < 0:
                await ctx.respond("Стольких страниц нет.")
                return

            start = 0
            if page != 0:
                start = (int(page) - 1) * 10
            end = start + 10

            if end > len(self.music_queue):
                end = len(self.music_queue)

            embed = discord.Embed(title="Очередь", color=0x00ddff)
            content = ""
            for i in range(start, end):
                content += str(i + 1) + ") [" + str(self.music_queue[i]["title"]) + "](<" + str(
                    self.music_queue[i]["request"]) + ">)\n"
            embed.description = content

            if page == 0:
                page = 1

            embed.set_footer(text="Страница " +
                             str(page) + " из " + str(pages))
            await ctx.respond(embed=embed)


    @commands.slash_command(name="loop", guild_ids=guild_ids, description="Включает или выключает повтор на боте.")
    @option("choice", description="Повторять всю очередь или только текущий трек? Может вообще выключить?", choices=["one", "all", "off"])
    async def _loop(self, ctx, choice: str):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Нельзя помешать вечеринке не участвуя в ней.")
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
                    await ctx.respond("Не выбор тоже выбор.")


    @commands.slash_command(name="remove", guild_ids=guild_ids, description="Удаляет трек под заданным номером из очереди.")
    @option("id", description="Номер трека в очереди")
    async def _remove(self, ctx, track_id: int):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:

                voice_channel = ctx.guild.voice_client
                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Нельзя помешать вечеринке не участвуя в ней.")
                    return

                track_id = int(track_id)
                if (track_id > len(self.music_queue)) or (track_id < 1):
                    await ctx.respond("Трека под этим номером нет.")
                    return

                if (track_id == len(self.music_queue)) and (track_id == 1):
                    await voice_channel.disconnect()

                    embed = discord.Embed(title="Остановлено", color=0xff0000)
                    embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                    timestamp = self._get_timestamp()
                    embed.add_field(name=str(self.music_queue[0]["title"]),
                                    value="На ``[" + str(timestamp) + "]``\n" + "Заказал " + (self.music_queue[0]["user"]))
                    await ctx.respond("Ты думал я не могу? А я могу!", embed=embed)

                    self.music_queue.clear()
                    self.repeat_all = False
                    self.repeat_one = False
                    return

                track_id = int(track_id - 1)
                embed = discord.Embed(title="Удалено", color=0xfc0303)
                embed.set_thumbnail(url=self.music_queue[track_id]["thumb"])
                embed.add_field(name=str(self.music_queue[track_id]["title"]),
                                value="Очередь смещена." + "\n" + "Заказал " + self.music_queue[track_id]["user"])
                await ctx.respond(embed=embed)

                if track_id == 0:
                    voice.stop()
                else:
                    del self.music_queue[track_id]

            else:
                await ctx.respond("Я даже не играю.")


    @commands.slash_command(name="seek", guild_ids=guild_ids, description="Перематывает текущий трек.")
    @option("timestamp", description="Интересующее время в формате Ч:ММ:СС")
    async def _seek(self, ctx, timestamp: str):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Нельзя помешать вечеринке не участвуя в ней.")
                    return

                try:
                    seek_time = datetime.strptime(timestamp, '%H:%M:%S')
                except Exception:
                    await ctx.respond("В школе формат записи времени не учили?")
                    return

                self.seeking["is_seeking"] = True
                self.seeking["timestamp"] = seek_time
                self.seeking["current_time"] = datetime.now()

                embed = discord.Embed(title="Перемотка", color=0x030ffc)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                embed.add_field(name=str(self.music_queue[0]["title"]), value="``[" + str(seek_time.time()) + " / " + str(
                    self.music_queue[0]["duration"] + "]``\n" + "Заказал " + self.music_queue[0]["user"]))

                await ctx.respond(embed=embed)
                voice.stop()
            else:
                await ctx.respond("Я даже не играю.")


    @commands.slash_command(name="nowplaying", guild_ids=guild_ids, description="Отображает текущий трек.")
    async def _nowplaying(self, ctx):
        result = await self._is_valid_channel(ctx)
        if result:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice is not None:
                voice_channel = ctx.guild.voice_client

                if voice_channel.channel != ctx.author.voice.channel:
                    await ctx.respond("Нельзя помешать вечеринке не  участвуя в ней.")
                    return

                embed = discord.Embed(title="Сейчас играет", color=0xf59e42)
                embed.set_thumbnail(url=self.music_queue[0]["thumb"])
                timestamp = self._get_timestamp()
                embed.add_field(name=str(self.music_queue[0]["title"]), value="``[" + str(timestamp) + " / " + str(
                    self.music_queue[0]["duration"] + "]``\n" + "Заказал " + self.music_queue[0]["user"]))

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("Я даже не играю.")
                

class MusicView(discord.ui.View):
    
    def __init__(self, music):
        super().__init__()
        self.music = music
    
    
    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏹️")
    async def stop_button_callback(self, button, interaction):

        voice = discord.utils.get(self.music.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            voice_channel = interaction.guild.voice_client

            if interaction.user.voice is None:
                await interaction.response.send_message("Не твое - не трогай.")
                return

            if voice_channel.channel != interaction.user.voice.channel:
                await interaction.response.send_message("Я играю в другом канале.")
                return

            embed = discord.Embed(title="Остановлено", color=0xff0000)
            embed.set_thumbnail(url=self.music.music_queue[0]["thumb"])
            timestamp = self.music._get_timestamp(False)
            embed.add_field(name=str(self.music.music_queue[0]["title"]),
                            value="На ``[" + str(timestamp) + "]``\n" + "Заказал " + (self.music.music_queue[0]["user"]))
            await interaction.response.send_message(embed=embed)

            await voice_channel.disconnect()

            self.music.music_queue.clear()
            self.music.repeat_one = False
            self.music.repeat_all = False

            await self.message.edit(view=None)
        else:
            await interaction.response.send_message("Я даже не играю.")


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⏭️")
    async def next_button_callback(self, button, interaction):
        voice = discord.utils.get(self.music.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            voice_channel = interaction.guild.voice_client

            if interaction.user.voice is None:
                await interaction.response.send_message("Не твое - не трогай.")
                return

            if voice_channel.channel != interaction.user.voice.channel:
                await interaction.response.send_message("Я играю в другом канале.")
                return

            embed = discord.Embed(title="Пропущено", color=0x9d00ff)
            embed.set_thumbnail(url=self.music.music_queue[0]["thumb"])
            timestamp = self.music._get_timestamp()
            embed.add_field(name=str(self.music.music_queue[0]["title"]),
                            value="На ``[" + str(timestamp) + "]``\n" + "Заказал " + (self.music.music_queue[0]["user"]))

            if len(self.music.music_queue) == 1 and not self.music.repeat_one and not self.music.repeat_all:
                await interaction.response.send_message(embed=embed)
                await voice_channel.disconnect()

                self.music.music_queue.clear()
                return

            voice.stop()
            await interaction.response.send_message(embed=embed)

            await self.message.edit(view=None)
        else:
            await interaction.response.send_message("Я даже не играю.")


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔀")
    async def shuffle_button_callback(self, button, interaction):
        voice = discord.utils.get(self.music.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            if len(self.music.music_queue) == 1:
                await interaction.response.send_message("Нечего мешать.")
                return

            voice_channel = interaction.guild.voice_client

            if interaction.user.voice is None:
                await interaction.response.send_message("Не твое - не трогай.")
                return

            if voice_channel.channel != interaction.user.voice.channel:
                await interaction.response.send_message("Я играю в другом канале.")
                return

            backup = self.music.music_queue[0]
            del self.music.music_queue[0]
            random.shuffle(self.music.music_queue)
            self.music.music_queue.insert(0, backup)

            await interaction.response.send_message("Успешно перемешано.")
        else:
            await interaction.response.send_message("Я даже не играю.")


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔁")
    async def loop_button_callback(self, button, interaction):
        voice = discord.utils.get(self.music.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            voice_channel = interaction.guild.voice_client

            if interaction.user.voice is None:
                await interaction.response.send_message("Не твое - не трогай.")
                return

            if voice_channel.channel != interaction.user.voice.channel:
                await interaction.response.send_message("Нельзя помешать вечеринке не участвуя в ней.")
                return

            if not self.music.repeat_all:
                self.music.repeat_one = False
                self.music.repeat_all = True
                await interaction.response.send_message("Переключил на повтор всей очереди.")
            elif self.music.repeat_all:
                self.music.repeat_all = False
                await interaction.response.send_message("Выключил повтор всей очереди.")
        else:
            await interaction.response.send_message("Я даже не играю.")


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔂")
    async def loop_one_button_callback(self, button, interaction):
        voice = discord.utils.get(self.music.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            voice_channel = interaction.guild.voice_client

            if interaction.user.voice is None:
                await interaction.response.send_message("Не твое - не трогай.")
                return

            if voice_channel.channel != interaction.user.voice.channel:
                await interaction.response.send_message("Нельзя помешать вечеринке не участвуя в ней.")
                return

            if not self.music.repeat_one:
                self.music.repeat_one = True
                self.music.repeat_all = False
                await interaction.response.send_message("Переключил на повтор трека.")
            elif self.music.repeat_one:
                self.music.repeat_one = False
                await interaction.response.send_message("Выключил повтор трека.")
        else:
            await interaction.response.send_message("Я даже не играю.")