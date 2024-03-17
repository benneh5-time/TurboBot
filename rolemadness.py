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
    "69":"Village Inventor",
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
    "21":"Wolf Watcher",
    "32":"Wolf Arsonist",
    "35":"Wolf Firefighter",
    "36":"Wolf Framer",
    "40":"Wolf Jack of All Trades",
    "42":"Wolf Universal Backup",
    "49":"Wolf Suicide Bomber",
    "51":"Wolf Poisoner",
    "68":"Wolf Fruit Vendor",
    "74":"Wolf Redirector",
    "76":"Wolf Power Role Killer"
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
    "faction_color":"#339933"
}

wolf_abilities = {
    "Wolf Doctor": {
        # Define abilities for Wolf Doctor here...
    },
    # Define abilities for other wolf roles here...
}

village_ability_weights = {
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
            0: 10,
            1: 20,
            2: 30,
            3: 40
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
    }
}