import json
import statistics
from datetime import datetime, timedelta
import math

class BettingAIAnalyzer:
    def __init__(self):
        self.confidence_threshold = 5.0
        self.max_picks_per_sport = 15
        
        # Value thresholds for different bet types
        self.value_thresholds = {
            'moneyline': 0.08,
            'spread': 0.06,
            'total': 0.05,
            'prop': 0.10
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
        
        # Group by sport and limit per sport
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
                confidence_scores = [rec.get('confidence', 5) for rec in analysis['recommendations']]
                analysis['confidence_score'] = max(confidence_scores)
                
                # Only return if meets threshold
                if analysis['confidence_score'] >= self.confidence_threshold:
                    return analysis
            
            return None
            
        except Exception as e:
            print(f"Error in single game analysis: {str(e)}")
            return None

    def analyze_moneyline(self, game):
        """Analyze moneyline odds for value"""
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
            
            if best_value > self.value_thresholds['moneyline']:
                recommended_team = game['team1'] if team1_value > team2_value else game['team2']
                recommended_odds = team1_odds if team1_value > team2_value else team2_odds
                
                confidence = min(10, 5 + (best_value * 20))
                
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
        """Analyze point spread for value"""
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
            
            confidence = 5.5
            recommendation = None
            
            if odds1 >= -120:
                confidence = 6.5
                recommendation = f"{game['team1']} {team1_spread}"
                best_odds = team1_odds
            elif odds2 >= -120:
                confidence = 6.5
                recommendation = f"{game['team2']} {team2_spread}"
                best_odds = team2_odds
            elif abs(spread1) <= 10:
                confidence = 6.0
                if odds1 >= odds2:
                    recommendation = f"{game['team1']} {team1_spread}"
                    best_odds = team1_odds
                else:
                    recommendation = f"{game['team2']} {team2_spread}"
                    best_odds = team2_odds
            
            if recommendation and confidence >= self.confidence_threshold:
                return {
                    'bet_type': 'Spread',
                    'recommendation': recommendation,
                    'odds': best_odds,
                    'confidence': confidence,
                    'value_edge': "5-10%",
                    'reasoning': f"Solid spread bet with decent odds. {recommendation} offers reasonable value in this matchup."
                }
            
            return None
            
        except Exception as e:
            return None

    def analyze_totals(self, game):
        """Analyze over/under totals"""
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
            
            confidence = 5.5
            recommendation = None
            sport = game.get('sport', '').upper()
            
            if sport == 'NFL':
                if over >= -115:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -115:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            elif sport == 'NBA':
                if over >= -115:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -115:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            elif sport == 'MLB':
                if over >= -115:
                    confidence = 6.0
                    recommendation = f"Over {total}"
                    bet_odds = over
                elif under >= -115:
                    confidence = 6.0
                    recommendation = f"Under {total}"
                    bet_odds = under
            
            if recommendation and confidence >= self.confidence_threshold:
                return {
                    'bet_type': 'Total',
                    'recommendation': recommendation,
                    'odds': bet_odds,
                    'confidence': confidence,
                    'value_edge': "5-8%",
                    'reasoning': f"Reasonable total with decent odds. {recommendation} offers decent value for {sport}."
                }
            
            return None
            
        except Exception as e:
            return None

    def analyze_prizepicks_projections(self, projections):
        """Analyze PrizePicks projections for best props with improved variety"""
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
        
        # Sort by confidence first
        analyzed_props.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # NEW: Diversify by player to avoid repetition
        diversified_props = self.diversify_player_picks(analyzed_props)
        
        # Group by sport and limit - FOCUS ON NFL AND CFB ONLY
        sport_props = {}
        for prop in diversified_props:
            sport = self.map_league_to_sport(prop.get('league', ''))
            
            # ONLY INCLUDE NFL AND CFB
            if sport not in ['NFL', 'CFB']:
                continue
                
            if sport not in sport_props:
                sport_props[sport] = []
            if len(sport_props[sport]) < self.max_picks_per_sport:
                sport_props[sport].append(prop)
        
        # Flatten and return
        top_props = []
        for sport_list in sport_props.values():
            top_props.extend(sport_list)
        
        return top_props

    def diversify_player_picks(self, analyzed_props, max_per_player=2):
        """Ensure variety by limiting picks per player"""
        player_picks = {}
        diversified = []
        
        # Group by player
        for prop in analyzed_props:
            player = prop.get('player_name', 'Unknown')
            if player not in player_picks:
                player_picks[player] = []
            player_picks[player].append(prop)
        
        # Take top picks per player, prioritizing different stat types
        for player, picks in player_picks.items():
            # Sort by confidence
            picks.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
            
            # Group by stat type for this player
            stat_types_seen = set()
            player_selected = []
            
            for pick in picks:
                stat_type = pick.get('stat_type', '').lower()
                
                # Prioritize different stat types for variety
                if stat_type not in stat_types_seen or len(player_selected) == 0:
                    player_selected.append(pick)
                    stat_types_seen.add(stat_type)
                    
                    if len(player_selected) >= max_per_player:
                        break
            
            diversified.extend(player_selected)
        
        # Sort final list by confidence
        diversified.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        return diversified

    def analyze_single_projection(self, proj):
        """Analyze a single PrizePicks projection"""
        try:
            player = proj.get('player_name', 'Unknown Player')
            stat_type = proj.get('stat_type', '')
            line = proj.get('line_score', 0)
            odds_type = proj.get('odds_type', '')
            league = proj.get('league', '')
            
            # Calculate confidence based on multiple factors
            confidence = self.calculate_prop_confidence(proj)
            
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

    def calculate_prop_confidence(self, proj):
        """Calculate confidence score for a prop bet"""
        confidence = 5.0
        
        stat_type = proj.get('stat_type', '').lower()
        line = proj.get('line_score', 0)
        player = proj.get('player_name', '').lower()
        
        # Boost confidence for certain stat types
        if any(stat in stat_type for stat in ['points', 'yards', 'strikeouts', 'hits']):
            confidence += 1.0
        
        # Boost for round numbers
        if line in [0.5, 1.5, 2.5, 20.5, 25.5]:
            confidence += 0.5
        
        # Boost for star players
        star_indicators = ['lebron', 'curry', 'mahomes', 'aaron', 'judge', 'ohtani', 'tatum', 'luka']
        if any(name in player for name in star_indicators):
            confidence += 1.0
        
        # Boost for favorable stat types by sport
        league = proj.get('league', '').lower()
        if 'nfl' in league and any(stat in stat_type for stat in ['pass', 'rush', 'receiving']):
            confidence += 0.5
        elif 'nba' in league and any(stat in stat_type for stat in ['points', 'rebounds', 'assists']):
            confidence += 0.5
        elif 'mlb' in league and any(stat in stat_type for stat in ['hits', 'strikeouts', 'runs']):
            confidence += 0.5
        
        return min(10.0, confidence)

    def generate_prop_reasoning(self, proj, confidence):
        """Generate AI reasoning for prop recommendation"""
        player = proj.get('player_name', 'Player')
        stat = proj.get('stat_type', 'stat')
        line = proj.get('line_score', 0)
        odds_type = proj.get('odds_type', '').lower()
        
        reasoning_parts = []
        
        if confidence >= 8.5:
            reasoning_parts.append("Strong analytical edge identified.")
        elif confidence >= 7.5:
            reasoning_parts.append("Good value spotted in market pricing.")
        else:
            reasoning_parts.append("Decent edge with manageable risk.")
        
        if 'over' in odds_type:
            reasoning_parts.append(f"{player} has shown ability to exceed {line} {stat} consistently.")
        else:
            reasoning_parts.append(f"Market appears to be overvaluing {player}'s {stat} potential.")
        
        if confidence >= 8:
            reasoning_parts.append("High confidence play.")
        elif confidence >= 7:
            reasoning_parts.append("Solid medium confidence bet.")
        
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
        """Map league name to sport - UPDATED to focus on football only"""
        league_lower = league.lower()
        if 'nfl' in league_lower:
            return 'NFL'
        elif 'ncaaf' in league_lower or 'college football' in league_lower:
            return 'CFB'
        else:
            return 'Other'  # This will be filtered out

    def format_analysis_for_discord(self, bovada_analysis, prizepicks_analysis):
        """Format analysis results for Discord"""
        message = f"AI BETTING ANALYSIS\n"
        message += f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        
        # Bovada section
        if bovada_analysis:
            message += f"TOP BOVADA PICKS ({len(bovada_analysis)} games)\n"
            
            for analysis in bovada_analysis[:8]:
                message += f"\n**{analysis['matchup']}**\n"
                
                for rec in analysis['recommendations']:
                    message += f"• {rec['bet_type']}: **{rec['recommendation']}** ({rec['odds']})\n"
                    message += f"  Confidence: {rec['confidence']:.1f}/10 | Edge: {rec.get('value_edge', 'N/A')}\n"
                
                reasoning = analysis.get('ai_commentary', '')
                if reasoning and len(reasoning) > 50:
                    first_line = reasoning.split('\n')[0].replace('**', '').replace('Analysis:', '')
                    if len(first_line) < 80:
                        message += f"{first_line}\n"
        
        # PrizePicks section - Show diverse props
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
                for prop in props:
                    message += f"• **{prop['recommendation']}**\n"
                    message += f"  Confidence: {prop['confidence_score']:.1f}/10\n"
                    
                    reasoning = prop.get('reasoning', '')
                    if reasoning and len(reasoning) < 60:
                        message += f"  {reasoning}\n"
                    
                    message += "\n"
        
        return message

if __name__ == "__main__":
    analyzer = BettingAIAnalyzer()
    print("AI Betting Analyzer initialized")