import discord
import random
import copy
import requests

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
    guild_ids : list
        Список идентификаторов серверов, к которым подключен бот

    Методы
    ------
    _roll(ctx: ApplicationContext, arg: int)
        Пишет пользователю результат подкидывания кубика от 1 до значения
        аргумента
    _flip(ctx: ApplicationContext)
        Пишет пользователю результат подкидывания монетки
    _deafen(ctx: ApplicationContext)
        Выключает входящий звук пользователю, включает если он был
        выключен
    _minesweeper(ctx: ApplicationContext)
        Игра в Сапера в поле 5 на 5
    _rockpaperscissors(ctx: ApplicationContext)
        Игра в Камень, Ножницы, Бумага на двоих
    _tictactoe(ctx: ApplicationContext)
        Игра в Крестики-Нолики
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
        message = "*Все мы игрушки в руках судьбы, <...> и"\
                  "теперь наше будущее зависит от того, "\
                  "как лягут игральные кости."\
                  "Не дрогнет ли рука провидения?..*\n"\
            f"Выпало **{str(num)}**"
        match num:
            case 1:
                message += "\n*Кол!*"
            case 3:
                message += "\n*Трое!*"
            case 10:
                message += "\n*Бычий глаз!*"
            case 11:
                message += "\n*Барабанные палочки!*"
            case 12:
                message += "\n*Дюжина!*"
            case 13:
                message += "\n*Чертова дюжина!*"
            case 18:
                message += "\n*В первый раз!*"
            case 22:
                message += "\n*Утята!*"
            case 25:
                message += "\n*Опять 25!*"
            case 44:
                message += "\n*Стульчики!*"
            case 50:
                message += "\n*Полста!*"
            case 55:
                message += "\n*Перчатки!*"
            case 66:
                message += "\n*Валенки!*"
            case 69:
                message += "\n*Nice!*"
            case 77:
                message += "\n*Топорики!*"
            case 88:
                message += "\n*Бабушка!*"
            case 89:
                message += "\n*Дедушкин сосед!*"
            case 90:
                message += "\n*Дедушка!*"

        embed = discord.Embed(title=f"Подкидывание кубика до {str(arg)}",
                              color=discord.Colour.blurple(),
                              description=message)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="flip", description="Подкидывает монетку.")
    async def _flip(self, ctx: ApplicationContext):
        """Подкидывание монетки

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        num = random.randint(0, 1)

        message = "*Счастье и горе — это две стороны монеты, "\
            "которую жизнь периодически ставит на ребро...*\n"

        if not num:
            message += "Выпал **орел**!"
        elif num:
            message += "Выпала **режка**!"
        else:
            message += "Выпало... ребро?"

        embed = discord.Embed(title="Подкидывание монетки",
                              color=discord.Colour.blurple(),
                              description=message)
        await ctx.respond(embed=embed)

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

        message = None
        if user.voice.deaf:
            await user.edit(deafen=False)
            message = "**Включил**"
        else:
            await user.edit(deafen=True)
            message = "**Выключил**"

        embed = discord.Embed(title="Входящий звук",
                              color=discord.Colour.blurple(),
                              description=f":headphones: {message} входящий звук.")
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="minesweeper", description="Игра Сапер, к сожалению только 5 на 5.")
    async def _minesweeper(self, ctx: ApplicationContext):
        """Игра Сапер
        Консольная имплементация: https://github.com/GEMATOGESH/minesweeper

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        await ctx.respond(view=MineSweeperView(ctx.user))

    @commands.slash_command(name="rockpaperscissors", description="Игра Камень, Ножницы, Бумага.")
    async def _rockpaperscissors(self, ctx: ApplicationContext):
        """Игра Камень, Ножницы, Бумага

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        await ctx.respond(view=RockPaperScissorsView())

    @commands.slash_command(name="tictactoe", description="Игра Крестики-Нолики.")
    async def _tictactoe(self, ctx: ApplicationContext):
        """Игра Крестики-Нолики

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        await ctx.respond(view=TicTacToeView())

    @commands.slash_command(name="blackjack", description="Игра в блекджек (американские правила).")
    async def _blackjack(self, ctx: ApplicationContext):
        """Игра в блекджек

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        """

        view = BlackjackView(ctx.user)
        await view.first_check(ctx)

    @commands.slash_command(name="color", description="Изображение соответствующего цвета.")
    @option("hex", description="16ричный код цвета.", required=True)
    async def _color(self, ctx: ApplicationContext, hex: str):
        """Получение цвета по 16ричному коду

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота 
        hex : str
            16ричный код цвета
        """

        answer = requests.get(f'https://singlecolorimage.com/get/{hex}/100x100')
        r,g,b = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
        
        if answer.status_code == 200:
            embed = discord.Embed(title=f"#{hex}",
                              color=discord.Color.from_rgb(r, g, b),
                              image=f'https://singlecolorimage.com/get/{hex[1:]}/100x100')
            await ctx.respond(embed=embed)
        else:
            await ctx.respond('Несуществующий цвет. Перепроверь код.')

    @commands.slash_command(name="color-random", description="Получение случайного цвета.")
    async def _color_random(self, ctx: ApplicationContext):
        """Получение случайного цвета

        Параметры
        ---------
        ctx : ApplicationContext
            Контекст взаимодействия с командой бота
        """
        
        color = discord.Color.random()
        hex = '#%02x%02x%02x' % (color.r, color.g, color.b)
        
        embed = discord.Embed(title=hex,
                              color=color,
                              image=f'https://singlecolorimage.com/get/{hex[1:]}/100x100')
        await ctx.respond(embed=embed)

