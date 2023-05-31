import requests
import hashlib
import re
from urllib3._collections import HTTPHeaderDict
import uuid
import json
from roles import vanilla_town_dict, mafia_goon_dict, joat_dict, cop_dict, vig_dict, big_ham_dict, frankie_dict, vanchilla_dict, vinnie_dict, zippy_dict, kingpin_dict
from bs4 import BeautifulSoup
from flavor import joat_flavor, cop9_flavor, cop13_flavor, vig_flavor

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

def post_thread(session, game_title, security_token, setup):

    protected_url = "https://www.mafiauniverse.com/forums/newthread.php"
    if setup == "joat10":
        game_flavor = joat_flavor
    if setup == "cop9":
        game_flavor = cop9_flavor
    if setup == "cop13":
        game_flavor = cop13_flavor
    if setup == "vig10":
        game_flavor = vig_flavor
        
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
        

def start_game(session, security_token, game_title, thread_id, player_aliases, game_setup, host_name):
    global data
    data = HTTPHeaderDict({'s': '', 'securitytoken': security_token, 'submit': '1', 'do': 'newgame', 'automated': '0', 'automation_setting': '2', 'game_name': game_title, 'thread_id': thread_id, 'speed_type': '1', 'game_type': 'Open', 'period': 'day', 'phase': '1', 'phase_end': '', 'started': '1', 'start_date': '', 'votecount_interval': '0', 'votecount_units': 'minutes', 'speed_preset': 'custom', 'day_length': '14', 'day_units': 'minutes', 'night_length': '3', 'night_units': 'minutes', 'itas_enabled': '0', 'default_ita_hit': '15', 'default_ita_count': '1', 'ita_immune_policy': '0', 'aliased': '0', 'alias_pool': 'Greek_Alphabet', 'daily_post_limit': '0', 'postlimit_cutoff': '0', 'postlimit_cutoff_units': 'hours', 'character_limit': '0', 'proxy_voting': '0', 'tied_lynch': '1', 'self_voting': '0', 'no_lynch': '1', 'announce_lylo': '1', 'votes_locked': '1', 'votes_locked_manual': '0', 'auto_majority': '2', 'maj_delay': '0', 'show_flips': '0', 'suppress_rolepms': '0', 'suppress_phasestart': '0', 'day_action_cutoff': '2', 'mafia_kill_enabled': '1', 'mafia_kill_type': 'kill', 'detailed_flips': '0', 'backup_inheritance': '0', 'mafia_win_con': '1', 'mafia_kill_assigned': '1', 'mafia_day_chat': '1', 'characters_enabled': '2', 'role_quantity': '1'})
    num_hosts = len(host_name)
    data.add('num_hosts', num_hosts)

    if game_setup == "joat10":
        add_joat_roles(game_title)
        data.add("preset", "custom")
        data.add('num_players', '10')
        data.add('roles_dropdown', '39')
    if game_setup == "vig10":
        add_vig_roles(game_title)
        data.add("preset", "vig-10") 
        data.add('num_players', '10')
    if game_setup == "cop9":
        add_cop9_roles(game_title)
        data.add("preset", "cop-9")
        data.add('num_players', '9')
        data.add('n0_peeks', '1')
    if game_setup == "cop13":
        add_cop13_roles(game_title)
        data.add("preset", "cop-13")
        data.add('num_players', '13')
        data.add('n0_peeks', '1')
        
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
	
