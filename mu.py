import requests
import hashlib
import re
from urllib3._collections import HTTPHeaderDict
import uuid
import json
import random
import mafia_roles
import town_roles
import roles
import rolemadness
from bs4 import BeautifulSoup

def load_json_file(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)


#with open('turboers.json', 'r') as file:
#    name_image_pairs = json.load(file)
#with open('powerroles.json', 'r') as file:
#    pr_name_image_pairs = json.load(file)
#with open('wolves.json', 'r') as file:
#    wolf_name_image_pairs = json.load(file)

data = None

def generate_game_thread_uuid():
    random_uuid = str(uuid.uuid4())[:16]
    return f"Automated turbo game thread: {random_uuid}"
    
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
        "securitytoken": "guest"
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
        "reason": "Automatic turbot replacement",
        "securitytoken": security_token
        }
    subs = session.post(url, data=payload)
    return subs.text
    
def new_thread_token(session):
    protected_url = "https://www.mafiauniverse.com/forums/newthread.php"
    
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

def list_dicts_in_module(module):
    dict_names = [name for name in dir(module) if isinstance(getattr(module, name), dict)]
    return dict_names

def post_thread(session, game_title, security_token, setup):

    flavor = load_json_file('flavor.json')
    flavors = flavor['flavors']

    protected_url = "https://www.mafiauniverse.com/forums/newthread.php"

    if setup == "closedrandom10er":
        town_role_names = [name for name in dir(town_roles) if not name.startswith('__')]
        mafia_role_names = [name for name in dir(mafia_roles)  if not name.startswith('__')]

        town_flavor = "<br>".join(town_role_names)
        mafia_flavor = "<br>".join(mafia_role_names)

        game_flavor = f"This is a closed and random 10er. Roles have been randomly selected from a pool of roles Turby has access to that is ever growing. <br><br>This cannot rand as mountainous.<br><br>The village rands between 1 and 2 PRs. If the village rands 1 PR, the wolves rand between 0 and 1 PRs. If the village rands 2 PRs, the wolves rand between 1 and 2 PRs. There is no weight assigned to any power roles--any variation of these setups is possible and balance is not guaranteed.<br><br>Millers can be randed into this setup. Each VT has a standalone 5% chance to rand as a miller instead. This does [b]NOT[/b] confirm or deny the existance of cops. Millers do not count as a 'PR' slot for the town. Godfathers may exist for mafia, but only as PR roles and the ones that are are noted in the role list below. <br><br>There are at most 2 PRs for the village and at most 2 for the wolves. <br><br>These are the roles possible for the village: <br><br>{town_flavor}<br><br>These are the roles possible for wolves:<br><br>{mafia_flavor}<br><br><br>[COLOR=\"#FF0000\"][U][B]Suffix Legend:[/B][/U][/COLOR]<br>[B]d(x)[/B] - Day (x) use of the PR<br>[B]de[/B] - Disabled in Endgame<br>[B]c [/B]- Compulsive<br>[B]m [/B]- Macho<br>[B]st [/B]- Self-Targetable<br>[B]gf [/B]- Godfather"
    else:
        game_flavor = random.choice(flavors)
        
    payload = {
        "do": "postthread",
        "f": "8",
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
        
def start_game(session, security_token, game_title, thread_id, player_aliases, game_setup, day_length, night_length, host_name, anon_enabled):
    global data

    if game_setup == "random10er":
        potential_setups = ["joat10", "vig10", "bomb10", "bml10"]
        final_game_setup = random.choice(potential_setups)
        setup_title = final_game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Open', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})

    elif game_setup == "closedrandom10er":
        #potential_setups = ["closedjoat10", "closedvig10", "closedbomb10", "closedbml10"]
        setup_title = "closedrandom10er"
        final_game_setup = game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Closed', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})
    elif game_setup == "rolemadness13":
        setup_title = "turby role madness 13er!"
        final_game_setup = game_setup
        data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': f"{game_title} - [{setup_title} game]", 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Closed', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_units': 'minutes', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '1', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})

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
    

    if final_game_setup == "joat10":
        add_joat_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
        data.add('roles_dropdown', '39')
    if final_game_setup == "bomb10":
        add_bomb_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
    if final_game_setup == "vig10":
        add_vig_roles(game_title)
        data.add("preset", "vig-10") 
        data.add('num_players', '10')
    if final_game_setup == "bml10":
        add_bml_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
    if final_game_setup == "closedrandom10er":
        add_closedrandom10er_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
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
        print("Game rand fucked up")

def load_flavor_jsons():
    name_image_pairs = load_json_file('turboers.json')
    pr_name_image_pairs = load_json_file('powerroles.json')
    wolf_name_image_pairs = load_json_file('wolves.json')
    return name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs

def add_closedrandom10er_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    village_pr_count = random.randint(1,2)
    if village_pr_count == 2:
        wolf_pr_count = random.randint(1,2)
    else:
        wolf_pr_count = random.randint(0,1)
    
    village_vt_count = 8 - village_pr_count
    wolf_goon_count = 2 - wolf_pr_count

    villagers = random.sample(name_image_pairs, village_vt_count)
    village_prs = random.sample(pr_name_image_pairs, village_pr_count)
    wolves = random.sample(wolf_name_image_pairs, 2)

    village_roles = [value for key, value in vars(town_roles).items() if isinstance(value, dict)]
    wolf_roles = [value for key, value in vars(mafia_roles).items() if isinstance(value, dict)]

    selected_village_roles = random.sample(village_roles, village_pr_count)
    selected_wolf_roles = random.sample(wolf_roles, wolf_pr_count)

    for i in range(0, village_pr_count):
        current_pr = selected_village_roles[i].copy()
        current_pr['character_name'] = village_prs[i]['character_name']
        current_pr['character_image'] = village_prs[i]['character_image']
        pr_json = json.dumps(current_pr)
        data.add("roles[]", pr_json)
        
    for i in range(0, wolf_pr_count):
        wolf = wolves.pop(0)
        current_wolf = selected_wolf_roles[i].copy()
        current_wolf['character_name'] = wolf['character_name']
        current_wolf['character_image'] = wolf['character_image']
        wolf_json = json.dumps(current_wolf)
        data.add("roles[]", wolf_json)

    for i in range(0, wolf_goon_count):
        wolf = wolves.pop(0)
        current_wolf = roles.goon.copy()
        current_wolf['character_name'] = wolf['character_name']
        current_wolf['character_image'] = wolf['character_image']
        wolf_json = json.dumps(current_wolf)
        data.add("roles[]", wolf_json)

    for i in range(0, village_vt_count):
        miller_rand = random.random()

        if miller_rand <=.05:
            current_vt = roles.miller.copy()
        else:
            current_vt = roles.vt.copy()
        current_vt['character_name'] = villagers[i]['character_name']
        current_vt['character_image'] = villagers[i]['character_image']
        vt_json = json.dumps(current_vt)
        data.add("roles[]", vt_json)


def add_rm13_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 10)
    wolves = random.sample(wolf_name_image_pairs, 3)

    for i in range(0,10):
        randomized_role_data = rolemadness.create_role_data('village')
        randomized_role_data['character_name'] = villagers[i]["character_name"]
        randomized_role_data['character_image'] = villagers[i]["character_image"]
        role_json = json.dumps(randomized_role_data)
        data.add("roles[]", role_json)
  
    for i in range(0,3):
        randomized_role_data = rolemadness.create_role_data('wolf')
        randomized_role_data['character_name'] = wolves[i]["character_name"]
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
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
      
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolves submit an action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    

