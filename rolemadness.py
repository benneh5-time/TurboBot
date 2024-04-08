import random

village_roles = {
    "1":"Vanilla Villager",
    "4":"Village Doctor",
    "6":"Village Miller",
    "10":"Village Vigilante",
    "12":"Village Roleblocker",
    "14":"Village Jailkeeper",
    "16":"Village Bodyguard",
    "18":"Village Tracker",
    "27":"Village Innocent Child",
    "41":"Village Universal Backup",
    "39":"Village Jack of All Trades",
    "46":"Village Parity Cop",
    "50":"Village Poisoner",
    "52":"Village Healer",
    "64":"Village Night Desperado",
    "67":"Village Fruit Vendor"
}

wolf_roles = {
    "5":"Wolf Doctor",
    "7":"Wolf Godfather",
    "9":"Wolf Role Cop",
    "11":"Wolf Vigilante",
    "13":"Wolf Roleblocker",
    "15":"Wolf Jailkeeper",
    "19":"Wolf Tracker",
    "36":"Wolf Framer",
    "40":"Wolf Jack of All Trades",
    "42":"Wolf Universal Backup",
    "49":"Wolf Suicide Bomber",
    "51":"Wolf Poisoner",
    "74":"Wolf Redirector",
    "76":"Wolf Power Role Killer"
}

v_joat_abilities = {
    "faction":"",
    "bpv_status":0,
    "ninja":0,
    "x_shot_limit":0,
    "strongman":0,
    "janitor":0,
    "even_night":0,
    "odd_night":0,
    "godfather":0,
    "backup":0,
    "night_x":0,
    "macho":0,
    "recluse":0,
    "lost":0,
    "vengeful":0,
    "flipless":0,
    "alignment_flip":0,
    "vote_weight":0,
    "hide_vote_weight":0,
    "non_consecutive":0,
    "self_targetable":0,
    "treestump":0,
    "neighbor":0,
    "mason":0,
    "lover":0,
    "loyal":0,
    "disloyal":0,
    "uncooperative":0,
    "blocked":0,
    "compulsive":0,
    "vendor_items":"",
    "joat":0,
    "inventor":0,
    "disable_in_endgame":0,
    "powers":{
        "alignment+inspection":1,
        "protection":1,
        "roleblock":0,
        "kill":1
        },
    "ita_count":0,
    "ita_base_hit":0,
    "ita_immunity":0,
    "ita_vulnerability":0,
    "ita_shield_status":0,
    "ita_booster":0,
    "ita_nerfer":0,
    "alignment":"village",
    "faction_color":"#339933"
}

w_joat_abilities = {
    "faction":"",
    "bpv_status":0,
    "ninja":0,
    "x_shot_limit":0,
    "strongman":0,
    "janitor":0,
    "even_night":0,
    "odd_night":0,
    "godfather":0,
    "backup":0,
    "night_x":0,
    "macho":0,
    "recluse":0,
    "lost":0,
    "vengeful":0,
    "flipless":0,
    "alignment_flip":0,
    "vote_weight":0,
    "hide_vote_weight":0,
    "non_consecutive":0,
    "self_targetable":0,
    "treestump":0,
    "neighbor":0,
    "mason":0,
    "lover":0,
    "loyal":0,
    "disloyal":0,
    "uncooperative":0,
    "blocked":0,
    "compulsive":0,
    "vendor_items":"",
    "joat":0,
    "inventor":0,
    "disable_in_endgame":0,
    "powers":{
        "rolecop":1,
        "protection":1,
        "roleblock":0,
        "watch": 1
        },
    "ita_count":0,
    "ita_base_hit":0,
    "ita_immunity":0,
    "ita_vulnerability":0,
    "ita_shield_status":0,
    "ita_booster":0,
    "ita_nerfer":0,
    "alignment":"wolves",
    "faction_color":"#ff2244"
}

village_abilities = {
    "faction":"",
    "bpv_status":0,
    "ninja":0,
    "x_shot_limit":0,
    "strongman":0,
    "janitor":0,
    "even_night":0,
    "odd_night":0,
    "godfather":0,
    "backup":0,
    "night_x":0,
    "macho":0,
    "recluse":0,
    "lost":0,
    "vengeful":0,
    "flipless":0,
    "alignment_flip":0,
    "vote_weight":0,
    "hide_vote_weight":0,
    "non_consecutive":0,
    "self_targetable":0,
    "treestump":0,
    "neighbor":0,
    "mason":0,
    "lover":0,
    "loyal":0,
    "disloyal":0,
    "uncooperative":0,
    "blocked":0,
    "compulsive":0,
    "vendor_items":"",
    "joat":0,
    "inventor":0,
    "disable_in_endgame":0,
    "powers":{
        "alignment+inspection":0,
        "protection":0,
        "roleblock":0,
        "kill":0
        },
    "ita_count":0,
    "ita_base_hit":0,
    "ita_immunity":0,
    "ita_vulnerability":0,
    "ita_shield_status":0,
    "ita_booster":0,
    "ita_nerfer":0,
    "alignment":"village",
    "faction_color":"#339933",
    "character_name": "",
    "character_image": ""
}

