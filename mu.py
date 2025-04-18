import requests
import hashlib
import re
from urllib3._collections import HTTPHeaderDict
import uuid
import json
import random
from bs4 import BeautifulSoup
### Custom imports
import mafia_roles
import town_roles
import independent_roles
import roles
import rolemadness
from role_definitions import create_random_role
from flavor import joat10_flavor, cop13_flavor, cop9_flavor, vig10_flavor, billager9_flavor, bomb10_flavor
import datetime

def parse_votecount(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("div", style="text-align: center;").text.strip()  # Title of the vote count section

    # Extract votecount table data
    rows = soup.find_all("tr", class_="cms_table_grid_tr")[1:]  # Skip the header row
    vote_data = []
    
    for row in rows:
        cells = row.find_all("td")
        votes = cells[0].text.strip()
        target = cells[1].text.strip()
        voters = cells[2].text.strip()
        vote_data.append([votes, target, voters])
    
    # Extract countdown info
    time_info = soup.find("span", class_="bbc_timezone").text.strip()

    # Format the data into a nice output
    formatted_output = f"\n{title}\n{'=' * len(title)}\n"
    formatted_output += f"{'Votes':<10} {'Target':<20} {'Voters (Posts in Phase)':<40}\n"
    formatted_output += "-" * 70 + "\n"
    
    for vote in vote_data:
        formatted_output += f"{vote[0]:<10} {vote[1]:<20} {vote[2]:<40}\n"
    
    formatted_output += f"\n{time_info}\n"
    
    return formatted_output

def load_json_file(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

data = None

def generate_game_thread_uuid():
    random_uuid = str(uuid.uuid4())[:16]
    return random_uuid
    
def login(username, password):
    session = requests.Session()
    login_url = "https://www.mafiauniverse.com/forums/login.php"  # Replace with the actual login URL

    # Encode the password as MD5 hash
    md5_password = hashlib.md5(password.encode('utf-8')).hexdigest()

    # Form data for login
    payload = {
        "do": "login",
        "vb_login_username": username,
        "vb_login_md5password": md5_password,
        "vb_login_md5password_utf": md5_password,
        "s": "",
        "securitytoken": "guest",
		"vb_login_password": "",
		"vb_login_password_hint": "Password",
		"cookieuser": "1"
    }

    # Send POST request to login
    response = session.post(login_url, data=payload)

    # Check if login was successful (verify response status code, content, or other criteria)
    if response.status_code == 200:
        print("Login successful.")

    else:
        print("Login failed.")
    
    return session

def extract_security_token(response_text):
    # Extract the security token from JavaScript code using regex
    pattern = r'var\s+SECURITYTOKEN\s+=\s+"([^"]+)";'
    match = re.search(pattern, response_text)
    if match:
        security_token = match.group(1)
        return security_token
    return None

def extract_game_id(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    game_id = soup.find('li', {'class': 'game-thread'}).get('data-gameid')

    return game_id

def open_game_thread(session, thread_id):
    url = f"https://www.mafiauniverse.com/forums/threads/{thread_id}"
    response = session.get(url)
    security_token = extract_security_token(response.text)
    game_id = extract_game_id(response.text)

    return game_id, security_token 

def get_vote_total(thread_id, atvote_array=None):
    url = "https://www.mafiauniverse.com/forums/modbot/botpost.php"
    payload = {
        "do": "get_votes",
        "userid": "11",
        "thread_id": thread_id,
        "message": "Votal",
        "securitytoken": "guest",
    }
    if atvote_array:
        payload["atvote_array[]"] = atvote_array
        
    try:
        votes = requests.post(url, data=payload)
        votes.raise_for_status()
        return votes.text
    except Exception as e:
        print(f"Error fetching vote total: {e}")
        return None

def is_day1_near_end(vote_html, minutes=7):
     soup = BeautifulSoup(vote_html, 'html.parser')
     title = soup.find('div', style='text-align: center;')
     if title and "Day 1 Votecount" in title.text:
         countdown = soup.find('span', class_='countdown')
         if countdown and countdown.has_attr('data-date'):
             timestamp = int(countdown['data-date']) // 1000
             current_time = datetime.datetime.utcnow().timestamp()
             return (timestamp - current_time) <= (minutes * 60)
     return False
 
def get_zero_posters(vote_html):
    soup = BeautifulSoup(vote_html, "html.parser")
    zero_posters = []
    
    for row in soup.find_all("tr", class_="cms_table_grid_tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        
        target = cells[1].text.strip()
        if target.lower() == "not voting":
            voters = cells[2].text.strip().split(", ")
            for voter in voters:
                if "(0)" in voter:
                    name = voter.rsplit(" (", 1)[0]  # Extract name before " (0)"
                    zero_posters.append(name)
    
    return zero_posters

def ita_window(session, game_id, security_token):
    url = "https://www.mafiauniverse.com/forums/modbot/ita-window.php"

    payload = {
        "do": "open",
        "game_id": game_id,
        "timeout": "60",
        "securitytoken": security_token
        }
    itas = session.post(url, data=payload)
    return itas.text

def sub_player(session, game_id, player, player_in, security_token):
    url = "https://www.mafiauniverse.com/forums/modbot/subs.php"

    payload = {
        "do": "immediate-sub",
        "game_id": game_id,
        "player": player,
        "player_in": player_in,
        "reason": "Automatic turby replacement",
        "securitytoken": security_token
        }
    subs = session.post(url, data=payload)
    return subs.text
    
def new_thread_token(session):
    protected_url = "https://www.mafiauniverse.com/forums/newthread.php"
    #
    payload = {
        "do": "newthread",
        "f": "8"
        }
        
    response = session.get(protected_url, data=payload)
    
    security_token = extract_security_token(response.text)
    if security_token:
        print("Security token extracted and stored.")
        return security_token
    else:
        print("Failed to extract security token.")
        
def extract_descriptions(role_categories):
    descriptions = []
    for category in role_categories:
        if isinstance(category, dict):
            for role in category.values():
                descriptions.append(role.get('description', 'Unknown role, tell @benneh to fix this!'))
    return descriptions    

def post_thread(session, game_title, security_token, setup, test):

    flavor = load_json_file('flavor.json')
    flavors = flavor['flavors']

    protected_url = "https://www.mafiauniverse.com/forums/newthread.php"

    if setup == "closedrandomXer":
        town_role_names = [name for name in dir(town_roles) if not name.startswith('__')]
        mafia_role_names = [name for name in dir(mafia_roles)  if not name.startswith('__')]
        independent_role_names = [name for name in dir(independent_roles) if not name.startswith('__')]

        town_descriptions = []
        mafia_descriptions = []
        independent_descriptions = []

        town_role_categories = [town_roles.killing_roles, town_roles.utility_roles]
        town_descriptions.extend(extract_descriptions(town_role_categories))

        mafia_role_categories = [mafia_roles.killing_roles, mafia_roles.utility_roles]
        mafia_descriptions.extend(extract_descriptions(mafia_role_categories))

        for name in independent_role_names:
            role = getattr(independent_roles, name)
            independent_descriptions.append(role.get('description', 'Unknown role, tell @benneh to fix this!'))

        town_flavor = "<br>[*]".join(town_descriptions)
        mafia_flavor = "<br>[*]".join(mafia_descriptions)
        independent_flavor = "<br>[*]".join(independent_descriptions)

        town_flavor = "[*]" + town_flavor
        mafia_flavor = "[*]" + mafia_flavor
        independent_flavor = "[*]" + independent_flavor
        game_flavor = f'''[CENTER][TITLE][B]Welcome to a Closed and Random Xer![/B][/TITLE][/CENTER]<br><br>[B][SIZE=4]Roles are randomly selected from Turby’s growing pool of available roles.[/SIZE][/B]<br><br>[BOX=Setup Details]<br><br>[LIST]<br>[*]This setup cannot be fully mountainous unless only 1 wolf is present.<br>[*]The [B][COLOR=#ff0000]wolf team[/COLOR][/B] will always make up 25% of the total players, rounded down. (e.g., 12 players = 3 wolves, 15 players = 3 wolves, 16 players = 4 wolves).<br>[*]Each team’s power roles (PRs) will be calculated as: (number of wolves ÷ 2) [b]or[/b] (number of wolves ÷ 2) + 1. (e.g., 4 wolves = at least 2 PRs, possibly 3).<br>[*]Both teams will have an equal number of PRs in closed random Xers.<br>[*]There is a [COLOR=#800080][B]1.5% chance[/B][/COLOR] that the final vanilla villager will be replaced with an [B][COLOR=#800080]independent role[/COLOR][/B]. Independent roles do not take up town PR slots.<br>[*]In setups with [B]2 POWER ROLES[/B], there can be a maximum of 1 killing role per team. However, killing roles are no longer guaranteed. It is possible to have:<br> - 2 utility roles per team, or  <br> - 2 utility roles for one team and 1 utility + 1 killing role for the other.<br> - A team having 2 killing roles is not possible.<br>[*]If there is [B]1 POWER ROLE[/B] or [B]3 OR MORE POWER ROLES[/B], any combination of killing and utility roles may be assigned to both teams.<br>[*]No power role has a weight assigned—any combination is possible, and balance is not guaranteed.<br>[*]Each wolf has a [B]10%[/B] chance to receive a bulletproof vest in addition to its regular role.<br>[*]There is a [B]20%[/B] overall chance for neighbors to appear in the setup. They can be any pairing of VT/PR/Wolves.<br>[/LIST]<br>[/BOX]<br><br>[BOX=Cop Checks May Not Be Trustworthy!]<br>[LIST]<br>[*][COLOR=#8b4513][B]Millers and Godfathers[/B][/COLOR] may appear in this setup. Millers are unaware of their status and will show as vanilla villagers in their role PMs.<br>[*]Each [B][COLOR=#008000]vanilla townie (VT)[/COLOR][/B] has a [B]2.5%[/B] chance to be a miller instead.<br>[*]Every [B][COLOR=#ff0000]wolf[/COLOR][/B] has a [B]5%[/B] chance to be a godfather in addition to its regular role.<br>[*]The presence of a flipped [B][COLOR=#8b4513]Miller or Godfather[/COLOR][/B] does NOT confirm or deny the existence of cops in the setup.<br>[*][COLOR=#8b4513][B]Millers[/B][/COLOR] do not take up a [B][COLOR=#008000]PR[/COLOR][/B] slot for town—they only replace [B][COLOR=#008000]VTs[/COLOR][/B].<br>[/LIST]<br>[/BOX]<br><br>[BOX=Possible Village Roles][LIST=1]{town_flavor}[/LIST][/BOX]<br><br>[BOX=Possible Independent Roles][LIST=1]{independent_flavor}[/LIST][/BOX]<br><br>[BOX=Possible Wolf Roles][LIST=1]{mafia_flavor}[/LIST][/BOX]<br><br>[BOX=Suffix Legend][LIST=1]<br>[*][B]d(x)[/B] - Ability can be used on Day (x).<br>[*][B]de[/B] - Ability is disabled in Endgame.<br>[*][B]c[/B] - Compulsive action.<br>[*][B]m[/B] - Macho (cannot be protected).<br>[*][B]st[/B] - Self-targetable ability.<br>[*][B]gf[/B] - Godfather role.<br>[/LIST][/BOX]'''

    elif setup == 'cop9' or setup == 'cop13' or setup == 'vig10' or setup == 'joat10' or setup == 'bomb10' or setup == 'billager9':
        game_flavor = globals().get(f"{setup}_flavor", random.choice(flavors))
    else:
        game_flavor = random.choice(flavors)

    if test == False:
        forum = "8"
    else:
        forum = "48"
        
    payload = {
        "do": "postthread",
        "f": forum,
        "s": "",
        "prefixid": "GameThread",
        "subject": f"{game_title} - [{setup} game]",
        "message": game_flavor,
        "message_backup": game_flavor,
        "sbutton": "Submit New Thread",
        "securitytoken": security_token,
        "wysiwyg": "1",
        "iconid": "0",        
        }
        
    response = session.post(protected_url, data=payload)
    
    if response.status_code == 200:
        print("Thread attempt successful.")
        thread_id = extract_thread_id(response.text)
        return thread_id
        
    else:
        print("Thread creation failed.")

def extract_thread_id(response_text):
    start_index = response_text.find('type="hidden" name="t" value="')
    if start_index != -1:
        start_index += len('name="t" type="hidden" value="')
        end_index = response_text.find('"', start_index)
        if end_index != -1:
            thread_id = response_text[start_index:end_index]
            return thread_id
    return None
    
def new_game_token(session, thread_id):
    protected_url = "https://www.mafiauniverse.com/forums/modbot/manage-game/"
    
    payload = {
        "do": "newgame",
        "thread_id": thread_id
        }
        
    response = session.get(protected_url, data=payload)
    
    security_token = extract_security_token(response.text)
    if security_token:
        print("Security token extracted and stored.")
        return security_token
    else:
        print("Failed to extract security token.")


def start_game(session, security_token, game_title, thread_id, player_aliases, game_setup, day_length, night_length, host_name, anon_enabled, player_limit):
    global data

    # Define base game settings (common for all setups)
    base_data = {
        's': '',
        'securitytoken': security_token,
        'submit': '1',
        'do': 'newgame',
        'automated': '0',
        'automation_setting': '2',
        'game_name': f"{game_title} - [{game_setup} game]",
        'thread_id': thread_id,
        'speed_type': '1',
        'game_type': 'Open',  # Default to "Open", update later if needed
        'period': 'day',  # Default starting period
        'phase': '1',
        'phase_end': '',
        'started': '1',
        'start_date': '',
        'votecount_interval': '0',
        'votecount_units': 'minutes',
        'speed_preset': 'custom',
        'day_units': 'minutes',
        'night_units': 'minutes',
        'itas_enabled': '0',
        'default_ita_hit': '15',
        'default_ita_count': '1',
        'ita_immune_policy': '0',
        'alias_pool': 'Greek_Alphabet',
        'daily_post_limit': '0',
        'postlimit_cutoff': '0',
        'postlimit_cutoff_units': 'hours',
        'character_limit': '0',
        'proxy_voting': '0',
        'tied_lynch': '1',
        'self_voting': '0',
        'no_lynch': '1',
        'announce_lylo': '1',
        'votes_locked': '1',
        'votes_locked_manual': '0',
        'auto_majority': '2',
        'maj_delay': '0',
        'show_flips': '0',
        'suppress_rolepms': '0',
        'suppress_phasestart': '0',
        'day_action_cutoff': '1',
        'mafia_kill_enabled': '1',
        'mafia_kill_type': 'kill',
        'detailed_flips': '0',
        'backup_inheritance': '0',
        'mafia_win_con': '1',
        'mafia_kill_assigned': '1',
        'mafia_day_chat': '1',
        'characters_enabled': '2',
        'role_quantity': '1'
    }

    # Modify game type and period based on game setup
    if game_setup in ["closedrandomXer", "randommadnessXer"]:
        base_data["game_type"] = "Closed"
    elif game_setup in ["bean10", "inno4"]:
        base_data["game_type"] = "Open"
        base_data["period"] = "night"  # These games start at night
    elif game_setup in ['quick11']:
        base_data["mafia_kill_enabled"] = "3"
        base_data["show_flips"] = "1"

    # Create an HTTPHeaderDict and add values
    data = HTTPHeaderDict(base_data)

    # Add dynamic game settings
    data.add('day_length', day_length)
    data.add('night_length', night_length)
    data.add('num_hosts', str(len(host_name)))

    # Anonymity settings
    if anon_enabled:
        data.add('aliased', '1')
        data.add('alias_pool', 'Marvel')
    else:
        data.add('aliased', '0')

    # Role Assignment based on game setup
    game_role_map = {
        "joat10": (add_joat_roles, "custom", "10"),
        "bomb10": (add_bomb_roles, "custom", "10"),
        "bean10": (add_bean_roles, "custom", "10"),
        "inno4": (add_inno4_roles, "custom", "4"),
        "billager9": (add_billager9_roles, "custom", "9"),
        "vig10": (add_vig_roles, "vig-10", "10"),
        "bml10": (add_bml_roles, "custom", "10"),
        "closedrandomXer": (add_closedrandomXer_roles, "custom", player_limit),
        "randommadnessXer": (add_randommadnessXer_roles, "custom", player_limit),
        "rolemadness13": (add_rm13_roles, "custom", "13"),
        "ita10": (add_ita10_roles, "custom", "10"),
        "ita13": (add_ita13_roles, "custom", "13"),
        "cop9": (add_cop9_roles, "cop-9", "9"),
        "paritycop9": (add_parity_cop9_roles, "cop-9", "9"),
        "cop13": (add_cop13_roles, "cop-13", "13"),
        "doublejoat13": (add_doublejoat13_roles, "custom", "13"),
        "quick11": (add_quick11_roles, "custom", "11"),
    }

    if game_setup in game_role_map:
        role_function, preset, num_players = game_role_map[game_setup]
        if game_setup in ['closedrandomXer', 'randommadnessXer']:
            role_function(game_title, num_players)
        else:
            role_function(game_title)
        data.add("preset", preset)
        data.add("num_players", str(num_players))
        
        if game_setup in ["inno4", "bean10"]:
            data.add("phase", "0")
        if "ita" in game_setup:
            data.add("itas_enabled", "1")
            data.add("default_ita_hit", "25")
            data.add("default_ita_count", "1")
            data.add("ita_immune_policy", "0")
        if game_setup in ["cop9", "paritycop9", "cop13"]:
            data.add("n0_peeks", "2" if game_setup == "paritycop9" else "1")

    # Add players to game
    add_players(player_aliases, host_name)

    # Submit game request
    protected_url = "https://www.mafiauniverse.com/forums/modbot/manage-game/"
    response = session.post(protected_url, data=data)

    # Handle response
    if response.status_code == 200:
        print("Game rand submitted successfully", flush=True)
        soup = BeautifulSoup(response.text, 'html.parser')
        errors_div = soup.find('div', class_='errors')

        if errors_div:
            blockhead_text = errors_div.find('h2', class_='blockhead').get_text(strip=True)
            if blockhead_text == "Success!":
                success_message = errors_div.find('div', class_='blockrow').find('p').get_text(strip=True)
                print(success_message)
                return success_message
            elif blockhead_text == "Errors":
                error_message = errors_div.find('div', class_='blockrow').find('p').get_text(strip=True)
                print(error_message)
                return error_message
            else:
                print("Unexpected blockhead text received:", blockhead_text, flush=True)
                return f"Unexpected blockhead text received: {blockhead_text}"
        else:
            print("No 'errors' div found in the response.", flush=True)            
            return "No 'errors' div found in the response."
    else:
        print("Game rand failed", flush=True)
        return "Game rand failed"
     
"""def start_game(session, security_token, game_title, thread_id, player_aliases, game_setup, day_length, night_length, host_name, anon_enabled, player_limit):
    global data

    if game_setup == "closedrandomXer" or game_setup == "randommadnessXer":
        setup_title = game_setup
        final_game_setup = game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Closed', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})
    elif game_setup == 'bean10' or game_setup == 'inno4':
        final_game_setup = game_setup
        setup_title = final_game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Open', 'period': 'night', 'phase': '0', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})
         
    else:
        final_game_setup = game_setup
        setup_title = final_game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Open', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})


    data.add('day_length', day_length)
    data.add('night_length', night_length)
    num_hosts = len(host_name)
    data.add('num_hosts', num_hosts)
    
    if anon_enabled == True:
        data.add('aliased', '1')
        data.add('alias_pool', 'Marvel')
    elif anon_enabled == False:
        data.add('aliased', '0')
    
    game_setups = {
        "joat10": {"func": add_joat_roles, "preset": "custom", "num_players": "10", "roles_dropdown": "39"},
        "bomb10": {"func": add_bomb_roles, "preset": "custom", "num_players": "10"},
        "bean10": {"func": add_bean_roles, "preset": "custom", "num_players": "10"},
        "inno4": {"func": add_inno4_roles, "preset": "custom", "num_players": "4"},
        "billager9": {"func": add_billager9_roles, "preset": "custom", "num_players": "9"},
        "vig10": {"func": add_vig_roles, "preset": "vig-10", "num_players": "10"},
        "bml10": {"func": add_bml_roles, "preset": "custom", "num_players": "10"},
        "closedrandomXer": {"func": add_closedrandomXer_roles, "preset": "custom", "num_players": player_limit},
        "randommadnessXer": {"func": add_randommadnessXer_roles, "preset": "custom", "num_players": player_limit},
        "rolemadness13": {"func": add_rm13_roles, "preset": "custom", "num_players": "13"},
        "ita10": {
            "func": add_ita10_roles, "preset": "custom", "num_players": "10",
            "itas_enabled": "1", "default_ita_hit": "25", "default_ita_count": "1", "ita_immune_policy": "0"
        },
        "ita13": {
            "func": add_ita13_roles, "preset": "custom", "num_players": "13",
            "itas_enabled": "1", "default_ita_hit": "25", "default_ita_count": "1", "ita_immune_policy": "0"
        },
        "cop9": {"func": add_cop9_roles, "preset": "cop-9", "num_players": "9", "n0_peeks": "1"},
        "paritycop9": {"func": add_parity_cop9_roles, "preset": "cop-9", "num_players": "9", "n0_peeks": "2"},
        "cop13": {"func": add_cop13_roles, "preset": "cop-13", "num_players": "13", "n0_peeks": "1"},
        "doublejoat13": {"func": add_doublejoat13_roles, "preset": "custom", "num_players": "13"},
    }
    setup_config = game_setups.get(final_game_setup)

    if setup_config:
        # Call the corresponding role-adding function
        setup_config["func"](game_title)

        # Add preset and num_players (mandatory)
        data.add("preset", setup_config["preset"])
        data.add("num_players", str(setup_config["num_players"]))

        # Add any additional settings specific to the game mode
        for key, value in setup_config.items():
            if key not in ["func", "preset", "num_players"]:  # Exclude function reference and mandatory keys
                data.add(key, value)
                
    if final_game_setup == "joat10":
        add_joat_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
        data.add('roles_dropdown', '39')
    if final_game_setup == "bomb10":
        add_bomb_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
    if final_game_setup == "bean10":
        add_bean_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
    if final_game_setup == "inno4":
        add_inno4_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '4')
    if final_game_setup == "billager9":
        add_billager9_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '9')
    if final_game_setup == "vig10":
        add_vig_roles(game_title)
        data.add("preset", "vig-10") 
        data.add('num_players', '10')
    if final_game_setup == "bml10":
        add_bml_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
    if final_game_setup == "closedrandomXer":
        add_closedrandomXer_roles(game_title, player_limit)
        data.add("preset", "custom")
        data.add('num_players', player_limit)
    if final_game_setup == 'randommadnessXer':
        add_randommadnessXer_roles(game_title, player_limit)
        data.add("preset", "custom")
        data.add('num_players', player_limit)
    if final_game_setup == "rolemadness13":
        add_rm13_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '13')
    if final_game_setup == "ita10":
        add_ita10_roles(game_title)
        data.add("preset", "custom")
        data.add("num_players", "10")
        data.add("itas_enabled", "1")
        data.add("default_ita_hit", "25")
        data.add("default_ita_count", "1")
        data.add("ita_immune_policy", "0")
    if final_game_setup == "ita13":
        add_ita13_roles(game_title)
        data.add("preset", "custom")
        data.add("num_players", "13")
        data.add("itas_enabled", "1")
        data.add("default_ita_hit", "25")
        data.add("default_ita_count", "1")
        data.add("ita_immune_policy", "0")
    if final_game_setup == "cop9":
        add_cop9_roles(game_title)
        data.add("preset", "cop-9")
        data.add('num_players', '9')
        data.add('n0_peeks', '1')
    if final_game_setup == "paritycop9":
        add_parity_cop9_roles(game_title)
        data.add("preset", "cop-9")
        data.add('num_players', '9')
        data.add('n0_peeks', '2')
    if final_game_setup == "cop13":
        add_cop13_roles(game_title)
        data.add("preset", "cop-13")
        data.add('num_players', '13')
        data.add('n0_peeks', '1')
    if final_game_setup == "doublejoat13":
        add_doublejoat13_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '13')

    add_players(player_aliases, host_name)
    
    protected_url = "https://www.mafiauniverse.com/forums/modbot/manage-game/"
    response = session.post(protected_url, data=data)
    if response.status_code == 200:
        print("Game rand submitted successfully")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        errors_div = soup.find('div', class_='errors')
        if errors_div:
            blockhead_text = errors_div.find('h2', class_='blockhead').get_text(strip=True)
            
            if blockhead_text == "Success!":
                success_message = errors_div.find('div', class_='blockrow').find('p').get_text(strip=True)
                print(success_message)
                return success_message
            
            elif blockhead_text == "Errors":
                error_message = errors_div.find('div', class_='blockrow').find('p').get_text(strip=True)
                print(error_message)
                return error_message
                
            else:
                print("Unexpected blockhead text received:", blockhead_text)
                return ("Unexpected blockhead text received:", blockhead_text)
        else:
            print("No 'errors' div found in the response.")            
            return ("No 'errors' div found in the response.")

    else:
        print("Game rand fucked up")"""


def load_flavor_jsons():
    name_image_pairs = load_json_file('turboers.json')
    pr_name_image_pairs = load_json_file('powerroles.json')
    wolf_name_image_pairs = load_json_file('wolves.json')
    return name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs

def add_closedrandomXer_roles(game_title, player_limit=13):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    wolf_count = (player_limit * 25) // 100
    village_count = player_limit - wolf_count

    pr_base_count = wolf_count // 2

    village_pr_count = random.randint(pr_base_count, pr_base_count + 1)
    wolf_pr_count = village_pr_count

    if village_pr_count == 2:
        village_killing_role_count = random.randint(0,1)
        wolf_killing_role_count = random.randint(0,1)
        village_utility_role_count = village_pr_count - village_killing_role_count
        wolf_utility_role_count = wolf_pr_count - wolf_killing_role_count
    else:
        village_killing_role_count = random.randint(0, village_pr_count)
        village_utility_role_count = village_pr_count - village_killing_role_count
        wolf_killing_role_count = random.randint(0, wolf_pr_count)
        wolf_utility_role_count = wolf_pr_count - wolf_killing_role_count
    
    village_vt_count = village_count - village_pr_count
    wolf_goon_count = wolf_count - wolf_pr_count


    villagers = random.sample(name_image_pairs, village_vt_count)
    village_prs = random.sample(pr_name_image_pairs, village_pr_count)
    independent_prs = random.sample(pr_name_image_pairs, village_pr_count)
    wolves = random.sample(wolf_name_image_pairs, wolf_count)

    village_killing_roles = [value for key, value in town_roles.killing_roles.items()]
    village_utility_roles = [value for key, value in town_roles.utility_roles.items()]
 
    wolf_killing_roles = [value for key, value in mafia_roles.killing_roles.items()]
    wolf_utility_roles = [value for key, value in mafia_roles.utility_roles.items()]

    thirdparty_roles = [value for key, value in vars(independent_roles).items() if isinstance(value, dict) and '__name__' not in value.keys()]

    selected_village_killing_roles = random.sample(village_killing_roles, village_killing_role_count)
    selected_village_utility_roles = random.sample(village_utility_roles, village_utility_role_count)
    selected_wolf_killing_roles = random.sample(wolf_killing_roles, wolf_killing_role_count)
    selected_wolf_utility_roles = random.sample(wolf_utility_roles, wolf_utility_role_count)

    selected_village_roles = selected_village_killing_roles + selected_village_utility_roles
    selected_wolf_roles = selected_wolf_killing_roles + selected_wolf_utility_roles
    selected_independent_roles = random.sample(thirdparty_roles, 1)
    
    neighbor_rand = random.random()

    vvneighbors, vprvneighbors, vtwneighbors, vprwneighbors, wwneighbors = False, False, False, False, False

    if 0.0 <= neighbor_rand < 0.05:
        vvneighbors = True
    elif 0.05 <= neighbor_rand < 0.1:
        vprvneighbors = True
    elif 0.1 <= neighbor_rand < 0.15:
        vtwneighbors = True
    elif 0.15 <= neighbor_rand < .2:
        vprwneighbors = True
    
    independent_assigned = False

    for i in range(village_vt_count):
        ind_and_miller_rand = random.random()
        
        if not independent_assigned and ind_and_miller_rand <= 0.05:
            role = selected_independent_roles[0].copy()
            independent_assigned = True
        elif ind_and_miller_rand <= 0.1:
            role = roles.miller.copy()
        else:
            role = roles.vt.copy()
            
        role['character_name'] = villagers[i]['character_name']
        role['character_image'] = villagers[i]['character_image']
        
        if vvneighbors and i in [0, 1] or (vtwneighbors and i == 0) or (vprvneighbors and i == 0):
            role['neighbor'] = "a"
                
        data.add("roles[]", json.dumps(role))

    for i in range(0, village_pr_count):
        current_pr = selected_village_roles[i].copy()
        current_pr['character_name'] = f"[COLOR=PURPLE]{village_prs[i]['character_name']}[/COLOR]"
        current_pr['character_image'] = village_prs[i]['character_image']
        if vprvneighbors and i == 0 or (vprwneighbors and i == 0):
            current_pr['neighbor'] = "a"

        data.add("roles[]", json.dumps(current_pr))
        
    for i in range(0, wolf_pr_count):
        wolf = wolves.pop(0)
        bpv_rand = random.random()
        gf_rand = random.random()

        current_wolf = selected_wolf_roles[i].copy()
        if bpv_rand <=.1:
            current_wolf['bpv_status'] = "1"
        if gf_rand <=.05:
            current_wolf['godfather'] = "1"
        if vtwneighbors and i == 0 or (vprwneighbors and i == 0):
            current_wolf['neighbor'] = "a"
            
        current_wolf['character_name'] = wolf['character_name']
        current_wolf['character_image'] = wolf['character_image']

        data.add("roles[]", json.dumps(current_wolf))

    for i in range(0, wolf_goon_count):
        wolf = wolves.pop(0)
        bpv_rand = random.random()
        gf_rand = random.random()

        current_wolf = roles.goon.copy()
        if bpv_rand <=.1:
            current_wolf['bpv_status'] = "1"
        if gf_rand <=.05:
            current_wolf['godfather'] = "1"

        current_wolf['character_name'] = wolf['character_name']
        current_wolf['character_image'] = wolf['character_image']
        data.add("roles[]", json.dumps(current_wolf))

def add_randommadnessXer_roles(game_title, player_limit=13):
    global data
    
    name_image_pairs, pr_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    wolf_count = (player_limit * 25) // 100
    village_count = player_limit - wolf_count
    
    
    villagers = random.sample(name_image_pairs, village_count)
    wolves = random.sample(wolf_name_image_pairs, wolf_count)

    for i in range(0, village_count):
        current_villa = create_random_role("Village")
        current_villa['character_name'] = villagers[i]['character_name']
        current_villa['character_image'] = villagers[i]['character_image']
        villa_json = json.dumps(current_villa)
        data.add("roles[]", villa_json)
        
    for i in range(0, wolf_count):
        wolf = wolves.pop(0)
        current_wolf = create_random_role("Wolf")
        current_wolf['character_name'] = wolf['character_name']
        current_wolf['character_image'] = wolf['character_image']
        wolf_json = json.dumps(current_wolf)
        data.add("roles[]", wolf_json)

def add_rm13_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 10)
    wolves = random.sample(wolf_name_image_pairs, 3)

    for i in range(0,10):
        randomized_role_data = rolemadness.create_role_data('village')
        randomized_role_data['character_name'] = villagers[i]['character_name']
        randomized_role_data['character_image'] = villagers[i]["character_image"]
        role_json = json.dumps(randomized_role_data)
        data.add("roles[]", role_json)
  
    for i in range(0,3):
        randomized_role_data = rolemadness.create_role_data('wolf')
        randomized_role_data['character_name'] = wolves[i]['character_name']
        randomized_role_data['character_image'] = wolves[i]["character_image"]
        role_json = json.dumps(randomized_role_data)
        data.add("roles[]", role_json)

def add_ita10_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 8)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,8):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)

    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)