def add_ita13_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 9)
    wolves = random.sample(wolf_name_image_pairs, 4)

    for i in range(0,9):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
      
    for i in range(0,4):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolves submit an action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    


def add_joat_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 7)
    joat = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    

    current_joat = town_roles.joat_peekvigdoc.copy()
    current_joat['character_name'] = joat[0]["character_name"]
    current_joat['character_image'] = joat[0]["character_image"]
    joat_json = json.dumps(current_joat)
    data.add("roles[]", joat_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Jack of All Trades (x1 Alignment Cop, x1 Doctor, x1 Vigilante)[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Jack Of All Trades[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Jack Of All Trades[/COLOR][/B], you have access to one or more miscellaneous night actions.\n\n[SIZE=4][B][I]x1 Alignment Cop[/I][/B][/SIZE]\n\nYou have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Doctor[/I][/B][/SIZE]\n\nYou have access to the [B]Protection[/B] Night Action. Protection will protect your target from being killed. You will not learn whether you successfully protected someone. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Vigilante[/I][/B][/SIZE]\n\nYou have access to the [B]Shoot[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have multiple uses of your abilities, you must cycle through all of them before being allowed to reuse any of them.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")       
    
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolves submit an action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    

def add_bomb_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 6)
    powerroles_bomb = random.sample(pr_name_image_pairs, 2)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    
    for i in range (0,2):
        if i < 1:
            current_ic = town_roles.ic.copy()
            current_ic['character_name'] = powerroles_bomb[i]["character_name"]
            current_ic['character_image'] = powerroles_bomb[i]["character_image"]
            ic_json = json.dumps(current_ic)
            data.add("roles[]", ic_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#339933]Village Innocent Child[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n[SIZE=4][B][I]Village Innocent Child[/I][/B][/SIZE]\nAs [B][COLOR=#339933]Village Innocent Child[/COLOR][/B], you have access to the [B]Claim Innocence[/B] Day action. Claiming your innocence announces your role and alignment in the Game thread for all to see. Submit your claim at any time during a Day, and your role and alignment will be announced in the Game thread. Submit your action using the form below the game thread.\n[B]Note:[/B] Innocence claims may take up to one minute to process.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")       
        else: 
            current_inven = town_roles.inv_1xsuibomb.copy()
            current_inven['character_name'] = powerroles_bomb[i]["character_name"]
            current_inven['character_image'] = powerroles_bomb[i]["character_image"]
            inven_json = json.dumps(current_inven)
            data.add("roles[]", inven_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Inventor (x1 Suicide Bomber)[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Inventor[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Inventor[/COLOR][/B], you have access to the [B]Give Item[/B] Night Action. Give Item allows you to send your target one of your items from the options below. The description you see below each item are the abilities your targets will receive. Each item is a single-use action or passive ability that will disappear once it has been used by your target.\n\n[SIZE=4]Item(s): [B][I]x1 Suicide Bomber[/I][/B][/SIZE][QUOTE]You have access to the [B]Suicide Bomb[/B] Day Action. You and the player targeted with this action will die within one minute after submission unless protected.[/QUOTE]\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have at least two different types of items, you must cycle through all of the types before you can give the same one out again.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
            
    for i in range(0,2):
        if i < 1:
            current_wolves = mafia_roles.prk.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf Power Role Killer[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an action, a player will be picked at random from the living non-Wolf players.\n[hr][/hr]\n[SIZE=4][B][I]Wolf Power Role Killer[/I][/B][/SIZE]\nAs [B][COLOR=#ff2244]Wolf Power Role Killer[/COLOR][/B], you have access to the [B]Power Role Kill[/B] Night Action. Players targeted with this action will die if they have a power role (i.e. are not a Vanilla Villager or Wolf) at the end of the Night unless protected. If they do not have a power role (i.e. are not a Vanilla Villager or Wolf Goon), this action will not affect them. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf you do not submit an action, you will forego your action on that night.\n{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
        else:
            current_wolves = mafia_roles.rb_1x.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#ff2244]Wolf Roleblocker | 1-Shot, Non-consecutive[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\n\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf no Wolf submits an action, a player will be picked at random from the living non-Wolf players.\n\n[hr][/hr][SIZE=4][B][I]Wolf Roleblocker[/I][/B][/SIZE]\n\nAs [B][COLOR=#ff2244]Wolf Roleblocker[/COLOR][/B], you have access to the [B]Roleblock[/B] Night Action. Roleblocking another player prevents them from being able to successfully use any Night Action that they might have that night. You will not learn whether your target had a Night Action. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf you do not submit an action, you will forego your action on that night.\n\n[SIZE=4][B][I]Non-consecutive[/I][/B][/SIZE]\n\nThe [B]Non-consecutive[/B] modifier prohibits you from targeting the same player two Cycles in a row.\n\n[SIZE=4][B][I]X-Shot[/I][/B][/SIZE]\n\nThe [B]X-Shot[/B] modifier limits the number of times you can use your Night actions. If you spend all of your shots then you will not be able to use Night actions anymore.\n\nYou have [B]1 shots[/B] at the start of the game.{{HIDE_FROM_FLIP}}\n\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")


def add_bml_roles(game_title):
    global data
    
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 7)
    powerroles_bml = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    

    current_inven = town_roles.inv_2xdayvig.copy()
    current_inven['character_name'] = powerroles_bml[0]["character_name"]
    current_inven['character_image'] = powerroles_bml[0]["character_image"]
    inven_json = json.dumps(current_inven)
    data.add("roles[]", inven_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Inventor (x2 Day Vigilante) | Non-consecutive[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Inventor[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Inventor[/COLOR][/B], you have access to the [B]Give Item[/B] Night Action. Give Item allows you to send your target one of your items from the options below. The description you see below each item are the abilities your targets will receive. Each item is a single-use action or passive ability that will disappear once it has been used by your target.\n\n[SIZE=4]Item(s): [B][I]x2 Day Vigilante[/I][/B][/SIZE][QUOTE]You have access to the [B]Shoot[/B] Day Action. Players targeted with this action will die within one minute after submission unless protected. Only one shot can be fired per player per Day. Submit your action during the Day using the form below the game thread.[/QUOTE]\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have at least two different types of items, you must cycle through all of the types before you can give the same one out again.\n\n[SIZE=4][B][I]Non-consecutive[/I][/B][/SIZE]\n\nThe [B]Non-consecutive[/B] modifier prohibits you from targeting the same player two Cycles in a row.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    
    for i in range(0,2):
        if i < 1:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
        else:
            current_wolves = mafia_roles.rb_2x.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#ff2244]Wolf Roleblocker | 2-Shot, Non-consecutive[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\n\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf no Wolf submits an action, a player will be picked at random from the living non-Wolf players.\n\n[hr][/hr][SIZE=4][B][I]Wolf Roleblocker[/I][/B][/SIZE]\n\nAs [B][COLOR=#ff2244]Wolf Roleblocker[/COLOR][/B], you have access to the [B]Roleblock[/B] Night Action. Roleblocking another player prevents them from being able to successfully use any Night Action that they might have that night. You will not learn whether your target had a Night Action. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf you do not submit an action, you will forego your action on that night.\n\n[SIZE=4][B][I]Non-consecutive[/I][/B][/SIZE]\n\nThe [B]Non-consecutive[/B] modifier prohibits you from targeting the same player two Cycles in a row.\n\n[SIZE=4][B][I]X-Shot[/I][/B][/SIZE]\n\nThe [B]X-Shot[/B] modifier limits the number of times you can use your Night actions. If you spend all of your shots then you will not be able to use Night actions anymore.\n\nYou have [B]1 shots[/B] at the start of the game.{{HIDE_FROM_FLIP}}\n\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
       



def add_doublejoat13_roles(game_title):

    global data
    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()

    villagers = random.sample(name_image_pairs, 9)
    joat = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 3)    

    for i in range(0,9):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
      
    current_joat = town_roles.joat_peekvigdoc.copy()
    current_joat['character_name'] = joat[0]["character_name"]
    current_joat['character_image'] = joat[0]["character_image"]
    joat_json = json.dumps(current_joat)
    data.add("roles[]", joat_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Jack of All Trades (x1 Alignment Cop, x1 Doctor, x1 Vigilante)[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Jack Of All Trades[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Jack Of All Trades[/COLOR][/B], you have access to one or more miscellaneous night actions.\n\n[SIZE=4][B][I]x1 Alignment Cop[/I][/B][/SIZE]\n\nYou have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Doctor[/I][/B][/SIZE]\n\nYou have access to the [B]Protection[/B] Night Action. Protection will protect your target from being killed. You will not learn whether you successfully protected someone. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Vigilante[/I][/B][/SIZE]\n\nYou have access to the [B]Shoot[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have multiple uses of your abilities, you must cycle through all of them before being allowed to reuse any of them.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")       
    
    for i in range(0,3):
        if i < 2:
            current_wolves = roles.goon.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    
        
        else:
            current_wolves = mafia_roles.joat_rb_rd_track.copy()
            current_wolves['character_name'] = wolves[i]['character_name']
            current_wolves['character_image'] = wolves[i]['character_image']
            wolf_json = json.dumps(current_wolves)
            data.add("roles[]", wolf_json)
            data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf Jack of All Trades (x1 Redirector, x1 Tracker, x1 Roleblock)[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players. \n\n[SIZE=4][B][I]][COLOR=#ff2244]Wolf Jack of All Trades[/COLOR][/B][/I][/SIZE]\n\n As [B][COLOR=#ff2244]Wolf Jack Of All Trades[/COLOR][/B], you have access to one or more miscellaneous night actions.\n\n[SIZE=4][B][I]x1 Roleblocker[/I][/B][/SIZE]\n\nYou have access to the [B]Roleblocking[/B] Night Action. Roleblocking another player prevents them from being able to successfully use any Night Action that they might have that night. You will not learn whether your target had a Night Action. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Redirector[/I][/B][/SIZE]\n\nYou have access to the [B]Redirect[/B] Night Action. Redirecting forces Target A's single-target actions (e.g. Roleblock, but not Redirector) onto Target B. You may not submit the same target for both A and B. You will not learn whether your target had a Night Action.\n\nPlayers will [U]not[/U] be informed if their action was redirected. Actions with reports (e.g. Alignment Cops) will show the target they ended the Night on in the report, but not why or how it changed.\n\n[SIZE=4][B][I]x1 Tracker[/I][/B][/SIZE]\n\nYou have access to the [B]Tracking[/B] Night Action. Tracking another player informs you who that player used a Night Action on that night, if any. You will not learn what type of Night Action your target has. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have multiple uses of your abilities, you must cycle through all of them before being allowed to reuse any of them.\n\n{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")

def add_vig_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 7)
    vig = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,7):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    
    current_vig = town_roles.vig_2x.copy()
    current_vig['character_name'] = vig[0]['character_name']
    current_vig['character_image'] = vig[0]['character_image']
    vig_json = json.dumps(current_vig)
    data.add("roles[]", vig_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Vigilante | 2-shot[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Vigilante[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Vigilante[/COLOR][/B], you have access to the [B]Shoot[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that night.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")        
    
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    


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

def add_cop9_roles(game_title):	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 6)
    cop = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 2)

    for i in range(0,6):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
  
    current_cop = town_roles.cop.copy()
    current_cop['character_name'] = cop[0]["character_name"]
    current_cop['character_image'] = cop[0]["character_image"]
    cop_json = json.dumps(current_cop)
    data.add("roles[]", cop_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Alignment Cop[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Alignment Cop[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Alignment Cop[/COLOR][/B], you have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, a player will be picked at random from the un-Inspected living players.{{HIDE_FROM_FLIP}}\n\n{{NIGHT_0_PEEKS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
     
    for i in range(0,2):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    


def add_cop13_roles(game_title):
	
    global data

    name_image_pairs, pr_name_image_pairs, wolf_name_image_pairs = load_flavor_jsons()
    villagers = random.sample(name_image_pairs, 9)
    cop = random.sample(pr_name_image_pairs, 1)
    wolves = random.sample(wolf_name_image_pairs, 3)

    for i in range(0,9):
        current_vanchilla = roles.vt.copy()
        current_vanchilla['character_name'] = villagers[i]["character_name"]
        current_vanchilla['character_image'] = villagers[i]["character_image"]
        vt_json = json.dumps(current_vanchilla)
        data.add("roles[]", vt_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Villager[/COLOR][/B]. You win when all threats to the Village have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
  
    current_cop = town_roles.cop.copy()
    current_cop['character_name'] = cop[0]["character_name"]
    current_cop['character_image'] = cop[0]["character_image"]
    cop_json = json.dumps(current_cop)
    data.add("roles[]", cop_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Village Alignment Cop[/COLOR][/B]. You win when all threats to the Village have been eliminated.\n\n[SIZE=4][B][I]Village Alignment Cop[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Village Alignment Cop[/COLOR][/B], you have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, a player will be picked at random from the un-Inspected living players.{{HIDE_FROM_FLIP}}\n\n{{NIGHT_0_PEEKS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
     
    for i in range(0,3):
        current_wolves = roles.goon.copy()
        current_wolves['character_name'] = wolves[i]['character_name']
        current_wolves['character_image'] = wolves[i]['character_image']
        wolf_json = json.dumps(current_wolves)
        data.add("roles[]", wolf_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Wolf[/COLOR][/B]. You win when you overpower the Village and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Wolf Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Wolf[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Wolf submits an  action, a player will be picked at random from the living non-Wolf players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    

def add_players(player_aliases, host_name):
    global data
    
    for host in host_name:
        data.add("host_name[]", host)
    
    for player_id in player_aliases:
        data.add("player_name[]", player_id)
        data.add("player_alias[]", "")