wolf_abilities = {
    "faction":"",
    "bpv_status":0,
    "ninja":0,
    "x_shot_limit":0,
    "strongman":0,
    "janitor":0,
    "even_night":0,
    "odd_night":0,
    "godfather":0,
    "backup":0,
    "night_x":0,
    "macho":0,
    "recluse":0,
    "lost":0,
    "vengeful":0,
    "flipless":0,
    "alignment_flip":0,
    "vote_weight":0,
    "hide_vote_weight":0,
    "non_consecutive":0,
    "self_targetable":0,
    "treestump":0,
    "neighbor":0,
    "mason":0,
    "lover":0,
    "loyal":0,
    "disloyal":0,
    "uncooperative":0,
    "blocked":0,
    "compulsive":0,
    "vendor_items":"",
    "joat":0,
    "inventor":0,
    "disable_in_endgame":0,
    "powers":{
        "alignment+inspection":0,
        "protection":0,
        "roleblock":0,
        "kill":0
        },
    "ita_count":0,
    "ita_base_hit":0,
    "ita_immunity":0,
    "ita_vulnerability":0,
    "ita_shield_status":0,
    "ita_booster":0,
    "ita_nerfer":0,
    "alignment":"wolves",
    "faction_color":"#ff2244",
    "character_name": "",
    "character_image": ""
}

village_ability_weights = {
    "Vanilla Villager": {
        "treestump": 1
    },
    "Village Doctor": {
        "even_night": 30,
        "odd_night": 30,
        "compulsive": 20,
        "night_x": {
            1: 20,
            2: 40,
            3: 40
        },
        "x_shot_limit": {
            0: 20,
            1: 20,
            2: 30,
            3: 30
        }
    },
    "Village Miller": {
        "bpv": 20
    },
    "Village Roleblocker": {
        "even_night": 40,
        "odd_night": 40,
        "self_targetable": 20,
        "non-consecutive": 100
    },
    "Village Jailkeeper": {
        "even_night": 40,
        "odd_night": 40,
        "self_targetable": 20,
        "loyal": 10,
        "disloyal": 10,
        "non-consecutive": 100
    },
    "Village Bodyguard": {
        "even_night": 50,
        "odd_night": 50
    },
    "Village Tracker": {
        "even_night": 20,
        "odd_night": 20,
        "x_shot_limit": {
            0: 10, 
            1: 20, 
            2: 30,
            3: 30
            },
        "loyal": 10,
        "self-targetable": 10
        },
    "Village Parity Cop": {
            "odd_night": 80,
            "even_night": 20,
            "macho": 50
        },
    "Village Innocent Child": {
        "night_x": {
            0: 10,
            1: 10,
            2: 15,
            3: 40,
            4: 10, 
            "3+": 5
            },
        "vengeful": 8,
        "flipless": 15,
        "treestump": 5
        },
    "Village Fruit Vendor": {
        "odd_night": 20,
        "even_night": 20,
        "loyal": 20,
        "disloyal": 20,
        "compulsive": 30,
        "vendor_items": "['boob1', 'boob2', 'thread pull']"
        },
    "Village Universal Backup": {
        "vote_weight": {
            2: 50,
            .5: 10,
            0: 40
            }
        },
    "Village Poisoner": {
        "ninja": 30,
        "odd_night": 10,
        "even_night": 10,
        "x_shot_limit": {
            0: 10,
            1: 20,
            2: 30,
            3: 40
            },
        "loyal": 10,
        "disloyal": 10,
        "macho": 10,
        "compulsive": 25
        },
    "Village Healer": {
        "x_shot_limit": {
            0: 10,
            1: 70,
            2: 10,
            3: 10
            },
        "loyal": 10
        },
    "Village Night Desperado": {
        "odd_night": 30,
        "even_night": 30,
        "loyal": 10,
        "macho": 10,
        "flipless": 10,
        "treestump": 10
        },
    "Village Parity Cop": {
        "macho": 25,
        "self-targetable": 15
        },
    "Village Vigilante": {
        "even_night": 30,
        "odd_night": 30,
        "compulsive": 20,
        "night_x": {
            1: 20,
            2: 40,
            3: 40
            },
        "x_shot_limit": {
            0: 20,
            1: 20,
            2: 30,
            3: 30
            }
        },
    "Village Jack of All Trades": {
        "x_shot_limit": {
            0: 10,
            1: 50,
            2: 40
        }
    }
}

