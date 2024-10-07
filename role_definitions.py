# role_definitions.py

import random

"""
# Village Roles
village_roles = [
    # Role ID    Role Name              
    3           Village Alignment Cop   
    4           Village Doctor          
    10          Village Vigilante       
    12          Village Roleblocker     
    14          Village Jailkeeper      
    18          Village Tracker         
    27          Village Innocent Child  
    31          Village Arsonist        
    37          Village Day Vigilante   
    39          Village Jack of All Trades
    43          Village Alignment Oracle
    46          Village Parity Cop      
    50          Village Poisoner             
    54          Village Motion Detector 
    63          Village Day Desperado   
    64          Village Night Desperado 
    67          Village Fruit Vendor       
    69          Village Inventor           
]

# Mafia Roles
mafia_roles = [
    # Role ID    Role Name              
    9           Wolf Role Cop           
    11          Wolf Vigilante          
    13          Wolf Roleblocker        
    15          Wolf Jailkeeper 
    21          Wolf Watcher        
    32          Wolf Arsonist           
    38          Wolf Day Vigilante      
    40          Wolf Jack of All Trades 
    42          Wolf Universal Backup   
    51          Wolf Poisoner
    59          Wolf Treestump
    68          Wolf Fruit Vendor
    70          Wolf Inventor           
    76          Wolf PR Killer

]

# Note: Some roles appear multiple times. Adjust for uniqueness as needed.
"""
# Define possible values for each key
possible_roles = {
    "Wolf": [9, 11, 13, 15, 21, 32, 38, 40, 42, 51, 59, 68, 70, 76],  # Possible base roles for Wolf
    "Village": [3, 4, 10, 12, 14, 18, 27, 31, 37, 39, 43, 46, 50, 54, 63, 64, 67, 69] # Possible base roles for Village
}
possible_values = {
    "bpv_status": [0, 1],
    "ninja": [0, 1],
    "x_shot_limit": [0, 1, 2],
    "strongman": [0, 1],
    "godfather": [0, 1],
    "backup": [0, 1],
    "macho": [0, 1],
    "recluse": [0, 1],
    "lost": [0, 1],
    "vengeful": [0, 1],
    "flipless": [0, 1],
    #"vote_weight": [0, 1],
    #"hide_vote_weight": [0, 1],
    "non_consecutive": [0, 1],
    "self_targetable": [0, 1],
    "treestump": [0, 1],
    #"neighbor": [0, 1],
    #"mason": [0, 1],
    #"lover": [0, 1],
    "loyal": [0, 1],
    "disloyal": [0, 1],
    "uncooperative": [0, 1],
    "vendor_items": ["item1", "item2"],
    "joat": [0, 1],
    "inventor": [0, 1]
}

# Define possible values for each power
possible_utility_powers = {
    "alignment inspection": [0, 1, 2],
    "fullcop": [0, 1, 2],
    "rolecop": [0, 1, 2],
    "neapolitan": [0, 1, 2],
    "vanilla cop": [0, 1, 2],
    "bodyguard": [0, 1, 2],
    "protection": [0, 1, 2],
    "fire protection": [0, 1, 2],
    "frame": [0, 1, 2],
    "jail": [0, 1, 2],
    "roleblock": [0, 1, 2],
    "redirect": [0, 1, 2],
    "empower": [0, 1, 2],
    "track": [0, 1, 2],
    "watch": [0, 1, 2],
    "motion detect": [0, 1, 2],
    "voyeur": [0, 1, 2],
    "heal": [0, 1, 2]
}

possible_kill_powers = {
    "kill": [0, 1, 2],
    "daykill": [0, 1, 2],
    "desperado": [0, 1, 2],
    "day desperado": [0, 1, 2],
    "bomb": [0, 1, 2],
    "poison": [0, 1, 2]
}

def get_static_values(faction):
    if faction == "Wolf":
        return {
            "faction": "Wolf",
            "alignment": "wolf",
            "faction_color": "#ff2244",
        }
    elif faction == "Village":
        return {
            "faction": "Village",
            "alignment": "village",
            "faction_color": "#00ff00",
        }
    else:
        raise ValueError("Invalid faction provided")

def randomize_night_restrictions():
    # Randomly decide what type of night restrictions to apply
    option = random.choice(["none", "even", "odd", "night_x"])

    if option == "none":
        return {
            "even_night": 0,
            "odd_night": 0,
            "night_x": 0  # No restrictions
        }
    elif option == "even":
        return {
            "even_night": 1,
            "odd_night": 0,
            "night_x": 0  # No night_x value
        }
    elif option == "odd":
        return {
            "even_night": 0,
            "odd_night": 1,
            "night_x": 0  # No night_x value
        }
    else:  # option == "night_x"
        night_x = random.choice([1, 2, 3, 4, 5, "2+"])  # Exclude 0 for night_x
        return {
            "even_night": 0,
            "odd_night": 0,
            "night_x": night_x
        }

def create_random_role(faction):
    # Choose the appropriate roles based on faction
    role_id = random.choice(possible_roles[faction])  # Randomly select a base role
    static_values = get_static_values(faction)  # Get static values based on faction

    role = {
        "role": str(role_id),
        **static_values,
    }

    # Randomize other values (up to 4)
    keys_to_modify = [key for key in possible_values.keys()]  # Get all keys from possible_values

    num_modifications = random.randint(1, 4)  # Choose how many values to modify (1 to 4)
    modifications = random.sample(keys_to_modify, min(num_modifications, len(keys_to_modify)))  # Select keys to modify

    for key in modifications:
        role[key] = random.choice(possible_values[key])
        
        
    if faction == "Wolf": 
        if role.get("inventor") != 1 and role.get("joat") != 1:
            for _ in range(2):
                if random.choice([True, False]):
                    if random.choice(["inventor", "joat"]) == "inventor":
                        role["inventor"] = 1
                    else:
                        role["joat"] = 1
                        
    # Randomize night restrictions
    night_restrictions = randomize_night_restrictions()
    role.update(night_restrictions)

    # Initialize powers
    role["powers"] = {}
    
    # Randomize utility powers
    if role.get("joat") == 1 or role.get("inventor") == 1 or role_id in [39, 40, 70]:
        num_utility_powers = random.randint(1, 3)  # Up to 3 utility powers
        utility_power_keys = list(possible_utility_powers.keys())
        selected_utilities = random.sample(utility_power_keys, min(num_utility_powers, len(utility_power_keys)))

        for power in selected_utilities:
            role["powers"][power] = random.choice(possible_utility_powers[power])

        # Add one kill power
        num_kill_powers = 3 - num_utility_powers
        kill_power_keys = list(possible_kill_powers.keys())
        selected_kill_powers = random.sample(kill_power_keys, min(num_kill_powers, len(kill_power_keys)))
        
        for power in selected_kill_powers:
            role["powers"][power] = random.choice(possible_kill_powers[power])

    return role

#faction_choice = "Village" 

#random_role = create_random_role(faction_choice)

#print(random_role)