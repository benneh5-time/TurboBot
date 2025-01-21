import csv
from collections import defaultdict

def calculate_player_win_rate(file_path, player_name, setup=None):
    # Create dictionaries to store total games and wins for the player
    total_games = {'Villager': 0, 'Wolf': 0}
    wins = {'Villager': 0, 'Wolf': 0}
    
    if setup:
        if setup.lower() == 'alexa role madness':
            setup = 'Alexa Role Madness'

    # Read the CSV file
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if setup and row['Setup'] != setup:
                continue  # Skip rows that don't match the specified setup

            winning_alignment = row['Winning Alignment']
            villagers = [v.lower() for v in eval(row['Villagers'])]  # Convert string list to actual list
            wolves = [w.lower() for w in eval(row['Wolves'])]

            # Check if the player participated as a Villager
            if player_name in villagers:
                total_games['Villager'] += 1
                if winning_alignment == 'Town':
                    wins['Villager'] += 1

            # Check if the player participated as a Wolf
            if player_name in wolves:
                total_games['Wolf'] += 1
                if winning_alignment == 'Mafia':
                    wins['Wolf'] += 1

    # Calculate win rates
    villager_win_rate = (wins['Villager'] / total_games['Villager'] * 100) if total_games['Villager'] > 0 else 0
    wolf_win_rate = (wins['Wolf'] / total_games['Wolf'] * 100) if total_games['Wolf'] > 0 else 0
    total_wins = sum(wins.values())
    total_games_played = sum(total_games.values())
    overall_win_rate = (total_wins / total_games_played * 100) if total_games_played > 0 else 0

    # Return the player's win rates
    return {
        'Player': player_name,
        'Setup': setup or 'All Setups',
        'Villager Win Rate': villager_win_rate,
        'Villager Games': total_games['Villager'],
        'Villager Wins': wins['Villager'],
        'Wolf Win Rate': wolf_win_rate,
        'Wolf Games': total_games['Wolf'],
        'Wolf Wins': wins['Wolf'],
        'Total Wins': total_wins,
        'Total Games Played': total_games_played,
        'Overall Win Rate': overall_win_rate
    }

# Example usage
# file_path = 'game_database.csv'  # Replace with the path to your CSV file
# player_name = 'pinguREFORMED'  # Replace with the player's name you want to query
# setup = 'Setup Name'  # Replace with the setup name or None for all setups
# player_win_rate = calculate_player_win_rate(file_path, player_name, setup)

# Print the result
# print(f"{player_win_rate['Player']} ({player_win_rate['Setup']}):")
# print(f"  Villager Win Rate: {player_win_rate['Villager Win Rate']:.2f}%")
# print(f"  Wolf Win Rate: {player_win_rate['Wolf Win Rate']:.2f}%")
