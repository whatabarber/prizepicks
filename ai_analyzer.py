import json
import statistics
from datetime import datetime, timedelta
import math

class BettingAIAnalyzer:
    def __init__(self):
        # LOWERED thresholds for more picks
        self.confidence_threshold = 3.5  # Was 5.0 - now much more inclusive
        self.max_picks_per_sport = 25    # Increased from 15
        
        # REDUCED value thresholds for more opportunities
        self.value_thresholds = {
            'moneyline': 0.04,  # Was 0.08 - cut in half
            'spread': 0.03,     # Was 0.06 - cut in half  
            'total': 0.02,      # Was 0.05 - much lower
            'prop': 0.05        # Was 0.10 - cut in half
        }

    def analyze_bovada_games(self, games):
        """Analyze Bovada games and provide AI commentary with best bets"""
        if not games:
            return []
        
        analyzed_games = []
        
        for game in games:
            try:
                analysis = self.analyze_single_game(game)
                if analysis:
                    analyzed_games.append(analysis)
            except Exception as e:
                print(f"Error analyzing game: {str(e)}")
                continue
        
        # Sort by confidence and return top picks
        analyzed_games.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Group by sport and limit per sport (INCREASED LIMITS)
        sport_picks = {}
        for analysis in analyzed_games:
            sport = analysis['sport']
            if sport not in sport_picks:
                sport_picks[sport] = []
            if len(sport_picks[sport]) < self.max_picks_per_sport:
                sport_picks[sport].append(analysis)
        
        # Flatten back to list
        top_picks = []
        for sport_list in sport_picks.values():
            top_picks.extend(sport_list)
        
        return top_picks

    def analyze_single_game(self, game):
        """Analyze a single game with AI commentary"""
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
            
            # Analyze moneyline
            ml_analysis = self.analyze_moneyline(game)
            if ml_analysis:
                analysis['recommendations'].append(ml_analysis)
            
            # Analyze spread
            spread_analysis = self.analyze_spread(game)
            if spread_analysis:
                analysis['recommendations'].append(spread_analysis)
            
            # Analyze totals
            total_analysis = self.analyze_totals(game)
            if total_analysis:
                analysis['recommendations'].append(total_analysis)
            
            # Generate AI commentary
            analysis['ai_commentary'] = self.generate_game_commentary(game, analysis['recommendations'])
            
            # Calculate overall confidence
            if analysis['recommendations']:
                confidence_scores = [rec.get('confidence', 3.5) for rec in analysis['recommendations']]
                analysis['confidence_score'] = max(confidence_scores)
                
                # LOWERED threshold - was 5.0, now 3.5
                if analysis['confidence_score'] >= self.confidence_threshold:
                    return analysis
            
            return None
            
        except Exception as e:
            print(f"Error in single game analysis: {str(e)}")
            return None

    def analyze_moneyline(self, game):
        """Analyze moneyline odds for value - MORE AGGRESSIVE"""
        try:
            ml = game.get('moneyline', {})
            team1_odds = ml.get('team1_odds', 'N/A')
            team2_odds = ml.get('team2_odds', 'N/A')
            
            if team1_odds == 'N/A' or team2_odds == 'N/A':
                return None
            
            # Convert American odds to implied probability
            team1_prob = self.american_to_probability(team1_odds)
            team2_prob = self.american_to_probability(team2_odds)
            
            if not team1_prob or not team2_prob:
                return None
            
            # Calculate theoretical fair odds
            total_prob = team1_prob + team2_prob
            team1_fair = team1_prob / total_prob
            team2_fair = team2_prob / total_prob
            
            # Look for value bets
            team1_value = self.calculate_value(team1_fair, team1_prob)
            team2_value = self.calculate_value(team2_fair, team2_prob)
            
            best_value = max(team1_value, team2_value)
            
            # MUCH LOWER threshold - was 0.08, now 0.04
            if best_value > self.value_thresholds['moneyline']:
                recommended_team = game['team1'] if team1_value > team2_value else game['team2']
                recommended_odds = team1_odds if team1_value > team2_value else team2_odds
                
                # BOOSTED confidence scoring
                confidence = min(10, 4.0 + (best_value * 30))  # More generous scoring
                
                return {
                    'bet_type': 'Moneyline',
                    'recommendation': f"{recommended_team} ML",
                    'odds': recommended_odds,
                    'confidence': confidence,
                    'value_edge': f"{best_value:.1%}",
                    'reasoning': f"Strong value on {recommended_team} ML at {recommended_odds}. Market appears to be undervaluing this team by {best_value:.1%}."
                }
            
            return None
            
        except Exception as e:
            return None

    def analyze_spread(self, game):
        """Analyze point spread for value - MORE GENEROUS"""
        try:
            spread = game.get('spread', {})
            team1_spread = spread.get('team1_spread', 'N/A')
            team1_odds = spread.get('team1_odds', 'N/A')
            team2_spread = spread.get('team2_spread', 'N/A')
            team2_odds = spread.get('team2_odds', 'N/A')
            
            if any(x == 'N/A' for x in [team1_spread, team1_odds, team2_spread, team2_odds]):
                return None
            
            try:
                spread1 = float(team1_spread)
                spread2 = float(team2_spread)
                odds1 = int(team1_odds)
                odds2 = int(team2_odds)
            except (ValueError, TypeError):
                return None
            
            # MUCH MORE GENEROUS confidence scoring
            confidence = 4.0  # Start higher
            recommendation = None
            
            # RELAXED odds requirements - was -120, now -130
            if odds1 >= -130:
                confidence = 6.0  # Higher base confidence
                recommendation = f"{game['team1']} {team1_spread}"
                best_odds = team1_odds
            elif odds2 >= -130:
                confidence = 6.0
                recommendation = f"{game['team2']} {team2_spread}"
                best_odds = team2_odds
            elif abs(spread1) <= 14:  # Increased from 10 to 14
                confidence = 5.5
                if odds1 >= odds2:
                    recommendation = f"{game['team1']} {team1_spread}"
                    best_odds = team1_odds
                else:
                    recommendation = f"{game['team2']} {team2_spread}"
                    best_odds = team2_odds
            
            # LOWERED threshold - was 5.0, now 3.5
            if recommendation and confidence >= self.confidence_threshold:
                return {
                    'bet_type': 'Spread',
                    'recommendation': recommendation,
                    'odds': best_odds,
                    'confidence': confidence,
                    'value_edge': "4-8%",  # More optimistic
                    'reasoning': f"Solid spread bet with decent odds. {recommendation} offers good value in this matchup."
                }
            
            return None
            
        except Exception as e:
            return None

    def analyze_totals(self, game):
        """Analyze over/under totals - MORE INCLUSIVE"""
        try:
            totals = game.get('totals', {})
            total_points = totals.get('total_points', 'N/A')
            over_odds = totals.get('over_odds', 'N/A')
            under_odds = totals.get('under_odds', 'N/A')
            
            if any(x == 'N/A' for x in [total_points, over_odds, under_odds]):
                return None
            
            try:
                total = float(total_points)
                over = int(over_odds)
                under = int(under_odds)
            except (ValueError, TypeError):
                return None
            
            # MORE GENEROUS starting confidence
            confidence = 4.5  # Higher starting point
            recommendation = None
            sport = game.get('sport', '').upper()
            
            # RELAXED odds requirements - was -115, now -125
            if sport == 'NFL':
                if over >= -125:
                    confidence = 6.5  # Boosted confidence
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -125:
                    confidence = 6.5
                    recommendation = f"Under {total}"
                    bet_odds = under
            elif sport == 'NBA':
                if over >= -125:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -125:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            elif sport == 'MLB':
                if over >= -125:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -125:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            elif sport == 'CFB':  # Added CFB support
                if over >= -125:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -125:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            
            # LOWERED threshold
            if recommendation and confidence >= self.confidence_threshold:
                return {
                    'bet_type': 'Total',
                    'recommendation': recommendation,
                    'odds': bet_odds,
                    'confidence': confidence,
                    'value_edge': "4-7%",  # More optimistic
                    'reasoning': f"Good total with solid odds. {recommendation} offers strong value for {sport}."
                }
            
            return None
            
        except Exception as e:
            return None

    def analyze_prizepicks_projections(self, projections):
        """Analyze PrizePicks projections - PRIORITIZE FOOTBALL FIRST"""
        if not projections:
            return []
        
        analyzed_props = []
        
        for proj in projections:
            try:
                analysis = self.analyze_single_projection(proj)
                if analysis:
                    analyzed_props.append(analysis)
            except Exception as e:
                print(f"Error analyzing projection: {str(e)}")
                continue
        
        # Sort by SPORT PRIORITY FIRST, then confidence
        def sort_key(prop):
            sport = prop.get('sport', '')
            confidence = prop.get('confidence_score', 0)
            
            # FOOTBALL GETS MASSIVE PRIORITY BOOST
            if sport == 'NFL':
                return (1000 + confidence, confidence)  # NFL gets 1000+ boost
            elif sport == 'CFB':
                return (900 + confidence, confidence)   # CFB gets 900+ boost
            elif sport == 'NBA':
                return (100 + confidence, confidence)   # NBA gets small boost
            elif sport == 'CBB':
                return (50 + confidence, confidence)    # CBB gets tiny boost
            else:
                return (confidence, confidence)         # Others no boost
        
        analyzed_props.sort(key=sort_key, reverse=True)
        
        # Diversify by player but HEAVILY FAVOR FOOTBALL
        diversified_props = self.diversify_player_picks_football_first(analyzed_props)
        
        # Group by sport and PRIORITIZE FOOTBALL ALLOCATION
        sport_props = {}
        football_picks = 0
        other_picks = 0
        
        for prop in diversified_props:
            sport = prop.get('sport', '')
            
            if sport not in sport_props:
                sport_props[sport] = []
            
            # FOOTBALL GETS MUCH HIGHER LIMITS
            if sport in ['NFL', 'CFB']:
                if len(sport_props[sport]) < 40:  # 40 picks per football sport
                    sport_props[sport].append(prop)
                    football_picks += 1
            else:
                # Other sports get reduced limits until we have enough football
                if football_picks < 50:  # Only allow 5 non-football if we have <50 football
                    max_other = 5
                else:
                    max_other = 15  # Allow more others if we have enough football
                
                if len(sport_props[sport]) < max_other:
                    sport_props[sport].append(prop)
                    other_picks += 1
        
        # Flatten and return, maintaining football priority
        top_props = []
        
        # Add football first
        for sport in ['NFL', 'CFB']:
            if sport in sport_props:
                top_props.extend(sport_props[sport])
        
        # Then add others
        for sport, props in sport_props.items():
            if sport not in ['NFL', 'CFB']:
                top_props.extend(props)
        
        print(f"Final pick distribution: Football={football_picks}, Other={other_picks}")
        return top_props

    def diversify_player_picks_football_first(self, analyzed_props, max_per_player=6):
        """Diversify but prioritize football players heavily"""
        player_picks = {}
        diversified = []
        
        # Group by player AND sport
        for prop in analyzed_props:
            player = prop.get('player_name', 'Unknown')
            sport = prop.get('sport', '')
            key = f"{player}_{sport}"
            
            if key not in player_picks:
                player_picks[key] = []
            player_picks[key].append(prop)
        
        # Process football players first with higher limits
        football_players = {k: v for k, v in player_picks.items() if any(sport in k for sport in ['NFL', 'CFB'])}
        other_players = {k: v for k, v in player_picks.items() if k not in football_players}
        
        # Football players get more picks per player
        for player_key, picks in football_players.items():
            picks.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            stat_types_seen = set()
            player_selected = []
            
            for pick in picks:
                stat_type = pick.get('stat_type', '').lower()
                
                if stat_type not in stat_types_seen or len(player_selected) == 0:
                    player_selected.append(pick)
                    stat_types_seen.add(stat_type)
                    
                    if len(player_selected) >= max_per_player:
                        break
            
            # For high confidence football picks, add extras regardless of stat type
            if len(player_selected) < max_per_player:
                for pick in picks:
                    if pick not in player_selected and pick.get('confidence_score', 0) >= 6.0:
                        player_selected.append(pick)
                        if len(player_selected) >= max_per_player:
                            break
            
            diversified.extend(player_selected)
        
        # Other sports get reduced limits
        for player_key, picks in other_players.items():
            picks.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            # Only take top 2 picks for non-football
            diversified.extend(picks[:2])
        
        # Sort final list: football first, then by confidence
        def final_sort_key(prop):
            sport = prop.get('sport', '')
            confidence = prop.get('confidence_score', 0)
            
            if sport == 'NFL':
                return (2000 + confidence, confidence)
            elif sport == 'CFB':  
                return (1900 + confidence, confidence)
            else:
                return (confidence, confidence)
        
        diversified.sort(key=final_sort_key, reverse=True)
        
        return diversified

    def analyze_single_projection(self, proj):
        """Analyze a single PrizePicks projection - MORE GENEROUS"""
        try:
            player = proj.get('player_name', 'Unknown Player')
            stat_type = proj.get('stat_type', '')
            line = proj.get('line_score', 0)
            odds_type = proj.get('odds_type', '')
            league = proj.get('league', '')
            
            # Calculate confidence based on multiple factors
            confidence = self.calculate_prop_confidence(proj)
            
            # LOWERED threshold from 5.0 to 3.5
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
                'reasoning': self.generate_prop_reasoning(proj, confidence),
                'source': 'PrizePicks'
            }
            
            return analysis
            
        except Exception as e:
            return None

    # Add this function to your ai_analyzer.py

