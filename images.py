import random
import discord
import os

def get_random_image(path: str):
    """Возвращает случайный файл из папки, в случае отсутствия - 
    возвращает None

    Параметры
    ---------
    path : str
        Путь до папки

    Возвращает
    ----------
    discord.File | None
        Файл или его отсутствие
    """

    image_list = os.listdir(path)
    
    if len(image_list) > 0:
        return discord.File((path + random.choice(image_list)))
    else:
        return None