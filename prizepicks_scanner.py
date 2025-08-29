import requests
import json
import time
from datetime import datetime
import os

class PrizePicksScanner:
    def __init__(self):
        # Try multiple API endpoints
        self.base_urls = [
            "https://partner-api.prizepicks.com/projections",
            "https://api.prizepicks.com/projections", 
            "https://partner-api.prizepicks.com/projections?league_id=1,2,3,4,5,6,7,8,9,10"
        ]
        self.leagues_url = "https://partner-api.prizepicks.com/leagues"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://app.prizepicks.com/',
            'Origin': 'https://app.prizepicks.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Target leagues we want to track - expanded to catch more variations
        self.target_leagues = {
            'NFL': ['NFL', 'NFLP'],  # Added NFLP for preseason
            'CFB': ['NCAAF', 'College Football', 'CFB'],
            'NBA': ['NBA'], 
            'CBB': ['NCAAB', 'College Basketball', 'CBB'],
            'MLB': ['MLB', 'Major League Baseball']
        }
        
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_active_leagues(self):
        """Get list of currently active leagues"""
        try:
            print("🔄 Fetching active leagues from PrizePicks...")
            response = requests.get(self.leagues_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                leagues = data.get('data', [])
                active_leagues = []
                
                print(f"📊 Raw leagues response: {len(leagues)} leagues found")
                
                for league in leagues:
                    league_name = league.get('attributes', {}).get('name', '')
                    league_id = league.get('id', '')
                    if league_name and league_id:
                        active_leagues.append({
                            'id': league_id,
                            'name': league_name
                        })
                        
                        # Debug: Print all league names to see what's available
                        if any(target.lower() in league_name.lower() for targets in self.target_leagues.values() for target in targets):
                            print(f"🎯 Target league found: {league_name} (ID: {league_id})")
                
                print(f"✅ Found {len(active_leagues)} active leagues")
                return active_leagues
            else:
                print(f"❌ Failed to fetch leagues: Status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching leagues: {str(e)}")
            return []

    def fetch_projections(self, league_ids=None):
        """Fetch live projections from PrizePicks - try multiple endpoints"""
        
        # Try each URL until we get data
        for i, base_url in enumerate(self.base_urls):
            try:
                print(f"🔄 Attempt {i+1}: Fetching projections from {base_url}")
                
                url = base_url
                if league_ids and i == 0:  # Only add league filter to first URL
                    league_filter = ','.join(map(str, league_ids))
                    url += f"?league_id={league_filter}"
                    print(f"🎯 Filtering for leagues: {league_filter}")
                
                print(f"📡 Requesting: {url}")
                response = requests.get(url, headers=self.headers, timeout=15)
                
                print(f"📡 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Debug: Print response structure
                    print(f"📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if isinstance(data, dict) and 'data' in data:
                        projection_count = len(data.get('data', []))
                        print(f"📊 Raw projections count: {projection_count}")
                        print(f"📊 Included items count: {len(data.get('included', []))}")
                        
                        # If we got projections, return this data
                        if projection_count > 0:
                            print(f"✅ Success! Found {projection_count} projections")
                            return data
                        else:
                            print(f"⚠️ No projections in response, trying next endpoint...")
                    else:
                        print(f"⚠️ Unexpected response format: {str(data)[:200]}...")
                        
                elif response.status_code == 429:
                    print(f"⚠️ Rate limited (429), trying next endpoint...")
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error with endpoint {i+1}: {str(e)}")
                continue
        
        print("❌ All endpoints failed or returned no data")
        return None

    def parse_projections(self, data):
        """Parse projection data into structured format"""
        if not data or 'data' not in data:
            print("❌ No projection data found in response")
            return []
            
        projections = []
        raw_projections = data.get('data', [])
        included = data.get('included', [])
        
        print(f"📊 Processing {len(raw_projections)} raw projections...")
        
        # Create lookup maps for related data
        players_map = {}
        leagues_map = {}
        teams_map = {}
        
        for item in included:
            item_type = item.get('type', '')
            item_id = item.get('id', '')
            
            if item_type == 'new_player':
                players_map[item_id] = item.get('attributes', {})
            elif item_type == 'league':
                leagues_map[item_id] = item.get('attributes', {})
            elif item_type == 'team':
                teams_map[item_id] = item.get('attributes', {})
        
        print(f"📊 Lookup maps - Players: {len(players_map)}, Leagues: {len(leagues_map)}, Teams: {len(teams_map)}")
        
        for i, proj in enumerate(raw_projections):
            try:
                projection_data = self.extract_projection_info(proj, players_map, leagues_map, teams_map)
                if projection_data:
                    league_name = projection_data.get('league', '')
                    is_target = self.is_target_league(league_name)
                    
                    if i < 5:  # Debug first 5 projections
                        print(f"🔍 Projection {i+1}: {projection_data.get('player_name', 'Unknown')} - {league_name} - Target: {is_target}")
                    
                    if is_target:
                        projections.append(projection_data)
                        
            except Exception as e:
                print(f"⚠️ Error parsing projection {i+1}: {str(e)}")
                continue
        
        print(f"✅ Parsed {len(projections)} target projections from {len(raw_projections)} total")
        return projections

    def extract_projection_info(self, proj, players_map, leagues_map, teams_map):
        """Extract projection information"""
        try:
            attributes = proj.get('attributes', {})
            relationships = proj.get('relationships', {})
            
            # Basic projection info
            stat_type = attributes.get('stat_type', '')
            line_score = attributes.get('line_score', 0)
            odds_type = attributes.get('odds_type', '')
            description = attributes.get('description', '')
            start_time = attributes.get('start_time', '')
            
            # Get player info
            player_data = relationships.get('new_player', {}).get('data', {})
            player_id = player_data.get('id', '')
            player_info = players_map.get(player_id, {})
            player_name = player_info.get('display_name', 'Unknown')
            position = player_info.get('position', '')
            
            # Get league info
            league_data = relationships.get('league', {}).get('data', {})
            league_id = league_data.get('id', '')
            league_info = leagues_map.get(league_id, {})
            league_name = league_info.get('name', 'Unknown')
            
            # Get team info if available
            team_data = relationships.get('team', {}).get('data', {})
            team_id = team_data.get('id', '')
            team_info = teams_map.get(team_id, {})
            team_name = team_info.get('name', '')
            
            projection_info = {
                'id': proj.get('id', ''),
                'player_name': player_name,
                'position': position,
                'team': team_name,
                'league': league_name,
                'stat_type': stat_type,
                'line_score': line_score,
                'odds_type': odds_type,
                'description': description,
                'start_time': start_time,
                'timestamp': datetime.now().isoformat(),
                'source': 'PrizePicks'
            }
            
            return projection_info
            
        except Exception as e:
            print(f"⚠️ Error extracting projection info: {str(e)}")
            return None

    def is_target_league(self, league_name):
        """Check if league is one we want to track"""
        for target_sport, league_variations in self.target_leagues.items():
            for variation in league_variations:
                if variation.lower() in league_name.lower():
                    return True
        return False

    def categorize_by_sport(self, projections):
        """Categorize projections by sport"""
        categorized = {
            'NFL': [],
            'CFB': [],
            'NBA': [],
            'CBB': [],
            'MLB': [],
            'Other': []
        }
        
        for proj in projections:
            league = proj.get('league', '').lower()
            
            if 'nfl' in league or 'nflp' in league:
                categorized['NFL'].append(proj)
            elif 'ncaaf' in league or 'college football' in league or 'cfb' in league:
                categorized['CFB'].append(proj)
            elif 'nba' in league:
                categorized['NBA'].append(proj)
            elif 'ncaab' in league or 'college basketball' in league or 'cbb' in league:
                categorized['CBB'].append(proj)
            elif 'mlb' in league or 'major league baseball' in league:
                categorized['MLB'].append(proj)
            else:
                categorized['Other'].append(proj)
                # Debug: Print unknown leagues
                print(f"🔍 Unknown league found: '{proj.get('league', 'N/A')}'")
        
        return categorized

    def scan_all_projections(self):
        """Scan all live projections"""
        print("🚀 Starting PrizePicks scan...")
        
        # First try without any league filtering to get ALL projections
        print("🎯 Attempting to fetch ALL projections first...")
        data = self.fetch_projections(league_ids=None)
        
        if not data:
            print("❌ No projection data retrieved from any endpoint")
            return []
        
        # Parse projections
        projections = self.parse_projections(data)
        
        # If we got projections, categorize and filter them
        if projections:
            # Categorize by sport
            categorized = self.categorize_by_sport(projections)
            
            # Print summary
            total_projections = 0
            for sport, projs in categorized.items():
                count = len(projs)
                total_projections += count
                if count > 0:
                    print(f"✅ {sport}: Found {count} projections")
            
            # Save all projections
            output_file = os.path.join(self.data_dir, 'prizepicks_projections.json')
            with open(output_file, 'w') as f:
                json.dump(projections, f, indent=2)
                
            categorized_file = os.path.join(self.data_dir, 'prizepicks_by_sport.json')
            with open(categorized_file, 'w') as f:
                json.dump(categorized, f, indent=2)
                
            print(f"💾 Saved {total_projections} total projections")
            return projections
        else:
            print("❌ No projections found after parsing")
            return []

    def format_for_discord(self, projections):
        """Format projections for Discord alerts"""
        if not projections:
            return "🚫 No live projections found on PrizePicks"
            
        categorized = self.categorize_by_sport(projections)
        
        message = f"🎯 **PRIZEPICKS LIVE PROJECTIONS** 🎯\n"
        message += f"⏰ {datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        
        for sport, projs in categorized.items():
            if not projs:
                continue
                
            message += f"**{sport}** ({len(projs)} projections)\n"
            
            # Show top projections for each sport
            for proj in projs[:8]:  # Limit to 8 per sport
                player = proj['player_name']
                stat = proj['stat_type']
                line = proj['line_score']
                team = proj['team']
                odds_type = proj['odds_type']
                
                # Format the line
                if odds_type.lower() == 'over':
                    direction = "Over"
                elif odds_type.lower() == 'under':
                    direction = "Under"
                else:
                    direction = odds_type
                
                team_info = f" ({team})" if team else ""
                message += f"🏈 **{player}**{team_info}\n"
                message += f"   📊 {stat}: {direction} {line}\n"
                
            if len(projs) > 8:
                message += f"... and {len(projs) - 8} more {sport} projections\n"
            message += "\n"
        
        return message

    def get_best_projections(self, projections, min_line=None, stat_types=None):
        """Filter projections based on criteria"""
        filtered = []
        
        for proj in projections:
            # Filter by minimum line if specified
            if min_line and proj.get('line_score', 0) < min_line:
                continue
                
            # Filter by stat types if specified
            if stat_types and proj.get('stat_type', '') not in stat_types:
                continue
                
            filtered.append(proj)
        
        return filtered

if __name__ == "__main__":
    scanner = PrizePicksScanner()
    projections = scanner.scan_all_projections()
    print(f"\n🎉 Scan complete! Found {len(projections)} total projections")