class MineSweeperView(discord.ui.View):
    """
    Класс кнопок для игры в Сапера

    Методы
    ------
    _print_classified_field(self)
        Вывод в консоль игрового поля
    _reveal_all(self)
        Открытие всех клеток игрового поля, обычно - в конце игры
    _reveal(self, i: int, j: int)
        Рекурсивное открытие клеток поля
    _button_update(self)
        Обновление стиля кнопки в соответствии с ситуацией в игре
    _button_callback(self, interaction: discord.Interaction)
        Обработчик нажатия на кнопки
    _create_minefield(self)
        Создание игрового поля, заполнение его минами и числами
    """

    def __init__(self, user):
        """ Первичная инициализация игры: создание кнопок и добавление
        их в вью.
        """

        super().__init__()

        self.user = user
        self.number_of_mines = 5
        self.field_x = 5
        self.field_y = 5
        self.revealed_tiles = 0
        self.turns = 0

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

    async def _reveal(self, i: int, j: int) -> bool:
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

        if self.user != interaction.user:
            await interaction.respond("Найди себе свое минное поле.",
                                      ephemeral=True)
            return

        self.turns += 1

        id = int(interaction.custom_id)
        i = id // 5
        j = id % 5

        res = await self._reveal(i, j)

        embed = None
        if not res:
            embed = discord.Embed(title="BOOM! :boom:",
                                  color=discord.Colour.red(),
                                  description=f"Игрок {self.user.mention}\n"
                                  f"Количество ходов: **{self.turns}**")

        if self.revealed_tiles == self.field_x * self.field_y - self.number_of_mines:
            await self._reveal_all()

            embed = discord.Embed(title="Победа! :crown:",
                                  color=discord.Colour.gold(),
                                  description=f"Игрок {self.user.mention}\n"
                                  f"Количество ходов: **{self.turns}**")

        await self._button_update()
        await interaction.response.edit_message(view=self)

        if embed is not None:
            await interaction.respond(embed=embed)

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

    Методы
    ------
    _button_callback(interaction: discord.Interaction)
        Обработка нажатий на кнопки, вывод результатов игры по окончанию
    """

    def __init__(self):
        """ Первичная инициализация игры. Создание кнопок для игроков.
        """

        super().__init__()

        self.players = [{"id": None, "choice": None},
                        {"id": None, "choice": None}]

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

        if interaction.user == self.players[0]["id"] or \
           interaction.user == self.players[1]["id"]:
            await interaction.respond(f"{interaction.user.mention}, ты уже сделал выбор.",
                                      ephemeral=True)
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

        if self.players[0]["id"] is not None and\
           self.players[1]["id"] is not None:
            message = f":crown: Победил {self.players[1]["id"].mention}!"
            color = discord.Colour.red()

            if self.players[0]["choice"] == self.players[1]["choice"]:
                message = ":flag_white: Победила дружба!"
                color = discord.Colour.lighter_grey()
            elif self.players[0]["choice"] == "камень":
                if self.players[1]["choice"] == "ножницы":
                    message = ":crown: Победил "\
                        f"{self.players[0]["id"].mention}!"
                    color = discord.Colour.green()
            elif self.players[0]["choice"] == "ножницы":
                if self.players[1]["choice"] == "бумагу":
                    message = ":crown: Победил "\
                        f"{self.players[0]["id"].mention}!"
                    color = discord.Colour.green()
            elif self.players[0]["choice"] == "бумагу":
                if self.players[1]["choice"] == "камень":
                    message = f":crown: Победил "\
                        f"{self.players[0]["id"].mention}!"
                    color = discord.Colour.green()

            desc = f"{self.players[0]["id"].mention} выбрал "\
                f"{self.players[0]["choice"]}.\n "\
                f"{self.players[1]["id"].mention} выбрал "\
                f"{self.players[1]["choice"]}.\n "\
                f"\n{message}"

            embed = discord.Embed(title="🪨✂️📜",
                                  color=color,
                                  description=desc)
            await interaction.respond(embed=embed)


class TicTacToeView(discord.ui.View):
    """
    Класс кнопок для игры в Крестики-Нолики

    Методы
    ------
    _button_callback(interaction: discord.Interaction)
        Обработка нажатий на кнопки, вывод результатов игры по окончанию
    _disable_all_buttons()
        Выключает все кнопки в конце игры
    """

    def __init__(self):
        """ Первичная инициализация игры. Создание поля и кнопок.
        """

        super().__init__()
        self.players = []
        self.turn = 0
        self.symbols = ["❌", "🟢"]
        self.colors = [discord.ButtonStyle.red, discord.ButtonStyle.green]

        self.field = [None] * 3
        for i in range(3):
            self.field[i] = [None] * 3

        for i in range(0, 3):
            for j in range(0, 3):
                btn = discord.ui.Button(style=discord.ButtonStyle.gray)
                btn.label = "◻"
                btn.custom_id = str(i * 3 + j)
                btn.row = i
                btn.callback = self._button_callback

                self.add_item(btn)

    async def _disable_all_buttons(self):
        """Выключает все кнопки во вью
        """

        for btn in self.children:
            btn.disabled = True

    async def _button_callback(self, interaction: discord.Interaction):
        """Ивент нажатия на кнопку, т.к. одио событие отвечает 
        за все кнопки, обрабатываем все случаи
        #TODO Проверки конца игры не самые красивые

        Параметры
        ----------
        interaction : discord.Interaction
            Объект взаимодействия с кнопкой
        """

        if len(self.players) < 2 or interaction.user in self.players:
            if len(self.players) == 0 or len(self.players) == 1 and\
               interaction.user not in self.players:
                self.players.append(interaction.user)

            if interaction.user in self.players:
                if self.turn % 2 == self.players.index(interaction.user):
                    i = int(interaction.custom_id) // 3
                    j = int(interaction.custom_id) % 3
                    id = i * 3 + j

                    self.field[i][j] = self.symbols[self.turn % 2]
                    self.children[id].label = self.symbols[self.turn % 2]
                    self.children[id].style = self.colors[self.turn % 2]
                    self.children[id].disabled = True

                    is_ended = False
                    for axys1 in range(0, 3):
                        if (self.field[axys1][0] == self.field[axys1][1] == self.field[axys1][2]) and \
                           (self.field[axys1][0] is not None) and \
                           (self.field[axys1][1] is not None) and \
                           (self.field[axys1][2] is not None):
                            for axys2 in range(0, 3):
                                id = axys1 * 3 + axys2
                                self.children[id].style = discord.ButtonStyle.blurple
                            await self._disable_all_buttons()
                            is_ended = True

                        if (self.field[0][axys1] == self.field[1][axys1] == self.field[2][axys1]) and \
                           (self.field[0][axys1] is not None) and \
                           (self.field[1][axys1] is not None) and \
                           (self.field[2][axys1] is not None):
                            for axys2 in range(0, 3):
                                id = axys2 * 3 + axys1
                                self.children[id].style = discord.ButtonStyle.blurple
                            await self._disable_all_buttons()
                            is_ended = True

                    if (self.field[0][0] == self.field[1][1] == self.field[2][2]) and \
                       (self.field[0][0] is not None) and \
                       (self.field[1][1] is not None) and \
                       (self.field[2][2] is not None):
                        self.children[0].style = discord.ButtonStyle.blurple
                        self.children[4].style = discord.ButtonStyle.blurple
                        self.children[8].style = discord.ButtonStyle.blurple
                        await self._disable_all_buttons()
                        is_ended = True

                    if (self.field[0][2] == self.field[1][1] == self.field[2][0]) and \
                       (self.field[0][2] is not None) and \
                       (self.field[1][1] is not None) and \
                       (self.field[2][0] is not None):
                        self.children[2].style = discord.ButtonStyle.blurple
                        self.children[4].style = discord.ButtonStyle.blurple
                        self.children[6].style = discord.ButtonStyle.blurple
                        await self._disable_all_buttons()
                        is_ended = True

                    await interaction.response.edit_message(view=self)

                    if is_ended:
                        await interaction.respond(f":crown: Победил {interaction.user.mention}.")

                    self.turn += 1
                    if self.turn == 9:
                        await interaction.respond(f":flag_white: Победила дружба.")

                    return
                else:
                    await interaction.respond("Не твой ход.", ephemeral=True)
                    return

        await interaction.respond("Ты не участвуешь в игре.", ephemeral=True)


class BlackjackView(discord.ui.View):
    """
    Класс кнопок для игры в Крестики-Нолики

    Методы
    ------
    _create_deck(self)
        Создание колды карт, состоящей из 4 стандартных колод
    _game_start(self)
        Начало игры, выдача начальных карт дилеру и игроку
    first_check(self, ctx: ApplicationContext)
        Первичная проверка конца игры, в случае если у дилера 21
    _game_results(self, winner: str, color: discord.Color)
        Составление сообщения конца игры
    _msg(self, hide=True)
        Составления сообщения текущего положения игры
    _get_dealer_hand(self, hide=True)
        Получение руки дилера в текстовом виде
    _get_player_hand(self)
        Получение руки игрока в текстовом виде
    _score(self, deck, hide=True)
        Получение счета руки
    _dealers_turn(self)
        Итерация ходов дилера до конца игры
    hit_callback(self, button: discord.ui.Button, interaction: discord.Interaction)
        Обработка ходов игрока
    stand_callback(self, button: discord.ui.Button, interaction: discord.Interaction)
        Обработка хода дилера
    """

    def __init__(self, user: discord.User):
        """
        Параметры
        ---------
        user : discord.User
            Пользователь вызвавщий команду

        Инициализация игры, создание колоды карт
        """

        super().__init__()

        self.deck = self._create_deck()
        self.dealer_hand = []
        self.player_hand = []

        self.player_id = user

        self._game_start()

    def _create_deck(self):
        """Создание игровой колоды

        Возвращает
        -------
        list
            Массив из словарей, представляющий собой 4 колоды игральных
            карт
        """

        suits = [":spades:", ":hearts:", ":clubs:", ":diamonds:"]

        deck = []
        for suit in suits:
            for i in range(2, 11):
                deck.append({"label": f"{i} {suit}", "value": i, "ace": False})

            deck.append({"label": f"Валет {suit}", "value": 10, "ace": False})
            deck.append({"label": f"Дама {suit}", "value": 10, "ace": False})
            deck.append({"label": f"Король {suit}", "value": 10, "ace": False})

            deck.append({"label": f"Туз {suit}", "value": 11, "ace": True})

        return deck * 4

    def _game_start(self):
        """Выдача дилеру и игроку двух карт
        """

        decks = [self.player_hand, self.dealer_hand]
        for i in range(0, 2):
            for _ in range(0, 2):
                id = random.randint(0, len(self.deck) - 1)
                decks[i].append(self.deck.pop(id))

    async def first_check(self, ctx: ApplicationContext):
        """Первичная проверка конца игры в случае если у дилера 21 с
        первой раздачи

        Параметры
        ----------
        ctx : ApplicationContext
            Контекст команды 
        """

        if await self._score(self.dealer_hand, False) == 21:
            embed = await self._game_results("Дилер", discord.Color.red())

            self.children.clear()
            await ctx.respond(embed=embed, view=self)

        elif await self._score(self.player_hand, False) == 21:
            embed = await self._dealers_turn()

            self.children.clear()
            await ctx.response.edit_message(embed=embed, view=self)

        else:
            embed = await self._msg()
            await ctx.respond(embed=embed, view=self)

    async def _game_results(self, winner: str, color: discord.Color) -> discord.Embed:
        """Генерация сообщения о победе

        Параметры
        ----------
        winner : str
            Имя победителя в игре
        color : discord.Color
            Цвет сообщения

        Возвращает
        -------
        discord.Embed
            Сообщение о победе
        """

        embed = await self._msg(hide=False)
        embed.title = f":crown: {winner}"
        embed.color = color

        return embed

    async def _msg(self, hide=True) -> discord.Embed:
        """Генерация сообщения о текущем положении игры

        Параметры
        ----------
        hide : bool, optional
            Скрывать ли первую карту в руке, by default True

        Возвращает
        -------
        discord.Embed
            Сообщение с текущим положением игры
        """

        embed = discord.Embed(title="Блекджек :spades: :hearts: :clubs: :diamonds:",
                              color=discord.Color.dark_green())
        if hide:
            embed.add_field(name="Рука Дилера",
                            value=await self._get_dealer_hand(hide=hide) + "\nСчет: ? + " +
                            str(await self._score(self.dealer_hand, hide=hide)),
                            inline=False)
        else:
            embed.add_field(name="Рука Дилера",
                            value=await self._get_dealer_hand(hide=hide) + "\nСчет: " +
                            str(await self._score(self.dealer_hand, hide=hide)),
                            inline=False)

        embed.add_field(name=f"Рука {self.player_id.display_name}",
                        value=await self._get_player_hand() + "\nСчет: " +
                        str(await self._score(self.player_hand, hide=False)),
                        inline=False)
        return embed

    async def _get_dealer_hand(self, hide=True) -> str:
        """Получение текстового описания руки дилера

        Параметры
        ----------
        hide : bool, optional
            Скрывать ли первую карту в руке, by default True

        Возвращает
        -------
        str
            Текстовое описание руки дилера
        """

        res = ""

        start = 0
        if hide:
            res += "?"
            start = 1

        for i in range(start, len(self.dealer_hand)):
            if i != 0:
                res += f", {self.dealer_hand[i]["label"]}"
            else:
                res += f"{self.dealer_hand[i]["label"]}"

        return res

    async def _get_player_hand(self) -> str:
        """Получение текстового описания руки игрока

        Возвращает
        -------
        str
            Текстовое описание руки игрока
        """

        res = self.player_hand[0]["label"]

        for i in range(1, len(self.player_hand)):
            res += f", {self.player_hand[i]["label"]}"

        return res

    async def _score(self, deck, hide=True) -> int:
        """Получение текущего счета колоды

        Параметры
        ----------
        deck : list
            Колода
        hide : bool, optional
            Скрывать ли первую карту в руке, by default True

        Возвращает
        -------
        int
            Счет предоставленной колоды
        """

        res = 0
        aces = 0

        start = 0
        if hide:
            start = 1

        for i in range(start, len(deck)):
            if deck[i]["ace"]:
                aces += 1

            res += deck[i]["value"]

        if res > 21:
            for _ in range(0, aces):
                res -= 10

                if res <= 21:
                    break

        return res

    async def _dealers_turn(self) -> discord.Embed:
        """Итерация хода дилера и получение сообщения о конце игры

        Возвращает
        -------
        discord.Embed
            Сообщение о конце игры
        """

        dealer_score = await self._score(self.dealer_hand, hide=False)
        player_score = await self._score(self.player_hand, hide=False)

        while True:
            if dealer_score < 17:
                id = random.randint(0, len(self.deck) - 1)
                self.dealer_hand.append(self.deck.pop(id))
                dealer_score = await self._score(self.dealer_hand, hide=False)
            else:
                break

        embed = None
        if player_score <= 21 and \
                (dealer_score < player_score or dealer_score > 21):
            embed = await self._game_results(self.player_id.display_name, discord.Color.gold())

        elif dealer_score == player_score and dealer_score != 21:
            embed = await self._game_results("Дружба!", discord.Color.light_gray())

        else:
            embed = await self._game_results("Дилер", discord.Color.red())

        return embed

    @discord.ui.button(style=discord.ButtonStyle.green, label="Hit")
    async def hit_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Обработка хода игрока, когда он берет дополнительную карту

        Параметры
        ----------
        button : discord.ui.Button
            Нажатая кнопка
        interaction : discord.Interaction
            Объект взаимодействия с кнопкой
        """

        if interaction.user != self.player_id:
            await interaction.respond("Найди себе свой стол", ephemeral=True)
            return

        id = random.randint(0, len(self.deck) - 1)
        self.player_hand.append(self.deck.pop(id))

        score = await self._score(self.player_hand, hide=False)
        embed = await self._msg()

        if score >= 21:
            embed = await self._dealers_turn()

            self.children.clear()

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.red, label="Stand")
    async def stand_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Обработка хода игрока, когда он закончил набирать карты

        Параметры
        ----------
        button : discord.ui.Button
            Нажатая кнопка
        interaction : discord.Interaction
            Объект взаимодействия с кнопкой
        """

        if interaction.user != self.player_id:
            await interaction.respond("Найди себе свой стол", ephemeral=True)
            return

        embed = await self._dealers_turn()
        self.children.clear()

        await interaction.response.edit_message(embed=embed, view=self)