def add_joat_roles(game_title):
    vanilla_town_json = json.dumps(vanchilla_dict)
    big_ham_json = json.dumps(big_ham_dict)
    frankie_json = json.dumps(frankie_dict)	
    joat_json = json.dumps(zippy_dict)	
    global data
    
    for i in range(0,7):
        data.add("roles[]", vanilla_town_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Town[/COLOR][/B]. You win when all threats to Town have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    
    data.add("roles[]", joat_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Town Jack of All Trades (x1 Alignment Cop, x1 Doctor, x1 Vigilante)[/COLOR][/B]. You win when all threats to Town have been eliminated.\n\n[SIZE=4][B][I]Town Jack Of All Trades[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Town Jack Of All Trades[/COLOR][/B], you have access to one or more miscellaneous night actions.\n\n[SIZE=4][B][I]x1 Alignment Cop[/I][/B][/SIZE]\n\nYou have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Doctor[/I][/B][/SIZE]\n\nYou have access to the [B]Protection[/B] Night Action. Protection will protect your target from being killed. You will not learn whether you successfully protected someone. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\n[SIZE=4][B][I]x1 Vigilante[/I][/B][/SIZE]\n\nYou have access to the [B]Shoot[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nSubmit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that day. Keep in mind that if you have multiple uses of your abilities, you must cycle through all of them before being allowed to reuse any of them.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")       
    data.add("roles[]", frankie_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    
    data.add("roles[]", big_ham_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")

def add_vig_roles(game_title):
    vanilla_town_json = json.dumps(vanchilla_dict)
    vinnie_json = json.dumps(vinnie_dict)
    kingpin_json = json.dumps(kingpin_dict)		
    vig_json = json.dumps(vig_dict)	
    global data
    
    for i in range(0,7):
        data.add("roles[]", vanilla_town_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Town[/COLOR][/B]. You win when all threats to Town have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    data.add("roles[]", vig_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Town Vigilante[/COLOR][/B]. You win when all threats to Town have been eliminated.\n\n[SIZE=4][B][I]Town Vigilante[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Town Vigilante[/COLOR][/B], you have access to the [B]Shoot[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, you will forego your action on that night.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")        
    data.add("roles[]", vinnie_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    
    data.add("roles[]", kingpin_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")

def add_cop9_roles(game_title):
    vanilla_town_json = json.dumps(vanchilla_dict)
    big_ham_json = json.dumps(big_ham_dict)
    frankie_json = json.dumps(frankie_dict)	
    cop_json = json.dumps(cop_dict)	
    global data
    
    for i in range(0,6):
        data.add("roles[]", vanilla_town_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Town[/COLOR][/B]. You win when all threats to Town have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    data.add("roles[]", cop_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Town Alignment Cop[/COLOR][/B]. You win when all threats to Town have been eliminated.\n\n[SIZE=4][B][I]Town Alignment Cop[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Town Alignment Cop[/COLOR][/B], you have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, a player will be picked at random from the un-Inspected living players.{{HIDE_FROM_FLIP}}\n\n{{NIGHT_0_PEEKS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
     
    data.add("roles[]", frankie_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    
    data.add("roles[]", big_ham_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")

def add_cop13_roles(game_title):
    vanilla_town_json = json.dumps(vanchilla_dict)
    big_ham_json = json.dumps(big_ham_dict)
    frankie_json = json.dumps(frankie_dict)	
    kingpin_json = json.dumps(kingpin_dict)	
    cop_json = json.dumps(cop_dict)	
    global data
    
    for i in range(0,9):
        data.add("roles[]", vanilla_town_json)
        data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Vanilla Town[/COLOR][/B]. You win when all threats to Town have been eliminated.{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    data.add("roles[]", cop_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\n\nYou are [B][COLOR=#339933]Town Alignment Cop[/COLOR][/B]. You win when all threats to Town have been eliminated.\n\n[SIZE=4][B][I]Town Alignment Cop[/I][/B][/SIZE]\n\nAs [B][COLOR=#339933]Town Alignment Cop[/COLOR][/B], you have access to the [B]Alignment Inspection[/B] Night Action. Alignment Inspection will reveal a target's alignment. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\n\nIf you do not submit an action, a player will be picked at random from the un-Inspected living players.{{HIDE_FROM_FLIP}}\n\n{{NIGHT_0_PEEKS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}{{HIDE_FROM_FLIP}}\n\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
     
    data.add("roles[]", frankie_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    
    data.add("roles[]", big_ham_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")
    data.add("roles[]", kingpin_json)
    data.add("role_pms[]", f"[CENTER][TITLE]Role PM for {game_title}[/TITLE][/CENTER]\nYou are [B][COLOR=#ff2244]Mafia Goon[/COLOR][/B]. You win when you overpower the Town and are the only evil faction remaining.{{HIDE_FROM_FLIP}} Your teammates are:\n[SIZE=4][B][I]Mafia Team[/I][/B][/SIZE]\n{{TEAM_MEMBERS_GENERATED_DURING_RAND}}{{/HIDE_FROM_FLIP}}\nAs [B][COLOR=#ff2244]Mafia[/COLOR][/B], you have access to the [B]Factional Night Kill[/B] Night Action. Players targeted with this action will die at the end of the Night unless protected. Submit your Night Action each night using the form below the game thread. You may change your target as many times as you want. The last action submitted will be used.\nIf no Mafia submit an action, a player will be picked at random from the living non-Mafia players.{{HIDE_FROM_FLIP}}\n{{ROLE_PM_FOOTER_LINKS}}{{/HIDE_FROM_FLIP}}")    

def add_players(player_aliases, host_name):
	global data
	
    for host in host_name:
    	data.add("host_name[]", host)
	
	for player_id in player_aliases:
		data.add("player_name[]", player_id)
		data.add("player_alias[]", "")