def add_ita13_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 9)
    wolves = random.sample(wolf_name_image_pairs, 4)

    for i in range(0,9):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
   
    for i in range(0,4):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)


def add_joat_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 7)
    joat = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
 
    current_joat = town_roles.utility_roles['joat_peekvigdoc'].copy()
    current_joat['character_name'] = f"[COLOR=PURPLE]{joat[0]['character_name']}[/COLOR]"
    current_joat['character_image'] = joat[0]["character_image"]
    joat_json = json.dumps(current_joat)
    data.add("roles[]", joat_json)
 
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        
def add_bean_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 6)
    powerroles_bean = random.sample(pr_name_image_pairs, 2)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
  

    for i in range(0,2):
        if i < 1:
            current_inven = roles.doc.copy()
            current_inven['character_name'] = f"[COLOR=PURPLE]{powerroles_bean[i]['character_name']}[/COLOR]"
            current_inven['character_image'] = powerroles_bean[i]["character_image"]
            inven_json = json.dumps(current_inven)
            data.add("roles[]", inven_json)
        else:
            current_vig = roles.vig_even.copy()
            current_vig['character_name'] = f"[COLOR=PURPLE]{powerroles_bean[i]['character_name']}[/COLOR]"
            current_vig['character_image'] = powerroles_bean[i]["character_image"]
            vig_json = json.dumps(current_vig)
            data.add("roles[]", vig_json)
            
    for i in range(0,2):
        if i < 1:
            current_wolves = roles.rb_nc.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        else:
            current_wolves = mafia_roles.killing_roles['prk_1x'].copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)

