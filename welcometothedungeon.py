import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

game_active = False
players = []
dungeon = []
equipment = []
health = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def start(ctx):
    global game_active, players, dungeon, equipment, health
    if game_active:
        await ctx.send("A game is already in progress!")
    else:
        game_active = True
        players = [ctx.author]
        dungeon = []
        equipment = ['Sword', 'Shield', 'Healing Potion']
        health[ctx.author] = 3
        await ctx.send(f"Game started by {ctx.author.mention}! Type `!join` to join the game.")

@bot.command()
async def join(ctx):
    if game_active and ctx.author not in players and len(players) < 4:
        players.append(ctx.author)
        health[ctx.author] = 3
        await ctx.send(f"{ctx.author.mention} has joined the game!")
    elif ctx.author in players:
        await ctx.send("You are already in the game!")
    elif len(players) >= 4:
        await ctx.send("Game full")
    else:
        await ctx.send("No active game to join. Type `!start` to start a new game.")

