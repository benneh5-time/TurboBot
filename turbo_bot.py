import discord
from discord.ext import commands, tasks
import json
import asyncio
import mu
import os
import argparse
import random

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
game_host_name = "Mafia Host"
current_setup = "joat10"
valid_setups = ["joat10", "vig10", "cop9", "cop13"] #future setups
allowed_channels = [223260125786406912]  # turbo-chat channel ID
status_id = None
status_channel = None
is_rand_running = False

def save_recruit_list():
    with open('recruit_list.json', 'w') as f:
        json.dump(recruit_list, f)

def load_recruit_list():
    try:
        with open('recruit_list.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_aliases():
    with open('aliases.json', 'w') as f:
        json.dump(aliases, f)

def load_aliases():
    try:
        with open("aliases.json", "r") as f:
            loaded_aliases = json.load(f)
            aliases.update({int(id): alias for id, alias in loaded_aliases.items()})
    except FileNotFoundError:
        pass
        
def save_player_list(player_list, waiting_list, current_setup, game_host_name, player_limit):
    with open('player_list_data.json', 'w') as f:
        json.dump({"player_list": player_list, "waiting_list": waiting_list, "current_setup": current_setup, "game_host_name": game_host_name, "player_limit": player_limit}, f)
       
def load_player_list():
    global player_list, waiting_list, current_setup, game_host_name, player_limit
    try:
        with open('player_list_data.json', 'r') as f:
            data = json.load(f)
        player_list = data.get('player_list')
        waiting_list = data.get('waiting_list')
        current_setup = data.get('current_setup')
        game_host_name = data.get('game_host_name')
        player_limit = data.get('player_limit')
        return player_list, waiting_list, current_setup, game_host_name, player_limit
    except FileNotFoundError:
        return {}, {}
    except json.JSONDecodeError:
        return {}, {}

@bot.event
async def on_ready():
    global players, waiting_list, current_setup, game_host_name, player_limit, recruit_list
    print(f"We have logged in as {bot.user}", flush=True)
    load_aliases()
    players, waiting_list, current_setup, game_host_name, player_limit = load_player_list()
    recruit_list = load_recruit_list()
    
    if players is None:
        players = {}
    if waiting_list is None:
        waiting_list = {}
    if current_setup is None:
        current_setup = "joat10" 
    if game_host_name is None:
        game_host_name = "Mafia Host" 
    if player_limit is None:
        player_limit = 10  
    # Start looping task
    update_players.start()  # Start background task

@bot.command()
async def game(ctx, setup_name=None):
    if ctx.channel.id not in allowed_channels:  
        return

    global current_setup, player_limit, players, waiting_list

    if setup_name is None:
        await ctx.send(f"The current game setup is '{current_setup}'. To change the setup, use !game <setup_name>. Valid setup names are: {', '.join(valid_setups)}.")
    elif setup_name in valid_setups:
        if setup_name == "cop9":
            new_player_limit = 9
        elif setup_name == "vig10" or setup_name == "joat10":
            new_player_limit = 10
        elif setup_name == "cop13":
            new_player_limit = 13
        else:
            await ctx.send(f"'{setup_name}' is not a valid setup name. Please choose from: {', '.join(valid_setups)}.")
            return
        
        if new_player_limit < len(players):
            await ctx.send(f"Cannot change setup to '{setup_name}'. The current number of players ({len(players)}) exceeds the player limit for this setup ({new_player_limit}).")
            return
        
        while new_player_limit > len(players) and len(waiting_list) > 0:
            next_in_line = waiting_list.popitem()
            players[next_in_line[0]] = next_in_line[1]
            
        current_setup = setup_name
        player_limit = new_player_limit
        
        await ctx.send(f"The game setup has been changed to '{current_setup}'")
    else:
        await ctx.send(f"'{setup_name}' is not a valid setup name. Please choose from: {', '.join(valid_setups)}.")
    await update_status()        
    
@bot.command(name="in")
async def in_(ctx, time: int = 60):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    if ctx.author.id not in aliases:
        await ctx.send("Please set your MU username by using !alias MU_Username before inning!")
        return

    alias = aliases[ctx.author.id]
    global game_host_name, player_limit, players, waiting_list

    if time < 10 or time > 90:
        await ctx.send("Invalid duration. Please choose a duration between 10 and 90 minutes.")
        return
        
    if game_host_name == alias:
        game_host_name = "Mafia Host"
        if len(players) < player_limit:
            players[alias] = time
            await ctx.send(f"{alias} has been removed as host and added to the list for the next {time} minutes.")
            
            return
        else:
            waiting_list[alias] = time 
            await ctx.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
            
            return
            
    if alias in players or alias in waiting_list:
        if alias in players:
            players[alias] = time
            
        else:
            waiting_list[alias] = time
            
        await ctx.send(f"{alias}'s in has been renewed for the next {time} minutes.")
    else:
        if len(players) < player_limit:
            players[alias] = time            
            await ctx.send(f"{alias} has been added to the list for the next {time} minutes.")
            
        else:
            waiting_list[alias] = time
            await ctx.send(f"The list is full. {alias} has been added to the waiting list.")
    await update_status()            

@bot.command()
async def out(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
        
    global game_host_name, player_limit, players, waiting_list 
    
    if ctx.author.id not in aliases:
        await ctx.send("You are not on the list and you haven't set an alias. Stop trolling me.")
        return

    alias = aliases[ctx.author.id]
    
    if game_host_name == alias:
        game_host_name = "Mafia Host"
        await ctx.send(f"{alias} has been removed as host")
        return
        
    if alias in players:
        del players[alias]
        await ctx.send(f"{alias} has been removed from the list.")
        
    elif alias in waiting_list:
        del waiting_list[alias]
        await ctx.send(f"{alias} has been removed from the waiting list.")
        
    else:
        await ctx.send(f"{alias} is not on the list.")

    # Add a player from waiting list to main list if it's not full
    if len(players) < player_limit and waiting_list:
        next_alias, next_time = waiting_list.popitem()
        players[next_alias] = next_time
        
        await ctx.send(f"{next_alias} has been moved from the waiting list to the main list.")
    await update_status()
@bot.command()
async def alias(ctx, *, alias):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    alias = alias.lower()
    if alias in aliases.values() or alias in players:
        await ctx.send(f"The alias {alias} is already taken or being used in a current sign-up. If someone has taken your alias, fight them.")
    else:
        old_alias = aliases.get(ctx.author.id)
        aliases[ctx.author.id] = alias
        save_aliases()
        await ctx.send(f"Alias for {ctx.author} has been set to {alias}.")

        # Update alias in players and waiting_list
        for player_list in [players, waiting_list]:
            for player in list(player_list.keys()):  # Create a copy of keys to avoid RuntimeError
                if player == old_alias:
                    player_list[alias] = player_list.pop(old_alias)                   
    await update_status()
        
@bot.command()
async def add(ctx, *, alias):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    alias = alias.lower()
    global game_host_name, player_limit, players, waiting_list
    
    if game_host_name == alias:
        game_host_name = "Mafia Host"
        if len(players) < player_limit:
            players[alias] = 60
            
            await ctx.send(f"{alias} has been removed as host and added to the list for the next 60 minutes.") 
            return
        else:
            waiting_list[alias] = 60             
            await ctx.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
            return
            
    if alias in players or alias in waiting_list:
        if alias in players:
            players[alias] = 60  # Default time
        else:
            waiting_list[alias] = 60  # Default time
        
        await ctx.send(f"{alias}'s in has been renewed for 60 minutes.")
    else:
        if len(players) < player_limit:
            players[alias] = 60  # Default time
            await ctx.send(f"{alias} has been added to the list with for 60 minutes.")
        else:
            waiting_list[alias] = 60  # Default time
            await ctx.send(f"The list is full. {alias} has been added to the waiting list.")
    await update_status()    

@bot.command()
async def remove(ctx, *, alias):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    alias = alias.lower()
    global game_host_name, player_limit, players, waiting_list
    
    if game_host_name == alias:
        game_host_name = "Mafia Host"
        await ctx.send(f"{alias} has been removed as host")
        return
        
    if alias in players:
        del players[alias]
        
        await ctx.send(f"{alias} has been removed from the list.")
    elif alias in waiting_list:
        del waiting_list[alias]
        
        await ctx.send(f"{alias} has been removed from the waiting list.")
    else:
        await ctx.send(f"{alias} is not on the list.")

    # Add a player from waiting list to main list if it's not full
    if len(players) < player_limit and waiting_list:
        next_alias, next_time = waiting_list.popitem()
        players[next_alias] = next_time
        
        await ctx.send(f"{next_alias} has been moved from the waiting list to the main list.")
    await update_status()
@bot.command()
async def status(ctx, *args):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
        
    global game_host_name, status_id, status_channel

    embed = discord.Embed(title="**Turbo sign-ups!**", description="Turbo Bot v1.0", color=0x1beb30)
    embed.add_field(name="**Game Setup**", value=current_setup, inline=True)
    embed.add_field(name="**Host**", value=game_host_name, inline=True)
    embed.add_field(name="", value="", inline=True)
    
    if players:
        player_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(players.items(), 1):
            player_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes remaining\n"
            
        spots_left = player_limit - len(players)
        if spots_left > 1:
            player_message += f"+{spots_left} !!\n"
        elif spots_left == 1:
            player_message += "+1 HERO NEEDED\n"
        else:
            player_message += "Game is full. Switch to a larger setup using `!game [setup]` or rand the game using `!rand -title \"Title of game thread\"`\n"        
        time_message +=  "!in to join!\n"  
        embed.add_field(name="**Players:**", value=player_message, inline=True)
        embed.add_field(name="**Time Remaining:**", value=time_message, inline=True)
        embed.add_field(name="", value="", inline=True)
    if waiting_list:
        waiting_list_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(waiting_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes remaining\n"
            
        embed.add_field(name="**Waiting List:**", value=waiting_list_message, inline=True)
        embed.add_field(name="**Time Remaining:**", value=time_message, inline=True)
        embed.add_field(name="", value="", inline=True)
    if not players and not waiting_list:
        embed.add_field(name="No players are currently signed up.", value="", inline=False)
    
    embed.set_thumbnail(url="https://i.imgur.com/7st6J5V.jpg")

    status_embed = await ctx.send(embed=embed)
    status_id = status_embed.id
    status_channel = ctx.channel
    print(status_id, flush=True)

async def update_status():

    global status_id 
    
    if status_id is None or status_channel is None:
        return
    
    status_message = await status_channel.fetch_message(status_id)
    embed = status_message.embeds[0]
    
    spots_left = player_limit - len(players)
    
    embed.set_field_at(0, name="**Game Setup**", value=current_setup, inline=True)
    embed.set_field_at(1, name="**Host**", value=game_host_name, inline=True)
    
    if players:
        player_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(players.items(), 1):
            player_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes remaining\n"
            
        spots_left = player_limit - len(players)
        if spots_left > 1:
            player_message += f"+{spots_left} !!\n"
        elif spots_left == 1:
            player_message += "+1 HERO NEEDED\n"
        else:
            player_message += "Game is full. Switch to a larger setup using `!game [setup]` or rand the game using `!rand -title \"Title of game thread\"`\n"        
        time_message +=  "!in to join!\n"
        
        print (len(embed.fields), flush=True)
        if len(embed.fields) > 4:
            embed.set_field_at(3, name="**Players:**", value=player_message, inline=True)
            embed.set_field_at(4, name="**Time Remaining:**", value=time_message, inline=True)
        else:
            embed.set_field_at(3,name="**Players:**", value=player_message, inline=True)
            embed.add_field(name="**Time Remaining:**", value=time_message, inline=True)
            embed.add_field(name="", value="", inline=True)
    
    if waiting_list:
        waiting_list_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(waiting_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes remaining\n"            
        if len(embed.fields) > 5:
            embed.set_field_at(5, name="**Waiting List:**", value=waiting_list_message, inline=True)
            embed.set_field_at(6, name="**Time Remaining:**", value=time_message, inline=True)
        else:
            embed.add_field(name="**Waiting List:**", value=waiting_list_message, inline=True)
            embed.add_field(name="**Time Remaining:**", value=time_message, inline=True)
        
    if not players and not waiting_list:
        if len(embed.fields) > 3:
            embed.set_field_at(3, name="No players are currently signed up.", value="", inline=False)
        else:
            embed.add_field(name="No players are currently signed up.", value="", inline=False)
    
    await status_message.edit(embed=embed)
    

@bot.command()
async def host(ctx, *, host_name=None):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
        
    global game_host_name
    
    if host_name is None:
        if ctx.author.id in aliases:
            host_name = aliases[ctx.author.id]
        else:
            await ctx.send("You have not set an alias. Please use `!alias [MU Username]` before trying to use !host or !in commands.")
            return
            
    if host_name in players or host_name in waiting_list:
        await ctx.send(f"{host_name} is already on the turbo list or waiting list.\n Please choose a different name for the host.")
        return
    
    game_host_name = host_name
    
    await ctx.send(f"Host for the next turbo has been set to {host_name}!")
    await update_status()
    
@tasks.loop(minutes=1)
async def update_players():
    global player_limit, recruit_timer
    
    if recruit_timer > 0:
        recruit_timer -= 1
    for alias in list(players.keys()):
        players[alias] -= 1
        if players[alias] <= 0:
            await bot.get_channel(223260125786406912).send(f"{alias} has run out of time and has been removed from the list.")
            del players[alias]

            # Add a player from waiting list to main list if it's not full
            if len(players) < player_limit and waiting_list:
                next_alias, next_time = waiting_list.popitem()
                players[next_alias] = next_time
                await bot.get_channel(223260125786406912).send(f"{next_alias} has been moved from the waiting list to the main list.")
    save_player_list(players, waiting_list, current_setup, game_host_name, player_limit)
    
@bot.command()
async def rand(ctx, *args):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    global player_limit, game_host_name, current_setup, is_rand_running
    
    if len(players) < player_limit:
        await ctx.send(f"Not enough players to start a game. Need {player_limit} players.")
        return
        
    if is_rand_running:
        await ctx.send("The !rand command is currently being processed. Please wait.")
        return
    
    is_rand_running = True
    
    try:
        player_aliases = list(players.keys())[:player_limit]
    
        username = os.environ.get('MUUN')
        password = os.environ.get('MUPW')
        
        # args = shlex.split(' '.join(args))
        parser = argparse.ArgumentParser()
        parser.add_argument('-title', default=None)
        parser.add_argument('-thread_id', default=None)
        
        try:
            args_parsed = parser.parse_args(args)
        except SystemExit:
            await ctx.send(f"Invalid arguments. Please check your command syntax. Do not use `-`, `--`, or `:` in your titles and try again.")
            return
        except Exception as e:
            await ctx.send(f"An unexpected error occurred. Please try again.\n{str(e)}")
            return
        
        #Login and get Initial Token
        session = mu.login(username, password)
        security_token = mu.new_thread_token(session)
        
        game_title = args_parsed.title
        thread_id = args_parsed.thread_id
        
        if not thread_id:
            if not game_title:
                game_title = mu.generate_game_thread_uuid()
            thread_id = mu.post_thread(session, game_title, security_token, current_setup)
            
        await ctx.send(f"Attempting to rand `{game_title}`, a {current_setup} game using thread ID: `{thread_id}`. Please standby.")
        
        security_token = mu.new_game_token(session, thread_id)
        response_message = mu.start_game(session, security_token, game_title, thread_id, player_aliases, current_setup, game_host_name)
        
        if "was created successfully." in response_message:
            # Use aliases to get the Discord IDs
            
            mention_list = []
            
            for player in player_aliases:
                for key, value in aliases.items():
                    if player == value:
                        mention_list.append(int(key))
                        
            player_mentions = " ".join([f"<@{id}>" for id in mention_list])
            game_url = f"https://www.mafiauniverse.com/forums/threads/{thread_id}"  # Replace BASE_URL with the actual base URL
            await ctx.send(f"{player_mentions} randed STFU {game_url}")
            
    
            game_host_name = "Mafia Host"
            players.clear()
            players.update(waiting_list)
            waiting_list.clear()
        elif "Error" in response_message:
            await ctx.send(f"Game failed to rand, reason: {response_message}\nPlease fix the error and re-attempt the rand with thread_id: {thread_id} by typing '!rand -thread_id \"{thread_id}\" so a new game thread is not created.")    
    
    finally:
        is_rand_running = False
        
@bot.command()
async def clear(ctx, *args):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
        
    global players, waiting_list, game_host_name, current_setup    
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-confirm', action='store_true') 
    
    try:
        args_parsed = parser.parse_args(args)
    except SystemExit:
        await ctx.send("Invalid arguments. Type `!clear -confirm` to clear the queue otherwise f off")
        return
    
    if args_parsed.confirm:        
        players = {}
        waiting_list = {}
        game_host_name = "Mafia Host"
        current_setup = "joat10"        
        await ctx.send("Player and waiting list has been cleared. Game is JOAT10 and host is Mafia Host")
    else:
        await ctx.send("To clear, run !clear -confirm")
        
@bot.command(name='help')
async def help(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    embed = discord.Embed(title="Bot Commands", description="Here are the commands you can use:", color=0x1e00ff)
    embed.add_field(name="!in", value="Joins the player list. You must first set an alias using `!alias` before joining. Optionally specify duration with a number, e.g. `!in 60` to join for 60 minutes.", inline=False)
    embed.add_field(name="!out", value="Leaves the player list.", inline=False)
    embed.add_field(name="!add", value="Add a player to the player list. Must specify player's username, e.g. `!add MU_Username`. You cannot control the duration with this command.", inline=False)
    embed.add_field(name="!remove", value="Removes a player from the player list. Must specify player's username, e.g. `!remove MU_Username`.", inline=False)
    embed.add_field(name="!rand", value="Randomly selects a game setup from a pre-defined list. Additional arguments may be used to specify thread title or id, e.g. `!rand -title \"Game Title\" -thread_id \"123456\"`.", inline=False)
    embed.add_field(name="!alias", value="Sets the user's Mafia Universe username for use in other commands, e.g. `!alias MU_Username`.", inline=False)
    embed.add_field(name="!clear", value="Resets the current game to defaults. Must be confirmed with `!clear -confirm`.", inline=False)
    embed.add_field(name="!status", value="Displays the current status of the game, including player list, waiting list, host, and setup.", inline=False)
    embed.add_field(name="!host", value="Sets the host of the game. By default, it will use your defined alias. You can specify a different host's username, e.g. `!host MU_Username`.", inline=False)
    embed.add_field(name="!game", value="Sets the game setup. Must specify setup name from available options: cop9, cop13, joat10, vig10. E.g. `!game cop9`.", inline=False)
    await ctx.send(embed=embed)
    
# The following is a troll command
@bot.command()
async def recruit(ctx, *args):
    if ctx.channel.id not in allowed_channels:  
        return
    global recruit_list, recruit_timer

    parser = argparse.ArgumentParser()
    parser.add_argument('-opt_in', action='store_true')
    parser.add_argument('-opt_out', action='store_true')
    
    try:
        args_parsed = parser.parse_args(args)
    except SystemExit:
        await ctx.send(f"wrong syntax dumbass")
        pass
    except Exception as e:
        await ctx.send(f"Invalid arguments. Please check your command syntax.\n{str(e)}")
        return
        
    if args_parsed.opt_in and args_parsed.opt_out:
        await ctx.send("You can't opt in and opt out at the same time.")
        return
        
    if args_parsed.opt_in:
        if str(ctx.author.id) not in recruit_list:
            recruit_list[str(ctx.author.id)] = str(ctx.author.id)
            save_recruit_list()
            await ctx.send(f"{ctx.author.mention} has opted in to be recruited.")
        else:
            await ctx.send("You're already in the recruit list.")
        
    elif args_parsed.opt_out:
        if str(ctx.author.id) in recruit_list:
            del recruit_list[str(ctx.author.id)]
            save_recruit_list()
            await ctx.send(f"{ctx.author.mention} has opted out of being recruited.")
        else:
            await ctx.send("You're not in the recruit list.")

    else:
        if recruit_timer > 0:
            await ctx.send(f"This command can only be used once every hour. Please try again in {recruit_timer} minutes.")
            return
        
        recruit_timer = 60
        
        if len(recruit_list) > 0:
            mention_list = [f"<@{id}>" for id in recruit_list]
            await ctx.send(' '.join(mention_list) + " come turbo!!")
        else:
            await ctx.send("No players have opted in to be recruited")
        
TOKEN = os.environ.get('TOKEN')
# Run the bot
bot.run(TOKEN)