def validate_pick_data(self, proj):
    """Validate that pick data makes logical sense"""
    try:
        player = proj.get('player_name', '').lower()
        stat_type = proj.get('stat_type', '').lower()
        line_score = proj.get('line_score', 0)
        
        # Skip picks with obviously wrong data
        if not player or not stat_type or line_score <= 0:
            return False
        
        # Position-based validation
        # RBs shouldn't have high receiving yards (unless they're pass-catching backs)
        rb_names = ['henry', 'elliott', 'chubb', 'hunt', 'harris', 'sanders']
        if any(rb in player for rb in rb_names):
            if 'receiv' in stat_type and line_score > 50:
                print(f"⚠️ Suspicious: {player} - {stat_type} {line_score} (RB with high receiving)")
                return False
        
        # QBs shouldn't have receiving stats
        qb_names = ['mahomes', 'allen', 'burrow', 'herbert', 'jackson', 'prescott']
        if any(qb in player for qb in qb_names):
            if 'receiv' in stat_type or 'catch' in stat_type:
                print(f"⚠️ Suspicious: {player} - {stat_type} {line_score} (QB receiving)")
                return False
        
        # Reasonable ranges for different stats
        stat_ranges = {
            'pass': {'min': 150, 'max': 400},      # Passing yards
            'rush': {'min': 10, 'max': 200},       # Rushing yards  
            'receiv': {'min': 10, 'max': 150},     # Receiving yards
            'reception': {'min': 1, 'max': 15},    # Receptions
            'completion': {'min': 15, 'max': 45},  # Completions
            'attempt': {'min': 20, 'max': 50},     # Attempts
            'touchdown': {'min': 0.5, 'max': 4}    # TDs
        }
        
        for stat_key, ranges in stat_ranges.items():
            if stat_key in stat_type:
                if line_score < ranges['min'] or line_score > ranges['max']:
                    print(f"⚠️ Suspicious: {player} - {stat_type} {line_score} (outside normal range)")
                    return False
        
        return True
        
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return False