wolf_ability_weights = {
    "Wolf Doctor": {
        "even_night": 30,
        "odd_night": 30,
        "compulsive": 20,
        "night_x": {
            1: 20,
            2: 40,
            3: 40
        },
        "x_shot_limit": {
            0: 20,
            1: 20,
            2: 30,
            3: 30
        }
    },
    "Wolf Godfather": {
        "flipless": 20
    },
    "Wolf Role Cop": {
            "odd_night": 20,
            "even_night": 20,
        },
    "Wolf Vigilante": {
        "even_night": 30,
        "odd_night": 30,
        "compulsive": 20,
        "night_x": {
            1: 20,
            2: 40,
            3: 40
            },
        "x_shot_limit": {
            0: 20,
            1: 20,
            2: 30,
            3: 30
            },
        "strongarm": 30
        },

    "Wolf Roleblocker": {
        "even_night": 40,
        "odd_night": 40,
        "self_targetable": 20,
        "non-consecutive": 100
    },
    "Wolf Jailkeeper": {
        "even_night": 40,
        "odd_night": 40,
        "self_targetable": 20,
        "loyal": 10,
        "disloyal": 10,
        "non-consecutive": 100
    },
    "Wolf Tracker": {
        "even_night": 20,
        "odd_night": 20,
        "x_shot_limit": {
            0: 10, 
            1: 20, 
            2: 30,
            3: 30
            },
        "loyal": 10,
        "self-targetable": 10
        },

    "Wolf Framer": {
        "night_x": {
            0: 10,
            1: 10,
            2: 15,
            3: 40,
            4: 10, 
            "3+": 5
            },
        "vote_weight": {
            2: 20,
            1: 80
        }
        },
    "Wolf Jack of All Trades": {
        "x_shot_limit": {
            0: 10,
            1: 50,
            2: 40
        }
    },
    "Wolf Universal Backup": {
        "vote_weight": {
            2: 50,
            .5: 10,
            0: 40
            }
        },
    "Wolf Suicide Bomber": {
        "lost": 30,
        "recluse": 30
        },
        
    "Wolf Poisoner": {
        "ninja": 30,
        "odd_night": 10,
        "even_night": 10,
        "x_shot_limit": {
            0: 10,
            1: 20,
            2: 30,
            3: 40
            },
        },

    "Wolf Redirector": {
        "odd_night": 30,
        "even_night": 30,
        "treestump": 10,
        "x_shot_limit": {
            1: 80,
            2: 20
        }
        },
    "Wolf Power Role Killer": {
        "loyal": 15
        }
}

def choose_role_and_ability(alignment):
    # Randomly select a role
    if alignment == "village":
        role = random.choice(list(village_roles.values()))
        abilities = village_ability_weights.get(role, {})
    
    else: 
        role = random.choice(list(wolf_roles.values()))
        abilities = wolf_ability_weights.get(role, {})
    
    selected_abilities = {}
    for ability, weights in abilities.items():
        if isinstance(weights, dict):  # Handling nested weights (like night_x, x_shot_limit)
            selected_abilities[ability] = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]
        else:
            selected_abilities[ability] = int(random.choices([0, 1], weights=[100 - weights, weights], k=1)[0])

    return role, selected_abilities

def create_role_data(alignment):
    selected_role, selected_abilities = choose_role_and_ability(alignment)

    if alignment == "village":
        selected_role_number = next(key for key, val in village_roles.items() if val == selected_role)
        if selected_role == "Village Jack of All Trades":
            role_data = v_joat_abilities.copy()
            role_data.update(selected_abilities)
            role_data['role_name'] = selected_role
            role_data['role_number'] = selected_role_number
        else:
            role_data = village_abilities.copy()
            role_data.update(selected_abilities)
            role_data['role_name'] = selected_role
            role_data['role_number'] = selected_role_number
    else:
        selected_role_number = next(key for key, val in wolf_roles.items() if val == selected_role)
        if selected_role == "Wolf Jack of All Trades": 
            role_data = w_joat_abilities.copy()
            role_data.update(selected_abilities)
            role_data['role_name'] = selected_role
            role_data['role_number'] = selected_role_number
        else:
            role_data = wolf_abilities.copy()
            role_data.update(selected_abilities)
            role_data['role_name'] = selected_role
            role_data['role_number'] = selected_role_number
    return role_data
