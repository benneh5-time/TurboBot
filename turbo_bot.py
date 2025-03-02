import discord
from discord.ext import commands, tasks
from discord import Poll, Button
import json
import asyncio
import os
import argparse
import random
import requests
import csv
from bs4 import BeautifulSoup
import pandas as pd
import re
import shlex
import datetime
import sqlite3
from io import StringIO
# custom imports below
import mu
import winrate
from elo_library import EloCalculator
import gpt_responses

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=intents, help_command=None)

# Game settings
player_limit = 10
current_game = None
current_setup = "joat10"
current_timer = "14-3"
valid_setups = ["joat10", "vig10", "bean10", "bomb10", "bml10", "inno4", "ita10", "ita13", "cop9", "cop13", "paritycop9", "billager9", "doublejoat13", "random10er", "closedrandomXer", "randommadnessXer"]
valid_timers = ["sunbae", "14-3", "16-5", "8-2"]
day_length = 14
night_length = 3
anon_enabled = False
is_rand_running = False
ineligible_setups = ['ita10', 'ita13', 'randommadnessXer', 'inno4', 'bean10', 'bml10']
username = os.environ.get('MUUN')
password = os.environ.get('MUPW')

# Player and Host Data
players = {}
waiting_list = {}
delay_list = {}
recruit_list = {}
spec_list = {}
game_host_name = ["Turby"]
recruit_timer = 0
aliases = {}
game_processors = {}

# Misc Discord Information
mods = [178647349369765888, 93432503863353344, 966170585040306276, 438413352616722435]
allowed_channels = [223260125786406912, 1258668573006495774, 306758456998887429, 1337149623361601699]  # turbo-chat channel ID
test_channels = [1337149623361601699]
bet_channel = [306758456998887429]
all_channels = [223260125786406912, 1256131761390489600]
turbo_chat = 223260125786406912
react_channels = [223260125786406912, 1114212787141492788]
log_channel = 1336076934332813402
dvc_channel = 1114212787141492788  # DVC #turbo-chat channel id
dvc_server = 1094321402489872436   # DVC Server iddvc_roles = {}
dvc_roles = {}
anni_event_channels = [1258668573006495774]
message_ids = {}
bets = {}
# ceki ban ends 3/23 (35829273)
banned_users = [1173036536166621286, 358292734962040842]
banned_randers = [612706340623876137]
future_banned = [190312702692818946]
non_1337_users = [827416091889762325]
status_id = None
status_channel = None
turbo_ping_message = None
alexas = [438413352616722435]
ranked_game = True

###################################################### 
# Opening Functions 
###################################################### 

def load_dvc_archive():
    with open('dvc_archive.json', 'r') as f:
        return json.load(f)

def save_dvc_archive(new_archive):
    with open('dvc_archive.json', 'w') as f:
        json.dump(new_archive, f, indent=4)

def save_recruit_list():
    with open('recruit_list.json', 'w') as f:
        json.dump(recruit_list, f, indent=4)

def load_recruit_list():
    try:
        with open('recruit_list.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
def load_flavor_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_flavor_json(file, existing_flavor):
    with open(file, 'w') as f:
        json.dump(existing_flavor, f, indent=4)

def load_bet_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_bet_json(file, bets):
    with open(file, 'w') as f:
        json.dump(bets, f, indent=4)
        
def save_spec_list():
    with open('spec_list.json', 'w') as f:
        json.dump(spec_list, f, indent=4)

def load_spec_list():
    try:
        with open('spec_list.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Failed to load spec list", flush=True)
        return {}

def save_messages():
    with open('messages.json', 'w') as f:
        json.dump(message_ids, f, indent=4)

def load_messages():
    try:
        with open("messages.json", "r") as f:
            loaded_messages = json.load(f)
            message_ids.update({int(id): int(alias) for id, alias in loaded_messages.items()})
    except FileNotFoundError:
        pass

def save_aliases():
    try:
        with open('aliases.json', 'w') as f:
            json.dump(aliases, f, indent=4)
    except Exception as e:
        print(f"Error saving aliases: {e}")

def load_aliases():
    try:
        with open("aliases.json", "r") as f:
            loaded_aliases = json.load(f)
            aliases.update({int(id): alias for id, alias in loaded_aliases.items()})
    except FileNotFoundError:
        pass

def save_dvc_roles():
    with open('dvc_roles.json', 'w') as f:
        json.dump(dvc_roles, f, indent=4)

def load_dvc_roles():
    try:
        with open("dvc_roles.json", "r") as f:
            loaded_dvc_roles = json.load(f)
            dvc_roles.update({int(id): alias for id, alias in loaded_dvc_roles.items()})
    except FileNotFoundError:
        pass

def save_player_list(player_list, waiting_list, current_setup, game_host_name, player_limit):
    with open('player_list_data.json', 'w') as f:
        json.dump({"player_list": player_list, "waiting_list": waiting_list, "current_setup": current_setup, "game_host_name": game_host_name, "player_limit": player_limit}, f, indent=4)
       
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
        
def find_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if isinstance(val, dict):
            if value == val.get("active") or value in val.get("all", []):
                return key
        elif value == val:
            return key
    return None
  
dvc_archive = load_dvc_archive()

@bot.event
async def on_ready():
    global players, waiting_list, current_setup, game_host_name, player_limit, recruit_list, spec_list, bets
    print(f"We have logged in as {bot.user}", flush=True)
    load_aliases()
    load_dvc_roles()
    load_messages()
    bets = load_bet_json('bets.json')
    players, waiting_list, current_setup, game_host_name, player_limit = load_player_list()
    recruit_list = load_recruit_list()
    spec_list = load_spec_list()
    if players is None:
        players = {}
    if waiting_list is None:
        waiting_list = {}
    if current_setup is None:
        current_setup = "joat10" 
    if game_host_name is None:
        game_host_name = ["Turby"] 
    if player_limit is None:
        player_limit = 10  
    update_players.start()  # Start background task

@bot.command(name='add_bet')
async def add_bet(ctx, game:str, *, bet: str):
    if ctx.channel.id not in bet_channel:  # Restrict to certain channels
        return
    global bets
    if game not in bets:
        bets[game] = []
    bets[game].append(f"{ctx.author.name} bets: {bet}")
    save_bet_json('bets.json', bets)
    await ctx.send(f"Your bet has been added for {game}!")

@bot.command(name='bets')
async def bets(ctx, game: str = None):
    if ctx.channel.id not in bet_channel:  # Restrict to certain channels
        return
    global bets 
    bets = load_bet_json('bets.json')
    if game is None:
        if not bets:
            await ctx.send("No games with bets currently.")
        else:
            games_list = '\n'.join([f'```{game}```' for game in bets.keys()])
            await ctx.send(f'Games with bets: \n{games_list}')
    else:
        if game not in bets or not bets[game]:
            await ctx.send(f'No bets found for "{game}".')
        else:
            bets_list = '\n'.join([f'```{bet}```' for bet in bets[game]])
            await ctx.send(bets_list)

async def create_dvc(thread_id):
    guild = bot.get_guild(dvc_server)
    category_id = 1117176858304336012
    voice_id = 1216555729138221066
    role = await guild.create_role(name=f"DVC: {thread_id}", permissions=discord.Permissions.none())
    dvc_roles[int(thread_id)] = role.id
    save_dvc_roles()
    await guild.me.add_roles(role)
    category = guild.get_channel(category_id)
    channel = await guild.create_text_channel(
        name = f"DVC {thread_id}",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True)
        },
        category = category,
        position = 0

    )
    voice_channel = guild.get_channel(voice_id)
    await voice_channel.set_permissions(role, connect=True, speak=True)

    return role, channel.id, guild

async def create_wolf_chat(thread_id):
    guild = bot.get_guild(dvc_server)
    category_id = 1117176858304336012
    category = guild.get_channel(category_id)
    channel = await guild.create_text_channel(
        name = f"WC {thread_id}",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        },
        category = category,
        position = 0

    )
    return channel.id, guild

async def dvc_limit():

    category = bot.get_channel(dvc_archive)
    channel_count = len(category.channels)

    if channel_count == 50:
        print("at cap", flush=True)
    elif channel_count < 50:
        print("under cap @ " + str(channel_count), flush=True)
    else:
        print("idk", flush=True)

async def edit_dvc(channel, guild):

    global dvc_archive

    category = bot.get_channel(dvc_archive)
    # backup_category = bot.get_channel(backup_archive)
    channel_count = len(category.channels)

    if channel:
        #Set an overwrite for the default role so players can read messages in the channel after update
        permissions = channel.overwrites_for(guild.default_role)
        permissions.read_messages = True

        #Check to make sure we aren't at the channel cap for our primary category. If not, move channel to that category.
        #Otherwise we move to the backup category and create a help message to remind me to update this thing.
        if channel_count < 50:
            await channel.edit(category=category, position=1)
            await channel.edit(category=category, position=0)

        else:
            match = re.search(r'\d+$', category.name)
            if match:
                # Increment the numeric part and create the new category
                old_number = int(match.group())
                new_number = old_number + 1
                new_category_name = f'dvc archive {new_number}'
                new_category = await guild.create_category(name=new_category_name)
                await new_category.edit(position=2)
                await channel.edit(category=new_category, position=1)
                await channel.edit(category=new_category, position=0)
                dvc_archive = new_category.id
                save_dvc_archive(dvc_archive)
                
            
        await channel.set_permissions(guild.default_role, overwrite=permissions)
        await channel.send("This channel is now open to everyone")

async def delete_dvc_role(channel, role):
    guild = bot.get_guild(dvc_server)

    if role:
        try:
            await role.delete()
            await channel.send("DVC Role deleted for post-game clean up.")
        except:
            await channel.send("Failed to delete dvc role")
            
async def kill_player(thread_id, dead_player):
    session = mu.login(username, password)
    url = f"https://www.mafiauniverse.com/forums/modbot/api/death/?do=kill&threadid={thread_id}&username={dead_player}"
    kill = session.get(url)
    return kill.json()

async def revive_player(thread_id, revived_player):
    session = mu.login(username, password)
    url = f"https://www.mafiauniverse.com/forums/modbot/api/death/?do=revive&threadid={thread_id}&username={revived_player}"
    revive = session.get(url)
    return revive.json()

async def post_game_reply(thread_id, message):
    session = mu.login(username,password)
    game_id, security_token = mu.open_game_thread(session, thread_id)
    mu.post(session, thread_id, security_token, message)


async def start_itas(current_game):
    ita_session = mu.login(username, password)
    ita_game_id, ita_security_token = mu.open_game_thread(ita_session, current_game)
    mu.ita_window(ita_session, ita_game_id, ita_security_token)

async def get_wolf_info(game_title, setup_title):
    session = mu.login(username, password)
    mafia_players = []

    pms = session.get("https://www.mafiauniverse.com/forums/private.php")
    pm_html_list = BeautifulSoup(pms.text, 'html.parser')
    pm_list_parsed = pm_html_list.find_all('li', class_='blockrow pmbit')

    link = None
    for pm in pm_list_parsed:
        unread_span = pm.find('span', class_='unread')
        if unread_span:
            title = unread_span.find('a', class_='title')
            if title.text == f"{game_title} - [{setup_title} game] Host Information":
                link = title['href']

    base_url = "https://www.mafiauniverse.com/forums/"

    if link:
        link_content_html = session.get(base_url + link)
        link_content_parsed = BeautifulSoup(link_content_html.text, 'html.parser')
        mafia_section = link_content_parsed.find('font', string='Mafia Players (Roles)').find_next('br').find_all_next('b')

        for player in mafia_section:
            username = player.find('span', style="color: #ff2244;")
            if username:
                mafia_players.append(username.text)
    return mafia_players   

