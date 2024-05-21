import discord
import random
import copy

from discord import option
from discord import ApplicationContext
from discord.ext import commands
from discord.ui.item import Item


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
    _roll(self, ctx: ApplicationContext, arg: int)
        Пишет пользователю результат подкидывания кубика от 1 до значения
        аргумента
    _flip(self, ctx: ApplicationContext)
        Пишет пользователю результат подкидывания монетки
    _deafen(self, ctx: ApplicationContext)
        Выключает входящий звук пользователю, включает если он был
        выключен
    _minesweeper(self, ctx: ApplicationContext)
        Игра в Сапера в поле 5 на 5
    _rockpaperscissors(self, ctx: ApplicationContext)
        Игра в Камень, Ножницы, Бумага на двоих
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

    @commands.slash_command(name="deafen", description="Выключение/включение себе входящего звука.")
    async def _deafen(self, ctx: ApplicationContext):
        """Выключает входящий звук пользователю, включает если он был
        выключен

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        user = ctx.user

        if user.voice.deaf:
            await user.edit(deafen=False)
            await ctx.respond(f"Включил входящий звук {user.mention} ({user.name}).",
                              ephemeral=True)
        else:
            await user.edit(deafen=True)
            await ctx.respond(f"Выключил входящий звук {user.mention} ({user.name}).",
                              ephemeral=True)

    @commands.slash_command(name="minesweeper", description="Игра Сапер, к сожалению только 5 на 5.")
    async def _minesweeper(self, ctx: ApplicationContext):
        """Игра Сапер
        Консольная имплементация: https://github.com/GEMATOGESH/minesweeper

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        view = MineSweeperView()
        await ctx.respond(view=view)

    @commands.slash_command(name="rockpaperscissors", description="Игра Камень, Ножницы, Бумага.")
    async def _rockpaperscissors(self, ctx: ApplicationContext):
        """Игра Камень, Ножницы, Бумага

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        view = RockPaperScissorsView()
        await ctx.respond(view=view)


class MineSweeperView(discord.ui.View):
    """
    Класс кнопок для игры в Сапера

    Атрибуты
    --------
    number_of_mines : int
        Число мин в игре
    field_x : int
        Длина поля по X
    field_y : int
        Длина поля по Y
    field : list[list[int | str]]
        Созданное игровое поле
    player_field : list[list[int | str]]
        Текущее поле со стороны игрока
    revealed_tiles : int
        Количество открытых клеток - для проверки конца игры

    Методы
    ------
    async def _print_classified_field(self)
        Вывод в консоль игрового поля
    async def _reveal_all(self)
        Открытие всех клеток игрового поля, обычно - в конце игры
    async def _reveal(self, i: int, j: int)
        Рекурсивное открытие клеток поля
    async def _button_update(self)
        Обновление стиля кнопки в соответствии с ситуацией в игре
    async def _button_callback(self, interaction: discord.Interaction)
        Обработчик нажатия на кнопки
    def _create_minefield(self)
        Создание игрового поля, заполнение его минами и числами
    """

    number_of_mines = 5
    field_x = 5
    field_y = 5

    user = None
    field = None
    player_field = None
    revealed_tiles = 0

    def __init__(self):
        """ Первичная инициализация игры: создание кнопок и добавление
        их в вью.
        """

        super().__init__()
        self._create_minefield()

        btns = [None] * self.field_x
        for i in range(self.field_x):
            btns[i] = [None] * self.field_x

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                btn = discord.ui.Button(style=discord.ButtonStyle.gray)
                btn.label = "?"
                btn.custom_id = str(i * self.field_y + j)
                btns[i][j] = btn

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                btns[i][j].callback = self._button_callback

                self.add_item(btns[i][j])

    async def _print_classified_field(self):
        """Отображение всего игрового поля, включая мины, используется
        только для дебага!
        """

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                print(self.field[i][j], end="")

            print()

    async def _reveal_all(self):
        """Открытие всех клеток на поле (обычно по окончанию игры)
        """

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                self.player_field[i][j] = self.field[i][j]

    async def _reveal(self, i: int, j: int):
        """Рекурсивное открытие клетки по координатам (i, j)

        Параметры
        ----------
        i : int
            Позиция по оси Х на поле
        j : int
            Позиция по оси Y на поле

        Возвращает
        -------
        bool
            Безопасна ли клетка, False в случае открытия мины
        """

        if self.player_field[i][j] == "?":
            if self.field[i][j] == "m":
                await self._reveal_all()
                return False

            self.player_field[i][j] = self.field[i][j]
            self.revealed_tiles += 1

            if self.field[i][j] == 0:
                if i > 0 and j > 0:
                    await self._reveal(i-1, j-1)  # NW
                if i > 0:
                    await self._reveal(i-1, j)  # N
                if i > 0 and j < (self.field_x - 1):
                    await self._reveal(i-1, j+1)  # E
                if j > 0:
                    await self._reveal(i, j-1)  # W
                if j < (self.field_x - 1):
                    await self._reveal(i, j+1)  # E
                if i < (self.field_y - 1) and j > 0:
                    await self._reveal(i+1, j-1)  # SW
                if i < (self.field_y - 1):
                    await self._reveal(i+1, j)  # S
                if i < (self.field_y - 1) and j < (self.field_x - 1):
                    await self._reveal(i+1, j+1)  # SE
            return True

        if self.player_field[i][j] != "?" and self.player_field[i][j] != "m":
            return True

    async def _button_update(self):
        """Обновление стиля кнопки в соответствии с ситуацией на поле
        """

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                if self.player_field[i][j] != "?":
                    id = i * self.field_y + j

                    if self.player_field[i][j] == "m":
                        self.children[id].style = discord.ButtonStyle.red
                        self.children[id].label = "💣"
                    else:
                        if self.player_field[i][j] == 0:
                            self.children[id].style = discord.ButtonStyle.gray

                        if 8 >= self.player_field[i][j] >= 1:
                            self.children[id].style = discord.ButtonStyle.blurple

                        self.children[id].label = str(self.player_field[i][j])

                    self.children[id].disabled = True

    async def _button_callback(self, interaction: discord.Interaction):
        """Ивент нажатия на кнопку на поле

        Параметры
        ----------
        interaction : discord.Interaction
            Объект взаимодействия с кнопкой
        """

        if self.user is None:
            self.user = interaction.user
        else:
            if self.user != interaction.user:
                await interaction.respond("Найди себе свое минное поле.", ephemeral=True)
                return

        id = int(interaction.custom_id)
        i = id // 5
        j = id % 5

        res = await self._reveal(i, j)
        await self._button_update()
        await interaction.response.edit_message(view=self)

        if not res:
            await interaction.respond("BOOM!")
            return

        if self.revealed_tiles == self.field_x * self.field_y - self.number_of_mines:
            await self._reveal_all()
            await self._button_update()
            await interaction.response.edit_message(view=self)
            await interaction.respond("WIN!")

    def _create_minefield(self):
        """Создание игрового поля, заполнение его минами и числами
        """

        self.field = [None] * self.field_x
        for i in range(self.field_x):
            self.field[i] = [None] * self.field_x

        self.player_field = copy.deepcopy(self.field)

        indxs = []
        for _ in range(self.number_of_mines):
            while True:
                pretendent = random.randint(0, self.field_x * self.field_y - 1)
                if pretendent not in indxs:
                    indxs.append(pretendent)
                    break

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                pos = i * self.field_y + j

                if pos in indxs:
                    self.field[i][j] = "m"

                self.player_field[i][j] = "?"

        for i in range(0, self.field_x):
            for j in range(0, self.field_y):
                if self.field[i][j] != "m":
                    neighbors = []
                    if i > 0 and j > 0:
                        neighbors.append(self.field[i-1][j-1])  # NW
                    if i > 0:
                        neighbors.append(self.field[i-1][j])  # N
                    if i > 0 and j < (self.field_x - 1):
                        neighbors.append(self.field[i-1][j+1])  # NE
                    if j > 0:
                        neighbors.append(self.field[i][j-1])  # W
                    if j < (self.field_x - 1):
                        neighbors.append(self.field[i][j+1])  # E
                    if i < (self.field_y - 1) and j > 0:
                        neighbors.append(self.field[i+1][j-1])  # SW
                    if i < (self.field_y - 1):
                        neighbors.append(self.field[i+1][j])  # S
                    if i < (self.field_y - 1) and j < (self.field_x - 1):
                        neighbors.append(self.field[i+1][j+1])  # SE

                    weight = 0
                    for neighbor in neighbors:
                        if neighbor == "m":
                            weight += 1

                    self.field[i][j] = weight


class RockPaperScissorsView(discord.ui.View):
    """
    Класс кнопок для игры в Камень, Ножницы, Бумагу

    Атрибуты
    --------
    players : list[dict, dict]
        Информация об игроках и их выборе

    Методы
    ------
    _button_callback(interaction: discord.Interaction)
        Обработка нажатий на кнопки, вывод результатов игры по окончанию
    """

    players = [{"id": None, "choice": None}, {"id": None, "choice": None}]

    def __init__(self):
        """ Первичная инициализация игры.
        """

        super().__init__()
        styles = [discord.ButtonStyle.green, discord.ButtonStyle.red]
        for i in range(0, 2):
            rock = discord.ui.Button(label=f"Игрок {str(
                i + 1)}", emoji="🪨", style=styles[i], row=i, custom_id=f"{i}0")
            rock.callback = self._button_callback
            self.add_item(rock)

            scissors = discord.ui.Button(label=f"Игрок {str(
                i + 1)}", emoji="✂️", style=styles[i], row=i, custom_id=f"{i}1")
            scissors.callback = self._button_callback
            self.add_item(scissors)

            paper = discord.ui.Button(label=f"Игрок {str(
                i + 1)}", emoji="📜", style=styles[i], row=i, custom_id=f"{i}2")
            paper.callback = self._button_callback
            self.add_item(paper)

    async def _button_callback(self, interaction: discord.Interaction):
        """Ивент нажатия на кнопку, т.к. одио событие отвечает 
        за все кнопки, обрабатываем все случаи.

        Параметры
        ----------
        interaction : discord.Interaction
            Объект взаимодействия с кнопкой
        """

        if interaction.user == self.players[0]["id"] or interaction.user == self.players[1]["id"]:
            await interaction.respond(f"{interaction.user.mention}, ты уже сделал выбор.", ephemeral=True)
            return

        player = int(interaction.custom_id[0])
        choice = int(interaction.custom_id[1])

        match choice:
            case 0:
                choice = "камень"
            case 1:
                choice = "ножницы"
            case 2:
                choice = "бумагу"

        self.players[player]["id"] = interaction.user
        self.players[player]["choice"] = choice

        for button_id in range(0, 3):
            self.children[player * 3 + button_id].disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.respond(f"{interaction.user.mention}, ты выбрал {choice}.", ephemeral=True)

        if self.players[0]["id"] is not None and self.players[1]["id"] is not None:
            result = 2

            if self.players[0]["choice"] == self.players[1]["choice"]:
                result = 0
            elif self.players[0]["choice"] == "камень":
                if self.players[1]["choice"] == "ножницы":
                    result = 1
            elif self.players[0]["choice"] == "ножницы":
                if self.players[1]["choice"] == "бумагу":
                    result = 1
            elif self.players[0]["choice"] == "бумагу":
                if self.players[1]["choice"] == "камень":
                    result = 1

            await interaction.channel.send(f"{self.players[0]["id"].mention} выбрал {self.players[0]["choice"]}.")
            await interaction.channel.send(f"{self.players[1]["id"].mention} выбрал {self.players[1]["choice"]}.")

            match result:
                case 0:
                    await interaction.channel.send("Победила дружба!")
                case 1:
                    await interaction.channel.send(f"Победил {self.players[0]["id"].mention}!")
                case 2:
                    await interaction.channel.send(f"Победил {self.players[1]["id"].mention}!")

# TODO: Tic Tac Toe
