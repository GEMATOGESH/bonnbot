
# BonnBot

Мультифункциональный дискорд бот. Поддерживает ведение лога, содержит набор команд для администрирования сервера, набор команд для работы с музыкой (также возможен вызов некоторых из команд через кнопки) и набор команд для рядовых участников сервера.


## Функции
### Ивенты

- Логирование дебаг информации в консоль и в `bonnbot.log`
- Логирование сообщений в консоль и в `bonnbot.log`
- Логирование команд и кто их вызвал в консоль и в `bonnbot.log`

### Admin cog

- `/say` - отправляет сообщение от имени бота с возможностью прикрепления файлов
- `/mute` - выключение микрофона пользователя, обратное его включение если он был выключен
- `/mute_all` - выключение или включение микрофонов пользователей в текущем голосовом канале
- `/move` - перемещение всех пользователей текущего голосового канала в канал на выбор
- `/kick` - кик пользователя с сервера
- `/ban` - бан пользователя с сервера
- `/timeout` - ограничение доступа к серверу на некоторый промежуток времени

### Default cog

- `/roll` - подкидывание кубика от 1 до значения аргумента
- `/flip` - подкидывание монетки
- `/deafen` - выключение входящего звука пользователю или его включение если он был выключен
- `/minesweeper` - игра в Сапера

### Music cog

- `/play` - запуск проигрывания музыки в текущем голосовом канале
- `/stop` - остановка проигрывания музыки, очистка очереди и покидание голосового канала
- `/shuffle` - перемешка музыкальной очереди
- `/skip` - пропуск текущего трека
- `/queue` - отображение музыкальной очереди
- `/loop` - включение или выключение повтора трека или всей очереди
- `/remove` - удаление композиции из очереди
- `/seek` - перемотка текущего трека
- `/nowplaying` - отображение текущего трека
## Запуск (Windows)

1. Скачать проект
2. Создать виртуальное окружение (https://docs.python.org/3/library/venv.html)
```bash
  python -m venv /path/to/new/virtual/environment
```
3. Активировать созданное виртуальное окружение
```bash
  /path/to/new/virtual/environment/Scripts/activate
```
4. Установить необходимые пакеты
```bash
  pip install -r requirements.txt
```
5. Установить переменные среды (см. ниже)
6. В файле bot.py в списке когов удалить `coalition` (опционально)
7. Запустить бота через 
```bash
  python bot.py
```
## Переменные среды

В боте используются 2 файла с переменными среды: один содержит основную информацию, другой - информацию для работы когов. Для работы бота необходимо переименовать файлы "template.env" и "cogs/template.env" в ".env" и "cogs/.env" соответственно.

### template.env:

`bot_key` - токен бота дискорда (https://discord.com/developers/applications/)

`servers` - идентификаторы серверов через запятую, необходимы для более быстрого обновления доступных команд

### cogs/template.env:

`cookie` - путь до файлов куки ютуба, необходим для проигрывания музыки у которой стоит возрастное ограничение

`owner_id` - идентификатор аккаунта человека, который держит бота, нужен для работы команды `/say`

`vk_login` - логин ВКонтакте, для работы музыки из сервиса

`vk_password` - пароль ВКонтакте, для работы музыки из сервиса

`ffmpeg_path` - путь к ffmpeg.exe, нужен для работы музыки

`valid_channel_id` - идентификатор текстового канала для заказа музыки, чтоб не засорять другие


## Изображения

Следующие команды имеют возможность отправки случайного изображения в ответе на вызов команды:
- `move`
- `mute`

Комманда `say` имеет возможность указания имени файла в качестве одного из параметров.

Если бот не найдет изображений на выбор - он отправит предустановленное текстовое сообщение, для предоставления возможности боту отправить файл необходимо создать следующую иерархию папок в папке с ботом:
```bash
.
├── ...
├── images           # Основная папка для изображений
│   ├── move         # Папка для изображений команды `move`
│   ├── mute         # Папка для изображений команды `mute`
│   └── say          # Папка для изображений команды `say`
├── bot.py
└── ...
```

Для своих будущих команд (если они будут), может использоваться модуль `images`, функция `get_random_image(path)` позволяет получить случайный файл из предоставленного пути.