class ThreadmarkProcessor:
    def __init__(self):
        self.processed_threadmarks = []
        self.checked_zero_posters = False
        self.poll_created = False
        self.ping_zero_posters = False

    async def process_threadmarks(self, thread_id, player_aliases, role, guild, channel_id, game_setup, current_game):
        """Fetch and process threadmarks from Mafia Universe."""
        while True:        
            url = f"https://www.mafiauniverse.com/forums/threadmarks/{thread_id}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            event_div = soup.find("div", class_="bbc_threadmarks view-threadmarks")
            channel = bot.get_channel(channel_id)

            for row in reversed(event_div.find_all("div", class_="threadmark-row")):
                event = row.find("div", class_="threadmark-event").text.strip()
                event_link = row.find("a")

                if event in self.processed_threadmarks:
                    continue
                
                if "Event" in event or "Game Information" in event:
                    continue
                else:
                    await channel.send(event)
                
                if event_link:
                    href = event_link['href']
                    match = re.search(r'#post(\d+)', href)
                    if match:
                        post_id = match.group(1)                    
                stop_game = await self.handle_event(event, player_aliases, role, guild, channel, thread_id, game_setup, current_game, post_id)
                
                if stop_game:
                    return

                self.processed_threadmarks.append(event)

            if "Day 1 Start" in self.processed_threadmarks and "Night 1 Start" not in self.processed_threadmarks and not self.checked_zero_posters:
                current_vc = mu.get_vote_total(thread_id)
                if current_vc:
                    if mu.is_day1_near_end(current_vc):
                        self.checked_zero_posters = True
                        zero_posters = mu.get_zero_posters(current_vc)
                        if zero_posters:
                            zero_poster_mention_list = [
                                int(key) for name in zero_posters
                                for key, value in aliases.items()
                                if name.lower() == value['active'] or name.lower() in value['all']
                            ]
                            zp_mentions = " ".join(f"<@{id}>" for id in zero_poster_mention_list) if zero_poster_mention_list else "Player w/ discord unknown to Turby" 
                            sub_commands = "\n".join(f'Use `!sub "{name}"` if they have not been replaced or confirmed they are back' for name in zero_posters)
                            message = f"<@&327124222512070656> {zp_mentions} - the ongoing turbo has zero poster(s)/AFK(s) that need to be replaced:\n{sub_commands}"
                            
                            turbo_channel = bot.get_channel(turbo_chat)
                            await turbo_channel.send(message)
                            
            if "Day 1 Start" in self.processed_threadmarks and not self.ping_zero_posters:
                current_vc = mu.get_vote_total(thread_id)
                if current_vc:
                    if mu.is_day1_near_end(current_vc, minutes=10):
                        self.ping_zero_posters = True
                        zero_posters = mu.get_zero_posters(current_vc)
                        if zero_posters:
                            zero_poster_mention_list = [
                                int(key) for name in zero_posters
                                for key, value in aliases.items()
                                if name.lower() == value['active'] or name.lower() in value['all']
                            ]
                            zp_mentions = " ".join(f"<@{id}>" for id in zero_poster_mention_list) if zero_poster_mention_list else "" 
                            message = f"{zp_mentions} - game randed join pls: https://www.mafiauniverse.com/forums/threads/{thread_id}"
                            turbo_channel = bot.get_channel(turbo_chat)
                            await turbo_channel.send(message)
                                             
            await asyncio.sleep(30)

    async def handle_event(self, event, player_aliases, role, guild, channel, thread_id, game_setup, current_game, post_id=None):
        """Handles specific game events based on threadmarks."""
        
        elimination_keywords = ["Elimination:", "Bomb (1):", "Results:", "Shots Fired (1):", "Poison Results:", "Desperado (1):"]
        
        # Process eliminations and deaths
        if any(keyword in event for keyword in elimination_keywords) and " was " in event:
            results = event.split(max([keyword for keyword in elimination_keywords if keyword in event], key=len), 1)[1].strip()
            players = results.split(", ")

            for player in players:
                if " was " in player:
                    username, flavor = self.parse_player_info(player)
                    user_added = await self.add_player_to_dvc(username, player_aliases, guild, role, channel)

                    # Special case for "neil the eel"
                    if "neil the eel" in flavor:
                        await post_game_reply(thread_id, "have you seen this fish\n[img]https://i.imgur.com/u9QjIqc.png[/img]\n now you have")
            if "Elimination:" in event:
                eod_votes = mu.get_vote_total(thread_id, post_id)
                formatted_votes = mu.parse_votecount(eod_votes)
                message = await channel.send(f"``` {formatted_votes}```")
                await message.pin()
                pass

        elif "Results: No one died" in event:
            await post_game_reply(thread_id, "WTF NO DEATHS?"
                                  )
        elif "Event" in event or "Game Information" in event:
            pass

        elif "Day 2 Start" in event and game_setup in ('ita10', 'ita13'):
            await start_itas(current_game)

        elif "Elimination: Sleep" in event:
            eod_votes = mu.get_vote_total(thread_id, post_id)
            formatted_votes = mu.parse_votecount(eod_votes)
            await channel.send("https://media1.tenor.com/m/VdIKn05yIh8AAAAd/cat-sleep.gif")
            message = await channel.send(f"``` {formatted_votes}```")
            await message.pin()
            await post_game_reply(thread_id, "eepy\n\n[img]https://media1.tenor.com/m/VdIKn05yIh8AAAAd/cat-sleep.gif[/img]\n\neepy")
        elif "Game Over:" in event:
            await channel.send("Game concluded -- attempting channel housekeeping/clean up")
            self.processed_threadmarks.clear()
            return True
        
        return False
    
        '''elif "Night 1 Start" in event and not self.poll_created:
            try: 
                duration = datetime.timedelta(hours=1)
                poll = Poll(question="who wolf", duration=duration, multiple=True)
                if player_aliases:
                    for player in player_aliases[:10]:
                        poll.add_answer(text=player)
                    await channel.send("n0 turby w", poll=poll)
                    self.poll_created = True
                else:
                    for player in ['moppo', 'dark forces', 'abraham delacey']:
                        poll.add_answer(text=player)
                    await channel.send("n0 turby w", poll=poll)
                    self.poll_created = True
            except Exception as e:
                print(f"Couldn't create poll: {e}")
                self.poll_created = True
        '''



    async def add_player_to_dvc(self, username, player_aliases, guild, role, channel):
        """Attempts to add a player to the Dead Voice Chat (DVC) based on their alias."""
        for mention_id, alias_data in aliases.items():
            if username == alias_data.get("active", "").lower() or username in [alt.lower() for alt in alias_data.get("all", [])]:
                try:
                    member = guild.get_member(int(mention_id))
                    if member:
                        await member.add_roles(role)
                        await channel.send(f"<@{mention_id}> has been added to DVC.")
                        return True  # Success
                    else:
                        await channel.send(f"{username} could not be added to DVC. They are not in the server.")
                except Exception as e:
                    await channel.send(f"Error adding {username} to DVC: {e}")
                return True  # Prevents fallback message

        await channel.send(f"{username} could not be added to DVC. I don't have an alias for them!")
        return False

    def parse_player_info(self, player):
        """Extracts username and flavor text from a player string."""
        username, flavor = player.split(" was ", 1)
        return username.strip().lower(), flavor.strip().lower()

@bot.command()
async def sub(ctx, player=None):
    global current_game, aliases

    if ctx.channel.id not in allowed_channels:
        return

    if player == None:
        await ctx.send("Use !sub [Player_to_replace] to sub into the game. You will need an alias set in order to sub.")
        return
    if current_game == None:
        await ctx.send("No current game running or known thread_id to use. Ping @benneh his shits broken if there is a game running")
        return
    if ctx.author.id not in aliases:
        await ctx.send("Please set your MU username by using !alias MU_Username before inning!")
        return

    player_in = aliases[ctx.author.id]['active']
    
    #Login and get Initial Token
    session = mu.login(username, password)
    game_id, security_token = mu.open_game_thread(session, current_game)
    
    sub = mu.sub_player(session, game_id, player, player_in, security_token)
    if '"success":true' in sub:
        await ctx.send(f"{player} has been successfully replaced by {player_in}. <@{ctx.author.id}> please report to the game thread: https://www.mafiauniverse.com/forums/threads/{current_game}")
    else:
        await ctx.send("Replacement didn't work, please do so manually or fix syntax")
        print(sub, flush=True)

def get_google_sheet(sheet_name):
    SHEET_ID = "1zjM5DPXizdgyrYxwAui6LT_yusMEs6I8XXj9iB6LVpE"  # Replace with your Google Sheet ID
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    response = requests.get(url)
    if response.status_code != 200:
        return None
    
    data = StringIO(response.text)
    return list(csv.DictReader(data)) 

def get_top_players(sheet_name, column_name, top_n=10):
    data = get_google_sheet(sheet_name)
    if data is None:
        return None, "Failed to fetch sheet data."

    # Ensure column exists
    if column_name not in data[0]:
        return None, f"Column '{column_name}' not found in sheet."

    # Sort by the specified column (convert to float for numerical sorting)
    sorted_data = sorted(data, key=lambda x: float(x[column_name]), reverse=True)

    # Extract top N players
    top_players = [(row["Name"], row[column_name]) for row in sorted_data[:top_n]]

    return top_players, None


@bot.command()
async def leaderboard(ctx, *, leaderboard: str = "Overall"):
    
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    if leaderboard.lower() == 'overall':
        column = "Overall ELO"
    elif leaderboard.lower() == 'town' or leaderboard.lower() == 'village':
        column = 'Town ELO'
    elif leaderboard.lower() == 'wolf' or leaderboard.lower() == 'mafia':
        column = 'Wolf ELO'
    else:
        await ctx.send("Not a valid leaderboard, use !leaderboard `overall/village/mafia`")
        return
    
    top_players, error = get_top_players("Turbo Champs 2025", column)
    if error:
        await ctx.send(error)
        return
    current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    embed = discord.Embed(
        title=f"Top 10 Players by {column}", description="as of {current_date} @ Midnight UTC",
        color=discord.Color.blue()
    )

    names = []
    scores = []

    for i, (name, score) in enumerate(top_players, start=1):
        names.append(f"#{i} {name}")
        scores.append(f"**{score}**")

    embed.add_field(name="Players", value="\n".join(names), inline=True)
    embed.add_field(name="Scores", value="\n".join(scores), inline=True)

    await ctx.send(embed=embed)
    
    
    
