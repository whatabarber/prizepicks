import requests
import json
import time
from datetime import datetime
import os

class OddsAPIScanner:
    def __init__(self):
        self.api_key = "8dfaf92c77d8fc5ebea9ba17af5b5518"
        self.base_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        self.cfb_url = "https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Common US sportsbooks
        self.bookmakers = "fanduel,draftkings,betmgm,caesars,bovada"
        
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def fetch_nfl_games(self):
        """Fetch NFL games from Odds API"""
        try:
            print("Fetching NFL games from Odds API...")
            
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',  # moneyline, spreads, totals
                'oddsFormat': 'american',
                'bookmakers': self.bookmakers
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                games = self.parse_odds_api_games(data, 'NFL')
                print(f"NFL: Found {len(games)} games")
                return games
            else:
                print(f"Failed to fetch NFL: Status {response.status_code}")
                if response.status_code == 422:
                    print("Error details:", response.text)
                return []
                
        except Exception as e:
            print(f"Error fetching NFL: {str(e)}")
            return []

    def fetch_cfb_games(self):
        """Fetch CFB games from Odds API"""
        try:
            print("Fetching CFB games from Odds API...")
            
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american',
                'bookmakers': self.bookmakers
            }
            
            response = requests.get(self.cfb_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                games = self.parse_odds_api_games(data, 'CFB')
                print(f"CFB: Found {len(games)} games")
                return games
            else:
                print(f"Failed to fetch CFB: Status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching CFB: {str(e)}")
            return []

    def parse_odds_api_games(self, data, sport_name):
        """Parse games from Odds API response"""
        games = []
        
        try:
            for event in data:
                try:
                    game_data = self.extract_odds_api_game_info(event, sport_name)
                    if game_data:
                        games.append(game_data)
                except Exception as e:
                    print(f"Error parsing game: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing {sport_name} data: {str(e)}")
            
        return games

    def extract_odds_api_game_info(self, event, sport_name):
        """Extract game information from Odds API format"""
        try:
            # Get team names
            home_team = event.get('home_team', 'Home Team')
            away_team = event.get('away_team', 'Away Team')
            
            game_time = event.get('commence_time', '')
            event_id = event.get('id', '')
            
            # Initialize odds structures
            moneyline_odds = {'team1_odds': 'N/A', 'team2_odds': 'N/A'}
            spread_odds = {'team1_spread': 'N/A', 'team1_odds': 'N/A', 'team2_spread': 'N/A', 'team2_odds': 'N/A'}
            total_odds = {'total_points': 'N/A', 'over_odds': 'N/A', 'under_odds': 'N/A'}
            
            # Parse bookmaker odds (use first available bookmaker)
            bookmakers = event.get('bookmakers', [])
            if bookmakers:
                bookmaker = bookmakers[0]  # Use first bookmaker
                markets = bookmaker.get('markets', [])
                
                for market in markets:
                    market_key = market.get('key', '')
                    outcomes = market.get('outcomes', [])
                    
                    if market_key == 'h2h' and len(outcomes) >= 2:
                        # Moneyline
                        for outcome in outcomes:
                            if outcome.get('name') == away_team:
                                moneyline_odds['team1_odds'] = outcome.get('price', 'N/A')
                            elif outcome.get('name') == home_team:
                                moneyline_odds['team2_odds'] = outcome.get('price', 'N/A')
                    
                    elif market_key == 'spreads' and len(outcomes) >= 2:
                        # Spreads
                        for outcome in outcomes:
                            if outcome.get('name') == away_team:
                                spread_odds['team1_spread'] = outcome.get('point', 'N/A')
                                spread_odds['team1_odds'] = outcome.get('price', 'N/A')
                            elif outcome.get('name') == home_team:
                                spread_odds['team2_spread'] = outcome.get('point', 'N/A')
                                spread_odds['team2_odds'] = outcome.get('price', 'N/A')
                    
                    elif market_key == 'totals' and len(outcomes) >= 2:
                        # Totals
                        total_points = None
                        for outcome in outcomes:
                            if outcome.get('name') == 'Over':
                                total_odds['over_odds'] = outcome.get('price', 'N/A')
                                total_points = outcome.get('point', 'N/A')
                            elif outcome.get('name') == 'Under':
                                total_odds['under_odds'] = outcome.get('price', 'N/A')
                                if not total_points:
                                    total_points = outcome.get('point', 'N/A')
                        
                        total_odds['total_points'] = total_points
            
            game_info = {
                'id': event_id,
                'sport': sport_name,
                'team1': away_team,  # Away team first
                'team2': home_team,  # Home team second
                'game_time': game_time,
                'moneyline': moneyline_odds,
                'spread': spread_odds,
                'totals': total_odds,
                'timestamp': datetime.now().isoformat(),
                'source': 'OddsAPI'
            }
            
            return game_info
            
        except Exception as e:
            print(f"Error extracting game info: {str(e)}")
            return None

    def scan_all_sports(self):
        """Scan NFL and CFB using Odds API"""
        all_games = []
        
        print("Starting Odds API scan for football...")
        
        # Get NFL games
        nfl_games = self.fetch_nfl_games()
        all_games.extend(nfl_games)
        
        time.sleep(1)  # Rate limiting
        
        # Get CFB games
        cfb_games = self.fetch_cfb_games()
        all_games.extend(cfb_games)
        
        # Save to JSON
        if all_games:
            output_file = os.path.join(self.data_dir, 'bovada_games.json')  # Keep same filename for compatibility
            with open(output_file, 'w') as f:
                json.dump(all_games, f, indent=2)
                
            print(f"Saved {len(all_games)} total football games to {output_file}")
        else:
            print("No football games found")
            
        return all_games

    def format_for_discord(self, games):
        """Format games for Discord"""
        if not games:
            return "No live football games found via Odds API"
            
        message = f"ODDS API FOOTBALL UPDATE\n"
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
            
            for game in sport_games[:3]:  # Limit display
                team1 = game['team1']
                team2 = game['team2']
                
                message += f"{team1} @ {team2}\n"
                
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

# Alias for compatibility with existing code
BovadaScanner = OddsAPIScanner

if __name__ == "__main__":
    scanner = OddsAPIScanner()
    games = scanner.scan_all_sports()
    print(f"Scan complete! Found {len(games)} football games")