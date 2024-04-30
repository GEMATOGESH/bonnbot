import random
import discord
import os

def get_random_image(path: str):
    image_list = os.listdir(path)
    
    if len(image_list) > 0:
        return discord.File((path + random.choice(image_list)))
    else:
        return None