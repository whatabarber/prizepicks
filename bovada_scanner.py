import requests
import json
import time
from datetime import datetime
import os

class BovadaScanner:
    def __init__(self):
        self.base_url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # ONLY FOOTBALL SPORTS
        self.sports = {
            'NFL': 'football',
            'CFB': 'college-football'
        }
        
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def fetch_sport_data(self, sport_name, sport_path):
        """Fetch live odds data for football only"""
        try:
            print(f"Fetching {sport_name} data from Bovada...")
            
            url = f"{self.base_url}{sport_path}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                games = self.parse_games(data, sport_name)
                return games
            else:
                print(f"Failed to fetch {sport_name}: Status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching {sport_name}: {str(e)}")
            return []

    def parse_games(self, data, sport_name):
        """Parse game data from Bovada response"""
        games = []
        
        try:
            if isinstance(data, list) and len(data) > 0:
                events = data[0].get('events', [])
            elif isinstance(data, dict):
                events = data.get('events', [])
            else:
                return games

            for event in events:
                try:
                    game_data = self.extract_game_info(event, sport_name)
                    if game_data:
                        games.append(game_data)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error parsing {sport_name} data: {str(e)}")
            
        return games

    def extract_game_info(self, event, sport_name):
        """Extract game information"""
        try:
            competitors = event.get('competitors', [])
            if len(competitors) < 2:
                return None
                
            team1 = competitors[0].get('name', 'Team 1')
            team2 = competitors[1].get('name', 'Team 2')
            
            game_time = event.get('startTime', '')
            event_id = event.get('id', '')
            
            # Get all odds types
            moneyline_odds = self.extract_moneyline(event)
            spread_odds = self.extract_spread(event)
            total_odds = self.extract_totals(event)
            
            game_info = {
                'id': event_id,
                'sport': sport_name,
                'team1': team1,
                'team2': team2,
                'game_time': game_time,
                'moneyline': moneyline_odds,
                'spread': spread_odds,
                'totals': total_odds,
                'timestamp': datetime.now().isoformat(),
                'source': 'Bovada'
            }
            
            return game_info
            
        except Exception as e:
            return None

    def extract_moneyline(self, event):
        """Extract moneyline odds"""
        try:
            display_groups = event.get('displayGroups', [])
            for group in display_groups:
                if group.get('description', '').lower() in ['moneyline', 'money line', 'match result']:
                    markets = group.get('markets', [])
                    for market in markets:
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            return {
                                'team1_odds': outcomes[0].get('price', {}).get('american', 'N/A'),
                                'team2_odds': outcomes[1].get('price', {}).get('american', 'N/A')
                            }
        except:
            pass
        return {'team1_odds': 'N/A', 'team2_odds': 'N/A'}

    def extract_spread(self, event):
        """Extract spread odds"""
        try:
            display_groups = event.get('displayGroups', [])
            for group in display_groups:
                if 'spread' in group.get('description', '').lower() or 'point spread' in group.get('description', '').lower():
                    markets = group.get('markets', [])
                    for market in markets:
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            return {
                                'team1_spread': outcomes[0].get('price', {}).get('handicap', 'N/A'),
                                'team1_odds': outcomes[0].get('price', {}).get('american', 'N/A'),
                                'team2_spread': outcomes[1].get('price', {}).get('handicap', 'N/A'), 
                                'team2_odds': outcomes[1].get('price', {}).get('american', 'N/A')
                            }
        except:
            pass
        return {'team1_spread': 'N/A', 'team1_odds': 'N/A', 'team2_spread': 'N/A', 'team2_odds': 'N/A'}

    def extract_totals(self, event):
        """Extract over/under totals"""
        try:
            display_groups = event.get('displayGroups', [])
            for group in display_groups:
                desc = group.get('description', '').lower()
                if 'total' in desc or 'over/under' in desc:
                    markets = group.get('markets', [])
                    for market in markets:
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            total_points = market.get('period', {}).get('main', {}).get('total', 'N/A')
                            return {
                                'total_points': total_points,
                                'over_odds': outcomes[0].get('price', {}).get('american', 'N/A'),
                                'under_odds': outcomes[1].get('price', {}).get('american', 'N/A')
                            }
        except:
            pass
        return {'total_points': 'N/A', 'over_odds': 'N/A', 'under_odds': 'N/A'}

    def scan_all_sports(self):
        """Scan ONLY football sports"""
        all_games = []
        
        print("Starting Football-Only Bovada scan...")
        
        for sport_name, sport_path in self.sports.items():
            games = self.fetch_sport_data(sport_name, sport_path)
            all_games.extend(games)
            print(f"{sport_name}: Found {len(games)} games")
            time.sleep(1)
            
        # Save to JSON
        output_file = os.path.join(self.data_dir, 'bovada_games.json')
        with open(output_file, 'w') as f:
            json.dump(all_games, f, indent=2)
            
        print(f"Saved {len(all_games)} total FOOTBALL games to {output_file}")
        return all_games

    def format_for_discord(self, games):
        """Format games data for Discord alerts"""
        if not games:
            return "No live football games found on Bovada"
            
        message = f"BOVADA FOOTBALL ODDS UPDATE\n"
        message += f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        
        # Group by sport
        sports_games = {}
        for game in games:
            sport = game['sport']
            if sport not in sports_games:
                sports_games[sport] = []
            sports_games[sport].append(game)
            
        for sport, sport_games in sports_games.items():
            message += f"**{sport}** ({len(sport_games)} games)\n"
            
            for game in sport_games:
                team1 = game['team1']
                team2 = game['team2']
                
                message += f"{team1} vs {team2}\n"
                
                # Show available odds
                ml = game['moneyline']
                if ml['team1_odds'] != 'N/A':
                    message += f"ML: {team1} ({ml['team1_odds']}) | {team2} ({ml['team2_odds']})\n"
                
                spread = game['spread']
                if spread['team1_spread'] != 'N/A':
                    message += f"Spread: {team1} ({spread['team1_spread']}) | {team2} ({spread['team2_spread']})\n"
                
                totals = game['totals']
                if totals['total_points'] != 'N/A':
                    message += f"O/U: {totals['total_points']}\n"
                
                message += "\n"
        
        return message

if __name__ == "__main__":
    scanner = BovadaScanner()
    games = scanner.scan_all_sports()
    print(f"Scan complete! Found {len(games)} football games")