def add_quick11_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 7)
    powerroles_quick = random.sample(pr_name_image_pairs, 2)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
  

    for i in range(0,2):
        if i < 1:
            current_pr = roles.jailkeeper.copy()
            current_pr['character_name'] = f"[COLOR=PURPLE]{powerroles_quick[i]['character_name']}[/COLOR]"
            current_pr['character_image'] = powerroles_quick[i]["character_image"]
            pr_json = json.dumps(current_pr)
            data.add("roles[]", pr_json)
        else:
            current_pr = roles.neopolitan.copy()
            current_pr['character_name'] = f"[COLOR=PURPLE]{powerroles_quick[i]['character_name']}[/COLOR]"
            current_pr['character_image'] = powerroles_quick[i]["character_image"]
            pr_json = json.dumps(current_pr)
            data.add("roles[]", pr_json)
            
    for i in range(0,2):
        if i < 1:
            current_wolves = roles.strongman_goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        else:
            current_wolves = roles.rolecop.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)

def add_bomb_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 6)
    powerroles_bomb = random.sample(pr_name_image_pairs, 2)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
  


    for i in range(0,2):
        if i < 1:
            current_inven = town_roles.killing_roles['inv_1xsuibomb'].copy()
            current_inven['character_name'] = f"[COLOR=PURPLE]{powerroles_bomb[i]['character_name']}[/COLOR]"
            current_inven['character_image'] = powerroles_bomb[i]["character_image"]
            inven_json = json.dumps(current_inven)
            data.add("roles[]", inven_json)
        else:
            current_inven = town_roles.utility_roles['ic_d2plus'].copy()
            current_inven['character_name'] = f"[COLOR=PURPLE]{powerroles_bomb[i]['character_name']}[/COLOR]"
            current_inven['character_image'] = powerroles_bomb[i]["character_image"]
            inven_json = json.dumps(current_inven)
            data.add("roles[]", inven_json)
            
    for i in range(0,2):
        if i < 1:
            current_wolves = mafia_roles.killing_roles['prk_1x'].copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        else:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
 