@bot.command()
async def elo(ctx, *, sheet_name: str = "Turbo Champs 2025"):
    
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    
    valid_sheets = ['Lifetime', 'Turbo Champs 2025', '2025', '2024', 'joat-2024', 'bomb-2024', 'vig-2024', 'crx-2024', 'cop9-2024']
    if sheet_name.lower() not in (s.lower() for s in valid_sheets):
        await ctx.send(f"Not a valid ELO leaderboard. Use one of the following sheet names to find your ELO for that leaderboard: {valid_sheets}.")
        return
        
    sheet_data = get_google_sheet(sheet_name)

    if not sheet_data:
        await ctx.send("Error fetching data from Google Sheets.")
        return
    
    alias_data = aliases.get(ctx.author.id, None)
    
    if not alias_data:
        await ctx.send(f"No alias data found for {ctx.author.name}.")
        return
    
    all_aliases = alias_data.get("all", [])
    user_data = None
    
    for active_alias in all_aliases:
        for row in sheet_data:
            if row.get("Name") == active_alias:
                user_data = row
    current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    if user_data:
        embed = discord.Embed(title=f"{sheet_name} ELO for {user_data['Name']}", description="As of {current_date} @ Midnight UTC", color=discord.Color.blue())
        embed.add_field(name="Overall ELO", value=user_data["Overall ELO"], inline=False)
        embed.add_field(name="Town ELO", value=user_data["Town ELO"], inline=True)
        embed.add_field(name="Wolf ELO", value=user_data["Wolf ELO"], inline=True)
        embed.add_field(name="Total Games Played", value=user_data["Games Played"], inline=False)
        embed.add_field(name="Town Games", value=user_data["Town games"], inline=True)
        embed.add_field(name="Wolf Games", value=user_data["Wolf games"], inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No ELO data found for you on the {sheet_name} leaderboards")

@bot.command()
async def player_stats(ctx, *, args=None):
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    # Use shlex to split arguments while respecting quotes
    args = shlex.split(args) if args else []
    specified_alias = None
    setup = None

    # Check the arguments
    if len(args) == 1:  # Single argument provided
        if args[0] in valid_setups or args[0].lower() == 'alexa role madness' or args[0].lower() == 'champs'  or args[0].lower() == 'anne role madness'  or args[0].lower() == 'bennehrm':
            setup = args[0]
        else:
            specified_alias = args[0].strip().lower()
    elif len(args) == 2:  # Two arguments provided
        specified_alias = args[0].strip().lower()
        if args[1] in valid_setups:
            setup = args[1]
        elif args[1].lower() == "alexa role madness" or args[1].lower() == 'champs' or args[1].lower() == 'anne role madness'  or args[1].lower() == 'bennehrm':
            setup = args[1]
        else:
            await ctx.send(f"Invalid setup '{args[1]}'. Please use one of the valid setups: {', '.join(valid_setups)}.")
            return

    # Retrieve alias data for the user
    alias_data = aliases.get(ctx.author.id, None)
    
    if not alias_data:
        await ctx.send(f"No alias data found for {ctx.author.name}.")
        return
    
    all_aliases = alias_data.get("all", [])
    
    # Check if the specified alias belongs to the user
    if specified_alias and specified_alias not in all_aliases:
        await ctx.send(f"The alias '{specified_alias}' does not belong to you. Please choose a valid alias.")
        return
    
    # Determine which aliases to use
    aliases_to_check = [specified_alias] if specified_alias else all_aliases

    # Initialize counters for accumulated stats
    total_games = 0
    total_wins = 0
    villager_games = 0
    villager_wins = 0
    wolf_games = 0
    wolf_wins = 0
    
    # Loop through the selected aliases and accumulate the stats
    for alias in aliases_to_check:
        if setup and setup.lower() == 'champs':
            player_win_rate = winrate.calculate_player_win_rate("database/2025_TurboChampDatabase.csv", alias, None)
        else:
            player_win_rate = winrate.calculate_player_win_rate("game_database.csv", alias, setup)
        
        # Accumulate stats
        total_games += player_win_rate['Total Games Played']
        total_wins += player_win_rate['Total Wins']
        villager_games += player_win_rate['Villager Games']
        villager_wins += player_win_rate['Villager Wins']
        wolf_games += player_win_rate['Wolf Games']
        wolf_wins += player_win_rate['Wolf Wins']

    # Calculate win rates
    overall_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    villager_win_rate = (villager_wins / villager_games * 100) if villager_games > 0 else 0
    wolf_win_rate = (wolf_wins / wolf_games * 100) if wolf_games > 0 else 0

    # Send the accumulated stats
    """await ctx.send(
        f"Stats for {', '.join(aliases_to_check)} ({setup if setup else 'All Setups'}):\n"
        f"  Overall:\n"
        f"    Games Played: {total_games}, Wins: {total_wins}, Win Rate: {overall_win_rate:.2f}%\n"
        f"  Villager:\n"
        f"    Games Played: {villager_games}, Wins: {villager_wins}, Win Rate: {villager_win_rate:.2f}%\n"
        f"  Wolf:\n"
        f"    Games Played: {wolf_games}, Wins: {wolf_wins}, Win Rate: {wolf_win_rate:.2f}%"
    )"""
    embed = discord.Embed(
        title=f"Stats for {setup if setup else 'All Setups'}",
        description=f"Aliases: {', '.join(aliases_to_check)}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Overall",
        value=f"**Games Played:** {total_games}\n**Wins:** {total_wins}\n**Win Rate:** {overall_win_rate:.2f}%",
        inline=False
    )

    embed.add_field(
        name="Villager",
        value=f"**Games Played:** {villager_games}\n**Wins:** {villager_wins}\n**Win Rate:** {villager_win_rate:.2f}%",
        inline=True
    )

    embed.add_field(
        name="Wolf",
        value=f"**Games Played:** {wolf_games}\n**Wins:** {wolf_wins}\n**Win Rate:** {wolf_win_rate:.2f}%",
        inline=True
    )
    await ctx.send(embed=embed)
@bot.command()
async def ranked(ctx, ranked: str = None):

    if ctx.channel.id not in allowed_channels:  
        return

    
    global ranked_game
    
    if ranked is None:  # No argument given, just return the current setting
        if ranked_game:
            await ctx.send("The current game is set to be ranked and will count for Turbo Champs.")
        else:
            await ctx.send("The current game is not ranked and will not count for Turbo Champs.")
    
    elif ranked.lower() == "on":
        if ranked_game:
            await ctx.send("The game is already set to count for Turbo Champs.")
        else:
            ranked_game = True
            await ctx.send("The game is now set to ranked and will count for Turbo Champs.")
            await update_status()

    elif ranked.lower() == "off":
        if not ranked_game:  # Already unranked
            await ctx.send("The game is already set to not count for Turbo Champs.")
        else:
            ranked_game = False
            await ctx.send("The game is now set to unranked and will not count for Turbo Champs.")
            await update_status()


    else:  # Invalid argument, return current setting
        if ranked_game:
            await ctx.send("Invalid argument. Use !ranked [on/off] instead. The current game is set to ranked and will count for Turbo Champs.")
        else:
            await ctx.send("Invalid argument. Use !ranked [on/off] instead. The current game is not ranked and will not count for Turbo Champs.")

   
@bot.command()
async def stats(ctx, game_setup=None):

    if ctx.channel.id not in allowed_channels:  
        return
    
    if game_setup and game_setup.lower() == 'champs':
        df = pd.read_csv('database/2025_TurboChampDatabase.csv')
    else:
        df = pd.read_csv('game_database.csv')
    

    overall_mafia_wins = 0
    overall_town_wins = 0
    overall_independent_wins = 0
    overall_draws = 0

    setup_wins = {}
    setup_total_games = {}

    for index, row in df.iterrows():
        if row['Winning Alignment'] == 'Mafia':
            winning_team = 'wolves'
        elif row['Winning Alignment'] == 'Evil Independent':
            winning_team = 'independent'
        elif row['Winning Alignment'] == 'Town':
            winning_team = 'villagers'
        else:
            winning_team = 'Draw'

        if winning_team == 'wolves':
            overall_mafia_wins += 1
        elif winning_team == 'independent':
            overall_independent_wins += 1
        elif winning_team == 'villagers':
            overall_town_wins += 1
        elif winning_team == 'Draw':
            overall_draws += 1

        setup = row['Setup']
        setup_wins[setup] = setup_wins.get(setup, {'mafia': 0, 'town': 0, 'evil_independent': 0, 'draw': 0})
        setup_total_games[setup] = setup_total_games.get(setup, 0) + 1

        if winning_team == 'wolves':
            setup_wins[setup]['mafia'] += 1
        elif winning_team == 'villagers':
            setup_wins[setup]['town'] += 1
        elif winning_team == 'independent':
            setup_wins[setup]['evil_independent'] += 1        
        elif winning_team == 'Draw':
            setup_wins[setup]['draw'] += 1

    # Calculate overall win percentages
    total_games = len(df)
    overall_mafia_win_percentage = (overall_mafia_wins / (total_games- overall_draws)) * 100
    overall_town_win_percentage = (overall_town_wins / (total_games- overall_draws)) * 100
    overall_ind_win_percentage = (overall_independent_wins / (total_games - overall_draws)) * 100
    overall_draw_percentage = (overall_draws / total_games) * 100

    # Display overall stats

    if game_setup is None:
        setup_embed = discord.Embed(title="Setup Stats", color=0x3381ff)
        setup_embed.add_field(name=f'Overall Stats', value=f"Total Games since September 2023: {total_games}", inline=False)
        setup_embed.add_field(name="Town Win Percentage", value=f'{overall_town_win_percentage:.2f}%', inline=True)
        setup_embed.add_field(name='Mafia Win Percentage', value=f'{overall_mafia_win_percentage:.2f}%', inline=True)
        setup_embed.add_field(name="Stats by Turby!", value=f"Use !stats [setup] to get individual setup stats!", inline=False)
        setup_embed.set_thumbnail(url="https://i.imgur.com/2sSTEh3.gif")
        await ctx.send(embed=setup_embed)
    elif game_setup.lower() == 'champs':
        setup_embed = discord.Embed(title="Setup Stats", color=0x3381ff)
        setup_embed.add_field(name=f'Overall Stats', value=f"Total Champs Games since 2/17/2025: {total_games}", inline=False)
        setup_embed.add_field(name="Town Win Percentage", value=f'{overall_town_win_percentage:.2f}%', inline=True)
        setup_embed.add_field(name='Mafia Win Percentage', value=f'{overall_mafia_win_percentage:.2f}%', inline=True)
        setup_embed.add_field(name="Stats by Turby!", value=f"Use !stats [setup] to get individual setup stats!", inline=False)
        setup_embed.set_thumbnail(url="https://i.imgur.com/2sSTEh3.gif")
        await ctx.send(embed=setup_embed)
    else:
        if game_setup not in setup_total_games:
            await ctx.send("Setup not found in the database.")
            return
        count = setup_total_games[game_setup]
        await display_setup_stats(ctx, game_setup, count, setup_wins)

async def display_setup_stats(ctx, setup, count, setup_wins):

    mafia_wins = setup_wins[setup]['mafia']
    town_wins = setup_wins[setup]['town']
    independent_wins = setup_wins[setup]['evil_independent']
    draws = setup_wins[setup]['draw']

    mafia_win_percentage = (mafia_wins / (count - draws)) * 100
    town_win_percentage = (town_wins / (count - draws)) * 100
    independent_win_percentage = (independent_wins / (count - draws)) * 100
    draw_percentage = (draws / count) * 100

    setup_embed = discord.Embed(title=f"{setup} Stats", color=0x3381ff)
    setup_embed.add_field(name="Total Games", value=count, inline=False)
    setup_embed.add_field(name="Mafia Win Percentage", value=f"{mafia_win_percentage:.2f}%", inline=True)
    setup_embed.add_field(name="Town Win Percentage", value=f"{town_win_percentage:.2f}%", inline=True)

    if independent_wins:
        setup_embed.add_field(name="Evil Independent Win Percentage", value=f"{independent_win_percentage:.2f}%", inline=True)
    setup_embed.set_thumbnail(url="https://i.imgur.com/2sSTEh3.gif")

    await ctx.send(embed=setup_embed)

@bot.command()
async def anongame(ctx, anon=None):
    if ctx.channel.id not in allowed_channels:  
        return
    
    global anon_enabled

    if anon is None:
        await ctx.send(f"The current game is set as Anon: {anon_enabled}, use !anongame on or !anongame off to turn anon games on and off.")
    
    elif anon.lower() == "on":
        anon_enabled = True
        await ctx.send(f"The current game is set to anonymous/aliased.")
    elif anon.lower() == "off":
        anon_enabled = False
        await ctx.send(f"The current game is set to normal accounts.")
    else:
        await ctx.send(f"The current game is set as Anon: {anon_enabled}, use !anongame on or !anongame off to turn anon games on and off.")       


@bot.command()
async def game(ctx, setup_name=None, Xer_Players: int = None):
    if ctx.channel.id not in allowed_channels:  
        return
    if ctx.author.id in future_banned:
        await ctx.send("Your future ban of August 1st, 2027 is not yet in effect, so you may use Turby until then.")

    global current_setup, player_limit, players, waiting_list

    if setup_name is None:
        await ctx.send(f"The current game setup is '{current_setup}'. To change the setup, use !game <setup_name>. Valid setup names are: {', '.join(valid_setups)}.")
    elif setup_name in valid_setups:
        if setup_name == "cop9" or setup_name == "paritycop9" or setup_name == "billager9":
            new_player_limit = 9
        elif setup_name == "vig10":
            new_player_limit = 10
        elif setup_name == 'inno4':
            new_player_limit = 4
        elif setup_name == "joat10":
            new_player_limit = 10
        elif setup_name == "bean10":
            new_player_limit = 10
        elif setup_name == "neilgame":
            new_player_limit = 3
        elif setup_name == "ita10":
            new_player_limit = 10
        elif setup_name == "ita13":
            new_player_limit = 13
        elif setup_name == "bml10":
            new_player_limit = 10
        elif setup_name == "bomb10":
            new_player_limit = 10
        elif setup_name == "random10er":
            new_player_limit = 10
        elif (setup_name == "closedrandomXer" or setup_name == "randommadnessXer") and Xer_Players is not None:
            new_player_limit = Xer_Players
            if new_player_limit < 7:
                await ctx.send(f"Cannot change setup to '{setup_name} - {new_player_limit}'. Minimum number of players for randomXers is 7")
                return
            if new_player_limit < len(players):
                await ctx.send(f"Cannot change setup to '{setup_name} - {new_player_limit}'. The current number of players ({len(players)}) exceeds the player limit for this setup ({new_player_limit}).")
                return
            await ctx.send(f"Player limit has been increased to {Xer_Players}!")

        elif setup_name == "closedrandomXer" or setup_name == "randommadnessXer":
            await ctx.send("Please include the number of players after !game (closedrandomXer|randommadnessXer) [#] and try again")
        elif setup_name == "cop13":
            new_player_limit = 13
        elif setup_name == "doublejoat13":
            new_player_limit = 13
        elif setup_name == "rolemadness13":
            new_player_limit = 13
        elif setup_name == "alexa25":
            new_player_limit = 25
        elif setup_name == "f3practice":
            new_player_limit = 3
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
        
        if current_setup == 'cop9' or current_setup == 'cop13':
            await ctx.send(f'The game setup has been changed to cop (created by insomnia)')
        elif current_setup == 'bml10':
            await ctx.send(f'The game setup has been changed to bml10 (whats wrong with you?)')
        else:
            await ctx.send(f"The game setup has been changed to '{current_setup}'")

    else:
        await ctx.send(f"'{setup_name}' is not a valid setup name. Please choose from: {', '.join(valid_setups)}.")

    await update_status()        

@bot.command()
async def phases(ctx, timer_name=None):
    if ctx.channel.id not in allowed_channels:  
        return

    global current_timer, day_length, night_length

    if timer_name is None:
        await ctx.send(f"The current phases are '{current_timer}'. To change the phases, use !phases <setup_name>. Valid setup names are: {', '.join(valid_timers)}.")
    elif timer_name in valid_timers:
        if timer_name == "sunbae":
            new_day_length = 1
            new_night_length = 1
        elif timer_name == "14-3":
            new_day_length = 14
            new_night_length = 3
        elif timer_name == "16-5":
            new_day_length = 16
            new_night_length = 5
        elif timer_name == "8-2":
            new_day_length = 8
            new_night_length = 2

        else:
            await ctx.send(f"'{timer_name}' is not a valid phase. Please choose from: {', '.join(valid_timers)}.")
            return
        
            
        day_length = new_day_length
        night_length = new_night_length
        current_timer = timer_name

        await ctx.send(f"The day/night phases have been changed to '{current_timer}'")
    else:
        await ctx.send(f"'{timer_name}' is not a valid setup name. Please choose from: {', '.join(valid_timers)}.")
    await update_status()     

@bot.command()
async def flavor(ctx, charname=None, charimage=None):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    existing_flavor = load_flavor_json('turboers.json')
    added_flavor = {'character_name': charname, 'character_image': charimage}

    if ctx.author.id not in mods:
        if charname != None:
            if charimage != None:
                await ctx.send(f"You don't have privs to add flavor. Doing flavor lookup for {charname} instead.")
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")
        return
    
    if charname != None:
        if charimage != None:
            for i, item in enumerate(existing_flavor):
                if item['character_name'].lower() == charname.lower():
                    existing_flavor[i]['character_image'] = charimage
                    await ctx.send("flavor updated successfully thxxxbai")
                    save_flavor_json('turboers.json', existing_flavor)
                    return
            existing_flavor.append(added_flavor)
            await ctx.send("flavor add successful thxxxbai")
        else:
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")

    else:
        await ctx.send("No character name selected, try again using quotes")
        return
    
    save_flavor_json('turboers.json', existing_flavor)

@bot.command()
async def smallpig(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    await ctx.send('''smallestpig 1.0 update (pork edition)
<@924804445303349269>''')

@bot.command()
async def benping(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    await ctx.send('''benping 1.0 (dad edition)
                   
                   
                   
<@178647349369765888> - hi ben pls join?''')
    
@bot.command()
async def pinguin(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    await ctx.send('''pingu ping 1.0 (flightless birb edition)
                   
                   
                   
<@158337985727692800>
<@164800310341009408>
                   
join!!!''')

    
@bot.command()
async def bigping(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return   
    await ctx.send('''# bigping 2.2 (oli has been retired edition)
                   bigping has been killed. long live bigping.''')
    
@bot.command()
async def badping(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return 
    await ctx.send('''<@93432503863353344> ur bad lol''')
    
@bot.command()
async def wolf_flavor(ctx, charname=None, charimage=None):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    existing_flavor = load_flavor_json('wolves.json')
    added_flavor = {'character_name': charname, 'character_image': charimage}

    if ctx.author.id not in mods:
        if charname != None:
            if charimage != None:
                await ctx.send(f"You don't have privs to add flavor. Doing flavor lookup for {charname} instead.")
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")
        return
    

    if charname != None:
        if charimage != None:
            for i, item in enumerate(existing_flavor):
                if item['character_name'].lower() == charname.lower():
                    existing_flavor[i]['character_image'] = charimage
                    await ctx.send("flavor updated successfully thxxxbai")
                    save_flavor_json('wolves.json', existing_flavor)
                    return
            existing_flavor.append(added_flavor)
            await ctx.send("flavor add successful thxxxbai")
        else:
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")

    else:
        await ctx.send("No character name selected, try again using quotes")
        return
    
    save_flavor_json('wolves.json', existing_flavor)

@bot.command()
async def pr_flavor(ctx, charname=None, charimage=None):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
 
    existing_flavor = load_flavor_json('powerroles.json')
    added_flavor = {'character_name': charname, 'character_image': charimage}
    if ctx.author.id not in mods:
        if charname != None:
            if charimage != None:
                await ctx.send(f"You don't have privs to add flavor. Doing flavor lookup for {charname} instead.")
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")
        return
    

    if charname != None:
        if charimage != None:
            for i, item in enumerate(existing_flavor):
                if item['character_name'].lower() == charname.lower():
                    existing_flavor[i]['character_image'] = charimage
                    await ctx.send("flavor updated successfully thxxxbai")
                    save_flavor_json('powerroles.json', existing_flavor)
                    return
            existing_flavor.append(added_flavor)
            await ctx.send("flavor add successful thxxxbai")
        else:
            for i in existing_flavor:
                if i['character_name'].lower() == charname.lower():
                    await ctx.send(f"Flavor found for {i['character_name']}: {i['character_image']}")
                    return
            await ctx.send(f"No flavor found for {charname}. Try again noob")

    else:
        await ctx.send("No character name selected, try again using quotes")
        return
    
    save_flavor_json('powerroles.json', existing_flavor)

@bot.command(name="in")
async def in_(ctx, *time):
    delayed_time = None
    if not time:
        time = '60'
    else:
        time = ' '.join(time)
        
    if time.startswith('0x'):
        time = int(time, 16)
    elif time.startswith('in '):
        parts = time.split()
        if len(parts) > 1 and parts[1].isdigit():
            delayed_time = int(parts[1])
            time = int(60)
    else:
        time = int(time)
        
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    if ctx.author.id in future_banned:
        await ctx.send("Your future ban of August 1st, 2027 is not yet in effect, so you may use Turby until then.")

    if ctx.author.id not in aliases:
        await ctx.send("Please set your MU username by using !alias MU_Username before inning!")
        return

    alias = aliases[ctx.author.id]["active"]
    global game_host_name, player_limit, players, waiting_list, delay_list

    if time < 10 or time > 90 and time != 10000 and time != 1610 and time != 420 and time != 6969 and time != 1337:
        if ctx.author.id in alexas:
            pass
        else:
            await ctx.send("Invalid duration. Please choose a duration between 10 and 90 minutes.")
            return
    
    if time == 1337 and ctx.author.id in non_1337_users:
        await ctx.send("you are not 1337 enuff for this time entry n00b")
        
    if alias in game_host_name:
        if delayed_time:
            delay_list[alias] = delayed_time
            await ctx.send(f"{alias} will be removed as host and added to the list in {delayed_time} minutes.")
            await update_status()
            return
        
        elif len(game_host_name) == 1:
            game_host_name = ["Turby"]
            if len(players) < player_limit:
                players[alias] = time
                await ctx.send(f"{alias} has been removed as host and added to the list for the next {time} minutes. Your current host is Turby :3")
            else:
                waiting_list[alias] = time
                await ctx.send(f"{alias} has been removed as host and added to the waiting list for the next {time} minutes. Your current host is Turby :3")
            await update_status()
            return
            
        elif len(game_host_name) > 1:
            game_host_name.remove(alias)
            if len(players) < player_limit:
                players[alias] = time
                await ctx.send(f"{alias} has been removed as host and added to the list for the next {time} minutes.")
            else:
                waiting_list[alias] = time
                await ctx.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
            await update_status()    
            return     
    if alias in players or alias in waiting_list:
        if delayed_time:
            await ctx.send(f"{alias} is already in and cant also join in {delayed_time} minutes.")
            return
        if alias in players:
            players[alias] = time            
        else:
            waiting_list[alias] = time            
        await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
    else:
        if delayed_time:
            delay_list[alias] = delayed_time
            await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
        elif len(players) < player_limit:
            players[alias] = time            
            await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
        else:
            waiting_list[alias] = time
            await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
    if ctx.guild is None:
        turbochannel = bot.get_channel(turbo_chat)
        await turbochannel.send(f"{alias} used `!in {time}` in DMs and joins the game!")
        
    await update_status()            

@bot.command()
async def out(ctx):
    
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    if ctx.author.id in future_banned:
        await ctx.send("Your future ban of August 1st, 2027 is not yet in effect, so you may use Turby until then.")
    global game_host_name, player_limit, players, waiting_list 
    
    if ctx.author.id not in aliases:
        await ctx.send("You are not on the list and you haven't set an alias. Stop trolling me.")
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        return
    
    alias = aliases[ctx.author.id]["active"]
    
    if alias in (hostname.lower() for hostname in game_host_name):
        if len(game_host_name) == 1:
            game_host_name = ["Turby"]
            await ctx.send(f"{alias} has been removed as host. Turby :3 has been set back to the default host.")
            await update_status()
            return
        else:
            game_host_name.remove(alias)
            host_list = [f"{host}" for host in game_host_name]
            hosts = ' '.join(host_list)
            await ctx.send(f"{alias} has been removed as host. Your current host(s): {hosts}")
            await update_status()
            return
        
    if alias in players:
        del players[alias]
        #await ctx.send(f"{alias} has been removed from the list.")
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        if ctx.guild is None:
            turbochannel = bot.get_channel(turbo_chat)
            await turbochannel.send(f"{alias} used `!out` in DMs and left the game!")
    elif alias in waiting_list:
        del waiting_list[alias]
        #await ctx.send(f"{alias} has been removed from the waiting list.")
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        if ctx.guild is None:
            turbochannel = bot.get_channel(turbo_chat)
            await turbochannel.send(f"{alias} used `!out` in DMs and left the game!")
    else:
        await ctx.send(f"{alias} is not on the list.")
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
    # Add a player from waiting list to main list if it's not full
    if len(players) < player_limit and waiting_list:
        next_alias, next_time = waiting_list.popitem()
        players[next_alias] = next_time
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        await ctx.send(f"{next_alias} has been moved from the waiting list to the main list.")

    await update_status()
    
@bot.command()
async def alias(ctx, *, alias=None):
    
    if ctx.guild and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    user_id = ctx.author.id  # Ensure consistent key type

    if alias is None:  # Show current aliases
        user_data = aliases.get(user_id, None)
        if not user_data:
            await ctx.send("You don't have any aliases set yet.")
            return

        alias_list = user_data.get("all", [])
        active_alias = user_data.get("active", "None")
        aliases_str = ", ".join(alias_list)
        await ctx.send(f"Your active alias is _{active_alias}_\n\nYour list of aliases includes: {aliases_str}")
        return

    alias = alias.lower()

    # Check if the alias is already in use by another user
    for other_user_id, data in aliases.items():
        if alias in data.get("all", []):
            if other_user_id == user_id:
                aliases[user_id]["active"] = alias  # Update active alias
                save_aliases()
                await ctx.send(f"Alias for {ctx.author} is now switched to '{alias}'.")
                if user_id in aliases:
                    user_aliases = aliases[user_id].get("all", [])
                    for player_list in [players, waiting_list]:
                        for player in list(player_list.keys()):  # Copy keys to avoid RuntimeError
                            # Check if the player matches any alias (case-insensitive)
                            if player.lower() in map(str.lower, user_aliases):
                                # Update the key to the new alias
                                player_list[alias] = player_list.pop(player)

                await update_status()
                return
            else:
                await ctx.send(f"The alias '{alias}' is already taken by another player. Ping @benneh or choose a different alias.")
                return

    # Initialize the user's alias list if it doesn't exist
    if user_id not in aliases:
        aliases[user_id] = {"active": alias, "all": [alias]}
    else:
        aliases[user_id]["all"].append(alias)
        aliases[user_id]["active"] = alias

    save_aliases()
    await ctx.send(f"Alias '{alias}' added for {ctx.author} and marked as active.")

    # Update alias in players and waiting_list
    if user_id in aliases:
        user_aliases = aliases[user_id].get("all", [])
        for player_list in [players, waiting_list]:
            for player in list(player_list.keys()):  # Copy keys to avoid RuntimeError
                # Check if the player matches any alias (case-insensitive)
                if player.lower() in map(str.lower, user_aliases):
                    # Update the key to the new alias
                    player_list[alias] = player_list.pop(player)

    await update_status()
    

@bot.command()
async def remove_alias(ctx, user_id: int, *, alias: str):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    global aliases
    if ctx.author.id in mods:

        alias = alias.lower()

        # Check if the user exists in the aliases dictionary
        if user_id not in aliases:
            await ctx.send(f"User <@{user_id}> does not have any aliases.")
            return

        user_aliases = aliases[user_id]["all"]

        # Check if the alias exists for the user
        if alias not in user_aliases:
            await ctx.send(f"The alias '{alias}' is not associated with user <@{user_id}>.")
            return

        # Remove the alias
        user_aliases.remove(alias)

        # Update the active alias if it was removed
        if aliases[user_id]["active"] == alias:
            aliases[user_id]["active"] = user_aliases[0] if user_aliases else None

        # Remove the user from the dictionary if they have no aliases left
        if not user_aliases:
            del aliases[user_id]

        save_aliases()  # Save the changes to persist
        await ctx.send(f"Alias '{alias}' has been removed from user <@{user_id}>.")
        await update_status()
    else:
        return

        
@bot.command()
async def add(ctx, *, alias):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    alias = alias.lower()
    global game_host_name, player_limit, players, waiting_list
    
    if alias in game_host_name:
        if len(game_host_name) == 1:
            game_host_name = ["Turby"]
            if len(players) < player_limit:
                players[alias] = 60
                await ctx.send(f"{alias} has been removed as host and added to the list for the next 60 minutes. Your current host is Turby :3.")
            else:
                waiting_list[alias] = 60
                await ctx.send(f"{alias} has been removed as host and added to the waiting list for the next 60 minutes. Your current host is Turby :3.")
            await update_status()
            return
            
        elif len(players) < player_limit:
            players[alias] = 60
            game_host_name.remove(alias)
            host_list = [f"{host}" for host in game_host_name]
            hosts = ' '.join(host_list)
            await ctx.send(f"{alias} has been removed as host and added to the list for the next 60 minutes. Your current host(s): {hosts}")
            await update_status()
            return
        else:
            waiting_list[alias] = 60 
            await ctx.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
            await update_status()
            return
            
    if alias in players or alias in waiting_list:
        if alias in players:
            players[alias] = 60  # Default time
        else:
            waiting_list[alias] = 60  # Default time
        await ctx.message.add_reaction('👍')    
        #await ctx.send(f"{alias}'s in has been renewed for 60 minutes.")
    else:
        if len(players) < player_limit:
            players[alias] = 60  # Default time
            #await ctx.send(f"{alias} has been added to the list with for 60 minutes.")
        else:
            waiting_list[alias] = 60  # Default time
            #await ctx.send(f"The list is full. {alias} has been added to the waiting list.")
        await ctx.message.add_reaction('👍')
    await update_status()    

@bot.command()
async def remove(ctx, *, alias):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    alias = alias.lower()
    global game_host_name, player_limit, players, waiting_list
    
    if alias in (hostname.lower() for hostname in game_host_name):
        if len(game_host_name) == 1:
            game_host_name = ["Turby"]
            await ctx.send(f"{alias} has been removed as host. Turby :3 has been set back to the default host.")
            await update_status()
            return
        else:
            game_host_name.remove(alias)
            host_list = [f"{host}" for host in game_host_name]
            hosts = ' '.join(host_list)
            await ctx.send(f"{alias} has been removed as host. Your current host(s): {hosts}")
            await update_status()
            return
        
    if alias in players:
        del players[alias]
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        #await ctx.send(f"{alias} has been removed from the list.")
    elif alias in waiting_list:
        del waiting_list[alias]
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
        #await ctx.send(f"{alias} has been removed from the waiting list.")
    else:
        await ctx.send(f"{alias} is not on the list.")
        await ctx.message.add_reaction('<:laserbensdog:1337171130166939739>')
    # Add a player from waiting list to main list if it's not full
    if len(players) < player_limit and waiting_list:
        next_alias, next_time = waiting_list.popitem()
        players[next_alias] = next_time
        
        await ctx.send(f"{next_alias} has been moved from the waiting list to the main list.")
    await update_status()

@bot.command()
async def status(ctx, *args):
    if ctx.guild is not None and ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    if ctx.author.id in future_banned:
        await ctx.send("Your future ban of August 1st, 2027 is not yet in effect, so you may use Turby until then.") 
    global game_host_name, status_id, status_channel

    embed = discord.Embed(title="**Turbo Bot v3.0 (w/ EoD VCs in DVC and auto-sub requests!) by benneh", color=0x3381ff)
    embed.add_field(name="**Game Setup**", value=current_setup, inline=True)    
    host_list = [f"{host}\n" for host in game_host_name]
    hosts = ''.join(host_list)
    embed.add_field(name="**Host**", value=hosts, inline=True)
    embed.add_field(name="**Phases**", value=str(day_length) + "m Days, " + str(night_length) + "m Nights", inline=True)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="", value="", inline=True)

    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="", value="", inline=True)
    embed.add_field(name="", value="", inline=True)
    if ranked_game:
        embed.add_field(name="Turbo Champs Ranked Game (use !ranked on/off to adjust)", value="True", inline=False)
    else:
        embed.add_field(name="Turbo Champs Ranked Game (use !ranked on/off to adjust)", value="False", inline=False)

    status_flavor = load_flavor_json('icons.json')    

    if players:
        player_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(players.items(), 1):
            player_msg = alias
            for item in status_flavor:
                if alias == item['alias']:
                    player_msg = f"{alias} {item['icon']}"
            player_message += f"{player_msg}\n"
            time_message += f"{remaining_time} minutes\n"
            
        spots_left = player_limit - len(players)
        if spots_left > 1:
            player_message += f"+{spots_left} !!\n"
        elif spots_left == 1:
            player_message += "+1 HERO NEEDED \n" 
        else:
            player_message += "Game is full. Switch to a larger setup using `!game [setup]` or rand the game using `!rand -title \"Title of game thread\"`\n"        
        time_message +=  "!in or react <:laserbensdog:1337171130166939739> to join!\n"  
        embed.set_field_at(3, name="**Players:**", value=player_message, inline=True)
        embed.set_field_at(5, name="**Time Remaining:**", value=time_message, inline=True)
        embed.set_field_at(4, name="", value="", inline=True)
        
    waiting_list_message = ""
    time_message = ""
    
    if delay_list:
        for i, (alias, remaining_time) in enumerate(delay_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"in in {remaining_time} minutes\n"
            
    if waiting_list:
        for i, (alias, remaining_time) in enumerate(waiting_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes\n"
                    
    if waiting_list_message:
        embed.set_field_at(6, name="**Waiting/Future-In List:**", value=waiting_list_message, inline=True)
        embed.set_field_at(7, name="**Time Remaining:**", value=time_message, inline=True)


    if not players and not waiting_list and not delay_list:
        embed.set_field_at(3, name="No players are currently signed up.", value="", inline=False)
    
    if not waiting_list and not delay_list:
        embed.set_field_at(6, name="", value="", inline=True)
        embed.set_field_at(7, name="", value="", inline=True)
    
    embed.set_thumbnail(url="https://i.imgur.com/2sSTEh3.gif")

    status_embed = await ctx.send(embed=embed)
    
    if ctx.guild:
        await status_embed.add_reaction('<:laserbensdog:1337171130166939739>')
        status_id = status_embed.id
        status_channel = ctx.channel

async def update_status():

    global status_id
    
    if status_id is None or status_channel is None:
        return
    
    status_message = await status_channel.fetch_message(status_id)
    embed = status_message.embeds[0]
    
    spots_left = player_limit - len(players)
    host_list = [f"{host}\n" for host in game_host_name]
    hosts = ''.join(host_list)

    embed.set_field_at(0, name="**Game Setup**", value=current_setup, inline=True)
    host_list = [f"{host}\n" for host in game_host_name]
    hosts = ''.join(host_list)
    embed.set_field_at(1, name="**Host**", value=hosts, inline=True)
    embed.set_field_at(2, name="**Phases**", value=str(day_length) + "m Days, " + str(night_length) + "m Nights", inline=True)

    status_flavor = load_flavor_json('icons.json')    

    if players:
        player_message = ""
        time_message = ""
        for i, (alias, remaining_time) in enumerate(players.items(), 1):
            player_msg = alias
            for item in status_flavor:
                if alias == item['alias']:
                    player_msg = f"{alias} {item['icon']}"
            player_message += f"{player_msg}\n"
            time_message += f"{remaining_time} minutes\n"

        spots_left = player_limit - len(players)
        if spots_left > 1:
            player_message += f"+{spots_left} !!\n"
        elif spots_left == 1:
            player_message += f"+{spots_left} !!\n"
        else:
            player_message += "Game is full. Switch to a larger setup using `!game [setup]` or rand the game using `!rand -title \"Title of game thread\"`\n"        
        
        time_message +=  "!in or react <:laserbensdog:1337171130166939739> to join!\n"
        
        embed.set_field_at(3, name="**Players:**", value=player_message, inline=True)
        embed.set_field_at(5, name="**Time Remaining:**", value=time_message, inline=True)
    
    waiting_list_message = ""
    time_message = ""
    
    if delay_list:
        for i, (alias, remaining_time) in enumerate(delay_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"in in {remaining_time} minutes\n"
            
    if waiting_list:
        for i, (alias, remaining_time) in enumerate(waiting_list.items(), 1):
            waiting_list_message += f"{alias}\n"
            time_message += f"{remaining_time} minutes\n"
                    
    if waiting_list_message:
        embed.set_field_at(6, name="**Waiting List/Future In List:**", value=waiting_list_message, inline=True)
        embed.set_field_at(7, name="**Time Remaining:**", value=time_message, inline=True)
        
    if not players and not waiting_list and not delay_list:
        embed.set_field_at(3, name="No players are currently signed up.", value="", inline=False)
        embed.set_field_at(4, name="", value="", inline=True)
        embed.set_field_at(5, name="", value="", inline=True)
        embed.set_field_at(6, name="", value="", inline=True)
        embed.set_field_at(7, name="", value="", inline=True)
    
    if not waiting_list and not delay_list:
        embed.set_field_at(6, name="", value="", inline=True)
        embed.set_field_at(7, name="", value="", inline=True)
    
    if ranked_game:
        embed.set_field_at(9, name="Turbo Champs Ranked Game (use !ranked on/off to adjust)", value="True", inline=False)
    else:
        embed.set_field_at(9, name="Turbo Champs Ranked Game (use !ranked on/off to adjust)", value="False", inline=False)
        
    
    await status_message.edit(embed=embed)
    
@bot.command()
async def delete_archive(ctx, category_name):
    if ctx.author.id not in mods:
        return
    
    guild = bot.get_guild(dvc_server)

    try:
        category = discord.utils.get(guild.categories, name=category_name)

        if category:
            for channel in category.channels:
                await channel.delete()
            await ctx.send(f"DVC Archive cleanup complete for {category_name}")
        else:
            await ctx.send(f"Category {category_name} not found on Turbo DVC server. Try again.")
    except:
        await ctx.send("Somethin' fucked up, check logs")

@bot.command()
async def process_archive(ctx, category_name):
    if ctx.author.id not in mods:
        return
    
    guild = bot.get_guild(dvc_server)
    pattern = re.compile(r'(\d+)$')
    category = discord.utils.get(guild.categories, name=category_name)
    try:
        if category:

            for channel in category.channels:
                chan_name = channel.name
                match = pattern.search(chan_name)
                thread_id_only = str(match.group(1))
                process(thread_id_only)

        else:
            await ctx.send(f"Category {category_name} not found on Turbo DVC server. Try again.")
    except Exception as error:
        print(f"Error: {error}", flush=True)
        await ctx.send("Somethin' fucked up, check logs")
    await ctx.send(f"Processed archive: {category_name}")


@bot.command()
async def host(ctx, *, host_name=None):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    
    if ctx.author.id not in mods:
        await ctx.send("Hosting is limited to a select set of users who will not ruin the DVC experience for others and also for those who have subscribed to the Turbot Advanced package, $5.99 a month. DM Benneh for billing options.")
        return
    global game_host_name
    
    if host_name == "Turby":
        game_host_name = ["Turby"]
        await update_status()
        await ctx.send("Host setting has been set to default for Turby :3 and cleared all other hosts.")
        return

    if host_name is not None and host_name.lower() in game_host_name:
        await ctx.send(f"That account is already a host. Stop trying to break me. nya~")
        return   
        
    if host_name is None:
        if ctx.author.id in aliases:
            host_name = aliases[ctx.author.id]["active"]
            if host_name in players or host_name in waiting_list:
                await ctx.send(f"{host_name} is already on the turbo list or waiting list.\n Please choose a different name for the host.")
                return
            if host_name in game_host_name:
                await ctx.send(f"That account is already a host. Stop trying to break me. nya~")
                return  
            else:
                game_host_name.append(host_name)
                host_list = [f"{host}" for host in game_host_name]
                hosts = ', '.join(host_list)
                await ctx.send(f"Hosts for the next turbo are set as {hosts}")
                await update_status()
                return
        else:
            await ctx.send("You have not set an alias. Please use `!alias [MU Username]` before trying to use !host or !in commands.")
            return
    host_name = host_name.lower()            
    if host_name in players or host_name in waiting_list:
        await ctx.send(f"{host_name} is already on the turbo list or waiting list.\n Please choose a different name for the host.")
        return
    

    game_host_name.append(host_name)
    host_list = [f"{host}" for host in game_host_name]
    hosts = ', '.join(host_list)
    await ctx.send(f"Hosts for the next turbo are set as {hosts}")
    await update_status() 
    return
    
@tasks.loop(minutes=1)
async def update_players():
    global player_limit, recruit_timer
    
    try:
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
        for alias in list(waiting_list.keys()):
            waiting_list[alias] -= 1
            if waiting_list[alias] <= 0:
                await bot.get_channel(223260125786406912).send(f"{alias} has run out of time and has been removed from the waitlist.")
                del waiting_list[alias]
        for alias in list(delay_list.keys()):
            delay_list[alias] -= 1
            if delay_list[alias] <= 0:
                if len(players) < player_limit and waiting_list:
                    next_alias = alias
                    waiting_list[next_alias] = 60
                    await bot.get_channel(223260125786406912).send(f"{alias}'s bait has run out of time and has been added to the waiting list.")
                    del delay_list[alias]
                else:
                    next_alias = alias
                    players[next_alias] = 60
                    await bot.get_channel(223260125786406912).send(f"{alias}'s bait has run out of time and has been added to the game.")
                    del delay_list[alias]
                
                
        save_player_list(players, waiting_list, current_setup, game_host_name, player_limit)
        await update_status()
    except Exception as e:
        print(f"Error updating players with update_player function: {e}", flush=True)

@bot.command()
async def live_dvc(ctx, thread_id):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    global player_limit, game_host_name, current_setup, is_rand_running, current_game, spec_list, anon_enabled, game_processors
    player_aliases = []
    final_game_setup = "custom"
	
    role, channel_id, guild = await create_dvc(thread_id)
    channel = bot.get_channel(channel_id)
	
    game_url = f"https://www.mafiauniverse.com/forums/threads/{thread_id}"
    pin_message = await channel.send(f"MU Link for the current game: \n\n{game_url}")
    if pin_message:
        await pin_message.pin()
    await new_game_spec_message(bot, thread_id, "Custom/Live DVC")
    current_game = thread_id 
    
    if thread_id not in game_processors:
        game_processors[thread_id] = ThreadmarkProcessor()
    await game_processors[thread_id].process_threadmarks(thread_id, player_aliases, role, guild, channel_id, final_game_setup, current_game)

    await edit_dvc(channel, guild)
    await delete_dvc_role(channel, role)
    current_game = None

    
@bot.command()
async def log_game(ctx, *args):
    if ctx.channel.id not in allowed_channels:
        return
    if ctx.author.id not in mods:
        return
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-thread_id', default=None)
    parser.add_argument('-setup', default=None)
    try:
        args_parsed = parser.parse_args(args)
    except SystemExit:
        await ctx.send(f"Invalid arguments. Please check your command syntax. Do not use `-`, `--`, or `:` in your titles and try again.")
        return
    except Exception as e:
        await ctx.send(f"An unexpected error occurred. Please try again.\n{str(e)}")
        return
    
    update_db_after_game(args_parsed.thread_id)
    summary_url = f"https://www.mafiauniverse.com/forums/modbot-beta/get-game-summary.php?threadid={args_parsed.thread_id}"
    summary_response = requests.get(summary_url)
    summary_json = summary_response.json()

    summary_csv = 'game_database.csv'
    summary_headers = ['Turbo Title', 'Setup', 'Thread ID', 'Game ID', 'Winning Alignment', 'Villagers', 'Wolves']
    town = summary_json['players']['town']
    mafia = summary_json['players']['mafia']

    town_list = []
    mafia_list = []

    for player in town:
        town_list.append(player['username'])
        
    for player in mafia:
        mafia_list.append(player['username'])
    
    title = summary_json['title']
    start_index = title.find(" - [")
    if start_index != -1:
        start_index += len(" - [")
        end_index = title.find(" game]", start_index)

        if end_index != -1:
            extracted_setup = title[start_index:end_index]
        else:
            extracted_setup = args_parsed.setup
            print("No setup found", flush=True)
    else:
        extracted_setup = args_parsed.setup
        print("No setup found", flush=True)

    with open(summary_csv, 'a', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=summary_headers)

        if csvfile.tell() == 0:
            csv_writer.writeheader()
        
        csv_writer.writerow({
            "Turbo Title": summary_json['title'],
            "Setup": extracted_setup,
            "Thread ID": summary_json['threadid'],
            "Game ID": summary_json['id'],
            "Winning Alignment": summary_json['winning_alignment'],
            "Villagers": town_list,
            "Wolves": mafia_list,                          
        })

def get_allowed_randers():
    """Retrieve allowed users based on aliases and hosts."""
    allowed = set()
    for player in list(players.keys())[:player_limit]:
        allowed.update(get_alias_ids(player))
    for host in game_host_name:
        allowed.update(get_alias_ids(host))
    return allowed

def get_alias_ids(name):
    """Retrieve the Discord IDs associated with a given alias."""
    return {int(k) for k, v in aliases.items() if name in v["all"] or name == v["active"]}


async def wait_for_cancel(message, allowed_users):
    """Wait for a ❌ reaction from an allowed user within 15 seconds."""
    def check(reaction, user):
        return (str(reaction.emoji) == '❌' and user.id in allowed_users and reaction.message.id == message.id)

    try:
        await bot.wait_for('reaction_add', timeout=15, check=check)
        return True  # Canceled
    except asyncio.TimeoutError:
        return False  # Proceed with rand
    
    
@bot.command()
async def rand(ctx, *args):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    global player_limit, game_host_name, current_setup, is_rand_running, current_game, spec_list, anon_enabled, ranked_game, game_processors

    allowed_randers = get_allowed_randers()
    player_aliases = list(players.keys())[:player_limit]
    
    if ctx.author.id not in allowed_randers:
        await ctx.send("Only hosts and players on the list are allowed to execute this function.")
        return 

    if len(players) < player_limit:
        await ctx.send(f"Not enough players to start a game. Need {player_limit} players.")
        return
        
    if is_rand_running:
        await ctx.send("The !rand command is currently being processed. Please wait.")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('-title', default=None)
    parser.add_argument('-thread_id', default=None)
    parser.add_argument('-wolves', default=None)
    parser.add_argument('-villager', default=None)
    
    try:
        args_parsed = parser.parse_args(args)
    except SystemExit:
        await ctx.send(f"Invalid arguments. Please check your command syntax. Do not use `-`, `--`, or `:` in your titles and try again.")
        return
    except Exception as e:
        await ctx.send(f"An unexpected error occurred. Please try again.\n{str(e)}")
        return

    is_rand_running = True
    current_game_ranked = bool(ranked_game)

    mentions = " ".join([f"<@{id}>" for id in allowed_randers])
    
    cancel = await ctx.send(f"{mentions} \n\nThe game will rand in 15 seconds unless canceled by reacting with '❌'")
    await cancel.add_reaction('❌')
    
    if await wait_for_cancel(cancel, allowed_randers):
        await ctx.send("Rand canceled")
        is_rand_running = False
        return
    
    await ctx.send("Randing, stfu")
        
    try:
        #Login and get Initial Token
        session = mu.login(username, password)
        security_token = mu.new_thread_token(session)
        
        game_title = args_parsed.title
        thread_id = args_parsed.thread_id
        wolves = args_parsed.wolves
        fake_villager = args_parsed.villager

        if wolves is not None:
            await ctx.send(f"{wolves} have been set as the wolf team, proceeding with rand.")
        if fake_villager is not None:
            await ctx.send(f"{fake_villager} has been set as the town IC for this game, proceeding with rand.")

        if current_setup == "random10er":
            potential_setups = ["joat10", "vig10", "bomb10"]
            final_game_setup = random.choice(potential_setups)
            setup_title = final_game_setup
        else:
            final_game_setup = current_setup
            setup_title = final_game_setup
        
        if not game_title:
            game_title = mu.generate_game_thread_uuid()
            
        if not thread_id:
            print(f"Attempting to post new thread with {game_title}", flush=True)
            thread_id = mu.post_thread(session, game_title, security_token, setup_title,test=False)
            
        hosts = ', '.join(game_host_name)
        await ctx.send(f"Attempting to rand `{game_title}`, a {current_setup} game hosted by `{hosts}` using thread ID: `{thread_id}`. Please standby.")
        print(f"Attempting to rand `{game_title}`, a {current_setup} game hosted by `{hosts}` using thread ID: `{thread_id}`. Please standby.", flush=True)
        
        security_token = mu.new_game_token(session, thread_id)
        response_message = mu.start_game(session, security_token, game_title, thread_id, player_aliases, final_game_setup, day_length, night_length, game_host_name, anon_enabled,player_limit)
        
        if "was created successfully." in response_message:
            # Use aliases to get the Discord IDs
            print("Game randed successfully", flush=True)
            mention_list = []
            
            for player in player_aliases:
                for key, value in aliases.items():
                    if player == value["active"] or player in value["all"]:
                        mention_list.append(int(key))
                        
            player_mentions = " ".join([f"<@{id}>" for id in mention_list])
            game_url = f"https://www.mafiauniverse.com/forums/threads/{thread_id}"  # Replace BASE_URL with the actual base URL
            await ctx.send(f"{player_mentions}\nranded STFU\n{game_url}\nType !dvc to join the turbo DVC/Graveyard. You will be auto-in'd to the graveyard channel upon your death if you are in that server!")
            
            ###################################################
            ####################### new code for wolf chat adds
            #wolf_team = await get_wolf_info(game_title, setup_title)
            #wc_channel_id, wc_guild = await create_wolf_chat(thread_id)
            #wc_channel = bot.get_channel(wc_channel_id)

            #wc_msg = "Wolf chat: "
            #for wolf in wolf_team:
            #    wolf = wolf.lower()
            #    mention_id = None

                # Search for the wolf in the active or all aliases
            #    for user_id, data in aliases.items():
            #        if wolf == data["active"] or wolf in data["all"]:
            #            mention_id = int(user_id)
            #            break

            #    if mention_id:
            #        try:
            #            wolf_id = wc_guild.get_member(mention_id)
            #            # await wolf_id.add_roles(wc_role)  # Uncomment if assigning roles
            #            await wc_channel.set_permissions(wolf_id, read_messages=True, send_messages=True)
            #            wc_msg += f"<@{mention_id}> "
            #        except Exception as e:
            #            print(f"Can't add {wolf} to wc: {e}", flush=True)

            #await wc_channel.send(wc_msg)

            #####################################################
            #####################################################
            role, channel_id, guild = await create_dvc(thread_id)
            print(f"DVC thread created.", flush=True)
            channel = bot.get_channel(channel_id)
            
            host_msg = "Hosts for the current game: "

            for host in game_host_name:
                host = host.lower()
                if host == 'turby':
                    pass
                mention_id = None

                # Search for the host in active or all aliases
                for user_id, data in aliases.items():
                    if host == data["active"] or host in data["all"]:
                        mention_id = int(user_id)
                        break

                if mention_id:
                    try:
                        member = guild.get_member(mention_id)
                        await member.add_roles(role)  # Assign the role
                        host_msg += f"<@{mention_id}> "  # Add to message
                    except Exception as e:
                        print(f"Can't add {host} to dvc: {e}", flush=True)
                        # Optionally send a failure message:
                        # await channel.send(f"Failed to add {host} to dvc.")
                else:
                    print(f"Host {host} not found in aliases", flush=True)
                    # Optionally send a message about the missing host:
                    # await channel.send(f"{host} is not registered in aliases.")

            await channel.send(host_msg)

            spec_msg = "Specs for the current game: "
            for spec in spec_list:
                if int(spec) in mention_list:
                    print(f"{spec} not in list, continuing to next", flush=True)
                    continue
                else:
                    try:
                        spec_int = int(spec)
                        spec_member = guild.get_member(spec_int)
                        await spec_member.add_roles(role)
                        spec_msg += f"<@{spec}> "
                        #await channel.send(f"<@{spec}> is spectating, welcome to dvc")
                    except Exception as error:
                        print(f"Error: {error}", flush=True)
            await channel.send(spec_msg)
            
            pin_message = await channel.send(f"MU Link for the current game: \n\n{game_url}")
            if pin_message:
                await pin_message.pin()

            await new_game_spec_message(bot, thread_id, game_title)
            postgame_players = players
            game_host_name = ["Turby"]
            players.clear()
            players.update(waiting_list)
            waiting_list.clear()  
            anon_enabled = False 
            print("Old player/waiting lists cleared and updated and host set back to default. Starting threadmark processor next.", flush=True)			
            is_rand_running = False
            current_game = thread_id
            if thread_id not in game_processors:
                game_processors[thread_id] = ThreadmarkProcessor()
            await game_processors[thread_id].process_threadmarks(thread_id, player_aliases, role, guild, channel_id, final_game_setup, current_game)
            print(f"Threadmark processor finished. rand function finished.", flush=True)
            await edit_dvc(channel, guild)
            #await edit_dvc(wc_channel, wc_guild)
            await delete_dvc_role(channel, role)
            # await delete_dvc_role(wc_channel, wc_role)
            current_game = None
            
            current_year = str(datetime.datetime.now().year)
            lifetime_file_path = 'game_database.csv'
            
            game_data = get_game_log(thread_id)
            update_db_after_game(thread_id)
            write_game_log(lifetime_file_path, game_data)
            write_game_log('database/' + current_year + '_database.csv', game_data)
            write_game_log('database/' + current_year + '_' + final_game_setup + '_database.csv', game_data)
            
            aliases_file = 'aliases.json'
            credentials_path = 'creds/turbo-champs-2025-a3862c5a5d97.json'      
            spreadsheet_name = 'Turbo ELO Sheet'
                        
            file_path = 'database/' + current_year + '_database.csv'
            sheet_name = '2025'
            df = pd.read_csv(file_path)
            df['Villagers'] = df['Villagers'].apply(eval)
            df['Wolves'] = df['Wolves'].apply(eval)
            y2025_elo_calculator = EloCalculator(credentials_path,aliases_file)
            y2025_elo_calculator.calculate_and_export(df, spreadsheet_name, sheet_name, 1)
            
            lifetime_sheet_name = 'Lifetime'
            lifetime_df = pd.read_csv(lifetime_file_path)
            lifetime_df['Villagers'] = lifetime_df['Villagers'].apply(eval)
            lifetime_df['Wolves'] = lifetime_df['Wolves'].apply(eval)  
            lifetime_elo_calculator = EloCalculator(credentials_path,aliases_file)
            lifetime_elo_calculator.calculate_and_export(lifetime_df, spreadsheet_name, lifetime_sheet_name, 1)
            
            #Turbo Champs stuff
            current_date_gmt = datetime.datetime.now(datetime.timezone.utc).date()

            # Define the date range
            start_date = datetime.date(current_date_gmt.year, 2, 17)  # February 17
            end_date = datetime.date(current_date_gmt.year, 3, 31)    # March 31

            # Check the conditions for turbo champs 2025
            if (
                final_game_setup not in ineligible_setups and 
                phases != 'sunbae' and 
                current_game_ranked == True and
                start_date <= current_date_gmt <= end_date
                ):
                write_game_log('database/2025_TurboChampDatabase.csv', game_data)
                champs_file_path = 'database/2025_TurboChampDatabase.csv'
                aliases_file = 'aliases.json'
                credentials_path = 'creds/turbo-champs-2025-a3862c5a5d97.json'
                spreadsheet_name = 'HiddenChamps'
                champs_sheet_name = 'Turbo Champs 2025'
                town_sheet_name = 'Sorted by Town'
                wolf_sheet_name = 'Sorted by Wolf'
                # Load data
                champs_df = pd.read_csv(champs_file_path)
                champs_df['Villagers'] = champs_df['Villagers'].apply(eval)
                champs_df['Wolves'] = champs_df['Wolves'].apply(eval)
                champs_elo_calculator = EloCalculator(credentials_path,aliases_file)
                champs_elo_calculator.calculate_and_export_champs(champs_df, spreadsheet_name, champs_sheet_name, town_sheet_name, wolf_sheet_name, 1)

        elif "Error" in response_message:
            print(f"Game failed to rand, reason: {response_message}", flush=True)
            await ctx.send(f"Game failed to rand, reason: {response_message}\nPlease fix the error and re-attempt the rand with thread_id: {thread_id} by typing '!rand -thread_id \"{thread_id}\" so a new game thread is not created.")    
    finally:
        is_rand_running = False
        
@bot.command()
async def test_champs_db(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    if ctx.author.id not in mods:
        return
    current_year = str(datetime.datetime.now().year)
    
    #Turbo Champs stuff
    current_date_gmt = datetime.datetime.now(datetime.timezone.utc).date()

    # Define the date range
    start_date = datetime.date(current_date_gmt.year, 1, 21)  # February 17
    end_date = datetime.date(current_date_gmt.year, 3, 31)    # March 31

    file_path = 'database/' + current_year + '_TurboChampDatabase.csv'
    aliases_file = 'aliases.json'
    credentials_path = 'creds/turbo-champs-2025-a3862c5a5d97.json'
    spreadsheet_name = 'Turbo ELO Sheet'
    sheet_name = 'Test Turbo Champs 2025'
    # Load data
    df = pd.read_csv(file_path)
    df['Villagers'] = df['Villagers'].apply(eval)
    df['Wolves'] = df['Wolves'].apply(eval)
    elo_calculator = EloCalculator(credentials_path,aliases_file)
    elo_calculator.calculate_and_export(df, spreadsheet_name, sheet_name)
    
def fetch_game_data(thread_id):
    """Fetches the game summary JSON from the API."""
    url = f"https://www.mafiauniverse.com/forums/modbot-beta/get-game-summary.php?threadid={thread_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for thread {thread_id}: {response.status_code}")
        return None

def store_game_data(thread_id, summary_json, db_name="game_logs.db"):
    """Stores the full JSON response in the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    json_str = json.dumps(summary_json)  # Convert JSON to string
    
    cursor.execute('''
        INSERT OR REPLACE INTO game_data (thread_id, json_data) 
        VALUES (?, ?)
    ''', (thread_id, json_str))
    
    conn.commit()
    conn.close()
    
def update_db_after_game(thread_id, db_name="game_logs.db"):
    """Fetches and stores the game data for a newly completed game."""
    
    summary_json = fetch_game_data(thread_id)  # Get game data

    if summary_json:
        store_game_data(thread_id, summary_json, db_name)
    else:
        print(f"Failed to fetch data for thread {thread_id}")

def get_game_log(thread_id):
    """Fetches the game summary from the API and returns relevant data."""
    summary_url = f"https://www.mafiauniverse.com/forums/modbot-beta/get-game-summary.php?threadid={thread_id}"
    summary_response = requests.get(summary_url)
    summary_json = summary_response.json()

    town_list = [player['username'] for player in summary_json['players']['town']]
    mafia_list = [player['username'] for player in summary_json['players']['mafia']]

    title = summary_json['title']
    extracted_setup = None
    start_index = title.find(" - [")
    if start_index != -1:
        start_index += len(" - [")
        end_index = title.find(" game]", start_index)
        if end_index != -1:
            extracted_setup = title[start_index:end_index]

    return {
        "Turbo Title": summary_json['title'],
        "Setup": extracted_setup if extracted_setup else "Unknown",
        "Thread ID": summary_json['threadid'],
        "Game ID": summary_json['id'],
        "Winning Alignment": summary_json['winning_alignment'],
        "Villagers": town_list,
        "Wolves": mafia_list
    }
     
def write_game_log(csv_file, game_data):
    """Writes the game summary data to a CSV file."""
    summary_headers = ['Turbo Title', 'Setup', 'Thread ID', 'Game ID', 'Winning Alignment', 'Villagers', 'Wolves']

    with open(csv_file, 'a', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=summary_headers)

        if csvfile.tell() == 0:  # Write header if the file is empty
            csv_writer.writeheader()
        
        csv_writer.writerow(game_data)

@bot.command()
async def suki (ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    quotes = load_flavor_json('sukiquotes.json')
    squote = quotes['quotes']
    suki_quote = random.choice(squote)
    
    await ctx.send(f"Suki Quote 1.0:\n```{suki_quote}```")
    
@bot.command()
async def recon (ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    quotes = load_flavor_json('reconquotes.json')
    squote = quotes['quotes']
    recon_quote = random.choice(squote)
    
    await ctx.send(f"RECONSPARTAN Quote 1.0:\n```{recon_quote}```")

def process(thread_id):
    summary_url = f"https://www.mafiauniverse.com/forums/modbot-beta/get-game-summary.php?threadid={thread_id}"
    summary_response = requests.get(summary_url)
    summary_json = summary_response.json()

    summary_csv = 'game_database.csv'
    summary_headers = ['Turbo Title', 'Setup', 'Thread ID', 'Game ID', 'Winning Alignment', 'Villagers', 'Wolves']
    town = summary_json['players']['town']
    mafia = summary_json['players']['mafia']

    town_list = []
    mafia_list = []

    for player in town:
        town_list.append(player['username'])
        
    for player in mafia:
        mafia_list.append(player['username'])
    
    title = summary_json['title']
    print(title, flush=True)

    start_index = title.find(" - [")
    if start_index != -1:
        start_index += len(" - [")
        end_index = title.find(" game]", start_index)

        if end_index != -1:
            extracted_setup = title[start_index:end_index]
        else:
            session = requests.get(f"https://www.mafiauniverse.com/forums/threads/{thread_id}")
            soup = BeautifulSoup(session.text, 'html.parser')
            title = soup.find('h2', {'class': 'title icon'})
            title_content = title.text.strip()
            start_index = title_content.find(" - [")
            if start_index != -1:
                start_index += len(" - [")
                end_index = title.find(" game]", start_index)

                if end_index != -1:
                    extracted_setup = title[start_index:end_index]
                else:
                    print("No setup found", flush=True)
            else:
                print("No setup found", flush=True)
    else:
        session = requests.get(f"https://www.mafiauniverse.com/forums/threads/{thread_id}")
        soup = BeautifulSoup(session.text, 'html.parser')
        title = soup.find('h2', {'class': 'title icon'})
        title_content = title.text.strip()
        start_index = title_content.find(" - [")
        if start_index != -1:
            start_index += len(" - [")
            end_index = title_content.find(" game]", start_index)

            if end_index != -1:
                extracted_setup = title_content[start_index:end_index]
            else: 
                print("No setup found", flush=True)
        else:
            print("No setup found", flush=True)

    with open(summary_csv, 'a', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=summary_headers)

        if csvfile.tell() == 0:
            csv_writer.writeheader()
        
        csv_writer.writerow({
            "Turbo Title": summary_json['title'],
            "Setup": extracted_setup,
            "Thread ID": summary_json['threadid'],
            "Game ID": summary_json['id'],
            "Winning Alignment": summary_json['winning_alignment'],
            "Villagers": town_list,
            "Wolves": mafia_list,                          
        })

@bot.command()
async def clear(ctx, *args):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return

    global players, waiting_list, game_host_name, current_setup, player_limit    
    
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
        player_limit = 10
        game_host_name = ["Turby"]
        current_setup = "joat10"        
        await ctx.send("Player and waiting list has been cleared. Game is JOAT10 and host is Turby :3")
    else:
        await ctx.send("To clear, run !clear -confirm")

@bot.command()
async def dvc(ctx):
    if ctx.channel.id not in allowed_channels:
        return
    guild = bot.get_guild(dvc_server)
    """members = await guild.query_members(user_ids=[ctx.author.id])
    if ctx.author.id not in members:
        invite = "https://discord.gg/Wt6rVWmG3B"
        await ctx.author.send(f"Here is an invite to the Turbo DVC Discord: {invite}")
    else:
        await ctx.send("You're already in the turbo DVC, liar.")
    """
    invite = "https://discord.gg/Wt6rVWmG3B"
    await ctx.send(f"Join the Turbo DVC/Graveyard here: {invite}")


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

@bot.command()
async def spec(ctx, *args):
    if ctx.channel.id not in allowed_channels:  
        return
    global spec_list

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
        if str(ctx.author.id) not in spec_list:
            spec_list[str(ctx.author.id)] = str(ctx.author.id)
            save_spec_list()
            await ctx.send(f"{ctx.author.mention} has opted in to auto-spec all games they are not in. Please note you will automatically join DVC and be ineligible for subbing so long as you are opted in..")
        else:
            await ctx.send("You're already on the spec list.")
        
    elif args_parsed.opt_out:
        if str(ctx.author.id) in spec_list:
            del spec_list[str(ctx.author.id)]
            save_spec_list()
            await ctx.send(f"{ctx.author.mention} has opted out of auto-spec.")
        else:
            await ctx.send("You're not on the spec list.")

async def new_game_spec_message(bot, thread_id, title):
    global message_ids

    channel = bot.get_channel(dvc_channel)
    
    message_text = f"Game thread: {title}, thread_id: {thread_id} has just randed! React with 👀 to spectate. Make sure you are not in the game or that you have died before adding yourself. Bot will attempt to auto add those who are signed up with their alias."
    message = await channel.send(message_text)
    await message.add_reaction('👀')

    message_ids[thread_id] = message.id
    save_messages()

    return

@bot.event
async def on_message(message):
    global turbo_ping_message
    
    if message.author.id in banned_users:
        return
    if message.channel.id == dvc_channel:
        await bot.process_commands(message)
        return
    
    if message.channel.id == anni_event_channels:
        await bot.process_commands(message)
        return

    if isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)  
        
        if message.author.bot:
            return
        
        log_channel_obj = bot.get_channel(log_channel)

        if log_channel_obj:
            embed = discord.Embed(
                title="New DM Received",
                description=f"**From:** {message.author} ({message.author.id})\n**Message:** {message.content}",
                color=discord.Color.blue()
            )
            await log_channel_obj.send(embed=embed)
        return

    if message.author == bot.user or message.channel.id not in allowed_channels:
        return      
    
    for mention in message.role_mentions:
        if mention.id == 327124222512070656:
            mention_list = [f"<@{id}>" for id in recruit_list if str(id) not in players]                    
            spots = player_limit - len(players)
            opt_in_mentions = ' '.join(mention_list)
            response = await message.channel.send(f'ITS TURBO TIME! {opt_in_mentions}!! +{spots} spots!  React to <:laserbensdog:1337171130166939739> to join the next turbo!')
            turbo_ping_message = response.id
            await response.add_reaction('<:laserbensdog:1337171130166939739>')
    await bot.process_commands(message)
    

@bot.event 
async def on_reaction_add(reaction, user):
    
    if user == bot.user or reaction.message.channel.id not in react_channels or user.id in banned_users:
        return
    global game_host_name, player_limit, players, waiting_list, turbo_ping_message   
    if reaction.message.id == turbo_ping_message:
        if str(reaction.emoji) == '<:laserbensdog:1337171130166939739>':
            if user.id not in aliases:
                await reaction.message.channel.send("Please set your MU username by using !alias MU_Username before inning!")
                return

            alias = aliases[user.id]['active']

            if alias in game_host_name:
                if len(game_host_name) == 1:
                    game_host_name = ["Turby"]    
                    if len(players) < player_limit:
                        players[alias] = 60
                        await reaction.message.channel.send(f"{alias} has been removed as host and added to the list for the next 60 minutes.")
                    else:
                        waiting_list[alias] = 60
                        await reaction.message.channel.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
                elif len(game_host_name) > 1:
                    game_host_name.remove(alias)
                    if len(players) < player_limit:
                        players[alias] = 60
                        await reaction.message.channel.send(f"{alias} has been removed as host and added to the list for the next 60 minutes.")
                    else:
                        waiting_list[alias] = 60
                        await reaction.message.channel.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
                await update_status()    
                return
                
            if alias in players or alias in waiting_list:
                if alias in players:
                    players[alias] = 60
                    
                else:
                    waiting_list[alias] = 60
                    
                await reaction.message.channel.send(f"{alias}'s in has been renewed for the next 60 minutes.")
                #await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
            else:
                if len(players) < player_limit:
                    players[alias] = 60            
                    await reaction.message.channel.send(f'{alias} joined the game!')
                    #await ctx.message.add_reaction('<:bensdog:1337168191465722088>')
                else:
                    waiting_list[alias] = 60
                    #await ctx.send(f"The list is full. {alias} has been added to the waiting list.")
                    #await ctx.message.add_reaction('<:bensdog:1337168191465722088>')           
                    await reaction.message.channel.send(f'{alias} joined the waiting list!')
            await update_status()

    if reaction.message.id == status_id:
        if str(reaction.emoji) == '<:laserbensdog:1337171130166939739>':
            if user.id not in aliases:
                await reaction.message.channel.send("Please set your MU username by using !alias MU_Username before inning!")
                return

            alias = aliases[user.id]['active']

            if alias in game_host_name:
                if len(game_host_name) == 1:
                    game_host_name = ["Turby"]    
                    if len(players) < player_limit:
                        players[alias] = 60
                        await reaction.message.channel.send(f"{alias} has been removed as host and added to the list for the next 60 minutes.")
                    else:
                        waiting_list[alias] = 60
                        await reaction.message.channel.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
                elif len(game_host_name) > 1:
                    game_host_name.remove(alias)
                    if len(players) < player_limit:
                        players[alias] = 60
                        await reaction.message.channel.send(f"{alias} has been removed as host and added to the list for the next 60 minutes.")
                    else:
                        waiting_list[alias] = 60
                        await reaction.message.channel.send(f"The list is full. {alias} has been removed as host and added to the waiting list instead.")
                await update_status()    
                return
                
            if alias in players or alias in waiting_list:
                if alias in players:
                    players[alias] = 60
                    
                else:
                    waiting_list[alias] = 60
                    
                await reaction.message.channel.send(f"{alias}'s in has been renewed for the next 60 minutes.")
                #await ctx.message.add_reaction('👍')
            else:
                if len(players) < player_limit:
                    players[alias] = 60            
                    await reaction.message.channel.send(f'{alias} joined the game!')
                    #await ctx.message.add_reaction('👍')
                else:
                    waiting_list[alias] = 60
                    #await ctx.send(f"The list is full. {alias} has been added to the waiting list.")
                    #await ctx.message.add_reaction('👍')           
                    await reaction.message.channel.send(f'{alias} joined the waiting list!')
            await update_status()
        else:
            print("Didn't match", flush=True)

    if reaction.message.id in message_ids.values():
        role_thread_id = find_key_by_value(message_ids, reaction.message.id)
        role_id = dvc_roles[int(role_thread_id)]
        guild = bot.get_guild(dvc_server)
        role = guild.get_role(role_id)
        member = guild.get_member(user.id)
        await member.add_roles(role)
        channel = bot.get_channel(dvc_channel)
        await channel.send(f"Added <@{user.id}> to #dvc-{str(role_thread_id)}")

@bot.command()
async def clear_dvc(ctx):
    if ctx.channel.id not in allowed_channels:  # Restrict to certain channels
        return
    try:
        await clear_active_games()
        await clear_dvc_roles()
    except:
        print("failed to run clear_dvc", flush=True)

async def clear_active_games():
    games_to_delete = []
    guild = bot.get_guild(dvc_server)

    active_games_category = bot.get_channel(1117176858304336012)
    games_to_delete = active_games_category.channels
    archive = bot.get_channel(dvc_archive)

    for game in games_to_delete:
        try:
            permissions = game.overwrites_for(guild.default_role)
            permissions.read_messages = True
            await game.edit(category=archive)
            await game.set_permissions(guild.default_role, overwrite=permissions)
            await game.send("This channel should now be open to everyone.")
        except:
            print("Failed in games_to_delete", flush=True)


async def clear_dvc_roles():
    roles_to_delete = []

    guild = bot.get_guild(dvc_server)
    for role in guild.roles:
        if "DVC:" in role.name:
            roles_to_delete.append(role)
    
    for role in roles_to_delete:
        try:
            await role.delete()
        except:
            print("Can't delete role", flush=True)
TOKEN = os.environ.get('TOKEN')
# Run the bot
bot.run(TOKEN)