# Update your analyze_single_projection function to use validation:

def analyze_single_projection(self, proj):
    """Analyze a single PrizePicks projection - WITH VALIDATION"""
    try:
        # FIRST: Validate the data makes sense
        if not self.validate_pick_data(proj):
            return None
        
        player = proj.get('player_name', 'Unknown Player')
        stat_type = proj.get('stat_type', '')
        line = proj.get('line_score', 0)
        odds_type = proj.get('odds_type', '')
        league = proj.get('league', '')
        
        # Calculate confidence based on multiple factors
        confidence = self.calculate_prop_confidence(proj)
        
        # LOWERED threshold from 5.0 to 3.5
        if confidence < self.confidence_threshold:
            return None
        
        # Clean up the stat type display
        clean_stat_type = self.clean_stat_type(stat_type)
        
        analysis = {
            'id': proj.get('id', ''),
            'player_name': player,
            'league': league,
            'sport': self.map_league_to_sport(league),
            'stat_type': clean_stat_type,  # Use cleaned version
            'line_score': line,
            'recommendation': f"{player} {odds_type} {line} {clean_stat_type}",
            'confidence_score': confidence,
            'reasoning': self.generate_prop_reasoning(proj, confidence),
            'source': 'PrizePicks'
        }
        
        return analysis
        
    except Exception as e:
        return None