def add_inno4_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 2)
    power_roles = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 1)

    for i in range(0,2):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
  

    current_ic = roles.ic.copy()
    current_ic['character_name'] = f"[COLOR=PURPLE]{power_roles[0]['character_name']}[/COLOR]"
    current_ic['character_image'] = power_roles[0]["character_image"]
    ic_json = json.dumps(current_ic)
    data.add("roles[]", ic_json)
            
    current_wolves = roles.goon.copy()
    current_wolves['character_name'] = wolves[0]['character_name']
    current_wolves['character_image'] = wolves[0]['character_image']
    wolf_json = json.dumps(current_wolves)
    data.add("roles[]", wolf_json)
            
def add_bml_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 7)
    powerroles_bml = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
   

    current_inven = town_roles.killing_roles['inv_2xdayvig'].copy()
    current_inven['character_name'] = f"[COLOR=PURPLE]{powerroles_bml[0]['character_name']}[/COLOR]"
    current_inven['character_image'] = powerroles_bml[0]["character_image"]
    inven_json = json.dumps(current_inven)
    data.add("roles[]", inven_json)
    
    for i in range(0,2):
        if i < 1:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        else:
            current_wolves = mafia_roles.utility_roles['rb_2x'].copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
       



def add_doublejoat13_roles(game_title):

    global data
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 8)
    joat = random.sample(pr_name_image_pairs, 2)
    wolves = random.sample(wolf_name_image_pairs, 3)    

    for i in range(0,8):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
    
    for i in range(0,2):
            current_joat = town_roles.utility_roles['joat_peekvigdoc_even' if i >= 1 else 'joat_peekvigdoc_odd'].copy()
            current_joat['character_name'] = f"[COLOR=PURPLE]{joat[i]['character_name']}[/COLOR]"
            current_joat['character_image'] = joat[i]["character_image"]
            joat_json = json.dumps(current_joat)
            data.add("roles[]", joat_json)
            
    for i in range(0,3):
        if i < 2:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        
        else:
            current_wolves = mafia_roles.utility_roles['joat_rb_rd_track'].copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
  
