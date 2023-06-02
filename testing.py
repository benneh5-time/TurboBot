import discord
from discord.ext import commands, tasks
import json
import asyncio
import mu
import os
import argparse
import random
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents, help_command=None)

player_limit = 10
players = {}
waiting_list = {}
recruit_list = {}
recruit_timer = 0
aliases = {}
dvc_roles = {}
game_host_name = ["Mafia Host"]
current_setup = "joat10"
valid_setups = ["joat10", "vig10", "cop9", "cop13"] #future setups
allowed_channels = [223260125786406912]  # turbo-chat channel ID
dvc_channel = 1097200194157809757
status_id = None
status_channel = None
is_rand_running = False
turbo_ping_message = None


TOKEN = os.environ.get('TOKEN')
# Run the bot

class Processor:
	def __init__(self):
		self.processed_threadmarks = 1

	async def newtask(self):
		print("proc.newtask function started.", flush=True)
		self.processed_threadmarks += 1
		if self.processed_threadmarks < 3:
			print(f"variable under 3. wait {self.processed_threadmarks} more minute(s)", flush=True)
		else:
			print("variable is 3. trying task.cancel()", flush=True)
			task.stop()
			print("task.cancel() complete. rest of code should finish", flush=True)

proc = Processor()
async def rand():
    print("rand command started, starting task.start()", flush=True)
    await task.start()
    print("task.start() closed out. exiting rand function", flush=True)

@tasks.loop(minutes=1)
async def task():
    print("task.start started", flush=True)
    await proc.newtask()
    print("task.start closing. proc.newtask finished/closed", flush=True)



@bot.event
async def on_ready():
    await rand()

bot.run(TOKEN)