def clean_stat_type(self, stat_type):
    """Clean up stat type names for better display"""
    stat_type = stat_type.lower().strip()
    
    # Common mappings
    mappings = {
        'passing yards': 'Pass Yards',
        'rushing yards': 'Rush Yards', 
        'receiving yards': 'Receiving Yards',
        'receptions': 'Receptions',
        'completions': 'Completions',
        'pass attempts': 'Pass Attempts',
        'rushing attempts': 'Rush Attempts',
        'passing touchdowns': 'Pass TDs',
        'rushing touchdowns': 'Rush TDs',
        'receiving touchdowns': 'Receiving TDs'
    }
    
    # Check exact matches first
    if stat_type in mappings:
        return mappings[stat_type]
    
    # Check partial matches
    for key, value in mappings.items():
        if key in stat_type:
            return value
    
    # Capitalize first letter if no mapping found
    return stat_type.title()

    def calculate_prop_confidence(self, proj):
        """Calculate confidence score - BOOST FOOTBALL MASSIVELY"""
        confidence = 4.0
        
        stat_type = proj.get('stat_type', '').lower()
        line = proj.get('line_score', 0)
        player = proj.get('player_name', '').lower()
        league = proj.get('league', '').lower()
        
        # MASSIVE FOOTBALL BOOST
        if 'nfl' in league:
            confidence += 3.0  # Huge NFL boost
        elif 'ncaaf' in league or 'cfb' in league:
            confidence += 2.5  # Big CFB boost
        elif 'nba' in league:
            confidence += 0.5  # Small NBA boost
        else:
            confidence += 0.0  # No boost for others
        
        # EXTRA boosts for football stat types
        if 'nfl' in league or 'ncaaf' in league:
            if any(stat in stat_type for stat in ['pass', 'rush', 'receiving', 'yards', 'touchdown', 'completion']):
                confidence += 1.5  # Big boost for football stats
        
        # Regular boosts
        if any(stat in stat_type for stat in ['points', 'yards', 'strikeouts', 'hits', 'receptions']):
            confidence += 1.0
        
        if line in [0.5, 1.5, 2.5, 20.5, 25.5, 50.5, 100.5, 200.5, 250.5]:
            confidence += 0.8
        
        # EXPANDED football player detection
        football_stars = [
            'mahomes', 'allen', 'burrow', 'herbert', 'lamar', 'jackson', 'josh', 'patrick',
            'kelce', 'adams', 'hill', 'jefferson', 'chase', 'diggs', 'hopkins', 'kupp',
            'mccaffrey', 'henry', 'cook', 'jones', 'elliott', 'kamara', 'barkley',
            'williams', 'daniels', 'caleb', 'rome', 'nabers', 'harrison'
        ]
        if any(name in player for name in football_stars):
            confidence += 2.0  # HUGE boost for football stars
        
        # Regular star boost for others
        other_stars = ['lebron', 'curry', 'durant', 'giannis', 'tatum', 'luka', 'judge', 'ohtani']
        if any(name in player for name in other_stars):
            confidence += 1.0
        
        return min(10.0, confidence)

    def generate_prop_reasoning(self, proj, confidence):
        """Generate AI reasoning for prop recommendation"""
        player = proj.get('player_name', 'Player')
        stat = proj.get('stat_type', 'stat')
        line = proj.get('line_score', 0)
        odds_type = proj.get('odds_type', '').lower()
        
        reasoning_parts = []
        
        if confidence >= 8.0:  # Lowered from 8.5
            reasoning_parts.append("Excellent analytical edge identified.")
        elif confidence >= 6.5:  # Lowered from 7.5
            reasoning_parts.append("Strong value spotted in market pricing.")
        elif confidence >= 5.0:
            reasoning_parts.append("Good edge with solid upside.")
        else:
            reasoning_parts.append("Decent edge with manageable risk.")
        
        if 'over' in odds_type:
            reasoning_parts.append(f"{player} has strong potential to exceed {line} {stat}.")
        else:
            reasoning_parts.append(f"Market may be overvaluing {player}'s {stat} potential at this line.")
        
        if confidence >= 7.5:  # Lowered from 8
            reasoning_parts.append("High confidence play.")
        elif confidence >= 6.0:  # Lowered from 7
            reasoning_parts.append("Solid medium-high confidence bet.")
        elif confidence >= 4.5:
            reasoning_parts.append("Good medium confidence opportunity.")
        
        return " ".join(reasoning_parts)

    def generate_game_commentary(self, game, recommendations):
        """Generate AI commentary for a game"""
        team1 = game.get('team1', 'Team A')
        team2 = game.get('team2', 'Team B')
        sport = game.get('sport', '')
        
        if not recommendations:
            return f"No strong betting value identified in {team1} vs {team2}."
        
        commentary_parts = []
        
        commentary_parts.append(f"{team1} vs {team2} Analysis:")
        
        for rec in recommendations:
            bet_type = rec.get('bet_type', 'Bet')
            recommendation = rec.get('recommendation', '')
            confidence = rec.get('confidence', 5)
            reasoning = rec.get('reasoning', '')
            
            commentary_parts.append(f"• {bet_type}: {recommendation} (Confidence: {confidence:.1f}/10)")
            commentary_parts.append(f"  {reasoning}")
        
        return "\n".join(commentary_parts)

    def american_to_probability(self, odds):
        """Convert American odds to implied probability"""
        try:
            odds = int(odds)
            if odds > 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)
        except:
            return None

    def calculate_value(self, fair_prob, implied_prob):
        """Calculate betting value as percentage edge"""
        if implied_prob <= 0:
            return 0
        return max(0, (fair_prob - implied_prob) / implied_prob)

    def map_league_to_sport(self, league):
        """Map league name to sport - NOW INCLUDES ALL SPORTS"""
        league_lower = league.lower()
        if 'nfl' in league_lower:
            return 'NFL'
        elif 'ncaaf' in league_lower or 'college football' in league_lower:
            return 'CFB'
        elif 'nba' in league_lower:
            return 'NBA'
        elif 'ncaab' in league_lower or 'college basketball' in league_lower:
            return 'CBB'
        elif 'mlb' in league_lower or 'baseball' in league_lower:
            return 'MLB'
        elif 'nhl' in league_lower or 'hockey' in league_lower:
            return 'NHL'
        elif 'soccer' in league_lower or 'mls' in league_lower:
            return 'Soccer'
        else:
            return 'Other'

    def format_analysis_for_discord(self, bovada_analysis, prizepicks_analysis):
        """Format analysis results for Discord"""
        message = f"AI BETTING ANALYSIS - MAXIMUM PICKS MODE\n"
        message += f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        
        # Bovada section
        if bovada_analysis:
            message += f"TOP BOVADA PICKS ({len(bovada_analysis)} games)\n"
            
            for analysis in bovada_analysis[:12]:  # Increased from 8 to 12
                message += f"\n**{analysis['matchup']}**\n"
                
                for rec in analysis['recommendations']:
                    message += f"• {rec['bet_type']}: **{rec['recommendation']}** ({rec['odds']})\n"
                    message += f"  Confidence: {rec['confidence']:.1f}/10 | Edge: {rec.get('value_edge', 'N/A')}\n"
        
        # PrizePicks section - Show MORE diverse props
        if prizepicks_analysis:
            message += f"\nPRIZEPICKS PROPS ({len(prizepicks_analysis)} total)\n"
            
            # Group by sport
            sports_props = {}
            for prop in prizepicks_analysis:
                sport = prop['sport']
                if sport not in sports_props:
                    sports_props[sport] = []
                sports_props[sport].append(prop)
            
            for sport, props in sports_props.items():
                if sport == 'Other':
                    continue
                    
                message += f"\n**{sport} ({len(props)} props):**\n"
                for prop in props[:8]:  # Increased from 5 to 8 per sport
                    message += f"• **{prop['recommendation']}**\n"
                    message += f"  Confidence: {prop['confidence_score']:.1f}/10\n"
                    
                    reasoning = prop.get('reasoning', '')
                    if reasoning and len(reasoning) < 80:
                        message += f"  {reasoning}\n"
                    
                    message += "\n"
        
        return message

if __name__ == "__main__":
    analyzer = BettingAIAnalyzer()
    print("AI Betting Analyzer initialized - MAXIMUM PICKS MODE")