def add_vig_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 7)
    vig = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
    
    current_vig = town_roles.killing_roles['vig_2x'].copy()
    current_vig['character_name'] = f"[COLOR=PURPLE]{vig[0]['character_name']}[/COLOR]"
    current_vig['character_image'] = vig[0]['character_image']
    vig_json = json.dumps(current_vig)
    data.add("roles[]", vig_json)
    
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
 

def post(session, thread_id, security_token, message):
	url = f"https://www.mafiauniverse.com/forums/newreply.php?do=postreply&t={thread_id}"
	payload = {
		"do": "postreply",
		"t": thread_id,
		"p": "who cares",
		"sbutton": "Post Quick Reply",
		"wysiwyg": "0",
		"message": message,
		"message_backup": message,
		"fromquickreply": "1",
		"securitytoken": security_token
		}
	post = session.post(url, data=payload)
	return post.text

def add_billager9_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 6)
    fv = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
   
    current_fv = town_roles.utility_roles['fv_loyal'].copy()
    current_fv['character_name'] = f"[COLOR=PURPLE]{fv[0]['character_name']}[/COLOR]"
    current_fv['character_image'] = fv[0]["character_image"]
    fv_json = json.dumps(current_fv)
    data.add("roles[]", fv_json)
     
    for i in range(0,2):
        if i < 1:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
        else:
            current_wolves = mafia_roles.utility_roles['fv'].copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
       
        
