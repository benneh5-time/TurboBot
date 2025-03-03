import pandas as pd
from collections import defaultdict
import math
import json
import gspread
from google.oauth2.service_account import Credentials

non_elo_setups = ['inno4', 'ita10', 'ita13', 'randommadnessXer']
opt_out_players = {"178647349369765888", "851954038068478002", "932116336568578069"}

class EloCalculator:
    def __init__(self, credentials_path, aliases_file, initial_elo=1000):
        self.initial_elo = initial_elo
        self.aliases = self._load_aliases(aliases_file)
        self.credentials = self._authorize(credentials_path)
        self.elo_scores = defaultdict(lambda: {'Town': self.initial_elo, 'Wolf': self.initial_elo})
        self.game_counts = defaultdict(lambda: {'Town': 0, 'Wolf': 0})

    def _load_aliases(self, aliases_file):
        with open(aliases_file, 'r') as f:
            return json.load(f)

    def _authorize(self, credentials_path):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        return Credentials.from_service_account_file(credentials_path, scopes=scopes)

    def get_active_alias(self, player_name):
        """Get the active alias for a player."""
        player_name_lower = player_name.lower()
        for discord_id, data in self.aliases.items():
            if player_name_lower in [alias.lower() for alias in data['all']]:
                return data['active']
        return player_name

    def calculate_dynamic_k(self, games_played):
        if games_played <= 20:
            return 32
        elif games_played <= 50:
            return 28
        elif games_played <= 100:
            return 24
        else:
            return 20

    def calculate_elo_with_team_impact(self, player_elo, team_elo, result, role, games_played, setup):
        k = self.calculate_dynamic_k(games_played)
        expected_score = 1 / (1 + 10 ** ((team_elo - player_elo) / 400))

        setup_multipliers = {
            "joat10": {"town": 57.32, "mafia": 42.68},
            "vig10": {"town": 50.77, "mafia": 49.23},
            "bomb10": {"town": 45.30, "mafia": 54.7},
            "closedrandomXer": {"town": 45.93, "mafia": 54.07},
            "cop9": {"town": 52.5, "mafia": 47.5},
            "default": {"town": 53.23, "mafia": 46.63},
        }
        if setup not in setup_multipliers:
            town_multiplier = 53.23
            mafia_multiplier = 46.63
        else:
            town_multiplier = setup_multipliers[setup]['town']
            mafia_multiplier = setup_multipliers[setup]['mafia']
            
        if role == "town":
            expected_score *= (50 / town_multiplier)
            #expected_score *= 1 + (50 / town_multiplier)
        elif role == "mafia":
            expected_score *= (50 / mafia_multiplier)
            #expected_score *= 1 + (50 / mafia_multiplier)
        return player_elo + k * (result - max(0, min(1, expected_score)))

    def process_game_data(self, df):
        for _, row in df.iterrows():
            if row['Setup'] in non_elo_setups:
                continue
                
            winning_alignment = row['Winning Alignment']
            villagers = row['Villagers']
            wolves = row['Wolves']
            town_elo = sum(self.elo_scores[self.get_active_alias(v)]['Town'] for v in villagers) / len(villagers)
            wolf_elo = sum(self.elo_scores[self.get_active_alias(w)]['Wolf'] for w in wolves) / len(wolves)
            print(f"{row['Turbo Title']} -- Wolf ELO: {wolf_elo}, Town ELO: {town_elo}")
            for villager in villagers:
                active_villager = self.get_active_alias(villager)
                self.game_counts[active_villager]['Town'] += 1
                result = 1 if winning_alignment == 'Town' else 0
                self.elo_scores[active_villager]['Town'] = self.calculate_elo_with_team_impact(
                    self.elo_scores[active_villager]['Town'], wolf_elo, result, 'town', self.game_counts[active_villager]['Town'], row['Setup']
                )
            for wolf in wolves:
                active_wolf = self.get_active_alias(wolf)
                self.game_counts[active_wolf]['Wolf'] += 1
                result = 0 if winning_alignment == 'Town' else 1
                self.elo_scores[active_wolf]['Wolf'] = self.calculate_elo_with_team_impact(
                    self.elo_scores[active_wolf]['Wolf'], town_elo, result, 'mafia', self.game_counts[active_wolf]['Wolf'], row['Setup']
                )

    def export_to_google_sheets(self, spreadsheet_name, sheet_name, data):
        client = gspread.authorize(self.credentials)
        try:
            spreadsheet = client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            spreadsheet = client.open(spreadsheet_name)
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        worksheet.update("A1", data)

    def calculate_and_export(self, df, spreadsheet_name, sheet_name, min_games = 25):
        self.process_game_data(df)
        result_data = [
            {
                'Name': player,
                'Town ELO': 0 if self.game_counts[player]['Town'] == 0 else round(scores['Town'], 2),
                'Wolf ELO': 0 if self.game_counts[player]['Wolf'] == 0 else round(scores['Wolf'], 2),
                'Overall ELO': (
                    (0 if self.game_counts[player]['Town'] == 0 else scores['Town']) + 
                    (0 if self.game_counts[player]['Wolf'] == 0 else scores['Wolf'])
                ),  # Sum of adjusted Town and Wolf ELO
                'Town games': self.game_counts[player]['Town'],
                'Wolf games': self.game_counts[player]['Wolf'],
                'Games Played': self.game_counts[player]['Town'] + self.game_counts[player]['Wolf']
            }
            for player, scores in self.elo_scores.items()
            if self.game_counts[player]['Town'] + self.game_counts[player]['Wolf'] >= min_games  # Include players with at least one game played
        ]
        result_df = pd.DataFrame(result_data).sort_values(by='Overall ELO', ascending=False)
        sheet_data = [result_df.columns.tolist()] + result_df.values.tolist()
        self.export_to_google_sheets(spreadsheet_name, sheet_name, sheet_data)
        
    def get_discord_id(self, player_name):
        """Get the Discord ID for a player based on their alias."""
        player_name_lower = player_name.lower()
        for discord_id, data in self.aliases.items():
            if player_name_lower in [alias.lower() for alias in data['all']]:
                return discord_id  # Return Discord ID
        return None  # Return None if not found
    
    def calculate_and_export_champs(self, df, spreadsheet_name, sheet_name, town_sheet_name, wolf_sheet_name, min_games = 25):
        self.process_game_data(df)
        result_data = [
            {
                'Name': player,
                'Town ELO': 0 if self.game_counts[player]['Town'] == 0 else round(scores['Town'], 2),
                'Wolf ELO': 0 if self.game_counts[player]['Wolf'] == 0 else round(scores['Wolf'], 2),
                'Overall ELO': (
                    (0 if self.game_counts[player]['Town'] == 0 else scores['Town']) + 
                    (0 if self.game_counts[player]['Wolf'] == 0 else scores['Wolf'])
                ),  # Sum of adjusted Town and Wolf ELO
                'Town games': self.game_counts[player]['Town'],
                'Wolf games': self.game_counts[player]['Wolf'],
                'Games Played': self.game_counts[player]['Town'] + self.game_counts[player]['Wolf']
            }
            for player, scores in self.elo_scores.items()
            if self.game_counts[player]['Town'] + self.game_counts[player]['Wolf'] >= min_games
            and (self.get_discord_id(player) not in opt_out_players) # Include players with at least one game played
        ]
        result_df = pd.DataFrame(result_data).sort_values(by='Overall ELO', ascending=False)
        sheet_data = [result_df.columns.tolist()] + result_df.values.tolist()
        self.export_to_google_sheets(spreadsheet_name, sheet_name, sheet_data)
        
        town_result_df = pd.DataFrame(result_data).sort_values(by='Town ELO', ascending=False)
        town_sheet_data = [town_result_df.columns.tolist()] + town_result_df.values.tolist()
        self.export_to_google_sheets(spreadsheet_name, town_sheet_name, town_sheet_data)        
        
        wolf_result_df = pd.DataFrame(result_data).sort_values(by='Wolf ELO', ascending=False)
        wolf_sheet_data = [wolf_result_df.columns.tolist()] + wolf_result_df.values.tolist()
        self.export_to_google_sheets(spreadsheet_name, wolf_sheet_name, wolf_sheet_data)


