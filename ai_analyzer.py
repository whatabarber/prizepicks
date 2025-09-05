import json
import statistics
from datetime import datetime, timedelta
import math
import random

class BettingAIAnalyzer:
    def __init__(self):
        # Simple thresholds for football only
        self.confidence_threshold = 2.0  # Low threshold to get picks
        self.max_picks_per_sport = 50    # Lots of picks per sport
        
        # Don't need value thresholds - we'll take anything football
        self.value_thresholds = {
            'moneyline': 0.01,  # Very low
            'spread': 0.01,     # Very low  
            'total': 0.01,      # Very low
            'prop': 0.01        # Very low
        }

    def analyze_bovada_games(self, games):
        """Analyze Bovada games - FOOTBALL ONLY"""
        if not games:
            return []
        
        analyzed_games = []
        
        for game in games:
            try:
                # ONLY ANALYZE NFL AND CFB
                sport = game.get('sport', '').upper()
                if sport not in ['NFL', 'CFB']:
                    continue
                    
                analysis = self.analyze_single_game(game)
                if analysis:
                    analyzed_games.append(analysis)
            except Exception as e:
                print(f"Error analyzing game: {str(e)}")
                continue
        
        # Sort by confidence and return all football picks
        analyzed_games.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        return analyzed_games

    def analyze_single_game(self, game):
        """Analyze a single game - simplified for football"""
        try:
            team1 = game.get('team1', 'Team A')
            team2 = game.get('team2', 'Team B')
            sport = game.get('sport', 'Unknown')
            
            analysis = {
                'id': game.get('id', ''),
                'sport': sport,
                'matchup': f"{team1} vs {team2}",
                'team1': team1,
                'team2': team2,
                'game_time': game.get('game_time', ''),
                'recommendations': [],
                'confidence_score': 0,
                'ai_commentary': '',
                'source': 'Bovada'
            }
            
            # Try all bet types - take anything with odds
            ml_analysis = self.analyze_moneyline(game)
            if ml_analysis:
                analysis['recommendations'].append(ml_analysis)
            
            spread_analysis = self.analyze_spread(game)
            if spread_analysis:
                analysis['recommendations'].append(spread_analysis)
            
            total_analysis = self.analyze_totals(game)
            if total_analysis:
                analysis['recommendations'].append(total_analysis)
            
            # Generate commentary
            analysis['ai_commentary'] = self.generate_game_commentary(game, analysis['recommendations'])
            
            # If we have any recommendations, take it
            if analysis['recommendations']:
                confidence_scores = [rec.get('confidence', 5) for rec in analysis['recommendations']]
                analysis['confidence_score'] = max(confidence_scores)
                return analysis
            
            return None
            
        except Exception as e:
            print(f"Error in single game analysis: {str(e)}")
            return None

    def analyze_moneyline(self, game):
        """Take any moneyline bet for football"""
        try:
            ml = game.get('moneyline', {})
            team1_odds = ml.get('team1_odds', 'N/A')
            team2_odds = ml.get('team2_odds', 'N/A')
            
            if team1_odds != 'N/A' and team2_odds != 'N/A':
                # Just pick the favorite (lower odds)
                try:
                    odds1 = int(team1_odds)
                    odds2 = int(team2_odds)
                    
                    if abs(odds1) < abs(odds2):  # Team1 is favorite
                        recommended_team = game['team1']
                        recommended_odds = team1_odds
                    else:
                        recommended_team = game['team2'] 
                        recommended_odds = team2_odds
                    
                    return {
                        'bet_type': 'Moneyline',
                        'recommendation': f"{recommended_team} ML",
                        'odds': recommended_odds,
                        'confidence': 7.0,
                        'value_edge': "5%",
                        'reasoning': f"Taking the favorite {recommended_team} on the moneyline."
                    }
                except:
                    pass
            
            return None
        except:
            return None

    def analyze_spread(self, game):
        """Take any spread bet for football"""
        try:
            spread = game.get('spread', {})
            team1_spread = spread.get('team1_spread', 'N/A')
            team1_odds = spread.get('team1_odds', 'N/A')
            team2_spread = spread.get('team2_spread', 'N/A')
            team2_odds = spread.get('team2_odds', 'N/A')
            
            if all(x != 'N/A' for x in [team1_spread, team1_odds, team2_spread, team2_odds]):
                # Just take team1 spread
                return {
                    'bet_type': 'Spread',
                    'recommendation': f"{game['team1']} {team1_spread}",
                    'odds': team1_odds,
                    'confidence': 6.5,
                    'value_edge': "4%",
                    'reasoning': f"Taking {game['team1']} against the spread."
                }
            
            return None
        except:
            return None

    def analyze_totals(self, game):
        """Take any totals bet for football"""
        try:
            totals = game.get('totals', {})
            total_points = totals.get('total_points', 'N/A')
            over_odds = totals.get('over_odds', 'N/A')
            under_odds = totals.get('under_odds', 'N/A')
            
            if all(x != 'N/A' for x in [total_points, over_odds, under_odds]):
                # Just take the over
                return {
                    'bet_type': 'Total',
                    'recommendation': f"Over {total_points}",
                    'odds': over_odds,
                    'confidence': 6.0,
                    'value_edge': "3%",
                    'reasoning': f"Taking the over {total_points} points."
                }
            
            return None
        except:
            return None

    def analyze_prizepicks_projections(self, projections):
        """Analyze PrizePicks projections - NFL AND CFB ONLY"""
        if not projections:
            return []
        
        analyzed_props = []
        
        for proj in projections:
            try:
                # ONLY ANALYZE FOOTBALL
                league = proj.get('league', '').upper()
                if not any(football in league for football in ['NFL', 'NCAAF', 'CFB']):
                    continue
                
                analysis = self.analyze_single_projection(proj)
                if analysis:
                    analyzed_props.append(analysis)
            except Exception as e:
                continue
        
        # Sort by confidence
        analyzed_props.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Take top 100 football picks
        return analyzed_props[:100]

    def analyze_single_projection(self, proj):
        """Analyze a single projection - simple football logic"""
        try:
            player = proj.get('player_name', 'Unknown Player')
            stat_type = proj.get('stat_type', '')
            line = proj.get('line_score', 0)
            odds_type = proj.get('odds_type', '')
            league = proj.get('league', '')
            
            # Basic validation
            if not player or not stat_type or line <= 0:
                return None
            
            # Calculate simple confidence
            confidence = self.calculate_simple_confidence(proj)
            
            if confidence < self.confidence_threshold:
                return None
            
            analysis = {
                'id': proj.get('id', ''),
                'player_name': player,
                'league': league,
                'sport': self.map_league_to_sport(league),
                'stat_type': stat_type,
                'line_score': line,
                'recommendation': f"{player} {odds_type} {line} {stat_type}",
                'confidence_score': confidence,
                'reasoning': f"Football pick: {player} {odds_type} {line} {stat_type}",
                'source': 'PrizePicks'
            }
            
            return analysis
            
        except Exception as e:
            return None

    def calculate_simple_confidence(self, proj):
        """Simple confidence - just boost football"""
        confidence = 5.0  # Start at 5
        
        league = proj.get('league', '').lower()
        player = proj.get('player_name', '').lower()
        
        # Big boost for football
        if 'nfl' in league:
            confidence += 2.0
        elif 'ncaaf' in league or 'cfb' in league:
            confidence += 1.5
        
        # Boost for known football players
        football_players = [
            'mahomes', 'allen', 'burrow', 'herbert', 'jackson', 'prescott',
            'kelce', 'adams', 'hill', 'jefferson', 'chase', 'diggs',
            'henry', 'mccaffrey', 'cook', 'jones', 'elliott', 'barkley'
        ]
        
        if any(name in player for name in football_players):
            confidence += 1.0
        
        # Add randomness for variety
        confidence += random.uniform(-0.5, 1.0)
        
        return min(9.5, max(4.0, confidence))

    def map_league_to_sport(self, league):
        """Map league to sport - FOOTBALL ONLY"""
        league_lower = league.lower()
        if 'nfl' in league_lower:
            return 'NFL'
        elif 'ncaaf' in league_lower or 'cfb' in league_lower:
            return 'CFB'
        else:
            return None  # Filter out non-football

    def generate_game_commentary(self, game, recommendations):
        """Generate simple commentary"""
        team1 = game.get('team1', 'Team A')
        team2 = game.get('team2', 'Team B')
        
        if not recommendations:
            return f"No bets identified for {team1} vs {team2}."
        
        commentary = f"{team1} vs {team2} - {len(recommendations)} betting opportunities found."
        return commentary

    def format_analysis_for_discord(self, bovada_analysis, prizepicks_analysis):
        """Format for Discord - football focus"""
        message = f"FOOTBALL BETTING ANALYSIS\n"
        message += f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        
        if bovada_analysis:
            message += f"BOVADA FOOTBALL GAMES ({len(bovada_analysis)})\n"
            for analysis in bovada_analysis[:5]:
                message += f"• {analysis['matchup']}\n"
        
        if prizepicks_analysis:
            message += f"\nPRIZEPICKS FOOTBALL PROPS ({len(prizepicks_analysis)})\n"
            for prop in prizepicks_analysis[:10]:
                message += f"• {prop['recommendation']}\n"
        
        return message

if __name__ == "__main__":
    analyzer = BettingAIAnalyzer()
    print("Football-Only AI Analyzer initialized")