def add_cop9_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 6)
    cop = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
   
    current_cop = town_roles.utility_roles['cop'].copy()
    current_cop['character_name'] = f"[COLOR=PURPLE]{cop[0]['character_name']}[/COLOR]"
    current_cop['character_image'] = cop[0]["character_image"]
    cop_json = json.dumps(current_cop)
    data.add("roles[]", cop_json)
     
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
 
def add_parity_cop9_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 6)
    cop = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
   
    current_cop = town_roles.utility_roles['parity_cop_m'].copy()
    current_cop['character_name'] = f"[COLOR=PURPLE]{cop[0]['character_name']}[/COLOR]"
    current_cop['character_image'] = cop[0]["character_image"]
    cop_json = json.dumps(current_cop)
    data.add("roles[]", cop_json)
     
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)

def add_cop13_roles(game_title):
	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 9)
    cop = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 3)

    for i in range(0,9):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]['character_name']
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
  
    current_cop = town_roles.utility_roles['cop'].copy()
    current_cop['character_name'] = f"[COLOR=PURPLE]{cop[0]['character_name']}[/COLOR]"
    current_cop['character_image'] = cop[0]["character_image"]
    cop_json = json.dumps(current_cop)
    data.add("roles[]", cop_json)
     
    for i in range(0,3):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
 
def add_players(player_aliases, host_name):
    global data
    
    for host in host_name:
        data.add("host_name[]", host)
    
    for player_id in player_aliases:
        data.add("player_name[]", player_id)
        data.add("player_alias[]", "")
